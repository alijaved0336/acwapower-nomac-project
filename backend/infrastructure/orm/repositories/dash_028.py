from datetime import datetime
from config.clickhouse_connector import execute_clickhouse_query
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
import os
from typing import Iterable, List, Tuple


class Dash028Repository:
    """
    ClickHouse repository layer for Dash-028.
    Wraps ClickHouseRepository and safely handles datetime comparisons.
    """

    def __init__(self):
        self.repo = ClickHouseRepository()

    def close(self):
        try:
            self.repo.close()
        except Exception:
            pass

    def _get_timezone(self) -> str:
        return os.getenv('CLICKHOUSE_TIMEZONE', 'Asia/Dubai')

    def get_table_columns(self, table_name: str):
        return self.repo.get_table_columns(table_name)

    def get_datetime_column(self, table_name: str):
        return self.repo.get_datetime_column(table_name)

    def fetch_columns_in_range(self, table_name: str, all_cols: list[str], dt_col: str, start_dt, end_dt):
        """
        Fetch all records for given columns between start and end datetime.
        Uses parseDateTimeBestEffortOrNull for robust datetime parsing.
        """
        # --- SELECT clause ---
        select_cols = []
        for c in all_cols:
            select_cols.append(f"`{c}`")

        # --- Query with simple, robust datetime parsing ---
        query = f"""
            SELECT {', '.join(select_cols)}
            FROM {{table:Identifier}}
            WHERE parseDateTimeBestEffortOrNull(`{dt_col}`)
              BETWEEN toDateTime({{start:String}})
              AND toDateTime({{end:String}})
            ORDER BY `{dt_col}` ASC
        """

        # --- Params ---
        params = {
            "table": table_name,
            "start": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "end": end_dt.strftime('%Y-%m-%d %H:%M:%S'),
        }

        # --- Execute ---
        res = execute_clickhouse_query(query, params)
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
                dt_select = f"""if(toTypeName(`{col}`) LIKE '%String%',
                    toTimeZone(parseDateTime64BestEffort(`{col}`), '{timezone}'),
                    toTimeZone(`{col}`, '{timezone}')) as `{col}`""".replace('\n', ' ')
                select_columns.append(dt_select)
            else:
                select_columns.append(f"`{col}`")

        # Smart datetime conversion in WHERE clause
        dt_where_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%String%',
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
    
    def get_max_timestamp(self, table_name: str, dt_col: str):
        timezone = self._get_timezone()
        
        # Smart datetime conversion for max calculation
        dt_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%String%',
            toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
            toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')
        
        q = f"SELECT max({dt_expr}) FROM {{table:Identifier}}"
        res = execute_clickhouse_query(q, {"table": table_name})
        return res.result_rows[0][0] if (res.result_rows and res.result_rows[0][0]) else None
    


    def fetch_all_in_range_timezone_removed(self,
                        table_name: str,
                        all_col_names: List[str],
                        dt_col: str,
                        start_dt,
                        end_dt) -> Iterable[Tuple]:
        """
        Fetch all rows from the given table within the specified datetime range.
        Returns datetime columns without timezone information.
        """
        timezone = self._get_timezone()
        
        # Detect the actual column type from table schema
        table_parts = table_name.split('.')
        simple_table_name = table_parts[-1] if table_parts else table_name
        
        type_query = "SELECT name, type FROM system.columns WHERE table = {table:String} AND name = {col:String}"
        type_result = execute_clickhouse_query(type_query, {"table": simple_table_name, "col": dt_col})
        
        is_string_type = True  # Default to string type for safety
        if type_result.result_rows and len(type_result.result_rows) > 0:
            col_type = type_result.result_rows[0][1]  # type is the second column
            # Check if it's a DateTime type (not String)
            is_string_type = not (col_type.startswith('DateTime') or col_type.startswith('Date'))
        
        # Build column list - use different alias for formatted datetime
        select_columns = []
        dt_col_alias = f"{dt_col}_formatted"
        
        for col in all_col_names:
            if col == dt_col:
                if is_string_type:
                    # String type: parse first, then format without timezone
                    dt_select = f"formatDateTime(parseDateTime64BestEffort(`{col}`), '%Y-%m-%d %H:%i:%S') as `{dt_col_alias}`"
                else:
                    # DateTime/DateTime64 type: format without timezone
                    dt_select = f"formatDateTime(`{col}`, '%Y-%m-%d %H:%M:%S') as `{dt_col_alias}`"
                select_columns.append(dt_select)
            else:
                select_columns.append(f"`{col}`")

        # WHERE and ORDER BY use original column, not the formatted alias
        if is_string_type:
            dt_where_expr = f"parseDateTime64BestEffort(`{dt_col}`)"
        else:
            dt_where_expr = f"`{dt_col}`"

        # Build query - ORDER BY uses original column
        query = (
            f"SELECT {', '.join(select_columns)} "
            f"FROM {{table:Identifier}} "
            f"WHERE {dt_where_expr} >= parseDateTime64BestEffort({{start:String}}) "
            f"AND {dt_where_expr} <= parseDateTime64BestEffort({{end:String}}) "
            f"ORDER BY {dt_where_expr} ASC"
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