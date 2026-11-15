import logging
import re
from typing import Dict, Any, Optional, List

from config.databricks_connector import get_databricks_connector

logger = logging.getLogger(__name__)


class ChemicalRepository:
    """Repository for handling plant-related database queries with safe parameterized queries"""

    def __init__(self):
        """Initialize repository with database connection"""
        self.databricks_connector = get_databricks_connector()
        self.cursor = self.databricks_connector.cursor()

        # --- Set Unity Catalog context (catalog + schema) ---
        self._use_uc_context(catalog="swro_mpc", schema="mpc_swro_be_analysis")

    def _use_uc_context(self, catalog: str, schema: str) -> None:
        """Set current catalog and schema for this session/cursor."""
        # Validate catalog and schema names to prevent SQL injection
        # Only allow alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', catalog):
            raise ValueError(f"Invalid catalog name: {catalog}. Only alphanumeric characters and underscores are allowed.")
        if not re.match(r'^[a-zA-Z0-9_]+$', schema):
            raise ValueError(f"Invalid schema name: {schema}. Only alphanumeric characters and underscores are allowed.")

        # Note: These are control statements; they can't be parameterized.
        self.cursor.execute(f"USE CATALOG {catalog}")
        self.cursor.execute(f"USE SCHEMA {schema}")

        # Verify and log context
        self.cursor.execute("SELECT current_catalog(), current_schema()")
        context = self.cursor.fetchone()
        logger.debug(f"UC context: {context}")

    def close(self):
        """Close the database connection"""
        if self.cursor:
            self.cursor.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup"""
        self.close()

    def get_areas_list(self, where_params: Dict[str, Any] = None):
        """
        Get areas list, optionally filtered by site.

        Args:
            where_params: Optional dict with filters. Supports:
                - 'site': Filter by site name (joins with sites table via area_chemicals)

        Returns:
            List of area rows with 'name' field
        """
        # Check if filtering by site - requires JOIN through area_chemicals bridge table
        site_filter = where_params.get("site") if where_params else None

        if site_filter:
            # Join areas -> area_chemicals -> sites to filter by site name
            query = """
                SELECT DISTINCT a.name
                FROM areas a
                JOIN area_chemicals ac ON a.id = ac.area_id
                JOIN sites s ON s.id = ac.site_id
                WHERE s.name = ?
                ORDER BY a.name
            """
            self.cursor.execute(query, [site_filter])
        else:
            # No site filter - return all areas
            query = """
                SELECT DISTINCT name
                FROM areas
                ORDER BY name
            """
            self.cursor.execute(query)

        result = self.cursor.fetchall()
        return result

    def get_chemical_list(
            self,
            site_name: Optional[str] = None,
            area_name: Optional[str] = None,
            where_params: Dict[str, Any] = None,
            select_all: bool = False,
            limit: Optional[int] = None,
    ):
        """
        Get chemicals for a specific site+area from Unity Catalog tables.

        Args:
            site_name: Site name filter (e.g., 'Rabigh3')
            area_name: Area name filter (e.g., 'RO')
            where_params: Additional column=value filters. Use qualified cols if needed (e.g., 's.id', 'c.type').
            select_all: If True, runs SELECT * (matches your example). Otherwise selects the chemical name.
            limit: Optional LIMIT N (integer)

        Returns:
            List of rows (driver typically returns dict-like rows if configured).
        """

        # Choose the SELECT list


        select_clause = "*" if select_all else "c.name AS chemical"

        # Fully qualified UC tables + area_chemicals bridge
        base_query = f"""
            SELECT {select_clause}
            FROM chemicals c
            JOIN area_chemicals ac ON ac.chemical_id = c.id
            JOIN areas a ON a.id = ac.area_id
            JOIN sites s ON s.id = ac.site_id
        """

        where_conditions = []
        params: List[Any] = []

        # Named filters
        if site_name:
            where_conditions.append("s.name = ?")
            params.append(site_name)

        if area_name:
            where_conditions.append("a.name = ?")
            params.append(area_name)

        if where_params:
            for column, value in where_params.items():
                where_conditions.append(f"{column} = ?")
                params.append(value)

        # Final assembly
        if where_conditions:
            query = f"{base_query} WHERE {' AND '.join(where_conditions)}"
        else:
            query = base_query

        # Keep a predictable order when not selecting all
        if not select_all:
            query += " ORDER BY c.name"

        # Optional LIMIT (safe int cast)
        if limit is not None:
            query += f" LIMIT {int(limit)}"

        # Execute
        self.cursor.execute(query, params if params else None)
        return self.cursor.fetchall()



