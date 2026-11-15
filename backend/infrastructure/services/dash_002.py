import logging
import pytz
from datetime import datetime, timedelta

from constants import Dash002Config
from collections import defaultdict
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.orm.repositories.dash_002 import Dash002Repository
from infrastructure.utils.datetime_utils import DateTimeParser

logger = logging.getLogger(__name__)


class Dash002Service:
    """Modified service to use ClickHouse repository with proper KPI structure"""

    def __init__(self):
        self.clickhouse_repository = ClickHouseRepository()
        self.dash_022_repository = Dash002Repository()

    def __del__(self):
        """Cleanup repository connection when service is destroyed"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def round_value(value, decimals=2):
        """
        Round numerical values to specified decimal places.
        Returns None for non-numeric values.

        Args:
            value: The value to round
            decimals: Number of decimal places (default: 2)

        Returns:
            Rounded value or original value if not numeric
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            try:
                return round(value, decimals)
            except (TypeError, ValueError):
                return value
        return value
    
    @staticmethod
    def get_value_from_row(row, index, column_name=None):
        """
        Safely extract value from a data row which could be list, tuple, or dict.
        
        Args:
            row: The data row (list, tuple, or dict)
            index: The index to access (for list/tuple)
            column_name: The column name (for dict)
            
        Returns:
            The value at the specified position or None
        """
        if isinstance(row, dict):
            # For dict, try column_name first, then fall back to getting by position
            if column_name and column_name in row:
                return row[column_name]
            # If no column_name or not found, get by position
            values = list(row.values())
            return values[index] if index < len(values) else None
        elif isinstance(row, (list, tuple)):
            # For list/tuple, just access by index
            return row[index] if index < len(row) else None
        return None

    def get_process_condition_and_unit_in_service_data(self, site_id):
        """Get process condition and unit in service data with proper error handling."""
        try:
            table = "_Process_Overview"
            table_name = site_id.replace("-", "_") + "_" + site_id.replace("-", "_") + table

            # Safe dictionary access with validation
            site_mapping = Dash002Config.SITE_TABLE_MAPPING.get(site_id.lower())
            if not site_mapping:
                logger.error(f"Site mapping not found for {site_id}")
                return {
                    "error": f"Site mapping not found for {site_id}",
                    "process_condition": {},
                    "units_in_service": {}
                }

            process_condition_mapping = site_mapping.get("process_condition", {})
            units_in_service_mapping = site_mapping.get("units_in_service", {})
            all_columns = self.extract_all_column_names(process_condition_mapping, units_in_service_mapping)

            if not all_columns:
                logger.warning(f"No columns found for process condition and units in service at {site_id}")
                return {
                    "error": f"No columns found for {site_id}",
                    "process_condition": {},
                    "units_in_service": {}
                }

            latest_data = self.clickhouse_repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=all_columns,
                limit=1,
                datetime_column="Timestamp"
            )

            # Handle ClickHouse response format: {'result_rows': [...], ...}
            if isinstance(latest_data, dict) and 'result_rows' in latest_data:
                latest_data = latest_data['result_rows']

            if not latest_data or len(latest_data) == 0:
                logger.warning(f"No data available for {site_id}")
                return {
                    "message": "No data available",
                    "process_condition": {},
                    "units_in_service": {}
                }

            # Data is a list of tuples: [(timestamp, value1, value2, ...)]
            first_row = latest_data[0]
            latest_datetime = first_row[0] if len(first_row) > 0 else None

            if not isinstance(latest_datetime, datetime):
                logger.warning(f"Invalid datetime for {site_id}")
                return {
                    "message": "No date available",
                    "process_condition": {},
                    "units_in_service": {}
                }

            latest_dt = latest_datetime.astimezone()
            modified = self.is_data_modified(latest_dt)

            column_value_map = self.create_column_value_map(all_columns, latest_data[0])

            process_condition_data = self.build_process_condition_data(process_condition_mapping, column_value_map)
            units_in_service_data = self.build_units_in_service_data(units_in_service_mapping, column_value_map)

            result = {
                "modified": modified,
                "timestamp": DateTimeParser.format_datetime_without_timezone(latest_datetime),
                "process_condition": process_condition_data,
                "units_in_service": units_in_service_data,
            }

            return result
            
        except Exception as e:
            logger.exception(f"Error in get_process_condition_and_unit_in_service_data for {site_id}: {str(e)}")
            return {
                "error": str(e),
                "process_condition": {},
                "units_in_service": {}
            }

    def extract_all_column_names(self, process_condition_mapping, units_in_service_mapping):
        """Extract all unique column names from process condition and units in service mappings."""
        columns = set()

        try:
            for category, streams in process_condition_mapping.items():
                for stream, items in streams.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and "column_name" in item:
                                columns.add(item["column_name"])

            for stream, items in units_in_service_mapping.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and "column_name" in item:
                            columns.add(item["column_name"])
                        elif isinstance(item, str):
                            columns.add(item)
        except Exception as e:
            logger.exception(f"Error extracting column names: {str(e)}")
            
        return list(columns)

    def create_column_value_map(self, columns, data_row):
        """Create a mapping of column names to their values from the data row."""
        column_value_map = {}

        try:
            # Data row is a tuple: (timestamp, value1, value2, ...)
            # Skip first element (timestamp) and map rest to column names
            for idx, col in enumerate(columns):
                # idx + 1 because first element is timestamp
                if idx + 1 < len(data_row):
                    column_value_map[col] = self.round_value(data_row[idx + 1])
        except Exception as e:
            logger.exception(f"Error creating column value map: {str(e)}")

        return column_value_map

    def build_process_condition_data(self, process_condition_mapping, column_value_map):
        """Build the process condition data structure with values mapped to column labels."""
        process_condition_data = {}

        try:
            for category, streams in process_condition_mapping.items():
                process_condition_data[category] = {}

                for stream, items in streams.items():
                    process_condition_data[category][stream] = []

                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and "column_name" in item and "column_label" in item:
                                column_name = item["column_name"]
                                column_label = item["column_label"]
                                value = column_value_map.get(column_name, None)

                                process_condition_data[category][stream].append({
                                    "label": column_label,
                                    "value": value
                                })
        except Exception as e:
            logger.exception(f"Error building process condition data: {str(e)}")

        return process_condition_data

    def build_units_in_service_data(self, units_in_service_mapping, column_value_map):
        """Build the units in service data structure with values mapped to column labels."""
        units_in_service_data = {}

        try:
            for stream, items in units_in_service_mapping.items():
                units_in_service_data[stream] = []

                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and "column_name" in item and "column_label" in item:
                            column_name = item["column_name"]
                            column_label = item["column_label"]
                            value = column_value_map.get(column_name, None)

                            units_in_service_data[stream].append({
                                "label": column_label,
                                "value": value
                            })
                        elif isinstance(item, str):
                            column_name = item
                            value = column_value_map.get(column_name, None)

                            units_in_service_data[stream].append({
                                "label": column_name,
                                "value": value
                            })
        except Exception as e:
            logger.exception(f"Error building units in service data: {str(e)}")

        return units_in_service_data

    def get_cards_and_graph_data(self, site_id):
        """Get cards and graph data with proper error handling."""
        try:
            table = "_Process_Overview"
            table_name = site_id.replace("-", "_") + "_" + site_id.replace("-", "_") + table

            site_mapping = Dash002Config.SITE_TABLE_MAPPING.get(site_id.lower())
            if not site_mapping:
                logger.error(f"Site mapping not found for {site_id}")
                return {"error": f"Site mapping not found for {site_id}", "cards": {}, "graph": {}}

            card_mapping = site_mapping.get("graph")
            if not card_mapping or not isinstance(card_mapping, list):
                logger.error(f"Invalid graph mapping for {site_id}")
                return {"error": f"Invalid graph mapping for {site_id}", "cards": {}, "graph": {}}

            columns = []
            column_types = {}
            
            for card in card_mapping:
                if isinstance(card, dict) and card.get("column_name"):
                    columns.append(card["column_name"])
                    column_types[card["column_name"]] = card.get("column_type", "unknown")

            if not columns:
                return {"error": "No valid columns found", "cards": {}, "graph": {}}

            latest_dt = self.dash_022_repository.get_max_timestamp(
                clickhouse_table_name=table_name,
                datetime_column="Timestamp"
            )
            
            if not latest_dt:
                logger.warning(f"No data available for {site_id}")
                return {"message": "No data available", "cards": {}, "graph": {}}
            
            # Ensure timezone
            if latest_dt.tzinfo is None:
                dubai_tz = pytz.timezone('Asia/Dubai')
                latest_dt = dubai_tz.localize(latest_dt)
            
            logger.info(f"Latest (MAX) timestamp: {latest_dt}")
            
            # Calculate past 72 hours
            past_72h_dt = self.calculate_past_72_hours(latest_dt)
            
            # Check if data is modified
            modified = self.is_data_modified(latest_dt)

            # Build WHERE conditions with BOTH bounds
            where_conditions, query_params = self.build_72h_where_conditions(past_72h_dt, latest_dt)
            
            # Query past 72 hours data
            past_72h_data = self.clickhouse_repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=columns,
                datetime_column="Timestamp",
                where_conditions=where_conditions,
                query_params=query_params
            )

            if isinstance(past_72h_data, dict) and 'result_rows' in past_72h_data:
                past_72h_data = past_72h_data['result_rows']

            logger.info(f"Retrieved {len(past_72h_data) if past_72h_data else 0} rows")

            if not past_72h_data:
                return {"message": "No data in range", "cards": {}, "graph": {}}

            # Determine actual data range
            timestamps = [row[0] for row in past_72h_data if isinstance(row[0], datetime)]
            
            if timestamps:
                actual_from_date = min(timestamps)
                actual_to_date = max(timestamps)
                time_span_hours = (actual_to_date - actual_from_date).total_seconds() / 3600
                
                logger.info(f"Actual range: {actual_from_date} to {actual_to_date}")
                logger.info(f"Time span: {time_span_hours:.2f} hours ({time_span_hours/24:.2f} days)")
            else:
                actual_from_date = actual_to_date = None

            # Map to graph data
            graph_data = self.map_columns_to_graph_data(columns, past_72h_data, column_types)

            # Extract cards from last row
            cards = {}
            if past_72h_data:
                latest_row = past_72h_data[-1]
                # Add timestamp to cards if available
                if latest_row and len(latest_row) > 0:
                    timestamp_value = latest_row[0]
                    if isinstance(timestamp_value, datetime):
                        cards["Timestamp"] = DateTimeParser.format_datetime_without_timezone(timestamp_value)
                    elif isinstance(timestamp_value, str) and timestamp_value:
                        try:
                            parsed_dt = DateTimeParser.parse_datetime(timestamp_value)
                            if parsed_dt:
                                cards["Timestamp"] = DateTimeParser.format_datetime_without_timezone(parsed_dt)
                            else:
                                cards["Timestamp"] = timestamp_value
                        except:
                            cards["Timestamp"] = timestamp_value
                
                for idx, col in enumerate(columns):
                    if idx + 1 < len(latest_row):
                        value = latest_row[idx + 1]
                        # Format datetime values without timezone
                        if isinstance(value, datetime):
                            cards[col] = DateTimeParser.format_datetime_without_timezone(value)
                        elif isinstance(value, str) and col == "Timestamp":
                            # Try to parse and format datetime strings for Timestamp column
                            try:
                                parsed_dt = DateTimeParser.parse_datetime(value)
                                if parsed_dt:
                                    cards[col] = DateTimeParser.format_datetime_without_timezone(parsed_dt)
                                else:
                                    cards[col] = value
                            except:
                                cards[col] = value
                        else:
                            cards[col] = self.round_value(value)

            return {
                "modified": modified,
                "from_date": DateTimeParser.format_datetime_without_timezone(actual_from_date) if actual_from_date else None,
                "to_date": DateTimeParser.format_datetime_without_timezone(actual_to_date) if actual_to_date else None,
                "cards": cards,
                "graph": graph_data,
            }

        except Exception as e:
            logger.exception(f"Error in get_cards_and_graph_data for {site_id}: {str(e)}")
            return {"error": str(e), "cards": {}, "graph": {}}

    def prepare_columns_with_timestamp(self, columns):
        """Ensure Timestamp column is at the beginning of the column list."""
        columns_without_timestamp = [col for col in columns if col != "Timestamp"]
        return ["Timestamp"] + columns_without_timestamp

    def calculate_past_72_hours(self, latest_datetime):
        """Calculate the datetime that is 72 hours before the given datetime."""
        return latest_datetime - timedelta(hours=72)

    def is_data_modified(self, latest_datetime):
        """Check if the latest data is from a date other than yesterday."""
        try:
            yesterday = datetime.now(latest_datetime.tzinfo).date() - timedelta(days=1)
            return latest_datetime.date() != yesterday
        except Exception as e:
            logger.exception(f"Error checking data modification: {str(e)}")
            return True

    def build_72h_where_conditions(self, past_72h_datetime, latest_datetime):
        """Build WHERE conditions and query parameters for retrieving past 72 hours of data."""
        where_conditions = [
            "`Timestamp` >= {past_72h_dt:String}",
            "`Timestamp` <= {latest_dt:String}"
        ]
        query_params = {
            "past_72h_dt": past_72h_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            "latest_dt": latest_datetime.strftime('%Y-%m-%d %H:%M:%S')
        }
        return where_conditions, query_params

    def extract_cards_from_graph_data(self, columns, data_rows):
        """Extract the latest values for cards from the graph data."""
        if not data_rows:
            return {}

        latest_row = data_rows[0]

        cards = {}
        for idx, col in enumerate(columns):
            if idx + 1 < len(latest_row):
                # Round the value before adding to cards
                cards[col] = self.round_value(latest_row[idx + 1])

        return cards

    def map_columns_to_graph_data(self, columns, data_rows, column_types):
        """Map column names to graph data structure for time series."""
        if not data_rows:
            return {}

        graph_data = {}

        for col in columns:
            graph_data[col] = {
                "datatype": column_types.get(col, "unknown"),
                "data": []
            }

        for row in data_rows:
            timestamp = row[0] if isinstance(row[0], datetime) else None

            if timestamp:
                for idx, col in enumerate(columns):
                    if idx + 1 < len(row):
                        value = row[idx + 1]
                        # Format datetime values without timezone
                        if isinstance(value, datetime):
                            formatted_value = DateTimeParser.format_datetime_without_timezone(value)
                        elif isinstance(value, str) and col == "Timestamp":
                            # Try to parse and format datetime strings for Timestamp column
                            try:
                                parsed_dt = DateTimeParser.parse_datetime(value)
                                if parsed_dt:
                                    formatted_value = DateTimeParser.format_datetime_without_timezone(parsed_dt)
                                else:
                                    formatted_value = value
                            except:
                                formatted_value = value
                        else:
                            formatted_value = self.round_value(value)
                        
                        graph_data[col]["data"].append({
                            "timestamp": DateTimeParser.format_datetime_without_timezone(timestamp),
                            "value": formatted_value
                        })

        return graph_data

    def get_operational_status_data(self, site_id, to_date=None, area=None):
        """Get operational status data with proper error handling - maintaining 72-hour business logic."""
        try:
            table = "_Process_status"
            table_name = site_id.replace("-", "_") + "_" + site_id.replace("-", "_") + table

            site_mapping = Dash002Config.SITE_TABLE_MAPPING.get(site_id.lower())
            if not site_mapping:
                logger.error(f"Site mapping not found for {site_id}")
                return {
                    "error": f"Site mapping not found for {site_id}",
                    "modified": False,
                    "operational_status": []
                }

            operational_mapping_config = site_mapping.get("operational_status")
            if not operational_mapping_config:
                logger.error(f"Operational status mapping not found for {site_id}")
                return {
                    "error": f"Operational status mapping not found for {site_id}",
                    "modified": False,
                    "operational_status": []
                }

            # Handle the configuration format
            operational_mapping = []
            
            if isinstance(operational_mapping_config, list):
                if operational_mapping_config and isinstance(operational_mapping_config[0], dict):
                    operational_mapping = [col["column_name"] for col in operational_mapping_config]
                else:
                    operational_mapping = operational_mapping_config
            elif isinstance(operational_mapping_config, str):
                operational_mapping = [col.strip() for col in operational_mapping_config.split(",")]
            else:
                logger.error(f"Unexpected operational_mapping_config type: {type(operational_mapping_config)} for {site_id}")
                return {
                    "error": f"Invalid operational status configuration format for {site_id}",
                    "modified": False,
                    "operational_status": []
                }

            if not operational_mapping:
                logger.warning(f"No operational status columns found for {site_id}")
                return {
                    "message": "No operational status columns found",
                    "modified": False,
                    "operational_status": []
                }

            logger.info(f"Using table: {table_name}, columns: {operational_mapping}")

            modified = False
            where_conditions = []
            query_params = {}
            
            requested_from_date = None
            requested_to_date = None
            actual_from_date = None
            actual_to_date = None
            data_availability = False

            if to_date:
                try:
                    end_dt = self._parse_dt(to_date)
                    start_dt = self.calculate_past_72_hours(end_dt)
                    
                    # Ensure timezone
                    if end_dt.tzinfo is None:
                        dubai_tz = pytz.timezone('Asia/Dubai')
                        end_dt = dubai_tz.localize(end_dt)
                    
                    if start_dt.tzinfo is None:
                        dubai_tz = pytz.timezone('Asia/Dubai')
                        start_dt = dubai_tz.localize(start_dt)
                    
                    requested_from_date = start_dt
                    requested_to_date = end_dt

                    wc, qp = self.build_time_range_where_conditions(
                        start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        end_dt.strftime('%Y-%m-%d %H:%M:%S')
                    )
                    
                    if wc:
                        where_conditions.extend(wc)
                    if qp:
                        query_params.update(qp)
                    logger.info(f"Using custom date with 72h range: {start_dt} to {end_dt}")
                    modified = False
                except Exception as e:
                    logger.error(f"Error parsing to_date: {to_date}, error: {str(e)}")
                    return {
                        "error": f"Invalid to_date format: {str(e)}",
                        "modified": False,
                        "operational_status": []
                    }
            else:
                latest_dt = self.dash_022_repository.get_max_timestamp(
                    clickhouse_table_name=table_name,
                    datetime_column="DateTime"
                )
                
                if not latest_dt:
                    logger.warning(f"No operational status data available for {site_id}")
                    return {
                        "message": "No operational status data available",
                        "modified": True,
                        "data_availability_for_given_date": False,
                        "from_date": None,
                        "to_date": None,
                        "operational_status": []
                    }
                
                # Ensure timezone
                if latest_dt.tzinfo is None:
                    dubai_tz = pytz.timezone('Asia/Dubai')
                    latest_dt = dubai_tz.localize(latest_dt)
                
                # Calculate 72 hours back from latest
                past_72h_dt = self.calculate_past_72_hours(latest_dt)
                
                requested_from_date = past_72h_dt
                requested_to_date = latest_dt

                # Add BOTH lower and upper bounds
                where_conditions.append("`DateTime` >= {past_72h_dt:String}")
                where_conditions.append("`DateTime` <= {latest_dt:String}")
                query_params["past_72h_dt"] = past_72h_dt.strftime('%Y-%m-%d %H:%M:%S')
                query_params["latest_dt"] = latest_dt.strftime('%Y-%m-%d %H:%M:%S')

                logger.info(f"Using default 72h range: {past_72h_dt} to {latest_dt}")
                modified = True

            if area:
                where_conditions.append("`Area` = {area:String}")
                query_params["area"] = area

            # Query the database
            data = self.clickhouse_repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=operational_mapping,
                datetime_column="DateTime",
                where_conditions=where_conditions,
                query_params=query_params,
            )

            if isinstance(data, dict) and 'result_rows' in data:
                data = data['result_rows']

            if not data or len(data) == 0:
                logger.warning(f"No operational status data available in the specified range for {site_id}")
                return {
                    "modified": modified,
                    "message": "No operational status data available in the specified range",
                    "data_availability_for_given_date": False,
                    "from_date": DateTimeParser.format_datetime_without_timezone(requested_from_date) if requested_from_date else None,
                    "to_date": DateTimeParser.format_datetime_without_timezone(requested_to_date) if requested_to_date else None,
                    "operational_status": []
                }

            logger.info(f"Retrieved {len(data)} rows of operational status data from database")
            
            # Determine actual data range from retrieved data
            timestamps = [row[0] for row in data if isinstance(row[0], datetime)]
            
            if timestamps:
                actual_from_date = min(timestamps)
                actual_to_date = max(timestamps)
                data_availability = True
                
                time_span_hours = (actual_to_date - actual_from_date).total_seconds() / 3600
                logger.info(f"Actual data range: {actual_from_date} to {actual_to_date}")
                logger.info(f"Time span: {time_span_hours:.2f} hours ({time_span_hours/24:.2f} days)")
                
                if time_span_hours > 72:
                    logger.warning(f"⚠ Data span ({time_span_hours:.2f} hours) exceeds 72 hours")

            # Process records
            records = []
            for row in data:
                record = {}
                for idx, col in enumerate(["DateTime"] + operational_mapping):
                    if idx < len(row):
                        val = row[idx]
                        record[col] = DateTimeParser.format_datetime_without_timezone(val) if isinstance(val, datetime) else val
                records.append(record)

            rack_periods = defaultdict(list)
            sorted_records = sorted(records, key=lambda x: (x.get("Asset", ""), x.get("DateTime", "")))

            current_asset = None
            current_period = None

            for rec in sorted_records:
                asset = rec.get("Asset")
                area_val = rec.get("Area")
                status = rec.get("Status")
                timestamp = rec.get("DateTime")

                if not asset or not status or not timestamp:
                    continue

                if asset != current_asset:
                    if current_period and current_period.get("start_time"):
                        rack_periods[current_asset].append(current_period)

                    current_asset = asset
                    current_period = {
                        "Asset": asset,
                        "Area": area_val,
                        "start_time": None,
                        "stop_time": None
                    }

                if status == "In-Service":
                    if current_period.get("stop_time") and not current_period.get("start_time"):
                        rack_periods[current_asset].append(current_period)
                        current_period = {
                            "Asset": asset,
                            "Area": area_val,
                            "start_time": timestamp,
                            "stop_time": None
                        }
                    elif not current_period.get("start_time"):
                        current_period["start_time"] = timestamp

                elif status == "Not In-Service":
                    if current_period.get("start_time") and not current_period.get("stop_time"):
                        current_period["stop_time"] = timestamp
                        rack_periods[current_asset].append(current_period)

                        current_period = {
                            "Asset": asset,
                            "Area": area_val,
                            "start_time": None,
                            "stop_time": None
                        }
                    elif not current_period.get("stop_time"):
                        current_period["stop_time"] = timestamp

            if current_period and (current_period.get("start_time") or current_period.get("stop_time")):
                rack_periods[current_asset].append(current_period)

            operational_status_data = []
            for asset, periods in rack_periods.items():
                for period in periods:
                    if period.get("start_time") or period.get("stop_time"):
                        operational_status_data.append({
                            "Area": period.get("Area", ""),
                            "Asset": period.get("Asset", ""),
                            "Start Time": period.get("start_time", ""),
                            "Stop Time": period.get("stop_time", "")
                        })

            operational_status_data.sort(key=lambda x: (x["Asset"], x["Start Time"] or ""))

            for idx, record in enumerate(operational_status_data, start=1):
                reordered = {"id": idx}
                reordered.update(record)
                operational_status_data[idx - 1] = reordered

            result = {
                "modified": modified,
                "from_date": DateTimeParser.format_datetime_without_timezone(actual_from_date) if actual_from_date else None,
                "to_date": DateTimeParser.format_datetime_without_timezone(actual_to_date) if actual_to_date else None,
                "operational_status": operational_status_data,
            }

            logger.info(f"Processed {len(operational_status_data)} operational periods")

            return result

        except Exception as e:
            logger.exception(f"Error in get_operational_status_data for {site_id}: {str(e)}")
            return {
                "error": str(e),
                "modified": False,
                "operational_status": []
            }

    def _parse_dt(self, value):
        """Parse datetime from various formats."""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            s = value.strip()
            if s.endswith('Z'):
                s = s[:-1] + '+00:00'
            try:
                return datetime.fromisoformat(s)
            except Exception:
                pass
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(s, fmt)
                    if fmt == '%Y-%m-%d':
                        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    return dt
                except Exception:
                    continue

        raise ValueError(f"Invalid to_date format: {value!r}")

    def build_time_range_where_conditions(self, start_datetime, end_datetime):
        """Build WHERE conditions and query parameters for retrieving data within a custom time range."""
        where_conditions = [
            "`DateTime` >= {start_dt:String}",
            "`DateTime` <= {end_dt:String}"
        ]

        query_params = {
            "start_dt": start_datetime,
            "end_dt": end_datetime
        }
        return where_conditions, query_params

    def get_daily_report_table_data(self, site_id, date):
        """Get daily report table data with proper error handling."""
        try:
            modified = False
            table = "_Process_Overview_Daily"
            table_name = site_id.replace("-", "_") + "_" + site_id.replace("-", "_") + table

            # Safe dictionary access
            site_mapping = Dash002Config.SITE_TABLE_MAPPING.get(site_id.lower())
            if not site_mapping:
                logger.error(f"Site mapping not found for {site_id}")
                return {
                    "error": f"Site mapping not found for {site_id}",
                    "table_data": []
                }

            daily_report_mapping = site_mapping.get("daily_report")
            if not daily_report_mapping:
                logger.error(f"Daily report mapping not found for {site_id}")
                return {
                    "error": f"Daily report mapping not found for {site_id}",
                    "table_data": []
                }

            daily_report_columns = []
            daily_report_labels = []

            for col in daily_report_mapping:
                daily_report_columns.append(col["column_name"])
                daily_report_labels.append(col["column_name"])

            if not daily_report_columns:
                logger.warning(f"No daily report columns found for {site_id}")
                return {
                    "message": "No daily report columns found",
                    "table_data": []
                }

            data = []
            if date:
                # Parse date format (DD-MM-YYYY) to YYYY-MM-DD for ClickHouse
                parsed_date = date
                try:
                    if isinstance(date, str) and '-' in date:
                        parts = date.split('-')
                        if len(parts) == 3 and len(parts[0]) == 2:
                            # DD-MM-YYYY format - convert to YYYY-MM-DD
                            parsed_date_obj = datetime.strptime(date[:10], '%d-%m-%Y')
                            parsed_date = parsed_date_obj.strftime('%Y-%m-%d')
                        elif len(parts) == 3 and len(parts[0]) == 4:
                            # Already YYYY-MM-DD format
                            parsed_date = date[:10]
                        else:
                            parsed_date = date[:10] if len(date) >= 10 else date
                except Exception as e:
                    logger.warning(f"Failed to parse date format {date}: {e}, using as-is")
                    parsed_date = date[:10] if len(date) >= 10 else date
                
                where_condition = ["`DateTime` == {from_date:String}"]
                query_params = {"from_date": parsed_date}
                data = self.clickhouse_repository.get_column_data_for_table(
                    clickhouse_table_name=table_name,
                    column_names=daily_report_columns[1:] if len(daily_report_columns) > 1 else [],
                    datetime_column=daily_report_columns[0],
                    where_conditions=where_condition,
                    query_params=query_params,
                )
                
            if not data or not date:
                data = self.clickhouse_repository.get_column_data_for_table(
                    clickhouse_table_name=table_name,
                    column_names=daily_report_columns[1:] if len(daily_report_columns) > 1 else [],
                    datetime_column=daily_report_columns[0],
                    limit=1
                )
                modified = True

            # Handle ClickHouse response format
            if isinstance(data, dict) and 'result_rows' in data:
                data = data['result_rows']

            table_data = []

            for row in data:
                row_dict = {}
                # Row is tuple: (datetime, value1, value2, ...)
                # Map to daily_report_labels
                for i, label in enumerate(daily_report_labels):
                    value = row[i] if i < len(row) else None
                    # Format datetime values without timezone
                    if isinstance(value, datetime):
                        value = DateTimeParser.format_datetime_without_timezone(value)
                    elif isinstance(value, str) and label == "DateTime":
                        # Try to parse and format datetime strings
                        try:
                            parsed_dt = DateTimeParser.parse_datetime(value)
                            if parsed_dt:
                                value = DateTimeParser.format_datetime_without_timezone(parsed_dt)
                        except:
                            pass
                    else:
                        value = self.round_value(value)
                    row_dict[label] = value
                
                if row_dict:  # Only add if row has data
                    table_data.append(row_dict)

            return {
                "modified": modified,
                "table_data": table_data
            }

        except Exception as e:
            logger.exception(f"Error in get_daily_report_table_data for {site_id}: {str(e)}")
            return {
                "error": str(e),
                "modified": False,
                "table_data": []
            }

    def get_area_filter(self, site_id):
        """Get area filter data with proper error handling."""
        try:
            table = "_Process_status"
            table_name = site_id.replace("-", "_") + table
            
            filter_data = self.clickhouse_repository.get_distinct_column_values(
                table_name=table_name,
                column_name="Area",
                site_name=site_id
            )
            
            if not filter_data:
                logger.warning(f"No filter data available for {site_id}")
                return []
            
            filter_values = filter_data.get("distinct_values", [])
            return filter_values if filter_values else []
            
        except Exception as e:
            logger.exception(f"Error in get_area_filter for {site_id}: {str(e)}")
            return []