from datetime import datetime, timedelta
from typing import Optional
from infrastructure.orm.repositories.dash_005 import Dash005Repository
from infrastructure.utils.datetime_utils import DateTimeParser
from constants import Dash005Config


class Dash_005Service:
    SITE_TABLE_MAPPING = Dash005Config.SITE_TABLE_MAPPING
    CARDS_COLUMNS = Dash005Config.CARDS_COLUMNS
    TENDENCY_COLUMNS = Dash005Config.TENDENCY_COLUMNS

    def __init__(self):
        self.dash_repo = Dash005Repository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.dash_repo.close()
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
        import re
        if value is None:
            return []
        parts = re.split(r'(\d+)', str(value))
        return [int(part) if part.isdigit() else part.lower() for part in parts]

    def _resolve_table(self, site: str, category: str, key: str) -> str:
        return (self.SITE_TABLE_MAPPING.get(site) or {}).get(key, {}).get(category)

    # ---------- Pump Categories ----------
    def get_pump_categories(self, site: str):
        # ... (this method is unchanged)
        mapping = (self.SITE_TABLE_MAPPING.get(site) or {}).get("reference")
        if not mapping:
            return {
                "site": site, "categories": [],
                "message": f"No pump reference tables mapped for site '{site}'"
            }
        table_name = mapping['tableName']
        columns_to_fetch = [col['columnName'] for col in mapping.get('columns', [])]
        if not columns_to_fetch:
            return {"site": site, "categories": [], "message": "No columns defined for reference table"}
        try:
            rows = self.dash_repo.repo.get_column_data_for_table_opt(
                table_name=table_name, column_names=columns_to_fetch, limit=None
            )
            raw_vals = [row[0].strip() for row in rows if row and row[0] and isinstance(row[0], str) and row[0].strip()]
            seen, unique_ids = set(), []
            for v in raw_vals:
                if v not in seen:
                    seen.add(v)
                    unique_ids.append(v)
            categories = [{"id": v, "name": self.humanize(v)} for v in unique_ids]
            return {"site": site, "categories": categories}
        except Exception as e:
            return {"site": site, "categories": [], "message": f"Error fetching pump categories: {str(e)}"}

    # ---------- Cards with Tendency (UPDATED) ----------
    def get_cards_averages(self, site: str, pump_category: str, date_str: str = None):
        """
        Fetch card data for a specific point in time and calculate 24h vs 24h tendency.
        - Card data is for the exact/latest timestamp.
        - Tendency compares the weighted average of the 24h period ending at the timestamp
          with the weighted average of the preceding 24h period.
        """
        table_name = (self.SITE_TABLE_MAPPING.get(site) or {}).get("cards", {}).get(pump_category)
        if not table_name:
            return {"data": "", "message": "Invalid site_id or pump_id"}

        dt_col = self.dash_repo.get_datetime_column(table_name)
        if not dt_col:
            return {"data": "", "message": "No DateTime column found for filtering"}

        column_names = [c["columnName"] for c in self.CARDS_COLUMNS]

        requested_datetime = None
        fallback_to_latest = False

        # Determine the timestamp to use as the anchor for our analysis
        if date_str:
            try:
                requested_datetime = datetime.fromisoformat(date_str)
            except Exception as e:
                return {"data": "",
                        "message": f"Invalid date format. Use ISO like 2025-09-02T12:00:00. Error: {str(e)}"}
        else:
            max_ts = self.dash_repo.get_max_timestamp(table_name, dt_col)
            if not max_ts:
                return {"data": "", "message": "No data available to determine latest date"}
            requested_datetime = max_ts

        # Fetch the card data for the specific point in time
        rows = self.dash_repo.fetch_exact_timestamp_row(
            table_name=table_name, column_names=column_names, dt_col=dt_col,
            target_datetime=requested_datetime
        )

        # If no exact match, fall back to latest available data
        if not rows:
            fallback_to_latest = True
            max_ts = self.dash_repo.get_max_timestamp(table_name, dt_col)
            if not max_ts:
                return {"data": "", "message": "No data available in table"}
            requested_datetime = max_ts
            rows = self.dash_repo.fetch_exact_timestamp_row(
                table_name=table_name, column_names=column_names, dt_col=dt_col,
                target_datetime=requested_datetime
            )

        # ========== CONSTRUCT CARD RESPONSE ==========
        data = []
        if rows:
            latest_row = rows[0]
            offset = max(0, len(latest_row) - len(column_names))
            for idx, col_spec in enumerate(self.CARDS_COLUMNS):
                value = latest_row[offset + idx] if (offset + idx) < len(latest_row) else None
                data.append({
                    "columnName": col_spec["columnName"],
                    "value": value,
                    "timestamp": DateTimeParser.format_datetime_without_timezone(requested_datetime) if requested_datetime else None,
                    "modified": fallback_to_latest,
                })
        else:
            # Populate with nulls if no data found
            for col_spec in self.CARDS_COLUMNS:
                data.append({
                    "columnName": col_spec["columnName"], "value": None,
                    "timestamp": DateTimeParser.format_datetime_without_timezone(requested_datetime) if requested_datetime else None,
                    "modified": fallback_to_latest,
                })

        # ========== CALCULATE 24h vs 24h TENDENCY ==========
        tendency_data = self._calculate_24hour_tendency(
            table_name=table_name,
            dt_col=dt_col,
            end_timestamp=requested_datetime
        )

        if date_str is None:
            msg = "Latest card data and tendency retrieved successfully"
        elif fallback_to_latest:
            msg = f"No data found for requested datetime {date_str}, returned latest available data. Tendency is based on this latest timestamp."
        else:
            msg = "Card data and tendency retrieved successfully for the provided datetime"

        return {
            "data": data,
            "tendency": tendency_data,
            "message": msg
        }

    def _calculate_24hour_tendency(self, table_name: str, dt_col: str, end_timestamp: datetime):
        """
        Calculate tendency by comparing the simple average of a 24-hour period
        against the simple average of the preceding 24-hour period.
        """
        if not end_timestamp:
            return {"error": "Cannot calculate tendency without a valid timestamp.", "columns": {}}

        try:
            current_window_end = end_timestamp
            current_window_start = end_timestamp - timedelta(hours=24)
            previous_window_end = current_window_start
            previous_window_start = previous_window_end - timedelta(hours=24)

            tendency_results = {}
            for col_name in self.TENDENCY_COLUMNS:
                # Get simple average for the current 24-hour period
                current_avg = self.dash_repo.calculate_simple_average(
                    table_name=table_name, column_name=col_name, dt_col=dt_col,
                    start_dt=current_window_start, end_dt=current_window_end
                )

                # Get simple average for the previous 24-hour period
                previous_avg = self.dash_repo.calculate_simple_average(
                    table_name=table_name, column_name=col_name, dt_col=dt_col,
                    start_dt=previous_window_start, end_dt=previous_window_end
                )

                if current_avg is not None and previous_avg is not None and previous_avg != 0:
                    change = current_avg - previous_avg
                    change_percent = (change / previous_avg) * 100

                    if change > 0.0001: tendency = "UP"
                    elif change < -0.0001: tendency = "DOWN"
                    else: tendency = "STABLE"

                    tendency_results[col_name] = {
                        "current_24h_avg": round(current_avg, 4),
                        "previous_24h_avg": round(previous_avg, 4),
                        "change": round(change, 4),
                        "change_percent": round(change_percent, 2),
                        "tendency": tendency,
                        "period": "24h_vs_prev_24h",
                        "method": "simple_average" # UPDATED
                    }
                else:
                    tendency_results[col_name] = {
                        "current_24h_avg": round(current_avg, 4) if current_avg is not None else None,
                        "previous_24h_avg": round(previous_avg, 4) if previous_avg is not None else None,
                        "tendency": "INSUFFICIENT_HISTORY",
                        "period": "24h_vs_prev_24h",
                        "method": "simple_average", # UPDATED
                        "note": "Insufficient data in the 48-hour window for comparison."
                    }

            return {
                "comparison_timestamp": DateTimeParser.format_datetime_without_timezone(end_timestamp),
                "current_window": {"start": DateTimeParser.format_datetime_without_timezone(current_window_start), "end": DateTimeParser.format_datetime_without_timezone(current_window_end)},
                "previous_window": {"start": DateTimeParser.format_datetime_without_timezone(previous_window_start), "end": DateTimeParser.format_datetime_without_timezone(previous_window_end)},
                "columns": tendency_results
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to calculate tendency: {str(e)}")
            return {"error": f"Failed to calculate tendency: {str(e)}", "columns": {}}

    # ---------- The rest of the methods are unchanged ----------
    def get_pump_kpis(self, site: str, pump_category: str, date_str: str = None):
        # ... (this method is unchanged)
        table_name = (self.SITE_TABLE_MAPPING.get(site) or {}).get("kpis", {}).get(pump_category)
        if not table_name:
            return {"site": site, "pump_category": pump_category, "table": "", "records": [],
                    "message": "Invalid site_id or pump_id"}
        start_dt = end_dt = None
        requested_date_str = None
        if date_str:
            start_dt = self._parse_iso(date_str)
            if not start_dt:
                return {"site": site, "pump_category": pump_category, "table": table_name, "records": [],
                        "message": "Invalid date format. Use ISO like 2025-09-25T15:03:52"}
            requested_date_str = DateTimeParser.format_datetime_without_timezone(start_dt)
            end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        cols_meta = self.dash_repo.get_table_columns(table_name)
        if not cols_meta:
            return {"site": site, "pump_category": pump_category, "table": table_name, "records": [],
                    "message": "No columns found for the specified table"}
        dt_col = self.dash_repo.get_datetime_column(table_name)
        pump_col = self.dash_repo.detect_pump_column(cols_meta)
        pump_id_col = self.dash_repo.detect_pump_id_column(cols_meta)
        if not pump_col:
            return {"site": site, "pump_category": pump_category, "table": table_name, "records": [],
                    "message": "No 'Pump' column found in table to group by"}
        all_col_names = [c["name"] for c in cols_meta if c.get("name")]
        rows = self.dash_repo.fetch_latest_per_pump(table_name, all_col_names, pump_col, dt_col, start_dt, end_dt)
        fallback_to_latest = False
        if not rows and date_str:
            fallback_to_latest = True
            rows = self.dash_repo.fetch_latest_per_pump(table_name, all_col_names, pump_col, dt_col, None, None)
        if not rows:
            window_msg = f" for {requested_date_str} to {DateTimeParser.format_datetime_without_timezone(end_dt)}" if (start_dt and end_dt) else ""
            return {"site": site, "pump_category": pump_category, "table": table_name, "records": [],
                    "message": f"No data found{window_msg}"}
        types_lookup = {c["name"]: c.get("type", "unknown") for c in cols_meta}

        def display_name(col: str) -> str:
            return col.replace("_", " ")

        def display_pump(val) -> str:
            return str(val).replace("_", " ") if val is not None else None

        col_names_excluding_pump = [c for c in all_col_names if c != pump_col and c != pump_id_col]
        records = []
        for row in rows:
            row_map = {col: (row[idx] if idx < len(row) else None) for idx, col in enumerate(all_col_names)}
            pump_raw = row_map.get(pump_col)
            pump_clean = display_pump(pump_raw)
            typed_columns = []
            for name in col_names_excluding_pump:
                original_value = row_map.get(name)
                modified = False
                final_value = original_value
                if fallback_to_latest:
                    modified = True
                elif original_value is None and pump_raw is not None:
                    latest_value = self._fetch_latest_non_null_value(table_name, name, pump_col, pump_raw, dt_col)
                    if latest_value is not None:
                        final_value = latest_value
                        modified = True
                
                # Format datetime values without timezone
                if isinstance(final_value, datetime):
                    final_value = DateTimeParser.format_datetime_without_timezone(final_value)
                elif isinstance(final_value, str) and (name == dt_col or "DateTime" in types_lookup.get(name, "") or "Date" in types_lookup.get(name, "")):
                    # Try to parse and format datetime strings
                    try:
                        parsed_dt = DateTimeParser.parse_datetime(final_value)
                        if parsed_dt:
                            final_value = DateTimeParser.format_datetime_without_timezone(parsed_dt)
                    except:
                        pass  # Keep original value if parsing fails
                
                typed_columns.append(
                    {"columnName": display_name(name), "type": types_lookup.get(name, "unknown"), "value": final_value,
                     "modified": modified})
            
            # Add Pump_ID column if it exists
            if pump_id_col:
                pump_id_value = row_map.get(pump_id_col)
                if pump_id_value is None and pump_raw is not None:
                    # Try to fetch from latest row if not found in current row
                    pump_id_value = self._fetch_latest_non_null_value(table_name, pump_id_col, pump_col, pump_raw, dt_col)
                pump_id_type = types_lookup.get(pump_id_col, "Int32")
                typed_columns.append({
                    "columnName": "Pump ID",
                    "type": pump_id_type,
                    "value": pump_id_value,
                    "modified": False
                })
            
            records.append({"pump": pump_clean, "pump_raw": pump_raw, "columns": typed_columns})
        records.sort(key=lambda r: self._natural_sort_key(r.get("pump_raw")))
        message = "Latest per-pump records for provided date" if start_dt and not fallback_to_latest else "Latest per-pump records"
        if fallback_to_latest:
            message = f"No data found for requested date {requested_date_str}, returning latest available data (all columns marked as modified)"
        return {"site": site, "pump_category": pump_category, "table": table_name, "timestamp_column": dt_col,
                "pump_column": pump_col, "requested_date": requested_date_str, "record_count": len(records),
                "records": records, "message": message}

    def _fetch_latest_non_null_value(self, table_name: str, column_name: str,
                                     pump_col: str, pump_value, dt_col: Optional[str]):
        # ... (this method is unchanged)
        try:
            where_conditions = [f"`{column_name}` IS NOT NULL", f"`{pump_col}` = {{pump_value:String}}"]
            query_params = {"pump_value": str(pump_value)}
            result_dict = self.dash_repo.repo.get_column_data_for_table(
                clickhouse_table_name=table_name, column_names=[column_name], datetime_column=dt_col,
                where_conditions=where_conditions, query_params=query_params, limit=1
            )
            # Extract result_rows from Dict response
            rows = result_dict.get("result_rows", [])
            if rows and len(rows) > 0 and rows[0][0] is not None:
                return rows[0][0]
            return None
        except Exception:
            return None

    def get_actions_overview(self, site: str, pump_category: str, from_date: str = None, to_date: str = None,
                             selected_pumps=None):
        """
        Get pump start/stop transitions for the date range.

        When NO pumps selected: Returns start/stop events for ALL pumps in the date range.
        When pumps ARE selected: Returns all status records for those specific pumps.
        """
        selected_pumps = selected_pumps or []
        table_name = (self.SITE_TABLE_MAPPING.get(site) or {}).get("kpis", {}).get(pump_category)
        if not table_name:
            return {"data": {"records": []}, "message": "Invalid site_id or pump_id"}

        dt_col = self.dash_repo.get_datetime_column(table_name)
        cols = self.dash_repo.get_table_columns(table_name)
        if not cols:
            return {"data": {"records": []}, "message": "No columns found for the specified table"}

        pump_col = self.dash_repo.detect_pump_column(cols)
        status_col = self.dash_repo.detect_status_column(cols)
        pump_id_col = self.dash_repo.detect_pump_id_column(cols)
        if not (pump_col and status_col and dt_col):
            return {"data": {"records": []}, "message": "Required columns (pump, status, datetime) not found."}

        def _parse(s):
            return self._parse_iso(s) if s else None

        requested_start = _parse(from_date)
        requested_end = _parse(to_date)

        # Handle date range logic
        if requested_start and not requested_end:
            requested_end = requested_start + timedelta(hours=24)
        if requested_end and not requested_start:
            requested_start = requested_end - timedelta(hours=24)

        if not (requested_start and requested_end):
            max_ts = self.dash_repo.get_max_timestamp(table_name, dt_col)
            if not max_ts:
                return {"data": {"records": []}, "message": "No data available to determine latest timestamp"}
            start_dt = max_ts - timedelta(hours=24)
            end_dt = max_ts + timedelta(seconds=1)
            mode = "all_pumps_transitions_last_24h" if not selected_pumps else "selected_pumps_last_24h"
            requested_window = None
        else:
            start_dt, end_dt = requested_start, requested_end
            mode = "all_pumps_transitions_date_range" if not selected_pumps else "selected_pumps_full_day"
            requested_window = (requested_start, requested_end)

        # Fetch data based on mode
        def _fetch_rows(sdt: datetime, edt: datetime):
            if not selected_pumps:
                # NEW: Fetch only transitions (start/stop events) for all pumps
                return self.dash_repo.fetch_pump_transitions(
                    table_name, dt_col, pump_col, status_col, sdt, edt
                )
            else:
                # Keep existing behavior: all records for selected pumps
                return self.dash_repo.fetch_actions_range_selected_pumps(
                    table_name, dt_col, pump_col, status_col, sdt, edt, selected_pumps
                )

        rows = _fetch_rows(start_dt, end_dt)
        fallback_to_latest = False
        actual_window_start, actual_window_end = start_dt, end_dt

        # Fallback logic if no data found
        if requested_window and not rows:
            max_ts = self.dash_repo.get_max_timestamp(table_name, dt_col)
            if max_ts:
                fallback_to_latest = True
                actual_window_start = max_ts - timedelta(hours=24)
                actual_window_end = max_ts + timedelta(seconds=1)
                rows = _fetch_rows(actual_window_start, actual_window_end)
                mode = "all_pumps_transitions_last_24h" if not selected_pumps else "selected_pumps_last_24h"

        def clean_label(v):
            return str(v).replace("_", " ") if v is not None else None

        # Group by pump
        grouped = {}
        for pval, sval, tval in rows or []:
            # Format datetime timestamp without timezone
            if tval:
                if isinstance(tval, datetime):
                    formatted_timestamp = DateTimeParser.format_datetime_without_timezone(tval)
                elif isinstance(tval, str):
                    try:
                        parsed_dt = DateTimeParser.parse_datetime(tval)
                        formatted_timestamp = DateTimeParser.format_datetime_without_timezone(parsed_dt) if parsed_dt else tval
                    except:
                        formatted_timestamp = tval
                else:
                    formatted_timestamp = str(tval)
            else:
                formatted_timestamp = None
            
            grouped.setdefault(pval, []).append({
                "status": sval,
                "timestamp": formatted_timestamp,
                "modified": fallback_to_latest
            })

        # Fetch Pump_ID for all unique pumps at once using repository method
        pump_id_map = {}
        if pump_id_col and grouped:
            unique_pumps = list(grouped.keys())
            pump_id_map = self.dash_repo.fetch_pump_ids_for_pumps(
                table_name, pump_col, pump_id_col, unique_pumps, dt_col
            )

        records = []
        for k, v in grouped.items():
            record = {"pump": clean_label(k), "pump_raw": k, "statuses": v}
            if pump_id_col and k in pump_id_map:
                record["Pump_ID"] = pump_id_map[k]
            records.append(record)
        records.sort(key=lambda r: self._natural_sort_key(r.get("pump_raw")))

        # Build appropriate message
        if not selected_pumps:
            if requested_window is None and not fallback_to_latest:
                message = "Pump start/stop transitions for all pumps (last 24h based on latest record)"
            elif fallback_to_latest:
                rs, re = requested_window
                message = f"No data for window {DateTimeParser.format_datetime_without_timezone(rs)} to {DateTimeParser.format_datetime_without_timezone(re)}, returned latest 24h transitions (items marked as modified)."
            else:
                message = "Pump start/stop transitions for all pumps in the provided date range"
        else:
            if requested_window is None and not fallback_to_latest:
                message = "All statuses for selected pumps (last 24h)"
            elif fallback_to_latest:
                rs, re = requested_window
                message = f"No data for window {DateTimeParser.format_datetime_without_timezone(rs)} to {DateTimeParser.format_datetime_without_timezone(re)}, returned latest 24h window (items marked as modified)."
            else:
                message = "All statuses for selected pumps (provided date)"

        return {
            "data": {
                "site": site,
                "pump_category": pump_category,
                "table": table_name,
                "mode": mode,
                "requested_window_start": DateTimeParser.format_datetime_without_timezone(requested_window[0]) if requested_window else None,
                "requested_window_end": DateTimeParser.format_datetime_without_timezone(requested_window[1]) if requested_window else None,
                "window_start": DateTimeParser.format_datetime_without_timezone(actual_window_start),
                "window_end": DateTimeParser.format_datetime_without_timezone(actual_window_end),
                "timestamp_column": dt_col,
                "pump_column": pump_col,
                "status_column": status_col,
                "record_groups": len(records),
                "records": records
            },
            "message": message
        }

    def get_unique_pumps(self, site: str, pump_category: str):
        # ... (this method is unchanged)
        table_name = (self.SITE_TABLE_MAPPING.get(site) or {}).get("kpis", {}).get(pump_category)
        if not table_name:
            return {"site": site, "pump_category": pump_category, "table": "", "pumps": [],
                    "message": "Invalid site_id or pump_id"}
        cols_meta = self.dash_repo.get_table_columns(table_name)
        if not cols_meta:
            return {"site": site, "pump_category": pump_category, "table": table_name, "pumps": [],
                    "message": "No columns found for the specified table"}
        pump_col = self.dash_repo.detect_pump_column(cols_meta)
        if not pump_col:
            return {"site": site, "pump_category": pump_category, "table": table_name, "pumps": [],
                    "message": "No 'Pump' column found in the table"}
        rows = self.dash_repo.fetch_distinct_pumps(table_name, pump_col)

        def clean_label(val):
            return str(val).replace("_", " ") if val is not None else None

        pumps = [{"label": clean_label(r[0]), "value": r[0]} for r in (rows or [])]
        pumps.sort(key=lambda p: self._natural_sort_key(p.get("value")))
        return {"site": site, "pump_category": pump_category, "table": table_name, "pump_column": pump_col,
                "count": len(pumps), "pumps": pumps}