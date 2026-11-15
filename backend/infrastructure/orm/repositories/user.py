"""
Repository module for handling users database operations with Databricks SQL Warehouse.
Supports users with roles JOIN operations for enhanced user management.
"""

import logging
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json

from config.databricks_connector import get_databricks_connector
from config.databricks_sql_queries import (CHECK_USER_EXISTS, DB_PREFIX,
                                           GET_USERS_BY_ROLE_ID,
                                           DELETE_USER, GET_USER_BY_EMAIL,
                                           GET_USER_BY_EMAIL_WITHOUT_ROLE_JOIN,
                                           GET_USER_BY_ID,
                                           GET_USER_BY_ID_WITH_ROLE,
                                           GET_USER_BY_SUB, GET_USER_WITH_ROLE,
                                           GET_USERS_WITH_ROLES,
                                           GET_USERS_WITH_ROLES_COUNT,
                                           GET_USERS_WITH_ROLES_FILTERED,
                                           INSERT_USER, UPDATE_USER,
                                           UPDATE_USER_ROLE)

logger = logging.getLogger(__name__)


class UserRepo:
    """
    Repository class for handling all database operations related to users.
    Uses Databricks SQL Warehouse for data storage and retrieval with roles JOIN.
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

    def get_users_with_filters(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        role_id: Optional[str] = None,
        role_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve users with roles using LEFT JOIN and optional filters with pagination.

        Args:
            search: Search term for name/email
            is_active: Filter by active status
            role_id: Filter by specific role ID
            role_type: Filter by role type
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of user dictionaries with nested role information

        Raises:
            Exception: If database query fails
        """
        try:
            with self._get_connection() as cursor:
                # Build dynamic query based on filters
                query, params = self._build_users_query(
                    search=search,
                    is_active=is_active,
                    role_id=role_id,
                    role_type=role_type,
                    offset=offset,
                    limit=limit,
                )

                logger.debug(f"Executing query: {query} with params: {params}")
                cursor.execute(query, params)
                rows = cursor.fetchall()

                logger.info(f"Retrieved {len(rows)} users from database")

                # Define column names based on the users-roles JOIN schema
                columns = [
                    "id",
                    "name",
                    "email",
                    "picture",
                    "sub",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "role_id",
                    "role_id_full",
                    "role_name",
                    "role_type",
                    "role_description",
                    "role_is_active",
                    "role_clusters",
                ]

                # Convert rows to list of dictionaries with processed role data
                if rows:
                    # Check if rows are already dictionaries
                    if isinstance(rows[0], dict):
                        return self._process_users_with_roles(rows)
                    else:
                        # Create dictionaries with column names
                        data = []
                        for row in rows:
                            data.append(dict(zip(columns, row)))
                        return self._process_users_with_roles(data)
                else:
                    return []

        except Exception as e:
            logger.error(f"Error fetching users with filters: {str(e)}", exc_info=True)
            raise Exception(f"Failed to fetch users from database: {str(e)}")

    def get_users_count(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        role_id: Optional[str] = None,
        role_type: Optional[str] = None,
    ) -> int:
        """
        Get the total count of users matching the filters.

        Args:
            search: Search term for name/email
            is_active: Filter by active status
            role_id: Filter by specific role ID
            role_type: Filter by role type

        Returns:
            Total count of matching users

        Raises:
            Exception: If database query fails
        """
        try:
            with self._get_connection() as cursor:
                # Build count query based on filters
                query, params = self._build_count_query(
                    search=search,
                    is_active=is_active,
                    role_id=role_id,
                    role_type=role_type,
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

                logger.info(f"Total users count with filters: {count}")
                return count

        except Exception as e:
            logger.error(f"Error getting users count: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get users count: {str(e)}")

    def _process_users_with_roles(
        self, raw_users: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process raw user data from JOIN query to create properly structured user objects with nested roles.

        Args:
            raw_users: List of raw user dictionaries from database JOIN

        Returns:
            List of processed user dictionaries with nested role objects
        """
        processed_users = []

        for raw_user in raw_users:
            # Build base user object
            user = {
                "id": raw_user.get("id"),
                "name": raw_user.get("name"),
                "email": raw_user.get("email"),
                "picture": raw_user.get("picture"),
                "sub": raw_user.get("sub"),
                "is_active": raw_user.get("is_active"),
                "created_at": raw_user.get("created_at"),
                "updated_at": raw_user.get("updated_at"),
                "role_id": raw_user.get("role_id"),
            }

            # Build nested role object if role data exists
            role_id_full = raw_user.get("role_id_full")
            if role_id_full:
                user["role"] = {
                    "id": role_id_full,
                    "name": raw_user.get("role_name"),
                    "type": raw_user.get("role_type"),
                    "description": raw_user.get("role_description"),
                    "is_active": raw_user.get("role_is_active"),
                    "clusters": raw_user.get("role_clusters"),
                }
            else:
                user["role"] = None

            processed_users.append(user)

        return processed_users

    def _build_users_query(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        role_id: Optional[str] = None,
        role_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple:
        """
        Build dynamic SQL query for users with roles based on provided filters using safe parameterization.

        Args:
            search: Search term for name/email
            is_active: Filter by active status
            role_id: Filter by specific role ID
            role_type: Filter by role type
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (query_string, parameters_list)
        """
        # Use centralized filter condition builder
        conditions, params = self._build_filter_conditions(
            search=search, is_active=is_active, role_id=role_id, role_type=role_type
        )

        # Build the complete query safely
        base_select = f"""
            SELECT 
                u.id, u.name, u.email, u.picture, u.sub,
                u.is_active, u.created_at, u.updated_at, u.role_id,
                r.id as role_id_full, r.name as role_name, 
                r.type as role_type, r.description as role_description,
                r.is_active as role_is_active, r.clusters as role_clusters
            FROM {DB_PREFIX}.users u
            LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id
        """

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""

        query = (
            base_select + where_clause + " ORDER BY u.created_at DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])

        return query, params

    def _build_count_query(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        role_id: Optional[str] = None,
        role_type: Optional[str] = None,
    ) -> tuple:
        """
        Build dynamic count query for users based on provided filters using safe parameterization.

        Args:
            search: Search term for name/email
            is_active: Filter by active status
            role_id: Filter by specific role ID
            role_type: Filter by role type

        Returns:
            Tuple of (query_string, parameters_list)
        """
        # Use centralized filter condition builder
        conditions, params = self._build_filter_conditions(
            search=search, is_active=is_active, role_id=role_id, role_type=role_type
        )

        # Build the complete count query safely
        base_count = f"SELECT COUNT(*) as count FROM {DB_PREFIX}.users u LEFT JOIN {DB_PREFIX}.roles r ON u.role_id = r.id"

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""

        query = base_count + where_clause

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
        is_active: Optional[bool] = None,
        role_id: Optional[str] = None,
        role_type: Optional[str] = None,
    ) -> tuple:
        """
        Build WHERE clause conditions and parameters based on provided filters.

        Args:
            search: Search term for name/email
            is_active: Filter by active status
            role_id: Filter by specific role ID
            role_type: Filter by role type

        Returns:
            Tuple of (conditions_list, parameters_list)
        """
        # Define allowed filter conditions with their SQL patterns
        # This whitelist approach prevents SQL injection
        allowed_conditions = {
            "search": "(LOWER(u.name) LIKE LOWER(?) OR LOWER(u.email) LIKE LOWER(?))",
            "is_active": "u.is_active = ?",
            "role_id": "u.role_id = ?",
            "role_type": "LOWER(r.type) = LOWER(?)",
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

        if is_active is not None:
            conditions.append(allowed_conditions["is_active"])
            params.append(is_active)

        if role_id and role_id.strip():
            # Validate role_id (should be UUID format)
            sanitized_role_id = self._sanitize_string_input(role_id.strip())
            if sanitized_role_id:
                conditions.append(allowed_conditions["role_id"])
                params.append(sanitized_role_id)

        if role_type and role_type.strip():
            # Validate role_type against allowed values
            sanitized_role_type = self._sanitize_string_input(role_type.strip())
            if sanitized_role_type:
                conditions.append(allowed_conditions["role_type"])
                params.append(sanitized_role_type)

        return conditions, params

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get single user by ID without role information.

        Args:
            user_id: User ID to retrieve

        Returns:
            User dictionary or None if not found

        Raises:
            Exception: If database query fails
        """
        try:
            with self._get_connection() as cursor:
                logger.debug(f"Executing query to get user by ID: {user_id}")
                cursor.execute(GET_USER_BY_ID, [user_id])
                row = cursor.fetchone()

                if not row:
                    logger.info(f"User with ID {user_id} not found")
                    return None

                # Define column names based on the users table schema
                columns = [
                    "id",
                    "name",
                    "email",
                    "picture",
                    "sub",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "role_id",
                ]

                # Convert row to dictionary
                if isinstance(row, dict):
                    user_data = row
                else:
                    user_data = dict(zip(columns, row))

                logger.info(f"Retrieved user with ID: {user_id}")
                return user_data

        except Exception as e:
            logger.error(
                f"Error fetching user by ID {user_id}: {str(e)}", exc_info=True
            )
            raise Exception(f"Failed to fetch user by ID: {str(e)}")

    def update_role(self, user_id: str, role_id: Optional[str]) -> bool:
        """
        Update user's role_id and updated_at timestamp.

        Args:
            user_id: User ID to update
            role_id: New role ID to assign (can be None to remove role)

        Returns:
            True if update was successful, False otherwise

        Raises:
            Exception: If database update fails
        """
        try:
            from datetime import datetime

            with self._get_connection() as cursor:
                updated_at = datetime.now()

                logger.debug(f"Updating role for user {user_id} to role_id: {role_id}")
                cursor.execute(UPDATE_USER_ROLE, [role_id, updated_at, user_id])

                # Check if any rows were affected
                if hasattr(cursor, "rowcount") and cursor.rowcount == 0:
                    logger.warning(
                        f"No rows affected when updating role for user {user_id}"
                    )
                    return False

                logger.info(
                    f"Successfully updated role for user {user_id} to role_id: {role_id}"
                )
                return True

        except Exception as e:
            logger.error(
                f"Error updating role for user {user_id}: {str(e)}", exc_info=True
            )
            raise Exception(f"Failed to update user role: {str(e)}")

    def get_with_role(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user with role information via LEFT JOIN.

        Args:
            user_id: User ID to retrieve

        Returns:
            User dictionary with nested role information or None if not found

        Raises:
            Exception: If database query fails
        """
        try:
            with self._get_connection() as cursor:
                logger.debug(f"Executing query to get user with role by ID: {user_id}")
                cursor.execute(GET_USER_WITH_ROLE, [user_id])
                row = cursor.fetchone()

                if not row:
                    logger.info(f"User with ID {user_id} not found")
                    return None

                # Define column names based on the users-roles JOIN schema
                columns = [
                    "id",
                    "name",
                    "email",
                    "picture",
                    "sub",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "role_id",
                    "role_id_full",
                    "role_name",
                    "role_type",
                    "role_description",
                    "role_is_active",
                    "role_clusters",
                ]

                # Convert row to dictionary
                if isinstance(row, dict):
                    raw_user = row
                else:
                    raw_user = dict(zip(columns, row))

                # Process the user data using existing method
                processed_users = self._process_users_with_roles([raw_user])

                if processed_users:
                    logger.info(f"Retrieved user with role info for ID: {user_id}")
                    return processed_users[0]
                else:
                    return None

        except Exception as e:
            logger.error(
                f"Error fetching user with role by ID {user_id}: {str(e)}",
                exc_info=True,
            )
            raise Exception(f"Failed to fetch user with role: {str(e)}")
    


    def get_users_by_role_id(self, role_id: str) -> list[Dict[str, Any]]:
        """
        Fetch all users assigned to a specific role ID.
        """
        try:
            with self._get_connection() as cursor:
                # query = "SELECT id, name, email FROM users WHERE role_id = ?"
                cursor.execute(GET_USERS_BY_ROLE_ID, [role_id])
                rows = cursor.fetchall()

                if not rows:
                    return []

                # Each row is likely a tuple, so convert to dict
                users = [
                    {"id": r[0], "name": r[1], "email": r[2]}
                    for r in rows
                ]
                return users

        except Exception as e:
            logger.error(
                f"Error fetching users with role ID {role_id}: {str(e)}", exc_info=True
            )
            raise Exception(f"Failed to get users with role {role_id}: {str(e)}")


    def find_by_email_with_role(self, email: str) -> Optional[Dict[str, Any]]:
        if not email or not email.strip():
            raise ValueError("Email is required")
        email = email.strip().lower()

        try:
            with self._get_connection() as cursor:
                cursor.execute(
                    GET_USER_BY_EMAIL, [email]
                )  # ensure query LOWER(email)=?
                row = cursor.fetchone()
                if not row:
                    return None

                columns = [
                    "id",
                    "name",
                    "email",
                    "picture",
                    "sub",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "role_id",
                    "role_id_full",
                    "role_name",
                    "role_type",
                    "role_description",
                    "role_is_active",
                    "role_clusters",
                ]
                raw_user = row if isinstance(row, dict) else dict(zip(columns, row))
                users = self._process_users_with_roles([raw_user])
                return users[0] if users else None

        except Exception as e:
            logger.error(
                f"Error fetching user with role by email {email}: {e}", exc_info=True
            )
            raise

    def create_user(
        self,
        *,
        name: str,
        email: str,
        picture: Optional[str] = None,
        sub: Optional[str] = None,
        role_id: Optional[str] = None,
        is_active: bool = True,
    ) -> Dict[str, Any]:
        if not email or not email.strip():
            raise ValueError("Email is required")
        email = email.strip().lower()

        # Check if user already exists first
        existing = self.find_by_email_with_role(email)
        if existing:
            return existing

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        try:
            with self._get_connection() as cursor:
                params = [
                    user_id,
                    name,
                    email,
                    picture,
                    sub,
                    is_active,
                    now,
                    now,
                    role_id,
                ]
                cursor.execute(INSERT_USER, params)

                if hasattr(cursor, "rowcount") and cursor.rowcount == 0:
                    raise Exception("Insert reported 0 affected rows")

        except Exception as e:
            logger.error(f"Error inserting user '{email}': {e}", exc_info=True)
            raise

        # Re-fetch to include joined role data using a separate connection
        return self.find_by_email_with_role(email)

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if not email or not email.strip():
            raise ValueError("Email is required")
        email = email.strip().lower()

        try:
            with self._get_connection() as cursor:
                cursor.execute(
                    GET_USER_BY_EMAIL_WITHOUT_ROLE_JOIN, [email]
                )  # ensure query LOWER(email)=?
                row = cursor.fetchone()
                if not row:
                    return None

                columns = [
                    "id",
                    "name",
                    "email",
                    "picture",
                    "sub",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "role_id",
                    "role_id_full",
                    "role_name",
                    "role_type",
                    "role_description",
                    "role_is_active",
                    "role_clusters",
                ]
                raw_user = row if isinstance(row, dict) else dict(zip(columns, row))
                users = self._process_users_with_roles([raw_user])
                return users[0] if users else None

        except Exception as e:
            logger.error(
                f"Error fetching user with role by email {email}: {e}", exc_info=True
            )
            raise



    # ---------- Updated requirements ----------

    def _process_users_with_roles_ur(
        self, raw_users: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process raw user data from JOIN query to create properly structured user objects with nested roles.

        Args:
            raw_users: List of raw user dictionaries from database JOIN

        Returns:
            List of processed user dictionaries with nested role objects
        """
        processed_users = []

        for raw_user in raw_users:
            # Build base user object
            user = {
                "id": raw_user.get("id"),
                "name": raw_user.get("name"),
                "email": raw_user.get("email"),
                "picture": raw_user.get("picture"),
                "sub": raw_user.get("sub"),
                "is_active": raw_user.get("is_active"),
                "created_at": raw_user.get("created_at"),
                "updated_at": raw_user.get("updated_at"),
                "role_id": raw_user.get("role_id"),
            }

            # Build nested role object if role data exists
            role_id_full = raw_user.get("role_id_full")
            if role_id_full:
                clusters_val = raw_user.get("role_clusters") or []

                # --- Normalize clusters ---
                normalized_clusters = []
                try:
                    if isinstance(clusters_val, str):
                        clusters_val = json.loads(clusters_val)

                    if isinstance(clusters_val, list):
                        for c in clusters_val:
                            if isinstance(c, dict):
                                # Already in new format {name, sites}
                                normalized_clusters.append({
                                    "name": c.get("name"),
                                    "sites": c.get("sites", []),
                                })
                            elif isinstance(c, str):
                                # Legacy format: cluster was a string, wrap with empty sites
                                normalized_clusters.append({
                                    "name": c,
                                    "sites": [],
                                })
                    elif isinstance(clusters_val, dict):
                        # Single dict instead of list
                        normalized_clusters = [{
                            "name": clusters_val.get("name"),
                            "sites": clusters_val.get("sites", []),
                        }]
                except Exception as e:
                    logger.warning(
                        f"Failed to normalize clusters for user {raw_user.get('email')}: {e}"
                    )
                    normalized_clusters = []

                user["role"] = {
                    "id": role_id_full,
                    "name": raw_user.get("role_name"),
                    "type": raw_user.get("role_type"),
                    "description": raw_user.get("role_description"),
                    "is_active": raw_user.get("role_is_active"),
                    "clusters": normalized_clusters,
                }
            else:
                user["role"] = None

            processed_users.append(user)

        return processed_users
