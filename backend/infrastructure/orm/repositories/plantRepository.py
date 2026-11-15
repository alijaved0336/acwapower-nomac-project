import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from config.databricks_connector import get_databricks_connector

logger = logging.getLogger(__name__)


class PlantRepository:
    """Repository for handling plant-related database queries with safe parameterized queries"""

    def __init__(self):
        """Initialize repository - connections will be created per operation"""
        pass

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections with proper resource management.
        Ensures cursors are properly closed but keeps the singleton connection alive.

        Yields:
            cursor: Database cursor for executing queries

        Raises:
            Exception: If database connection fails
        """
        connection = None
        cursor = None
        try:
            connection = get_databricks_connector()
            cursor = connection.cursor()
            yield cursor
        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                    logger.info("Transaction rolled back due to error")
                except:
                    pass
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            # Only close the cursor, not the singleton connection
            if cursor:
                cursor.close()
            # Note: We don't close the connection here as it's a singleton that should be reused

    def get_cluster_count_by_table(
        self, table_name: str, where_params: Dict[str, Any] = None
    ) -> int:
        """Query: Get count of clusters in a specific table with safe parameters"""
        base_query = f"SELECT COUNT(*) as cluster_count FROM {table_name}"

        if where_params:
            where_conditions = []
            params = []

            for column, value in where_params.items():
                where_conditions.append(f"{column} = ?")
                params.append(value)

            query = f"{base_query} WHERE {' AND '.join(where_conditions)}"
        else:
            query = base_query
            params = []

        with self._get_connection() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result["cluster_count"] if result else 0

    def get_sites_by_cluster_and_table(
        self, table_name: str, where_params: Dict[str, Any] = None
    ) -> List[Dict]:
        """Query: Get distinct site names with safe parameters"""
        base_query = f"SELECT DISTINCT(Site_Name) FROM {table_name}"

        if where_params:
            where_conditions = []
            params = []

            for column, value in where_params.items():
                where_conditions.append(f"{column} = ?")
                params.append(value)

            query = f"{base_query} WHERE {' AND '.join(where_conditions)}"
        else:
            query = base_query
            params = []

        with self._get_connection() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_all_clusters_from_table(
        self, table_name: str, where_params: Dict[str, Any] = None
    ) -> List[Dict]:
        """Query: Get all distinct clusters with safe parameters"""
        base_query = f"SELECT DISTINCT(Cluster_Name) FROM {table_name}"

        if where_params:
            where_conditions = []
            params = []

            for column, value in where_params.items():
                where_conditions.append(f"{column} = ?")
                params.append(value)

            query = f"{base_query} WHERE {' AND '.join(where_conditions)}"
        else:
            query = base_query
            params = []

        with self._get_connection() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_site_coordinates(self, where_params: Dict[str, Any] = None) -> List[Dict]:
        """Query: Get coordinates for sites with safe parameters"""
        base_query = """
        SELECT Site_Name, Latitute, Longitiude
        FROM hive_metastore.nomac_mpc_swro_gold_j3a.landing_cor
        """

        if where_params:
            where_conditions = []
            params = []

            for column, value in where_params.items():
                where_conditions.append(f"{column} = ?")
                params.append(value)

            query = f"{base_query} WHERE {' AND '.join(where_conditions)}"
        else:
            query = base_query
            params = []

        with self._get_connection() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_all_energy_plants_union(
        self, where_params: Dict[str, Any] = None
    ) -> List[Dict]:
        """Query: Get all energy plants using UNION ALL with safe parameters"""
        # Base subqueries
        subqueries = [
            (
                "hive_metastore.nomac_mpc_swro_gold_j3a.plant_landing",
                "Jubail Energy Plant",
            ),
            (
                "hive_metastore.nomac_mpc_swro_gold_j3a.plant_rabigh_landing",
                "Rabigh Energy Plant",
            ),
            (
                "hive_metastore.nomac_mpc_swro_gold_j3a.plant_stpc_landing",
                "STPC Energy Plant",
            ),
            (
                "hive_metastore.nomac_mpc_swro_gold_j3a.plant_uaq_landing",
                "UAQ Energy Plant",
            ),
        ]

        query_parts = []
        all_params = []

        for table_name, plant_type in subqueries:
            subquery = f"SELECT DISTINCT Site_Name, Cluster_Name, '{plant_type}' as Plant_Type FROM {table_name}"

            if where_params:
                where_conditions = []
                params = []

                for column, value in where_params.items():
                    where_conditions.append(f"{column} = ?")
                    params.append(value)

                subquery = f"{subquery} WHERE {' AND '.join(where_conditions)}"
                all_params.extend(params)

            query_parts.append(subquery)

        final_query = " UNION ALL ".join(query_parts)

        with self._get_connection() as cursor:
            if where_params:
                cursor.execute(final_query, all_params)
            else:
                cursor.execute(final_query)
            return cursor.fetchall()

    def get_plant_kpi_data_from_table(
        self, table_name: str, where_params: Dict[str, Any] = None
    ) -> Optional[Dict]:
        """Query: Get KPI data from a specific plant table with safe parameters"""
        base_query = f"""
                    SELECT Plant_Dispatched_Flow, Plant_Sec, Plant_Power_Consumption, 
                    Plant_Dispatched_Quality, Site_Name, Plant_Daily_Dispatched, Plant_Daily_Dispatched_Percent
                    FROM {table_name}
                 """

        if where_params:
            where_conditions = []
            params = []

            for column, value in where_params.items():
                where_conditions.append(f"{column} = ?")
                params.append(value)

            query = f"{base_query} WHERE {' AND '.join(where_conditions)} ORDER BY datetime DESC"
        else:
            query = f"{base_query} ORDER BY datetime DESC"
            params = []

        with self._get_connection() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def get_plant_kpi_sum_from_table(
        self, table_name: str, where_params: Dict[str, Any] = None
    ) -> Optional[Dict]:
        """Query: Get SUM of KPI data from a specific plant table for total calculations"""
        base_query = f"""
                    SELECT 
                        SUM(Plant_Dispatched_Flow) as Total_Plant_Dispatched_Flow,
                        AVG(Plant_Sec) as Avg_Plant_Sec,
                        SUM(Plant_Power_Consumption) as Total_Plant_Power_Consumption,
                        AVG(Plant_Dispatched_Quality) as Avg_Plant_Dispatched_Quality,
                        AVG(Plant_Daily_Dispatched) as Avg_Plant_Daily_Dispatched,
                        AVG(Plant_Daily_Dispatched_Percent) as Avg_Plant_Daily_Dispatched_Percent
                    FROM (
                        SELECT Plant_Dispatched_Flow, Plant_Sec, Plant_Power_Consumption,
                               Plant_Dispatched_Quality, Plant_Daily_Dispatched, Plant_Daily_Dispatched_Percent
                        FROM {table_name}
                 """

        if where_params:
            where_conditions = []
            params = []

            for column, value in where_params.items():
                where_conditions.append(f"{column} = ?")
                params.append(value)

            query = f"{base_query} WHERE {' AND '.join(where_conditions)} ORDER BY datetime DESC LIMIT 1) as latest_data"
        else:
            query = f"{base_query} ORDER BY datetime DESC LIMIT 1) as latest_data"
            params = []

        with self._get_connection() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
