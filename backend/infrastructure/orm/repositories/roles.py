"""
Repository module for handling roles database operations with Databricks SQL Warehouse.
"""

import json
import logging
import re
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from config.databricks_connector import get_databricks_connector
from config.databricks_sql_queries import \
    UPDATE_ROLE_FULL  # optional fixed-shape
from config.databricks_sql_queries import (DB_PREFIX, DELETE_ROLE,
                                           GET_ALL_ROLES, GET_ROLE_BY_ID,
                                           GET_ROLE_BY_NAME,
                                           GET_ROLES_BY_ACTIVE_STATUS,
                                           GET_ROLES_BY_CLUSTER,
                                           GET_ROLES_BY_TYPE, GET_ROLES_COUNT,
                                           GET_ROLES_WITH_SEARCH, INSERT_ROLE)

logger = logging.getLogger(__name__)


class RoleRepository:
    """
    Repository class for handling all database operations related to roles.
    Uses Databricks SQL Warehouse for data storage and retrieval.
    """

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections with proper resource management.
        Ensures connections are properly closed even if exceptions occur.

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

    def get_roles_with_filters(
        self,
        search: Optional[str] = None,
        role_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        cluster: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve roles with optional filters and pagination.

        Args:
            search: Search term for name/description
            role_type: Filter by role type
            is_active: Filter by active status
            cluster: Filter by cluster association
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of role dictionaries matching the filters

        Raises:
            Exception: If database query fails
        """
        try:
            with self._get_connection() as cursor:
                # Build dynamic query based on filters
                query, params = self._build_roles_query(
                    search=search,
                    role_type=role_type,
                    is_active=is_active,
                    cluster=cluster,
                    offset=offset,
                    limit=limit,
                )

                logger.debug(f"Executing query: {query} with params: {params}")
                cursor.execute(query, params)
                rows = cursor.fetchall()

                logger.info(f"Retrieved {len(rows)} roles from database")

                # Define column names based on the roles table schema
                columns = [
                    "id",
                    "name",
                    "type",
                    "description",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "clusters",
                ]

                # Convert rows to list of dictionaries
                if rows:
                    # Check if rows are already dictionaries
                    if isinstance(rows[0], dict):
                        return rows
                    else:
                        # Create dictionaries with column names
                        data = []
                        for row in rows:
                            data.append(dict(zip(columns, row)))
                        return data
                else:
                    return []

        except Exception as e:
            logger.error(f"Error fetching roles with filters: {str(e)}", exc_info=True)
            raise Exception(f"Failed to fetch roles from database: {str(e)}")

    def get_roles_count(
        self,
        search: Optional[str] = None,
        role_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        cluster: Optional[str] = None,
    ) -> int:
        """
        Get the total count of roles matching the filters.

        Args:
            search: Search term for name/description
            role_type: Filter by role type
            is_active: Filter by active status
            cluster: Filter by cluster association

        Returns:
            Total count of matching roles

        Raises:
            Exception: If database query fails
        """
        try:
            with self._get_connection() as cursor:
                # Build count query based on filters
                query, params = self._build_count_query(
                    search=search,
                    role_type=role_type,
                    is_active=is_active,
                    cluster=cluster,
                )

                logger.debug(f"Executing count query: {query} with params: {params}")
                cursor.execute(query, params)
                result = cursor.fetchone()

                # Extract count from result
                if result:
                    count = (
                        result[0]
                        if isinstance(result, (list, tuple))
                        else result.get("count", 0)
                    )
                else:
                    count = 0

                logger.info(f"Total roles count with filters: {count}")
                return count

        except Exception as e:
            logger.error(f"Error getting roles count: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get roles count: {str(e)}")

    def _build_roles_query(
        self,
        search: Optional[str] = None,
        role_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        cluster: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple:
        """
        Build dynamic SQL query based on provided filters using safe parameterization.

        Args:
            search: Search term for name/description
            role_type: Filter by role type
            is_active: Filter by active status
            cluster: Filter by cluster association
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (query_string, parameters_list)
        """
        # Use centralized filter condition builder
        conditions, params = self._build_filter_conditions(
            search=search, role_type=role_type, is_active=is_active, cluster=cluster
        )

        # Build the complete query safely
        base_select = f"""
            SELECT id, name, type, description, is_active, created_at, updated_at, clusters
            FROM {DB_PREFIX}.roles
        """

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""

        query = base_select + where_clause + " ORDER BY name ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return query, params

    def _sanitize_search_input(self, search: str) -> Optional[str]:
        """
        Sanitize search input to prevent SQL injection.

        Args:
            search: Raw search input

        Returns:
            Sanitized search string or None if invalid
        """
        if not search or not search.strip():
            return None

        # Remove dangerous characters and patterns
        dangerous_patterns = [
            "--",
            "/*",
            "*/",
            "xp_",
            "sp_",
            ";",
            "union",
            "select",
            "insert",
            "update",
            "delete",
            "drop",
            "create",
            "alter",
            "exec",
            "execute",
        ]

        sanitized = search.strip()

        # Remove dangerous SQL keywords (case insensitive)
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern.lower(), "")
            sanitized = sanitized.replace(pattern.upper(), "")

        # Keep only alphanumeric, space, and safe special characters
        sanitized = re.sub(r"[^a-zA-Z0-9\s\-_.]", "", sanitized)

        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized.strip() if sanitized.strip() else None

    def _sanitize_string_input(self, value: str) -> Optional[str]:
        """
        Sanitize general string input for database queries.

        Args:
            value: Raw string input

        Returns:
            Sanitized string or None if invalid
        """
        if not value or not value.strip():
            return None

        # Remove dangerous characters
        sanitized = value.strip()

        # Keep only alphanumeric, underscore, and hyphen
        sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "", sanitized)

        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50]

        return sanitized if sanitized else None

    def _build_filter_conditions(
        self,
        search: Optional[str] = None,
        role_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        cluster: Optional[str] = None,
    ) -> tuple:
        """
        Build WHERE clause conditions and parameters based on provided filters.

        Args:
            search: Search term for name/description
            role_type: Filter by role type
            is_active: Filter by active status
            cluster: Filter by cluster association

        Returns:
            Tuple of (conditions_list, parameters_list)
        """
        # Define allowed filter conditions with their SQL patterns
        # This whitelist approach prevents SQL injection
        allowed_conditions = {
            "search": "(LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))",
            "role_type": "LOWER(type) = LOWER(?)",
            "is_active": "is_active = ?",
            "cluster": "array_contains(clusters, ?)",
        }

        conditions = []
        params = []

        if search and search.strip():
            # Sanitize search input - remove potential SQL injection patterns
            sanitized_search = self._sanitize_search_input(search.strip())
            if sanitized_search:
                conditions.append(allowed_conditions["search"])
                search_pattern = f"%{sanitized_search}%"
                params.extend([search_pattern, search_pattern])

        if role_type and role_type.strip():
            # Validate role_type against allowed values
            sanitized_role_type = self._sanitize_string_input(role_type.strip())
            if sanitized_role_type:
                conditions.append(allowed_conditions["role_type"])
                params.append(sanitized_role_type)

        if is_active is not None:
            conditions.append(allowed_conditions["is_active"])
            params.append(is_active)

        if cluster and cluster.strip():
            # Validate cluster input
            sanitized_cluster = self._sanitize_string_input(cluster.strip())
            if sanitized_cluster:
                conditions.append(allowed_conditions["cluster"])
                params.append(sanitized_cluster)

        return conditions, params

    def _build_count_query(
        self,
        search: Optional[str] = None,
        role_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        cluster: Optional[str] = None,
    ) -> tuple:
        """
        Build dynamic count query based on provided filters using safe parameterization.

        Args:
            search: Search term for name/description
            role_type: Filter by role type
            is_active: Filter by active status
            cluster: Filter by cluster association

        Returns:
            Tuple of (query_string, parameters_list)
        """
        # Use centralized filter condition builder
        conditions, params = self._build_filter_conditions(
            search=search, role_type=role_type, is_active=is_active, cluster=cluster
        )

        # Build the complete count query safely
        base_count = f"SELECT COUNT(*) as count FROM {DB_PREFIX}.roles"

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""

        query = base_count + where_clause

        return query, params

    def get_by_id(self, role_id: str) -> Optional[Dict[str, Any]]:
        """
        Get single role by ID for validation purposes.

        Args:
            role_id: Role ID to retrieve

        Returns:
            Role dictionary or None if not found

        Raises:
            Exception: If database query fails
        """
        try:
            with self._get_connection() as cursor:
                logger.debug(f"Executing query to get role by ID: {role_id}")
                cursor.execute(GET_ROLE_BY_ID, [role_id])
                row = cursor.fetchone()

                if not row:
                    logger.info(f"Role with ID {role_id} not found")
                    return None

                # Define column names based on the roles table schema
                columns = [
                    "id",
                    "name",
                    "type",
                    "description",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "clusters",
                ]

                # Convert row to dictionary
                if isinstance(row, dict):
                    role_data = row
                else:
                    role_data = dict(zip(columns, row))

                logger.info(f"Retrieved role with ID: {role_id}")
                return role_data

        except Exception as e:
            logger.error(
                f"Error fetching role by ID {role_id}: {str(e)}", exc_info=True
            )
            raise Exception(f"Failed to fetch role by ID: {str(e)}")

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Case-insensitive lookup by role name.
        """
        if not name or not name.strip():
            return None
        try:
            with self._get_connection() as cursor:
                cursor.execute(GET_ROLE_BY_NAME, [name.strip()])
                row = cursor.fetchone()
                if not row:
                    return None

                columns = [
                    "id",
                    "name",
                    "type",
                    "description",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "clusters",
                ]
                return row if isinstance(row, dict) else dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Error in get_by_name('{name}'): {e}", exc_info=True)
            raise

    # ---------- DELETE ----------
    def delete_row(self, role_id: str) -> None:
        """
        Delete a role by id. Silent if row doesn't exist.
        """
        if not role_id:
            raise ValueError("role_id is required")

        try:
            with self._get_connection() as cursor:
                cursor.execute(DELETE_ROLE, [role_id])

                # Optional: verify affected rows
                # if hasattr(cursor, "rowcount") and cursor.rowcount == 0:
                #     logger.info(f"No role deleted for id={role_id}")

        except Exception as e:
            logger.error(f"Error deleting role '{role_id}': {e}", exc_info=True)
            raise





   # ---------- Updated requirements ----------

   # ---------- INSERT ----------
    def insert_row(self, row: Dict[str, Any]) -> None:
        """
        Insert a new role row. Expects keys:
        id, name, type, description, is_active, created_at, updated_at,
        clusters (list[dict] in format: {"name": str, "sites": list[str]})
        """
        try:
            # Serialize clusters as JSON
            clusters_json = json.dumps(row.get("clusters") or "[]")
            params = [
                row["id"],
                row["name"],
                row["type"],
                row.get("description"),
                bool(row.get("is_active", True)),
                row["created_at"],
                row["updated_at"],
                clusters_json,
            ]

            with self._get_connection() as cursor:
                cursor.execute(INSERT_ROLE, params)

                # Optional: verify insert
                if hasattr(cursor, "rowcount") and cursor.rowcount == 0:
                    raise Exception("Insert affected 0 rows")

        except Exception as e:
            logger.error(
                f"Error inserting role '{row.get('name')}': {e}", exc_info=True
            )
            raise


  # ---------- UPDATE (partial, dynamic) ----------
    def update_row(
        self, role_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not role_id:
            raise ValueError("role_id is required")

        set_parts = []
        params: Dict[str, Any] = {"id": role_id}

        if "name" in updates:
            set_parts.append("name = %(name)s")
            params["name"] = updates["name"]

        if "type" in updates:
            set_parts.append("type = %(type)s")
            params["type"] = updates["type"]

        if "description" in updates:
            set_parts.append("description = %(description)s")
            params["description"] = updates.get("description")

        if "is_active" in updates:
            set_parts.append("is_active = %(is_active)s")
            params["is_active"] = bool(updates["is_active"])

        if "clusters" in updates:
            set_parts.append(
                "clusters = from_json(%(clusters)s, 'array<struct<name:string,sites:array<string>>>')"
            )
            params["clusters"] = json.dumps(updates.get("clusters") or [])

        # always bump updated_at
        set_parts.append("updated_at = %(updated_at)s")
        params["updated_at"] = updates["updated_at"]

        if not set_parts:
            return self.get_by_id(role_id)

        sql = f"UPDATE {DB_PREFIX}.roles SET {', '.join(set_parts)} WHERE id = %(id)s"

        with self._get_connection() as cursor:
            cursor.execute(sql, params)
            if hasattr(cursor, "rowcount") and cursor.rowcount == 0:
                return None

        return self.get_by_id(role_id)
