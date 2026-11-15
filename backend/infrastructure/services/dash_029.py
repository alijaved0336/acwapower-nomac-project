from datetime import datetime, timedelta, time

from infrastructure.orm.repositories.dash_028 import Dash028Repository
from typing import List, Optional, Any, Dict
from constants import Dash029Config
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.orm.repositories.dash_029 import Dash029Repository
import re
from dateutil import parser
import pandas as pd


class Dash_029Service:
    # Centralized mapping so controllers stay thin
    SITE_TABLE_MAPPING = Dash029Config.SITE_TABLE_MAPPING

    def __init__(self):
        self.repo = Dash028Repository()
        self.clickhouse_repo = ClickHouseRepository()
        self.dash029_repo = Dash029Repository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.repo.close()
        return False

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
    
    def get_pass_power_consumption():
        pass


    def get_average_table_heatmap():
        pass
    
    def get_weighted_ro_conductivity_heatmap(self, site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)

        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("sec_pwr_compare_table", {})
        clickhouse_table_name = table_info.get(ro_pass)
        columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)

        datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)
        
        available_columns = [col["name"] for col in columns]
        
        columns_to_fetch = [col for col in available_columns if col.lower() != datetime_column.lower()]

        # Use dash029_repo to avoid AMBIGUOUS_COLUMN_NAME error with String-stored DateTime columns
        result_dict = self.dash029_repo.get_weighted_heatmap_data(
            clickhouse_table_name=clickhouse_table_name,
            columns_to_fetch=columns_to_fetch,
            datetime_column=datetime_column,
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )

        result_rows = result_dict.get("result_rows", [])
        to_date = result_dict.get("to_date")
        from_date = result_dict.get("from_date")
        data_availability_for_given_date = result_dict.get("data_availability_for_given_date", True)

        if not result_rows:
            return {
                "data": [],
                "metadata": {
                    "data_availability_for_given_date": data_availability_for_given_date,
                    "from_date": from_date,
                    "to_date": to_date
                }
            }

        # Find the datetime column index
        datetime_col_index = None
        datetime_col_name = None
        for idx, col_name in enumerate(available_columns):
            if col_name.lower().strip() == datetime_column.lower().strip() or col_name.lower().strip() == "date":
                datetime_col_index = idx
                datetime_col_name = col_name
                break

        # Find the latest datetime and get all rows with that datetime
        if datetime_col_index is not None:
            latest_datetime = None
            for row in result_rows:
                dt_value = row[datetime_col_index]
                if isinstance(dt_value, datetime):
                    if latest_datetime is None or dt_value > latest_datetime:
                        latest_datetime = dt_value
                elif isinstance(dt_value, str):
                    try:
                        parsed_dt = parser.isoparse(dt_value)
                        if latest_datetime is None or parsed_dt > latest_datetime:
                            latest_datetime = parsed_dt
                    except Exception:
                        continue
            
            # Filter rows to only those with the latest datetime
            if latest_datetime:
                filtered_rows = []
                for row in result_rows:
                    dt_value = row[datetime_col_index]
                    row_datetime = None
                    if isinstance(dt_value, datetime):
                        row_datetime = dt_value
                    elif isinstance(dt_value, str):
                        try:
                            row_datetime = parser.isoparse(dt_value)
                        except Exception:
                            continue
                    
                    if row_datetime == latest_datetime:
                        filtered_rows.append(row)
                
                result_rows = filtered_rows

        # Define required columns (excluding datetime)
        if site_id.lower() == "uaq":
            required_columns = [
                "Stream","Rack", "Exp Normalized Permeate Flow", "Exp Normalized Dp", 
                "Exp Normalized SP", "Exp NDP", "Exp Feed Pressure", 
                "Act Normalized Permeate Flow", "Act Normalized Dp", 
                "Act Normalized SP", "Act NDP", "Act Feed Pressure", 
                "Diff Normalized Permeate Flow", "Diff Normalized Dp", 
                "Diff Normalized SP", "Diff NDP", "Diff Feed Pressure"
            ]
        else:
            required_columns = [
            "Rack", "Exp Normalized Permeate Flow", "Exp Normalized Dp", 
            "Exp Normalized SP", "Exp NDP", "Exp Feed Pressure", 
            "Act Normalized Permeate Flow", "Act Normalized Dp", 
            "Act Normalized SP", "Act NDP", "Act Feed Pressure", 
            "Diff Normalized Permeate Flow", "Diff Normalized Dp", 
            "Diff Normalized SP", "Diff NDP", "Diff Feed Pressure"
        ]

        types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}

        # Create a filtered list of columns excluding datetime
        columns_without_datetime = [col for col in available_columns if col != datetime_col_name]

        # Build column data structure
        column_data = {}
        for col_name in columns_without_datetime:
            clickhouse_type = types_lookup.get(col_name, "unknown")
            parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
            column_data[col_name] = {
                "siteName": site_id,
                "tableName": self.humanize(clickhouse_table_name),
                "columnName": self.humanize(col_name),
                "columnType": parquet_type,
                "dataSource": []
            }

        # Populate data for all filtered rows (all racks at latest datetime)
        for row in result_rows:
            col_data_idx = 0  # Index for columns_without_datetime
            for idx, col_name in enumerate(available_columns):
                # Skip datetime column entirely
                if col_name == datetime_col_name:
                    continue
                
                # Get value from row at the original index
                value = row[idx] if idx < len(row) else None
                
                # Add to column_data using the filtered column name
                column_name_key = columns_without_datetime[col_data_idx]
                if column_name_key in column_data:
                    column_data[column_name_key]["dataSource"].append(value)
                
                col_data_idx += 1

        # Filter to only required columns
        filtered_result = [column_data[col] for col in columns_without_datetime 
                        if col in column_data and self.humanize(col) in required_columns]

        return {
            "data": self._round_numeric_values(filtered_result),
            "metadata": {
                "data_availability_for_given_date": data_availability_for_given_date,
                "from_date": from_date,
                "to_date": to_date
            }
        }
    

    def get_averaged_ro_conductivity_heatmap(self, site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)
        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("sec_pwr_compare_table_avg", {})
        clickhouse_table_name = table_info.get(ro_pass)
        
        columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)
        datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)
        available_columns = [col["name"] for col in columns]
        stream_col_index = None
        
        columns_to_fetch = [col for col in available_columns if col.lower() != datetime_column.lower()]
        
        # Use dash029_repo to avoid AMBIGUOUS_COLUMN_NAME error with String-stored DateTime columns
        result_dict = self.dash029_repo.get_weighted_heatmap_data(
            clickhouse_table_name=clickhouse_table_name,
            columns_to_fetch=columns_to_fetch,
            datetime_column=datetime_column,
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )
        
        result_rows = result_dict.get("result_rows", [])
        to_date = result_dict.get("to_date")
        from_date = result_dict.get("from_date")
        data_availability_for_given_date = result_dict.get("data_availability_for_given_date", True)

        if not result_rows:
            return {
                "data": [],
                "metadata": {
                    "data_availability_for_given_date": data_availability_for_given_date,
                    "from_date": from_date,
                    "to_date": to_date
                }
            }

        # Find the datetime column index
        datetime_col_index = None
        datetime_col_name = None
        for idx, col_name in enumerate(available_columns):
            if col_name.lower().strip() == datetime_column.lower().strip() or col_name.lower().strip() == "date":
                datetime_col_index = idx
                datetime_col_name = col_name
            if col_name.lower().strip() == "stream":
                stream_col_index = idx
        
        # Find the latest datetime and filter rows
        if datetime_col_index is not None:
            latest_datetime = None
            for row in result_rows:
                dt_value = row[datetime_col_index]
                if isinstance(dt_value, datetime):
                    if latest_datetime is None or dt_value > latest_datetime:
                        latest_datetime = dt_value
                elif isinstance(dt_value, str):
                    try:
                        parsed_dt = parser.isoparse(dt_value)
                        if latest_datetime is None or parsed_dt > latest_datetime:
                            latest_datetime = parsed_dt
                    except Exception:
                        continue
            
            # Filter rows to only those with the latest datetime
            if latest_datetime:
                filtered_rows = []
                for row in result_rows:
                    dt_value = row[datetime_col_index]
                    row_datetime = None
                    if isinstance(dt_value, datetime):
                        row_datetime = dt_value
                    elif isinstance(dt_value, str):
                        try:
                            row_datetime = parser.isoparse(dt_value)
                        except Exception:
                            continue
                    if row_datetime == latest_datetime:
                        # For UAQ: Exclude rows that already have "Total Average" or "Total_Average" in Stream column
                        if site_id.lower() == "uaq" and stream_col_index is not None:
                            stream_value = row[stream_col_index] if stream_col_index < len(row) else None
                            if isinstance(stream_value, str) and "total" in stream_value.lower().replace("_", " "):
                                continue  # Skip this row
                        filtered_rows.append(row)
                result_rows = filtered_rows
        
        types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}
        
        # Define columns to exclude from averaging and from results
        if site_id.lower() == "uaq":
            # For UAQ: exclude datetime and rack from results
            columns_to_exclude = [datetime_col_name, "Rack"]
            grouping_column = "Stream"  # Group by Stream for UAQ
            
            # Define required columns (excluding datetime and rack)
            required_columns = [
                "Stream",
                "Exp Normalized Permeate Flow", "Exp Normalized Dp", "Exp Normalized SP", 
                "Exp NDP", "Exp Feed Pressure",
                "Act Normalized Permeate Flow", "Act Normalized Dp", "Act Normalized SP", 
                "Act NDP", "Act Feed Pressure",
                "Diff Normalized Permeate Flow", "Diff Normalized Dp", "Diff Normalized SP", 
                "Diff NDP", "Diff Feed Pressure"
            ]
        else:
            # For non-UAQ: exclude datetime and rack from results
            columns_to_exclude = [datetime_col_name, "Rack"]
            grouping_column = "Rack"  # Group by Rack for non-UAQ (to calculate average)
            
            # Define required columns (excluding datetime and rack)
            required_columns = [
                "Exp Normalized Permeate Flow", "Exp Normalized Dp", "Exp Normalized SP", 
                "Exp NDP", "Exp Feed Pressure",
                "Act Normalized Permeate Flow", "Act Normalized Dp", "Act Normalized SP", 
                "Act NDP", "Act Feed Pressure",
                "Diff Normalized Permeate Flow", "Diff Normalized Dp", "Diff Normalized SP", 
                "Diff NDP", "Diff Feed Pressure"
            ]
        
        # Create column indices mapping
        column_indices = {col_name: idx for idx, col_name in enumerate(available_columns)}
        
        # Process data based on site
        if site_id.lower() == "uaq":
            # For UAQ: Keep stream data as-is, add "Total Average" row
            column_data = {}
            columns_without_excluded = [col for col in available_columns if col not in columns_to_exclude]
            
            # Initialize column data structure
            for col_name in columns_without_excluded:
                clickhouse_type = types_lookup.get(col_name, "unknown")
                parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
                column_data[col_name] = {
                    "siteName": site_id,
                    "tableName": self.humanize(clickhouse_table_name),
                    "columnName": self.humanize(col_name),
                    "columnType": parquet_type,
                    "dataSource": []
                }

            stream_col_idx = column_indices.get("Stream")
            if stream_col_idx is not None:
                # Custom sort to handle "Stream X" format
                def get_stream_number(row):
                    stream_value = row[stream_col_idx] if stream_col_idx < len(row) else ""
                    if isinstance(stream_value, str) and "Stream" in stream_value:
                        try:
                            # Extract number from "Stream X"
                            return int(stream_value.split()[-1])
                        except (ValueError, IndexError):
                            return float('inf')
                    return float('inf')
                
                result_rows = sorted(result_rows, key=get_stream_number)
            
            # Populate data from filtered rows (all streams at latest datetime)
            for row in result_rows:
                for col_name in columns_without_excluded:
                    col_idx = column_indices.get(col_name)
                    if col_idx is not None:
                        value = row[col_idx] if col_idx < len(row) else None
                        column_data[col_name]["dataSource"].append(value)
            
            # Calculate and add "Total Average" for numeric columns
            stream_col_idx = column_indices.get("Stream")
            if stream_col_idx is not None:
                column_data["Stream"]["dataSource"].append("Total Average")
            
            for col_name in columns_without_excluded:
                if col_name == "Stream":
                    continue
                
                # Calculate average for numeric columns
                values = column_data[col_name]["dataSource"]
                numeric_values = [v for v in values if isinstance(v, (int, float)) and v is not None]
                
                if numeric_values:
                    avg_value = sum(numeric_values) / len(numeric_values)
                    column_data[col_name]["dataSource"].append(avg_value)
                else:
                    column_data[col_name]["dataSource"].append(None)
            
        else:
            # For non-UAQ: Calculate average across all racks
            column_data = {}
            columns_without_excluded = [col for col in available_columns if col not in columns_to_exclude]
            
            # Initialize column data structure
            for col_name in columns_without_excluded:
                clickhouse_type = types_lookup.get(col_name, "unknown")
                parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
                column_data[col_name] = {
                    "siteName": site_id,
                    "tableName": self.humanize(clickhouse_table_name),
                    "columnName": self.humanize(col_name),
                    "columnType": parquet_type,
                    "dataSource": []
                }
            
            # Calculate averages for each column
            for col_name in columns_without_excluded:
                col_idx = column_indices.get(col_name)
                if col_idx is not None:
                    values = [row[col_idx] for row in result_rows if col_idx < len(row)]
                    
                    # Calculate average for numeric values
                    numeric_values = [v for v in values if isinstance(v, (int, float)) and v is not None]
                    
                    if numeric_values:
                        avg_value = sum(numeric_values) / len(numeric_values)
                        column_data[col_name]["dataSource"].append(avg_value)
                    else:
                        # For non-numeric columns, take first value or None
                        column_data[col_name]["dataSource"].append(values[0] if values else None)
        
        # Filter to only required columns
        filtered_result = [
            column_data[col] for col in columns_without_excluded 
            if col in column_data and self.humanize(col) in required_columns
        ]
        
        return {
            "data": self._round_numeric_values(filtered_result),
            "metadata": {
                "data_availability_for_given_date": data_availability_for_given_date,
                "from_date": from_date,
                "to_date": to_date
            }
        }
    


    def get_ro_power_consumption_metrics(self, site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)

        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("sec_pwr_compare", {})
        # clickhouse_table_name = table_info.get(ro_pass)
        clickhouse_table_names = table_info.get(ro_pass)
        if not isinstance(clickhouse_table_names, list):
            clickhouse_table_names = [clickhouse_table_names]
        
        # Check if site has multiple streams (like UAQ)
        has_multiple_streams = len(clickhouse_table_names) > 1
        
        final_data = []
        streams_data = {}
        metadata = {
            "data_availability_for_given_date": True,
            "from_date": None,
            "to_date": None
        }
        
        for clickhouse_table_name in clickhouse_table_names:
            columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)


            datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)
            
            available_columns = [col["name"] for col in columns]
            
            where_conditions, query_params = [], {}
            columns_to_fetch = [col for col in available_columns if col.lower() != datetime_column.lower()]
            
            result_dict = self.dash029_repo.get_power_consumption_data(
                clickhouse_table_name=clickhouse_table_name,
                columns_to_fetch=columns_to_fetch,
                datetime_column=datetime_column,
                start_time=start_time,
                end_time=end_time,
                rack_column="Rack",
                limit=10000
            )

            result_rows = result_dict.get("result_rows", [])
            to_date = result_dict.get("to_date")
            from_date = result_dict.get("from_date")
            data_availability_for_given_date = result_dict.get("data_availability_for_given_date", True)

            # Update metadata (use last available for multi-stream, or single for single-stream)
            metadata["data_availability_for_given_date"] = data_availability_for_given_date
            metadata["from_date"] = from_date
            metadata["to_date"] = to_date

            if not result_rows:
                if not has_multiple_streams:
                    return {
                        "data": [],
                        "metadata": {
                            "data_availability_for_given_date": data_availability_for_given_date,
                            "from_date": from_date,
                            "to_date": to_date
                        }
                    }
                continue

            # Find the datetime column index
            datetime_col_index = None
            datetime_col_name = None
            for idx, col_name in enumerate(available_columns):
                if col_name.lower().strip() == datetime_column.lower().strip() or col_name.lower().strip() == "datetime":
                    datetime_col_index = idx
                    datetime_col_name = col_name
                    break

            # Find the latest datetime and get all rows with that datetime
            if datetime_col_index is not None:
                latest_datetime = None
                for row in result_rows:
                    dt_value = row[datetime_col_index]
                    if isinstance(dt_value, datetime):
                        if latest_datetime is None or dt_value > latest_datetime:
                            latest_datetime = dt_value
                    elif isinstance(dt_value, str):
                        try:
                            parsed_dt = parser.isoparse(dt_value)
                            if latest_datetime is None or parsed_dt > latest_datetime:
                                latest_datetime = parsed_dt
                        except Exception:
                            continue
                
                # Filter rows to only those with the latest datetime
                if latest_datetime:
                    filtered_rows = []
                    for row in result_rows:
                        dt_value = row[datetime_col_index]
                        row_datetime = None
                        if isinstance(dt_value, datetime):
                            row_datetime = dt_value
                        elif isinstance(dt_value, str):
                            try:
                                row_datetime = parser.isoparse(dt_value)
                            except Exception:
                                continue
                        
                        if row_datetime == latest_datetime:
                            filtered_rows.append(row)
                    
                    result_rows = filtered_rows

            # Define required columns (excluding datetime)

            required_columns = ["Rack", "Base", "Aging", "dp Fouling", "ERD Mixing", "ERD Recovery"]
            types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}

            # Create a filtered list of columns excluding datetime
            columns_without_datetime = [col for col in available_columns if col != datetime_col_name]

            # Build column data structure
            column_data = {}
            for col_name in columns_to_fetch:
                clickhouse_type = types_lookup.get(col_name, "unknown")
                parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
                column_data[col_name] = {
                    "siteName": site_id,
                    "tableName": self.humanize(clickhouse_table_name),
                    "columnName": self.humanize(col_name),
                    "columnType": parquet_type,
                    "dataSource": []
                }

            # Populate data for all filtered rows (all racks at latest datetime)
            for row in result_rows:
                for idx, col_name in enumerate(columns_to_fetch):
                    # Get value from row at the correct index
                    value = row[idx] if idx < len(row) else None
                    
                    # Add to column_data
                    if col_name in column_data:
                        column_data[col_name]["dataSource"].append(value)

            # Filter to only required columns (case-insensitive comparison)
            required_columns_lower = [rc.lower() for rc in required_columns]
            filtered_result = [column_data[col] for col in columns_to_fetch 
                            if col in column_data and self.humanize(col).lower() in required_columns_lower]
            rounded_result = self._round_numeric_values(filtered_result)
            
            # Extract stream number from table name for UAQ sites
            if has_multiple_streams:
                stream_number = self.extract_stream_number(clickhouse_table_name)
                if stream_number:
                    streams_data[stream_number] = rounded_result
                else:
                    # Fallback: use table name as key
                    streams_data[clickhouse_table_name] = rounded_result
            else:
                final_data.extend(rounded_result)

        # Return grouped by streams for multi-stream sites, flat array for single-stream sites
        if has_multiple_streams:
            # For multi-stream sites, return streams as keys in data
            return {
                "data": streams_data,
                "metadata": metadata
            }
        else:
            return {
                "data": final_data,
                "metadata": metadata
            }

    def _round_numeric_values(self, data):
        """
        Recursively rounds numeric values in dataSource to max 2 decimal places.
        Whole numbers remain without decimals.
        """
        def round_value(v):
            if isinstance(v, (int, float)):
                if float(v).is_integer():
                    return int(v)
                return round(v, 2)
            return v

        for item in data:
            if isinstance(item, dict) and "dataSource" in item:
                item["dataSource"] = [round_value(v) for v in item["dataSource"]]
        return data
