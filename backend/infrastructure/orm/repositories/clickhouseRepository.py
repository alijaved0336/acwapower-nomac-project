import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import re
import os
import pytz

from config.clickhouse_connector import execute_clickhouse_query, validate_table_name
from infrastructure.utils.datetime_utils import DateTimeParser
from constants import (
    ErrorMessages,
    ClickHouseMigrationStatus,
    ClickHouseColumnPatterns,
    ClickHouseDataValidation,
    ClickHouseQueryConfig
)
from datetime import datetime as dt, timedelta
from constants import CLICKHOUSE_FALLBACK_DAYS

logger = logging.getLogger(__name__)


class ClickHouseRepository:
    """Repository for handling ClickHouse-related database queries"""

    def __init__(self):
        """Initialize repository"""
        pass

    def _get_timezone(self) -> str:
        """
        Get the configured timezone for the application.
        
        Returns:
            str: Timezone string (e.g., 'Asia/Dubai')
        """
        import os
        return os.getenv('CLICKHOUSE_TIMEZONE', 'Asia/Dubai')
    
    def _convert_user_datetime_to_utc(self, user_datetime: datetime) -> str:
        """
        Convert user-provided datetime from Asia/Dubai timezone to UTC.
        
        Args:
            user_datetime: Datetime object (interpreted as Asia/Dubai)
            
        Returns:
            UTC datetime string in format 'YYYY-MM-DD HH:MM:SS'
        """
        try:
            user_tz = pytz.timezone('Asia/Dubai')
            utc_tz = pytz.UTC
            
            # Ensure datetime is naive (no timezone info)
            if user_datetime.tzinfo is not None:
                dt = user_datetime.replace(tzinfo=None)
            else:
                dt = user_datetime
            
            # Localize to Asia/Dubai (user's timezone)
            dt_dubai = user_tz.localize(dt)
            
            # Convert to UTC
            dt_utc = dt_dubai.astimezone(utc_tz)
            
            # Return as string in UTC
            return dt_utc.strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.error(f"Error converting user datetime to UTC: {e}", exc_info=True)
            # Fallback: return as-is
            return user_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    def _convert_user_date_string_to_utc(self, user_date_str: str) -> Optional[str]:
        """
        Convert user-provided date string from Asia/Dubai timezone to UTC.
        
        Args:
            user_date_str: Date string (interpreted as Asia/Dubai)
            
        Returns:
            UTC datetime string in format 'YYYY-MM-DD HH:MM:SS' or None
        """
        if not user_date_str:
            return None
        
        try:
            from infrastructure.utils.datetime_utils import DateTimeParser
            user_tz = pytz.timezone('Asia/Dubai')
            utc_tz = pytz.UTC
            
            # Parse the date string
            dt = DateTimeParser.parse_datetime(user_date_str)
            if not dt:
                logger.warning(f"Failed to parse date string: {user_date_str}")
                return None
            
            # Ensure datetime is naive
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            
            # Localize to Asia/Dubai
            dt_dubai = user_tz.localize(dt)
            
            # Convert to UTC
            dt_utc = dt_dubai.astimezone(utc_tz)
            
            # Return as string in UTC
            return dt_utc.strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.error(f"Error converting user date string to UTC: {e}", exc_info=True)
            return None

    def get_all_tables(self) -> List[str]:
        """
        Get all table names from the current ClickHouse database.

        Returns:
            List[str]: List of table names

        Raises:
            Exception: If query execution fails
        """
        try:
            query = "SELECT name FROM system.tables WHERE database = currentDatabase() ORDER BY name"
            result = execute_clickhouse_query(query)

            # Extract table names from result
            table_names = [row[0] for row in result.result_rows]

            logger.info(f"Retrieved {len(table_names)} tables from ClickHouse")
            return table_names

        except Exception as e:
            logger.error(f"Failed to retrieve tables from ClickHouse: {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=str(e)))

    def get_sites(self) -> List[Dict[str, str]]:
        """
        Get all sites from site_table_mapping.

        Returns:
            List of sites with name and path
            
        Raises:
            Exception: If query execution fails
        """
        try:
            query = """
            SELECT DISTINCT
                site_name,
                'tables/gold/' || site_name AS path
            FROM site_table_mapping
            WHERE migration_status IN {statuses:Array(String)}
            AND NOT (site_name = 'coordinates' AND base_path = 'tables')
            ORDER BY site_name
            """

            result = execute_clickhouse_query(query, params={"statuses": ClickHouseMigrationStatus.BASIC_STATUSES})

            sites = []
            for row in result.result_rows:
                sites.append({
                    "name": row[0],
                    "path": row[1]
                })

            logger.info(f"Retrieved {len(sites)} sites from ClickHouse")
            return sites

        except Exception as e:
            logger.error(f"Error retrieving sites from ClickHouse: {e}")
            raise Exception(f"Failed to retrieve sites: {str(e)}")

    def get_tables_for_site(self, site_name: str) -> List[Dict[str, str]]:
        """
        Get all tables for a specific site from site_table_mapping.

        Args:
            site_name: The site identifier

        Returns:
            List of tables with tableName and siteName
            
        Raises:
            Exception: If query execution fails
        """
        try:
            query = """
            SELECT DISTINCT
                table_name,
                site_name
            FROM site_table_mapping
            WHERE site_name = {site_name:String}
              AND migration_status IN {statuses:Array(String)}
              AND NOT (site_name = 'coordinates' AND base_path = 'tables')
            ORDER BY table_name
            """

            result = execute_clickhouse_query(query, params={"site_name": site_name, "statuses": ClickHouseMigrationStatus.BASIC_STATUSES})

            tables = []
            for row in result.result_rows:
                tables.append({
                    "tableName": row[0],
                    "siteName": row[1]
                })

            logger.info(f"Retrieved {len(tables)} tables for site {site_name} from ClickHouse")
            return tables

        except Exception as e:
            logger.error(f"Error retrieving tables for site {site_name}: {e}")
            raise Exception(f"Failed to retrieve tables for site {site_name}: {str(e)}")

    def get_migration_status_data(self) -> Dict[str, Any]:
        """
        Get raw migration status data from database.
        
        Returns:
            Dict with sites_stats, tables_stats, and recent_logs
            
        Raises:
            Exception: If query execution fails
        """
        try:
            # Get site statistics
            sites_query = """
            SELECT
                COUNT(DISTINCT site_name) as total_sites,
                COUNT(DISTINCT CASE WHEN migration_status = 'migrated' THEN site_name END) as migrated_sites
            FROM site_table_mapping
            """

            # Get table statistics
            tables_query = """
            SELECT
                migration_status,
                COUNT(*) as count,
                SUM(row_count) as total_rows
            FROM site_table_mapping
            GROUP BY migration_status
            """

            # Get recent migration logs
            logs_query = """
            SELECT
                migration_id,
                command_type,
                status,
                sites_processed,
                tables_processed,
                started_at,
                completed_at
            FROM migration_log
            ORDER BY started_at DESC
            LIMIT {limit:UInt32}
            """

            sites_result = execute_clickhouse_query(sites_query)
            tables_result = execute_clickhouse_query(tables_query)
            logs_result = execute_clickhouse_query(logs_query, params={"limit": ClickHouseQueryConfig.RECENT_LOGS_LIMIT})

            # Process sites results
            sites_stats = sites_result.result_rows[0] if sites_result.result_rows else (0, 0)

            # Process tables results
            tables_stats = {}
            for row in tables_result.result_rows:
                status, count, rows = row
                tables_stats[status] = {
                    "count": count,
                    "rows": rows or 0
                }

            # Process logs results
            recent_logs = []
            for row in logs_result.result_rows:
                recent_logs.append({
                    "migration_id": row[0],
                    "command_type": row[1],
                    "status": row[2],
                    "sites_processed": row[3],
                    "tables_processed": row[4],
                    "started_at": str(row[5]),
                    "completed_at": str(row[6]) if row[6] else None
                })

            return {
                "sites_stats": sites_stats,
                "tables_stats": tables_stats,
                "recent_logs": recent_logs
            }

        except Exception as e:
            logger.error(f"Error retrieving migration status data: {e}")
            raise Exception(f"Failed to retrieve migration status data: {str(e)}")

    def get_columns_for_tables(self, tables_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Get column information for multiple tables from site_table_mapping and system.columns.

        Args:
            tables_list: List of dictionaries with siteName and tableName

        Returns:
            List of column information with parquet-equivalent types
            
        Raises:
            Exception: If query execution fails
        """
        try:
            all_columns = []

            for table_request in tables_list:
                site_name = table_request.get('siteName')
                table_name = table_request.get('tableName')

                if not site_name or not table_name:
                    continue

                # Get ClickHouse table name from mapping
                mapping_query = """
                SELECT clickhouse_table_name
                FROM site_table_mapping
                WHERE site_name = {site_name:String} AND table_name = {table_name:String}
                  AND migration_status IN {statuses:Array(String)}
                """

                mapping_result = execute_clickhouse_query(mapping_query, params={
                    "site_name": site_name,
                    "table_name": table_name,
                    "statuses": ClickHouseMigrationStatus.BASIC_STATUSES
                })

                if not mapping_result.result_rows:
                    logger.warning(f"No ClickHouse table found for {site_name}.{table_name}")
                    continue

                clickhouse_table_name = mapping_result.result_rows[0][0]

                # Get column information from ClickHouse system tables
                columns_query = """
                SELECT name, type
                FROM system.columns
                WHERE table = {table_name:String}
                ORDER BY position
                """

                columns_result = execute_clickhouse_query(columns_query, params={
                    "table_name": clickhouse_table_name
                })

                # Convert ClickHouse types to parquet-equivalent types
                for row in columns_result.result_rows:
                    column_name, clickhouse_type = row
                    
                    # Exclude internal tracking columns from results
                    if column_name in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS:
                        continue
                    
                    parquet_type = self._convert_clickhouse_to_parquet_type(clickhouse_type)

                    all_columns.append({
                        "columnName": column_name,
                        "columnType": parquet_type,
                        "tableName": table_name,
                        "siteName": site_name
                    })

            logger.info(f"Retrieved columns for {len(tables_list)} tables")
            return all_columns

        except Exception as e:
            logger.error(f"Error retrieving columns for tables: {e}")
            raise Exception(f"Failed to retrieve columns: {str(e)}")

    def get_clickhouse_table_name(self, site_name: str, table_name: str) -> Optional[str]:
        """
        Get ClickHouse table name from site_table_mapping.
        
        Args:
            site_name: Site identifier
            table_name: Table identifier
            
        Returns:
            ClickHouse table name or None if not found
            
        Raises:
            Exception: If query execution fails
        """
        try:
            mapping_query = """
            SELECT clickhouse_table_name
            FROM site_table_mapping
            WHERE site_name = {site_name:String} AND table_name = {table_name:String}
              AND migration_status IN {statuses:Array(String)}
            """

            mapping_result = execute_clickhouse_query(mapping_query, params={
                "site_name": site_name,
                "table_name": table_name,
                "statuses": ClickHouseMigrationStatus.ALL_STATUSES
            })

            if not mapping_result.result_rows:
                return None

            return mapping_result.result_rows[0][0]

        except Exception as e:
            logger.error(f"Error retrieving ClickHouse table name for {site_name}.{table_name}: {e}")
            raise Exception(f"Failed to retrieve ClickHouse table name: {str(e)}")

    def get_datetime_column(self, table_name: str) -> Optional[str]:
        """
        Find the DateTime column in the table.
        
        Args:
            table_name: ClickHouse table name
            
        Returns:
            DateTime column name or None if not found
        """
        try:
            columns_query = """
            SELECT name, type
            FROM system.columns
            WHERE table = {table_name:String}
            ORDER BY position
            """

            columns_result = execute_clickhouse_query(columns_query, params={
                "table_name": table_name
            })

            # Look for common datetime column names and types
            datetime_candidates = ClickHouseColumnPatterns.DATETIME_CANDIDATES[:9]  # Use first 9 candidates

            # First priority: exact name matches
            for row in columns_result.result_rows:
                column_name, column_type = row
                if column_name.lower() in [c.lower() for c in datetime_candidates]:
                    logger.info(f"Found datetime column by name: {column_name} ({column_type})")
                    return column_name

            # Second priority: type-based detection
            for row in columns_result.result_rows:
                column_name, column_type = row
                if ('datetime' in column_type.lower() or 
                    'timestamp' in column_type.lower() or
                    column_type.lower().startswith('date')):
                    logger.info(f"Found datetime column by type: {column_name} ({column_type})")
                    return column_name

            return None

        except Exception as e:
            logger.error(f"Error finding datetime column in table {table_name}: {e}")
            return None

    def get_rack_trailer_column(self, table_name: str) -> Optional[str]:
        """
        Find rack or trailer column in the table.
        
        Args:
            table_name: ClickHouse table name
            
        Returns:
            Rack/trailer column name or None if not found
        """
        try:
            columns_query = """
            SELECT name, type
            FROM system.columns
            WHERE table = {table_name:String}
            ORDER BY position
            """

            columns_result = execute_clickhouse_query(columns_query, params={
                "table_name": table_name
            })

            # High priority rack/trailer column candidates
            rack_candidates = ClickHouseColumnPatterns.RACK_CANDIDATES

            for row in columns_result.result_rows:
                column_name, column_type = row
                column_lower = column_name.lower()
                
                for candidate in rack_candidates:
                    if column_lower == candidate:
                        logger.info(f"Found rack/trailer column by exact match: {column_name}")
                        return column_name

            logger.warning(f"No rack/trailer column found in table {table_name}")
            return None

        except Exception as e:
            logger.error(f"Error finding rack/trailer column in table {table_name}: {e}")
            return None

    def _get_last_available_date(
        self,
        clickhouse_table_name: str,
        datetime_column: Optional[str],
        where_conditions: Optional[List[str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        before_date: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the most recent date/time from table, optionally limited to dates before a reference date.

        Args:
            clickhouse_table_name: ClickHouse table name
            datetime_column: DateTime column to query
            where_conditions: Optional WHERE conditions (excluding date filters)
            query_params: Optional query parameters
            before_date: Optional reference date (YYYY-MM-DD format). If provided, finds MAX date <= before_date.
                        If None, finds overall MAX date in table.

        Returns:
            ISO format datetime string (YYYY-MM-DD) or None if no data
        """
        if not datetime_column:
            logger.warning(f"No datetime column provided for table {clickhouse_table_name}")
            return None

        try:
            import os
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            # Use UTC for date extraction since data is stored in UTC
            # The returned date will be used in UTC context for fallback queries

            # Build query to get the MAX datetime using aggregate function
            # Convert to UTC first, then extract date - handle String, DateTime, and DateTime64 types
            query = f"""
            SELECT MAX(toDate(
                toTimeZone(
                    if(toTypeName(`{datetime_column}`) LIKE '%%String%%',
                    parseDateTime64BestEffort(`{datetime_column}`),
                    if(toTypeName(`{datetime_column}`) LIKE '%%DateTime64%%',
                    `{datetime_column}`,
                    toDateTime64(`{datetime_column}`, 3)
                    )
                    ),
                    'UTC'
                )
            )) as max_date
            FROM `{database}`.`{clickhouse_table_name}`
            """

            # Build WHERE conditions list
            where_parts = []

            # Add non-date WHERE conditions if provided
            if where_conditions:
                # Filter out date-related conditions
                non_date_conditions = []
                for condition in where_conditions:
                    if datetime_column not in condition:
                        non_date_conditions.append(condition)

                if non_date_conditions:
                    where_parts.extend(non_date_conditions)

            # Add before_date constraint if provided
            if before_date:
                # Convert before_date to UTC datetime for comparison
                # before_date is expected to be in YYYY-MM-DD format (user timezone)
                # Convert to UTC for comparison with stored data
                before_date_utc = self._convert_user_date_string_to_utc(before_date + ' 23:59:59')
                if before_date_utc:
                    # Handle String, DateTime, and DateTime64 types correctly
                    datetime_conversion_utc = f"""if(toTypeName(`{datetime_column}`) LIKE '%%String%%',
                    parseDateTime64BestEffort(`{datetime_column}`),
                    if(toTypeName(`{datetime_column}`) LIKE '%%DateTime64%%',
                    `{datetime_column}`,
                    toDateTime64(`{datetime_column}`, 3)
                    )
                    )""".strip().replace('\n', ' ')
                    where_parts.append(f"{datetime_conversion_utc} <= toDateTime64({{before_date:String}}, 3, 'UTC')")
                    if query_params is None:
                        query_params = {}
                    query_params['before_date'] = before_date_utc

            # Add WHERE clause if we have any conditions
            if where_parts:
                query += " WHERE " + " AND ".join(where_parts)

            result = execute_clickhouse_query(query, params=query_params)

            if result.result_rows and result.result_rows[0][0]:
                last_date = result.result_rows[0][0]
                # Convert to string in YYYY-MM-DD format
                if hasattr(last_date, 'strftime'):
                    return last_date.strftime('%Y-%m-%d')
                else:
                    return str(last_date)

            logger.warning(f"No data found in table {clickhouse_table_name}")
            return None

        except Exception as e:
            logger.error(f"Error getting last available date from {clickhouse_table_name}: {e}")
            return None

    def _check_data_exists_in_range(
        self,
        clickhouse_table_name: str,
        where_conditions: List[str],
        query_params: Dict[str, Any]
    ) -> bool:
        """
        Check if any data exists for the given conditions.

        Args:
            clickhouse_table_name: ClickHouse table name
            where_conditions: WHERE conditions to check
            query_params: Query parameters

        Returns:
            True if data exists, False otherwise
        """
        try:
            import os
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            query = f"SELECT COUNT(*) FROM `{database}`.`{clickhouse_table_name}`"

            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)

            result = execute_clickhouse_query(query, params=query_params)

            count = result.result_rows[0][0] if result.result_rows else 0
            return count > 0

        except Exception as e:
            logger.error(f"Error checking data existence in {clickhouse_table_name}: {e}")
            return False

    def get_column_data_for_table(self, clickhouse_table_name: str, column_names: List[str],
                             datetime_column: Optional[str] = None,
                             where_conditions: Optional[List[str]] = None,
                             query_params: Optional[Dict[str, Any]] = None,
                             limit: Optional[int] = None,
                             offset: Optional[int] = None,
                             group_by_columns: Optional[List[str]] = None,
                             aggregations: Optional[Dict[str, str]] = None,
                             enable_fallback: bool = True) -> Dict[str, Any]:
        """
        Get data for multiple columns from a single ClickHouse table with optional auto-fallback for missing data.

        This method provides flexible data retrieval with intelligent fallback behavior for different API types.
        When no data exists for a requested date range, the behavior depends on the enable_fallback parameter.

        Auto-Fallback Logic:
            When enable_fallback=True (default):
                - If requested date range has no data, automatically looks for data in the 7 days
                  immediately before the requested start date
                - If data exists in that 7-day window before the requested start, uses that range as fallback
                - If no data exists in the 7-day window before requested start, returns empty result
                - Returns metadata indicating data_availability_for_given_date=False when fallback is applied
                - Updates from_date and to_date to reflect the fallback range used
                - Logs warning about fallback application

            When enable_fallback=False:
                - If requested date range has no data, returns empty result_rows
                - Returns metadata indicating data_availability_for_given_date=False
                - Maintains original from_date and to_date in metadata
                - Logs info message about disabled fallback

        Args:
            clickhouse_table_name (str): Name of the ClickHouse table to query
            column_names (List[str]): List of column names to retrieve from the table
            datetime_column (Optional[str]): Datetime column name for ordering and date filtering.
                                            If provided, used for time-based queries and sorting.
            where_conditions (Optional[List[str]]): List of WHERE clause conditions.
                                                   Use parameterized placeholders like {param:Type}.
            query_params (Optional[Dict[str, Any]]): Dictionary of query parameters for WHERE conditions.
                                                     Keys should match placeholders in where_conditions.
            limit (Optional[int]): Maximum number of rows to return. Applied at database level.
            offset (Optional[int]): Number of rows to skip for pagination. Applied at database level.
            group_by_columns (Optional[List[str]]): List of column names for GROUP BY clause.
                                                   Requires aggregations parameter if specified.
            aggregations (Optional[Dict[str, str]]): Dictionary mapping column names to aggregation functions.
                                                    Example: {"temperature": "AVG", "pressure": "MAX"}
                                                    Common functions: AVG, SUM, MAX, MIN, COUNT
            enable_fallback (bool): Controls automatic 7-day fallback behavior when no data found.
                                  Default: True (maintains backward compatibility)
                                  - True: Enable automatic fallback to 7 days before requested start date
                                  - False: Return empty result without fallback

        Returns:
            Dict[str, Any]: Dictionary containing query results and metadata:
                {
                    "result_rows": List[Tuple]: List of tuples containing query result rows.
                                               Each tuple represents one row of data.
                    "data_availability_for_given_date": bool: Indicates whether data was found
                                                             for the originally requested date range.
                                                             False if fallback was applied or no data exists.
                    "from_date": str: Actual start date used in YYYY-MM-DD format.
                                    May differ from requested if fallback was applied.
                    "to_date": str: Actual end date used in YYYY-MM-DD format.
                                  May differ from requested if fallback was applied.
                }

        Raises:
            Exception: If ClickHouse query execution fails due to:
                      - Invalid table name
                      - Invalid column names
                      - Malformed WHERE conditions
                      - Database connection errors
                      - Query timeout
                      - Insufficient permissions

        Note:
            API-Specific Usage Patterns:

            Dashboard APIs (default behavior):
                Use enable_fallback=True (default) to ensure dashboards always display data.
                When requested data is unavailable, shows 7 days of data before the requested start date.
                Example: dash_001.py, dash_002.py services use default parameter.

            Analysis APIs (no fallback):
                Use enable_fallback=False to provide transparent, predictable data retrieval.
                Returns empty result when requested date range has no data.
                Users get clear feedback about data availability.
                Example: clickhouse_fetch_latest_handler.py passes enable_fallback=False

            Widgets APIs (no fallback):
                Use enable_fallback=False to avoid confusing date range mismatches.
                Returns empty dataSource arrays when requested data is unavailable.
                Widget structure and metadata are preserved.
                Example: clickhouse_adls_service.py passes enable_fallback=False

        Examples:
            Basic query with fallback enabled (default):
                >>> result = repository.get_column_data_for_table(
                ...     clickhouse_table_name="plant_data",
                ...     column_names=["DateTime", "Temperature", "Pressure"],
                ...     datetime_column="DateTime",
                ...     where_conditions=["`DateTime` >= {start:DateTime}"],
                ...     query_params={"start": "2025-01-01"}
                ... )
                >>> print(result["data_availability_for_given_date"])
                True  # or False if fallback was applied

            Query with fallback disabled (Analysis/Widgets APIs):
                >>> result = repository.get_column_data_for_table(
                ...     clickhouse_table_name="analysis_data",
                ...     column_names=["Value"],
                ...     enable_fallback=False
                ... )
                >>> if len(result["result_rows"]) == 0:
                ...     print("No data available for requested range")

            Aggregated query with grouping:
                >>> result = repository.get_column_data_for_table(
                ...     clickhouse_table_name="sensor_data",
                ...     column_names=["site", "avg_temp"],
                ...     group_by_columns=["site"],
                ...     aggregations={"avg_temp": "AVG"}
                ... )

        See Also:
            - _get_last_available_date: Helper method for finding last available data
            - _check_data_exists_in_range: Helper method for checking data existence
            - constants.ENABLE_FALLBACK_FOR_ANALYSIS_APIS: Constant for Analysis API fallback setting
            - constants.ENABLE_FALLBACK_FOR_WIDGETS_APIS: Constant for Widgets API fallback setting
        """
        try:
            timezone = self._get_timezone()
            
            # Ensure datetime_column is a string or None, never a list
            if isinstance(datetime_column, list):
                datetime_column = datetime_column[0] if datetime_column else None
                logger.warning(f"datetime_column was passed as list, using first element: {datetime_column}")
            
            # If datetime_column not provided, try to detect it
            if not datetime_column:
                datetime_column = self.get_datetime_column(clickhouse_table_name)
            
            # Validate that we have columns to select
            if not column_names:
                raise Exception(
                    f"No column names provided for table {clickhouse_table_name}. "
                    f"Cannot build SELECT query without columns."
                )
            
            # Filter out internal tracking columns from column_names
            column_names = [col for col in column_names if col not in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS]
            
            # Build column list for SELECT
            select_columns = []

            # Add datetime column with smart conversion using runtime type checking
            # Convert to user timezone (formatting handled in Python to avoid query issues)
            if datetime_column and not group_by_columns:
                # Use ClickHouse if() to check type at runtime and apply appropriate conversion
                # Handle String, DateTime, and DateTime64 types correctly, then convert timezone
                datetime_select_final = f"""toTimeZone(
                    if(toTypeName(`{datetime_column}`) LIKE '%%String%%',
                    parseDateTime64BestEffort(`{datetime_column}`),
                    if(toTypeName(`{datetime_column}`) LIKE '%%DateTime64%%',
                    `{datetime_column}`,
                    toDateTime64(`{datetime_column}`, 3)
                    )
                    ),
                    '{timezone}'
                ) as `{datetime_column}`""".strip().replace('\n', ' ')
                select_columns.append(datetime_select_final)

            # Handle aggregation vs regular column selection
            if group_by_columns and aggregations:
                # Add GROUP BY columns first
                for group_col in group_by_columns:
                    if group_col == datetime_column:
                        # Convert datetime to user timezone (formatting handled in Python)
                        # Handle String, DateTime, and DateTime64 types correctly
                        datetime_select = f"""toTimeZone(
                            if(toTypeName(`{group_col}`) LIKE '%%String%%',
                            parseDateTime64BestEffort(`{group_col}`),
                            if(toTypeName(`{group_col}`) LIKE '%%DateTime64%%',
                            `{group_col}`,
                            toDateTime64(`{group_col}`, 3)
                            )
                            ),
                            '{timezone}'
                        ) as `{group_col}`""".strip().replace('\n', ' ')
                        select_columns.append(datetime_select)
                    else:
                        select_columns.append(f"`{group_col}`")

                # Add aggregated columns
                for col_name in column_names:
                    if col_name in aggregations:
                        agg_func = aggregations[col_name].upper()
                        # Validate aggregation function to prevent SQL injection
                        if agg_func in ['SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'STDDEV']:
                            select_columns.append(f"{agg_func}(`{col_name}`) as {col_name}_{agg_func.lower()}")
                        else:
                            logger.warning(f"Invalid aggregation function '{agg_func}' for column '{col_name}', skipping")
                    else:
                        # For non-aggregated columns in GROUP BY context, just include them
                        if col_name in group_by_columns:
                            select_columns.append(f"`{col_name}`")
                        else:
                            logger.warning(f"Column '{col_name}' not in GROUP BY and no aggregation specified, skipping")
            else:
                # Regular column selection without aggregation
                for col_name in column_names:
                        select_columns.append(f"`{col_name}`")

            # Validate that we have at least one column to select
            if not select_columns:
                raise Exception(
                    f"No columns to select for table {clickhouse_table_name}. "
                    f"column_names={column_names}, datetime_column={datetime_column}, "
                    f"group_by_columns={group_by_columns}, aggregations={aggregations}"
                )

            # Get database name for proper context
            import os
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            query = f"SELECT {', '.join(select_columns)} FROM `{database}`.`{clickhouse_table_name}`"

            # Process WHERE conditions with UTC comparison
            # Data is stored in UTC, and parameters are in UTC, so compare in UTC
            if where_conditions:
                processed_conditions = []
                for condition in where_conditions:
                    # CRITICAL FIX: Ensure datetime_column is a string before using 'in' operator
                    if datetime_column and isinstance(datetime_column, str) and datetime_column in condition:
                        modified_condition = condition

                        # Handle {param:DateTime} or {param:DateTime64} or {param:String} parameters
                        # Parameters are already in UTC from service layer, so use UTC timezone
                        import re
                        datetime_params = re.findall(r'\{(\w+):(DateTime\d*|String)\}', condition)
                        for param_name, param_type in datetime_params:
                            # Replace the parameter placeholder with UTC timezone
                            # Parameters from service layer are already UTC strings
                            # Use DateTime64 for consistency
                            old_placeholder = f'{{{param_name}:{param_type}}}'
                            new_placeholder = f"toDateTime64({{{param_name}:String}}, 3, 'UTC')"
                            modified_condition = modified_condition.replace(old_placeholder, new_placeholder)

                            # Convert the actual parameter value to string format if it exists
                            if query_params and param_name in query_params:
                                param_value = query_params[param_name]
                                if hasattr(param_value, 'strftime'):
                                    query_params[param_name] = param_value.strftime('%Y-%m-%d %H:%M:%S')

                        # For WHERE conditions, data is stored in UTC, so compare directly
                        # Handle String, DateTime, and DateTime64 types correctly
                        # Parameters are already in UTC from service layer
                        datetime_conversion_utc = f"""if(toTypeName(`{datetime_column}`) LIKE '%String%',
                        parseDateTime64BestEffort(`{datetime_column}`),
                        if(toTypeName(`{datetime_column}`) LIKE '%DateTime64%',
                        `{datetime_column}`,
                        toDateTime64(`{datetime_column}`, 3)
                        )
                        )""".strip().replace('\n', ' ')
                        modified_condition = modified_condition.replace(
                            f"`{datetime_column}`",
                            datetime_conversion_utc
                        )
                        processed_conditions.append(modified_condition)
                    else:
                        # No datetime column in this condition
                        processed_conditions.append(condition)

                query += " WHERE " + " AND ".join(processed_conditions)

            # Add GROUP BY if specified
            if group_by_columns:
                group_by_clause = ", ".join([f"`{col}`" for col in group_by_columns])
                query += f" GROUP BY {group_by_clause}"

                # Add ORDER BY for GROUP BY queries
                query += f" ORDER BY {group_by_clause}"
            else:
                # Add ordering for non-aggregated queries
                # ORDER BY must use the original datetime column (not formatted string)
                # Use UTC conversion for consistent ordering - handle String, DateTime, and DateTime64 types
                if datetime_column:
                    datetime_order_expr = f"""toTimeZone(
                        if(toTypeName(`{datetime_column}`) LIKE '%%String%%',
                        parseDateTime64BestEffort(`{datetime_column}`),
                        if(toTypeName(`{datetime_column}`) LIKE '%%DateTime64%%',
                        `{datetime_column}`,
                        toDateTime64(`{datetime_column}`, 3)
                        )
                        ),
                        'UTC'
                    )""".strip().replace('\n', ' ')
                    query += f" ORDER BY {datetime_order_expr} ASC"

            # Add limit if specified
            if limit:
                query += f" LIMIT {limit}"

            if offset:
                query += f" OFFSET {offset}"

            # Execute query
            result = execute_clickhouse_query(query, params=query_params)

            # Initialize metadata
            data_availability_for_given_date = True
            from_date = None
            to_date = None

            # Extract original date parameters if they exist
            if query_params:
                from_date = query_params.get('start_date') or query_params.get('from_date')
                to_date = query_params.get('end_date') or query_params.get('to_date')

                # Convert datetime objects to string format
                if from_date and hasattr(from_date, 'strftime'):
                    from_date = from_date.strftime('%Y-%m-%d')
                elif from_date and isinstance(from_date, str) and len(from_date) > 10:
                    from_date = from_date[:10]  # Extract YYYY-MM-DD

                if to_date and hasattr(to_date, 'strftime'):
                    to_date = to_date.strftime('%Y-%m-%d')
                elif to_date and isinstance(to_date, str) and len(to_date) > 10:
                    to_date = to_date[:10]  # Extract YYYY-MM-DD

            # Check if we need to apply auto-fallback logic
            has_datetime_filtering = (
                datetime_column and 
                isinstance(datetime_column, str) and 
                where_conditions and 
                query_params and 
                any(datetime_column in condition for condition in where_conditions)
            )

            if len(result.result_rows) == 0 and has_datetime_filtering:
                if enable_fallback:
                    logger.warning(
                        f"No data found for requested date range in {clickhouse_table_name}, applying auto-fallback",
                        extra={
                            "table": clickhouse_table_name,
                            "from_date": from_date,
                            "to_date": to_date,
                            "enable_fallback": True,
                            "action": "applying_fallback"
                        }
                    )

                    # Calculate fallback date range: 7 days before requested start date
                    last_available_date = None
                    fallback_from_date = None
                    fallback_to_date = None

                    if not from_date:
                        logger.warning(f"Cannot apply fallback: no from_date available in query_params")
                    else:
                        # Parse requested start date
                        requested_start = dt.strptime(from_date, '%Y-%m-%d')
                        
                        # Calculate fallback range: 7 days before requested start date
                        fallback_end_date = (requested_start - timedelta(days=1)).strftime('%Y-%m-%d')  # Day before requested start
                        fallback_start_date = (requested_start - timedelta(days=CLICKHOUSE_FALLBACK_DAYS)).strftime('%Y-%m-%d')  # 7 days before

                        # Check if data exists in the 7-day window before requested start date
                        last_available_date = self._get_last_available_date(
                            clickhouse_table_name=clickhouse_table_name,
                            datetime_column=datetime_column,
                            where_conditions=where_conditions,
                            query_params=query_params,
                            before_date=fallback_end_date  # Find MAX date <= fallback_end_date
                        )

                        if last_available_date:
                            # Use the last available date to determine fallback range
                            last_date_obj = dt.strptime(last_available_date, '%Y-%m-%d')
                            fallback_start_obj = dt.strptime(fallback_start_date, '%Y-%m-%d')
                            
                            if last_date_obj >= fallback_start_obj:
                                # Data exists in the 7-day window before requested start
                                # Use the actual last available date as fallback end (may be less than fallback_end_date)
                                fallback_to_date = last_available_date
                                fallback_from_date = fallback_start_date
                                
                                logger.info(f"Auto-fallback: Using date range {fallback_from_date} to {fallback_to_date} (7 days before requested start {from_date})")
                            else:
                                # Data exists but is older than 7 days before requested start
                                # Show the last 7 days of available data ending at last_available_date
                                fallback_to_date = last_available_date
                                fallback_from_date = (last_date_obj - timedelta(days=CLICKHOUSE_FALLBACK_DAYS - 1)).strftime('%Y-%m-%d')
                                
                                logger.info(
                                    f"Auto-fallback: Using last 7 days of available data {fallback_from_date} to {fallback_to_date} "
                                    f"(data is older than 7 days before requested start {from_date})",
                                    extra={
                                        "table": clickhouse_table_name,
                                        "requested_start": from_date,
                                        "fallback_window": f"{fallback_start_date} to {fallback_end_date}",
                                        "last_available": last_available_date,
                                        "actual_fallback": f"{fallback_from_date} to {fallback_to_date}",
                                        "action": "fallback_using_older_data"
                                    }
                                )
                        else:
                            logger.warning(
                                f"No data available before requested start date {from_date}",
                                extra={
                                    "table": clickhouse_table_name,
                                    "requested_start": from_date,
                                    "fallback_window": f"{fallback_start_date} to {fallback_end_date}",
                                    "action": "fallback_no_data_before"
                                }
                            )

                    if last_available_date and fallback_from_date and fallback_to_date:

                        # Step 2: Build new WHERE conditions with fallback dates
                        # We need to replace original date conditions with fallback date range
                        new_where_conditions = []
                        new_query_params = query_params.copy() if query_params else {}

                        # Step 3: Filter out original date conditions and preserve other conditions
                        # We identify date conditions by checking if they reference the datetime_column
                        for condition in where_conditions:
                            if datetime_column in condition:
                                # Skip original date conditions - they'll be replaced with fallback dates
                                continue
                            else:
                                # Preserve non-date conditions (e.g., rack filters, site filters)
                                new_where_conditions.append(condition)

                        # Add new date range conditions
                        # Use UTC for comparison since data is stored in UTC
                        # Handle String, DateTime, and DateTime64 types correctly
                        datetime_conversion_utc = f"""if(toTypeName(`{datetime_column}`) LIKE '%%String%%',
                        parseDateTime64BestEffort(`{datetime_column}`),
                        if(toTypeName(`{datetime_column}`) LIKE '%%DateTime64%%',
                        `{datetime_column}`,
                        toDateTime64(`{datetime_column}`, 3)
                        )
                        )""".strip().replace('\n', ' ')

                        # Fallback dates are in UTC context (from _get_last_available_date which uses UTC)
                        # Use UTC timezone for comparison with DateTime64
                        new_where_conditions.append(
                            f"{datetime_conversion_utc} >= toDateTime64({{fallback_start:String}}, 3, 'UTC') " +
                            f"AND {datetime_conversion_utc} <= toDateTime64({{fallback_end:String}}, 3, 'UTC')"
                        )

                        # Append time to date strings - these are treated as UTC times
                        new_query_params['fallback_start'] = fallback_from_date + ' 00:00:00'
                        new_query_params['fallback_end'] = fallback_to_date + ' 23:59:59'

                        # Rebuild query with new conditions
                        import os
                        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
                        # Ensure select_columns is not empty for fallback query
                        if not select_columns:
                            raise Exception(
                                f"No columns to select for fallback query on table {clickhouse_table_name}. "
                                f"column_names={column_names}, datetime_column={datetime_column}"
                            )
                        fallback_query = f"SELECT {', '.join(select_columns)} FROM `{database}`.`{clickhouse_table_name}`"

                        # Add WHERE clause if conditions exist
                        if new_where_conditions:
                            fallback_query += " WHERE " + " AND ".join(new_where_conditions)

                        # Add GROUP BY and ORDER BY clauses based on query type
                        if group_by_columns:
                            # Aggregated query: group and order by grouping columns
                            group_by_clause = ", ".join([f"`{col}`" for col in group_by_columns])
                            fallback_query += f" GROUP BY {group_by_clause}"
                            fallback_query += f" ORDER BY {group_by_clause}"
                        else:
                            # Regular query: order by datetime column for chronological results
                            if datetime_column and isinstance(datetime_column, str):
                                fallback_query += f" ORDER BY `{datetime_column}` ASC"

                        # Apply pagination parameters if specified
                        if limit:
                            fallback_query += f" LIMIT {limit}"
                        if offset:
                            fallback_query += f" OFFSET {offset}"

                        # Step 6: Execute fallback query with new date range
                        result = execute_clickhouse_query(fallback_query, params=new_query_params)

                        # Step 7: Update metadata to reflect fallback was applied
                        # This signals to callers that returned data is NOT from original requested range
                        data_availability_for_given_date = False  # Original date range had no data
                        from_date = fallback_from_date  # Actual start date used (fallback)
                        to_date = fallback_to_date      # Actual end date used (fallback)

                        logger.info(
                            f"Auto-fallback successful: Retrieved {len(result.result_rows)} rows from {fallback_from_date} to {fallback_to_date}",
                            extra={
                                "table": clickhouse_table_name,
                                "fallback_from_date": fallback_from_date,
                                "fallback_to_date": fallback_to_date,
                                "rows_retrieved": len(result.result_rows),
                                "action": "fallback_successful"
                            }
                        )
                    else:
                        # No data found in 7-day window before requested start date
                        # This case is already logged above, but we keep this for consistency
                        logger.warning(
                            f"No data available in 7-day window before requested start date for auto-fallback",
                            extra={
                                "table": clickhouse_table_name,
                                "requested_start": from_date if from_date else "unknown",
                                "action": "fallback_failed_no_data_in_window"
                            }
                        )
                else:
                    # Fallback is disabled - return empty result with appropriate logging
                    logger.info(
                        f"No data found for requested date range in {clickhouse_table_name}, fallback disabled - returning empty result",
                        extra={
                            "table": clickhouse_table_name,
                            "from_date": from_date,
                            "to_date": to_date,
                            "enable_fallback": False,
                            "action": "fallback_disabled_empty_result"
                        }
                    )

            logger.info(f"Retrieved {len(result.result_rows)} rows for columns {column_names} from table {clickhouse_table_name}" +
                    (f" with aggregation" if aggregations else "") +
                    f" (timezone: {timezone}, smart datetime conversion, data_available: {data_availability_for_given_date})")

            return {
                "result_rows": result.result_rows,
                "data_availability_for_given_date": data_availability_for_given_date,
                "from_date": from_date,
                "to_date": to_date
            }

        except Exception as e:
            logger.error(f"Error retrieving column data from table {clickhouse_table_name}: {e}")
            raise Exception(f"Failed to retrieve column data: {str(e)}")

    def get_count_for_table(self, clickhouse_table_name: str,
                           where_conditions: Optional[List[str]] = None,
                           query_params: Optional[Dict[str, Any]] = None) -> int:
        """
        Get total count of rows in a table matching WHERE conditions.
        Enables efficient database-level pagination without loading all data.

        Args:
            clickhouse_table_name: ClickHouse table name
            where_conditions: Optional WHERE conditions
            query_params: Optional query parameters as dictionary

        Returns:
            Total count of rows matching conditions

        Raises:
            Exception: If query execution fails
        """
        try:
            query = f"SELECT COUNT(*) FROM `{clickhouse_table_name}`"

            # Add WHERE conditions if provided
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)

            # Execute query
            result = execute_clickhouse_query(query, params=query_params)

            count = result.result_rows[0][0] if result.result_rows else 0
            logger.info(f"Counted {count} rows in table {clickhouse_table_name}")
            return count

        except Exception as e:
            logger.error(f"Error counting rows in table {clickhouse_table_name}: {e}")
            raise Exception(f"Failed to count rows: {str(e)}")

    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        """
        Get the data type of a specific column.
        
        Args:
            table_name: ClickHouse table name
            column_name: Column name
            
        Returns:
            Column type string or None if not found
        """
        try:
            query = """
            SELECT type
            FROM system.columns
            WHERE table = {table_name:String} AND name = {column_name:String}
            """
            
            result = execute_clickhouse_query(query, params={
                "table_name": table_name, 
                "column_name": column_name
            })
            
            if result.result_rows:
                return result.result_rows[0][0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting column type for {table_name}.{column_name}: {e}")
            return None

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get column information for a specific table.

        Args:
            table_name (str): Name of the table

        Returns:
            List[Dict[str, Any]]: List of column dictionaries with name, type, and nullable info

        Raises:
            Exception: If query execution fails or table name is invalid
        """
        try:
            # Validate table name to prevent SQL injection
            validated_table_name = validate_table_name(table_name)

            query = """
            SELECT name, type, default_kind, default_expression
            FROM system.columns
            WHERE database = currentDatabase()
            AND table = {table_name:String}
            ORDER BY position
            """

            result = execute_clickhouse_query(query, params={"table_name": validated_table_name})

            # Convert result to list of dictionaries
            columns = []
            for row in result.result_rows:
                column_name = row[0]
                # Skip internal tracking columns
                if column_name in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS:
                    continue
                column_info = {
                    "name": column_name,
                    "type": row[1],
                    "nullable": self._determine_nullable(row[1], row[2])
                }
                columns.append(column_info)

            logger.info(f"Retrieved {len(columns)} columns for table '{table_name}'")
            return columns

        except Exception as e:
            logger.error(f"Failed to retrieve columns for table '{table_name}': {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to retrieve columns for table '{table_name}': {str(e)}"))

    def get_tables_with_columns(self) -> List[Dict[str, Any]]:
        """
        Get all tables with their column information using a single optimized query.

        Returns:
            List[Dict[str, Any]]: List of table dictionaries with name and columns

        Raises:
            Exception: If query execution fails
        """
        try:
            # Single optimized query to get all tables and columns using ClickHouse-compatible columns
            query = """
            SELECT
                table,
                name as column_name,
                type as column_type,
                default_kind
            FROM system.columns
            WHERE database = currentDatabase()
            ORDER BY table, position
            """

            result = execute_clickhouse_query(query)

            # Process results into the expected data structure
            tables_dict = {}

            for row in result.result_rows:
                table_name = row[0]
                column_name = row[1]
                column_type = row[2]
                default_kind = row[3]

                # Skip internal tracking columns
                if column_name in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS:
                    continue

                # Initialize table entry if not exists
                if table_name not in tables_dict:
                    tables_dict[table_name] = []

                # Add column information with proper nullable detection
                column_info = {
                    "name": column_name,
                    "type": column_type,
                    "nullable": self._determine_nullable(column_type, default_kind)
                }
                tables_dict[table_name].append(column_info)

            # Convert to expected list format
            tables_with_columns = []
            for table_name, columns in tables_dict.items():
                table_info = {
                    "table_name": table_name,
                    "columns": columns
                }
                tables_with_columns.append(table_info)

            # Sort by table name for consistent ordering
            tables_with_columns.sort(key=lambda x: x["table_name"])

            logger.info(f"Retrieved {len(tables_with_columns)} tables with column information using optimized single query")
            return tables_with_columns

        except Exception as e:
            logger.error(f"Failed to retrieve tables with columns: {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to retrieve tables with columns: {str(e)}"))

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the current database.

        Args:
            table_name (str): Name of the table to check

        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            # Validate table name to prevent SQL injection
            validated_table_name = validate_table_name(table_name)

            query = """
            SELECT count()
            FROM system.tables
            WHERE database = currentDatabase()
            AND name = {table_name:String}
            """

            result = execute_clickhouse_query(query, params={"table_name": validated_table_name})

            # Check if count is greater than 0
            count = result.result_rows[0][0] if result.result_rows else 0
            exists = count > 0

            logger.debug(f"Table '{table_name}' exists: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Failed to check if table '{table_name}' exists: {str(e)}")
            # Return False on error to be safe
            return False

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get basic information about the current ClickHouse database.

        Returns:
            Dict[str, Any]: Database information including name, table count, and connection status
        """
        try:
            # Get current database name
            db_query = "SELECT currentDatabase() as database_name"
            db_result = execute_clickhouse_query(db_query)
            database_name = db_result.result_rows[0][0] if db_result.result_rows else "unknown"

            # Get table count
            count_query = "SELECT count() FROM system.tables WHERE database = currentDatabase()"
            count_result = execute_clickhouse_query(count_query)
            table_count = count_result.result_rows[0][0] if count_result.result_rows else 0

            info = {
                "database_name": database_name,
                "table_count": table_count,
                "connection_successful": True
            }

            logger.info(f"Database info retrieved: {info}")
            return info

        except Exception as e:
            logger.error(f"Failed to retrieve database info: {str(e)}")
            return {
                "database_name": "unknown",
                "table_count": 0,
                "connection_successful": False,
                "error": str(e)
            }

    def get_column_data(self, table_name: str, column_name: str, limit: int = 1000) -> Dict[str, Any]:
        """
        Get actual data from a specific column in a ClickHouse table.

        Args:
            table_name (str): Name of the table
            column_name (str): Name of the column
            limit (int): Maximum number of rows to retrieve (default: 1000)

        Returns:
            Dict[str, Any]: Dictionary containing column data and metadata

        Raises:
            Exception: If query execution fails or table/column doesn't exist
        """
        try:
            # Validate table and column names
            validated_table_name = validate_table_name(table_name)

            # Validate column name (basic validation to prevent injection)
            if not re.match(ClickHouseDataValidation.COLUMN_NAME_REGEX, column_name):
                raise ValueError(f"Invalid column name: {column_name}")

            # First check if table exists
            if not self.table_exists(table_name):
                raise Exception(f"Table '{table_name}' does not exist")

            # Reject internal tracking columns
            if column_name in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS:
                raise ValueError(f"Column '{column_name}' is not accessible for data retrieval (internal tracking column)")

            # Get column metadata to verify column exists and get type
            columns = self.get_table_columns(table_name)
            column_info = next((col for col in columns if col["name"] == column_name), None)

            if not column_info:
                raise Exception(f"Column '{column_name}' does not exist in table '{table_name}'")

            # Get database name for proper context
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            # Get actual column data using parameterized query
            query = f"""
            SELECT `{column_name}`
            FROM `{database}`.`{validated_table_name}`
            LIMIT {limit}
            """

            result = execute_clickhouse_query(query)

            # Extract data from result
            data_source = [row[0] for row in result.result_rows]

            # Get row count
            count_query = f"SELECT count() FROM `{database}`.`{validated_table_name}`"
            count_result = execute_clickhouse_query(count_query)
            total_rows = count_result.result_rows[0][0] if count_result.result_rows else 0

            response_data = {
                "table_name": table_name,
                "column_name": column_name,
                "data_source": data_source,
                "data_type": column_info["type"],
                "row_count": len(data_source),
                "total_rows_in_table": total_rows
            }

            logger.info(f"Retrieved {len(data_source)} rows for column '{column_name}' from table '{table_name}'")
            return response_data

        except Exception as e:
            logger.error(f"Failed to retrieve column data for '{table_name}.{column_name}': {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to retrieve column data for '{table_name}.{column_name}': {str(e)}"))

    def get_column_data_with_enhanced_filters(self, 
                                   table_name: str, 
                                   column_name: str, 
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None,
                                   racks: Optional[List[str]] = None,
                                   filtering_mode: str = 'default',
                                   limit: int = 1000) -> Dict[str, Any]:
        """
        Get filtered data from a specific column in a ClickHouse table with enhanced datetime filtering modes.

        Enhanced DateTime Filtering Modes:
        - Range Filtering: When both start_date and end_date are provided
        - Exact Match: When only one date parameter is provided (full day range)
        - Default Range: When no dates are provided (last 7 days)

        DateTime Formats Supported:
        - Comma-separated: 2025-06-01,10:00:00
        - Standard: 2025-06-01 10:00:00
        - Date-only: 2025-06-01
        - ISO format: 2025-04-03T00:59:00Z

        Args:
            table_name (str): Name of the table
            column_name (str): Name of the column
            start_date (Optional[datetime]): Start date for filtering (processed by serializer)
            end_date (Optional[datetime]): End date for filtering (processed by serializer)
            racks (Optional[List[str]]): List of rack names for filtering
            filtering_mode (str): Filtering mode ('range', 'exact', 'default')
            limit (int): Maximum number of rows to retrieve (default: 1000)

        Returns:
            Dict[str, Any]: Dictionary containing filtered column data and metadata

        Raises:
            Exception: If query execution fails or table/column doesn't exist
        """
        try:
            timezone = self._get_timezone()
            
            # Validate table and column names
            validated_table_name = validate_table_name(table_name)

            # Validate column name (basic validation to prevent injection)
            if not re.match(ClickHouseDataValidation.COLUMN_NAME_REGEX, column_name):
                raise ValueError(f"Invalid column name: {column_name}")

            # Reject internal tracking columns
            if column_name in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS:
                raise ValueError(f"Column '{column_name}' is not accessible for data retrieval (internal tracking column)")

            # First check if table exists
            if not self.table_exists(table_name):
                raise Exception(f"Table '{table_name}' does not exist")

            # Get column metadata to verify column exists and get type
            columns = self.get_table_columns(table_name)
            column_info = next((col for col in columns if col["name"] == column_name), None)

            if not column_info:
                raise Exception(f"Column '{column_name}' does not exist in table '{table_name}'")

            # Get database name
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            # Build the enhanced filtered query with timezone support
            query_parts = []
            where_conditions = []
            params = {}
            
            # Detect if we're selecting a timestamp column
            timestamp_column = self._detect_timestamp_column(table_name)
            
            # SELECT clause - apply timezone conversion if selecting timestamp column
            # Handle String, DateTime, and DateTime64 types correctly
            if column_name == timestamp_column:
                query_parts.append(f"""SELECT toTimeZone(
                    if(toTypeName(`{column_name}`) LIKE '%%String%%',
                    parseDateTime64BestEffort(`{column_name}`),
                    if(toTypeName(`{column_name}`) LIKE '%%DateTime64%%',
                    `{column_name}`,
                    toDateTime64(`{column_name}`, 3)
                    )
                    ),
                    '{timezone}'
                ) AS `{column_name}`""".strip().replace('\n', ' '))
            else:
                query_parts.append(f"SELECT `{column_name}`")
            
            query_parts.append(f"FROM `{database}`.`{validated_table_name}`")

            # Add datetime filtering based on mode - use UTC for comparison
            # Data is stored in UTC, so convert user dates to UTC and compare in UTC
            if start_date or end_date:
                if timestamp_column:
                    # Convert user dates from Asia/Dubai to UTC
                    start_date_utc_str = self._convert_user_datetime_to_utc(start_date) if start_date else None
                    end_date_utc_str = self._convert_user_datetime_to_utc(end_date) if end_date else None
                    
                    # Build datetime conversion expression - handle String, DateTime, and DateTime64 types
                    datetime_where_expr = f"""if(toTypeName(`{timestamp_column}`) LIKE '%%String%%',
                    parseDateTime64BestEffort(`{timestamp_column}`),
                    if(toTypeName(`{timestamp_column}`) LIKE '%%DateTime64%%',
                    `{timestamp_column}`,
                    toDateTime64(`{timestamp_column}`, 3)
                    )
                    )""".strip().replace('\n', ' ')
                    
                    if filtering_mode == 'range' and start_date and end_date:
                        # Range filtering: Use UTC for comparison with DateTime64
                        where_conditions.append(
                            f"{datetime_where_expr} >= toDateTime64({{start_date:String}}, 3, 'UTC') "
                            f"AND {datetime_where_expr} <= toDateTime64({{end_date:String}}, 3, 'UTC')"
                        )
                        params["start_date"] = start_date_utc_str
                        params["end_date"] = end_date_utc_str
                        logger.debug(f"Repository: Applying range filtering from {start_date} (Asia/Dubai) -> {start_date_utc_str} (UTC) to {end_date} (Asia/Dubai) -> {end_date_utc_str} (UTC)")
                        
                    elif filtering_mode == 'exact' and start_date and end_date:
                        # Exact match: Use full day range with UTC
                        where_conditions.append(
                            f"{datetime_where_expr} >= toDateTime64({{start_date:String}}, 3, 'UTC') "
                            f"AND {datetime_where_expr} <= toDateTime64({{end_date:String}}, 3, 'UTC')"
                        )
                        params["start_date"] = start_date_utc_str
                        params["end_date"] = end_date_utc_str
                        logger.debug(f"Repository: Applying exact match filtering for full day from {start_date} (Asia/Dubai) -> {start_date_utc_str} (UTC) to {end_date} (Asia/Dubai) -> {end_date_utc_str} (UTC)")
                        
                    elif filtering_mode == 'default' and start_date and end_date:
                        # Default range: Last 7 days with UTC
                        where_conditions.append(
                            f"{datetime_where_expr} >= toDateTime64({{start_date:String}}, 3, 'UTC') "
                            f"AND {datetime_where_expr} <= toDateTime64({{end_date:String}}, 3, 'UTC')"
                        )
                        params["start_date"] = start_date_utc_str
                        params["end_date"] = end_date_utc_str
                        logger.debug(f"Repository: Applying default 7-day filtering from {start_date} (Asia/Dubai) -> {start_date_utc_str} (UTC) to {end_date} (Asia/Dubai) -> {end_date_utc_str} (UTC)")
                        
                else:
                    logger.warning(f"No timestamp column found in table '{table_name}' for datetime filtering mode: {filtering_mode}")

            # Add rack filtering if provided
            if racks and len(racks) > 0:
                rack_column = self._detect_rack_column(table_name)
                
                if rack_column:
                    # Validate rack names to prevent injection
                    validated_racks = []
                    for rack in racks:
                        if re.match(ClickHouseDataValidation.RACK_NAME_REGEX, rack):
                            validated_racks.append(rack)
                        else:
                            logger.warning(f"Skipping invalid rack name: {rack}")
                    
                    if validated_racks:
                        # Use IN clause for rack filtering
                        rack_params = []
                        for i, rack in enumerate(validated_racks):
                            rack_param = f"rack_{i}"
                            rack_params.append(f"{{{rack_param}:String}}")
                            params[rack_param] = rack
                        
                        where_conditions.append(f"{rack_column} IN ({', '.join(rack_params)})")
                        logger.debug(f"Repository: Applying rack filtering for {len(validated_racks)} racks")
                else:
                    logger.warning(f"No rack column found in table '{table_name}' for rack filtering")

            # Combine query parts
            if where_conditions:
                query_parts.append("WHERE " + " AND ".join(where_conditions))

            # Add ORDER BY for consistent results (if timestamp column exists)
            if timestamp_column:
                query_parts.append(f"ORDER BY {timestamp_column} ASC")

            # Add LIMIT
            query_parts.append(f"LIMIT {{limit:UInt32}}")
            params["limit"] = limit

            query = " ".join(query_parts)

            logger.info(f"Repository: Executing enhanced {filtering_mode} filtering query for '{table_name}.{column_name}' with timezone {timezone}")
            result = execute_clickhouse_query(query, params)

            # Extract data from result
            data_source = [row[0] for row in result.result_rows]

            # Get filtered row count for metadata
            count_query_parts = [f"SELECT count() FROM `{database}`.`{validated_table_name}`"]
            if where_conditions:
                count_query_parts.append("WHERE " + " AND ".join(where_conditions))
            
            count_query = " ".join(count_query_parts)
            count_params = {k: v for k, v in params.items() if k != "limit"}
            
            count_result = execute_clickhouse_query(count_query, count_params)
            filtered_total_rows = count_result.result_rows[0][0] if count_result.result_rows else 0

            response_data = {
                "table_name": table_name,
                "column_name": column_name,
                "data_source": data_source,
                "data_type": column_info["type"],
                "row_count": len(data_source),
                "filtered_total_rows": filtered_total_rows,
                "filters_applied": {
                    "filtering_mode": filtering_mode,
                    "start_date": DateTimeParser.format_datetime_without_timezone(start_date) if start_date else None,
                    "end_date": DateTimeParser.format_datetime_without_timezone(end_date) if end_date else None,
                    "racks": racks if racks else [],
                    "timezone": timezone
                }
            }

            logger.info(f"Repository: Retrieved {len(data_source)} filtered rows using {filtering_mode} mode for column '{column_name}' from table '{table_name}' (total filtered: {filtered_total_rows}, timezone: {timezone})")
            return response_data

        except Exception as e:
            logger.error(f"Repository: Failed to retrieve enhanced filtered column data for '{table_name}.{column_name}': {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to retrieve enhanced filtered column data for '{table_name}.{column_name}': {str(e)}"))

    def _detect_timestamp_column(self, table_name: str) -> Optional[str]:
        """
        Detect the timestamp column in a table for date filtering.

        Args:
            table_name (str): Name of the table

        Returns:
            Optional[str]: Name of the timestamp column, or None if not found
        """
        try:
            columns = self.get_table_columns(table_name)
            
            # Common timestamp column names (in order of preference)
            timestamp_candidates = ClickHouseColumnPatterns.DATETIME_CANDIDATES
            
            # Also look for columns with DateTime types
            datetime_columns = [col['name'] for col in columns 
                              if any(dt_type in col['type'].lower() 
                                   for dt_type in ['datetime', 'date', 'timestamp'])]
            
            # Check candidates first (case-insensitive)
            for candidate in timestamp_candidates:
                for col in columns:
                    if col['name'].lower() == candidate.lower():
                        logger.debug(f"Found timestamp column '{col['name']}' in table '{table_name}'")
                        return col['name']
            
            # If no candidate found, use first datetime column
            if datetime_columns:
                logger.debug(f"Using datetime column '{datetime_columns[0]}' in table '{table_name}'")
                return datetime_columns[0]
            
            logger.debug(f"No timestamp column detected in table '{table_name}'")
            return None
            
        except Exception as e:
            logger.warning(f"Error detecting timestamp column in table '{table_name}': {str(e)}")
            return None

    def _detect_rack_column(self, table_name: str) -> Optional[str]:
        """
        Detect the rack column in a table for rack filtering.

        Args:
            table_name (str): Name of the table

        Returns:
            Optional[str]: Name of the rack column, or None if not found
        """
        try:
            columns = self.get_table_columns(table_name)
            
            # Common rack column names (in order of preference)
            rack_candidates = ClickHouseColumnPatterns.RACK_CANDIDATES  # Use first 8 rack candidates
            
            # Check candidates (case-insensitive)
            for candidate in rack_candidates:
                for col in columns:
                    if col['name'].lower() == candidate.lower():
                        logger.debug(f"Found rack column '{col['name']}' in table '{table_name}'")
                        return col['name']
            
            logger.debug(f"No rack column detected in table '{table_name}'")
            return None
            
        except Exception as e:
            logger.warning(f"Error detecting rack column in table '{table_name}': {str(e)}")
            return None

    def validate_column_exists(self, table_name: str, column_name: str) -> bool:
        """
        Check if a column exists in a specific table.

        Args:
            table_name (str): Name of the table
            column_name (str): Name of the column

        Returns:
            bool: True if column exists, False otherwise
        """
        try:
            # Validate inputs
            validated_table_name = validate_table_name(table_name)

            if not re.match(ClickHouseDataValidation.COLUMN_NAME_REGEX, column_name):
                return False

            query = """
            SELECT count()
            FROM system.columns
            WHERE database = currentDatabase()
            AND table = {table_name:String}
            AND name = {column_name:String}
            """

            result = execute_clickhouse_query(query, params={
                "table_name": validated_table_name,
                "column_name": column_name
            })

            count = result.result_rows[0][0] if result.result_rows else 0
            exists = count > 0

            logger.debug(f"Column '{column_name}' in table '{table_name}' exists: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Failed to check if column '{column_name}' exists in table '{table_name}': {str(e)}")
            return False

    def get_column_data_with_validation(self, table_name: str, column_name: str, limit: int = 1000) -> Dict[str, Any]:
        """
        Optimized method that combines validation and data retrieval into fewer queries.

        Args:
            table_name (str): Name of the table
            column_name (str): Name of the column
            limit (int): Maximum number of rows to retrieve (default: 1000)

        Returns:
            Dict[str, Any]: Dictionary containing column data and metadata

        Raises:
            Exception: If table/column doesn't exist or query execution fails
        """
        try:
            # Validate table and column names
            validated_table_name = validate_table_name(table_name)

            if not re.match(ClickHouseDataValidation.COLUMN_NAME_REGEX, column_name):
                raise ValueError(f"Invalid column name: {column_name}")

            # Reject internal tracking columns
            if column_name in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS:
                raise ValueError(f"Column '{column_name}' is not accessible for data retrieval (internal tracking column)")

            # Single query to get column metadata and validate existence
            metadata_query = """
            SELECT name, type, default_kind
            FROM system.columns
            WHERE database = currentDatabase()
            AND table = {table_name:String}
            AND name = {column_name:String}
            """

            metadata_result = execute_clickhouse_query(metadata_query, params={
                "table_name": validated_table_name,
                "column_name": column_name
            })

            # Check if table and column exist
            if not metadata_result.result_rows:
                # Determine if it's a table or column issue for better error message
                table_exists_query = """
                SELECT count()
                FROM system.tables
                WHERE database = currentDatabase()
                AND name = {table_name:String}
                """
                table_check_result = execute_clickhouse_query(table_exists_query, params={"table_name": validated_table_name})
                table_exists = table_check_result.result_rows[0][0] > 0 if table_check_result.result_rows else False

                if not table_exists:
                    raise Exception(f"Table '{table_name}' does not exist")
                else:
                    raise Exception(f"Column '{column_name}' does not exist in table '{table_name}'")

            # Extract column metadata
            column_info = {
                "name": metadata_result.result_rows[0][0],
                "type": metadata_result.result_rows[0][1],
                "nullable": self._determine_nullable(metadata_result.result_rows[0][1], metadata_result.result_rows[0][2])
            }

            # Get actual column data using parameterized query
            data_query = """
            SELECT {column_name:Identifier}
            FROM {table_name:Identifier}
            LIMIT {limit:UInt32}
            """

            data_result = execute_clickhouse_query(data_query, params={
                "column_name": column_name,
                "table_name": validated_table_name,
                "limit": limit
            })

            # Extract data from result
            data_source = [row[0] for row in data_result.result_rows]

            # Get total row count in table (for metadata)
            # Get database name for proper context
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            count_query = f"SELECT count() FROM `{database}`.`{validated_table_name}`"
            count_result = execute_clickhouse_query(count_query)
            total_rows = count_result.result_rows[0][0] if count_result.result_rows else 0

            response_data = {
                "table_name": table_name,
                "column_name": column_name,
                "data_source": data_source,
                "data_type": column_info["type"],
                "row_count": len(data_source),
                "total_rows_in_table": total_rows
            }

            logger.info(f"Retrieved {len(data_source)} rows for column '{column_name}' from table '{table_name}' using optimized method")
            return response_data

        except Exception as e:
            logger.error(f"Failed to retrieve column data with validation for '{table_name}.{column_name}': {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to retrieve column data for '{table_name}.{column_name}': {str(e)}"))

    def batch_validate_columns(self, column_specs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Batch validation for multiple column specifications.

        Args:
            column_specs: List of dictionaries with 'table_name' and 'column_name' keys

        Returns:
            Dict[str, Any]: Validation results including valid/invalid specifications
        """
        try:
            if not column_specs:
                return {
                    "valid": False,
                    "errors": ["No column specifications provided"],
                    "valid_specs": [],
                    "invalid_specs": []
                }

            # Simple validation approach with individual validation per spec
            validation_results = []
            for spec in column_specs:
                table_name = spec.get("table_name", "")
                column_name = spec.get("column_name", "")

                try:
                    validated_table_name = validate_table_name(table_name)
                    if not re.match(ClickHouseDataValidation.COLUMN_NAME_REGEX, column_name):
                        validation_results.append({
                            "table_name": table_name,
                            "column_name": column_name,
                            "valid": False,
                            "error": f"Invalid column name: {column_name}"
                        })
                        continue

                    # Simple validation query per column
                    validation_query = """
                    SELECT count() as exists_count
                    FROM system.columns
                    WHERE database = currentDatabase()
                    AND table = {table_name:String}
                    AND name = {column_name:String}
                    """

                    result = execute_clickhouse_query(validation_query, params={
                        "table_name": validated_table_name,
                        "column_name": column_name
                    })

                    exists = result.result_rows[0][0] > 0 if result.result_rows else False
                    validation_results.append({
                        "table_name": table_name,
                        "column_name": column_name,
                        "valid": exists,
                        "error": None if exists else f"Table '{table_name}' or column '{column_name}' does not exist"
                    })

                except Exception as e:
                    validation_results.append({
                        "table_name": table_name,
                        "column_name": column_name,
                        "valid": False,
                        "error": str(e)
                    })

            # Process validation results
            valid_specs = [r for r in validation_results if r["valid"]]
            invalid_specs = [r for r in validation_results if not r["valid"]]
            errors = [r["error"] for r in invalid_specs if r["error"]]

            return {
                "valid": len(invalid_specs) == 0,
                "errors": errors,
                "valid_specs": [{"table_name": r["table_name"], "column_name": r["column_name"]} for r in valid_specs],
                "invalid_specs": [{"table_name": r["table_name"], "column_name": r["column_name"]} for r in invalid_specs]
            }

        except Exception as e:
            logger.error(f"Failed to perform batch validation: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Batch validation failed: {str(e)}"],
                "valid_specs": [],
                "invalid_specs": column_specs
            }

    def _convert_clickhouse_to_parquet_type(self, clickhouse_type: str) -> str:
        """
        Convert ClickHouse data type back to parquet-equivalent type.

        Args:
            clickhouse_type: ClickHouse column type string

        Returns:
            Parquet-equivalent type string
        """
        # Remove Nullable wrapper if present
        type_str = clickhouse_type
        if type_str.startswith('Nullable(') and type_str.endswith(')'):
            type_str = type_str[9:-1]  # Remove "Nullable(" and ")"

        # Map ClickHouse types back to parquet types
        type_mapping = {
            'UInt8': 'int8',
            'Int8': 'int8',
            'Int16': 'int16',
            'Int32': 'int32',
            'Int64': 'int64',
            'UInt16': 'uint16',
            'UInt32': 'uint32',
            'UInt64': 'uint64',
            'Float32': 'float',
            'Float64': 'double',
            'String': 'string',
            'Date': 'date32[day]',
            'DateTime64(6)': 'timestamp[us]',
            'DateTime64(3)': 'timestamp[ms]',
            'DateTime64(9)': 'timestamp[ns]',
        }

        # Handle DateTime64 with any precision
        if type_str.startswith('DateTime64('):
            precision = type_str[11:-1]  # Extract precision number
            if precision == '3':
                return 'timestamp[ms]'
            elif precision == '6':
                return 'timestamp[us]'
            elif precision == '9':
                return 'timestamp[ns]'
            else:
                return 'timestamp[us]'  # Default fallback

        # Return mapped type or fallback to string
        return type_mapping.get(type_str, 'string')

    def _determine_nullable(self, column_type: str, default_kind: str) -> bool:
        """
        Determine if a ClickHouse column is nullable based on its type and default configuration.

        Args:
            column_type (str): The column data type
            default_kind (str): The default kind from system.columns

        Returns:
            bool: True if column is nullable, False otherwise
        """
        try:
            # Check if type explicitly declares nullable
            if column_type.startswith("Nullable("):
                return True

            # Check default_kind for null-allowing configurations
            if default_kind in ("DEFAULT", "MATERIALIZED", "ALIAS"):
                return True

            # Default to False for non-nullable types
            return False

        except Exception as e:
            logger.warning(f"Error determining nullable status for column type '{column_type}': {str(e)}")
            # Default to False if unable to determine
            return False

    def get_rack_columns_for_table(self, table_name: str) -> List[str]:
        """
        Get columns that potentially contain rack information from a ClickHouse table.
        Uses RACK_CANDIDATES from constants.py to detect rack columns with different names.
        Uses strict pattern matching to exclude columns with non-rack suffixes like "_Name", "_ID", "_Type".

        Args:
            table_name (str): ClickHouse table name

        Returns:
            List[str]: List of column names that strictly match rack patterns from RACK_CANDIDATES

        Raises:
            Exception: If query execution fails
        """
        try:
            # Validate table name to prevent SQL injection
            validated_table_name = validate_table_name(table_name)

            # Build dynamic LIKE conditions for all RACK_CANDIDATES patterns
            # Use stricter patterns: exact match, starts with, ends with, or word boundary matches
            rack_patterns = ClickHouseColumnPatterns.RACK_CANDIDATES
            like_conditions_parts = []
            
            for pattern in rack_patterns:
                pattern_lower = pattern.lower()
                # Match exact column name (case-insensitive)
                like_conditions_parts.append(f"lower(name) = '{pattern_lower}'")
                # Match column name starting with pattern (e.g., "rack", "rack_01")
                like_conditions_parts.append(f"lower(name) LIKE '{pattern_lower}%'")
                # Match column name ending with pattern (e.g., "_rack", "train_rack")
                like_conditions_parts.append(f"lower(name) LIKE '%_{pattern_lower}'")
                # Match pattern as a word (with underscore boundaries, e.g., "rack_id", "train_name")
                like_conditions_parts.append(f"lower(name) LIKE '%_{pattern_lower}_%'")
            
            like_conditions = " OR ".join(like_conditions_parts)

            query = f"""
            SELECT name
            FROM system.columns
            WHERE database = currentDatabase()
            AND table = {{table_name:String}}
            AND (
                    {like_conditions}
                )
            AND (
                    type LIKE 'String%'
                    OR type LIKE 'Nullable(String)%'
                    OR type LIKE 'FixedString%'
                )
            ORDER BY name
            """

            result = execute_clickhouse_query(query, params={"table_name": validated_table_name})

            # Extract column names from result
            rack_columns = [row[0] for row in result.result_rows]

            logger.info(f"Found {len(rack_columns)} rack columns in table '{table_name}': {rack_columns}")
            return rack_columns

        except Exception as e:
            logger.error(f"Failed to retrieve rack columns for table '{table_name}': {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=str(e)))

    def get_unique_rack_values(self, table_name: str, rack_columns: List[str], limit: int = 1000) -> List[Dict]:
        """
        Get unique rack values from specified rack columns in a ClickHouse table.

        Args:
            table_name (str): ClickHouse table name
            rack_columns (List[str]): List of rack column names
            limit (int): Maximum number of unique values to return per column

        Returns:
            List[Dict]: List of dictionaries with rack values and metadata

        Raises:
            Exception: If query execution fails or rack_columns is empty
        """
        try:
            if not rack_columns:
                logger.warning(f"No rack columns provided for table '{table_name}'")
                return []

            # Validate table name to prevent SQL injection
            validated_table_name = validate_table_name(table_name)

            # Validate column names
            validated_columns = []
            for column in rack_columns:
                if not re.match(ClickHouseDataValidation.COLUMN_NAME_REGEX, column):
                    logger.warning(f"Skipping invalid column name: {column}")
                    continue
                validated_columns.append(column)

            if not validated_columns:
                logger.warning(f"No valid rack columns found for table '{table_name}'")
                return []

            all_rack_values = []

            # Process each rack column separately
            for rack_column in validated_columns:
                try:
                    query = """
                    SELECT DISTINCT {rack_column:Identifier} as rack_value
                    FROM {table_name:Identifier}
                    WHERE {rack_column:Identifier} IS NOT NULL
                      AND trim({rack_column:Identifier}) != ''
                      AND upper(trim({rack_column:Identifier})) NOT IN {invalid_values:Array(String)}
                    ORDER BY rack_value
                    LIMIT {limit:UInt32}
                    """

                    result = execute_clickhouse_query(query, params={
                        "table_name": validated_table_name,
                        "rack_column": rack_column,
                        "limit": limit,
                        "invalid_values": ClickHouseDataValidation.INVALID_RACK_VALUES
                    })

                    # Process results for this column
                    for row in result.result_rows:
                        rack_value = row[0]
                        if rack_value and str(rack_value).strip():
                            all_rack_values.append({
                                "rack_value": str(rack_value).strip(),
                                "rack_column": rack_column,
                                "table_name": table_name
                            })

                    logger.info(f"Retrieved {len(result.result_rows)} unique rack values from column '{rack_column}' in table '{table_name}'")

                except Exception as col_e:
                    logger.error(f"Error retrieving rack values from column '{rack_column}' in table '{table_name}': {col_e}")
                    continue

            logger.info(f"Total unique rack values retrieved from table '{table_name}': {len(all_rack_values)}")
            return all_rack_values

        except Exception as e:
            logger.error(f"Failed to retrieve unique rack values for table '{table_name}': {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=str(e)))

    def get_rack_data_with_timestamps(
        self,
        table_name: str,
        rack_columns: List[str],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        rack: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get rack values with timestamps for the specified date range.
        Returns rack data in the same format as column data (timestamp, value pairs).

        Args:
            table_name (str): ClickHouse table name
            rack_columns (List[str]): List of rack column names
            from_date (str, optional): Start date for filtering (format: YYYY-MM-DD HH:MM:SS)
            to_date (str, optional): End date for filtering (format: YYYY-MM-DD HH:MM:SS)
            rack (List[str], optional): List of rack values to filter by

        Returns:
            List[Dict]: List with rack data in format: {"rack_column": str, "data": [{"timestamp": str, "value": str}, ...]}
        """
        try:
            if not rack_columns:
                logger.warning(f"No rack columns provided for table '{table_name}'")
                return []

            # Validate table name
            validated_table_name = validate_table_name(table_name)

            # Detect timestamp column
            timestamp_col = self._detect_timestamp_column(validated_table_name)
            if not timestamp_col:
                logger.warning(f"No timestamp column found for table '{table_name}'")
                return []

            # Get timezone
            timezone = self._get_timezone()

            # Validate rack columns
            validated_columns = []
            for column in rack_columns:
                if not re.match(ClickHouseDataValidation.COLUMN_NAME_REGEX, column):
                    logger.warning(f"Skipping invalid column name: {column}")
                    continue
                validated_columns.append(column)

            if not validated_columns:
                logger.warning(f"No valid rack columns found for table '{table_name}'")
                return []

            all_rack_data = []

            # Process each rack column
            for rack_column in validated_columns:
                try:
                    # Build query with date filtering
                    # Convert timestamp to user timezone (formatting handled in Python)
                    # Handle String, DateTime, and DateTime64 types correctly
                    query = f"""
                    SELECT
                        toTimeZone(
                            if(toTypeName({timestamp_col}) LIKE '%String%',
                            parseDateTime64BestEffort({timestamp_col}),
                            if(toTypeName({timestamp_col}) LIKE '%DateTime64%',
                            {timestamp_col},
                            toDateTime64({timestamp_col}, 3)
                            )
                            ),
                            {{timezone:String}}
                        ) as timestamp,
                        trim({{rack_column:Identifier}}) as value
                    FROM {{table_name:Identifier}}
                    """

                    params = {
                        "table_name": validated_table_name,
                        "rack_column": rack_column,
                        "timezone": timezone,
                    }

                    # Build WHERE conditions list
                    where_conditions = []

                    # Add date filtering if provided - use UTC for comparison
                    # Data is stored in UTC, so convert user dates to UTC and compare in UTC
                    if from_date:
                        # Convert user date from Asia/Dubai to UTC
                        from_date_utc = self._convert_user_date_string_to_utc(from_date)
                        if from_date_utc:
                            # Handle String, DateTime, and DateTime64 types correctly
                            datetime_conversion_utc = f"""if(toTypeName(`{timestamp_col}`) LIKE '%String%',
                            parseDateTime64BestEffort(`{timestamp_col}`),
                            if(toTypeName(`{timestamp_col}`) LIKE '%DateTime64%',
                            `{timestamp_col}`,
                            toDateTime64(`{timestamp_col}`, 3)
                            )
                            )""".strip().replace('\n', ' ')
                            where_conditions.append(f"{datetime_conversion_utc} >= toDateTime64({{from_date:String}}, 3, 'UTC')")
                            params["from_date"] = from_date_utc

                    if to_date:
                        # Convert user date from Asia/Dubai to UTC
                        to_date_utc = self._convert_user_date_string_to_utc(to_date)
                        if to_date_utc:
                            # Handle String, DateTime, and DateTime64 types correctly
                            datetime_conversion_utc = f"""if(toTypeName(`{timestamp_col}`) LIKE '%String%',
                            parseDateTime64BestEffort(`{timestamp_col}`),
                            if(toTypeName(`{timestamp_col}`) LIKE '%DateTime64%',
                            `{timestamp_col}`,
                            toDateTime64(`{timestamp_col}`, 3)
                            )
                            )""".strip().replace('\n', ' ')
                            where_conditions.append(f"{datetime_conversion_utc} <= toDateTime64({{to_date:String}}, 3, 'UTC')")
                            params["to_date"] = to_date_utc

                    # Add rack filtering if provided
                    if rack and len(rack) > 0:
                        # Detect rack column for filtering (use get_rack_trailer_column)
                        rack_filter_column = self.get_rack_trailer_column(validated_table_name)
                        
                        if rack_filter_column:
                            # Validate rack names to prevent injection
                            validated_racks = []
                            for rack_value in rack:
                                if isinstance(rack_value, str) and re.match(ClickHouseDataValidation.RACK_NAME_REGEX, rack_value):
                                    validated_racks.append(rack_value)
                                else:
                                    logger.warning(f"Skipping invalid rack name: {rack_value}")
                            
                            if validated_racks:
                                # Use IN clause for rack filtering
                                rack_params = []
                                for i, rack_value in enumerate(validated_racks):
                                    rack_param = f"rack_filter_{i}"
                                    rack_params.append(f"{{{rack_param}:String}}")
                                    params[rack_param] = rack_value
                                
                                where_conditions.append(f"`{rack_filter_column}` IN ({', '.join(rack_params)})")
                                logger.debug(f"Applying rack filtering for {len(validated_racks)} racks: {validated_racks}")
                        else:
                            logger.warning(f"No rack column found in table '{table_name}' for rack filtering")

                    # Add WHERE clause if we have conditions
                    if where_conditions:
                        query += " WHERE " + " AND ".join(where_conditions)

                    query += f" ORDER BY {timestamp_col}"

                    result = execute_clickhouse_query(query, params=params)

                    # Format data as timestamp-value pairs
                    # Ensure timestamps are formatted consistently for matching with main column data
                    data_points = []
                    for row in result.result_rows:
                        timestamp = row[0]
                        value = row[1]
                        
                        # Format timestamp consistently (same format as main column DateTime)
                        # Convert datetime object to ISO string format if needed
                        if timestamp and hasattr(timestamp, 'strftime'):
                            # DateTime object from ClickHouse (already in user timezone)
                            timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S')
                        elif timestamp:
                            # Already a string, ensure it's in the right format
                            timestamp_str = str(timestamp)
                            # Remove timezone suffixes and microseconds
                            timestamp_str = re.sub(r'[+-]\d{2}:\d{2}$', '', timestamp_str)
                            timestamp_str = re.sub(r'[+-]\d{4}$', '', timestamp_str)
                            timestamp_str = re.sub(r'Z$', '', timestamp_str)
                            if ' ' in timestamp_str and 'T' not in timestamp_str:
                                timestamp_str = timestamp_str.replace(' ', 'T')
                            timestamp_str = re.sub(r'\.\d+$', '', timestamp_str)
                        else:
                            timestamp_str = None
                        
                        if value and str(value).strip() and timestamp_str:
                            data_points.append({
                                "timestamp": timestamp_str,
                                "value": str(value).strip()
                            })

                    if data_points:
                        all_rack_data.append({
                            "rack_column": rack_column,
                            "table_name": table_name,
                            "data": data_points
                        })

                    logger.info(f"Retrieved {len(data_points)} rack data points from column '{rack_column}' in table '{table_name}'")

                except Exception as col_e:
                    logger.error(f"Error retrieving rack data from column '{rack_column}' in table '{table_name}': {col_e}")
                    continue

            logger.info(f"Total rack columns with data from table '{table_name}': {len(all_rack_data)}")
            return all_rack_data

        except Exception as e:
            logger.error(f"Failed to retrieve rack data with timestamps for table '{table_name}': {str(e)}")
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=str(e)))

    def _is_clickhouse_available(self) -> bool:
        """
        Check if ClickHouse is available and responsive.

        Returns:
            bool: True if ClickHouse is available, False otherwise
        """
        try:
            from config.clickhouse_connector import check_clickhouse_health
            health = check_clickhouse_health()
            return health.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"ClickHouse availability check failed: {e}")
            return False
        

    
    """Methods Refactoring for the need only (Simplest Version)"""

    def get_column_data_for_table_opt(self, table_name: str, column_names: List[str], limit: Optional[int] = None) -> List[List]:
        """
        Retrieve data for specified columns from a ClickHouse table.
        NOW WITH TIMEZONE SUPPORT using runtime type detection in SQL.

        Args:
            table_name (str): Name of the ClickHouse table.
            column_names (List[str]): List of column names to retrieve.
            limit (Optional[int]): Optional row limit.

        Returns:
            List[List]: Query result rows.

        Raises:
            Exception: If query execution fails.
        """
        import os

        if not column_names:
            raise ValueError("At least one column name must be provided")

        # Filter out internal tracking columns
        column_names = [col for col in column_names if col not in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS]
        
        if not column_names:
            raise ValueError("No valid columns provided after filtering internal tracking columns")

        timezone = self._get_timezone()

        # Use environment variable or fallback
        database = os.getenv("CLICKHOUSE_DATABASE", "swro_db")

        # Detect datetime column for timezone conversion
        timestamp_col = self._detect_timestamp_column(table_name)

        # Safely quote columns and apply smart timezone conversion
        safe_columns = []
        for col in column_names:
            if col == timestamp_col:
                # Use runtime type checking in SQL to apply appropriate conversion
                # Handle String, DateTime, and DateTime64 types correctly
                datetime_select = f"""toTimeZone(
                    if(toTypeName(`{col}`) LIKE '%%String%%',
                    parseDateTime64BestEffort(`{col}`),
                    if(toTypeName(`{col}`) LIKE '%%DateTime64%%',
                    `{col}`,
                    toDateTime64(`{col}`, 3)
                    )
                    ),
                    '{timezone}'
                ) AS `{col}`""".strip().replace('\n', ' ')
                safe_columns.append(datetime_select)
            else:
                safe_columns.append(f"`{col}`")

        # Build base query
        query = f"SELECT {', '.join(safe_columns)} FROM `{database}`.`{table_name}`"

        # Apply limit if specified
        if limit and limit > 0:
            query += f" LIMIT {limit}"

        try:
            # Execute the query (assuming a safe query executor)
            result = execute_clickhouse_query(query)

            row_count = len(result.result_rows)
            logger.info(f"[ClickHouse] Retrieved {row_count} rows from `{table_name}` for columns {column_names} (timezone: {timezone}, smart datetime conversion)")

            return result.result_rows

        except Exception as e:
            logger.exception(f"[ClickHouse] Failed to fetch data from `{table_name}`: {e}")
            raise Exception(f"Failed to retrieve column data from `{table_name}`: {str(e)}")

    def get_distinct_column_values(self, site_name: str, table_name: str, column_name: str) -> Dict[str, Any]:
        """
        Get distinct values for a specific column in a table.
        Generic function that works with any column type and applies appropriate filtering.

        Args:
            site_name (str): Site identifier
            table_name (str): Table identifier (parquet table name)
            column_name (str): Column name to get distinct values from


        Returns:
            Dict[str, Any]: Dictionary containing:
                - distinct_values: List of distinct values
                - column_name: Column name
                - column_type: Data type of the column
                - count: Number of distinct values returned
                - total_distinct: Total count of distinct values in the column
                - table_name: Table identifier
                - site_name: Site identifier

        Raises:
            Exception: If query execution fails or table/column doesn't exist
        """
        try:

            # Validate column name
            if not re.match(ClickHouseDataValidation.COLUMN_NAME_REGEX, column_name):
                raise ValueError(f"Invalid column name: {column_name}")
            
            # Reject internal tracking columns
            if column_name in ClickHouseDataValidation.INTERNAL_TRACKING_COLUMNS:
                raise ValueError(f"Column '{column_name}' is not accessible for data retrieval (internal tracking column)")
            
            # Get ClickHouse table name from mapping
            clickhouse_table_name = self.get_clickhouse_table_name(site_name, table_name)


            if not clickhouse_table_name:
                raise Exception(f"No ClickHouse table found for site '{site_name}' and table '{table_name}'")

            # Validate table exists
            if not self.table_exists(clickhouse_table_name):
                raise Exception(f"ClickHouse table '{clickhouse_table_name}' does not exist")

            # Validate column exists and get its type
            if not self.validate_column_exists(clickhouse_table_name, column_name):
                raise Exception(f"Column '{column_name}' does not exist in table '{clickhouse_table_name}'")

            column_type = self.get_column_type(clickhouse_table_name, column_name)

            # Get database name
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Build query for distinct values with smart filtering
            query = f"""
            SELECT DISTINCT(`{column_name}`) as distinct_value
            FROM `{database}`.`{clickhouse_table_name}`
            """
            # Execute query to get distinct values
            result = execute_clickhouse_query(query)

            # Extract distinct values
            distinct_values = [row[0] for row in result.result_rows]


            response_data = {
                "distinct_values": distinct_values,
                "column_name": column_name,
                "column_type": column_type,
                "count": len(distinct_values),
                "table_name": table_name,
                "site_name": site_name,
                "clickhouse_table_name": clickhouse_table_name
            }

            logger.info(
                f"Retrieved {len(distinct_values)} distinct values for column '{column_name}' "
                f"from table '{table_name}' (site: '{site_name}')"
            )

            return response_data

        except Exception as e:
            logger.error(
                f"Failed to retrieve distinct values for column '{column_name}' "
                f"in table '{table_name}' (site: '{site_name}'): {str(e)}"
            )
            raise Exception(
                f"Failed to retrieve distinct values for '{site_name}.{table_name}.{column_name}': {str(e)}"
            )