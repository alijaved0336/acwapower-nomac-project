"""
Spark-based file processing component for optimized parquet file handling.
Replaces PyArrow with Spark for dramatically improved performance.
"""
import logging
import math
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, isnan, isnull, asc, upper, from_unixtime, lit
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType, LongType

from infrastructure.services.spark_singleton import get_spark_session
from infrastructure.utils.datetime_utils import DateTimeParser
from infrastructure.utils.number_formatting import format_decimal_value
from .models import FilterMode, FileInfo

logger = logging.getLogger(__name__)


class SparkFileProcessor:
    """
    High-performance Spark-based file processor for parquet files.
    Replaces PyArrow with Spark for 5-10x performance improvement.
    """

    def __init__(self):
        # Use pre-initialized Spark session from singleton (no initialization overhead!)
        self.spark = get_spark_session()
        self.max_files_per_table = 20
        self.max_rows_per_file = 50000

        logger.info("[SPARK_FILE_PROCESSOR] Initialized with pre-initialized Spark session (zero overhead!)")

    def read_table_data_optimized(
        self,
        site_name: str,
        table_name: str,
        columns: List[str],
        filter_mode: FilterMode,
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        rack_list: Optional[List[str]] = None,
        column_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[Any]]:
        """
        Main entry point for Spark-optimized table reading.
        Uses Spark's distributed processing for 5-10x performance improvement.

        Args:
            site_name: Name of the site
            table_name: Name of the table
            columns: List of columns to retrieve
            filter_mode: DateTime filtering mode
            from_dt: Start datetime for filtering
            to_dt: End datetime for filtering
            rack_list: List of rack values for filtering
            column_types: Optional column type mapping
        """
        start_time = time.time()

        try:
            # Ensure rack_list is initialized
            if rack_list is None:
                rack_list = []

            rack_summary = f" with {len(rack_list)} rack filters: {rack_list}" if rack_list else ""
            logger.info(f"[SPARK_FILE_PROCESSOR] Processing {site_name}/{table_name} for columns: {columns}{rack_summary}")

            # Build Azure Data Lake path
            azure_path = f"wasbs://swro@mpcswrosg.blob.core.windows.net/tables/gold/{site_name}/{table_name}"

            # Read parquet files with Spark
            df = self._read_parquet_with_spark(azure_path, columns)

            if df is None or df.count() == 0:
                logger.warning(f"[SPARK_FILE_PROCESSOR] No data found for {site_name}/{table_name}")
                return {col: [] for col in columns}

            # Apply filters
            filtered_df = self._apply_filters(df, filter_mode, from_dt, to_dt, rack_list, columns)

            # Apply DateTime ordering if column exists
            if 'DateTime' in filtered_df.columns:
                filtered_df = filtered_df.orderBy(col("DateTime").asc())
                logger.debug(f"[SPARK_FILE_PROCESSOR] Applied DateTime ascending ordering for {site_name}/{table_name}")
            else:
                logger.warning(f"[SPARK_FILE_PROCESSOR] DateTime column not found in {site_name}/{table_name} - returning unordered data")

            # Convert to Python format
            result = self._convert_to_python_format(filtered_df, columns, column_types)

            # Process each column and format datetime columns
            for column in columns:
                if column in result:
                    # Check if this is a datetime column that needs formatting
                    if self._is_datetime_column(column, column_types.get(column, "") if column_types else ""):
                        result[column] = self._format_datetime_values_to_iso(result[column])

            processing_time = time.time() - start_time
            total_rows = len(result.get('DateTime', result.get(columns[0], [])))

            logger.info(f"[SPARK_FILE_PROCESSOR] Completed processing {total_rows} rows in {processing_time:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"[SPARK_FILE_PROCESSOR] Error reading {site_name}/{table_name}: {e}")
            return {col: [] for col in columns}

    def _read_parquet_with_spark(self, azure_path: str, columns: List[str]) -> Optional[Any]:
        """
        Read parquet files using Spark's optimized parquet reader with pushdown predicates.
        """
        try:
            logger.info(f"[SPARK_FILE_PROCESSOR] Reading parquet files from: {azure_path}")

            # Read with Spark's optimized parquet reader with pushdown predicates
            df = self.spark.read.option("recursiveFileLookup", "true").option("pushDownPredicate", "true").parquet(azure_path)

            # Get available columns
            available_columns = df.columns
            logger.info(f"[SPARK_FILE_PROCESSOR] Available columns: {available_columns}")

            # Select only requested columns that exist
            columns_to_select = [col for col in columns if col in available_columns]

            if not columns_to_select:
                logger.warning(f"[SPARK_FILE_PROCESSOR] No requested columns found in parquet files")
                return None

            # Always include DateTime for filtering if it exists
            if 'DateTime' not in columns_to_select and 'DateTime' in available_columns:
                columns_to_select.append('DateTime')

            # Select columns
            df_selected = df.select(*columns_to_select)

            # Cache for performance
            df_selected.cache()

            total_rows = df_selected.count()
            logger.info(f"[SPARK_FILE_PROCESSOR] Read {total_rows} rows from parquet files")

            return df_selected

        except Exception as e:
            logger.error(f"[SPARK_FILE_PROCESSOR] Error reading parquet files: {e}")
            return None

    def _apply_filters(
        self,
        df: Any,
        filter_mode: FilterMode,
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        rack_list: Optional[List[str]],
        columns: List[str]
    ) -> Any:
        """
        Apply DateTime and rack filters using Spark SQL with optimized predicates.
        Enhanced to support multiple racks using isin() for better performance.
        Handles both BIGINT (epoch) and TIMESTAMP DateTime columns.
        """
        try:
            filtered_df = df

            # Apply DateTime filtering with optimized predicates
            if from_dt and to_dt and 'DateTime' in df.columns:
                logger.info(f"[SPARK_FILE_PROCESSOR] Applying DateTime filter: {from_dt} to {to_dt}")

                # Check the data type of DateTime column
                datetime_dtype = dict(df.dtypes).get('DateTime', '')
                logger.info(f"[SPARK_FILE_PROCESSOR] DateTime column type: {datetime_dtype}")

                # Handle BIGINT (epoch) DateTime columns
                if 'bigint' in datetime_dtype.lower() or 'long' in datetime_dtype.lower():
                    logger.info("[SPARK_FILE_PROCESSOR] DateTime is BIGINT/LONG - converting filter values to epoch milliseconds")

                    # Convert datetime to epoch milliseconds (assuming the BIGINT is in milliseconds)
                    # If it's nanoseconds, we'll need to multiply by 1000000
                    from_epoch = int(from_dt.timestamp() * 1000)  # Convert to milliseconds
                    to_epoch = int(to_dt.timestamp() * 1000)

                    # Check if the values are likely nanoseconds (very large numbers)
                    # Sample a value to determine the scale
                    sample_value = filtered_df.select("DateTime").limit(1).collect()
                    if sample_value and sample_value[0]["DateTime"]:
                        sample_dt = sample_value[0]["DateTime"]
                        # If the value is > 10^15, it's likely nanoseconds
                        if sample_dt > 10**15:
                            logger.info("[SPARK_FILE_PROCESSOR] DateTime appears to be in nanoseconds")
                            from_epoch = int(from_dt.timestamp() * 1_000_000_000)  # Convert to nanoseconds
                            to_epoch = int(to_dt.timestamp() * 1_000_000_000)
                        # If the value is > 10^12, it's likely microseconds
                        elif sample_dt > 10**12:
                            logger.info("[SPARK_FILE_PROCESSOR] DateTime appears to be in microseconds")
                            from_epoch = int(from_dt.timestamp() * 1_000_000)  # Convert to microseconds
                            to_epoch = int(to_dt.timestamp() * 1_000_000)

                    if filter_mode == FilterMode.EXACT:
                        # For exact match, check if within same minute
                        exact_start = from_dt.replace(second=0, microsecond=0)
                        exact_end = from_dt.replace(second=59, microsecond=999999)

                        # Determine the scale based on sample
                        if sample_value and sample_value[0]["DateTime"] and sample_value[0]["DateTime"] > 10**15:
                            exact_start_epoch = int(exact_start.timestamp() * 1_000_000_000)
                            exact_end_epoch = int(exact_end.timestamp() * 1_000_000_000)
                        elif sample_value and sample_value[0]["DateTime"] and sample_value[0]["DateTime"] > 10**12:
                            exact_start_epoch = int(exact_start.timestamp() * 1_000_000)
                            exact_end_epoch = int(exact_end.timestamp() * 1_000_000)
                        else:
                            exact_start_epoch = int(exact_start.timestamp() * 1000)
                            exact_end_epoch = int(exact_end.timestamp() * 1000)

                        filtered_df = filtered_df.filter(
                            (col("DateTime") >= exact_start_epoch) & (col("DateTime") <= exact_end_epoch)
                        )
                    else:  # FilterMode.RANGE
                        filtered_df = filtered_df.filter(
                            (col("DateTime") >= from_epoch) & (col("DateTime") <= to_epoch)
                        )

                    logger.info(f"[SPARK_FILE_PROCESSOR] Applied epoch filter: {from_epoch} to {to_epoch}")

                else:
                    # Handle TIMESTAMP DateTime columns (original logic)
                    logger.info("[SPARK_FILE_PROCESSOR] DateTime is TIMESTAMP - using direct datetime comparison")

                    if filter_mode == FilterMode.EXACT:
                        # For exact match, check if within same minute
                        exact_start = from_dt.replace(second=0, microsecond=0)
                        exact_end = from_dt.replace(second=59, microsecond=999999)
                        filtered_df = filtered_df.filter(
                            (col("DateTime") >= exact_start) & (col("DateTime") <= exact_end)
                        )
                    else:  # FilterMode.RANGE
                        filtered_df = filtered_df.filter(
                            (col("DateTime") >= from_dt) & (col("DateTime") <= to_dt)
                        )

            # Apply rack filtering with enhanced multi-rack support
            if rack_list:
                rack_column = self._detect_rack_column(df.columns)
                if rack_column:
                    logger.info(f"[SPARK_FILE_PROCESSOR] Applying rack filters: {rack_list} on column {rack_column}")

                    if len(rack_list) == 1:
                        # Single rack - use case-insensitive exact matching
                        filtered_df = filtered_df.filter(
                            col(rack_column).rlike(f"(?i)^{rack_list[0]}$")
                        )
                    else:
                        # Multiple racks - use isin() for optimal performance with case-insensitive matching
                        rack_list_upper = [rack.upper() for rack in rack_list]
                        filtered_df = filtered_df.filter(
                            upper(col(rack_column)).isin(rack_list_upper)
                        )
                        logger.info(f"[SPARK_FILE_PROCESSOR] Using optimized isin() filter for {len(rack_list)} racks")
                else:
                    logger.warning(f"[SPARK_FILE_PROCESSOR] No rack column found for filtering")

            # Limit rows for memory management
            if self.max_rows_per_file > 0:
                filtered_df = filtered_df.limit(self.max_rows_per_file)

            # Cache filtered result for better performance
            filtered_df.cache()

            filtered_count = filtered_df.count()
            logger.info(f"[SPARK_FILE_PROCESSOR] After filtering: {filtered_count} rows")

            return filtered_df

        except Exception as e:
            logger.error(f"[SPARK_FILE_PROCESSOR] Error applying filters: {e}")
            return df

    def _convert_to_python_format(
        self,
        df: Any,
        columns: List[str],
        column_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[Any]]:
        """
        Convert Spark DataFrame to Python dictionary format.
        """
        try:
            # Collect data from Spark
            rows = df.collect()

            # Initialize result dictionary
            result = {col: [] for col in columns}

            # Process each row
            for row in rows:
                for col_name in columns:
                    if col_name in df.columns:
                        value = getattr(row, col_name)
                        converted_value = self._convert_value_by_type(value, column_types.get(col_name, 'string') if column_types else 'string', col_name)
                        result[col_name].append(converted_value)
                    else:
                        result[col_name].append(None)

            return result

        except Exception as e:
            logger.error(f"[SPARK_FILE_PROCESSOR] Error converting to Python format: {e}")
            return {col: [] for col in columns}

    def _convert_value_by_type(self, value: Any, column_type: str, column_name: str) -> Any:
        """
        Convert a value to the appropriate type based on columnType.
        """
        if value is None:
            return None

        # Handle empty strings and whitespace-only strings
        if isinstance(value, str):
            value_stripped = value.strip()
            if not value_stripped or value_stripped.lower() in ['null', 'none', 'nan', '']:
                return None

        try:
            # Handle datetime values
            if isinstance(value, datetime):
                return DateTimeParser.format_datetime_without_timezone(value)

            # Convert based on column type
            column_type_lower = column_type.lower()

            if column_type_lower in ['double', 'float', 'decimal', 'numeric']:
                # Use centralized formatting: 2 decimals for |value| >= 1, 4 decimals for small values
                result = format_decimal_value(value)
                if result is None and value is not None:
                    logger.warning(f"[SPARK_FILE_PROCESSOR] Cannot convert '{value}' to float for column {column_name}")
                return result

            elif column_type_lower in ['int', 'integer', 'bigint', 'long']:
                try:
                    # Additional safety check for empty/invalid values
                    if isinstance(value, str) and not value.strip():
                        return None

                    if isinstance(value, str) and ('e' in value.lower() or '.' in value):
                        float_value = float(value)
                        return int(round(float_value))
                    else:
                        return int(value)
                except (ValueError, TypeError):
                    logger.warning(f"[SPARK_FILE_PROCESSOR] Cannot convert '{value}' to int for column {column_name}")
                    return None

            elif column_type_lower in ['boolean', 'bool']:
                try:
                    if isinstance(value, str):
                        return value.lower() in ['true', '1', 'yes', 'on']
                    return bool(value)
                except (ValueError, TypeError):
                    return False

            else:
                return str(value)

        except Exception as e:
            logger.warning(f"[SPARK_FILE_PROCESSOR] Error converting value '{value}' for column {column_name}: {e}")
            if column_type.lower() in ['double', 'float', 'decimal', 'numeric']:
                return None  # Return None instead of 0.0 for consistency with inf/NaN handling
            elif column_type.lower() in ['int', 'integer', 'bigint', 'long']:
                return None  # Return None instead of 0 for consistency
            elif column_type.lower() in ['boolean', 'bool']:
                return None  # Return None instead of False for consistency
            else:
                return str(value) if value is not None else None

    def _detect_rack_column(self, available_columns: List[str]) -> Optional[str]:
        """
        Detect rack or trailer column in the available columns.
        """
        columns_lower = {col.lower(): col for col in available_columns}

        if 'rack' in columns_lower:
            return columns_lower['rack']

        if 'trailer' in columns_lower:
            return columns_lower['trailer']

        for col_lower, col_original in columns_lower.items():
            if 'rack' in col_lower or 'trailer' in col_lower:
                return col_original

        return None

    def _is_datetime_column(self, column_name: str, column_type: str) -> bool:
        """
        Determine if a column should be treated as datetime and formatted.
        """
        # Check by column name patterns
        datetime_column_names = {"datetime", "timestamp", "time", "date"}
        if column_name.lower() in datetime_column_names:
            return True

        # Check by column type patterns
        datetime_type_patterns = [
            "timestamp", "datetime", "date", "time",
            "datetime64", "timestamp[ns", "datetime[ns"
        ]
        column_type_lower = column_type.lower()
        if any(pattern in column_type_lower for pattern in datetime_type_patterns):
            return True

        return False

    def _format_datetime_values_to_iso(self, datetime_values: List[Any]) -> List[str]:
        """
        Convert list of datetime values to ISO format strings.
        Handles nanosecond timestamps, datetime objects, and string formats using PyArrow.
        """
        formatted_values = []

        for value in datetime_values:
            try:
                if value is None or str(value).lower() in ['nan', 'none', 'null', '']:
                    formatted_values.append("")
                    continue

                dt_value = None

                # Handle datetime objects directly
                if isinstance(value, datetime):
                    dt_value = value
                else:
                    value_str = str(value).strip()

                    # Handle nanosecond timestamps (like "1754812740000000000")
                    if value_str.isdigit() and len(value_str) >= 10:
                        try:
                            # Convert nanoseconds to seconds
                            if len(value_str) == 19:  # nanoseconds
                                timestamp_seconds = int(value_str) / 1_000_000_000
                            elif len(value_str) == 16:  # microseconds
                                timestamp_seconds = int(value_str) / 1_000_000
                            elif len(value_str) == 13:  # milliseconds
                                timestamp_seconds = int(value_str) / 1_000
                            else:  # assume seconds
                                timestamp_seconds = int(value_str)

                            dt_value = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)

                        except (ValueError, OSError) as e:
                            logger.warning(f"[SPARK_FILE_PROCESSOR] Failed to parse timestamp '{value_str}': {e}")
                            formatted_values.append(str(value))
                            continue

                    elif 'Timestamp' in value_str:
                        import re
                        match = re.search(r"'([^']+)'", value_str)
                        if match:
                            dt_value = datetime.fromisoformat(match.group(1).replace('Z', '+00:00'))

                    # Try direct ISO parsing
                    else:
                        try:
                            dt_value = datetime.fromisoformat(value_str.replace('Z', '+00:00'))
                        except:
                            try:
                                # Use PyArrow for timestamp parsing as fallback
                                import pyarrow as pa
                                try:
                                    # Try to parse as timestamp
                                    ts_array = pa.array([value_str])
                                    parsed_ts = pa.strptime(ts_array, format='%Y-%m-%d %H:%M:%S', unit='s')
                                    dt_value = parsed_ts[0].as_py()
                                except:
                                    try:
                                        # Try different timestamp format
                                        parsed_ts = pa.strptime(ts_array, format='%Y-%m-%dT%H:%M:%S', unit='s')
                                        dt_value = parsed_ts[0].as_py()
                                    except:
                                        formatted_values.append(str(value))
                                        continue
                            except ImportError:
                                formatted_values.append(str(value))
                                continue

                # Ensure timezone awareness and convert to UTC
                if dt_value:
                    if dt_value.tzinfo is None:
                        dt_value = dt_value.replace(tzinfo=timezone.utc)
                    elif dt_value.tzinfo != timezone.utc:
                        dt_value = dt_value.astimezone(timezone.utc)

                    # Format to ISO string
                    iso_string = dt_value.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    formatted_values.append(iso_string)
                else:
                    formatted_values.append(str(value))

            except Exception as e:
                logger.warning(f"[SPARK_FILE_PROCESSOR] Failed to format datetime value '{value}': {e}")
                formatted_values.append(str(value))

        return formatted_values