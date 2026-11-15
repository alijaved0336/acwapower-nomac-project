import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import os
import pytz

from config.optimized_clickhouse_connector import execute_optimized_clickhouse_query
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from constants import DatabaseColumns, DatabaseConfig

logger = logging.getLogger(__name__)


class Dash001Repository:
    """
    Repository for Dash-001 specific ClickHouse queries.
    Handles daily dispatch data retrieval with proper timezone-aware datetime conversions.
    """

    def __init__(self):
        """Initialize repository with ClickHouseRepository"""
        self.clickhouse_repository = ClickHouseRepository()

    def _get_timezone(self) -> str:
        """Get the configured timezone for the application."""
        return os.getenv('CLICKHOUSE_TIMEZONE', 'Asia/Dubai')

    def _build_datetime_conversion_expr(self, datetime_column: str, target_timezone: str = 'UTC') -> str:
        """
        Build datetime conversion expression for ClickHouse queries.
        Handles String, DateTime, and DateTime64 types correctly.

        Args:
            datetime_column: Name of the datetime column
            target_timezone: Target timezone ('UTC' or 'Asia/Dubai')

        Returns:
            SQL expression string for datetime conversion
        """
        return f"""toTimeZone(
            if(toTypeName(`{datetime_column}`) LIKE '%%String%%',
            parseDateTime64BestEffort(`{datetime_column}`),
            if(toTypeName(`{datetime_column}`) LIKE '%%DateTime64%%',
            `{datetime_column}`,
            toDateTime64(`{datetime_column}`, 3)
            )
            ),
            '{target_timezone}'
        )""".strip().replace('\n', ' ')

    def _build_datetime_utc_expr(self, datetime_column: str) -> str:
        """
        Build datetime expression for UTC comparison (without timezone conversion).
        Used for WHERE clauses where data is stored in UTC.

        Args:
            datetime_column: Name of the datetime column

        Returns:
            SQL expression string for datetime conversion to UTC
        """
        return f"""if(toTypeName(`{datetime_column}`) LIKE '%%String%%',
            parseDateTime64BestEffort(`{datetime_column}`),
            if(toTypeName(`{datetime_column}`) LIKE '%%DateTime64%%',
            `{datetime_column}`,
            toDateTime64(`{datetime_column}`, 3)
            )
            )""".strip().replace('\n', ' ')

    def _convert_date_to_utc_range(self, target_date: str) -> tuple:
        """
        Convert a target date (YYYY-MM-DD) to UTC date range for query comparison.
        Converts full day in Asia/Dubai timezone to UTC range.
        
        The key insight: Data stored in ClickHouse is in UTC. When we want to find
        records for a date in Asia/Dubai, we need to account for the 4-hour offset.
        For example, 2025-11-26 00:00:00 Asia/Dubai = 2025-11-25 20:00:00 UTC.

        Args:
            target_date: Target date in YYYY-MM-DD format (interpreted as Asia/Dubai date)

        Returns:
            Tuple of (start_utc_str, end_utc_str) in 'YYYY-MM-DD HH:MM:SS' format
        """
        # Parse target date
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d')

        # Start of day in Asia/Dubai: 2025-11-26 00:00:00 Asia/Dubai
        start_datetime_dubai = target_date_obj.replace(hour=0, minute=0, second=0)
        # End of day in Asia/Dubai: 2025-11-26 23:59:59 Asia/Dubai
        end_datetime_dubai = target_date_obj.replace(hour=23, minute=59, second=59, microsecond=999000)

        # Convert to UTC for comparison (data is stored in UTC)
        dubai_tz = pytz.timezone('Asia/Dubai')
        utc_tz = pytz.UTC

        # Localize to Asia/Dubai
        start_dubai = dubai_tz.localize(start_datetime_dubai)
        end_dubai = dubai_tz.localize(end_datetime_dubai)

        # Convert to UTC (this accounts for the 4-hour offset)
        start_utc = start_dubai.astimezone(utc_tz)
        end_utc = end_dubai.astimezone(utc_tz)

        # Return as strings
        # Use end_utc as-is (inclusive) since we use <= in the query
        return (
            start_utc.strftime('%Y-%m-%d %H:%M:%S'),
            end_utc.strftime('%Y-%m-%d %H:%M:%S')
        )

    def get_overall_latest_date(
        self,
        clusters_to_process: List[str],
        clusters_with_plants: Dict,
        plant_sites: Dict,
        check_cluster_data_func
    ) -> Optional[str]:
        """
        Get the most recent date across all relevant sites using DESC order (limit 1).
        Queries each site with ORDER BY datetime DESC LIMIT 1, extracts the date in Asia/Dubai,
        and returns the maximum date across all sites.

        Args:
            clusters_to_process: List of cluster names to process
            clusters_with_plants: Dictionary mapping cluster names to their assigned sites
            plant_sites: Dictionary mapping site names to table names
            check_cluster_data_func: Function to check if site has cluster data

        Returns:
            Most recent date in YYYY-MM-DD format, or None if no data found
        """
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            latest_dates = []

            for cluster_name in clusters_to_process:
                cluster_filter_data = clusters_with_plants.get(cluster_name, [])
                cluster_filter_str = f"Cluster: {cluster_name}" if ": " not in cluster_name else cluster_name

                for site_name, table_name in plant_sites.items():
                    if site_name not in cluster_filter_data:
                        continue

                    try:
                        # Check if site has data for this cluster
                        has_cluster_data = check_cluster_data_func(
                            site_name, table_name, [cluster_filter_str]
                        )

                        if not has_cluster_data:
                            continue

                        # Get ClickHouse table name using repository method
                        clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(site_name, table_name)
                        if not clickhouse_table_name:
                            continue

                        # Get datetime column using repository method
                        datetime_column = self.clickhouse_repository.get_datetime_column(clickhouse_table_name)
                        if not datetime_column:
                            continue

                        # Build datetime conversion expression for ORDER BY (convert to UTC for consistent ordering)
                        datetime_order_expr = self._build_datetime_conversion_expr(datetime_column, 'UTC')

                        # Build datetime expression for date extraction in Asia/Dubai timezone
                        # This ensures dates are extracted in the user's timezone, not UTC
                        datetime_date_expr = self._build_datetime_conversion_expr(datetime_column, 'Asia/Dubai')

                        # Query to get the latest datetime record (DESC, limit 1), then extract date in Asia/Dubai
                        query = f"""
                        SELECT toDate({datetime_date_expr}) as latest_date
                        FROM `{database}`.`{clickhouse_table_name}`
                        WHERE `{DatabaseColumns.CLUSTER_NAME}` = {{cluster:String}}
                        ORDER BY {datetime_order_expr} DESC
                        LIMIT 1
                        """

                        query_params = {"cluster": cluster_filter_str}

                        # Execute query to get latest datetime, then extract date
                        result = execute_optimized_clickhouse_query(
                            query,
                            params=query_params,
                            use_cache=False
                        )

                        result_rows = result.result_rows if hasattr(result, 'result_rows') else []
                        if result_rows and len(result_rows) > 0 and result_rows[0][0]:
                            latest_date = result_rows[0][0]
                            # Convert to string in YYYY-MM-DD format
                            if hasattr(latest_date, 'strftime'):
                                date_str = latest_date.strftime('%Y-%m-%d')
                            else:
                                date_str = str(latest_date)

                            latest_dates.append(date_str)
                            logger.debug(f"Latest date for {site_name}.{cluster_name}: {date_str}")

                    except Exception as e:
                        logger.warning(f"Error getting latest date for {site_name}.{cluster_name}: {e}")
                        continue

            if not latest_dates:
                return None

            # Find the overall latest date (most recent)
            overall_latest = max(latest_dates)
            logger.info(f"Overall latest date across all data: {overall_latest}")
            return overall_latest

        except Exception as e:
            logger.error(f"Error finding overall latest date: {e}", exc_info=True)
            return None

    def get_latest_date_for_site(
        self,
        site_name: str,
        table_name: str,
        cluster_filter: str,
        clickhouse_table_name: str,
        datetime_column: str
    ) -> Optional[str]:
        """
        Get the latest available date for a specific site using Asia/Dubai timezone conversion.
        This ensures dates are extracted in the user's timezone, not UTC, which is critical for
        late-night times (e.g., 2025-11-28 01:33:00 Asia/Dubai should return 2025-11-28, not 2025-11-27).

        Args:
            site_name: Site identifier
            table_name: Table name
            cluster_filter: Cluster filter string
            clickhouse_table_name: ClickHouse table name
            datetime_column: Datetime column name

        Returns:
            Latest available date in YYYY-MM-DD format (Asia/Dubai timezone), or None if no data found
        """
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Build datetime conversion expression for ORDER BY (convert to UTC for consistent ordering)
            datetime_order_expr = self._build_datetime_conversion_expr(datetime_column, 'UTC')

            # Build datetime expression for date extraction in Asia/Dubai timezone
            # This ensures dates are extracted in the user's timezone, not UTC
            datetime_date_expr = self._build_datetime_conversion_expr(datetime_column, 'Asia/Dubai')

            # Query to get the latest datetime record (DESC, limit 1), then extract date in Asia/Dubai
            query = f"""
            SELECT toDate({datetime_date_expr}) as latest_date
            FROM `{database}`.`{clickhouse_table_name}`
            WHERE `{DatabaseColumns.CLUSTER_NAME}` = {{cluster:String}}
            ORDER BY {datetime_order_expr} DESC
            LIMIT 1
            """

            query_params = {"cluster": cluster_filter}

            logger.debug(f"Getting latest date for site {site_name} (table: {clickhouse_table_name}, cluster: {cluster_filter})")

            # Execute query to get latest datetime, then extract date
            result = execute_optimized_clickhouse_query(
                query,
                params=query_params,
                use_cache=False
            )

            result_rows = result.result_rows if hasattr(result, 'result_rows') else []
            if result_rows and len(result_rows) > 0 and result_rows[0][0]:
                latest_date = result_rows[0][0]
                # Convert to string in YYYY-MM-DD format
                if hasattr(latest_date, 'strftime'):
                    date_str = latest_date.strftime('%Y-%m-%d')
                else:
                    date_str = str(latest_date)

                logger.info(f"Latest date for site {site_name} (Asia/Dubai): {date_str}")
                return date_str

            logger.warning(f"No data found for site {site_name} in cluster {cluster_filter}")
            return None

        except Exception as e:
            logger.error(f"Error getting latest date for site {site_name}: {e}", exc_info=True)
            return None

    def get_daily_dispatch_for_date(
        self,
        site_name: str,
        table_name: str,
        cluster_filter: str,
        target_date: str,
        datetime_column: str,
        clickhouse_table_name: str,
        daily_dispatch_column: str
    ) -> Optional[Dict]:
        """
        Get the latest daily dispatch record for a specific date using DESC ordering (limit 1).
        Uses date extraction in Asia/Dubai timezone to match the target date correctly.

        Args:
            site_name: Site identifier
            table_name: Table name
            cluster_filter: Cluster filter string
            target_date: Target date in YYYY-MM-DD format
            datetime_column: Datetime column name
            clickhouse_table_name: ClickHouse table name

        Returns:
            Dictionary with daily dispatch data including table_name, datetime, and dispatch value,
            or None if no data found
        """
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Convert target date to UTC date range for comparison
            # This ensures we capture all records that fall within the target date in Asia/Dubai
            # Example: For 2025-11-26 in Asia/Dubai, we need UTC range from 2025-11-25 20:00:00 to 2025-11-26 19:59:59 UTC
            # This accounts for the 4-hour offset (Asia/Dubai = UTC+4)
            start_utc_str, end_utc_str = self._convert_date_to_utc_range(target_date)
            
            # Build datetime expression for UTC comparison (data is stored in UTC)
            # This matches the pattern used in clickhouseRepository.py line 1509-1515
            # IMPORTANT: DateTime64 columns are stored without timezone, but data is already in UTC
            # We should NOT use toTimeZone() because that assumes data is in connection timezone
            # Instead, normalize the column and compare directly with UTC parameters
            datetime_where_expr = f"""if(toTypeName(`{datetime_column}`) LIKE '%%String%%',
                parseDateTime64BestEffort(`{datetime_column}`),
                if(toTypeName(`{datetime_column}`) LIKE '%%DateTime64%%',
                `{datetime_column}`,
                toDateTime64(`{datetime_column}`, 3)
                )
                )""".strip().replace('\n', ' ')

            # Build datetime conversion expression for ORDER BY
            # Use the same expression as WHERE clause for consistency
            # IMPORTANT: DateTime64 columns in ClickHouse are stored without timezone
            # We need to compare them directly (not convert timezone) for proper ordering
            datetime_order_expr = datetime_where_expr

            # Use UTC range comparison with toDateTime64 - this is the most reliable approach
            # Following the pattern from clickhouseRepository.py line 1520-1521
            # The UTC range already accounts for the 4-hour offset from Asia/Dubai
            # IMPORTANT: Data in ClickHouse is stored in UTC, so we compare directly in UTC
            # DateTime64 columns are stored without timezone, so wrap with toDateTime64 for explicit UTC comparison
            query = f"""
            SELECT `{datetime_column}`, `{daily_dispatch_column}`
            FROM `{database}`.`{clickhouse_table_name}`
            WHERE `{DatabaseColumns.CLUSTER_NAME}` = {{cluster:String}}
                AND {datetime_where_expr} >= toDateTime64({{start_datetime:String}}, 3, 'UTC')
                AND {datetime_where_expr} <= toDateTime64({{end_datetime:String}}, 3, 'UTC')
            ORDER BY {datetime_order_expr} DESC
            LIMIT 1
            """

            query_params = {
                "cluster": cluster_filter,
                "start_datetime": start_utc_str,
                "end_datetime": end_utc_str
            }

            logger.debug(f"Querying for date {target_date} (Asia/Dubai) using UTC range: {start_utc_str} to {end_utc_str} (accounts for 4-hour offset)")
            logger.debug(f"Full query: {query}")
            logger.debug(f"Query params: {query_params}")

            logger.info(f"Fetching latest daily dispatch for {site_name} on {target_date} (table: {clickhouse_table_name}, cluster: {cluster_filter})")

            # Execute custom query with DESC ordering
            result = execute_optimized_clickhouse_query(
                query,
                params=query_params,
                use_cache=False
            )

            # Extract result rows
            result_rows = result.result_rows if hasattr(result, 'result_rows') else []

            if result_rows and len(result_rows) > 0:
                row = result_rows[0]
                result_datetime = row[0] if len(row) > 0 else None
                
                # Convert returned datetime from UTC to Asia/Dubai for display
                # Data is stored in UTC, but we need to display it in user's timezone (Asia/Dubai)
                if result_datetime:
                    try:
                        dubai_tz = pytz.timezone('Asia/Dubai')
                        utc_tz = pytz.UTC
                        
                        # Handle different datetime formats
                        if isinstance(result_datetime, datetime):
                            # If datetime is timezone-aware, convert directly
                            if result_datetime.tzinfo is not None:
                                dt_utc = result_datetime.astimezone(utc_tz)
                            else:
                                # If naive, assume it's UTC (from ClickHouse)
                                dt_utc = utc_tz.localize(result_datetime)
                            
                            # Convert to Asia/Dubai
                            dt_dubai = dt_utc.astimezone(dubai_tz)
                            result_datetime = dt_dubai
                        elif isinstance(result_datetime, str):
                            # Parse string datetime (assume UTC from ClickHouse)
                            from infrastructure.utils.datetime_utils import DateTimeParser
                            dt_parsed = DateTimeParser.parse_datetime(result_datetime)
                            if dt_parsed:
                                # Assume parsed datetime is UTC
                                if dt_parsed.tzinfo is None:
                                    dt_utc = utc_tz.localize(dt_parsed)
                                else:
                                    dt_utc = dt_parsed.astimezone(utc_tz)
                                # Convert to Asia/Dubai
                                dt_dubai = dt_utc.astimezone(dubai_tz)
                                result_datetime = dt_dubai
                    except Exception as e:
                        logger.warning(f"Could not convert datetime to Asia/Dubai: {e}, using original value")
                
                result_dict = {
                    "table_name": table_name,  # Include table_name in the result
                    datetime_column: result_datetime,
                    daily_dispatch_column: row[1] if len(row) > 1 else None
                }

                # Verify the returned datetime matches the target date (in Asia/Dubai)
                if result_datetime:
                    try:
                        # Extract date from returned datetime to verify it matches target_date
                        if isinstance(result_datetime, datetime):
                            # Use the datetime as-is (now in Asia/Dubai)
                            returned_date = result_datetime.strftime('%Y-%m-%d')
                        elif isinstance(result_datetime, str):
                            if 'T' in result_datetime:
                                returned_date = result_datetime.split('T')[0]
                            else:
                                returned_date = result_datetime.split(' ')[0]
                        else:
                            returned_date = str(result_datetime)[:10]

                        if returned_date != target_date:
                            logger.warning(f"⚠️ Date mismatch: Query for {target_date} returned datetime {result_datetime} (date: {returned_date})")
                    except Exception as e:
                        logger.debug(f"Could not verify date match: {e}")

                logger.info(f"✓ Retrieved data for {site_name} on {target_date}: dispatch={result_dict.get(daily_dispatch_column)}, datetime={result_dict.get(datetime_column)}")
                return result_dict

            logger.warning(f"✗ No data found for {site_name} on {target_date} (table: {clickhouse_table_name}, cluster: {cluster_filter})")
            return None

        except Exception as e:
            logger.error(f"Error getting daily dispatch for {site_name} on {target_date}: {e}", exc_info=True)
            return None

