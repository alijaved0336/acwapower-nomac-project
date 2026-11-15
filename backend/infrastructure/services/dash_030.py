import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dateutil import parser
import math
import pandas as pd

from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.utils.datetime_utils import DateTimeParser
from constants import Dash030Config

logger = logging.getLogger(__name__)


class Dash_030Service:
    """
    Service class for Dash-030 module containing business logic for RO Summary data merging.
    """

    # Regex pattern for rack name validation
    RACK_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

    def __init__(self):
        self.repository = ClickHouseRepository()
        self._columns_cache = {}
        
    # Table suffixes for the three RO Summary tables
    table_suffixes = Dash030Config.TABLE_SUFFIXES
    site_prefix_mapping = Dash030Config.SITE_PREFIX_MAPPING

    def _create_fallback_metadata(self, data_available_for_requested_date: bool, 
                                  start_dt: datetime = None, end_dt: datetime = None) -> Dict[str, Any]:
        """
        Create standardized fallback metadata for API responses.
        
        Args:
            data_available_for_requested_date: True if data was found for requested date, False if fallback was used
            start_dt: Start datetime of the actual data range used
            end_dt: End datetime of the actual data range used
            
        Returns:
            Dictionary with data_availability_for_given_date, from_date, to_date keys
            Dates are formatted as YYYY-MM-DD (date only, no time or timezone)
        """
        return {
            "data_availability_for_given_date": data_available_for_requested_date,
            "from_date": start_dt.strftime('%Y-%m-%d') if start_dt else None,
            "to_date": end_dt.strftime('%Y-%m-%d') if end_dt else None
        }

    def get_site_prefix(self, site_name: str) -> str:
        """Get site prefix for table naming based on site name."""
        return self.site_prefix_mapping.get(site_name, site_name.replace("-", "_"))

    def build_table_names(self, site_name: str, stream: str = None) -> List[str]:
        """Build the three RO Summary table names based on site name and stream."""
        site_prefix = self.get_site_prefix(site_name)
        table_names = []
        
        for suffix in self.table_suffixes:
            if site_name == "UAQ" and stream:
                table_name = f"{site_prefix}_{site_prefix}_{stream}_{suffix}"
            else:
                table_name = f"{site_prefix}_{site_prefix}_{suffix}"
            table_names.append(table_name)
            
        logger.info(f"Built table names for site '{site_name}'{f' stream {stream}' if stream else ''}: {table_names}")
        return table_names

    def validate_rack_names(self, racks_filter: List[str]) -> List[str]:
        """Validate rack names to prevent SQL injection."""
        if not racks_filter:
            return []
        
        validated_racks = []
        for rack in racks_filter:
            if rack and isinstance(rack, str) and self.RACK_NAME_PATTERN.match(rack):
                validated_racks.append(rack)
            else:
                logger.warning(f"Invalid rack name format rejected: {rack}")
        
        logger.info(f"Validated {len(validated_racks)} out of {len(racks_filter)} rack names")
        return validated_racks

    def get_cached_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get table columns with manual caching to avoid redundant database calls."""
        if table_name in self._columns_cache:
            logger.debug(f"Using cached columns for table '{table_name}'")
            return self._columns_cache[table_name]
        
        try:
            if not self.repository.table_exists(table_name):
                logger.warning(f"Table '{table_name}' does not exist")
                return []
            
            columns = self.repository.get_table_columns(table_name)
            columns_list = [{"name": col["name"], "type": col["type"]} for col in columns]
            
            self._columns_cache[table_name] = columns_list
            logger.info(f"Cached {len(columns_list)} columns for table '{table_name}'")
            return columns_list
            
        except Exception as e:
            logger.error(f"Error getting cached columns for table '{table_name}': {e}")
            return []

    def parse_datetime_parameters(self, start_date: str = None, end_date: str = None) -> tuple:
        """Parse and validate datetime parameters from frontend."""
        parsed_start = None
        parsed_end = None
        
        try:
            if start_date:
                parsed_start = parser.parse(start_date)
            if end_date:
                parsed_end = parser.parse(end_date)
                
            if parsed_start and not parsed_end:
                parsed_end = parsed_start + timedelta(days=1)
            elif parsed_end and not parsed_start:
                parsed_start = parsed_end - timedelta(days=1)
                
            if not parsed_start and not parsed_end:
                parsed_end = datetime.now()
                parsed_start = parsed_end - timedelta(days=7)
                
        except Exception as e:
            logger.warning(f"Error parsing datetime parameters: {e}")
            parsed_end = datetime.now()
            parsed_start = parsed_end - timedelta(days=7)
            
        logger.info(f"Parsed datetime range: {parsed_start} to {parsed_end}")
        return parsed_start, parsed_end

    def build_datetime_where_conditions(self, datetime_column: str, column_type: str, 
                                      start_date: datetime, end_date: datetime) -> tuple:
        """Build WHERE conditions for datetime filtering based on column type."""
        try:
            if 'String' in column_type or 'FixedString' in column_type:
                start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
                end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
                
                where_conditions = [
                    f"`{datetime_column}` >= {{start_date:String}}",
                    f"`{datetime_column}` <= {{end_date:String}}"
                ]
                query_params = {"start_date": start_str, "end_date": end_str}
                logger.info(f"Using string comparison for datetime column '{datetime_column}'")
            else:
                where_conditions = [
                    f"`{datetime_column}` >= {{start_date:DateTime}}",
                    f"`{datetime_column}` <= {{end_date:DateTime}}"
                ]
                query_params = {"start_date": start_date, "end_date": end_date}
                logger.info(f"Using DateTime comparison for datetime column '{datetime_column}'")
            
            return where_conditions, query_params
            
        except Exception as e:
            logger.error(f"Error building datetime WHERE conditions: {e}")
            start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            return [
                f"`{datetime_column}` >= {{start_date:String}}",
                f"`{datetime_column}` <= {{end_date:String}}"
            ], {"start_date": start_str, "end_date": end_str}

    def add_rack_filter_to_conditions(self, where_conditions: List[str], query_params: Dict,
                                     rack_column: str, racks_filter: List[str]) -> None:
        """Add rack filtering to WHERE conditions."""
        if not racks_filter or not rack_column:
            return
        
        validated_racks = self.validate_rack_names(racks_filter)
        if not validated_racks:
            return
        
        rack_params = []
        for i, rack in enumerate(validated_racks):
            rack_param = f"rack_{i}"
            rack_params.append(f"{{{rack_param}:String}}")
            query_params[rack_param] = rack
        
        where_conditions.append(f"`{rack_column}` IN ({', '.join(rack_params)})")
        logger.info(f"Applied racks filter for {len(validated_racks)} racks")

    def find_conductivity_columns(self, column_names: List[str], 
                                 pass_type: str = "pass1") -> Dict[str, str]:
        """Find conductivity columns by pattern matching."""
        result = {}
        
        for col_name in column_names:
            col_lower = col_name.lower()
            
            if pass_type == "pass1":
                if "rear" in col_lower and "permeate" in col_lower and "conductivity" in col_lower:
                    result["rear"] = col_name
                elif "front" in col_lower and "permeate" in col_lower and "conductivity" in col_lower:
                    result["front"] = col_name
            elif pass_type == "pass2":
                if "permeate_weighted_conductivity" in col_lower:
                    result["permeate"] = col_name
        
        return result
    
    def get_table_data_with_datetime(self, table_name: str, start_date: datetime, 
                               end_date: datetime, requested_start: datetime = None,
                               requested_end: datetime = None) -> Dict[str, Any]:
        """
        Get all data from a single table with datetime filtering.
        Extracts metadata from repository's auto-fallback logic.
        """
        try:
            if not self.repository.table_exists(table_name):
                logger.warning(f"Table '{table_name}' does not exist")
                return {
                    "exists": False, "data": [], "datetime_column": None,
                    "columns": [], "table_name": table_name,
                    "used_fallback": False, "actual_start": start_date, "actual_end": end_date
                }
            
            cached_columns = self.get_cached_table_columns(table_name)
            if not cached_columns:
                logger.warning(f"No columns found for table '{table_name}'")
                return {
                    "exists": False, "data": [], "datetime_column": None,
                    "columns": [], "table_name": table_name,
                    "used_fallback": False, "actual_start": start_date, "actual_end": end_date
                }
            
            column_names = [col["name"] for col in cached_columns]
            datetime_column = self.repository._detect_timestamp_column(table_name)
            
            if not datetime_column:
                logger.warning(f"No datetime column found in table '{table_name}'")
                return {
                    "exists": True, "data": [], "datetime_column": None,
                    "columns": column_names, "table_name": table_name,
                    "used_fallback": False, "actual_start": start_date, "actual_end": end_date
                }
            
            datetime_column_type = self.repository.get_column_type(table_name, datetime_column)
            data_columns = [col for col in column_names if col != datetime_column]
            
            if not data_columns:
                logger.warning(f"No data columns found in table '{table_name}'")
                return {
                    "exists": True, "data": [], "datetime_column": datetime_column,
                    "columns": column_names, "table_name": table_name,
                    "used_fallback": False, "actual_start": start_date, "actual_end": end_date
                }
            
            where_conditions, query_params = self.build_datetime_where_conditions(
                datetime_column, datetime_column_type, start_date, end_date
            )

            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=data_columns,
                datetime_column=datetime_column,
                where_conditions=where_conditions,
                query_params=query_params
            )
            
            # CRITICAL: Extract metadata from repository response
            result_rows = result_dict.get("result_rows", [])
            data_availability = result_dict.get("data_availability_for_given_date", True)
            from_date_str = result_dict.get("from_date")
            to_date_str = result_dict.get("to_date")
            
            # Parse the dates from repository response
            actual_start = start_date
            actual_end = end_date
            used_fallback = not data_availability  # If data not available, fallback was used
            
            if from_date_str:
                try:
                    if isinstance(from_date_str, str):
                        actual_start = datetime.strptime(from_date_str, '%Y-%m-%d')
                    elif isinstance(from_date_str, datetime):
                        actual_start = from_date_str
                except Exception as e:
                    logger.warning(f"Error parsing from_date from repository: {e}")
            
            if to_date_str:
                try:
                    if isinstance(to_date_str, str):
                        actual_end = datetime.strptime(to_date_str, '%Y-%m-%d')
                    elif isinstance(to_date_str, datetime):
                        actual_end = to_date_str
                except Exception as e:
                    logger.warning(f"Error parsing to_date from repository: {e}")

            logger.info(f"Retrieved {len(result_rows)} rows from table '{table_name}' (data_availability: {data_availability}, used_fallback: {used_fallback})")
            return {
                "exists": True, 
                "data": result_rows, 
                "datetime_column": datetime_column,
                "columns": column_names, 
                "data_columns": data_columns, 
                "table_name": table_name,
                "used_fallback": used_fallback, 
                "actual_start": actual_start, 
                "actual_end": actual_end,
                "data_availability_for_given_date": data_availability
            }
            
        except Exception as e:
            logger.error(f"Error getting data from table '{table_name}': {e}")
            return {
                "exists": False, "data": [], "datetime_column": None,
                "columns": [], "error": str(e), "table_name": table_name,
                "used_fallback": False, "actual_start": start_date, "actual_end": end_date,
                "data_availability_for_given_date": False
            }

    def merge_table_data_by_datetime(self, table_results: List[Dict[str, Any]], 
                               site_name: str) -> List[Dict[str, Any]]:
        """
        Merge data from multiple tables based on datetime, ensuring ALL columns are included.
        """
        try:
            # Filter out tables that don't exist
            valid_tables = [result for result in table_results if result.get("exists")]
            
            if not valid_tables:
                logger.warning("No valid tables found for merging")
                return []
            
            # Helper function to normalize datetime strings
            def normalize_datetime(dt_str):
                """Normalize datetime string to comparable format"""
                if not dt_str:
                    return None
                try:
                    # Parse the datetime string and convert to standard format
                    from dateutil import parser
                    dt = parser.parse(str(dt_str))
                    # Return ISO format without timezone for comparison
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    logger.warning(f"Failed to normalize datetime '{dt_str}': {e}")
                    return str(dt_str)
            
            # Collect ALL column names from ALL tables
            all_table_columns = {}
            column_types = {}
            datetime_column = None
            
            for i, table_result in enumerate(valid_tables):
                table_suffix = self.table_suffixes[i] if i < len(self.table_suffixes) else f"table_{i}"
                table_columns = table_result.get("columns", [])
                data_columns = table_result.get("data_columns", [])
                table_name = table_result.get("table_name")
                
                # Get datetime column from first available table
                if not datetime_column and table_result.get("datetime_column"):
                    datetime_column = table_result.get("datetime_column")
                
                # Get actual ClickHouse column types from the table
                if table_name and self.repository.table_exists(table_name):
                    table_columns_info = self.repository.get_table_columns(table_name)
                    for col_info in table_columns_info:
                        col_name = col_info.get("name")
                        col_type = col_info.get("type")
                        if col_name in data_columns:
                            column_key = f"{col_name}"
                            column_types[column_key] = col_type
                        elif col_name == datetime_column:
                            column_types["datetime"] = col_type
                
                # Store all data columns with their table suffix
                all_table_columns[table_suffix] = {
                    "data_columns": data_columns,
                    "has_data": len(table_result.get("data", [])) > 0,
                    "table_data": table_result.get("data", [])
                }
                
                logger.info(f"Table {table_suffix}: {len(data_columns)} columns, has_data: {len(table_result.get('data', [])) > 0}")
            
            if not datetime_column:
                logger.warning("No datetime column found for merging")
                return []
            
            # Collect all unique datetimes from all tables with normalization
            all_datetimes = {}  # normalized_datetime -> original_datetime (use first occurrence)
            merged_data = {}
            
            # First pass: collect all datetimes and initialize data structure
            for table_suffix, table_info in all_table_columns.items():
                for row in table_info["table_data"]:
                    if row:
                        row_datetime_original = str(row[0]) if row else None
                        if row_datetime_original:
                            # Normalize for comparison
                            row_datetime_normalized = normalize_datetime(row_datetime_original)
                            
                            if row_datetime_normalized:
                                # Store first occurrence of this datetime
                                if row_datetime_normalized not in all_datetimes:
                                    all_datetimes[row_datetime_normalized] = row_datetime_original
                                
                                # Initialize merged data entry if needed
                                if row_datetime_normalized not in merged_data:
                                    merged_data[row_datetime_normalized] = {
                                        "datetime": all_datetimes[row_datetime_normalized]
                                    }
            
            logger.info(f"Found {len(all_datetimes)} unique normalized datetimes across all tables")
            
            # Second pass: populate data for each table
            for table_suffix, table_info in all_table_columns.items():
                data_columns = table_info["data_columns"]
                table_data = table_info["table_data"]
                
                # Create a lookup dictionary for this table's data by normalized datetime
                table_data_lookup = {}
                for row in table_data:
                    if row:
                        row_datetime_original = str(row[0]) if row else None
                        if row_datetime_original:
                            row_datetime_normalized = normalize_datetime(row_datetime_original)
                            if row_datetime_normalized:
                                table_data_lookup[row_datetime_normalized] = row
                
                # For each normalized datetime, add this table's columns
                for datetime_normalized in merged_data.keys():
                    # Add each column from this table
                    for j, column_name in enumerate(data_columns):
                        column_key = f"{column_name}"
                        
                        if datetime_normalized in table_data_lookup:
                            # Table has data for this datetime
                            row = table_data_lookup[datetime_normalized]
                            if j + 1 < len(row):  # +1 because first column is datetime
                                merged_data[datetime_normalized][column_key] = row[j + 1]
                            else:
                                merged_data[datetime_normalized][column_key] = None
                        else:
                            # Table has no data for this datetime - fill with null
                            merged_data[datetime_normalized][column_key] = None
            
            # Convert merged data to required format
            formatted_data = self.format_merged_data_to_columns(merged_data, site_name, all_table_columns, column_types)
            
            logger.info(f"Merged data from {len(valid_tables)} tables with {len(merged_data)} unique datetime entries")
            logger.info(f"Total columns in merged data: {len(formatted_data)}")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error merging table data: {e}")
            return []
    def format_merged_data_to_columns(self, merged_data: Dict[str, Dict], 
                                    site_name: str, all_table_columns: Dict[str, Dict] = None,
                                    column_types: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Format merged data into the required column-based format, ensuring ALL columns are included.
        
        Args:
            merged_data: Dictionary of merged data by datetime
            site_name: Original site name
            all_table_columns: Dictionary containing all table column information
            column_types: Dictionary mapping column names to their ClickHouse types
            
        Returns:
            List of formatted column data
        """
        try:
            if not merged_data:
                return []
            
            # Sort datetimes for consistent ordering
            sorted_datetimes = sorted(merged_data.keys())
            
            formatted_columns = []
            
            # Add datetime column first with proper type conversion
            datetime_data = []
            for dt in sorted_datetimes:
                dt_value = merged_data[dt]["datetime"]
                # Format datetime values without timezone
                if isinstance(dt_value, datetime):
                    datetime_data.append(DateTimeParser.format_datetime_without_timezone(dt_value))
                elif isinstance(dt_value, str) and dt_value:
                    try:
                        parsed_dt = DateTimeParser.parse_datetime(dt_value)
                        if parsed_dt:
                            datetime_data.append(DateTimeParser.format_datetime_without_timezone(parsed_dt))
                        else:
                            datetime_data.append(dt_value)
                    except:
                        datetime_data.append(dt_value)
                else:
                    datetime_data.append(dt_value)
            datetime_clickhouse_type = column_types.get("datetime", "DateTime") if column_types else "DateTime"
            datetime_parquet_type = self.repository._convert_clickhouse_to_parquet_type(datetime_clickhouse_type)
            
            formatted_columns.append({
                "columnName": "datetime",
                "columnType": datetime_parquet_type,
                "tableName": "RO_Summary_Merged",
                "siteName": site_name,
                "dataSource": datetime_data
            })
            
            # Collect all unique column names (excluding datetime) from all tables
            all_columns = set()
            
            if all_table_columns:
                # Use comprehensive table column information
                for table_suffix, table_info in all_table_columns.items():
                    data_columns = table_info.get("data_columns", [])
                    for column_name in data_columns:
                        column_key = f"{column_name}"
                        all_columns.add(column_key)
            else:
                # Fallback: collect from merged data
                for datetime_entry in merged_data.values():
                    for key in datetime_entry.keys():
                        if key != "datetime":
                            all_columns.add(key)
            
            logger.info(f"Including {len(all_columns)} total columns from all tables")
            
            # Add all columns (sorted for consistency) with proper ClickHouse type conversion
            for column_name in sorted(all_columns):
                column_data = []
                
                # Get ClickHouse type for this column and convert to parquet type
                clickhouse_type = column_types.get(column_name, "String") if column_types else "String"
                parquet_type = self.repository._convert_clickhouse_to_parquet_type(clickhouse_type)
                
                logger.debug(f"Column '{column_name}': ClickHouse type '{clickhouse_type}' -> Parquet type '{parquet_type}'")
                
                for dt in sorted_datetimes:
                    entry = merged_data[dt]
                    value = entry.get(column_name)
                    
                    # Handle None/null values - keep them as None for proper null representation
                    column_data.append(value)
                
                formatted_columns.append({
                    "columnName": column_name,
                    "columnType": parquet_type,
                    "tableName": "RO_Summary_Merged", 
                    "siteName": site_name,
                    "dataSource": column_data
                })
            
            logger.info(f"Formatted {len(formatted_columns)} columns from merged data (including datetime) using ClickHouse type conversion")
            return formatted_columns
            
        except Exception as e:
            logger.error(f"Error formatting merged data: {e}")
            return []

    def get_ro_summary_merged_data(self, site_name: str, stream: str = None, 
                         start_date: str = None, end_date: str = None, 
                         user: dict = None) -> Dict[str, Any]:
        """
        Main method to get merged RO Summary data from three tables.
        Uses SYNCHRONIZED date ranges - finds oldest available range and applies to all tables.
        """
        try:
            logger.info(f"Getting RO Summary merged data for site: {site_name}{f', stream: {stream}' if stream else ''}")
            
            if site_name not in self.site_prefix_mapping:
                logger.warning(f"Unknown site name: {site_name}")
            
            if site_name == "UAQ" and not stream:
                stream = "Stream1"
            
            parsed_start, parsed_end = self.parse_datetime_parameters(start_date, end_date)
            requested_start = parsed_start if (start_date or end_date) else None
            requested_end = parsed_end if (start_date or end_date) else None
            
            table_names = self.build_table_names(site_name, stream)
            
            # PHASE 1: Get initial data and find the OLDEST (earliest) date range with data
            initial_table_results = []
            oldest_start = None
            oldest_end = None
            any_data_found = False

            for table_name in table_names:
                logger.info(f"Checking table: {table_name}")
                table_result = self.get_table_data_with_datetime(
                    table_name, parsed_start, parsed_end, requested_start, requested_end
                )
                initial_table_results.append(table_result)
                
                # Check if this table has data
                has_data = len(table_result.get("data", [])) > 0
                data_available = table_result.get("data_availability_for_given_date", True)
                table_start = table_result.get("actual_start")
                table_end = table_result.get("actual_end")
                
                if has_data and table_start and table_end:
                    any_data_found = True
                    
                    # Track the OLDEST (earliest) date range
                    if oldest_start is None or table_start < oldest_start:
                        oldest_start = table_start
                        logger.info(f"  → Updated oldest_start to: {oldest_start}")
                    
                    if oldest_end is None or table_end < oldest_end:
                        oldest_end = table_end
                        logger.info(f"  → Updated oldest_end to: {oldest_end}")

            # If no data found at all, return empty response
            if not any_data_found or not oldest_start or not oldest_end:
                logger.warning("No data found in any table for merging")
                return {
                    "table": [], 
                    "graph": [],
                    **self._create_fallback_metadata(False)
                }
            
            # PHASE 2: Re-fetch all tables using the SYNCHRONIZED oldest date range
            synchronized_table_results = []
            all_data_available = True
            
            for table_name in table_names:
                logger.info(f"Re-fetching table: {table_name} with synchronized dates")
                
                # Re-fetch with the oldest (synchronized) date range
                table_result = self.get_table_data_with_datetime(
                    table_name, oldest_start, oldest_end, oldest_start, oldest_end
                )
                synchronized_table_results.append(table_result)
                
                # Track overall data availability
                if not table_result.get("data_availability_for_given_date", True):
                    all_data_available = False
                
                has_data = len(table_result.get("data", [])) > 0
                data_available = table_result.get("data_availability_for_given_date", True)

            # PHASE 3: Merge the synchronized data
            merged_data = self.merge_table_data_by_datetime(synchronized_table_results, site_name)
            
            if not merged_data:
                logger.warning(f"No merged data produced for site '{site_name}'")
                return {
                    "table": [], 
                    "graph": [],
                    **self._create_fallback_metadata(False)
                }
            
            graph_columns = Dash030Config.MERGED_TABLE_GRAPH_COLUMNS
            table_data = merged_data.copy()
            graph_data = [col for col in merged_data if col.get("columnName") in graph_columns]

            return {
                "table": table_data, 
                "graph": graph_data,
                **self._create_fallback_metadata(all_data_available, oldest_start, oldest_end)
            }
            
        except Exception as e:
            logger.error(f"Error in get_ro_summary_merged_data: {e}")
            return {
                "table": [], 
                "graph": [],
                **self._create_fallback_metadata(False)
            }

    def build_conductivities_table_name(self, site_name: str, stream: str = None, 
                                       pass_type: str = "pass1") -> str:
        """Build conductivities table name."""
        site_prefix = self.get_site_prefix(site_name)
        suffix = "RO_Summary_Conductivities_Pass2" if pass_type == "pass2" else "RO_Summary_Conductivities_pass1"
        
        if site_name == "UAQ" and stream:
            table_name = f"{site_prefix}_{site_prefix}_{stream}_{suffix}"
        else:
            table_name = f"{site_prefix}_{site_prefix}_{suffix}"
            
        logger.info(f"Built conductivities {pass_type} table: {table_name}")
        return table_name


    def get_conductivities_grouped_data(self, site_name: str, stream: str = None,
                                   racks: List[str] = None, from_date: str = None,
                                   to_date: str = None, user: dict = None,
                                   pass_type: str = "pass1") -> Dict[str, Any]:
        try:
            logger.info(f"Getting conductivities {pass_type} data for site: {site_name}")
            
            if site_name == "UAQ" and not stream:
                stream = "Stream1"
            
            table_name = self.build_conductivities_table_name(site_name, stream, pass_type)
            
            if not self.repository.table_exists(table_name):
                logger.warning(f"Table '{table_name}' does not exist")
                # ✅ Return ONLY data payload (no success/message)
                return {
                    "data": [],
                    "data_availability_for_given_date": False,
                    "from_date": from_date,
                    "to_date": to_date
                }
            
            parsed_start, parsed_end = self.parse_datetime_parameters(from_date, to_date)
            
            grouped_data, metadata = self._get_grouped_by_racks(
                table_name, parsed_start, parsed_end, racks, pass_type
            )
            
            if not grouped_data:
                logger.warning(f"No conductivities {pass_type} data found")
                return {
                    "data": [],
                    "data_availability_for_given_date": False,
                    "from_date": from_date,
                    "to_date": to_date
                }
            
            data_availability = metadata.get("data_availability_for_given_date", True)
            from_date_str = metadata.get("from_date")
            to_date_str = metadata.get("to_date")
            
            def _parse_date_safe(date_value, fallback):
                if not date_value:
                    return fallback
                try:
                    if isinstance(date_value, str):
                        return datetime.strptime(date_value, '%Y-%m-%d')
                    elif isinstance(date_value, datetime):
                        return date_value
                except Exception as e:
                    logger.warning(f"Error parsing date '{date_value}': {e}")
                    return fallback

            actual_start = _parse_date_safe(from_date_str, parsed_start)
            actual_end = _parse_date_safe(to_date_str, parsed_end)
            
            formatted_data = self._format_conductivities_data(grouped_data, site_name, pass_type)
            
            logger.info(f"Retrieved {len(grouped_data)} rack groups for {pass_type} (data_availability: {data_availability})")

            return {
                "data": formatted_data,
                "data_availability_for_given_date": data_availability,
                "from_date": actual_start.strftime('%Y-%m-%d') if actual_start else None,
                "to_date": actual_end.strftime('%Y-%m-%d') if actual_end else None
            }

        except Exception as e:
            logger.error(f"Error in get_conductivities_{pass_type}_data: {e}")
            return {
                "data": [],
                "data_availability_for_given_date": False,
                "from_date": from_date,
                "to_date": to_date
            }

    def get_conductivities_pass1_data(self, site_name: str, stream: str = None,
                                    racks: List[str] = None, from_date: str = None,
                                    to_date: str = None, user: dict = None) -> Dict[str, Any]:
        """Get conductivities pass1 data with fallback metadata."""
        return self.get_conductivities_grouped_data(
            site_name, stream, racks, from_date, to_date, user, "pass1"
        )

    def get_conductivities_pass2_data(self, site_name: str, stream: str = None,
                                    racks: List[str] = None, from_date: str = None,
                                    to_date: str = None, user: dict = None) -> Dict[str, Any]:
        """Get conductivities pass2 data with fallback metadata."""
        return self.get_conductivities_grouped_data(
            site_name, stream, racks, from_date, to_date, user, "pass2"
        )

    def _get_grouped_by_racks(self, table_name: str, start_date: datetime,
                         end_date: datetime, racks_filter: List[str],
                         pass_type: str) -> tuple:
        """
        Get conductivities data grouped by racks with averages.
        Returns tuple of (grouped_data, metadata_dict)
        """
        try:
            datetime_column = self.repository._detect_timestamp_column(table_name)
            rack_column = self.repository._detect_rack_column(table_name)
            
            if not datetime_column or not rack_column:
                logger.error(f"Missing required columns in '{table_name}'")
                return [], {}
            
            cached_columns = self.get_cached_table_columns(table_name)
            column_names = [col["name"] for col in cached_columns]
            
            conductivity_cols = self.find_conductivity_columns(column_names, pass_type)
            
            if pass_type == "pass1" and (not conductivity_cols.get("rear") or not conductivity_cols.get("front")):
                logger.error(f"Required pass1 conductivity columns not found")
                return [], {}
            elif pass_type == "pass2" and not conductivity_cols.get("permeate"):
                logger.error(f"Required pass2 conductivity column not found")
                return [], {}
            
            datetime_column_type = self.repository.get_column_type(table_name, datetime_column)
            where_conditions, query_params = self.build_datetime_where_conditions(
                datetime_column, datetime_column_type, start_date, end_date
            )
            
            self.add_rack_filter_to_conditions(where_conditions, query_params, rack_column, racks_filter)
            
            if pass_type == "pass1":
                data_cols = [conductivity_cols["rear"], conductivity_cols["front"]]
                aggregations = {
                    conductivity_cols["rear"]: "AVG",
                    conductivity_cols["front"]: "AVG"
                }
            else:
                data_cols = [conductivity_cols["permeate"]]
                aggregations = {conductivity_cols["permeate"]: "AVG"}

            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=data_cols,
                datetime_column=datetime_column,
                where_conditions=where_conditions,
                query_params=query_params,
                group_by_columns=[rack_column],
                aggregations=aggregations
            )
            
            # Extract result_rows AND metadata
            result_rows = result_dict.get("result_rows", [])
            metadata = {
                "data_availability_for_given_date": result_dict.get("data_availability_for_given_date", True),
                "from_date": result_dict.get("from_date"),
                "to_date": result_dict.get("to_date")
            }

            grouped_data = []
            for row in result_rows:
                if not row:
                    continue
                
                if pass_type == "pass1" and len(row) >= 3:
                    grouped_data.append({
                        "rack": row[0],
                        "rear_avg": row[1],
                        "front_avg": row[2]
                    })
                elif pass_type == "pass2" and len(row) >= 2:
                    grouped_data.append({
                        "rack": row[0],
                        "permeate_avg": row[1]
                    })
            
            # Sort by rack name using natural sorting
            def natural_sort_key(item):
                """Convert rack name to natural sorting key"""
                rack_name = str(item.get("rack", ""))
                parts = re.split(r'(\d+)', rack_name)
                return [int(part) if part.isdigit() else part.lower() for part in parts]
            
            grouped_data.sort(key=natural_sort_key)
            
            logger.info(f"Retrieved {len(grouped_data)} rack groups for {pass_type} (sorted, data_availability: {metadata['data_availability_for_given_date']})")
            return grouped_data, metadata
            
        except Exception as e:
            logger.error(f"Error getting grouped {pass_type} data: {e}")
            return [], {}

    def _format_conductivities_data(self, grouped_data: List[Dict[str, Any]], 
                                   site_name: str, pass_type: str) -> List[Dict[str, Any]]:
        """Format grouped conductivities data."""
        if not grouped_data:
            return []
        
        racks = [item["rack"] for item in grouped_data]
        table_name = f"RO_Summary_Conductivities_{'Pass2' if pass_type == 'pass2' else 'pass1'}"
        
        formatted_data = [{
            "columnName": "Racks",
            "columnType": "string",
            "tableName": table_name,
            "siteName": site_name,
            "dataSource": racks
        }]
        
        if pass_type == "pass1":
            formatted_data.extend([
                {
                    "columnName": "Rear_Permeate_Weighted_Conductivity",
                    "columnType": "double",
                    "tableName": table_name,
                    "siteName": site_name,
                    "dataSource": [item["rear_avg"] for item in grouped_data]
                },
                {
                    "columnName": "Front_Permeate_Weighted_Conductivity",
                    "columnType": "double",
                    "tableName": table_name,
                    "siteName": site_name,
                    "dataSource": [item["front_avg"] for item in grouped_data]
                }
            ])
        else:
            formatted_data.append({
                "columnName": "Permeate_Weighted_Conductivity",
                "columnType": "double",
                "tableName": table_name,
                "siteName": site_name,
                "dataSource": [round(item["permeate_avg"], 2) for item in grouped_data]
            })
        
        return formatted_data

    def _handle_null_nan_values(self, value: Any) -> Any:
        """Handle null, NaN, and invalid values."""
        if value is None:
            return None
        
        if isinstance(value, str):
            if value.lower().strip() in ['null', 'nan', 'none', '', 'n/a', 'na']:
                return None
        
        # Handle pandas-specific types
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return None
        
        return value

    def get_conductivities_raw_data(self, site_name: str, stream: str = None,
                                racks: List[str] = None, from_date: str = None,
                                to_date: str = None, user: dict = None,
                                pass_type: str = "pass1") -> Dict[str, Any]:
        """
        Get raw conductivities table data without aggregation.
        Uses repository's built-in 7-day fallback logic.
        """
        try:
            logger.info(f"Getting conductivities {pass_type} raw data for site: {site_name}")
            
            if site_name == "UAQ" and not stream:
                stream = "Stream1"
            
            table_name = self.build_conductivities_table_name(site_name, stream, pass_type)
            
            if not self.repository.table_exists(table_name):
                logger.warning(f"Table '{table_name}' does not exist")
                return {
                    "table": [], 
                    "graph": [],
                    **self._create_fallback_metadata(False)
                }
            
            parsed_start, parsed_end = self.parse_datetime_parameters(from_date, to_date)
            
            # Get raw data - repository handles fallback internally
            raw_data = self._get_raw_table_data(table_name, parsed_start, parsed_end, racks)
            
            if not raw_data or not raw_data.get("rows"):
                logger.warning(f"No raw {pass_type} data found")
                return {
                    "table": [], 
                    "graph": [],
                    **self._create_fallback_metadata(False)
                }
            
            # Extract metadata from repository response
            data_availability = raw_data.get("data_availability_for_given_date", True)
            from_date_str = raw_data.get("from_date")
            to_date_str = raw_data.get("to_date")
            
            # Parse dates if they're in string format
            actual_start = None
            actual_end = None
            
            if from_date_str:
                try:
                    if isinstance(from_date_str, str):
                        # Handle YYYY-MM-DD format
                        actual_start = datetime.strptime(from_date_str, '%Y-%m-%d')
                    elif isinstance(from_date_str, datetime):
                        actual_start = from_date_str
                except Exception as e:
                    logger.warning(f"Error parsing from_date: {e}")
                    actual_start = parsed_start
            
            if to_date_str:
                try:
                    if isinstance(to_date_str, str):
                        # Handle YYYY-MM-DD format
                        actual_end = datetime.strptime(to_date_str, '%Y-%m-%d')
                    elif isinstance(to_date_str, datetime):
                        actual_end = to_date_str
                except Exception as e:
                    logger.warning(f"Error parsing to_date: {e}")
                    actual_end = parsed_end
            
            # Use parsed dates as fallback
            if not actual_start:
                actual_start = parsed_start
            if not actual_end:
                actual_end = parsed_end
            
            table_name_formatted = f"RO_Summary_Conductivities_{'Pass2' if pass_type == 'pass2' else 'pass1'}"
            
            graph_columns = (Dash030Config.CONDUCTIVITIES_PASS2_GRAPH_COLUMNS 
                        if pass_type == "pass2" 
                        else Dash030Config.CONDUCTIVITIES_PASS1_GRAPH_COLUMNS)
            
            formatted_data = self._format_raw_data(raw_data, site_name, table_name_formatted, graph_columns)
            
            graph_data = [col for col in formatted_data if col.get("columnName") in graph_columns]
            
            # Remove racks field from table data (keep only in graph data)
            table_data = []
            for col in formatted_data:
                col_copy = col.copy()
                col_copy.pop("racks", None)  # Remove racks if it exists
                table_data.append(col_copy)
            
            logger.info(f"Retrieved {len(raw_data.get('rows', []))} rows for {pass_type} (data_availability: {data_availability})")
            return {
                "table": table_data, 
                "graph": graph_data,
                **self._create_fallback_metadata(data_availability, actual_start, actual_end)
            }
            
        except Exception as e:
            logger.error(f"Error in get_conductivities_{pass_type}_raw_data: {e}")
            return {
                "table": [], 
                "graph": [],
                **self._create_fallback_metadata(False)
            }

    def get_conductivities_pass1_raw_data(self, site_name: str, stream: str = None,
                                        racks: List[str] = None, from_date: str = None,
                                        to_date: str = None, user: dict = None) -> Dict[str, Any]:
        """Get raw conductivities pass1 data with fallback metadata."""
        return self.get_conductivities_raw_data(site_name, stream, racks, from_date, to_date, user, "pass1")

    def get_conductivities_pass2_raw_data(self, site_name: str, stream: str = None,
                                        racks: List[str] = None, from_date: str = None,
                                        to_date: str = None, user: dict = None) -> Dict[str, Any]:
        """Get raw conductivities pass2 data with fallback metadata."""
        return self.get_conductivities_raw_data(site_name, stream, racks, from_date, to_date, user, "pass2")

    def _get_raw_table_data(self, table_name: str, start_date: datetime,
                       end_date: datetime, racks_filter: List[str] = None) -> Dict[str, Any]:
        """Get raw data from table with filtering."""
        try:
            datetime_column = self.repository._detect_timestamp_column(table_name)
            rack_column = self.repository._detect_rack_column(table_name)
            
            if not datetime_column:
                logger.error(f"No datetime column found in '{table_name}'")
                return {}
            
            cached_columns = self.get_cached_table_columns(table_name)
            all_column_names = [col["name"] for col in cached_columns]
            data_columns = [col for col in all_column_names if col != datetime_column]
            
            datetime_column_type = self.repository.get_column_type(table_name, datetime_column)
            where_conditions, query_params = self.build_datetime_where_conditions(
                datetime_column, datetime_column_type, start_date, end_date
            )
            
            self.add_rack_filter_to_conditions(where_conditions, query_params, rack_column, racks_filter)

            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=data_columns,
                datetime_column=datetime_column,
                where_conditions=where_conditions,
                query_params=query_params
            )
            
            # Extract result_rows AND metadata from repository response
            result_rows = result_dict.get("result_rows", [])
            data_availability = result_dict.get("data_availability_for_given_date", True)
            from_date = result_dict.get("from_date")
            to_date = result_dict.get("to_date")

            column_metadata = []
            for col_name in [datetime_column] + data_columns:
                col_type = next((col["type"] for col in cached_columns if col["name"] == col_name), "String")
                parquet_type = self.repository._convert_clickhouse_to_parquet_type(col_type)
                column_metadata.append({"name": col_name, "type": parquet_type})
            
            # Extract rack column values only (not concatenated)
            # Rows structure: [datetime, col1, col2, ...] (datetime is first, then data_columns)
            # column_metadata structure: [datetime, col1, col2, ...] (matches row structure)
            rack_values = []
            
            # Find rack column index in column_metadata
            rack_column_index = None
            if rack_column:
                for idx, col_meta in enumerate(column_metadata):
                    if col_meta["name"] == rack_column:
                        rack_column_index = idx
                        break
            
            # Extract rack values from each row
            if rack_column_index is not None:
                for row in result_rows:
                    if not row or rack_column_index >= len(row):
                        rack_values.append("")
                    else:
                        rack_value = row[rack_column_index]
                        # Convert to string, handle None
                        if rack_value is not None:
                            rack_values.append(str(rack_value))
                        else:
                            rack_values.append("")
            else:
                # If no rack column found, fill with empty strings
                logger.warning(f"Rack column '{rack_column}' not found in column metadata for table '{table_name}'")
                rack_values = [""] * len(result_rows)
            
            logger.info(f"Retrieved {len(result_rows)} raw rows from '{table_name}' (data_availability: {data_availability})")
            return {
                "rows": result_rows,
                "columns": column_metadata,
                "datetime_column": datetime_column,
                "rack_column": rack_column,
                "rack_values": rack_values,
                "total_rows": len(result_rows),
                "data_availability_for_given_date": data_availability,
                "from_date": from_date,
                "to_date": to_date
            }
            
        except Exception as e:
            logger.error(f"Error getting raw data from '{table_name}': {e}")
            return {}

    def _format_raw_data(self, raw_data: Dict[str, Any], site_name: str, 
                        table_name: str, graph_columns: List[str] = None) -> List[Dict[str, Any]]:
        """Format raw table data into column-based format."""
        if not raw_data or not raw_data.get("rows"):
            return []
        
        rows = raw_data["rows"]
        columns = raw_data.get("columns", [])
        rack_values = raw_data.get("rack_values", [])
        
        if not columns:
            return []
        
        datetime_column = raw_data.get("datetime_column")
        formatted_data = []
        for col_index, col_metadata in enumerate(columns):
            column_data = []
            col_name = col_metadata["name"]
            for row in rows:
                value = row[col_index] if row and col_index < len(row) else None
                # Format datetime values without timezone
                if value is not None and isinstance(value, datetime):
                    value = DateTimeParser.format_datetime_without_timezone(value)
                elif value is not None and isinstance(value, str) and col_name == datetime_column:
                    # Try to parse and format datetime strings
                    try:
                        parsed_dt = DateTimeParser.parse_datetime(value)
                        if parsed_dt:
                            value = DateTimeParser.format_datetime_without_timezone(parsed_dt)
                    except:
                        pass
                else:
                    value = self._handle_null_nan_values(value)
                column_data.append(value)
            
            column_obj = {
                "columnName": col_metadata["name"],
                "columnType": col_metadata["type"],
                "tableName": table_name,
                "siteName": site_name,
                "dataSource": column_data
            }
            
            # Add racks field only to graph columns (non-datetime columns that are in graph_columns)
            if (col_name != datetime_column and 
                rack_values and 
                graph_columns and 
                col_name in graph_columns):
                column_obj["racks"] = rack_values
            
            formatted_data.append(column_obj)
        
        logger.info(f"Formatted {len(formatted_data)} columns from raw data")
        return formatted_data
    
    def get_unique_racks(self, site_name: str, stream: str = None, user: dict = None) -> Dict[str, Any]:
        """
        Get unique rack values from both conductivities tables (pass1 and pass2).
        
        Args:
            site_name: Site identifier
            stream: Stream identifier (for UAQ site)
            user: User context
            
        Returns:
            List of unique rack dictionaries with rackLabel, siteName, tableName, and rackValue
        """
        try:
            logger.info(f"Getting unique racks for site: {site_name}{f', stream: {stream}' if stream else ''}")
            
            # Handle UAQ default stream
            if site_name == "UAQ" and not stream:
                stream = "Stream1"
            
            # Build both table names
            pass1_table = self.build_conductivities_table_name(site_name, stream, "pass1")
            pass2_table = self.build_conductivities_table_name(site_name, stream, "pass2")
            
            all_racks = set()  # Use set to automatically handle duplicates
            
            # Get racks from pass1 table
            if self.repository.table_exists(pass1_table):
                try:
                    # Get rack columns for this table
                    rack_columns_pass1 = self.repository.get_rack_columns_for_table(pass1_table)
                    
                    if rack_columns_pass1:
                        # Get unique rack values using existing repository method
                        unique_racks_data = self.repository.get_unique_rack_values(
                            table_name=pass1_table,
                            rack_columns=rack_columns_pass1,
                            limit=10000  # Set high limit to get all racks
                        )
                        
                        # Extract rack values and add to set
                        for rack_item in unique_racks_data:
                            rack_value = rack_item.get("rack_value")
                            if rack_value:
                                all_racks.add(str(rack_value).strip())
                        
                        logger.info(f"Retrieved {len(unique_racks_data)} unique racks from {pass1_table}")
                    else:
                        logger.warning(f"No rack columns found in table {pass1_table}")
                except Exception as e:
                    logger.error(f"Error retrieving racks from {pass1_table}: {e}")
            else:
                logger.warning(f"Table {pass1_table} does not exist")
            
            # Get racks from pass2 table
            if self.repository.table_exists(pass2_table):
                try:
                    # Get rack columns for this table
                    rack_columns_pass2 = self.repository.get_rack_columns_for_table(pass2_table)
                    
                    if rack_columns_pass2:
                        # Get unique rack values using existing repository method
                        unique_racks_data = self.repository.get_unique_rack_values(
                            table_name=pass2_table,
                            rack_columns=rack_columns_pass2,
                            limit=10000  # Set high limit to get all racks
                        )
                        
                        # Extract rack values and add to set
                        for rack_item in unique_racks_data:
                            rack_value = rack_item.get("rack_value")
                            if rack_value:
                                all_racks.add(str(rack_value).strip())
                        
                        logger.info(f"Retrieved {len(unique_racks_data)} unique racks from {pass2_table}")
                    else:
                        logger.warning(f"No rack columns found in table {pass2_table}")
                except Exception as e:
                    logger.error(f"Error retrieving racks from {pass2_table}: {e}")
            else:
                logger.warning(f"Table {pass2_table} does not exist")
            
            def natural_sort_key(rack_name):
                """Convert rack name to natural sorting key"""
                parts = re.split(r'(\d+)', str(rack_name))
                return [int(part) if part.isdigit() else part.lower() for part in parts]
            
            # Format the response with natural sorting
            formatted_racks = []
            for rack_value in sorted(all_racks, key=natural_sort_key):  # Natural sort
                if rack_value and str(rack_value).strip():
                    formatted_racks.append({
                        "rackLabel": str(rack_value).strip(),
                        "siteName": site_name,
                        "tableName": "RO_Summary_Conductivities",
                        "rackValue": str(rack_value).strip()
                    })
            
            logger.info(f"Total unique racks found: {len(formatted_racks)}")
            return {
                "data": formatted_racks,
                **self._create_fallback_metadata(True)  # No date filtering, always True
            }
            
        except Exception as e:
            logger.error(f"Error in get_unique_racks: {e}")
            return {
                "data": [],
                **self._create_fallback_metadata(False)
            }