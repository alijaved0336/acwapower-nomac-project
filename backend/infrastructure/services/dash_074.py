import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dateutil import parser
import math
import pandas as pd

from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.utils.datetime_utils import DateTimeParser


logger = logging.getLogger(__name__)


class Dash074Service:
    """
    Service for Dashboard 074 - SS Alerts
    """

    def __init__(self):
        self.repository = ClickHouseRepository()
        self._columns_cache = {}

    def __del__(self):
        """Cleanup repository connection when service is destroyed"""
        pass

        # ---------- Utilities ----------
    @staticmethod
    def humanize(token: str) -> str:
        parts = [p for p in token.split('_') if p]
        pretty = []
        for p in parts:
            if p.isupper():
                pretty.append(p)
            else:
                pretty.append(p.capitalize())
        return " ".join(pretty)

    @staticmethod
    def _parse_iso(s: str):
        if not s:
            return None
        return datetime.fromisoformat(s)
    
    
    @staticmethod
    def extract_pass_number(text: str) -> str:
        match = re.search(r'pass\s*(\d+)', text, re.IGNORECASE)
        if match:
            return f"pass{match.group(1)}"
        return "" 
    
    @staticmethod
    def extract_stream_number(text: str) -> str:
        match = re.search(r'stream\s*(\d+)', text, re.IGNORECASE)
        if match:
            return f"Stream{match.group(1)}"
        return "" 
    
    # Helper function to normalize datetime strings
    def normalize_datetime(dt_str):
        """Normalize datetime string to comparable format"""
        if not dt_str:
            return None
        try:
            # Parse the datetime string and convert to standard format
            dt = parser.parse(str(dt_str))
            # Return ISO format without timezone for comparison
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.warning(f"Failed to normalize datetime '{dt_str}': {e}")
            return str(dt_str)
    
    @staticmethod
    def _is_datetime_column(col_name: str) -> bool:
        """Check if a column name indicates it's a datetime column"""
        if not col_name:
            return False
        col_lower = col_name.lower()
        return (
            col_lower in ['datetime', 'timestamp', 'start_time', 'end_time', 'created_on', 'updated_on', 
                         'last_occurrence', 'commissioned_date', 'last_maintenance_date', 'created on', 
                         'updated on', 'last occurrence', 'commissioned date', 'last maintenance date'] or
            'time' in col_lower or 
            'date' in col_lower
        )
    
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
    
    def build_datetime_where_conditions(self, datetime_column: str, column_type: str, 
                                      start_date: datetime, end_date: datetime) -> tuple:
        """Build WHERE conditions for datetime filtering based on column type."""
        try:
            if 'String' in column_type or 'FixedString' in column_type:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                start_str = start_dt.strftime('%Y-%m-%d')
                end_str = end_dt.strftime('%Y-%m-%d')
                
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
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            return [
                f"`{datetime_column}` >= {{start_date:String}}",
                f"`{datetime_column}` <= {{end_date:String}}"
            ], {"start_date": start_str, "end_date": end_str}
            
            
    def build_datetime_where_conditions_graph_data(self, datetime_column: str, column_type: str, 
                                      start_date: datetime, end_date: datetime) -> tuple:
        """Build WHERE conditions for datetime filtering based on column type."""
        try:
            if 'String' in column_type or 'FixedString' in column_type:
                #start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                # Compute start_date directly — 7 days before
                start_date = end_dt - timedelta(days=7)

                start_str = start_date.strftime("%Y-%m-%d")
                end_str = end_dt.strftime("%Y-%m-%d")
                
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
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            return [
                f"`{datetime_column}` >= {{start_date:String}}",
                f"`{datetime_column}` <= {{end_date:String}}"
            ], {"start_date": start_str, "end_date": end_str}
            
            
    def get_table_data_with_datetime_SS_Alerts_table(self, table_name: str, start_date: datetime, 
                               end_date: datetime, data_columns, datetime_column, requested_start: datetime = None,
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
            
            #datetime_column = self.repository._detect_timestamp_column(table_name)
            
            #print(datetime_column)
            
            if not datetime_column:
                logger.warning(f"No datetime column found in table '{table_name}'")
                return {
                    "exists": True, "data": [], "datetime_column": None,
                    "columns": column_names, "table_name": table_name,
                    "used_fallback": False, "actual_start": start_date, "actual_end": end_date
                }
            
            datetime_column_type = self.repository.get_column_type(table_name, datetime_column)
            data_columns_type = []
            
            for i in range(len(data_columns)):
                data_columns_type.append(self.repository.get_column_type(table_name, data_columns[i]))
            
            
            if not data_columns:
                logger.warning(f"No data columns found in table '{table_name}'")
                return {
                    "exists": True, "data": [], "datetime_column": datetime_column,
                    "columns": data_columns, "table_name": table_name,
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
                "datetime_column_type": datetime_column_type,
                "data_columns": data_columns, 
                "data_columns_type": data_columns_type,
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
            
            
            
    def get_alerts_table_data(self, site_id: str, from_date: str = None, to_date: str = None):
        
        try:
            table = "_SS_Assets_Alerts"
            table_name = site_id.replace("-", "_") + "_" + site_id.replace("-", "_") + table
            
            data_column_names = ["Asset name", "Description", "ID", "Process", "Area", "Active","With losses", 
                            "Density", "Status", "Count", "Type", "Updated on", "Last occurrence"]
            
            datetime_column_name = "Created on"
            
            result_interim = self.get_table_data_with_datetime_SS_Alerts_table(table_name, from_date, to_date, data_column_names, 
                                                                  datetime_column_name)
            
            data_rows = result_interim.get("data")
            datetime_col = result_interim.get("datetime_column")
            datetime_col_type = result_interim.get("datetime_column_type")
            data_col_names = result_interim.get("data_columns")
            data_col_types = result_interim.get("data_columns_type")
            
            all_data_col_names = []
            all_data_col_names.append(datetime_col)
            for item in data_col_names: 
                all_data_col_names.append(item)
            
            all_data_col_types = []
            all_data_col_types.append(datetime_col_type)
            for item in data_col_types: 
                all_data_col_types.append(item)
                
            data_avail = result_interim.get("data_availability_for_given_date")
            from_d = result_interim.get("actual_start")
            to_d = result_interim.get("actual_end")
            
            
            #Transposing the data_rows
            data_columns = list(zip(*data_rows))
            
            table = []

            for i in range(len(data_columns)):
                # Format datetime values in dataSource if this is a datetime column
                data_source = list(data_columns[i][:])
                col_name = all_data_col_names[i]
                col_type = all_data_col_types[i] if i < len(all_data_col_types) else None
                
                # Check if column is datetime by type or name
                is_datetime_col = (
                    col_type and ('DateTime' in col_type or 'Date' in col_type)
                ) or self._is_datetime_column(col_name)
                
                if is_datetime_col:
                    # Format datetime values without timezone
                    formatted_data_source = []
                    for value in data_source:
                        if isinstance(value, datetime):
                            formatted_data_source.append(DateTimeParser.format_datetime_without_timezone(value))
                        elif isinstance(value, str) and value:
                            # Try to parse and reformat datetime strings
                            try:
                                parsed_dt = DateTimeParser.parse_datetime(value)
                                if parsed_dt:
                                    formatted_data_source.append(DateTimeParser.format_datetime_without_timezone(parsed_dt))
                                else:
                                    formatted_data_source.append(value)
                            except:
                                formatted_data_source.append(value)
                        else:
                            formatted_data_source.append(value)
                    data_source = formatted_data_source
                
                record = {
                "columnName": all_data_col_names[i],
                "columnType": all_data_col_types[i],
                "tableName" : table_name,
                "siteName" : site_id,
                "dataSource": data_source
                        }
            
                table.append(record)
                
            formatted_data = {
                "table" : table,
                "data_availability_for_given_date" : data_avail,
                "from_date" : from_d,
                "to_date" : to_d
            }

            
            return formatted_data
        
        except Exception as e:
            logger.exception(f"Error in get_alerts_table_data for {site_id}: {str(e)}")
            return {
                "error": str(e),
            }
            
            
    def get_table_data_with_datetime_SS_Assets_graph(self, table_name: str, start_date: datetime, 
                               end_date: datetime, data_columns, datetime_column, requested_start: datetime = None,
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
            print(datetime_column_type)
            data_columns_type = []
            
            for i in range(len(data_columns)):
                data_columns_type.append(self.repository.get_column_type(table_name, data_columns[i]))
            
            
            if not data_columns:
                logger.warning(f"No data columns found in table '{table_name}'")
                return {
                    "exists": True, "data": [], "datetime_column": datetime_column,
                    "columns": data_columns, "table_name": table_name,
                    "used_fallback": False, "actual_start": start_date, "actual_end": end_date
                }
                
            
                
            where_conditions, query_params = self.build_datetime_where_conditions_graph_data(
                datetime_column, datetime_column_type, None, end_date
            )
            
            
            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=data_columns,
                datetime_column=datetime_column,
                where_conditions= where_conditions,
                query_params= query_params
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
                "datetime_column_type": datetime_column_type,
                "data_columns": data_columns, 
                "data_columns_type": data_columns_type,
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
            
            
    
                
    def get_alerts_graph_data(self, site_name: str, asset_name: str, to_date: str = None):
        try:
            table = "_SS_Assets_Data"
            table_name = site_name.replace("-", "_") + "_" + site_name.replace("-", "_") + table
            
            data_column_names = ["Asset name", "Signal", "Measured value", "Expected value", 
                            "Min limit", "Max limit", "Residual value"]
            datetime_column_name = "DateTime"
            
            result_interim = self.get_table_data_with_datetime_SS_Assets_graph(
                table_name, None, to_date, data_column_names, datetime_column_name
            )
        
            data_rows = result_interim.get("data")
            data_avail = result_interim.get("data_availability_for_given_date")
            from_d = result_interim.get("actual_start")
            to_d = result_interim.get("actual_end")
            
            # Extract unique signal types dynamically based on asset_name
            unique_signals = set()
            for row in data_rows:
                if row[1] == asset_name and row[2]:  # row[1] = Asset name, row[2] = Signal
                    unique_signals.add(row[2])
            signal_types = sorted(list(unique_signals))
            
            # Validate that signals were found
            if not signal_types:
                logger.warning(f"No signals found for asset_name '{asset_name}' in site '{site_name}'")
                return {
                    "graph": {},
                    "data_availability_for_given_date": data_avail,
                    "from_date": from_d,
                    "to_date": to_d,
                    "message": f"No signals found for asset '{asset_name}'"
                }
            
            # Get column types from result_interim
            datetime_type = result_interim.get("datetime_column_type")
            data_column_types = result_interim.get("data_columns_type")
            
            # Convert to parquet types
            datetime_parquet_type = self.repository._convert_clickhouse_to_parquet_type(datetime_type) if datetime_type else "unknown"
            
            # Column definitions with their types
            value_columns = [
                ("ActualValue", data_column_types[2] if data_column_types else "unknown"),
                ("ExpectedValue", data_column_types[3] if data_column_types else "unknown"),
                ("MinLimit", data_column_types[4] if data_column_types else "unknown"),
                ("MaxLimit", data_column_types[5] if data_column_types else "unknown"),
                ("ResidualValue", data_column_types[6] if data_column_types else "unknown")
            ]
            
            # Convert value column types to parquet
            value_columns_parquet = [
                (col_name, self.repository._convert_clickhouse_to_parquet_type(col_type))
                for col_name, col_type in value_columns
            ]
            
            # Initialize data structure for each signal type
            signal_data = {signal: {col_name: [] for col_name, _ in [("DateTime", datetime_parquet_type)] + value_columns_parquet} 
                        for signal in signal_types}
            
            # Initialize ResidualChart data
            residual_data = {
                "DateTime": [],
                "ResidualValue": []
            }
            
            # Populate data arrays by filtering rows
            for row in data_rows:
                if row[1] == asset_name:  # Check Asset name
                    signal = row[2]  # Signal type
                    
                    # Format datetime value without timezone
                    datetime_value = row[0]
                    if isinstance(datetime_value, datetime):
                        formatted_datetime = DateTimeParser.format_datetime_without_timezone(datetime_value)
                    elif isinstance(datetime_value, str) and datetime_value:
                        try:
                            parsed_dt = DateTimeParser.parse_datetime(datetime_value)
                            formatted_datetime = DateTimeParser.format_datetime_without_timezone(parsed_dt) if parsed_dt else datetime_value
                        except:
                            formatted_datetime = datetime_value
                    else:
                        formatted_datetime = datetime_value
                    
                    if signal in signal_types:
                        signal_data[signal]["DateTime"].append(formatted_datetime)
                        signal_data[signal]["ActualValue"].append(row[3])
                        signal_data[signal]["ExpectedValue"].append(row[4])
                        signal_data[signal]["MinLimit"].append(row[5])
                        signal_data[signal]["MaxLimit"].append(row[6])
                        signal_data[signal]["ResidualValue"].append(row[7])
                    
                    # Add to ResidualChart (all signals)
                    residual_data["DateTime"].append(formatted_datetime)
                    residual_data["ResidualValue"].append(row[7])
            
            # Build columnData structure - exactly 5 keys per column like heatmap
            result_data = {}
            
            # Add columns for each signal type
            for signal in signal_types:
                result_data[signal] = []
                
                # DateTime column for this signal
                result_data[signal].append({
                    "siteName": site_name,
                    "tableName": self.humanize(table_name),
                    "columnName": self.humanize("DateTime"),
                    "columnType": datetime_parquet_type,
                    "dataSource": signal_data[signal]["DateTime"]
                })
                
                # Value columns for this signal
                for col_name, col_type in value_columns_parquet:
                    result_data[signal].append({
                        "siteName": site_name,
                        "tableName": self.humanize(table_name),
                        "columnName": self.humanize(col_name),
                        "columnType": col_type,
                        "dataSource": signal_data[signal][col_name]
                    })
            
            # Add ResidualChart columns
            result_data["ResidualChart"] = []
            
            result_data["ResidualChart"].append({
                "siteName": site_name,
                "tableName": self.humanize(table_name),
                "columnName": self.humanize("DateTime"),
                "columnType": datetime_parquet_type,
                "dataSource": residual_data["DateTime"]
            })
            
            result_data["ResidualChart"].append({
                "siteName": site_name,
                "tableName": self.humanize(table_name),
                "columnName": self.humanize("ResidualValue"),
                "columnType": value_columns_parquet[4][1],  # ResidualValue type
                "dataSource": residual_data["ResidualValue"]
            })
            
            formatted_data = {
                "graph": result_data,
                "data_availability_for_given_date": data_avail,
                "from_date": from_d,
                "to_date": to_d
            }
            
            return formatted_data
            
        except Exception as e:
            logger.exception(f"Error in get_alerts_graph_data for {site_name} and {asset_name}: {str(e)}")
            return {"error": str(e)}
        
    def get_table_data_with_datetime_SS_Assets_history(self, table_name: str, data_columns) -> Dict[str, Any]:
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
                    "used_fallback": False
                }
            
            cached_columns = self.get_cached_table_columns(table_name)
            if not cached_columns:
                logger.warning(f"No columns found for table '{table_name}'")
                return {
                    "exists": False, "data": [], "datetime_column": None,
                    "columns": [], "table_name": table_name,
                    "used_fallback": False
                }
                
                
            column_names = [col["name"] for col in cached_columns]
            
            data_columns_type = []
            
            for i in range(len(data_columns)):
                data_columns_type.append(self.repository.get_column_type(table_name, data_columns[i]))
            
            
            if not data_columns:
                logger.warning(f"No data columns found in table '{table_name}'")
                return {
                    "exists": True, "data": [], 
                    "columns": data_columns, "table_name": table_name,
                    "used_fallback": False, 
                }

            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=data_columns,
                datetime_column= None,
                where_conditions= None,
                query_params= None
            )
            
            # CRITICAL: Extract metadata from repository response
            result_rows = result_dict.get("result_rows", [])
            data_availability = result_dict.get("data_availability_for_given_date", True)
            # from_date_str = result_dict.get("from_date")
            # to_date_str = result_dict.get("to_date")
            
            logger.info(f"Retrieved {len(result_rows)} rows from table '{table_name}' (data_availability: {data_availability}")
            return {
                "exists": True, 
                "data": result_rows, 
                "data_columns": data_columns, 
                "data_columns_type": data_columns_type,
                "table_name": table_name,
                "data_availability_for_given_date": data_availability
            }
            
        except Exception as e:
            logger.error(f"Error getting data from table '{table_name}': {e}")
            return {
                "exists": False, "data": [], "datetime_column": None,
                "columns": [], "error": str(e), "table_name": table_name,
                "used_fallback": False, 
                "data_availability_for_given_date": False
            }
            
    
    def get_asset_history_data(self, site_name: str):
        try:
            table = "_SS_Assest_History"
            table_name = site_name.replace("-", "_") + "_" + site_name.replace("-", "_") + table
            
            data_column_names = ["Asset name", "Commissioned date", "Last maintenance date", "Number of failures", "Total run hours", "Status"]
            
            result_interim = self.get_table_data_with_datetime_SS_Assets_history(table_name, data_column_names)
            
            data_rows = result_interim.get("data")
            data_col_names = result_interim.get("data_columns")
            data_col_types = result_interim.get("data_columns_type")
            
            all_data_col_names = data_col_names
            all_data_col_types = data_col_types
         
            data_avail = result_interim.get("data_availability_for_given_date")
            
            #Transposing the data_rows
            data_columns = list(zip(*data_rows))
            
            table = []

            for i in range(len(data_columns)):
                # Format datetime values in dataSource if this is a datetime column
                data_source = list(data_columns[i][:])
                col_name = all_data_col_names[i] if i < len(all_data_col_names) else None
                col_type = all_data_col_types[i] if i < len(all_data_col_types) else None
                
                # Check if column is datetime by type or name
                is_datetime_col = (
                    col_type and ('DateTime' in col_type or 'Date' in col_type)
                ) or self._is_datetime_column(col_name)
                
                if is_datetime_col:
                    # Format datetime values without timezone
                    formatted_data_source = []
                    for value in data_source:
                        if isinstance(value, datetime):
                            formatted_data_source.append(DateTimeParser.format_datetime_without_timezone(value))
                        elif isinstance(value, str) and value:
                            # Try to parse and reformat datetime strings
                            try:
                                parsed_dt = DateTimeParser.parse_datetime(value)
                                if parsed_dt:
                                    formatted_data_source.append(DateTimeParser.format_datetime_without_timezone(parsed_dt))
                                else:
                                    formatted_data_source.append(value)
                            except:
                                formatted_data_source.append(value)
                        else:
                            formatted_data_source.append(value)
                    data_source = formatted_data_source
                
                record = {
                "Column Name": all_data_col_names[i],
                "Column Type": all_data_col_types[i],
                "Table Name" : table_name,
                "Site Name" : site_name,
                "Data Source": data_source
                        }
            
                table.append(record)
                
            formatted_data = {
                "table" : table,
                "data_availability_for_given_date" : data_avail,
                
            }

            
            return formatted_data
        
        except Exception as e:
            logger.exception(f"Error in getting assets_history_data for {site_name}: {str(e)}")
            return {
                "error": str(e),
            }
            
            
        