"""
Utility function for fetching latest data from parquet files.
Similar to read_parquet_optimized but specifically for getting latest records.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import pyarrow.parquet as pq
import io

from infrastructure.orm.repositories.sparkRepository import SparkRepository
from infrastructure.utils.azure.blobStorageClient import BlobStorageClient

logger = logging.getLogger(__name__)


def fetch_latest_data(
    site: str,
    table: str,
    columns: List[str],
    target_date: Optional[str] = None,
    coordinates: bool = False
) -> Dict[str, Any]:
    """
    Fetch the latest data from parquet files for a given site and table.

    Args:
        site: Site name (e.g., 'Rabigh3')
        table: Table name (e.g., 'Rabigh3_Chemicals_Stocks')
        columns: List of column names to fetch
        target_date: Optional specific date in 'YYYY-MM-DD' format.
                    If None, finds the latest available date.
        coordinates: Whether to use coordinates data instead of gold data

    Returns:
        Dict containing:
        - success: bool
        - data: Dict with siteName, tableName, dateFilter, totalRows, columnNames, columns
        - message: str
        - error: Optional error message
    """
    try:
        logger.info(f"[FETCH_LATEST_DATA] Starting fetch for {site}/{table}")

        # Initialize services
        spark_repo = SparkRepository()
        blob_client = BlobStorageClient()

        # Determine the date to fetch
        if target_date:
            from_date = f"{target_date},00:00:00"
            to_date = f"{target_date},23:59:59"
            logger.info(f"[FETCH_LATEST_DATA] Using provided date: {target_date}")
        else:
            # Find the latest available date
            latest_date = _get_latest_available_date(spark_repo, site, table, coordinates)
            if not latest_date:
                return {
                    "success": False,
                    "data": None,
                    "message": f"No data found for {site}/{table}",
                    "error": "No latest date found"
                }

            from_date = f"{latest_date},00:00:00"
            to_date = f"{latest_date},23:59:59"
            logger.info(f"[FETCH_LATEST_DATA] Using latest date: {latest_date}")

        # Fetch the data
        column_data = _fetch_data_with_datetime_filtering(
            blob_client, site, table, columns, from_date, to_date, coordinates
        )

        if not column_data:
            return {
                "success": False,
                "data": None,
                "message": f"No data found for {site}/{table} on {target_date or 'latest date'}",
                "error": "No data returned"
            }

        # Format the response
        result_data = {
            "siteName": site,
            "tableName": table,
            "dateFilter": f"{from_date} to {to_date}",
            "totalRows": len(list(column_data.values())[0]) if column_data else 0,
            "columnNames": columns,
            "columns": column_data
        }

        logger.info(f"[FETCH_LATEST_DATA] Successfully fetched {result_data['totalRows']} rows")

        return {
            "success": True,
            "data": result_data,
            "message": f"Successfully fetched {result_data['totalRows']} rows",
            "error": None
        }

    except Exception as e:
        logger.error(f"[FETCH_LATEST_DATA] Error: {e}")
        return {
            "success": False,
            "data": None,
            "message": f"Error fetching data: {str(e)}",
            "error": str(e)
        }


def _get_latest_available_date(
    spark_repo: SparkRepository,
    site: str,
    table: str,
    coordinates: bool = False
) -> Optional[str]:
    """
    Get the latest available date by reading the actual data from the table.
    """
    try:
        logger.info(f"[FETCH_LATEST_DATA] Finding latest date for {site}/{table}")

        # Use Spark SQL to get the maximum DateTime value
        from pyspark.sql.functions import max as spark_max

        # Read only the DateTime column
        spark_df = spark_repo.read_parquet_optimized(
            siteName=site,
            tableName=table,
            columns=["DateTime"],
            coordinates=coordinates
        )

        if spark_df is None or spark_df.count() == 0:
            logger.warning(f"[FETCH_LATEST_DATA] No data found for {site}/{table}")
            return None

        # Get the maximum DateTime value using Spark SQL aggregation
        max_datetime_df = spark_df.select(spark_max("DateTime").alias("max_datetime"))
        max_datetime_row = max_datetime_df.collect()

        if max_datetime_row and len(max_datetime_row) > 0:
            max_datetime = max_datetime_row[0]["max_datetime"]
            if max_datetime:
                # Convert to date string
                if hasattr(max_datetime, 'strftime'):
                    latest_date = max_datetime.strftime('%Y-%m-%d')
                else:
                    # Handle different datetime formats
                    latest_date = str(max_datetime).split(' ')[0]

                logger.info(f"[FETCH_LATEST_DATA] Found latest date: {latest_date}")
                return latest_date

        logger.warning(f"[FETCH_LATEST_DATA] No valid datetime found for {site}/{table}")
        return None

    except Exception as e:
        logger.error(f"[FETCH_LATEST_DATA] Error getting latest date: {e}")
        return None


def _fetch_data_with_datetime_filtering(
    blob_client: BlobStorageClient,
    site: str,
    table: str,
    column_names: List[str],
    from_date: str,
    to_date: str,
    coordinates: bool = False
) -> Dict[str, List]:
    """
    Fetch data using direct blob client approach with DateTime column filtering.
    """
    try:
        logger.info(f"[FETCH_LATEST_DATA] Fetching data with DateTime filtering for {site}/{table}")

        # Parse the date range
        from_date_obj = datetime.strptime(from_date.split(',')[0], '%Y-%m-%d')
        to_date_obj = datetime.strptime(to_date.split(',')[0], '%Y-%m-%d')

        logger.info(f"[FETCH_LATEST_DATA] Filtering by DateTime range: {from_date_obj.date()} to {to_date_obj.date()}")

        # Get all parquet files
        data_type = "coordinates" if coordinates else "gold"
        blob_prefix = f"tables/{data_type}/{site}/{table}/"
        parquet_files = blob_client.list_parquet_files(blob_prefix)

        if not parquet_files:
            logger.warning(f"[FETCH_LATEST_DATA] No parquet files found for {site}/{table}")
            return {}

        logger.info(f"[FETCH_LATEST_DATA] Found {len(parquet_files)} files to check")

        all_data = []
        for file in parquet_files:
            try:
                logger.info(f"[FETCH_LATEST_DATA] Reading file: {file.name}")
                blob_client_instance = blob_client.get_blob_client(file.name)
                blob_data = blob_client_instance.download_blob().readall()

                # Read parquet file
                parquet_file = pq.ParquetFile(io.BytesIO(blob_data))
                table_data = parquet_file.read(columns=column_names)

                # Filter by DateTime column if it exists
                filtered_rows = 0
                for i in range(len(table_data)):
                    row_data = {}
                    include_row = True

                    for col_name in column_names:
                        if col_name in table_data.column_names:
                            value = table_data[col_name][i].as_py()

                            # If this is the DateTime column, check if it's within our date range
                            if col_name == "DateTime" and value is not None:
                                try:
                                    # Parse the datetime value
                                    if isinstance(value, str):
                                        # Try different datetime formats
                                        dt_value = None
                                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                                            try:
                                                dt_value = datetime.strptime(value, fmt)
                                                break
                                            except ValueError:
                                                continue
                                    else:
                                        # Handle datetime objects
                                        dt_value = value

                                    if dt_value:
                                        # Check if datetime is within our date range
                                        if dt_value.date() < from_date_obj.date() or dt_value.date() > to_date_obj.date():
                                            include_row = False
                                            break
                                except Exception as e:
                                    logger.debug(f"[FETCH_LATEST_DATA] Could not parse DateTime '{value}': {e}")
                                    # If we can't parse the datetime, include the row
                                    pass

                            row_data[col_name] = str(value) if value is not None else None
                        else:
                            row_data[col_name] = None

                    # Only add the row if it passes the DateTime filter
                    if include_row:
                        all_data.append(row_data)
                        filtered_rows += 1

                logger.info(f"[FETCH_LATEST_DATA] Read {len(table_data)} rows, {filtered_rows} passed DateTime filter from {file.name}")

            except Exception as e:
                logger.error(f"[FETCH_LATEST_DATA] Error reading file {file.name}: {e}")
                continue

        if not all_data:
            logger.warning(f"[FETCH_LATEST_DATA] No data found matching DateTime range {from_date_obj.date()} to {to_date_obj.date()}")
            return {}

        logger.info(f"[FETCH_LATEST_DATA] Total rows after DateTime filtering: {len(all_data)}")

        # Organize data by columns
        column_data = {}
        for col_name in column_names:
            column_data[col_name] = []

        # Extract data for each column
        for row_data in all_data:
            for col_name in column_names:
                column_data[col_name].append(row_data.get(col_name))

        return column_data

    except Exception as e:
        logger.error(f"[FETCH_LATEST_DATA] Error fetching data: {e}")
        return {}

