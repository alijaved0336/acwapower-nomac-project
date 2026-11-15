import copy
import re
import logging
import json
import statistics
from datetime import datetime, timedelta

from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

from constants import (DatabaseColumns, ErrorMessages, KPIConfig, LogMessages,
                       PlantConfig, QualityConfig, DatabaseConfig, Dash033Config)
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.orm.repositories.dash_001_repository import Dash001Repository
from config.optimized_clickhouse_connector import execute_optimized_clickhouse_query
from infrastructure.orm.repositories.roles import RoleRepository

from infrastructure.helpers.dash_001_helper import Dash001Helper
from itertools import groupby

from infrastructure.utils.datetime_utils import DateTimeParser

logger = logging.getLogger(__name__)


class Dash_001Service:
    """Modified service to use ClickHouse repository with proper KPI structure"""

    def __init__(self):
        self.clickhouse_repository = ClickHouseRepository()
        self.dash_001_repository = Dash001Repository()

    def __del__(self):
        """Cleanup repository connection when service is destroyed"""
        pass
    
    
    def get_plants_by_cluster_for_role(self, cluster_filters, role_id: Optional[str]) -> List[Dict]:
        """
        Get plants by cluster for role. 
        Supports 'All Clusters' to return all assigned clusters and sites.
        """
        
        if not role_id:
            logger.info(ErrorMessages.NO_ROLE_PROVIDED)
            return []
        
        try:

            if isinstance(cluster_filters, str):
                normalized_filters = [cluster_filters]
            elif isinstance(cluster_filters, list):
                normalized_filters = cluster_filters
            else:
                logger.error(f"Invalid cluster_filters type: {type(cluster_filters)}")
                return []
            
            role_repo = RoleRepository()
            role = role_repo.get_by_id(role_id)

            if not role:
                logger.warning(ErrorMessages.ROLE_NOT_FOUND.format(role_id=role_id))
                return []

            raw_clusters = Dash001Helper.normalize_role_clusters(role)

            
            if not raw_clusters:
                logger.info(ErrorMessages.NO_CLUSTERS_ASSIGNED.format(role_id=role_id))
                return []
            
            # --- Parse clusters into structured form ---
            clusters_with_plants = Dash001Helper._get_clusters_for_plants(raw_clusters)
            
            # Check if requesting "All Clusters"
            is_all_clusters = any(
                filter_val.strip().lower() in ["all clusters", "all"] 
                for filter_val in normalized_filters
            )
            
            if is_all_clusters:
                # Return plants from ALL assigned clusters
                clusters_to_process = list(clusters_with_plants.keys())
                logger.info(f"Processing ALL clusters for role {role_id}: {clusters_to_process}")
            else:
                # Extract clean cluster name
                clean_cluster_name = cluster_filters.split(": ", 1)[1] if ": " in cluster_filters else cluster_filters
                
                # Check if cluster exists in user's assigned clusters
                if clean_cluster_name not in clusters_with_plants:
                    logger.info(f"Cluster {clean_cluster_name} not found in user's assigned clusters")
                    return []
                
                clusters_to_process = [clean_cluster_name]
            
            # Process plants for the selected clusters
            matching_plants = []
            seen_sites = set()

            plants_with_cluster = []
            
            plant_sites = DatabaseConfig.PLANT_SITES
            
            # Iterate through each cluster to process
            for cluster_name in clusters_to_process:
                cluster_filter_data = clusters_with_plants.get(cluster_name, [])
                
                # Build cluster filter string for query
                cluster_filter = f"Cluster: {cluster_name}" if ": " not in cluster_name else cluster_name
                
                for site_name, table_name in plant_sites.items():
                    if site_name in seen_sites:
                        continue
                    
                    # Check if site is assigned to this cluster
                    if site_name not in cluster_filter_data:
                        continue
                    
                    try:
                        has_cluster_data = self._get_cluster_data_for_table(
                            site_name, table_name, [cluster_filter]
                        )
                        
                        if has_cluster_data:
                            seen_sites.add(site_name)
                            plants_with_cluster.append((site_name, table_name, cluster_name))
                            logger.info(f"Site {site_name} has cluster data for cluster {cluster_name}")

                    except Exception as e:
                        logger.warning(f"Error processing site {site_name} for cluster {cluster_name}: {e}")
                        continue

            # Calculate KPI data with proper plant mappings
            plant_mappings = {
                table_name: Dash001Helper._get_plant_name_for_site(site_name) 
                for site_name, table_name, _ in plants_with_cluster
            }
            
            plant_kpi_data = (
                self.get_plant_kpi_data(plant_mappings, None) 
                if plants_with_cluster 
                else Dash001Helper._get_empty_kpi_data()
            )

            # Create plant objects for matching plants
            for site_name, table_name, cluster_name in plants_with_cluster:
                try:
                    # Get the specific cluster for this site with proper formatting
                    site_cluster = f"Cluster: {cluster_name}"
                    
                    plant_info = {
                        "id": site_name.lower().replace(" ", "_").replace("-", "_"),
                        "name": Dash001Helper._get_plant_name_for_site(site_name),
                        "site_name": site_name,
                        "cluster": site_cluster,
                        "group": PlantConfig.ENERGY_GROUP,
                        "plant_kpis": copy.deepcopy(plant_kpi_data),
                    }
                    matching_plants.append(plant_info)
                    logger.info(f"Added plant: {site_name} with cluster {site_cluster}")
                except Exception as e:
                    logger.warning(f"Error creating plant object for {site_name}: {e}")
                    continue

            logger.info(f"Found {len(matching_plants)} plants for clusters: {clusters_to_process}")
            return matching_plants


      
        except Exception as e:
            logger.error(f"Error getting plants by clusters {cluster_filters}: {e}")
            return []



    def get_plant_kpi_data(self, plant_mappings, cluster_filters=None) -> List[Dict]:
        """
        Get plant KPI data with optional cluster filtering - UPDATED TO HANDLE MULTIPLE CLUSTERS

        Args:
            plant_mappings: Dictionary mapping table names to plant names
            cluster_filters: Single cluster string, list of clusters, or None
        """
        logger.info(f"Getting plant KPI data with cluster_filters: {cluster_filters}")

        # Validate input parameters
        if not plant_mappings or not isinstance(plant_mappings, dict):
            logger.error("Invalid plant_mappings provided")
            raise ValueError(ErrorMessages.INVALID_PLANT_MAPPINGS)

        # Normalize cluster_filters to a list
        if cluster_filters is None:
            normalized_cluster_filters = None
        elif isinstance(cluster_filters, str):
            normalized_cluster_filters = [cluster_filters]
        elif isinstance(cluster_filters, list):
            normalized_cluster_filters = cluster_filters
        else:
            logger.warning(f"Invalid cluster_filters type: {type(cluster_filters)}")
            normalized_cluster_filters = None

        logger.info(f"Normalized cluster filters: {normalized_cluster_filters}")

        kpi_template = [
            {"key": 1, "kpi": "Production"},
            {"key": 2, "kpi": "Load"},
            {"key": 3, "kpi": "Sec"},
            {"key": 4, "kpi": "Power"},
            {"key": 5, "kpi": "Availability"},
            {"key": 6, "kpi": "Quality"},
            {"key": 7, "kpi": "Daily Dispatch"},
            {"key": 8, "kpi": "Daily Dispatch Percentage"},
        ]

        # Initialize KPI data with plant columns
        kpi_data = [
            {**row, **{plant_name: None for plant_name in plant_mappings.values()}}
            for row in kpi_template
        ]

        # KPI mapping with rounding to 2 decimal places
        def round_formatter(value, unit=""):
            """Format value with rounding to 2 decimal places"""
            if value is None:
                return "N/A"
            try:
                rounded = round(float(value), 2)
                return f"{rounded}{unit}" if unit else str(rounded)
            except (ValueError, TypeError):
                return "N/A"

        def quality_formatter(value):
            """Format quality value - handles both string (OK/Not OK) and numeric values"""
            if value is None or (isinstance(value, str) and not value.strip()):
                return "N/A"
            # If it's already a string like "OK" or "Not OK", return it with "%"
            if isinstance(value, str):
                value_upper = value.upper().strip()
                if value_upper in ["OK", "NOT OK", "NOTOK"]:
                    # Return the original value (preserving case) with "%"
                    return f"{value.strip()}"
                # If it's a numeric string, try to convert
                try:
                    rounded = round(float(value), 2)
                    return f"{rounded}"
                except (ValueError, TypeError):
                    # If conversion fails, return the string value with "%"
                    return f"{value.strip()}"
            # If it's numeric, round and format
            try:
                rounded = round(float(value), 2)
                return f"{rounded}"
            except (ValueError, TypeError):
                return "N/A"

        kpi_column_mapping = {
            "Production": ("Plant_Dispatched_Flow", lambda v: round_formatter(v, " m3/h")),
            "Load": ("Plant_Dispatched_Flow", lambda v: round_formatter(v, " m3/h")),
            "Sec": ("Plant_SEC", lambda v: round_formatter(v)),
            "Power": ("Plant_Power_Consumption", lambda v: round_formatter(v, " kW")),
            "Availability": (None, lambda v: "N/A"),
            "Quality": ("Plant_Dispatched_Quality", quality_formatter),
            "Daily Dispatch": ("Plant_Daily_Dispatched", lambda v: round_formatter(v)),
            "Daily Dispatch Percentage": ("Plant_Daily_Dispatched_Percent", lambda v: round_formatter(v, "%")),
        }

        # Initialize totals
        total_dispatched_flow = 0
        total_power_consumption = 0
        total_production = 0
        quality_values = []

        try:
            for table_name, plant_name in plant_mappings.items():
                logger.debug(f"Processing plant: {plant_name} from table: {table_name}")

                try:
                    result = self._get_plant_kpi_data_from_table(table_name, normalized_cluster_filters)


                    if not result:
                        logger.warning(f"No data found for plant: {plant_name}")
                        continue

                    # Set individual plant values
                    for row in kpi_data:
                        kpi = row["kpi"]
                        col_name, formatter = kpi_column_mapping[kpi]
                        
                        # For Daily Dispatch, always use PLANT_DAILY_DISPATCHED since _get_plant_kpi_data_from_table
                        # maps both columns to this key in result_dict
                        if kpi == "Daily Dispatch":
                            col_name = DatabaseColumns.PLANT_DAILY_DISPATCHED
                        
                        if col_name is None:
                            row[plant_name] = formatter(None)
                        else:
                            try:
                                value = result.get(col_name) if hasattr(result, "get") else result[col_name]
                                # Always call formatter - it handles None values
                                row[plant_name] = formatter(value)
                            except (KeyError, TypeError, ValueError) as e:
                                logger.warning(f"Error formatting {kpi} for {plant_name}: {e}")
                                row[plant_name] = "N/A"

                    # For totals - accumulate from the result
                    total_dispatched_flow, total_power_consumption, quality_values, total_production = (
                        self._accumulate_totals(
                            result,
                            kpi_column_mapping,
                            total_dispatched_flow,
                            total_power_consumption,
                            quality_values,
                            total_production
                        )
                    )

                except Exception as e:
                    logger.error(f"Error processing plant {plant_name}: {e}")
                    continue

            # Calculate SEC, evaluate quality, and update totals
            calculated_sec = self._calculate_sec(total_power_consumption, total_dispatched_flow)
            quality_total = self._evaluate_quality_status(quality_values)
            self._update_kpi_totals(
                kpi_data,
                total_dispatched_flow,
                total_power_consumption,
                calculated_sec,
                quality_total,
                total_production
            )

            logger.info(f"Successfully processed KPI data for {len(plant_mappings)} plants")
            return kpi_data

        except Exception as e:
            logger.error(f"Critical error in get_plant_kpi_data: {e}")
            return kpi_data

    def _get_plant_kpi_data_from_table(self, table_name: str, cluster_filters=None) -> Optional[Dict]:
        """
        Updated to handle multiple cluster filters using IN clause
        AND use different daily dispatch columns based on site
        """
        try:
            # Get site name from table name
            site_name = Dash001Helper._get_site_name_from_table(table_name)
            if not site_name:
                logger.warning(f"Could not find site name for table: {table_name}")
                return None

            # Get ClickHouse table name
            clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(site_name, table_name)
            if not clickhouse_table_name:
                logger.debug(f"No ClickHouse table found for {site_name}.{table_name}")
                return None



            logger.debug(f"Using daily dispatch column {DatabaseColumns.PLANT_DAILY_DISPATCHED} for site {site_name}")

            # Define KPI columns to retrieve
            kpi_columns = [
                DatabaseColumns.PLANT_DISPATCHED_FLOW,
                DatabaseColumns.PLANT_POWER_CONSUMPTION,
                DatabaseColumns.PLANT_SEC,
                DatabaseColumns.PLANT_DISPATCHED_QUALITY,
                DatabaseColumns.PLANT_DAILY_DISPATCHED,  # Use the conditional column
                DatabaseColumns.PLANT_DAILY_DISPATCHED_PERCENT
            ]

            # Build where conditions for multiple clusters
            where_conditions = []
            params = {}

            if cluster_filters:
                if len(cluster_filters) == 1:
                    # Single cluster - use equality
                    where_conditions.append(f"`{DatabaseColumns.CLUSTER_NAME}` = {{cluster_0:String}}")
                    params['cluster_0'] = cluster_filters[0]
                else:
                    # Multiple clusters - use IN clause
                    cluster_placeholders = []
                    for i, cluster_value in enumerate(cluster_filters):
                        param_key = f"cluster_{i}"
                        cluster_placeholders.append(f"{{{param_key}:String}}")
                        params[param_key] = cluster_value
                    where_conditions.append(f"`{DatabaseColumns.CLUSTER_NAME}` IN ({', '.join(cluster_placeholders)})")

            # Get datetime column for ordering
            datetime_column = self.clickhouse_repository.get_datetime_column(clickhouse_table_name)

            # Build optimized query for LATEST single record
            kpi_columns_str = ', '.join([f"`{col}`" for col in kpi_columns])

            query = f"SELECT {kpi_columns_str} FROM `{clickhouse_table_name}`"

            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)

            if datetime_column:
                query += f" ORDER BY `{datetime_column}` DESC"

            query += " LIMIT 1"

            logger.info(f"Fetching KPI data for {site_name} with filters: {cluster_filters}")
            result = execute_optimized_clickhouse_query(
                query,
                params=params if params else None,
                use_cache=True,
                cache_ttl=300  # Cache KPI data for 5 minutes
            )
            kpi_data = result.result_rows

            if kpi_data and len(kpi_data) > 0:
                row = kpi_data[0]

                result_dict = {}

                for i, column_name in enumerate(kpi_columns):
                    if i < len(row):
                        # Map the conditional column back to standard name
                        if column_name == DatabaseColumns.PLANT_DAILY_DISPATCHED:
                            result_dict[DatabaseColumns.PLANT_DAILY_DISPATCHED] = row[i]
                        else:
                            result_dict[column_name] = row[i]
                    else:
                        result_dict[column_name] = None

                logger.info(
                    f"KPI data retrieved for {site_name}: Production={result_dict.get(DatabaseColumns.PLANT_DISPATCHED_FLOW)}, Power={result_dict.get(DatabaseColumns.PLANT_POWER_CONSUMPTION)}")
                return result_dict

            logger.warning(
                f"No KPI data rows returned for {site_name}.{table_name} with cluster filters: {cluster_filters}")
            return None

        except Exception as e:
            logger.error(f"Error getting KPI data from table {table_name}: {e}", exc_info=True)
            return None


    def _accumulate_totals(
            self,
            filtered_result: Any,
            kpi_column_mapping: Dict,
            total_dispatched_flow: float,
            total_power_consumption: float,
            quality_values: List,
            total_production:float
    ) -> Tuple[float, float, List, float]:
        """Accumulate total values for KPI calculations with validation"""
        logger = logging.getLogger(__name__)

        try:
            # Extract production and power values first
            production_value = None
            power_value = None

            # Get production value using constant column name
            try:
                prod_raw = (
                    filtered_result.get(DatabaseColumns.PLANT_DISPATCHED_FLOW)
                    if hasattr(filtered_result, "get")
                    else filtered_result[DatabaseColumns.PLANT_DISPATCHED_FLOW]
                )
                if prod_raw is not None and str(prod_raw).upper() != "N/A":
                    production_value = float(prod_raw)
            except (ValueError, TypeError, KeyError) as e:
                logger.debug(f"Could not extract production value: {e}")

            # Get power value using constant column name
            try:
                power_raw = (
                    filtered_result.get(DatabaseColumns.PLANT_POWER_CONSUMPTION)
                    if hasattr(filtered_result, "get")
                    else filtered_result[DatabaseColumns.PLANT_POWER_CONSUMPTION]
                )
                if power_raw is not None and str(power_raw).upper() != "N/A":
                    power_value = float(power_raw)
                    # Validate power: must be > 0 and >= 200
                    if power_value <= 0 or power_value < 200:
                        logger.warning(
                            f"Invalid power value: {power_value} (must be >= 200)"
                        )
                        power_value = None
            except (ValueError, TypeError, KeyError) as e:
                logger.debug(f"Could not extract power value: {e}")

            # ===== MODIFIED LOGIC: Only accumulate if BOTH values are valid =====
            total_production += production_value
            if production_value is not None and power_value is not None:
                total_dispatched_flow += production_value
                total_power_consumption += power_value
                logger.debug(
                    f"Added site data - Production: {production_value}, Power: {power_value}. "
                    f"Running totals - Flow: {total_dispatched_flow}, Power: {total_power_consumption}"
                )
            else:
                logger.info(
                    f"Site excluded from SEC calculation - Production: {production_value}, Power: {power_value}. "
                    "Both values must be valid to be included in totals."
                )

            # Handle Quality separately (always accumulate if available)
            quality_col = kpi_column_mapping.get("Quality")[0] if kpi_column_mapping.get("Quality") else None
            if quality_col:
                try:
                    quality_raw = (
                        filtered_result.get(quality_col)
                        if hasattr(filtered_result, "get")
                        else filtered_result[quality_col]
                    )
                    if quality_raw is not None:
                        quality_values.append(quality_raw)
                except (ValueError, TypeError, KeyError) as e:
                    logger.debug(f"Could not extract quality value: {e}")

        except Exception as e:
            logger.error(f"Error in _accumulate_totals: {e}")

        return total_dispatched_flow, total_power_consumption, quality_values, total_production

    def get_all_clusters(self) -> List[Dict]:
        """
        Retrieve all unique clusters across all sites using ClickHouse.
        
        Returns:
            A list of cluster dictionaries in the format:
            {
                "id": "Cluster: MEASEA",
                "name": "MEASEA",
                "plant": "<Plant Name>",
                "group": "<Energy Group>",
                "sites": []
            }
            """
        try:
            all_clusters = []
            seen_clusters = set()

            logger.info("[Clusters] Fetching clusters for all sites...")
            for site_name, table_name in DatabaseConfig.PLANT_SITES.items():
                logger.debug(f"[Clusters] Processing site={site_name}, table={table_name}")

                try:
                    cluster = self._get_clusters_from_table(site_name, table_name)
                    logger.info(f"get clusters from table sv {cluster}")
                    if not cluster:
                        logger.debug(f"No cluster found for {site_name}.{table_name}")
                        continue

                    if not cluster or cluster in seen_clusters:
                        continue

                    
                    seen_clusters.add(cluster)

                    # Extract clean cluster name safely
                    clean_cluster_name = cluster.split(": ", 1)[1] if ": " in cluster else cluster

                    cluster_info = {
                        "id": cluster,
                        "name": clean_cluster_name,
                        "plant": Dash001Helper._get_plant_name_for_site(site_name),
                        "group": PlantConfig.ENERGY_GROUP,
                        "sites": [],
                    }
                    all_clusters.append(cluster_info)

                    logger.debug(f"[Clusters] Added cluster '{cluster}' from site '{site_name}'")

                except Exception as site_error:
                    logger.warning(f"[Clusters] Error fetching clusters for {site_name}: {site_error}")
                    continue

            logger.info(f"[Clusters] Retrieved {len(all_clusters)} unique clusters across all sites.")
            return all_clusters

        except Exception as e:
            logger.exception(f"[Clusters] Unexpected error in get_all_clusters: {e}")
            return []


    def get_plants_with_kpis_for_role(self, role_id: Optional[str]) -> Dict:
        """Get plants with KPIs filtered by user's role"""
        if not role_id:
            logger.info(ErrorMessages.NO_ROLE_PROVIDED)
            return {
                "plants": [],
                "summary": {
                    "total_plants": 0,
                    "active_plants": 0,
                    "maintenance_plants": 0,
                },
                "plant_kpis": Dash001Helper._get_empty_kpi_data_with_plants(),
            }

        # Fetch role_clusters (new structure with sites)
        role_clusters = self.get_clusters_for_role(role_id)

        if not role_clusters:
            logger.info(ErrorMessages.NO_CLUSTERS_ASSIGNED.format(role_id=role_id))
            return {
                "plants": [],
                "summary": {
                    "total_plants": 0,
                    "active_plants": 0,
                    "maintenance_plants": 0,
                },
                "plant_kpis": Dash001Helper._get_empty_kpi_data_with_plants(),
            }

        # Build mapping of cluster_id -> set(sites)
        allowed_sites_by_cluster = {
            cluster.get("id"): set(cluster.get("sites", []))
            for cluster in role_clusters
        }

        logger.info(f"Filtering plants by role_clusters: {allowed_sites_by_cluster}")


        all_plants = self.get_energy_plants()
        filtered_plants = []

        # --- Embedded filter_energy_plants logic ---
        for plant in all_plants:
            cluster_id = plant.get("cluster", "")
            if cluster_id not in allowed_sites_by_cluster:
                continue

            allowed_sites = allowed_sites_by_cluster[cluster_id]

            # If no sites specified -> allow all plants in cluster
            if not allowed_sites or plant.get("id") in allowed_sites:
                filtered_plants.append(plant)

        logger.info(
            LogMessages.FILTERED_PLANTS.format(
                filtered_count=len(filtered_plants), total_count=len(all_plants)
            )
        )

        # Map plants to DB table names for KPI fetching
        plant_mappings = {}
        for plant in filtered_plants:
            site_name = plant.get("name")
            if site_name in DatabaseConfig.PLANT_SITES:
                table_name = DatabaseConfig.PLANT_SITES[site_name]
                plant_mappings[table_name] = Dash001Helper._get_plant_name_for_site(site_name)
        # Fetch KPI data for plants
        plant_kpi_data = self.get_plant_kpi_data(plant_mappings, None)

        


        # Enhance plant data with KPIs
        plants_with_kpis = []
        for plant in filtered_plants:

            enhanced_plant = {
                **plant,
                "coordinates": {
                    "lat": plant["coordinates"][0],
                    "lon": plant["coordinates"][1],
                },
                "kpis": {
                    "production": f"{plant['capacity']}",
                    "efficiency": (
                        KPIConfig.DEFAULT_EFFICIENCY_ACTIVE
                        if plant["status"] == PlantConfig.STATUS_ACTIVE
                        else KPIConfig.DEFAULT_EFFICIENCY_MAINTENANCE
                    ),
                    "status": plant["status"],
                },
            }
            plants_with_kpis.append(enhanced_plant)

        return {
            "plants": plants_with_kpis,
            "summary": {
                "total_plants": len(filtered_plants),
                "active_plants": len(
                    [p for p in filtered_plants if p["status"] == PlantConfig.STATUS_ACTIVE]
                ),
                "maintenance_plants": len(
                    [p for p in filtered_plants if p["status"] == PlantConfig.STATUS_MAINTENANCE]
                ),
            },
            "plant_kpis": plant_kpi_data,
        }
  

    def get_energy_plants(self) -> List[Dict]:
        """Get all energy plants from ClickHouse"""
        try:
            plant_sites = list(DatabaseConfig.PLANT_SITES.keys())
            energy_plants = []
            seen_sites = set()

            coordinates_map = self._get_coordinates_map()

            for site_name in plant_sites:
                if site_name in seen_sites:
                    continue

                try:
                    cluster_name = self._get_cluster_for_site(site_name)
                    if not cluster_name:
                        continue

                    seen_sites.add(site_name)
                    # Try to get coordinates with original site name first, then normalized name
                    coordinates = coordinates_map.get(site_name)
                    if coordinates is None:
                        normalized_name = self._normalize_site_name(site_name)
                        coordinates = coordinates_map.get(normalized_name, [0, 0])

                    plant_info = {
                        "id": site_name,
                        "name": site_name,
                        "plant_type": Dash001Helper._get_plant_type_for_site(site_name),
                        "cluster": cluster_name,
                        "coordinates": coordinates,
                        "capacity": PlantConfig.UNKNOWN_CAPACITY,
                        "status": PlantConfig.STATUS_ACTIVE,
                        "type": PlantConfig.ENERGY_GROUP,
                    }
                    energy_plants.append(plant_info)
                    logger.info(f"Added energy plant: {site_name}")

                except Exception as e:
                    logger.warning(f"Error processing energy plant for site {site_name}: {e}")
                    continue

            logger.info(f"Retrieved {len(energy_plants)} energy plants")
            return energy_plants

        except Exception as e:
            logger.error(f"Error getting energy plants: {e}")
            return []


    def _get_cluster_data_for_table(self, site_name: str, table_name: str, cluster_filters) -> bool:
        """Check if table contains cluster data matching any of the filters - UPDATED"""
        try:
            if cluster_filters is None:
                return True 
            elif isinstance(cluster_filters, str):
                normalized_filters = [cluster_filters]
            elif isinstance(cluster_filters, list):
                normalized_filters = cluster_filters
            else:
                logger.warning(f"Invalid cluster_filters type: {type(cluster_filters)}")
                return False

            logger.debug(f"Checking for cluster data {normalized_filters} in {site_name}.{table_name}")
            
            clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(site_name, table_name)
            if not clickhouse_table_name:
                logger.debug(f"No ClickHouse table found for {site_name}.{table_name}")
                return False

            where_conditions = []
            query_params = {}
            
            if len(normalized_filters) == 1:
                where_conditions.append(f"`{DatabaseColumns.CLUSTER_NAME}` = %(cluster_name)s")
                query_params["cluster_name"] = normalized_filters[0]
            else:
                # Multiple clusters - use IN clause
                placeholders = []
                for idx, cluster_value in enumerate(normalized_filters):
                    key = f"cluster_name_{idx}"
                    placeholders.append(f"%({key})s")
                    query_params[key] = cluster_value

                where_conditions.append(f"`{DatabaseColumns.CLUSTER_NAME}` IN ({', '.join(placeholders)})")

            try:
                cluster_data = self.clickhouse_repository.get_column_data_for_table(
                    clickhouse_table_name=clickhouse_table_name,
                    column_names=[DatabaseColumns.CLUSTER_NAME],
                    where_conditions=where_conditions,
                    query_params=query_params
                )

                # Extract data from repository response
                # cluster_data = result_dict.get("result_rows", [])
            except Exception as column_error:
                # If column doesn't exist, return False
                if "UNKNOWN_IDENTIFIER" in str(column_error) or "Unknown expression identifier" in str(column_error):
                    logger.debug(f"Column {DatabaseColumns.CLUSTER_NAME} does not exist in {clickhouse_table_name}")
                    return False
                else:
                    raise column_error

            has_data = len(cluster_data) > 0
            logger.debug(f"Cluster filters {normalized_filters} found in {site_name}.{table_name}: {has_data}")
            return has_data

        except Exception as e:
            logger.debug(f"No cluster data found for {site_name}.{table_name} with filters {cluster_filters}: {e}")
            return False

    def _normalize_site_name(self, site_name: str) -> str:
        """Normalize site name using Dash033Config mappings"""
        return Dash033Config.SITE_NAME_MAPPINGS.get(site_name, site_name)
    
    def _get_coordinates_map(self) -> Dict[str, List[float]]:
        """Get coordinates mapping from ClickHouse using optimized connector"""
        try:
            coordinates_site = DatabaseConfig.COORDINATES_SITE
            coordinates_table = DatabaseConfig.COORDINATES_TABLE
            
            clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(
                coordinates_site, coordinates_table
            )
            if not clickhouse_table_name:
                logger.warning(f"No ClickHouse table found for coordinates: {coordinates_site}.{coordinates_table}")
                return {}

            # Use optimized connector with caching for coordinates data
            query = f"""
                SELECT `{DatabaseColumns.SITE_NAME}`, `{DatabaseColumns.LATITUDE}`, `{DatabaseColumns.LONGITUDE}`
                FROM `{clickhouse_table_name}`
                WHERE `{DatabaseColumns.SITE_NAME}` IS NOT NULL
                AND `{DatabaseColumns.LATITUDE}` IS NOT NULL 
                AND `{DatabaseColumns.LONGITUDE}` IS NOT NULL
            """
            
            logger.info(f"Fetching coordinates using optimized connector from {clickhouse_table_name}")
            result = execute_optimized_clickhouse_query(
                query,
                use_cache=True,
                cache_ttl=1800  # Cache coordinates for 30 minutes
            )
            coords_data = result.result_rows
            
            coordinates_map = {}
            if coords_data:
                for row in coords_data:
                    if len(row) >= 3:
                        site_name = str(row[0]) if row[0] else None
                        lat = float(row[1]) if row[1] is not None else 0.0
                        lon = float(row[2]) if row[2] is not None else 0.0
                        
                        if site_name:
                            # Normalize site name to handle variations like "Jubail - Jazlah" -> "Jubail-Jazlah"
                            normalized_site_name = self._normalize_site_name(site_name)
                            coordinates_map[normalized_site_name] = [lat, lon]
                            # Also keep original name as fallback
                            if normalized_site_name != site_name:
                                coordinates_map[site_name] = [lat, lon]

            logger.info(f"Loaded coordinates for {len(coordinates_map)} sites")
            return coordinates_map

        except Exception as e:
            logger.warning(f"Error getting coordinates map: {e}")
            return {}

    def _get_cluster_for_site(self, site_name: str) -> Optional[str]:
        """Get cluster name for a specific site"""
        try:
            for site, table_name in DatabaseConfig.PLANT_SITES.items():
                if site_name == site:  # match the given site
                    cluster = self._get_clusters_from_table(site, table_name)
                    if cluster:
                        return cluster

            return None

        except Exception as e:
            logger.debug(f"Error getting cluster for site {site_name}: {e}")
            return None


    def _calculate_sec(self, total_power_consumption: float, total_dispatched_flow: float) -> Optional[float]:
        """Calculate SEC - SAME AS ORIGINAL"""
        logger = logging.getLogger(__name__)

        try:
            if total_power_consumption < 0:
                logger.warning(f"Negative total power consumption: {total_power_consumption}")
                return None

            if total_dispatched_flow <= 0:
                logger.warning(f"Invalid total dispatched flow for SEC calculation: {total_dispatched_flow}")
                return None

            try:
                logger.debug(f"SEC calculation inputs - Power: {total_power_consumption}, Flow: {total_dispatched_flow}")

                # Updated formula: (total_power_consumption / 24) / total_dispatched_flow
                calculated_sec = ((total_power_consumption / 24) / total_dispatched_flow) * 1000

                logger.debug(f"SEC calculation steps - Power per hour: {total_power_consumption / 24}, Final SEC: {calculated_sec}")

                if not (0 <= calculated_sec <= float("inf")):
                    logger.error(f"SEC calculation resulted in invalid value: {calculated_sec}")
                    return None

                calculated_sec = round(calculated_sec, 2)
                logger.debug(f"SEC calculated: {calculated_sec}")
                return calculated_sec

            except (OverflowError, ZeroDivisionError) as e:
                logger.error(f"SEC calculation overflow/division error: {e}")
                return None

        except Exception as e:
            logger.error(f"Unexpected error in SEC calculation: {e}")
            return None

    def _evaluate_quality_status(self, quality_values: List) -> str:
        """EXACT OLD CODE LOGIC - reproducing the original bug and behavior"""
        logger = logging.getLogger(__name__)

        try:
            if not quality_values:
                logger.warning("No quality values available for evaluation")
                return QualityConfig.QUALITY_NOT_OK

            all_quality_ok = True
            for value in quality_values:
                if not value == QualityConfig.QUALITY_OK:
                    all_quality_ok = False
                    logger.debug(f"Quality value {value} is not acceptable")
                    break 

            result = (
                QualityConfig.QUALITY_OK
                if all_quality_ok
                else QualityConfig.QUALITY_NOT_OK
            )
            logger.info(
                LogMessages.OVERALL_QUALITY_STATUS.format(
                    result=result, count=len(quality_values)
                )
            )

            return result

        except Exception as e:
            logger.error(f"Error evaluating quality status: {e}")
            return QualityConfig.QUALITY_NOT_OK

    def _update_kpi_totals(
        self,
        kpi_data: List[Dict],
        total_dispatched_flow: float,
        total_power_consumption: float,
        calculated_sec: Optional[float],
        quality_total: str,
        total_production
    ) -> None:
        """Update KPI totals with rounding to 2 decimal places"""
        try:
            for row in kpi_data:
                kpi_name = row.get("kpi", "")

                if kpi_name == "Production":
                    row["total"] = f"{round(total_production, 2)} m3/h"
                elif kpi_name == "Power":
                    row["total"] = f"{round(total_power_consumption, 2)} kW"
                elif kpi_name == "Sec":
                    if calculated_sec is not None:
                        row["total"] = f"{round(calculated_sec, 2)} sec"
                    else:
                        row["total"] = "N/A"
                elif kpi_name == "Quality":
                    row["total"] = quality_total
                else:
                    row["total"] = ""

            logger.debug("Successfully updated KPI totals")

        except Exception as e:
            logger.error(f"Error updating KPI totals: {e}")

    # Context manager support for the service
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # No cleanup needed since repositories are created per operation
        pass

    #"-------------- Updated Requirements --------------"

    def get_clusters_for_role(self, role_id: Optional[str]) -> List[Dict]:
        """Get clusters assigned to a role (supports old format and new format with sites)."""
        if not role_id:
            logger.info(ErrorMessages.NO_ROLE_PROVIDED)
            return []
        
        try:
            role_repo = RoleRepository()
            role = role_repo.get_by_id(role_id)

            if not role:
                logger.warning(ErrorMessages.ROLE_NOT_FOUND.format(role_id=role_id))
                return []

            raw_clusters = Dash001Helper.normalize_role_clusters(role)

            
            if not raw_clusters:
                logger.info(ErrorMessages.NO_CLUSTERS_ASSIGNED.format(role_id=role_id))
                return []

            # --- Parse clusters into structured form ---
            parsed_clusters = Dash001Helper._parse_clusters(raw_clusters)

            # --- Get all available clusters ---
            all_clusters = self.get_all_clusters()


            # --- Filter and enrich clusters ---
            logger.debug(f"[Clusters] Retrieved {len(all_clusters)} total clusters from database.")

            # --- Filter clusters assigned to the role ---
            filtered_clusters = Dash001Helper._filter_clusters(all_clusters, parsed_clusters)
            return filtered_clusters

        except Exception as e:
            logger.error(
                ErrorMessages.ERROR_GETTING_CLUSTERS.format(
                    role_id=role_id, error=str(e)
                )
            )
            return []
        

    def get_all_clusters_with_sites(self) -> List[Dict]:
        """Get all clusters from all sites using ClickHouse"""
        try:
            plant_sites = DatabaseConfig.PLANT_SITES
            all_clusters = []
            seen_clusters = set()

            for site_name, table_name in plant_sites.items():
                try:
                    logger.info(f"Processing site: {site_name}, table: {table_name}")
                    
                    cluster_name = self._get_clusters_from_table(site_name, table_name)
                    
                    if not cluster_name :
                        continue 

                    if cluster_name not in seen_clusters:
                            seen_clusters.add(cluster_name)
                            
                            clean_cluster_name = (
                                cluster_name.split(": ")[1]
                                if ": " in cluster_name
                                else cluster_name
                            )

                            sites = []
                            if clean_cluster_name== "KSA":
                                sites = ["Jubail-Jazlah" , "Rabigh3" , "STPC"]
                            
                            if clean_cluster_name == "MEASEA":
                                sites = ["UAQ"]
                            
                            cluster_info = {
                                "id": cluster_name,
                                "name": clean_cluster_name,
                                "plant": Dash001Helper._get_plant_name_for_site(site_name),
                                "group": PlantConfig.ENERGY_GROUP,
                                "sites": sites,
                            }
                            all_clusters.append(cluster_info)
                            logger.info(f"Added cluster: {cluster_name} from site: {site_name}")
                        

                except Exception as e:
                    logger.warning(f"Error processing clusters for site {site_name}: {e}")
                    continue

            logger.info(f"Retrieved {len(all_clusters)} unique clusters")
            return all_clusters

        except Exception as e:
            logger.error(f"Error getting all clusters: {e}")
            return []
    

    def _get_clusters_from_table(self, site_name: str, table_name: str) -> List[str]:
        """
        Retrieve the cluster name from a ClickHouse table by fetching only the first row.
        Returns an empty list if the table or column doesn't exist.
        """
        try:
            clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(site_name, table_name)
            if not clickhouse_table_name:
                logger.warning(f"[ClickHouse] No table found for {site_name}.{table_name}")
                return []

            try:
                # Fetch only one row to avoid scanning entire table
                cluster_data = self.clickhouse_repository.get_column_data_for_table_opt(
                    table_name=clickhouse_table_name,
                    column_names=[DatabaseColumns.CLUSTER_NAME],
                    limit=1
                )
            except Exception as err:
                error_msg = str(err)
                if "UNKNOWN_IDENTIFIER" in error_msg or "Unknown expression identifier" in error_msg:
                    logger.warning(
                        f"[ClickHouse] Missing column `{DatabaseColumns.CLUSTER_NAME}` in `{clickhouse_table_name}`"
                    )
                    return []
                logger.exception(
                    f"[ClickHouse] Error retrieving cluster data for {site_name}.{table_name}: {err}"
                )
                return []

            if not cluster_data or not cluster_data[0] or not cluster_data[0][0]:
                logger.info(f"[ClickHouse] No cluster data found in {site_name}.{table_name}")
                return []

            cluster_value = str(cluster_data[0][0]).strip()
            logger.info(f"[ClickHouse] Cluster for {site_name}.{table_name}: {cluster_value}")

            return cluster_value

        except Exception as e:
            logger.exception(f"[ClickHouse] Unexpected error while getting clusters from {site_name}.{table_name}: {e}")
            return []

    # Service Layer - dash_001.py modifications only
    # No repository changes needed - uses existing get_column_data_for_table method

    def get_daily_dispatch_graph_data(self, role_id: Optional[str], cluster_filter: Optional[str] = None,
                                      site_filter: Optional[str] = None) -> List[Dict]:
        """
        Get daily dispatch data for the last 72 hours from the latest available date in data.
        Returns all records within the 72-hour window (not just latest per day).
        Datetime values are formatted without timezone offsets.

        Args:
            role_id: User's role ID for filtering
            cluster_filter: Optional cluster name to filter by
            site_filter: Optional site name to filter by

        Returns:
            List of dictionaries containing columnName, columnType, tableName, siteName, and dataSource
            Only returns Date and Daily Dispatch columns.
        """

        if not role_id:
            logger.info(ErrorMessages.NO_ROLE_PROVIDED)
            return []

        try:
            # Get role and assigned clusters
            role_repo = RoleRepository()
            role = role_repo.get_by_id(role_id)

            if not role:
                logger.warning(ErrorMessages.ROLE_NOT_FOUND.format(role_id=role_id))
                return []

            raw_clusters = Dash001Helper.normalize_role_clusters(role)
            logger.info(f"Assigned Clusters: {raw_clusters}")

            if not raw_clusters:
                logger.info(ErrorMessages.NO_CLUSTERS_ASSIGNED.format(role_id=role_id))
                return []

            # Parse clusters into structured form
            clusters_with_plants = Dash001Helper._get_clusters_for_plants(raw_clusters)

            # Determine which clusters to process
            if cluster_filter:
                clean_cluster_name = cluster_filter.split(": ", 1)[1] if ": " in cluster_filter else cluster_filter

                if clean_cluster_name not in clusters_with_plants:
                    logger.info(f"Cluster {clean_cluster_name} not found in user's assigned clusters")
                    return []

                clusters_to_process = [clean_cluster_name]
            else:
                clusters_to_process = list(clusters_with_plants.keys())

            logger.info(f"Processing daily dispatch data for clusters: {clusters_to_process}")

            # Collect all graph data in row format first
            all_row_data = []
            plant_sites = DatabaseConfig.PLANT_SITES

            # Process each cluster
            for cluster_name in clusters_to_process:
                cluster_filter_data = clusters_with_plants.get(cluster_name, [])
                cluster_filter_str = f"Cluster: {cluster_name}" if ": " not in cluster_name else cluster_name

                logger.info(f"Processing cluster {cluster_name}: sites from role assignment = {cluster_filter_data}")

                # Process each site in the cluster
                for site_name, table_name in plant_sites.items():
                    # Check if site is assigned to this cluster
                    if site_name not in cluster_filter_data:
                        logger.debug(f"Skipping site {site_name} - not in role assignment for cluster {cluster_name}")
                        continue

                    # If site_filter is provided, skip sites that don't match
                    if site_filter and site_name != site_filter:
                        logger.debug(f"Skipping site {site_name} - doesn't match site_filter {site_filter}")
                        continue

                    try:
                        # Check if site has data for this cluster
                        has_cluster_data = self._get_cluster_data_for_table(
                            site_name, table_name, [cluster_filter_str]
                        )

                        if not has_cluster_data:
                            logger.info(f"No cluster data for site {site_name} in cluster {cluster_name}")
                            continue

                        plant_name = Dash001Helper._get_plant_name_for_site(site_name)

                        # Get site-specific latest date
                        site_latest_date = self._get_latest_date_for_site(
                            site_name=site_name,
                            table_name=table_name,
                            cluster_filter=cluster_filter_str
                        )

                        if not site_latest_date:
                            logger.warning(
                                f"No latest date found for site {site_name} in cluster {cluster_filter_str} - skipping.")
                            continue

                        logger.info(f"Latest date for site {site_name}: {site_latest_date}")

                        # Calculate 72 hours back from site-specific latest date
                        site_latest_date_obj = datetime.strptime(site_latest_date, '%Y-%m-%d').date()
                        start_date = (site_latest_date_obj - timedelta(days=2)).strftime('%Y-%m-%d')
                        end_date = site_latest_date_obj.strftime('%Y-%m-%d')

                        logger.info(
                            f"Fetching ALL records for last 72 hours for {site_name}: {start_date} to {end_date}")


                        # Fetch ALL records for the 72-hour window (not just latest per day)
                        records_72hr = self._get_daily_dispatch_for_date_range(
                            site_name=site_name,
                            table_name=table_name,
                            cluster_filter=cluster_filter_str,
                            start_date=start_date,
                            end_date=end_date,
                            dispatch_column=DatabaseColumns.PLANT_DAILY_DISPATCHED
                        )

                        if records_72hr:
                            for record in records_72hr:
                                # Format datetime value without timezone offset
                                datetime_value = record.get("datetime")
                                formatted_datetime = self._format_datetime_value(datetime_value)

                                if formatted_datetime:
                                    dispatch_value = record.get('daily_dispatch')

                                    all_row_data.append({
                                        "date": formatted_datetime,
                                        "plant_name": plant_name,
                                        "site_name": site_name,
                                        "table_name": table_name,
                                        "daily_dispatch": dispatch_value,
                                    })

                            logger.info(f"Retrieved {len(records_72hr)} records for {site_name} in 72-hour window")
                        else:
                            logger.debug(f"No data found for {plant_name} ({site_name}) in 72-hour window")

                    except Exception as e:
                        logger.warning(f"Error processing site {site_name} for cluster {cluster_name}: {e}")
                        continue

            # Sort by date and site for consistent ordering
            all_row_data.sort(key=lambda x: (x["site_name"], x["date"]))

            # Transform row-based data to column-based format (only Date and Daily Dispatch)
            column_based_data = self._transform_to_column_format(all_row_data)

            filter_description = ""
            if site_filter and cluster_filter:
                filter_description = f" for site {site_filter} in cluster {cluster_filter}"
            elif cluster_filter:
                filter_description = f" for cluster {cluster_filter}"

            logger.info(
                f"Transformed {len(all_row_data)} row records into {len(column_based_data)} column records " +
                f"for 72-hour window{filter_description}"
            )
            return column_based_data

        except Exception as e:
            logger.error(f"Error getting daily dispatch graph data: {e}", exc_info=True)
            return []

    def _get_daily_dispatch_for_date_range(
            self,
            site_name: str,
            table_name: str,
            cluster_filter: str,
            start_date: str,
            end_date: str,
            dispatch_column: str
    ) -> List[Dict]:
        """
        Get ALL daily dispatch records for a date range (72 hours).
        Uses existing ClickHouse repository method.

        Args:
            site_name: Site identifier
            table_name: Table name
            cluster_filter: Cluster filter string
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            dispatch_column: Column name for daily dispatch data

        Returns:
            List of dictionaries with daily dispatch data including table_name, datetime, and dispatch value
        """


        try:
            # Get ClickHouse table name using repository method
            clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(site_name, table_name)
            if not clickhouse_table_name:
                logger.debug(f"No ClickHouse table found for {site_name}.{table_name}")
                return []

            # Get datetime column using repository method
            datetime_column = self.clickhouse_repository.get_datetime_column(clickhouse_table_name)
            if not datetime_column:
                logger.warning(f"No datetime column found for {clickhouse_table_name}")
                return []

            # Build WHERE conditions for date range filtering
            where_conditions = [
                f"`{DatabaseColumns.CLUSTER_NAME}` = {{cluster:String}}",
                f"`{datetime_column}` >= {{start_date:DateTime}}",
                f"`{datetime_column}` <= {{end_date:DateTime}}"
            ]

            # Prepare query parameters with full datetime strings (00:00:00 and 23:59:59)
            query_params = {
                "cluster": cluster_filter,
                "start_date": f"{start_date} 00:00:00",
                "end_date": f"{end_date} 23:59:59"
            }

            # Use existing get_column_data_for_table method to fetch all records
            result = self.clickhouse_repository.get_column_data_for_table(
                clickhouse_table_name=clickhouse_table_name,
                column_names=[datetime_column, dispatch_column],
                datetime_column=datetime_column,
                where_conditions=where_conditions,
                query_params=query_params,
                enable_fallback=False  # Disable fallback for this specific query
            )

            # Extract result rows
            result_rows = result.get("result_rows", [])


            if not result_rows:
                logger.warning(f"✗ No data found for {site_name} from {start_date} to {end_date}")
                return []

            # Process all records and convert to expected format
            # IMPORTANT: Store both with the generic key "datetime" for transformation
            records = []
            for row in result_rows:
                result_datetime = row[1] if len(row) > 0 else None
                dispatch_value = row[2] if len(row) > 1 else None

                # Use standardized keys for transformation
                result_dict = {
                    "table_name": table_name,
                    "datetime": result_datetime,  # Standardized key
                    "daily_dispatch": dispatch_value  # Standardized key
                }
                records.append(result_dict)

            logger.info(f"✓ Retrieved {len(records)} records for {site_name} from {start_date} to {end_date}")
            return records

        except Exception as e:
            logger.error(f"Error getting daily dispatch for {site_name} date range {start_date} to {end_date}: {e}",
                         exc_info=True)
            return []

    def _format_datetime_value(self, value) -> Optional[str]:
        """
        Format a datetime value without timezone offset.
        Handles both datetime objects and datetime strings.

        Args:
            value: datetime object or string

        Returns:
            Formatted datetime string in YYYY-MM-DDTHH:MM:SS format or None
        """
        if value is None:
            return None

        # If it's already a datetime object
        if isinstance(value, datetime):
            return DateTimeParser.format_datetime_without_timezone(value)

        # If it's a string, parse it first then format
        if isinstance(value, str):
            parsed_dt = DateTimeParser.parse_datetime(value)
            if parsed_dt:
                return DateTimeParser.format_datetime_without_timezone(parsed_dt)
            # If parsing fails, return the original string
            return value

        return None

    def _get_overall_latest_date(
            self,
            clusters_to_process: List[str],
            clusters_with_plants: Dict
    ) -> Optional[str]:
        """
        Get the most recent date across all relevant sites using DESC order (limit 1).
        Delegates to repository method for query execution.

        Args:
            clusters_to_process: List of cluster names to process
            clusters_with_plants: Dictionary mapping cluster names to their assigned sites

        Returns:
            Most recent date in YYYY-MM-DD format, or None if no data found
        """
        try:
            plant_sites = DatabaseConfig.PLANT_SITES
            
            # Delegate to repository method
            return self.dash_001_repository.get_overall_latest_date(
                clusters_to_process=clusters_to_process,
                clusters_with_plants=clusters_with_plants,
                plant_sites=plant_sites,
                check_cluster_data_func=self._get_cluster_data_for_table
            )

        except Exception as e:
            logger.error(f"Error finding overall latest date: {e}", exc_info=True)
            return None

    def _get_latest_date_for_site(
            self,
            site_name: str,
            table_name: str,
            cluster_filter: str
    ) -> Optional[str]:
        """
        Get the latest available date for a specific site.

        Args:
            site_name: Site identifier
            table_name: Table name
            cluster_filter: Cluster filter string

        Returns:
            Latest available date in YYYY-MM-DD format, or None if no data found
        """
        try:
            # Get ClickHouse table name using repository method
            clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(site_name, table_name)
            if not clickhouse_table_name:
                logger.debug(f"No ClickHouse table found for {site_name}.{table_name}")
                return None

            # Get datetime column using repository method
            datetime_column = self.clickhouse_repository.get_datetime_column(clickhouse_table_name)
            if not datetime_column:
                logger.warning(f"No datetime column found for {clickhouse_table_name}")
                return None

            # Use repository method to get the latest date for this specific site
            # This method uses Asia/Dubai timezone conversion, ensuring correct dates for late-night times
            last_date = self.dash_001_repository.get_latest_date_for_site(
                site_name=site_name,
                table_name=table_name,
                cluster_filter=cluster_filter,
                clickhouse_table_name=clickhouse_table_name,
                datetime_column=datetime_column
            )

            if last_date:
                logger.debug(f"Latest date for site {site_name} (Asia/Dubai): {last_date}")
                return last_date

            logger.warning(f"No data found for site {site_name} in cluster {cluster_filter}")
            return None

        except Exception as e:
            logger.error(f"Error getting latest date for site {site_name}: {e}", exc_info=True)
            return None

    def _transform_to_column_format(self, row_data: List[Dict]) -> List[Dict]:
        """
        Transform row-based data to column-based format with unified datetime column.

        UPDATED: Creates a single DateTime column at index 0 with all unique dates,
        and for each plant's daily dispatch column, fills null for missing dates.
        All datetime values are formatted without timezone offsets.

        Args:
            row_data: List of row-based data dictionaries

        Returns:
            List of column-based data dictionaries with:
            - Index 0: Single DateTime column with all unique dates (formatted without timezone)
            - Index 1+: Daily Dispatch columns for each plant (with nulls for missing dates)
        """
        if not row_data:
            return []


        # Step 1: Collect all unique dates across all plants and sort them
        all_dates_set = set()
        for row in row_data:
            date_value = row.get("date")
            if date_value:
                # Format the date value to ensure consistency
                formatted_date = self._format_datetime_value(date_value)
                if formatted_date:
                    all_dates_set.add(formatted_date)

        # Sort dates chronologically
        all_dates_sorted = sorted(list(all_dates_set))

        logger.info(f"Found {len(all_dates_sorted)} unique dates across all plants: {all_dates_sorted}")

        # Step 2: Create the unified DateTime column (index 0)
        datetime_column = {
            "columnName": "DateTime",
            "columnType": "timestamp[ns]",
            "tableName": "unified",  # Indicates this is a unified column
            "siteName": "all",  # Indicates this spans all sites
            "dataSource": all_dates_sorted
        }

        column_based_data = [datetime_column]  # DateTime column at index 0

        # Step 3: Group data by plant (table_name + site_name)
        sorted_data = sorted(row_data, key=lambda x: (x.get("table_name", ""), x.get("site_name", "")))

        # Step 4: Process each plant
        for (table_name, site_name), plant_rows in groupby(
                sorted_data,
                key=lambda x: (x.get("table_name", ""), x.get("site_name", ""))
        ):
            plant_rows_list = list(plant_rows)

            logger.info(f"Processing {len(plant_rows_list)} rows for plant {site_name} (table: {table_name})")

            # Create a mapping of date -> daily_dispatch value for this plant
            date_to_dispatch = {}
            for row in plant_rows_list:
                date_value = row.get("date")
                dispatch_value = row.get("daily_dispatch")

                # Format the date value for consistent mapping
                formatted_date = self._format_datetime_value(date_value)
                if formatted_date:
                    date_to_dispatch[formatted_date] = dispatch_value

            # Step 5: Create daily dispatch column for this plant
            # Fill with actual values or null for missing dates
            data_source = []
            for date in all_dates_sorted:
                if date in date_to_dispatch:
                    data_source.append(date_to_dispatch[date])
                else:
                    data_source.append(None)  # null for missing dates
                    logger.debug(f"Missing data for {site_name} on {date}, filling with null")

            # Create column entry for this plant's daily dispatch
            plant_name = Dash001Helper._get_plant_name_for_site(site_name)
            column_entry = {
                "columnName": f"{plant_name}_Daily_Dispatch",  # Unique name per plant
                "columnType": "double",
                "tableName": table_name,
                "siteName": site_name,
                "dataSource": data_source
            }

            column_based_data.append(column_entry)

        logger.info(
            f"Transformed to column format with unified DateTime column and {len(column_based_data) - 1} plant columns"
        )
        return column_based_data

    def _get_latest_available_date(self, clusters_to_process: List[str], clusters_with_plants: Dict) -> Optional[str]:
        """
        Find the latest available date across all relevant data for the given clusters.

        Args:
            clusters_to_process: List of cluster names to process
            clusters_with_plants: Dictionary mapping clusters to their plants

        Returns:
            Latest available date in YYYY-MM-DD format, or None if no data found
        """
        try:

            latest_dates = []
            plant_sites = DatabaseConfig.PLANT_SITES

            for cluster_name in clusters_to_process:
                cluster_filter_data = clusters_with_plants.get(cluster_name, [])
                cluster_filter_str = f"Cluster: {cluster_name}" if ": " not in cluster_name else cluster_name

                for site_name, table_name in plant_sites.items():
                    if site_name not in cluster_filter_data:
                        continue

                    try:
                        # Check if site has data for this cluster
                        has_cluster_data = self._get_cluster_data_for_table(
                            site_name, table_name, [cluster_filter_str]
                        )

                        if not has_cluster_data:
                            continue

                        # Get ClickHouse table name using repository method
                        clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(site_name,
                                                                                                     table_name)
                        if not clickhouse_table_name:
                            continue

                        # Get datetime column using repository method
                        datetime_column = self.clickhouse_repository.get_datetime_column(clickhouse_table_name)
                        if not datetime_column:
                            continue

                        # Use repository method to get the last available date
                        last_date = self.clickhouse_repository._get_last_available_date(
                            clickhouse_table_name=clickhouse_table_name,
                            datetime_column=datetime_column,
                            where_conditions=[f"`{DatabaseColumns.CLUSTER_NAME}` = {{cluster:String}}"],
                            query_params={"cluster": cluster_filter_str}
                        )

                        if last_date:
                            latest_dates.append(last_date)
                            logger.debug(f"Latest date for {site_name}.{cluster_name}: {last_date}")

                    except Exception as e:
                        logger.warning(f"Error getting latest date for {site_name}.{cluster_name}: {e}")
                        continue
            if not latest_dates:
                return None

            # Find the overall latest date
            overall_latest = max(latest_dates)
            logger.info(f"Overall latest date across all data: {overall_latest}")
            return overall_latest

        except Exception as e:
            logger.error(f"Error finding latest available date: {e}", exc_info=True)
            return None

    def _get_daily_dispatch_for_date(
            self,
            site_name: str,
            table_name: str,
            cluster_filter: str,
            target_date: str
    ) -> Optional[Dict]:
        """
        Get the latest daily dispatch record for a specific date using repository methods.
        Uses PLANT_DAILY_DISPATCHED for Rabigh3, PLANT_DAILY_DISPATCHED_OLD for all other sites.

        Args:
            site_name: Site identifier
            table_name: Table name
            cluster_filter: Cluster filter string
            target_date: Target date in YYYY-MM-DD format

        Returns:
            Dictionary with daily dispatch data including table_name or None if no data found
        """
        try:

            # Get ClickHouse table name using repository method
            clickhouse_table_name = self.clickhouse_repository.get_clickhouse_table_name(site_name, table_name)
            if not clickhouse_table_name:
                logger.debug(f"No ClickHouse table found for {site_name}.{table_name}")
                return None

            # Get datetime column using repository method
            datetime_column = self.clickhouse_repository.get_datetime_column(clickhouse_table_name)
            if not datetime_column:
                logger.warning(f"No datetime column found for {clickhouse_table_name}")
                return None


            # Delegate to repository method
            return self.dash_001_repository.get_daily_dispatch_for_date(
                site_name=site_name,
                table_name=table_name,
                cluster_filter=cluster_filter,
                target_date=target_date,
                datetime_column=datetime_column,
                clickhouse_table_name=clickhouse_table_name,
                daily_dispatch_column=DatabaseColumns.PLANT_DAILY_DISPATCHED
            )

        except Exception as e:
            logger.error(f"Error getting daily dispatch for {site_name} on {target_date}: {e}", exc_info=True)
            return None