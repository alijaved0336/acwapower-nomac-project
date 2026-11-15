import logging
from typing import Dict, List

from config.clickhouse_connector import execute_clickhouse_query

logger = logging.getLogger(__name__)

class Dash071Repository:
    """Repository for handling ClickHouse-related database queries"""

    def __init__(self):
        """Initialize repository"""
        pass


    def close(self):
        try:
            self.repo.close()
        except Exception:
            pass

    def fetch_stock_table_data(
            self,
            stock_table: str,
            date_filter: str,
            params: Dict,
    ) -> Dict[str, Dict[str, List]]:
        """
        Fetch data from the stock EAV table only.

        Returns:
            Dict organized by Chemical -> Stream -> Metric -> Value
        """
        query = f"""
        SELECT DateTime, Area, Stream, Chemical, Metric, Value
        FROM `{stock_table}`
        WHERE Chemical IS NOT NULL
        AND Chemical != 'Unknown'
        AND Value IS NOT NULL
          {date_filter}
        ORDER BY Chemical, Stream, Metric, DateTime DESC
        LIMIT 1 BY Chemical, Stream, Metric
        """


        result = execute_clickhouse_query(query, params=params if params else None)


        # Organize stock data by Chemical -> DateTime
        chemical_datetime_map = {}
        stock_data_organized = {}

        for row in result.result_rows:
            dt, area, stream, chemical, metric, value = row

            # Track datetime and area for ppm query
            if chemical not in chemical_datetime_map:
                chemical_datetime_map[chemical] = {
                    'datetime': dt,
                    'area': area
                }

            # Organize stock data with rounding
            if chemical not in stock_data_organized:
                stock_data_organized[chemical] = {}
            if stream not in stock_data_organized[chemical]:
                stock_data_organized[chemical][stream] = {}

            stock_data_organized[chemical][stream][metric] = self._round_value(value)


        return chemical_datetime_map, stock_data_organized

    def fetch_ppm_table_data(
            self,
            ppm_table: str,
            chemical_datetime_map: Dict,
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Fetch ppm and Flow data for each chemical from the ppm EAV table.

        Args:
            ppm_table: Name of the ppm table
            chemical_datetime_map: Dict with datetime and area info for each chemical

        Returns:
            Dict organized by Chemical -> Stream -> Metric -> Value
        """
        ppm_data_organized = {}

        for chemical, info in chemical_datetime_map.items():
            dt = info['datetime']
            area = info['area']

            ppm_query = f"""
            SELECT Stream, Metric, Value
            FROM `{ppm_table}`
            WHERE Chemical = {{chemical:String}}
              AND Area = {{area:String}}
              AND DateTime = {{datetime:DateTime}}
              AND Metric IN ('ppm', 'Flow')
              AND Value IS NOT NULL
            ORDER BY Stream, Metric
            """

            ppm_params = {
                'chemical': chemical,
                'area': area,
                'datetime': dt
            }

            try:
                ppm_result = execute_clickhouse_query(ppm_query, params=ppm_params)



                # Organize ppm data with rounding
                if chemical not in ppm_data_organized:
                    ppm_data_organized[chemical] = {}

                for ppm_row in ppm_result.result_rows:
                    stream, metric, value = ppm_row

                    if stream not in ppm_data_organized[chemical]:
                        ppm_data_organized[chemical][stream] = {}

                    ppm_data_organized[chemical][stream][metric] = self._round_value(value)

            except Exception as e:
                logger.error(f"Error fetching ppm data for {chemical}: {e}")
                ppm_data_organized[chemical] = {}



        return ppm_data_organized