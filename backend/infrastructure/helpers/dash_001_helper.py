import copy
import re
import logging
import json
import statistics
from typing import Any, Dict, List, Optional, Tuple
from constants import (DatabaseColumns, ErrorMessages, KPIConfig, LogMessages,
                       PlantConfig, QualityConfig, DatabaseConfig)

logger = logging.getLogger(__name__)

class Dash001Helper:
    """Helper utilities for normalizing and parsing cluster data."""

    @staticmethod
    def normalize_role_clusters(role: dict) -> list:
        """
        Safely normalize the `clusters`  from a role record.
        Ensures the result is always a list of clusters (or empty list on error).
        """
        raw_clusters = role.get("clusters", [])

        # Case 1: Missing or empty field
        if isinstance(raw_clusters, str):
            try:
                raw_clusters = json.loads(raw_clusters)
            except Exception:
                logger.warning(f"Could not parse clusters string: {raw_clusters}")
                raw_clusters = []

        if not isinstance(raw_clusters, list):
            try:
                raw_clusters = list(raw_clusters)
            except Exception:
                raw_clusters = []

        logger.info(f"normalize clusetrs {raw_clusters}")

        return raw_clusters
    

    @staticmethod
    def _filter_clusters(
        all_clusters: List[Dict], parsed_clusters: List[Dict]
    ) -> List[Dict]:
        """Filter clusters assigned to the role based on parsed cluster list."""
        assigned_map = {c["name"].lower(): c for c in parsed_clusters}
        filtered_clusters = []

        for cluster in all_clusters:
            assigned = assigned_map.get(cluster["name"].lower())
            if assigned:
                cluster_copy = cluster.copy()
                if assigned["sites"]:
                    cluster_copy["sites"] = assigned["sites"]
                filtered_clusters.append(cluster_copy)

        logger.info(
            f"{len(filtered_clusters)} of {len(all_clusters)} clusters matched assignment."
        )
        return filtered_clusters
    

    @staticmethod
    def _parse_clusters(cluster_list: List[str]) -> List[Dict]:
        """
        Parse clusters from format: {ClusterName, [Site1, Site2, ...]}.
        Example: "{KSA, [Rabigh3, Jubail-Jazlah]}"
        to this format [{name : KSA , sites:  [Rabigh3, Jubail-Jazlah]}]
        """
        parsed = []
        for c in cluster_list:
            if not isinstance(c, str):
                logger.debug(f"Skipping non-string cluster: {c}")
                continue

            c = c.strip()

            match = re.match(r"\{([^,]+),\s*\[(.*)\]\}", c)
            if match:
                cluster_name = match.group(1).strip()
                sites_str = match.group(2).strip()
                sites = [s.strip() for s in sites_str.split(",") if s.strip()]
                parsed.append({"name": cluster_name, "sites": sites})
            else:
                logger.debug(f"[Clusters] Failed to parse new format cluster: {c}")

        return parsed
    

    @staticmethod
    def _get_clusters_for_plants(cluster_list: List[str]) -> List[Dict]:
        """
        Parse clusters from format: {ClusterName, [Site1, Site2, ...]}.
        Example: "{KSA, [Rabigh3, Jubail-Jazlah]}"
        to this format {KSA: [Rabigh3, Jubail-Jazlah]}
        """
        clusters_with_plants = {}
        for c in cluster_list:
            if not isinstance(c, str):
                logger.debug(f"Skipping non-string cluster: {c}")
                continue

            c = c.strip()
            
            match = re.match(r"\{([^,]+),\s*\[(.*)\]\}", c)
            if match:
                cluster_name = match.group(1).strip()
                sites_str = match.group(2).strip()
                sites = [s.strip() for s in sites_str.split(",") if s.strip()]
                clusters_with_plants[cluster_name] = sites
                # parsed.append({"name": cluster_name, "sites": sites})
            else:
                logger.debug(f"[Clusters] Failed to parse new format cluster: {c}")

        return clusters_with_plants
    

    @staticmethod
    def _get_empty_kpi_data() -> List[Dict]:
        """Return empty KPI data structure without plant columns"""
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
        return [{**row, "total": "0"} for row in kpi_template]
    
   
    @staticmethod
    def _get_empty_kpi_data_with_plants() -> List[Dict]:
        """Return empty KPI data structure with plant columns"""
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
        
        # Add plant columns
        plant_names = list(PlantConfig.SITE_TO_PLANT_MAPPINGS.values())
        kpi_data = []
        for row in kpi_template:
            kpi_row = {**row}
            for plant_name in plant_names:
                kpi_row[plant_name] = "N/A"
            kpi_row["total"] = "0"
            kpi_data.append(kpi_row)
        
        return kpi_data


    @staticmethod
    def _get_plant_name_for_site(site_name: str) -> str:
        """Map site name to plant name using constants"""
        if site_name in PlantConfig.SITE_TO_PLANT_MAPPINGS:
            return PlantConfig.SITE_TO_PLANT_MAPPINGS[site_name]
        
        return f"{site_name} Energy Plant"
    
    @staticmethod
    def _get_plant_type_for_site(site_name: str) -> str:
        """Get plant type for a site"""
        return Dash001Helper._get_plant_name_for_site(site_name)
    

    @staticmethod
    def get_groups() -> List[str]:
        """Get all available groups"""
        return PlantConfig.PLANT_GROUPS
    
    @staticmethod
    def _get_site_name_from_table(table_name: str) -> Optional[str]:
        """Get site name from table name using the mapping"""
        for site_name, mapped_table in DatabaseConfig.PLANT_SITES.items():
            if mapped_table == table_name:
                return site_name
        return None