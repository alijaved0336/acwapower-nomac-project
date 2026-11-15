from datetime import datetime, timedelta

from infrastructure.orm.repositories.dash_009 import Dash009Repository
from infrastructure.services.clickhouse import ClickHouseService
from typing import List, Optional, Any, Dict
from constants import Dash009Config
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository

class Dash_009Service:
    # Centralized mapping so controllers stay thin
    SITE_TABLE_MAPPING = Dash009Config.SITE_TABLE_MAPPING

    def __init__(self):
        self.repo = Dash009Repository()
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
    def _natural_sort_key(value):
        """
        Generate a sort key for natural/alphanumeric sorting.
        Handles strings like "Pump_1", "Pump_10", "Pump_2" correctly.
        """
        import re
        if value is None:
            return []

        # Convert to string and split into text and number parts
        parts = re.split(r'(\d+)', str(value))
        # Convert numeric parts to integers for proper sorting
        return [int(part) if part.isdigit() else part.lower() for part in parts]

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
    
    def _resolve_table(self, site: str, category: str, key: str) -> str:
        return (self.SITE_TABLE_MAPPING.get(site) or {}).get(key, {}).get(category)

    # ---------- Pump Categories ----------
    def get_pump_categories(self, site: str):
        """
        Fetch pump categories using ClickHouse repository directly.
        Uses ClickHouseRepository (via repo.repo) for generic data access.
        """
        mapping = (self.SITE_TABLE_MAPPING.get(site) or {}).get("reference")
        if not mapping:
            return {
                "site": site,
                "categories": [],
                "message": f"No pump reference tables mapped for site '{site}'",
                **self._create_fallback_metadata(True)  # No date filtering, so always True
            }

        table_name = mapping['tableName']
        columns_to_fetch = [col['columnName'] for col in mapping.get('columns', [])]

        if not columns_to_fetch:
            return {
                "site": site,
                "categories": [],
                "message": "No columns defined for reference table",
                **self._create_fallback_metadata(True)  # No date filtering, so always True
            }

        try:
            # Use ClickHouseRepository's optimized method via repo.repo
            rows = self.repo.repo.get_column_data_for_table_opt(
                table_name=table_name,
                column_names=columns_to_fetch,
                limit=None
            )

            # Extract unique values from the first column (Pump_Category)
            raw_vals = []
            for row in rows:
                if row and row[0] and isinstance(row[0], str):
                    val = row[0].strip()
                    if val:
                        raw_vals.append(val)

            # Remove duplicates while preserving order
            seen, unique_ids = set(), []
            for v in raw_vals:
                if v not in seen:
                    seen.add(v)
                    unique_ids.append(v)

            categories = [{"id": v, "name": self.humanize(v)} for v in unique_ids]
            return {
                "site": site, 
                "categories": categories,
                **self._create_fallback_metadata(True)  # No date filtering, so always True
            }

        except Exception as e:
            return {
                "site": site,
                "categories": [],
                "message": f"Error fetching pump categories: {str(e)}",
                **self._create_fallback_metadata(True)  # No date filtering, so always True
            }



    # ---------- Pump KPIs (heatmap version - keeping as is) ----------

    def _time_weighted_average(self, value_timestamp_pairs: List[tuple]) -> float:
        """
        Calculate time-weighted average.
        Each value is weighted by the duration it was active.
        """
        if len(value_timestamp_pairs) <= 1:
            return float(value_timestamp_pairs[0][0])
        
        # Sort by timestamp
        sorted_pairs = sorted(value_timestamp_pairs, key=lambda x: x[1])
        
        total_weighted_value = 0
        total_duration = 0
        
        for i in range(len(sorted_pairs) - 1):
            value, timestamp = sorted_pairs[i]
            next_timestamp = sorted_pairs[i + 1][1]
            
            # Calculate duration (time difference)
            duration = (next_timestamp - timestamp).total_seconds()
            
            if duration > 0:
                total_weighted_value += float(value) * duration
                total_duration += duration
        
        # Handle the last value (assume it continues until present or use small weight)
        if total_duration > 0:
            return total_weighted_value / total_duration
        else:
            # If no duration available, return the last value
            return float(sorted_pairs[-1][0])

    def _aggregate_time_weighted(
        self, 
        values: List[Any], 
        timestamps: List
    ) -> Optional[Any]:
        """
        Aggregate values using time-weighted average method.
        """
        # Filter out None values and create pairs
        valid_pairs = [(v, t) for v, t in zip(values, timestamps) if v is not None and t is not None]
        
        if not valid_pairs:
            return None
        
        # Handle non-numeric values - return last value
        try:
            # Try to convert to float to check if numeric
            numeric_pairs = [(float(v), t) for v, t in valid_pairs]
        except (ValueError, TypeError):
            # Non-numeric data - return last value
            return valid_pairs[-1][0]
        
        # Calculate time-weighted average
        return self._time_weighted_average(numeric_pairs)

    def get_pump_kpis_range(
        self, 
        site: str, 
        pump_category: str, 
        from_date: str = None, 
        to_date: str = None
    ):
        """
        Get aggregated pump KPIs for a date range using time-weighted average.
        Falls back to last 7 days from DB if no data found in requested range.
        """
        table_name = (self.SITE_TABLE_MAPPING.get(site) or {}).get("kpis", {}).get(pump_category)
        if not table_name:
            return {
                "data": [],
                "message": "Invalid site_id or pump_id",
                **self._create_fallback_metadata(False)
            }

        # Parse date range
        start_dt = self._parse_iso(from_date) if from_date else None
        end_dt = self._parse_iso(to_date) if to_date else None
        
        # Track if we found data for the requested date range
        data_available_for_requested_date = True
        requested_start_dt = start_dt
        requested_end_dt = end_dt

        # Validate date range if provided
        if from_date and not start_dt:
            return {
                "data": [],
                "message": "Invalid from_date format. Use ISO like 2025-09-25T15:03:52",
                **self._create_fallback_metadata(False)
            }
        
        if to_date and not end_dt:
            return {
                "data": [],
                "message": "Invalid to_date format. Use ISO like 2025-09-25T15:03:52",
                **self._create_fallback_metadata(False)
            }

        # Get table metadata
        cols_meta = self.repo.get_table_columns(table_name)
        if not cols_meta:
            return {
                "data": [],
                "message": "No columns found for the specified table",
                **self._create_fallback_metadata(False)
            }

        dt_col = self.repo.get_datetime_column(table_name)
        pump_col = self.repo.detect_pump_column(cols_meta)
        
        if not pump_col:
            return {
                "data": [],
                "message": "No 'Pump' column found in table to group by",
                **self._create_fallback_metadata(False)
            }

        # If no date range provided, get the latest available data
        if not start_dt and not end_dt:
            if dt_col:
                max_ts = self.repo.get_max_timestamp(table_name, dt_col)
                if max_ts:
                    # Get data from the last 24 hours by default
                    end_dt = max_ts
                    start_dt = max_ts - timedelta(hours=24)
        
        # If only one date is provided, calculate the other
        if start_dt and not end_dt:
            end_dt = start_dt + timedelta(hours=24)
        elif end_dt and not start_dt:
            start_dt = end_dt - timedelta(hours=24)

        # Fetch ALL data in range (not just latest per pump)
        all_col_names = [c["name"] for c in cols_meta if c.get("name")]
        
        # Fetch all records in range for aggregation
        rows = self.repo.fetch_all_in_range(
            table_name,
            all_col_names,
            dt_col,
            start_dt,
            end_dt
        )
        
        # FALLBACK LOGIC: If no data found in requested range, try last 7 days from DB
        if not rows and dt_col and (requested_start_dt or requested_end_dt):
            db_range = self.repo.get_last_7_days_range_from_db(table_name, dt_col)
            if db_range:
                # Data not available for requested date - using fallback
                data_available_for_requested_date = False
                start_dt, end_dt = db_range
                
                # Retry fetching with DB-based range
                rows = self.repo.fetch_all_in_range(
                    table_name,
                    all_col_names,
                    dt_col,
                    start_dt,
                    end_dt
                )
        
        if not rows:
            window_msg = ""
            if requested_start_dt and requested_end_dt:
                window_msg = f" for date range {requested_start_dt.strftime('%Y-%m-%d')} to {requested_end_dt.strftime('%Y-%m-%d')}"
            return {
                "data": [],
                "message": f"No data found{window_msg}",
                **self._create_fallback_metadata(False)
            }

        # Build columnar response structure
        types_lookup = {c["name"]: c.get("type", "unknown") for c in cols_meta}
        col_names_excluding_pump = [c for c in all_col_names if c != pump_col and c != dt_col]
        
        # Group data by pump
        pump_data = {}
        for row in rows:
            row_map = {col: (row[idx] if idx < len(row) else None) for idx, col in enumerate(all_col_names)}
            pump_value = row_map.get(pump_col)
            
            if pump_value not in pump_data:
                pump_data[pump_value] = []
            
            pump_data[pump_value].append(row_map)
        
        # Initialize column objects
        column_data = {}
        for col_name in col_names_excluding_pump:
            clickhouse_type = types_lookup.get(col_name, "unknown")
            parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(clickhouse_type)
            column_data[col_name] = {
                "siteName": site,
                "tableName": self.humanize(pump_category),
                "columnName": self.humanize(col_name),
                "columnType": parquet_type,
                "dataSource": []
            }
        
        # Add pump column data
        pump_clickhouse_type = types_lookup.get(pump_col, "String")
        pump_parquet_type = self.clickhouse_repo._convert_clickhouse_to_parquet_type(pump_clickhouse_type)
        column_data[pump_col] = {
            "siteName": site,
            "tableName": self.humanize(pump_category),
            "columnName": self.humanize(pump_col),
            "columnType": pump_parquet_type,
            "dataSource": []
        }

        # Sort pumps in natural ascending order (Pump 1, 2, 3... not 1, 10, 2)
        sorted_pump_values = sorted(pump_data.keys(), key=self._natural_sort_key)

        # Process each pump and aggregate values using time-weighted average
        for pump_value in sorted_pump_values:
            pump_records = pump_data[pump_value]
            
            # Add pump identifier
            pump_display = str(pump_value).replace("_", " ") if pump_value is not None else None
            column_data[pump_col]["dataSource"].append(pump_display)
            
            # Aggregate each column for this pump
            for col_name in col_names_excluding_pump:
                # Extract values and timestamps
                values = [record.get(col_name) for record in pump_records]
                timestamps = [record.get(dt_col) for record in pump_records]
                
                # Aggregate using time-weighted average
                aggregated_value = self._aggregate_time_weighted(values, timestamps)
                column_data[col_name]["dataSource"].append(aggregated_value)

        # Convert to list format (pump column first, then others)
        result = [column_data[pump_col]]
        result.extend([column_data[col] for col in col_names_excluding_pump])

        # Build message based on whether fallback was used
        if not data_available_for_requested_date:
            message = f"No data found for requested date range. Showing aggregated data from last 7 days available in database (time-weighted average)"
        elif from_date or to_date:
            message = f"Per-pump aggregated data using time-weighted average for requested date range"
        else:
            message = f"Per-pump aggregated data using time-weighted average (last 24 hours)"

        return {
            "data": result,
            "message": message,
            "aggregation_method": "time_weighted_avg",
            **self._create_fallback_metadata(data_available_for_requested_date, start_dt, end_dt)
        }