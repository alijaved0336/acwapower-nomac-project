"""
ClickHouse-based utility function for fetching latest data.
Equivalent to fetch_latest_handler.py but uses ClickHouse instead of Spark.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from constants import ENABLE_FALLBACK_FOR_ANALYSIS_APIS

logger = logging.getLogger(__name__)


def fetch_latest_data_clickhouse(
    site: str,
    table: str,
    columns: List[str],
    target_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch the latest data from ClickHouse for a given site and table.

    Note: This function is used by Analysis APIs and has 7-day fallback DISABLED.
    When no data is found for the requested date range, it returns empty result
    instead of falling back to last 7 days of available data.

    Args:
        site: Site name (e.g., 'Rabigh3')
        table: Table name (e.g., 'Rabigh3_Chemicals_Stocks')
        columns: List of column names to fetch
        target_date: Optional specific date in 'YYYY-MM-DD' format.
                    If None, finds the latest available date.

    Returns:
        Dict containing:
        - success: bool
        - data: Dict with siteName, tableName, dateFilter, totalRows, columnNames, columns
        - message: str
        - error: Optional error message
    """
    try:
        logger.info(f"[FETCH_LATEST_DATA_CH] Starting ClickHouse fetch for {site}/{table}")

        repository = ClickHouseRepository()

        # Get ClickHouse table name from site mapping
        clickhouse_table = repository.get_clickhouse_table_name(site, table)
        if not clickhouse_table:
            logger.warning(f"No ClickHouse table found for site '{site}', table '{table}'")
            return {
                "success": False,
                "data": None,
                "message": f"Table '{table}' not found for site '{site}'",
                "error": f"No mapping found for {site}.{table}"
            }

        # Find datetime column for filtering
        datetime_column = repository.get_datetime_column(clickhouse_table)

        # Build WHERE conditions and parameters
        where_conditions = []
        query_params = {}

        if target_date and datetime_column:
            # Parse target date
            try:
                target_dt = datetime.strptime(target_date, '%Y-%m-%d')
                start_dt = target_dt.replace(hour=0, minute=0, second=0)
                end_dt = target_dt.replace(hour=23, minute=59, second=59)

                # Add date filter
                where_conditions.append(
                    f"`{datetime_column}` >= {{start_date:DateTime}} AND "
                    f"`{datetime_column}` <= {{end_date:DateTime}}"
                )
                query_params['start_date'] = start_dt
                query_params['end_date'] = end_dt

                logger.info(f"[FETCH_LATEST_DATA_CH] Using target date: {target_date}")

            except ValueError as e:
                logger.error(f"Invalid date format '{target_date}': {e}")
                return {
                    "success": False,
                    "data": None,
                    "message": f"Invalid date format: {target_date}",
                    "error": str(e)
                }
        else:
            logger.info(f"[FETCH_LATEST_DATA_CH] Fetching latest available data")

        # Fetch data WITHOUT fallback logic (disabled for Analysis APIs)
        # Uses constant ENABLE_FALLBACK_FOR_ANALYSIS_APIS from constants.py
        result = repository.get_column_data_for_table(
            clickhouse_table_name=clickhouse_table,
            column_names=columns,
            datetime_column=datetime_column,
            where_conditions=where_conditions if where_conditions else None,
            query_params=query_params if query_params else None,
            enable_fallback=ENABLE_FALLBACK_FOR_ANALYSIS_APIS  # Centrally configured: False for Analysis APIs
        )

        # Extract data and metadata from repository response
        result_rows = result.get("result_rows", [])
        data_availability = result.get("data_availability_for_given_date", True)
        from_date_used = result.get("from_date")
        to_date_used = result.get("to_date")

        if not result_rows:
            message = "No data found" if data_availability else f"Fallback applied: No data for requested date"
            return {
                "success": False,
                "data": None,
                "message": message,
                "error": "No data available"
            }

        # Convert rows to column-oriented format
        column_data = {}
        total_rows = len(result_rows)

        for idx, column_name in enumerate(columns):
            column_data[column_name] = [
                row[idx] if idx < len(row) else None 
                for row in result_rows
            ]

        # Format the response to match original structure
        date_filter = f"{from_date_used} to {to_date_used}" if from_date_used and to_date_used else "latest"

        result_data = {
            "siteName": site,
            "tableName": table,
            "dateFilter": date_filter,
            "totalRows": total_rows,
            "columnNames": columns,
            "columns": column_data,
            # Add fallback metadata
            "metadata": {
                "data_availability_for_given_date": data_availability,
                "from_date": from_date_used,
                "to_date": to_date_used
            }
        }

        # Determine message based on fallback status
        if data_availability:
            message = f"Successfully fetched {total_rows} rows from ClickHouse"
        else:
            message = (f"No data found for requested date. Retrieved last 7 days of available data "
                      f"({from_date_used} to {to_date_used}). Total rows: {total_rows}")

        logger.info(f"[FETCH_LATEST_DATA_CH] {message}")

        return {
            "success": True,
            "data": result_data,
            "message": message,
            "error": None
        }

    except Exception as e:
        logger.error(f"[FETCH_LATEST_DATA_CH] Error: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "message": f"Error fetching data from ClickHouse: {str(e)}",
            "error": str(e)
        }


