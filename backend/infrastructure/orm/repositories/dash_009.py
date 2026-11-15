import os
from typing import List, Dict, Iterable, Tuple, Optional
from datetime import datetime
from config.clickhouse_connector import execute_clickhouse_query
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from datetime import timedelta


class Dash009Repository:
    """
    Encapsulates all ClickHouse access for Dash-009.
    """

    def __init__(self):
        self.repo = ClickHouseRepository()

    def close(self):
        try:
            self.repo.close()
        except Exception:
            pass

    def _get_timezone(self) -> str:
        """
        Get the configured timezone for the application.
        
        Returns:
            str: Timezone string (e.g., 'Asia/Dubai')
        """
        return os.getenv('CLICKHOUSE_TIMEZONE', 'Asia/Dubai')

    # ------- Metadata helpers -------
    def get_datetime_column(self, table_name: str) -> Optional[str]:
        return self.repo.get_datetime_column(table_name)

    def get_table_columns(self, table_name: str) -> List[Dict]:
        return self.repo.get_table_columns(table_name)

    def detect_pump_column(self, cols_meta: List[Dict]) -> Optional[str]:
        names = [c["name"] for c in cols_meta if c.get("name")]
        return next((c for c in names if c.lower() == "pump"), None) or next((c for c in names if "pump" in c.lower()), None)

    def detect_status_column(self, cols_meta: List[Dict]) -> Optional[str]:
        names = [c["name"] for c in cols_meta if c.get("name")]
        return next((c for c in names if c.lower() == "status"), None) or next((c for c in names if "status" in c.lower()), None)

    def get_max_timestamp(self, table_name: str, dt_col: str):
        timezone = self._get_timezone()
        
        # Smart datetime conversion for max calculation
        dt_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%%String%%',
            toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
            toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')
        
        q = f"SELECT max({dt_expr}) FROM {{table:Identifier}}"
        res = execute_clickhouse_query(q, {"table": table_name})
        return res.result_rows[0][0] if (res.result_rows and res.result_rows[0][0]) else None

    # ------- Domain queries -------
    def fetch_latest_per_pump(self,
                              table_name: str,
                              all_col_names: List[str],
                              pump_col: str,
                              dt_col: Optional[str],
                              start_dt=None,
                              end_dt=None) -> Iterable[Tuple]:
        timezone = self._get_timezone()
        
        # Build column list with smart datetime conversion
        select_columns = []
        for c in all_col_names:
            if c == dt_col and dt_col:
                dt_select = f"""if(toTypeName(`{c}`) LIKE '%%String%%',
                    toTimeZone(parseDateTime64BestEffort(`{c}`), '{timezone}'),
                    toTimeZone(`{c}`, '{timezone}')) as `{c}`""".replace('\n', ' ')
                select_columns.append(dt_select)
            else:
                select_columns.append(f"`{c}`")
        
        where_clause = ""
        params = {"table_name": table_name}

        if dt_col and start_dt and end_dt:
            # Smart datetime conversion in WHERE clause
            dt_where_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
                toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')
            
            where_clause = f"WHERE {dt_where_expr} >= toDateTime({{start_date:String}}, '{timezone}') AND {dt_where_expr} <= toDateTime({{end_date:String}}, '{timezone}')"
            params.update({
                "start_date": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                "end_date": end_dt.strftime('%Y-%m-%d %H:%M:%S')
            })

        if dt_col:
            query = (
                f"SELECT {', '.join(select_columns)} "
                f"FROM {{table_name:Identifier}} "
                f"{where_clause} "
                f"ORDER BY `{dt_col}` DESC "
                f"LIMIT 1 BY `{pump_col}`"
            )
        else:
            query = (
                f"SELECT {', '.join(select_columns)} "
                f"FROM {{table_name:Identifier}} "
                f"{where_clause} "
                f"LIMIT 1 BY `{pump_col}`"
            )

        res = execute_clickhouse_query(query, {**params, "pump_col": pump_col})
        return res.result_rows or []

    def fetch_actions_range_all_pumps(self,
                                      table_name: str,
                                      dt_col: str,
                                      pump_col: str,
                                      status_col: str,
                                      start_dt,
                                      end_dt) -> Iterable[Tuple]:
        timezone = self._get_timezone()
        
        # Smart datetime conversion for SELECT
        dt_select = f"""if(toTypeName({dt_col}) LIKE '%%String%%',
            toTimeZone(parseDateTime64BestEffort({dt_col}), '{timezone}'),
            toTimeZone({dt_col}, '{timezone}')) AS ts""".replace('\n', ' ')
        
        # Smart datetime conversion in WHERE clause
        dt_where_expr = f"""if(toTypeName({dt_col}) LIKE '%%String%%',
            toTimeZone(parseDateTime64BestEffort({dt_col}), '{timezone}'),
            toTimeZone({dt_col}, '{timezone}'))""".replace('\n', ' ')
        
        q = (
            f"SELECT {pump_col} AS pump_value, {status_col} AS status_value, {dt_select} "
            f"FROM {{table:Identifier}} "
            f"WHERE {dt_where_expr} >= toDateTime({{start:String}}, '{timezone}') "
            f"AND {dt_where_expr} < toDateTime({{end:String}}, '{timezone}') "
            f"ORDER BY {pump_col} ASC, {dt_col} DESC"
        )
        params = {
            "table": table_name,
            "start": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "end": end_dt.strftime('%Y-%m-%d %H:%M:%S')
        }
        res = execute_clickhouse_query(q, params)
        return res.result_rows or []

    def fetch_actions_range_selected_pumps(self,
                                           table_name: str,
                                           dt_col: str,
                                           pump_col: str,
                                           status_col: str,
                                           start_dt,
                                           end_dt,
                                           selected_pumps: List[str]) -> Iterable[Tuple]:
        timezone = self._get_timezone()
        
        # Smart datetime conversion for SELECT
        dt_select = f"""if(toTypeName({dt_col}) LIKE '%%String%%',
            toTimeZone(parseDateTime64BestEffort({dt_col}), '{timezone}'),
            toTimeZone({dt_col}, '{timezone}')) AS ts""".replace('\n', ' ')
        
        # Smart datetime conversion in WHERE clause
        dt_where_expr = f"""if(toTypeName({dt_col}) LIKE '%%String%%',
            toTimeZone(parseDateTime64BestEffort({dt_col}), '{timezone}'),
            toTimeZone({dt_col}, '{timezone}'))""".replace('\n', ' ')
        
        # normalized compare
        norm_expr = f"lower(replaceAll(replaceAll({pump_col}, ' ', ''), '_', ''))"
        placeholders = []
        params = {
            "table": table_name,
            "start": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "end": end_dt.strftime('%Y-%m-%d %H:%M:%S')
        }
        for i, p in enumerate(selected_pumps):
            key = f"p_{i}"
            placeholders.append(f"{{{key}:String}}")
            params[key] = (p or "").lower().replace(" ", "").replace("_", "")

        q = (
            f"SELECT {pump_col} AS pump_value, {status_col} AS status_value, {dt_select} "
            f"FROM {{table:Identifier}} "
            f"WHERE {dt_where_expr} >= toDateTime({{start:String}}, '{timezone}') "
            f"AND {dt_where_expr} < toDateTime({{end:String}}, '{timezone}') "
            f"AND {norm_expr} IN ({', '.join(placeholders)}) "
            f"ORDER BY {pump_col} ASC, {dt_col} DESC"
        )
        res = execute_clickhouse_query(q, params)
        return res.result_rows or []

    def fetch_distinct_pumps(self, table_name: str, pump_col: str):
        q = (
            "SELECT DISTINCT {pump_col:Identifier} AS pump_value "
            "FROM {table:Identifier} "
            "WHERE {pump_col:Identifier} IS NOT NULL AND trim({pump_col:Identifier}) != '' "
            "ORDER BY pump_value"
        )
        params = {"table": table_name, "pump_col": pump_col}
        res = execute_clickhouse_query(q, params)
        return res.result_rows or []

    def fetch_all_in_range(self,
                           table_name: str,
                           all_col_names: List[str],
                           dt_col: str,
                           start_dt,
                           end_dt) -> Iterable[Tuple]:
        """
        Fetch all rows from the given table within the specified datetime range.
        """
        timezone = self._get_timezone()
        
        # Build column list with smart datetime conversion
        select_columns = []
        for col in all_col_names:
            if col == dt_col:
                dt_select = f"""if(toTypeName(`{col}`) LIKE '%%String%%',
                    toTimeZone(parseDateTime64BestEffort(`{col}`), '{timezone}'),
                    toTimeZone(`{col}`, '{timezone}')) as `{col}`""".replace('\n', ' ')
                select_columns.append(dt_select)
            else:
                select_columns.append(f"`{col}`")

        # Smart datetime conversion in WHERE clause
        dt_where_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%%String%%',
            toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
            toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')

        # Build query
        query = (
            f"SELECT {', '.join(select_columns)} "
            f"FROM {{table:Identifier}} "
            f"WHERE {dt_where_expr} >= toDateTime({{start:String}}, '{timezone}') "
            f"AND {dt_where_expr} <= toDateTime({{end:String}}, '{timezone}') "
            f"ORDER BY `{dt_col}` ASC"
        )

        # Query params
        params = {
            "table": table_name,
            "start": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "end": end_dt.strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Execute query
        res = execute_clickhouse_query(query, params)

        # Return result rows or empty list
        return res.result_rows or []

    def get_min_timestamp(self, table_name: str, dt_col: str):
        """Get the minimum timestamp from the table."""
        q = f"SELECT min({dt_col}) FROM {{table:Identifier}}"
        res = execute_clickhouse_query(q, {"table": table_name})
        return res.result_rows[0][0] if (res.result_rows and res.result_rows[0][0]) else None

    def get_last_7_days_range_from_db(self, table_name: str, dt_col: str) -> Optional[Tuple]:
        """
        Get the date range for the last 7 days of data available in the DB.
        
        Returns:
            Tuple of (start_datetime, end_datetime) or None if no data exists
        """
        max_ts = self.get_max_timestamp(table_name, dt_col)
        if not max_ts:
            return None
        
        # Calculate 7 days before the max timestamp
        start_ts = max_ts - timedelta(days=7)
        
        return (start_ts, max_ts)
