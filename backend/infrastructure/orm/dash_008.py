"""
Dashboard 008 Repository - Database Queries
Handles direct database queries for Dashboard 008 - Pump Analysis.
"""

from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple

from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService
from config.clickhouse_connector import execute_clickhouse_query

logger = logging.getLogger(__name__)


class Dash008Repository:
    """
    Repository for Dashboard 008 - Pump Analysis.
    Provides direct database access methods.
    """

    def __init__(self):
        """Initialize repository with ClickHouse ADLS service dependency."""
        self.clickhouse_service = ClickHouseADLSService()

    def get_latest_date_range_from_db(
        self,
        site_id: str,
        table_name: str,
        days: int = 7
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the latest date range from the database for operational/performance data.
        Finds the most recent timestamp and calculates a date range going back N days.

        Args:
            site_id: Site identifier
            table_name: Table name
            days: Number of days to go back from latest timestamp (default: 7)

        Returns:
            Tuple of (from_date, to_date) as strings in YYYY-MM-DD format
            Returns (None, None) if no data found

        Raises:
            Exception: If query fails
        """
        try:
            logger.info(f"Finding latest timestamp in DB for site {site_id}, table {table_name}")

            # Get ClickHouse table name
            clickhouse_table_name = self.clickhouse_service.repository.get_clickhouse_table_name(
                site_id, table_name
            )
            if not clickhouse_table_name:
                raise Exception(f"No ClickHouse table found for {site_id}.{table_name}")

            # Find datetime column
            datetime_column = self.clickhouse_service.repository.get_datetime_column(
                clickhouse_table_name
            )
            if not datetime_column:
                logger.warning(f"No datetime column found in table {clickhouse_table_name}")
                return None, None

            # Query to get the maximum (latest) timestamp
            query = f"""
                SELECT MAX(`{datetime_column}`) as latest_timestamp
                FROM `{clickhouse_table_name}`
            """

            logger.info(f"Executing max timestamp query: {query}")

            # Execute query
            result = execute_clickhouse_query(query=query)

            # Check if result has data
            if not result.result_rows or not result.result_rows[0] or result.result_rows[0][0] is None:
                logger.warning(f"No data found in table {table_name}")
                return None, None

            latest_timestamp = result.result_rows[0][0]
            logger.info(f"Latest timestamp found: {latest_timestamp}")

            # Convert to datetime object if it's a string
            if isinstance(latest_timestamp, str):
                # Handle different timestamp formats
                latest_timestamp = latest_timestamp.replace('Z', '+00:00')
                try:
                    latest_date = datetime.fromisoformat(latest_timestamp)
                except ValueError:
                    # Try parsing without timezone info
                    latest_date = datetime.strptime(latest_timestamp.split('+')[0], '%Y-%m-%d %H:%M:%S')
            else:
                latest_date = latest_timestamp

            # Calculate from_date (N days before latest_date)
            from_date_obj = latest_date - timedelta(days=days)

            # Format as YYYY-MM-DD strings
            to_date = latest_date.strftime('%Y-%m-%d')
            from_date = from_date_obj.strftime('%Y-%m-%d')

            logger.info(f"Calculated date range from DB: {from_date} to {to_date}")

            return from_date, to_date

        except Exception as e:
            logger.error(f"Error getting latest date range from DB: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get latest date range from DB: {str(e)}")