def _get_column_types_from_schema(table_name: str, column_names: List[str]) -> Dict[str, str]:
    """
    Get actual column types from ClickHouse schema using system.columns.

    Args:
        table_name: Name of the ClickHouse table
        column_names: List of column names to query

    Returns:
        Dictionary mapping column names to standardized types
    """
    try:
        from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository

        repository = ClickHouseRepository()
        column_types = {}

        # Query ClickHouse for actual column types
        for column_name in column_names:
            clickhouse_type = repository.get_column_type(table_name, column_name)

            if clickhouse_type:
                # Map ClickHouse type to standardized type
                standardized_type = _map_clickhouse_type_to_standard(clickhouse_type)
                column_types[column_name] = standardized_type
            else:
                # Fallback if column not found
                logger.warning(f"[FETCH_LATEST_DATA_CH] Could not find type for column {column_name} in table {table_name}, using default 'double'")
                column_types[column_name] = "double"

        return column_types

    except Exception as e:
        logger.error(f"[FETCH_LATEST_DATA_CH] Error querying column types: {e}")
        # Return empty dict to use fallback behavior
        return {}


def _map_clickhouse_type_to_standard(clickhouse_type: str) -> str:
    """
    Map ClickHouse data types to standardized type names used by the application.

    Args:
        clickhouse_type: ClickHouse column type string

    Returns:
        Standardized type name (e.g., 'timestamp[ns, tz=Etc/UTC]', 'double', 'int64', etc.)
    """
    if not clickhouse_type:
        return "double"

    # Convert to lowercase for comparison
    type_lower = clickhouse_type.lower()

    # Handle nullable types
    if type_lower.startswith('nullable('):
        # Extract inner type from Nullable(Type)
        inner_type = clickhouse_type[9:-1] if clickhouse_type.endswith(')') else clickhouse_type[9:]
        return _map_clickhouse_type_to_standard(inner_type)

    # Type mappings based on ClickHouseService pattern
    type_mappings = {
        # Integer types
        'int8': 'int64',
        'int16': 'int64',
        'int32': 'int64',
        'int64': 'int64',
        'uint8': 'int64',
        'uint16': 'int64',
        'uint32': 'int64',
        'uint64': 'int64',

        # Float types
        'float32': 'double',
        'float64': 'double',
        'double': 'double',
        'decimal': 'double',

        # String types
        'string': 'string',
        'fixedstring': 'string',

        # Date/Time types
        'date': 'timestamp[ns]',
        'datetime': 'timestamp[ns]',
        'datetime64': 'timestamp[ns]',
        'timestamp': 'timestamp[ns]',

        # Boolean
        'boolean': 'boolean',
        'bool': 'boolean',
    }

    # Check for exact match first
    if type_lower in type_mappings:
        return type_mappings[type_lower]

    # Check for partial matches (e.g., DateTime64(3) -> datetime64)
    for clickhouse_prefix, standard_type in type_mappings.items():
        if type_lower.startswith(clickhouse_prefix):
            return standard_type

    # Default to double for unknown types
    logger.debug(f"Unknown ClickHouse type '{clickhouse_type}', defaulting to 'double'")
    return "double"