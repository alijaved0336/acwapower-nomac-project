"""
File processing component for optimized parquet file handling.
Handles file selection, DateTime filtering, and data extraction.
"""
import logging
import pyarrow.parquet as pq
import pyarrow as pa
import io
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from infrastructure.utils.azure.blobStorageClient import BlobStorageClient
from infrastructure.utils.datetime_utils import DateTimeParser as DateTimeParserUtil
from infrastructure.utils.number_formatting import format_decimal_value
from .models import FilterMode, FileInfo
from .datetimeProcessor import DateTimeProcessor

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Handles optimized file processing with DateTime filtering and column extraction.
    """
    
    def __init__(self):
        self.blob_client = BlobStorageClient()
        self.datetime_processor = DateTimeProcessor()
        self.max_files_per_table = 20
        self.max_rows_per_file = 50000  # Limit rows per file for memory management
    
    def _convert_value_by_type(self, value: Any, column_type: str, column_name: str) -> Any:
        """
        Convert a value to the appropriate type based on columnType.
        
        Args:
            value: Raw value from parquet file
            column_type: Type specification ('double', 'int', 'integer', etc.)
            column_name: Column name for logging
            
        Returns:
            Converted value (float, int, or original)
        """
        if value is None:
            return None
            
        try:
            # Handle datetime values
            if isinstance(value, datetime):
                return DateTimeParserUtil.format_datetime_without_timezone(value)
            
            # Convert based on column type
            column_type_lower = column_type.lower()
            
            if column_type_lower in ['double', 'float', 'decimal', 'numeric']:
                # Use centralized formatting: 2 decimals for |value| >= 1, 4 decimals for small values
                result = format_decimal_value(value)
                if result is None and value is not None:
                    logger.warning(f"[FILE_PROCESSOR] Cannot convert '{value}' to float for column {column_name}")
                    return 0.0
                return result if result is not None else 0.0
                    
            elif column_type_lower in ['int', 'integer', 'bigint', 'long']:
                # Convert to integer
                try:
                    # Handle scientific notation and float strings
                    if isinstance(value, str) and ('e' in value.lower() or '.' in value):
                        float_value = float(value)
                        return int(round(float_value))
                    else:
                        return int(value)
                except (ValueError, TypeError):
                    logger.warning(f"[FILE_PROCESSOR] Cannot convert '{value}' to int for column {column_name}")
                    return 0
                    
            elif column_type_lower in ['boolean', 'bool']:
                # Convert to boolean
                try:
                    if isinstance(value, str):
                        return value.lower() in ['true', '1', 'yes', 'on']
                    return bool(value)
                except (ValueError, TypeError):
                    return False
                    
            else:
                # For string types or unknown types, convert to string
                return str(value)
                
        except Exception as e:
            logger.warning(f"[FILE_PROCESSOR] Error converting value '{value}' for column {column_name} (type: {column_type}): {e}")
            # Return appropriate default based on type
            if column_type.lower() in ['double', 'float', 'decimal', 'numeric']:
                return 0.0
            elif column_type.lower() in ['int', 'integer', 'bigint', 'long']:
                return 0
            elif column_type.lower() in ['boolean', 'bool']:
                return False
            else:
                return str(value) if value is not None else None
    
    def read_table_data_optimized(
        self,
        site_name: str,
        table_name: str,
        columns: List[str],
        filter_mode: FilterMode,
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        rack: Optional[str] = None,
        column_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[Any]]:
        """
        Main entry point for optimized table reading with intelligent file selection 
        and DateTime filtering.
        """
        try:
            rack_summary = f" with rack filter: {rack}" if rack else ""
            logger.info(f"[FILE_PROCESSOR] Processing {site_name}/{table_name} for columns: {columns}{rack_summary}")
            
            # Step 1: Get optimal file list based on DateTime criteria
            files = self._select_files_for_datetime_filter(
                site_name, table_name, filter_mode, from_dt, to_dt
            )
            
            if not files:
                logger.warning(f"[FILE_PROCESSOR] No files found for {site_name}/{table_name}")
                return {col: [] for col in columns}
            
            logger.info(f"[FILE_PROCESSOR] Processing {len(files)} files for {site_name}/{table_name}")
            
            # Step 2: Process files based on filter mode
            if filter_mode == FilterMode.EXACT:
                return self._read_files_exact_match(files, columns, from_dt, rack, column_types)
            elif filter_mode == FilterMode.RANGE:
                return self._read_files_range_filter(files, columns, from_dt, to_dt, rack, column_types)
            else:
                # FilterMode.NONE - but we still have default 7-day range from DateTimeProcessor
                return self._read_files_range_filter(files, columns, from_dt, to_dt, rack, column_types)
                
        except Exception as e:
            logger.error(f"[FILE_PROCESSOR] Error reading {site_name}/{table_name}: {e}")
            # Return empty data rather than failing completely
            return {col: [] for col in columns}
    
    def _select_files_for_datetime_filter(
        self,
        site_name: str,
        table_name: str,
        filter_mode: FilterMode,
        from_dt: Optional[datetime],
        to_dt: Optional[datetime]
    ) -> List[FileInfo]:
        """
        Intelligent file selection based on DateTime criteria and path structure.
        Uses directory structure for pre-filtering.
        """
        blob_prefix = f"tables/gold/{site_name}/{table_name}/"
        
        try:
            # Get all parquet files for this table
            blob_files = self.blob_client.list_parquet_files(blob_prefix)
            
            if not blob_files:
                logger.warning(f"[FILE_PROCESSOR] No parquet files found with prefix: {blob_prefix}")
                return []
            
            # Convert to FileInfo objects
            file_infos = []
            for blob in blob_files:
                file_info = FileInfo(
                    path=blob.name,
                    name=blob.name.split('/')[-1],
                    size=getattr(blob, 'size', None),
                    last_modified=getattr(blob, 'last_modified', None)
                )
                file_infos.append(file_info)
            
            # Filter files based on DateTime if filtering is applied
            if from_dt and to_dt:
                relevant_files = self._filter_files_by_datetime_path(
                    file_infos, filter_mode, from_dt, to_dt
                )
            else:
                # No filtering - return most recent files
                relevant_files = file_infos
            
            # Sort by path (which includes date structure) and limit
            sorted_files = sorted(relevant_files, key=lambda x: x.path, reverse=True)
            limited_files = sorted_files[:self.max_files_per_table]
            
            logger.info(f"[FILE_PROCESSOR] Selected {len(limited_files)}/{len(file_infos)} files for processing")
            return limited_files
            
        except Exception as e:
            logger.error(f"[FILE_PROCESSOR] Error selecting files for {site_name}/{table_name}: {e}")
            return []
    
    def _filter_files_by_datetime_path(
        self,
        files: List[FileInfo],
        filter_mode: FilterMode,
        from_dt: datetime,
        to_dt: datetime
    ) -> List[FileInfo]:
        """
        Filter files based on DateTime and path structure.
        Uses YYYY/MM/DD directory structure for efficient filtering.
        """
        relevant_files = []
        
        for file_info in files:
            if self.datetime_processor.is_file_relevant_for_filter(
                file_info.path, filter_mode, from_dt, to_dt
            ):
                relevant_files.append(file_info)
        
        logger.debug(f"[FILE_PROCESSOR] DateTime path filtering: {len(relevant_files)}/{len(files)} files relevant")
        return relevant_files
    
    def _read_files_exact_match(
        self,
        files: List[FileInfo],
        columns: List[str],
        exact_dt: datetime,
        rack: Optional[str] = None,
        column_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[Any]]:
        """
        Read files with exact timestamp matching.
        """
        combined_data = {col: [] for col in columns}
        
        logger.info(f"[FILE_PROCESSOR] Reading {len(files)} files for exact match: {exact_dt}")
        
        for file_info in files:
            try:
                table_data = self._read_single_file_with_datetime_filter(
                    file_info, columns, FilterMode.EXACT, exact_dt, exact_dt, rack, column_types
                )
                
                # Combine data from this file
                for col in columns:
                    if col in table_data and table_data[col]:
                        combined_data[col].extend(table_data[col])
                        
            except Exception as e:
                logger.warning(f"[FILE_PROCESSOR] Error reading file {file_info.name}: {e}")
                continue
        
        total_rows = len(combined_data.get('DateTime', combined_data.get(columns[0], [])))
        logger.info(f"[FILE_PROCESSOR] Exact match processing completed: {total_rows} rows")
        
        return combined_data
    
    def _read_files_range_filter(
        self,
        files: List[FileInfo],
        columns: List[str],
        from_dt: datetime,
        to_dt: datetime,
        rack: Optional[str] = None,
        column_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[Any]]:
        """
        Read files with DateTime range filtering.
        """
        combined_data = {col: [] for col in columns}
        
        logger.info(f"[FILE_PROCESSOR] Reading {len(files)} files for range: {from_dt} to {to_dt}")
        
        for file_info in files:
            try:
                table_data = self._read_single_file_with_datetime_filter(
                    file_info, columns, FilterMode.RANGE, from_dt, to_dt, rack, column_types
                )
                
                # Combine data from this file
                for col in columns:
                    if col in table_data and table_data[col]:
                        combined_data[col].extend(table_data[col])
                        
            except Exception as e:
                logger.warning(f"[FILE_PROCESSOR] Error reading file {file_info.name}: {e}")
                continue
        
        total_rows = len(combined_data.get('DateTime', combined_data.get(columns[0], [])))
        logger.info(f"[FILE_PROCESSOR] Range filtering completed: {total_rows} rows")
        
        return combined_data
    
    def _read_single_file_with_datetime_filter(
        self,
        file_info: FileInfo,
        columns: List[str],
        filter_mode: FilterMode,
        from_dt: datetime,
        to_dt: datetime,
        rack: Optional[str] = None,
        column_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[Any]]:
        """
        Read a single parquet file with DateTime filtering applied.
        """
        try:
            # Download file from blob storage
            blob_client = self.blob_client.get_blob_client(file_info.path)
            blob_data = blob_client.download_blob().readall()
            
            # Read parquet file
            parquet_file = pq.ParquetFile(io.BytesIO(blob_data))
            
            # Ensure DateTime column is included for filtering
            required_columns = list(set(columns + ["DateTime"]))
            
            # Get available columns from file
            available_columns = parquet_file.schema.names
            
            # Detect rack/trailer column if rack filtering is requested
            rack_column = None
            if rack:
                rack_column = self._detect_rack_column(available_columns)
                if rack_column:
                    required_columns.append(rack_column)
                    logger.debug(f"[FILE_PROCESSOR] Found rack column: {rack_column}")
                else:
                    logger.warning(f"[FILE_PROCESSOR] No rack/trailer column found in {file_info.name}")
            
            columns_to_read = [col for col in required_columns if col in available_columns]
            
            if not columns_to_read:
                logger.warning(f"[FILE_PROCESSOR] No requested columns found in {file_info.name}")
                return {col: [] for col in columns}
            
            # Read table with column selection
            table = parquet_file.read(
                columns=columns_to_read,
                use_threads=True,
                use_pandas_metadata=False
            )
            
            # Apply DateTime filtering if DateTime column is available
            if 'DateTime' in table.column_names and from_dt and to_dt:
                filtered_table = self._apply_datetime_filter_to_table(
                    table, filter_mode, from_dt, to_dt
                )
            else:
                filtered_table = table
            
            # Apply rack filtering if rack parameter and rack column are available
            if rack and rack_column and rack_column in filtered_table.column_names:
                filtered_table = self._apply_rack_filter_to_table(
                    filtered_table, rack_column, rack
                )
                logger.debug(f"[FILE_PROCESSOR] Applied rack filter: {rack} on column {rack_column}")
            elif rack and not rack_column:
                logger.debug(f"[FILE_PROCESSOR] Rack filter requested but no rack/trailer column found")
            
            # Limit rows for memory management
            if len(filtered_table) > self.max_rows_per_file:
                logger.info(f"[FILE_PROCESSOR] Limiting {file_info.name} from {len(filtered_table)} to {self.max_rows_per_file} rows")
                filtered_table = filtered_table.slice(0, self.max_rows_per_file)
            
            # Convert to column dictionary with type-aware conversion
            result = {}
            for col in columns:
                if col in filtered_table.column_names:
                    column_data = filtered_table[col]
                    # Get column type for conversion, default to string
                    col_type = column_types.get(col, 'string') if column_types else 'string'
                    
                    # Convert to Python objects with appropriate types
                    python_data = []
                    for i in range(len(column_data)):
                        try:
                            value = column_data[i].as_py()
                            converted_value = self._convert_value_by_type(value, col_type, col)
                            python_data.append(converted_value)
                        except Exception as e:
                            logger.debug(f"[FILE_PROCESSOR] Error processing value at index {i} for column {col}: {e}")
                            python_data.append(None)
                    
                    result[col] = python_data
                else:
                    result[col] = []
            
            logger.debug(f"[FILE_PROCESSOR] Read {file_info.name}: {len(filtered_table)} rows")
            return result
            
        except Exception as e:
            logger.error(f"[FILE_PROCESSOR] Error reading file {file_info.path}: {e}")
            return {col: [] for col in columns}
    
    def _apply_datetime_filter_to_table(
        self,
        table: pa.Table,
        filter_mode: FilterMode,
        from_dt: datetime,
        to_dt: datetime
    ) -> pa.Table:
        """
        Apply DateTime filtering to a PyArrow table.
        """
        try:
            datetime_column = table['DateTime']
            mask = []
            
            for i in range(len(datetime_column)):
                try:
                    value = datetime_column[i].as_py()
                    if value is not None and isinstance(value, datetime):
                        # Ensure timezone awareness
                        if value.tzinfo is None:
                            value = value.replace(tzinfo=timezone.utc)
                        
                        if filter_mode == FilterMode.EXACT:
                            # For exact match, check if within same minute (handle precision issues)
                            exact_start = from_dt.replace(second=0, microsecond=0)
                            exact_end = from_dt.replace(second=59, microsecond=999999)
                            mask.append(exact_start <= value <= exact_end)
                        else:  # FilterMode.RANGE
                            mask.append(from_dt <= value <= to_dt)
                    else:
                        mask.append(False)
                except Exception:
                    mask.append(False)
            
            # Apply the mask
            filtered_table = table.filter(mask)
            
            logger.debug(f"[FILE_PROCESSOR] DateTime filtering: {len(filtered_table)}/{len(table)} rows match")
            return filtered_table
            
        except Exception as e:
            logger.warning(f"[FILE_PROCESSOR] Error applying DateTime filter: {e}")
            return table  # Return unfiltered table on error
    
    def _detect_rack_column(self, available_columns: List[str]) -> Optional[str]:
        """
        Detect rack or trailer column in the available columns.
        Returns the column name if found, None otherwise.
        """
        # Convert to lowercase for case-insensitive comparison
        columns_lower = {col.lower(): col for col in available_columns}
        
        # Check for 'rack' column first (preferred)
        if 'rack' in columns_lower:
            return columns_lower['rack']
        
        # Check for 'trailer' column as fallback
        if 'trailer' in columns_lower:
            return columns_lower['trailer']
        
        # Check for variations (case-insensitive)
        for col_lower, col_original in columns_lower.items():
            if 'rack' in col_lower or 'trailer' in col_lower:
                logger.debug(f"[FILE_PROCESSOR] Found potential rack column: {col_original}")
                return col_original
        
        return None
    
    def _apply_rack_filter_to_table(
        self,
        table: pa.Table,
        rack_column: str,
        rack_value: str
    ) -> pa.Table:
        """
        Apply rack filtering to a PyArrow table.
        """
        try:
            rack_col = table[rack_column]
            mask = []
            
            for i in range(len(rack_col)):
                try:
                    value = rack_col[i].as_py()
                    if value is not None:
                        # Convert to string for comparison
                        value_str = str(value).strip()
                        rack_value_str = str(rack_value).strip()
                        # Case-insensitive comparison
                        mask.append(value_str.lower() == rack_value_str.lower())
                    else:
                        mask.append(False)
                except Exception:
                    mask.append(False)
            
            # Apply the mask
            filtered_table = table.filter(mask)
            
            logger.debug(f"[FILE_PROCESSOR] Rack filtering: {len(filtered_table)}/{len(table)} rows match rack={rack_value}")
            return filtered_table
            
        except Exception as e:
            logger.warning(f"[FILE_PROCESSOR] Error applying rack filter: {e}")
            return table  # Return unfiltered table on error