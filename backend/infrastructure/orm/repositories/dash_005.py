import os
from typing import List, Dict, Iterable, Tuple, Optional
from datetime import datetime, timedelta
from config.clickhouse_connector import execute_clickhouse_query
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository

import logging
logger = logging.getLogger(__name__)

class Dash005Repository:
    """
    Encapsulates all ClickHouse access for Dash-005.
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
        return next((c for c in names if c.lower() == "pump"), None) or next((c for c in names if "pump" in c.lower()),
                                                                             None)

    def detect_status_column(self, cols_meta: List[Dict]) -> Optional[str]:
        names = [c["name"] for c in cols_meta if c.get("name")]
        return next((c for c in names if c.lower() == "status"), None) or next(
            (c for c in names if "status" in c.lower()), None)

    def detect_pump_id_column(self, cols_meta: List[Dict]) -> Optional[str]:
        names = [c["name"] for c in cols_meta if c.get("name")]
        return next((c for c in names if c.lower() == "pump_id"), None) or next(
            (c for c in names if "pump_id" in c.lower()), None)

    def get_max_timestamp(self, table_name: str, dt_col: str):
        timezone = self._get_timezone()
        
        # Smart datetime conversion for max calculation
        dt_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%%String%%',
            toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
            toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')
        
        q = f"SELECT max({dt_expr}) FROM {{table:Identifier}}"
        res = execute_clickhouse_query(q, {"table": table_name})
        return res.result_rows[0][0] if (res.result_rows and res.result_rows[0][0]) else None

    def get_min_timestamp(self, table_name: str, dt_col: str):
        """Get the earliest timestamp in the table."""
        timezone = self._get_timezone()
        
        # Smart datetime conversion for min calculation
        dt_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%%String%%',
            toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
            toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')
        
        q = f"SELECT min({dt_expr}) FROM {{table:Identifier}}"
        res = execute_clickhouse_query(q, {"table": table_name})
        return res.result_rows[0][0] if (res.result_rows and res.result_rows[0][0]) else None

    def fetch_closest_timestamp(self,
                                table_name: str,
                                column_names: List[str],
                                dt_col: str,
                                target_datetime: datetime) -> Iterable[Tuple]:
        """
        Fetch the row with the closest timestamp to the target datetime.
        Searches within ±30 minutes of the target.
        """
        try:
            import os
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            timezone = self._get_timezone()

            time_before = target_datetime - timedelta(minutes=30)
            time_after = target_datetime + timedelta(minutes=30)

            # Build column list with smart datetime conversion
            select_columns = []
            for c in column_names:
                if c == dt_col:
                    dt_select = f"""if(toTypeName(`{c}`) LIKE '%%String%%',
                        toTimeZone(parseDateTime64BestEffort(`{c}`), '{timezone}'),
                        toTimeZone(`{c}`, '{timezone}')) as `{c}`""".replace('\n', ' ')
                    select_columns.append(dt_select)
                else:
                    select_columns.append(f"`{c}`")

            # Smart datetime conversion in WHERE clause
            dt_where_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
                toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')

            query = f"""
            SELECT {', '.join(select_columns)}
            FROM `{database}`.`{table_name}`
            WHERE {dt_where_expr} >= toDateTime({{time_before:String}}, '{timezone}')
              AND {dt_where_expr} <= toDateTime({{time_after:String}}, '{timezone}')
            ORDER BY abs(dateDiff('second', {dt_where_expr}, toDateTime({{target_datetime:String}}, '{timezone}'))) ASC
            LIMIT 1
            """

            params = {
                "time_before": time_before.strftime('%Y-%m-%d %H:%M:%S'),
                "time_after": time_after.strftime('%Y-%m-%d %H:%M:%S'),
                "target_datetime": target_datetime.strftime('%Y-%m-%d %H:%M:%S')
            }

            res = execute_clickhouse_query(query, params)
            return res.result_rows or []

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to fetch closest timestamp: {str(e)}")
            return []

    def calculate_simple_average(self,
                                 table_name: str,
                                 column_name: str,
                                 dt_col: str,
                                 start_dt: datetime,
                                 end_dt: datetime) -> Optional[float]:
        try:
            timezone = self._get_timezone()
            
            # Smart datetime conversion in WHERE clause
            dt_where_expr = f"""if(toTypeName({{dt_col:Identifier}}) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort({{dt_col:Identifier}}), '{timezone}'),
                toTimeZone({{dt_col:Identifier}}, '{timezone}'))""".replace('\n', ' ')
            
            query = f"""
            SELECT
                avg({{column_name:Identifier}})
            FROM {{table_name:Identifier}}
            WHERE {dt_where_expr} >= toDateTime({{start_dt:String}}, '{timezone}')
              AND {dt_where_expr} <= toDateTime({{end_dt:String}}, '{timezone}')
              AND {{column_name:Identifier}} IS NOT NULL
            """
            params = {
                "table_name": table_name,
                "column_name": column_name,
                "dt_col": dt_col,
                "start_dt": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                "end_dt": end_dt.strftime('%Y-%m-%d %H:%M:%S')
            }
            result = execute_clickhouse_query(query, params)
            if result.result_rows and result.result_rows[0][0] is not None:
                return float(result.result_rows[0][0])
            return None

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to calculate simple average for {column_name} in {table_name}: {str(e)}")
            return None

    def calculate_weighted_average(self,
                                   table_name: str,
                                   column_name: str,
                                   dt_col: str,
                                   start_dt: datetime,
                                   end_dt: datetime) -> Optional[float]:
        try:
            timezone = self._get_timezone()
            
            # Smart datetime conversion in WHERE clause
            dt_where_expr = f"""if(toTypeName({{dt_col:Identifier}}) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort({{dt_col:Identifier}}), '{timezone}'),
                toTimeZone({{dt_col:Identifier}}, '{timezone}'))""".replace('\n', ' ')
            
            query = f"""
            WITH ranked_data AS (
                SELECT
                    {{column_name:Identifier}} as value,
                    ROW_NUMBER() OVER (ORDER BY {{dt_col:Identifier}}) as row_num
                FROM {{table_name:Identifier}}
                WHERE {dt_where_expr} >= toDateTime({{start_dt:String}}, '{timezone}')
                  AND {dt_where_expr} <= toDateTime({{end_dt:String}}, '{timezone}')
                  AND {{column_name:Identifier}} IS NOT NULL
            )
            SELECT
                sum(value * row_num) / sum(row_num) as weighted_avg
            FROM ranked_data
            """
            params = {
                "table_name": table_name,
                "column_name": column_name,
                "dt_col": dt_col,
                "start_dt": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                "end_dt": end_dt.strftime('%Y-%m-%d %H:%M:%S')
            }
            result = execute_clickhouse_query(query, params)
            if result.result_rows and result.result_rows[0][0] is not None:
                return float(result.result_rows[0][0])
            return None

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to calculate weighted average for {column_name} in {table_name}: {str(e)}")
            return None

    def fetch_exact_timestamp_row(self,
                                  table_name: str,
                                  column_names: List[str],
                                  dt_col: str,
                                  target_datetime: datetime) -> Iterable[Tuple]:
        """
        Fetch row for exact timestamp match.
        """
        try:
            import os
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            timezone = self._get_timezone()

            # Build column list with smart datetime conversion
            select_columns = []
            for c in column_names:
                if c == dt_col:
                    dt_select = f"""if(toTypeName(`{c}`) LIKE '%%String%%',
                        toTimeZone(parseDateTime64BestEffort(`{c}`), '{timezone}'),
                        toTimeZone(`{c}`, '{timezone}')) as `{c}`""".replace('\n', ' ')
                    select_columns.append(dt_select)
                else:
                    select_columns.append(f"`{c}`")

            # Smart datetime conversion in WHERE clause
            dt_where_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
                toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')

            query = f"""
            SELECT {', '.join(select_columns)}
            FROM `{database}`.`{table_name}`
            WHERE {dt_where_expr} = toDateTime({{target_datetime:String}}, '{timezone}')
            LIMIT 1
            """

            params = {"target_datetime": target_datetime.strftime('%Y-%m-%d %H:%M:%S')}

            res = execute_clickhouse_query(query, params)
            return res.result_rows or []

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to fetch exact timestamp: {str(e)}")
            return []

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

    def fetch_pump_ids_for_pumps(self,
                                 table_name: str,
                                 pump_col: str,
                                 pump_id_col: str,
                                 pump_values: List[str],
                                 dt_col: Optional[str]) -> Dict[str, str]:
        """
        Fetch Pump_ID for multiple pumps from the latest row for each pump.
        Returns a dictionary mapping pump_value -> pump_id.
        """
        if not pump_values:
            return {}
        
        try:
            timezone = self._get_timezone()
            
            # Build WHERE clause for pump values
            pump_placeholders = []
            params = {"table": table_name}
            for i, pump_val in enumerate(pump_values):
                key = f"pump_{i}"
                pump_placeholders.append(f"{{{key}:String}}")
                params[key] = str(pump_val)
            
            # Build query to get Pump_ID for each pump from latest row
            if dt_col:
                # Smart datetime conversion in ORDER BY
                dt_order_expr = f"""if(toTypeName(`{dt_col}`) LIKE '%%String%%',
                    toTimeZone(parseDateTime64BestEffort(`{dt_col}`), '{timezone}'),
                    toTimeZone(`{dt_col}`, '{timezone}'))""".replace('\n', ' ')
                
                query = (
                    f"SELECT `{pump_col}` AS pump_value, `{pump_id_col}` AS pump_id_value "
                    f"FROM {{table:Identifier}} "
                    f"WHERE `{pump_col}` IN ({', '.join(pump_placeholders)}) "
                    f"AND `{pump_id_col}` IS NOT NULL "
                    f"ORDER BY `{pump_col}` ASC, {dt_order_expr} DESC "
                    f"LIMIT 1 BY `{pump_col}`"
                )
            else:
                query = (
                    f"SELECT `{pump_col}` AS pump_value, `{pump_id_col}` AS pump_id_value "
                    f"FROM {{table:Identifier}} "
                    f"WHERE `{pump_col}` IN ({', '.join(pump_placeholders)}) "
                    f"AND `{pump_id_col}` IS NOT NULL "
                    f"LIMIT 1 BY `{pump_col}`"
                )
            
            res = execute_clickhouse_query(query, params)
            
            # Build dictionary mapping pump_value -> pump_id
            pump_id_map = {}
            for row in res.result_rows or []:
                if len(row) >= 2 and row[0] is not None and row[1] is not None:
                    pump_value = str(row[0])
                    pump_id = str(row[1])
                    pump_id_map[pump_value] = pump_id
            
            return pump_id_map
            
        except Exception as e:
            logger.error(f"Failed to fetch Pump_IDs for pumps: {str(e)}")
            return {}

    def fetch_pump_transitions(self,
                               table_name: str,
                               dt_col: str,
                               pump_col: str,
                               status_col: str,
                               start_dt: datetime,
                               end_dt: datetime) -> Iterable[Tuple]:
        """
        Fetch start and stop transitions for each pump in the given date range.
        """
        try:
            timezone = self._get_timezone()
            
            # Smart datetime conversion for SELECT
            dt_select = f"""if(toTypeName({dt_col}) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort({dt_col}), '{timezone}'),
                toTimeZone({dt_col}, '{timezone}')) AS ts""".replace('\n', ' ')
            
            # Smart datetime conversion in WHERE clause
            dt_where_expr = f"""if(toTypeName({dt_col}) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort({dt_col}), '{timezone}'),
                toTimeZone({dt_col}, '{timezone}'))""".replace('\n', ' ')
            
            query = f"""
               WITH ordered_data AS (
                   SELECT 
                       {pump_col} AS pump_value,
                       {status_col} AS status_value,
                       {dt_select},
                       lagInFrame({status_col}) OVER (PARTITION BY {pump_col} ORDER BY {dt_col}) AS prev_status
                   FROM {{table:Identifier}}
                   WHERE {dt_where_expr} >= toDateTime({{start:String}}, '{timezone}')
                     AND {dt_where_expr} < toDateTime({{end:String}}, '{timezone}')
                     AND {status_col} IS NOT NULL
               ),
               transitions AS (
                   SELECT 
                       pump_value,
                       status_value,
                       ts,
                       prev_status
                   FROM ordered_data
                   WHERE prev_status IS NULL
                      OR status_value != prev_status
               )
               SELECT 
                   pump_value,
                   status_value,
                   ts
               FROM transitions
               ORDER BY pump_value ASC, ts ASC
               """

            params = {
                "table": table_name,
                "start": start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                "end": end_dt.strftime('%Y-%m-%d %H:%M:%S')
            }

            res = execute_clickhouse_query(query, params)
            return res.result_rows or []

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to fetch pump transitions: {str(e)}")
            return self.fetch_actions_range_all_pumps(
                table_name, dt_col, pump_col, status_col, start_dt, end_dt
            )

    def fetch_pump_transitions_selected(self,
                                        table_name: str,
                                        dt_col: str,
                                        pump_col: str,
                                        status_col: str,
                                        start_dt: datetime,
                                        end_dt: datetime,
                                        selected_pumps: List[str]) -> Iterable[Tuple]:
        """
        Fetch start and stop transitions for selected pumps.
        """
        try:
            timezone = self._get_timezone()
            
            # Smart datetime conversion for SELECT
            dt_select = f"""if(toTypeName({dt_col}) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort({dt_col}), '{timezone}'),
                toTimeZone({dt_col}, '{timezone}')) AS ts""".replace('\n', ' ')
            
            # Smart datetime conversion in WHERE clause
            dt_where_expr = f"""if(toTypeName({dt_col}) LIKE '%%String%%',
                toTimeZone(parseDateTime64BestEffort({dt_col}), '{timezone}'),
                toTimeZone({dt_col}, '{timezone}'))""".replace('\n', ' ')
            
            # Build pump filter
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

            pump_filter = f"AND {norm_expr} IN ({', '.join(placeholders)})"

            query = f"""
               WITH ordered_data AS (
                   SELECT 
                       {pump_col} AS pump_value,
                       {status_col} AS status_value,
                       {dt_select},
                       lagInFrame({status_col}) OVER (PARTITION BY {pump_col} ORDER BY {dt_col}) AS prev_status
                   FROM {{table:Identifier}}
                   WHERE {dt_where_expr} >= toDateTime({{start:String}}, '{timezone}')
                     AND {dt_where_expr} < toDateTime({{end:String}}, '{timezone}')
                     AND {status_col} IS NOT NULL
                     {pump_filter}
               ),
               transitions AS (
                   SELECT 
                       pump_value,
                       status_value,
                       ts,
                       prev_status
                   FROM ordered_data
                   WHERE prev_status IS NULL
                      OR status_value != prev_status
               )
               SELECT 
                   pump_value,
                   status_value,
                   ts
               FROM transitions
               ORDER BY pump_value ASC, ts ASC
               """

            res = execute_clickhouse_query(query, params)
            return res.result_rows or []

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to fetch pump transitions for selected pumps: {str(e)}")
            # Fallback to all records for selected pumps
            return self.fetch_actions_range_selected_pumps(
                table_name, dt_col, pump_col, status_col, start_dt, end_dt, selected_pumps
            )