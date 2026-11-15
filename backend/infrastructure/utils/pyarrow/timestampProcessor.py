import pyarrow as pa
from datetime import datetime
from typing import Optional, List
import re
import os


class TimestampProcessor:
    """
    Handles timestamp precision and conversion for PyArrow with dynamic column detection.
    """
    
    def __init__(self):
        # Expanded timestamp column names to match actual data patterns
        self.timestamp_column_names = [
            'Start_Time','End_Time','Datetime',             
            'datetime', 'timestamp', 'date', 'time', 
            'created_at', 'updated_at', 'Begin_Time', 'Finish_Time',
            'StartTime', 'EndTime', 'start_time', 'end_time'
        ]
    
    def _validate_and_parse_date(self, date_str: str) -> datetime:
        """
        Validate and parse date string with multiple format support.
        """
        if not date_str or not isinstance(date_str, str):
            raise ValueError(f"Invalid date string: {date_str}")
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',           # 2025-01-15
            '%Y-%m-%d %H:%M:%S',  # 2025-01-15 10:30:00
            '%Y-%m-%dT%H:%M:%S',  # 2025-01-15T10:30:00
            '%Y-%m-%dT%H:%M:%SZ', # 2025-01-15T10:30:00Z
            '%Y-%m-%d %H:%M:%S.%f', # 2025-01-15 10:30:00.123456
        ]
        
        # Clean the date string (remove extra spaces, handle timezone info)
        clean_date = date_str.strip()
        
        # Try parsing with different formats
        for fmt in date_formats:
            try:
                return datetime.strptime(clean_date, fmt)
            except ValueError:
                continue
        
        # Try ISO format as fallback
        try:
            return datetime.fromisoformat(clean_date.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # If all else fails, try to extract just the date part
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', clean_date)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), '%Y-%m-%d')
            except ValueError:
                pass
        
        raise ValueError(f"Unable to parse date string: {date_str}. Supported formats: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, ISO format")
    
    def find_available_timestamp_columns(self, table) -> List[str]:
        """
        Find the timestamp column in the table, trying multiple common names.
        """
        available_columns = table.column_names
        found_timestamp_columns = []
        
        print(f"[TIMESTAMP_PROCESSOR] Available columns: {available_columns}")
        
        # First check timestamp columns in order
        for col_name in self.timestamp_column_names:
            if col_name in available_columns:
                col_type = table.column(col_name).type
                if pa.types.is_timestamp(col_type) or pa.types.is_date(col_type) or pa.types.is_time(col_type):
                    found_timestamp_columns.append(col_name)
                    print(f"[TIMESTAMP_PROCESSOR] Found primary timestamp column: {col_name} (type: {col_type})")
        
        # Then check other timestamp columns
        for col_name in self.timestamp_column_names:
            if col_name in available_columns and col_name not in found_timestamp_columns:
                col_type = table.column(col_name).type
                if pa.types.is_timestamp(col_type) or pa.types.is_date(col_type) or pa.types.is_time(col_type):
                    found_timestamp_columns.append(col_name)
                    print(f"[TIMESTAMP_PROCESSOR] Found additional timestamp column: {col_name} (type: {col_type})")
        
        if not found_timestamp_columns:
            print(f"[TIMESTAMP_PROCESSOR] No timestamp columns found in: {available_columns}")
        
        return found_timestamp_columns
    
    def _find_timestamp_column(self, table) -> Optional[str]:
        """
        Find the best timestamp column in the table, trying multiple common names.
        Returns None if no timestamp column is found.
        """
        found_columns = self.find_available_timestamp_columns(table)
        
        if found_columns:
            # Return the first (highest priority) timestamp column
            best_column = found_columns[0]
            print(f"[TIMESTAMP_PROCESSOR] Using timestamp column: {best_column}")
            return best_column
        
        # Final fallback - return None instead of a non-existent column
        print(f"[TIMESTAMP_PROCESSOR] No valid timestamp column found")
        return None
    
    def apply_date_filter(self, table, from_date: str, to_date: str):
        """Apply date filtering with automatic timestamp precision handling and column detection."""
        try:
            # Find available timestamp columns
            timestamp_columns = self.find_available_timestamp_columns(table)
            
            if not timestamp_columns:
                print(f"[TIMESTAMP_PROCESSOR] No timestamp columns found for filtering, returning unfiltered table")
                return table
            
            # Use the first available timestamp column (highest priority)
            timestamp_col_name = timestamp_columns[0]
            datetime_col = table.column(timestamp_col_name)
            
            # Get the actual timestamp type from the column
            col_type = datetime_col.type
            print(f"[TIMESTAMP_PROCESSOR] Using column '{timestamp_col_name}' with type: {col_type}")
            
            # Validate and parse dates with robust error handling
            try:
                parsed_from_date = self._validate_and_parse_date(from_date)
                parsed_to_date = self._validate_and_parse_date(to_date)
            except ValueError as e:
                print(f"[TIMESTAMP_PROCESSOR] Date validation failed: {e}")
                return table  # Return unfiltered table on date parsing error
            
            # Handle different timestamp precisions
            if pa.types.is_timestamp(col_type):
                # Convert date strings to match the column's timestamp precision
                if col_type.unit == 'ns':
                    # Nanosecond precision
                    from_timestamp = pa.scalar(parsed_from_date, type=pa.timestamp('ns', tz=col_type.tz))
                    to_timestamp = pa.scalar(parsed_to_date.replace(hour=23, minute=59, second=59, microsecond=999999), type=pa.timestamp('ns', tz=col_type.tz))
                elif col_type.unit == 'us':
                    # Microsecond precision
                    from_timestamp = pa.scalar(parsed_from_date, type=pa.timestamp('us', tz=col_type.tz))
                    to_timestamp = pa.scalar(parsed_to_date.replace(hour=23, minute=59, second=59, microsecond=999999), type=pa.timestamp('us', tz=col_type.tz))
                else:
                    # Default to microsecond for other precisions
                    from_timestamp = pa.scalar(parsed_from_date, type=pa.timestamp('us'))
                    to_timestamp = pa.scalar(parsed_to_date.replace(hour=23, minute=59, second=59, microsecond=999999), type=pa.timestamp('us'))
            else:
                # Fallback for non-timestamp types
                from_timestamp = pa.scalar(parsed_from_date)
                to_timestamp = pa.scalar(parsed_to_date.replace(hour=23, minute=59, second=59, microsecond=999999))
            
            print(f"[TIMESTAMP_PROCESSOR] Applying filter on '{timestamp_col_name}': {from_timestamp} to {to_timestamp}")
            
            mask = pa.compute.and_(
                pa.compute.greater_equal(datetime_col, from_timestamp),
                pa.compute.less_equal(datetime_col, to_timestamp)
            )
            
            filtered_table = pa.compute.filter(table, mask)
            print(f"[TIMESTAMP_PROCESSOR] Applied date filter: {len(table)} -> {len(filtered_table)} rows")
            return filtered_table
            
        except Exception as e:
            print(f"[TIMESTAMP_PROCESSOR] Date filtering failed: {e}")
            print(f"[TIMESTAMP_PROCESSOR] Returning unfiltered table with {len(table)} rows")
            return table
    
    def convert_timestamp_precision(self, table):
        """
        Convert timestamps with better error handling and type checking.
        """
        try:
            arrays = []
            schema_fields = []
            
            for i, field in enumerate(table.schema):
                array = table.column(i)
                field_name = field.name
                
                # timestamp type checking
                if pa.types.is_timestamp(array.type):
                    if array.type.unit == 'ns':
                        print(f"[TIMESTAMP_PROCESSOR] Converting {field_name} from nanoseconds to microseconds")
                        try:
                            us_array = pa.compute.cast(array, pa.timestamp('us', tz=array.type.tz))
                            arrays.append(us_array)
                            schema_fields.append(pa.field(field_name, pa.timestamp('us', tz=array.type.tz), field.nullable))
                        except Exception as cast_error:
                            print(f"[TIMESTAMP_PROCESSOR] Cast failed for {field_name}: {cast_error}")
                            # Keep original if cast fails
                            arrays.append(array)
                            schema_fields.append(field)
                    else:
                        arrays.append(array)
                        schema_fields.append(field)
                else:
                    arrays.append(array)
                    schema_fields.append(field)
            
            new_schema = pa.schema(schema_fields)
            converted_table = pa.table(arrays, schema=new_schema)
            
            print(f"[TIMESTAMP_PROCESSOR] Timestamp conversion completed successfully")
            return converted_table
            
        except Exception as e:
            print(f"[TIMESTAMP_PROCESSOR] Timestamp conversion failed: {e}")
            print(f"[TIMESTAMP_PROCESSOR] Returning original table")
            return table