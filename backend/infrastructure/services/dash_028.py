from datetime import datetime, timedelta, time

from infrastructure.orm.repositories.dash_028 import Dash028Repository
from typing import List, Optional, Any, Dict
from constants import Dash028Config
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.utils.datetime_utils import DateTimeParser
import re
from dateutil import parser
import pandas as pd


class Dash_028Service:
    # Centralized mapping so controllers stay thin
    SITE_TABLE_MAPPING = Dash028Config.SITE_TABLE_MAPPING

    def __init__(self):
        self.repo = Dash028Repository()
        self.clickhouse_repo = ClickHouseRepository()

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
    
    @staticmethod
    def adjust_time_range(start_time: datetime, end_time: datetime):
        """
        If start_time and end_time are on the same datetime (no range),
        return start_time as beginning of the day (00:00:00) 
        and keep end_time unchanged.
        """
        if start_time == end_time:
            start_time = datetime.combine(start_time.date(), datetime.min.time())
        return start_time, end_time

    
    def get_rack_performance_RO_overall(self,site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)
       
        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("performance_overall", {})
        clickhouse_table_name = table_info.get(ro_pass)
        columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)

        datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)
        
        available_columns = [col["name"] for col in columns]
        final_columns = []

        if datetime_column in available_columns:
            final_columns.append(datetime_column)
            final_columns.extend([c for c in available_columns if c != datetime_column])

        
        start_time = start_time
        end_time = end_time

        start_time,end_time = self.adjust_time_range(start_time, end_time)

        used_last_db_fallback = True

        data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, final_columns, datetime_column, start_time, end_time)
        if not data:
             
            last_date = self.get_last_timestamp_from_DB(clickhouse_table_name, final_columns, datetime_column, start_time, end_time)
            data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, final_columns, datetime_column, last_date, last_date)
            
            if not data:
                return {
                    "message": f"No data found for date {DateTimeParser.format_datetime_without_timezone(last_date)}",
                }
            else :
                used_last_db_fallback = False

        rows  = data
        if not rows:
            window_msg = ""
            if start_time and end_time:
                window_msg = f" for date range {DateTimeParser.format_datetime_without_timezone(start_time)} to {DateTimeParser.format_datetime_without_timezone(end_time)}"
            return {
                "message": f"No data found{window_msg}",
                "lastdaysdb": False
            }

            # Step 4: Get column metadata
        types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}

        # Step 5: Build column data in frontend-friendly structure
        column_data = {}
        for col_name in available_columns:
            clickhouse_type = types_lookup.get(col_name, "unknown")
            parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
            column_data[col_name] = {
                "siteName": site_id,
                "tableName": self.humanize(clickhouse_table_name),
                "columnName": self.humanize(col_name),
                "columnType": parquet_type,
                "dataSource": []
            }

        # Step 6: Fill dataSource for each column
        if RO_identifier == "pass1":
            required_columns = [ "Pass 1 Permeate Flow Percent", "Pass 1 Permeate Flow", "Pass 1 SEC", "Pass 1 SEC Percent","RO Inlet Temperature", "RO Inlet Conductivity", "Conductivity"]
        elif RO_identifier == "pass2":
            required_columns = ["Pass 2 Permeate Flow", "Pass 2 Permeate Flow Percent", "Pass 2 SEC", "Pass 2 SEC Percent", "RO Inlet Temperature", "RO Inlet Conductivity", "pH", "ph", "PH", "Ph"]
        for row in rows:
            for idx, col_name in enumerate(available_columns):
                value = row[idx] if idx < len(row) else None
                column_data[col_name]["dataSource"].append(value)

        result = [column_data[col] for col in available_columns]
        datetime_col = next((col for col in result if col["columnName"].lower() == "datetime"), None)

        if datetime_col and datetime_col["dataSource"]:
            timestamps = []
            for t in datetime_col["dataSource"]:
                if isinstance(t, datetime):
                    timestamps.append(t)
                elif isinstance(t, str):
                    try:
                        timestamps.append(parser.isoparse(t))
                    except Exception:
                        continue

            if timestamps:
                latest_index = max(range(len(timestamps)), key=lambda i: timestamps[i])
                end_time = timestamps[latest_index]

                for col in result:
                    values = col["dataSource"]
                    col["dataSource"] = [values[latest_index] if latest_index < len(values) else None]
        
        days = 3
        graph = self.get_rack_performance_RO_overall_lastNdays(site_id, clickhouse_table_name, available_columns, columns, final_columns, datetime_column, start_time, end_time, days)
        filtered_data = [item for item in result if item["columnName"] in required_columns]
        
        filtered_data = []
        for item in result:
            col_name = item["columnName"]
            if col_name in required_columns:
                # Copy so we don’t modify original list
                new_item = item.copy()
                ds = new_item["dataSource"]

                if ds and isinstance(ds[0], (int, float)):
                    value = ds[0]
                    if "percent" in col_name.lower():
                        new_item["dataSource"] = [round(value, 2)]
                    else:
                        new_item["dataSource"] = [round(value)]


                filtered_data.append(new_item)   

        start_time = end_time - timedelta(days=3)
        return {
            "cards": filtered_data,
            "graph": graph,
            "message": "message",
            "data_availability_for_given_date" : used_last_db_fallback,
            "from_date": start_time,
            "to_date": end_time,
        }

    def get_rack_performance_RO_overall_lastNdays(self, site_id, clickhouse_table_name, available_columns, columns,
                                                  final_columns, datetime_column, start_time, end_time, days):
        start_time = end_time - timedelta(days=days)

        data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, final_columns, datetime_column,
                                                             start_time, end_time)

        rows = data
        types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}

        column_data = {}
        for col_name in available_columns:
            clickhouse_type = types_lookup.get(col_name, "unknown")
            parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)

            # Override columnType for datetime columns
            if col_name.lower() == "datetime":
                parquet_type = "timestamp[ns]"

            if site_id.lower() == "uaq":
                stream_name = self.extract_stream_number(clickhouse_table_name)

                # Check if column is "Datetime"
                if col_name.lower() == "datetime":
                    column_name = self.humanize(col_name)
                else:
                    column_name = f"{stream_name} {self.humanize(col_name)}"

                column_data[col_name] = {
                    "siteName": site_id,
                    "tableName": self.humanize(clickhouse_table_name),
                    "columnName": column_name,
                    "columnType": parquet_type,
                    "dataSource": []
                }
            else:
                stream_name = ""
                column_data[col_name] = {
                    "siteName": site_id,
                    "tableName": self.humanize(clickhouse_table_name),
                    "columnName": self.humanize(col_name),
                    "columnType": parquet_type,
                    "dataSource": []
                }

        for row in rows:
            for idx, col_name in enumerate(available_columns):
                value = row[idx] if idx < len(row) else None
                # Convert datetime objects to string format for consistency
                if value is not None and isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                column_data[col_name]["dataSource"].append(value)

        result = [column_data[col] for col in available_columns]

        if site_id == "UAQ" or site_id == "uaq":
            required_columns = ["Datetime", f"{stream_name} Pass 1 Permeate Flow", f"{stream_name} Pass 1 SEC",
                                f"{stream_name} Pass 2 Permeate Flow", f"{stream_name} Pass 2 SEC"]
        else:
            required_columns = ["Datetime", "Pass 1 Permeate Flow", "Pass 1 SEC", "Pass 2 Permeate Flow", "Pass 2 SEC"]
        filtered_data = [item for item in result if item["columnName"] in required_columns]
        filtered_data = []
        for item in result:
            col_name = item["columnName"]
            if col_name in required_columns:
                new_item = item.copy()
                ds = new_item["dataSource"]

                if isinstance(ds, list):
                    rounded_values = []
                    for v in ds:
                        if isinstance(v, (int, float)):
                            if "sec" in col_name.lower():
                                rounded_values.append(round(v, 2))
                            else:
                                rounded_values.append(round(v))
                        else:
                            rounded_values.append(v)

                    new_item["dataSource"] = rounded_values

                filtered_data.append(new_item)

        return filtered_data

    def get_last_timestamp_from_DB(self, clickhouse_table_name, final_columns, datetime_column, start_time, end_time):
        last_timestamp = self.repo.get_max_timestamp(clickhouse_table_name, datetime_column)

        return last_timestamp


    def get_rack_performance_RO_table(self,site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)
        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("performance", {})
        clickhouse_table_name = table_info.get(ro_pass)
        columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)

        datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)
        available_columns = [col["name"] for col in columns]
        final_columns = [] 


        start_time = start_time
        end_time = end_time


        start_time,end_time = self.adjust_time_range(start_time, end_time)

        if datetime_column in available_columns:
            final_columns.append(datetime_column)
            final_columns.extend([c for c in available_columns if c != datetime_column])

        used_last_db_fallback = True
        data = self.repo.fetch_all_in_range(clickhouse_table_name, final_columns, datetime_column, start_time, end_time)

        if not data:
             
            test_date = self.get_last_timestamp_from_DB(clickhouse_table_name, final_columns, datetime_column, start_time, end_time)
            data = self.repo.fetch_all_in_range(clickhouse_table_name, final_columns, datetime_column, test_date, test_date)

            if not data:
                return {
                    "message": f"No data found for date {DateTimeParser.format_datetime_without_timezone(test_date)}",
                }  
            else:
                used_last_db_fallback = False
            

        rows  = data
        if not rows:
            window_msg = ""
            if start_time and end_time:
                window_msg = f" for date range {DateTimeParser.format_datetime_without_timezone(start_time)} to {DateTimeParser.format_datetime_without_timezone(end_time)}"
            return {
                "message": f"No data found{window_msg}",
                "lastdaysdb": False
            }

            # Step 4: Get column metadata

        types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}

        # Step 5: Build column data in frontend-friendly structure
        column_data = {}
        for col_name in available_columns:
            clickhouse_type = types_lookup.get(col_name, "unknown")
            parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
            column_data[col_name] = {
                "siteName": site_id,
                "tableName": self.humanize(clickhouse_table_name),
                "columnName": self.humanize(col_name),
                "columnType": parquet_type,
                "dataSource": []
            }

        # Step 6: Fill dataSource for each column
        for row in rows:
            for idx, col_name in enumerate(final_columns):
                value = row[idx] if idx < len(row) else None
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
                column_data[col_name]["dataSource"].append(value)

        # Step 7: Convert to list format for frontend
        result = [column_data[col] for col in final_columns]
 
        datetime_col = next((col for col in result if col["columnName"].lower() == "datetime"), None)

        if datetime_col and datetime_col["dataSource"]:
            timestamps = []
            for t in datetime_col["dataSource"]:
                if isinstance(t, datetime):
                    timestamps.append(t)
                elif isinstance(t, str):
                    try:
                        timestamps.append(parser.isoparse(t))
                    except Exception:
                        continue

            if timestamps:
                # Find the maximum timestamp
                max_timestamp = max(timestamps)
                end_time = max_timestamp
                
                # Get all indices where timestamp equals the maximum
                latest_indices = [i for i, t in enumerate(timestamps) if t == max_timestamp]

                # Reduce each column's dataSource to only records with latest timestamp
                for col in result:
                    values = col["dataSource"]
                    col["dataSource"] = [values[i] for i in latest_indices if i < len(values)]

        if RO_identifier == "pass1":
            required_columns = ["Rack", "SEC Measured", "SEC Expected", "SEC Deviation", 
                                "Feed Conductivity", "Feed Pressure", "Recovery", "Split", "Erd mixing", "Total permeate flow", "Front Permeate Conductivity", "Rear Permeate Conductivity", "Overall Permeate Conductivity", "Rack booster pump speed", "Dp norm", "Permeate flow", "Salt Passage Norm Percent", ]
            column_order = [
                "Rack",
                "Feed Pressure",
                "Recovery",
                "Total permeate flow",
                "Front Permeate Conductivity",
                "Rear Permeate Conductivity",
                "Overall Permeate Conductivity",
                "Split",
                "Erd mixing",
                "Rack booster pump speed",
                "Feed Conductivity",
                "Dp norm",
                "Permeate flow",
                "Salt Passage Norm Percent",
                "SEC Measured",
                "SEC Expected",
                "SEC Deviation"
            ]
        
        elif RO_identifier == "pass2":
            required_columns = ["Rack", "SEC Measured", "Feed Conductivity", "Feed Pressure", "Recovery", "1st stream permeate flow", "2nd stream permeate flow", "Total permeate flow", "Total Permeate Conductivity", "1st stream dp", "2nd stream dp", "Overall dp", "Rack booster pump speed"]

            column_order = [
                "Rack",
                "Feed Pressure",
                "Overall dp",
                "1st stream dp",
                "2nd stream dp",
                "Total permeate flow",
                "1st stream permeate flow",
                "2nd stream permeate flow",
                "Recovery",
                "Total Permeate Conductivity",
                "Feed Conductivity",
                "Rack booster pump speed",
                "SEC Measured",
            ]


        

        
        filtered_data = []
        for item in result:
            col_name = item["columnName"]
            if col_name in required_columns:
                new_item = item.copy()
                ds = new_item["dataSource"]

                # Only process if dataSource is a list
                if isinstance(ds, list):
                    rounded_values = []
                    for v in ds:
                        if isinstance(v, (int, float)):

                            rounded_values.append(round(v, 2))  
                        else:
                            rounded_values.append(v)  # keep non-numeric as-is

                    new_item["dataSource"] = rounded_values

                filtered_data.append(new_item)
        
        
        ordered_data = sorted(
            filtered_data,
            key=lambda x: column_order.index(x["columnName"])
            if x["columnName"] in column_order else len(column_order)
        )


        start_time = end_time - timedelta(days=3)
        return {
            "table": ordered_data,
            "message": "message",
            "data_availability_for_given_date" : used_last_db_fallback,
            "from_date": start_time,
            "to_date": end_time,
        }

    def get_rack_performance_RO_operational_status(self,site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)
        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("status", {})
        clickhouse_table_name = table_info.get(ro_pass)
        columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)
        datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)

        available_columns = [col["name"] for col in columns]
        final_columns = [] 


        start_time = start_time
        end_time = end_time


        start_time,end_time = self.adjust_time_range(start_time, end_time)


        

        if datetime_column in available_columns:
            final_columns.append(datetime_column)
            final_columns.extend([c for c in available_columns if c != datetime_column])

        used_last_db_fallback = True

        data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, available_columns, datetime_column, start_time, end_time)
        if not data:
            days = 7
            end_time = self.get_last_timestamp_from_DB(clickhouse_table_name, final_columns, datetime_column, start_time, end_time)
            start_time = end_time - timedelta(days=days)
            data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, available_columns, datetime_column, start_time, end_time)
            if not data:
                return {
                    "message": f"No data found for date {DateTimeParser.format_datetime_without_timezone(end_time)}",
                }  
            else:
                used_last_db_fallback = False
            

        rows  = data
        if not rows:
            window_msg = ""
            if start_time and end_time:
                window_msg = f" for date range {DateTimeParser.format_datetime_without_timezone(start_time)} to {DateTimeParser.format_datetime_without_timezone(end_time)}"
            return {
                "message": f"No data found{window_msg}",
                "lastdaysdb": False
            }

        types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}

     
        column_data = {}
        for col_name in available_columns:
            clickhouse_type = types_lookup.get(col_name, "unknown")
            parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
            column_data[col_name] = {
                "siteName": site_id,
                "tableName": self.humanize(clickhouse_table_name),
                "columnName": self.humanize(col_name),
                "columnType": parquet_type,
                "dataSource": []
            }

        # Step 6: Fill dataSource for each column
        for row in rows:
            for idx, col_name in enumerate(available_columns):
                value = row[idx] if idx < len(row) else None
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
                column_data[col_name]["dataSource"].append(value)

        # Step 7: Convert to list format for frontend
        result = [column_data[col] for col in available_columns]

        formated_data = self.extract_running_intervals_columnwise(result, start_time, end_time,RO_identifier)

        for item in formated_data:
            item['siteName'] = site_id
            item['tableName'] = self.humanize(clickhouse_table_name)

        start_time = end_time - timedelta(days=7)
        return {
            "operation_status": formated_data,
            "message": "message",
            "data_availability_for_given_date": used_last_db_fallback,
            "from_date": start_time,
            "to_date": end_time,
        }
    
    def extract_running_intervals_columnwise(self, raw_data, start_range, end_range, RO_identifier):

        if RO_identifier == "pass1":
            column_name = "1st Pass"
            column_value = "RO 1st Pass"
        elif RO_identifier == "pass2":
            column_name = "2nd Pass"
            column_value = "RO 2nd Pass"
        
        data_dict = {item["columnName"]: item["dataSource"] for item in raw_data}
        df = pd.DataFrame(data_dict)
        df.rename(columns={"Asset": "Rack", "Datetime": "Date"}, inplace=True)

        # Normalize datetime and clean up statuses
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        # Convert to pandas datetime and ensure no timezone
        start_range = pd.Timestamp(start_range).tz_localize(None) if pd.Timestamp(start_range).tz else pd.Timestamp(start_range)
        end_range = pd.Timestamp(end_range).tz_localize(None) if pd.Timestamp(end_range).tz else pd.Timestamp(end_range)
        df["Status"] = df["Status"].str.strip()

        # Filter within selected range
        df = df[(df["Date"] >= start_range) & (df["Date"] <= end_range)].copy()
        df.sort_values(["Rack", "Date"], inplace=True)

        results = []

        # Extract start-stop intervals for each rack
        for rack, rack_df in df.groupby("Rack"):
            rack_df = rack_df.reset_index(drop=True)
            running = False
            start_time = None

            for _, row in rack_df.iterrows():
                status = row["Status"].lower()
                time = row["Date"]

                # Treat "in-service" or "running" as active states
                if status in ["in-service", "running"]:
                    if not running:
                        running = True
                        start_time = time
                else:
                    if running:
                        results.append({
                            "Rack": rack,
                            "Start Time": start_time,
                            "Stop Time": time
                        })
                        running = False
                        start_time = None

            # If still running at the end
            if running:
                results.append({
                    "Rack": rack,
                    "Start Time": start_time,
                    "Stop Time": None
                })

        # Convert results to column-wise format
        if not results:
            return []  # Return empty if no data found

        result_df = pd.DataFrame(results)

        # Convert Start Time to string, but handle Stop Time specially to preserve None
        start_times = result_df["Start Time"].astype(str).tolist()
        stop_times = [
            None if pd.isna(stop) or stop is None else str(stop) 
            for stop in result_df["Stop Time"]
        ]

        # Build final structure
        final_output = [
            {
                "columnName": column_name,
                "columnType": "string",
                "dataSource": [column_value] * len(result_df)
            },
            {
                "columnName": "Asset",
                "columnType": "string",
                "dataSource": result_df["Rack"].tolist()
            },
            {
                "columnName": "Start Time",
                "columnType": "string",
                "dataSource": start_times
            },
            {
                "columnName": "Stop Time",
                "columnType": "string",
                "dataSource": stop_times
            }
        ]

        return final_output

   ############################### UAQ Versions #################################



    def UAQ_get_performance_RO_overall(self, site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)
       
        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("performance_overall", {})
        clickhouse_table_names = table_info.get(ro_pass)
        final_data = []
        final_graph = []
        for clickhouse_table_name in clickhouse_table_names:
            columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)

            datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)
            
            available_columns = [col["name"] for col in columns]
            final_columns = []

            if datetime_column in available_columns:
                final_columns.append(datetime_column)
                final_columns.extend([c for c in available_columns if c != datetime_column])

            
            start_time = start_time
            end_time = end_time

            start_time,end_time = self.adjust_time_range(start_time, end_time)

            used_last_db_fallback = False

            data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, final_columns, datetime_column, start_time, end_time)
            if not data:
                
                test_date = self.get_last_timestamp_from_DB(clickhouse_table_name, final_columns, datetime_column, start_time, end_time)
                data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, final_columns, datetime_column, test_date, test_date)
                
                if not data:
                    return {
                        "message": f"No data found for date {DateTimeParser.format_datetime_without_timezone(test_date)}",
                    }
                else :
                    used_last_db_fallback = True

            rows  = data
            if not rows:
                window_msg = ""
                if start_time and end_time:
                    window_msg = f" for date range {DateTimeParser.format_datetime_without_timezone(start_time)} to {DateTimeParser.format_datetime_without_timezone(end_time)}"
                return {
                    "message": f"No data found{window_msg}",
                    "lastdaysdb": False
                }

                # Step 4: Get column metadata
            types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}

            # Step 5: Build column data in frontend-friendly structure
            stream_name = self.extract_stream_number(clickhouse_table_name)
            column_data = {}
            for col_name in available_columns:
                clickhouse_type = types_lookup.get(col_name, "unknown")
                parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
                column_data[col_name] = {
                    "siteName": site_id,
                    "tableName": self.humanize(clickhouse_table_name),
                    "columnName": self.humanize(col_name),
                    "columnType": parquet_type,
                    "dataSource": []
                }

            # Step 6: Fill dataSource for each column
            if RO_identifier == "pass1":
                required_columns = [ "Pass 1 Permeate Flow Percent", "Pass 1 Permeate Flow", "Pass 1 SEC", "Pass 1 SEC Percent","RO Inlet Temperature", "RO Inlet Conductivity", "Conductivity"]
            elif RO_identifier == "pass2":
                required_columns = ["Pass 2 Permeate Flow", "Pass 2 Permeate Flow Percent", "Pass 2 SEC", "Pass 2 SEC Percent", "RO Inlet Temperature", "RO Inlet Conductivity", "pH", "ph", "PH", "Ph"]
            for row in rows:
                for idx, col_name in enumerate(available_columns):
                    value = row[idx] if idx < len(row) else None
                    column_data[col_name]["dataSource"].append(value)

            # Step 7: Convert to list format for frontend
            result = [column_data[col] for col in available_columns]
            datetime_col = next((col for col in result if col["columnName"].lower() == "datetime"), None)

            if datetime_col and datetime_col["dataSource"]:
                timestamps = []
                for t in datetime_col["dataSource"]:
                    if isinstance(t, datetime):
                        timestamps.append(t)
                    elif isinstance(t, str):
                        try:
                            timestamps.append(parser.isoparse(t))
                        except Exception:
                            continue

                if timestamps:
                    latest_index = max(range(len(timestamps)), key=lambda i: timestamps[i])
                    end_time = timestamps[latest_index]

                    # Reduce each column’s dataSource to only the latest value
                    for col in result:
                        values = col["dataSource"]
                        col["dataSource"] = [values[latest_index] if latest_index < len(values) else None]
            # Step 8: Build final message
            days = 3
            graph = self.get_rack_performance_RO_overall_lastNdays(site_id, clickhouse_table_name, available_columns, columns, final_columns, 
            datetime_column, start_time, end_time, days)
            final_graph.extend(graph)
            filtered_data = [item for item in result if item["columnName"] in required_columns]
            
            filtered_data = []
            for item in result:
                col_name = item["columnName"]
                if col_name in required_columns:
                    # Copy so we don’t modify the original item
                    new_item = item.copy()
                    ds = new_item["dataSource"]

                  
                    new_item["columnName"] = f"{stream_name} {col_name}"   # or f"{stream_id} - {col_name}"

                    # Handle numeric rounding
                    if ds and isinstance(ds[0], (int, float)):
                        value = ds[0]
                        if "percent" in col_name.lower():
                            new_item["dataSource"] = [round(value, 2)]
                        else:
                            new_item["dataSource"] = [round(value)]
                    # Non-numeric (e.g., datetime) remains unchanged

                    filtered_data.append(new_item)
            if RO_identifier == "pass1" and stream_name == "Stream3":
                has_conductivity = any("RO Inlet Conductivity" in item["columnName"] for item in filtered_data)
                if not has_conductivity:
                    # Build the missing entry
                    new_entry = {
                        "siteName": site_id,
                        "tableName": self.humanize(clickhouse_table_name),
                        "columnName": f"{stream_name} RO Inlet Conductivity",
                        "columnType": "double",
                        "dataSource": [None],
                    }

                    # Find where to insert (right after RO Inlet Temperature)
                    insert_index = next(
                        (i + 1 for i, item in enumerate(filtered_data)
                        if "RO Inlet Temperature" in item["columnName"]),
                        len(filtered_data)  # fallback: append at end
                    )
                    filtered_data.insert(insert_index, new_entry)
            final_data.extend(filtered_data) 
        

        updated_graph = self.merge_stream_data(final_graph)
        start_time = end_time - timedelta(days=3)
        return {
            "cards": final_data  ,
            "graph": updated_graph,
            "message": "message",
            "data_availability_for_given_date" : used_last_db_fallback,
            "from_date": start_time,
            "to_date": end_time,
        }
        

    def UAQ_get_performance_RO_table(self, site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)
    
        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("performance", {})
        clickhouse_table_names = table_info.get(ro_pass)
        
        # Dictionary to accumulate data by column name
        merged_column_data = {}
        stream_data = []  # To track stream labels
        used_last_db_fallback = False
        actual_start_time = start_time
        actual_end_time = end_time
        
        for stream_idx, clickhouse_table_name in enumerate(clickhouse_table_names, 1):
            columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)
            datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)
            available_columns = [col["name"] for col in columns]
            final_columns = [] 

            start_time_adjusted, end_time_adjusted = self.adjust_time_range(start_time, end_time)

            if datetime_column in available_columns:
                final_columns.append(datetime_column)
                final_columns.extend([c for c in available_columns if c != datetime_column])

            data = self.repo.fetch_all_in_range(clickhouse_table_name, final_columns, datetime_column, 
                                            start_time_adjusted, end_time_adjusted)

            if not data:
                test_date = self.get_last_timestamp_from_DB(clickhouse_table_name, final_columns, 
                                                        datetime_column, start_time_adjusted, end_time_adjusted)
                data = self.repo.fetch_all_in_range(clickhouse_table_name, final_columns, datetime_column, 
                                                test_date, test_date)
                if not data:
                    continue  # Skip this table if no data
                else:
                    used_last_db_fallback = True
                    actual_end_time = test_date

            rows = data
            if not rows:
                continue  # Skip this table if no rows

            types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}
            num_records = len(rows)
            
            # Add stream labels for this table's records
            stream_data.extend([f"Stream{stream_idx}"] * num_records)

            # Process each column
            for col_name in available_columns:
                humanized_name = self.humanize(col_name)
                
                # Initialize column if not exists
                if humanized_name not in merged_column_data:
                    clickhouse_type = types_lookup.get(col_name, "unknown")
                    parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
                    merged_column_data[humanized_name] = {
                        "siteName": site_id,
                        "tableName": self.humanize(clickhouse_table_name.split('_')[0]),  # Generic name
                        "columnName": humanized_name,
                        "columnType": parquet_type,
                        "dataSource": []
                    }
                
                # Append data from this table to the column
                col_idx = final_columns.index(col_name)
                for row in rows:
                    value = row[col_idx] if col_idx < len(row) else None
                    merged_column_data[humanized_name]["dataSource"].append(value)

        # Check if we have any data at all
        if not merged_column_data:
            window_msg = f" for date range {DateTimeParser.format_datetime_without_timezone(start_time)} to {DateTimeParser.format_datetime_without_timezone(end_time)}"
            return {
                "message": f"No data found{window_msg}",
                "lastdaysdb": False
            }

        # Add the Stream column
        
        merged_column_data["Stream"] = {
            "siteName": site_id,
            "tableName": "Performance",
            "columnName": "Stream",
            "columnType": "string",
            "dataSource": stream_data
        }

        # Filter for latest timestamp
        datetime_col_key = next((key for key in merged_column_data.keys() if key.lower() == "datetime"), None)
        
        if datetime_col_key and merged_column_data[datetime_col_key]["dataSource"]:
            timestamps = []
            for t in merged_column_data[datetime_col_key]["dataSource"]:
                if isinstance(t, datetime):
                    timestamps.append(t)
                elif isinstance(t, str):
                    try:
                        timestamps.append(parser.isoparse(t))
                    except Exception:
                        continue

            if timestamps:
                max_timestamp = max(timestamps)
                actual_end_time = max_timestamp
                latest_indices = [i for i, t in enumerate(timestamps) if t == max_timestamp]

                # Filter all columns to only latest records
                for col_key in merged_column_data:
                    values = merged_column_data[col_key]["dataSource"]
                    merged_column_data[col_key]["dataSource"] = [values[i] for i in latest_indices if i < len(values)]

        # Define required columns and order based on RO_identifier
        if RO_identifier == "pass1":
            required_columns = [ "Rack", "Stream","SEC Measured", "SEC Expected", "SEC Deviation", 
                                "Feed Conductivity", "Feed Pressure", "Recovery", "Split", "Erd mixing", 
                                "Total permeate flow", "Front Permeate Conductivity", "Rear Permeate Conductivity", 
                                "Overall Permeate Conductivity", "Rack booster pump speed", "Dp norm", 
                                "Permeate flow", "Salt Passage Norm Percent"]
            column_order = [ "Rack","Stream" ,"Feed Pressure", "Recovery", "Total permeate flow",
                        "Front Permeate Conductivity", "Rear Permeate Conductivity", 
                        "Overall Permeate Conductivity", "Split", "Erd mixing", "Rack booster pump speed",
                        "Feed Conductivity", "Dp norm", "Permeate flow", "Salt Passage Norm Percent",
                        "SEC Measured", "SEC Expected", "SEC Deviation"]
        
        elif RO_identifier == "pass2":
            required_columns = [ "Rack", "Stream", "SEC Measured", "Feed Conductivity", "Feed Pressure", 
                            "Recovery", "1st stream permeate flow", "2nd stream permeate flow", 
                            "Total permeate flow", "Total Permeate Conductivity", "1st stream dp", 
                            "2nd stream dp", "Overall dp", "Rack booster pump speed"]
            column_order = [ "Rack", "Stream","Feed Pressure", "Overall dp", "1st stream dp", "2nd stream dp",
                        "Total permeate flow", "1st stream permeate flow", "2nd stream permeate flow",
                        "Recovery", "Total Permeate Conductivity", "Feed Conductivity", 
                        "Rack booster pump speed", "SEC Measured"]

        # Filter and round numeric values
        filtered_data = []
        for col_name, item in merged_column_data.items():
            if col_name in required_columns:
                new_item = item.copy()
                ds = new_item["dataSource"]

                if isinstance(ds, list):
                    rounded_values = []
                    for v in ds:
                        if isinstance(v, (int, float)):
                            rounded_values.append(round(v, 2))
                        else:
                            rounded_values.append(v)
                    new_item["dataSource"] = rounded_values

                filtered_data.append(new_item)
        
        # Sort by column order
        ordered_data = sorted(
            filtered_data,
            key=lambda x: column_order.index(x["columnName"])
            if x["columnName"] in column_order else len(column_order)
        )

        start_time = end_time - timedelta(days=3)
        return {
            "table": ordered_data,
            "message": "message",
            "data_availability_for_given_date": used_last_db_fallback,
            "from_date": actual_start_time,
            "to_date": actual_end_time,
        }
    

    def UAQ_get_rack_performance_RO_operational_status(self, site_id, RO_identifier, start_time, end_time):
        ro_pass = self.extract_pass_number(RO_identifier)
        tables_info = self.SITE_TABLE_MAPPING.get(site_id)
        table_info = tables_info.get("status", {})
        clickhouse_table_names = table_info.get(ro_pass)  # Changed to plural - expecting list
        
        # Accumulate all data across tables
        all_rows = []
        all_columns_info = None
        used_last_db_fallback = False
        actual_start_time = start_time
        actual_end_time = end_time
        
        for stream_idx, clickhouse_table_name in enumerate(clickhouse_table_names, 1):
            columns = self.clickhouse_repo.get_table_columns(clickhouse_table_name)
            datetime_column = self.clickhouse_repo.get_datetime_column(clickhouse_table_name)
            available_columns = [col["name"] for col in columns]
            
            # Store column info from first table (assuming all tables have same structure)
            if all_columns_info is None:
                all_columns_info = {
                    "columns": columns,
                    "datetime_column": datetime_column,
                    "available_columns": available_columns
                }
            
            start_time_adjusted, end_time_adjusted = self.adjust_time_range(start_time, end_time)
            
            data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, available_columns, datetime_column, 
                                            start_time_adjusted, end_time_adjusted)
            
            if not data:
                days = 7
                end_time_db = self.get_last_timestamp_from_DB(clickhouse_table_name, available_columns, 
                                                            datetime_column, start_time_adjusted, end_time_adjusted)
                start_time_db = end_time_db - timedelta(days=days)
                data = self.repo.fetch_all_in_range_timezone_removed(clickhouse_table_name, available_columns, datetime_column, 
                                                start_time_db, end_time_db)
                if not data:
                    continue  # Skip this table if no data
                else:
                    used_last_db_fallback = True
                    actual_end_time = end_time_db
                    actual_start_time = start_time_db
            
            # Add stream identifier to each row
            for row in data:
                row_with_stream = list(row) + [f"Stream{stream_idx}"]
                all_rows.append(row_with_stream)
        
        # Check if we have any data
        if not all_rows or all_columns_info is None:
            window_msg = f" for date range {DateTimeParser.format_datetime_without_timezone(start_time)} to {DateTimeParser.format_datetime_without_timezone(end_time)}"
            return {
                "message": f"No data found{window_msg}",
                "lastdaysdb": False
            }
        
        # Add Stream to available columns
        available_columns = all_columns_info["available_columns"] + ["Stream"]
        columns = all_columns_info["columns"] + [{"name": "Stream", "type": "String"}]
        datetime_column = all_columns_info["datetime_column"]
        
        types_lookup = {c["name"]: c.get("type", "unknown") for c in columns}
        
        # Build column data structure
        column_data = {}
        for col_name in available_columns:
            clickhouse_type = types_lookup.get(col_name, "unknown")
            parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
            column_data[col_name] = {
                "siteName": site_id,
                "tableName": self.humanize(clickhouse_table_names[0]) if clickhouse_table_names else "Performance",
                "columnName": self.humanize(col_name),
                "columnType": parquet_type if col_name != "Stream" else "string",
                "dataSource": []
            }
        
        # Fill dataSource for each column from all accumulated rows
        for row in all_rows:
            for idx, col_name in enumerate(available_columns):
                value = row[idx] if idx < len(row) else None
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
                column_data[col_name]["dataSource"].append(value)
        
        # Convert to list format for frontend
        result = [column_data[col] for col in available_columns]
        
        formated_data = self.UAQ_extract_running_intervals_columnwise(result, actual_start_time, actual_end_time, RO_identifier)
        
        for item in formated_data:
            item['siteName'] = site_id
            item['tableName'] = self.humanize(clickhouse_table_names[0]) if clickhouse_table_names else "Performance"
        
        actual_start_time = actual_end_time - timedelta(days=7)
        return {
            "operation_status": formated_data,
            "message": "message",
            "data_availability_for_given_date": used_last_db_fallback,
            "from_date": actual_start_time,
            "to_date": actual_end_time,
        }

    def UAQ_extract_running_intervals_columnwise(self, shared_data, start_range, end_range, RO_identifier):
        # Convert incoming column-based structure into a row-wise DataFrame
        if RO_identifier == "pass1":
            column_name = "1st Pass"
            column_value = "RO 1st Pass"
        elif RO_identifier == "pass2":
            column_name = "2nd Pass"
            column_value = "RO 2nd Pass"
        
        data_dict = {item["columnName"]: item["dataSource"] for item in shared_data}
        df = pd.DataFrame(data_dict)
        df.rename(columns={"Asset": "Rack", "Datetime": "Date"}, inplace=True)
        
        # Normalize datetime and clean up statuses
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        # Convert to pandas datetime and ensure no timezone
        start_range = pd.Timestamp(start_range).tz_localize(None) if pd.Timestamp(start_range).tz else pd.Timestamp(start_range)
        end_range = pd.Timestamp(end_range).tz_localize(None) if pd.Timestamp(end_range).tz else pd.Timestamp(end_range)        
        df["Status"] = df["Status"].str.strip()
        
        # Filter within selected range
        df = df[(df["Date"] >= start_range) & (df["Date"] <= end_range)].copy()
        df.sort_values(["Rack", "Date"], inplace=True)
        
        results = []
        
        # Extract start-stop intervals for each rack AND stream combination
        for (rack, stream), group_df in df.groupby(["Rack", "Stream"]):
            group_df = group_df.reset_index(drop=True)
            running = False
            start_time = None
            
            for _, row in group_df.iterrows():
                status = row["Status"].lower()
                time = row["Date"]
                
                # Treat "in-service" or "running" as active states
                if status in ["in-service", "running"]:
                    if not running:
                        running = True
                        start_time = time
                else:
                    if running:
                        results.append({
                            "Rack": rack,
                            "Stream": stream,
                            "Start Time": start_time,
                            "Stop Time": time
                        })
                        running = False
                        start_time = None
            
            # If still running at the end
            if running:
                results.append({
                    "Rack": rack,
                    "Stream": stream,
                    "Start Time": start_time,
                    "Stop Time": None
                })
        
        # Convert results to column-wise format
        if not results:
            return []  # Return empty if no data found
        
        result_df = pd.DataFrame(results)
        
        # Convert Start Time to string, but handle Stop Time specially to preserve None
        start_times = result_df["Start Time"].astype(str).tolist()
        stop_times = [
            None if pd.isna(stop) or stop is None else str(stop) 
            for stop in result_df["Stop Time"]
        ]
        
        # Build final structure with Stream column
        final_output = [
            {
                "columnName": column_name,
                "columnType": "string",
                "dataSource": [column_value] * len(result_df)
            },
            {
                "columnName": "Stream",
                "columnType": "string",
                "dataSource": result_df["Stream"].tolist()
            },
            {
                "columnName": "Asset",
                "columnType": "string",
                "dataSource": result_df["Rack"].tolist()
            },
            {
                "columnName": "Start Time",
                "columnType": "string",
                "dataSource": start_times
            },
            {
                "columnName": "Stop Time",
                "columnType": "string",
                "dataSource": stop_times
            }
        ]
        
        return final_output
    
    def merge_stream_data(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        # Step 1: Collect all timestamps from all streams
        all_dates = set()
        for item in data_list:
            if item["columnName"].lower() == "datetime":
                for d in item["dataSource"]:
                    if isinstance(d, datetime):
                        all_dates.add(d)
                    else:
                        try:
                            all_dates.add(datetime.fromisoformat(str(d)))
                        except Exception:
                            raise ValueError(f"Invalid datetime format: {d}")

        # Step 2: Sort and normalize all dates back to ISO strings
        all_dates = sorted(all_dates)
        all_dates_str = [d.strftime("%Y-%m-%d %H:%M:%S") for d in all_dates]


        # Step 3: Create mapping from tableName → datetime → index
        from collections import defaultdict
        datetime_maps = defaultdict(dict)
        stream_data = defaultdict(list)

        for item in data_list:
            table = item["tableName"]
            if item["columnName"].lower() == "datetime":
                dt_list = []
                for d in item["dataSource"]:
                    if isinstance(d, datetime):
                        dt_list.append(d)
                    else:
                        dt_list.append(datetime.fromisoformat(str(d)))
                datetime_maps[table] = {d.strftime("%Y-%m-%d %H:%M:%S"): i for i, d in enumerate(dt_list)}
            else:
                stream_data[table].append(item)

        # Step 4: Create single global Datetime column
        merged_data = [{
            "siteName": data_list[0]["siteName"] if data_list else "Unknown",
            "tableName": "Merged Overall Data",
            "columnName": "Datetime",
            "columnType": "timestamp[ns]",  # Changed from "Datetime"
            "dataSource": all_dates_str
        }]

        # Step 5: Align all stream columns to master datetime
        date_index = {d: i for i, d in enumerate(all_dates_str)}

        for table, items in stream_data.items():
            dt_map = datetime_maps.get(table, {})

            for item in items:

                aligned_ds = [None] * len(all_dates_str)

                for dt_str, idx in dt_map.items():
                    if dt_str in date_index:
                        aligned_ds[date_index[dt_str]] = item["dataSource"][idx]

                new_item = {
                    "siteName": item["siteName"],
                    "tableName": "Merged Overall Data",
                    "columnName": item["columnName"],
                    "columnType": item["columnType"],
                    "dataSource": aligned_ds
                }
                merged_data.append(new_item)

        return merged_data