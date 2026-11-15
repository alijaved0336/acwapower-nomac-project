import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Removed pandas dependency for performance - using native Python data structures

from config.databricks_connector import get_databricks_connector
from config.databricks_sql_queries import (
    CHECK_ANALYSIS_EXISTS, DB_PREFIX, DELETE_ANALYSIS, GET_ALL_ACTIVE_ANALYSIS,
    GET_ANALYSIS_BY_ALL_FILTERS, GET_ANALYSIS_BY_ALL_FILTERS_WITH_VISIBILITY,
    GET_ANALYSIS_BY_DATE_RANGE, GET_ANALYSIS_BY_DATE_RANGE_AND_VISIBILITY,
    GET_ANALYSIS_BY_NAME_FILTER, GET_ANALYSIS_BY_NAME_FILTER_AND_DATE_RANGE,
    GET_ANALYSIS_BY_NAME_FILTER_AND_DATE_RANGE_AND_VISIBILITY,
    GET_ANALYSIS_BY_NAME_FILTER_AND_VISIBILITY, GET_ANALYSIS_BY_USER,
    GET_ANALYSIS_BY_USER_AND_DATE_RANGE,
    GET_ANALYSIS_BY_USER_AND_DATE_RANGE_AND_VISIBILITY,
    GET_ANALYSIS_BY_USER_AND_NAME_FILTER,
    GET_ANALYSIS_BY_USER_AND_NAME_FILTER_AND_VISIBILITY,
    GET_ANALYSIS_BY_USER_AND_VISIBILITY, GET_ANALYSIS_BY_VISIBILITY,
    INSERT_ANALYSIS, UPDATE_ANALYSIS_DYNAMIC_BASE, GET_ANALYSIS_BY_ID)

logger = logging.getLogger(__name__)


class AnalysisRepo:
    """Repository for handling analysis reports database queries with Databricks"""

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with transaction support"""
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

    def get_all_analysis(self) -> List[Dict]:
        """Return all active analysis reports as DataFrame."""
        try:
            with self._get_connection() as cursor:
                cursor.execute(GET_ALL_ACTIVE_ANALYSIS)
                rows = cursor.fetchall()
                logger.info(f"Retrieved {len(rows)} active analysis records")

                # Define column names matching the query
                columns = [
                    "id",
                    "user_id", 
                    "user_name",  # from JOIN with users table
                    "name",
                    "asset_type",
                    "type",
                    "visibility",
                    "applied_date_filter",
                    "created_at",
                    "updated_at",
                ]

                # Convert rows to list of dicts with proper column names
                if rows:
                    # If rows are already dictionaries, use them directly
                    if isinstance(rows[0], dict):
                        # Apply deserialization to each record
                        return [self._deserialize_applied_date_filter(row) for row in rows]
                    # Otherwise, create dictionaries with column names
                    else:
                        data = []
                        for row in rows:
                            record = dict(zip(columns, row))
                            # Deserialize applied_date_filter from JSON string to object
                            record = self._deserialize_applied_date_filter(record)
                            data.append(record)
                        return data
                else:
                    return []
        except Exception as e:
            logger.error(f"Error fetching analysis data: {e}")
            return []

    def get_analysis_with_filters(
        self,
        user: str = None,
        name: str = None,
        from_date: datetime = None,
        to_date: datetime = None,
        visibility: str = None,
    ) -> List[Dict]:
        """Get analysis reports with various filters applied"""
        try:
            with self._get_connection() as cursor:
                # Determine which query to use based on filters
                params = []

                # Check if all filters are provided (including visibility)
                if user and name and from_date and to_date and visibility:
                    query = GET_ANALYSIS_BY_ALL_FILTERS_WITH_VISIBILITY
                    params = [user, f"%{name}%", from_date, to_date, visibility]
                elif user and name and from_date and to_date:
                    query = GET_ANALYSIS_BY_ALL_FILTERS
                    params = [user, f"%{name}%", from_date, to_date]
                elif user and name and visibility:
                    query = GET_ANALYSIS_BY_USER_AND_NAME_FILTER_AND_VISIBILITY
                    params = [user, f"%{name}%", visibility]
                elif user and from_date and to_date and visibility:
                    query = GET_ANALYSIS_BY_USER_AND_DATE_RANGE_AND_VISIBILITY
                    params = [user, from_date, to_date, visibility]
                elif name and from_date and to_date and visibility:
                    query = GET_ANALYSIS_BY_NAME_FILTER_AND_DATE_RANGE_AND_VISIBILITY
                    params = [f"%{name}%", from_date, to_date, visibility]
                elif user and name:
                    query = GET_ANALYSIS_BY_USER_AND_NAME_FILTER
                    params = [user, f"%{name}%"]
                elif user and from_date and to_date:
                    query = GET_ANALYSIS_BY_USER_AND_DATE_RANGE
                    params = [user, from_date, to_date]
                elif name and from_date and to_date:
                    query = GET_ANALYSIS_BY_NAME_FILTER_AND_DATE_RANGE
                    params = [f"%{name}%", from_date, to_date]
                elif user and visibility:
                    query = GET_ANALYSIS_BY_USER_AND_VISIBILITY
                    params = [user, visibility]
                elif name and visibility:
                    query = GET_ANALYSIS_BY_NAME_FILTER_AND_VISIBILITY
                    params = [f"%{name}%", visibility]
                elif from_date and to_date and visibility:
                    query = GET_ANALYSIS_BY_DATE_RANGE_AND_VISIBILITY
                    params = [from_date, to_date, visibility]
                elif user:
                    query = GET_ANALYSIS_BY_USER
                    params = [user]
                elif name:
                    query = GET_ANALYSIS_BY_NAME_FILTER
                    params = [f"%{name}%"]
                elif from_date and to_date:
                    query = GET_ANALYSIS_BY_DATE_RANGE
                    params = [from_date, to_date]
                elif visibility:
                    query = GET_ANALYSIS_BY_VISIBILITY
                    params = [visibility]
                else:
                    query = GET_ALL_ACTIVE_ANALYSIS
                    params = []

                cursor.execute(query, params)
                rows = cursor.fetchall()
                filter_info = f"user_id={user}, name={name}, from_date={from_date}, to_date={to_date}, visibility={visibility}"
                logger.info(
                    f"Retrieved {len(rows)} analysis records with filters: {filter_info}"
                )

                # Define column names matching the query
                columns = [
                    "id",
                    "user_id",
                    "user_name",
                    "name",
                    "asset_type",
                    "type",
                    "visibility",
                    "created_at",
                    "updated_at",
                ]

                # Convert rows to list of dicts with proper column names
                if rows:
                    # If rows are already dictionaries, use them directly
                    if isinstance(rows[0], dict):
                        return rows
                    # Otherwise, create dictionaries with column names
                    else:
                        data = []
                        for row in rows:
                            data.append(dict(zip(columns, row)))
                        return data
                else:
                    return []

        except Exception as e:
            logger.error(f"Error fetching filtered analysis data: {e}")
            return []

    def delete_by_id(self, analysis_id: str) -> bool:
        """Delete analysis permanently from database"""
        if not analysis_id:
            logger.warning("Attempted to delete analysis with empty ID")
            return False

        try:
            with self._get_connection() as cursor:
                # Check if analysis exists
                cursor.execute(CHECK_ANALYSIS_EXISTS, [analysis_id])
                result = cursor.fetchone()
                if not result or result["count"] == 0:
                    logger.warning(f"Analysis {analysis_id} not found for deletion")
                    return False

                # Delete the analysis
                cursor.execute(DELETE_ANALYSIS, [analysis_id])
                logger.info(f"Successfully deleted analysis {analysis_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            return False

    def create(self, data: dict) -> dict:
        """Create a new analysis record"""
        # Validate required fields
        required_fields = ["id", "user_id", "name", "asset_type", "type"]
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Required field '{field}' is missing or empty")

        try:
            with self._get_connection() as cursor:
                # Convert created_at to proper timestamp format if it's a string
                created_at = data.get("created_at")
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        created_at = datetime.now(timezone.utc)
                elif not created_at:
                    created_at = datetime.now(timezone.utc)

                # Set updated_at
                updated_at = datetime.now(timezone.utc)

                # Insert new record
                cursor.execute(
                    INSERT_ANALYSIS,
                    (
                        data["id"],
                        data["user_id"],
                        data["name"],
                        data["asset_type"],
                        data["type"],
                        data.get("visibility", "private"),
                        data.get("applied_date_filter"),
                        created_at,
                        updated_at,
                    ),
                )

                logger.info(
                    f"Successfully created analysis {data['id']} for user {data['user_id']}"
                )
                
                # Return the data with applied_date_filter as object (not JSON string)
                return_data = data.copy()
                return_data = self._deserialize_applied_date_filter(return_data)
                return return_data

        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            raise

    def check_analysis_exists(self, analysis_id: str) -> bool:
        """Check if analysis exists in database"""
        if not analysis_id:
            logger.warning("Attempted to check existence with empty analysis ID")
            return False

        try:
            with self._get_connection() as cursor:
                cursor.execute(CHECK_ANALYSIS_EXISTS, [analysis_id])
                result = cursor.fetchone()
                exists = result and result["count"] > 0
                logger.debug(f"Analysis {analysis_id} exists: {exists}")
                return exists
        except Exception as e:
            logger.error(f"Error checking if analysis exists {analysis_id}: {e}")
            return False
    
    def get_by_id(self, analysis_id: str) -> Optional[dict]:
        """Get a single analysis by ID"""
        if not analysis_id:
            return None

        try:
            with self._get_connection() as cursor:
                cursor.execute(GET_ANALYSIS_BY_ID, [analysis_id])
                record = cursor.fetchone()
                
                if not record:
                    return None
                    
                if not isinstance(record, dict):
                    columns = [
                        "id", "user_id", "name", "asset_type", "type", 
                        "visibility", "applied_date_filter", "created_at", "updated_at"
                    ]
                    record = dict(zip(columns, record))
                
                # Deserialize applied_date_filter from JSON string to object
                record = self._deserialize_applied_date_filter(record)
                    
                return record
                
        except Exception as e:
            logger.error(f"Error fetching analysis {analysis_id}: {e}")
            return None
    
    def update_by_id(self, analysis_id: str, update_data: dict) -> dict:
        """Update an existing analysis record"""
        if not analysis_id:
            raise ValueError("Analysis ID is required for update")

        try:
            with self._get_connection() as cursor:
                # First, get the current record using imported query
                cursor.execute(GET_ANALYSIS_BY_ID, [analysis_id])
                current_record = cursor.fetchone()
                
                if not current_record:
                    raise ValueError(f"Analysis with ID {analysis_id} not found")

                # Convert current record to dict if it's not already
                if not isinstance(current_record, dict):
                    columns = [
                        "id", "user_id", "name", "asset_type", "type", 
                        "visibility", "applied_date_filter", "created_at", "updated_at"
                    ]
                    current_record = dict(zip(columns, current_record))
                
                # Deserialize applied_date_filter from JSON string to object
                current_record = self._deserialize_applied_date_filter(current_record)

                # Build the update query dynamically based on provided fields
                update_fields = []
                update_values = []
                
                for field, value in update_data.items():
                    if field != "id" and value is not None:  # Don't update ID
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)

                if not update_fields:
                    # No fields to update, return current record
                    return current_record

                # Add the ID to the end for the WHERE clause
                update_values.append(analysis_id)
                
                # Construct the update query using the imported base
                update_query = UPDATE_ANALYSIS_DYNAMIC_BASE.format(
                update_fields=', '.join(update_fields)
            )
                
                cursor.execute(update_query, update_values)
                
                # Get the updated record using imported query
                cursor.execute(GET_ANALYSIS_BY_ID, [analysis_id])
                updated_record = cursor.fetchone()
                
                if not isinstance(updated_record, dict):
                    columns = [
                        "id", "user_id", "name", "asset_type", "type", 
                        "visibility", "applied_date_filter", "created_at", "updated_at"
                    ]
                    updated_record = dict(zip(columns, updated_record))

                # Deserialize applied_date_filter from JSON string to object
                updated_record = self._deserialize_applied_date_filter(updated_record)

                logger.info(f"Successfully updated analysis {analysis_id}")
                return updated_record

        except Exception as e:
            logger.error(f"Error updating analysis {analysis_id}: {e}")
            raise

    def get_analysis_with_access_control(
        self,
        authenticated_user_id: str,
        authenticated_user_email: str = None,
        user_id: str = None,
        name: str = None,
        from_date: datetime = None,
        to_date: datetime = None,
        visibility: str = None,
        is_super_admin: bool = False,
    ) -> List[Dict]:
        """Get analysis reports with access control.

        Access Control:
        - Super admins (is_super_admin=True): Can view ALL analyses (public and private)
        - Regular users: Can only see their own analyses + others' public analyses
        """
        try:
            with self._get_connection() as cursor:
                # Build the base query with access control checking BOTH ID and EMAIL
                # Super admin bypass: If is_super_admin=TRUE, skip access control
                base_query = f"""
                SELECT a.id, a.user_id, u.name as user_name, a.name, a.asset_type, a.type,
                    a.visibility, a.created_at, a.updated_at
                FROM {DB_PREFIX}.analysis a
                LEFT JOIN {DB_PREFIX}.users u ON a.user_id = u.id
                WHERE (? = 1 OR a.user_id = ? OR a.visibility = 'public'
                """

                params = [1 if is_super_admin else 0, authenticated_user_id]

                # Add email check if provided
                if authenticated_user_email:
                    base_query += " OR LOWER(a.user_id) = LOWER(?)"
                    params.append(authenticated_user_email)

                base_query += ")"  # Close the WHERE condition

                # Add additional filters
                if user_id:
                    base_query += " AND a.user_id = ?"
                    params.append(user_id)

                if name:
                    base_query += " AND LOWER(a.name) LIKE LOWER(?)"
                    params.append(f"%{name}%")

                if from_date:
                    base_query += " AND a.created_at >= ?"
                    params.append(from_date)

                if to_date:
                    base_query += " AND a.created_at <= ?"
                    params.append(to_date)

                if visibility:
                    base_query += " AND LOWER(a.visibility) = LOWER(?)"
                    params.append(visibility)

                base_query += " ORDER BY a.created_at DESC"

                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                filter_info = f"authenticated_user_id={authenticated_user_id}, authenticated_user_email={authenticated_user_email}, is_super_admin={is_super_admin}, user_id={user_id}, name={name}, from_date={from_date}, to_date={to_date}, visibility={visibility}"
                logger.info(
                    f"Retrieved {len(rows)} analysis records with access control and filters: {filter_info}"
                )

                # Define column names matching the query
                columns = [
                    "id",
                    "user_id",
                    "user_name",
                    "name",
                    "asset_type",
                    "type",
                    "visibility",
                    "created_at",
                    "updated_at",
                ]

                # Convert rows to list of dicts with proper column names
                if rows:
                    if isinstance(rows[0], dict):
                        return rows
                    else:
                        data = []
                        for row in rows:
                            data.append(dict(zip(columns, row)))
                        return data
                else:
                    return []

        except Exception as e:
            logger.error(f"Error fetching analysis data with access control: {e}")
            return []

    def get_analysis_by_id_with_access_control(
        self,
        analysis_id: int,
        authenticated_user_id: str,
        authenticated_user_email: str = None,
        is_super_admin: bool = False,
    ) -> Optional[dict]:
        """Get a single analysis by ID with access control.

        Access Control:
        - Super admins (is_super_admin=True): Can view ANY analysis (public or private)
        - Regular users: Can only view their own analyses + others' public analyses
        """
        if not analysis_id or not authenticated_user_id:
            return None

        try:
            with self._get_connection() as cursor:
                # Query with access control checking BOTH ID and EMAIL
                # Super admin bypass: If is_super_admin=TRUE, skip access control
                query = f"""
                SELECT a.id, a.user_id, a.name, a.asset_type, a.type,
                    a.visibility, a.applied_date_filter, a.created_at, a.updated_at
                FROM {DB_PREFIX}.analysis a
                WHERE a.id = ?
                AND (? = 1 OR a.user_id = ? OR a.visibility = 'public'
                """

                params = [analysis_id, 1 if is_super_admin else 0, authenticated_user_id]
                
                # Add email check if provided
                if authenticated_user_email:
                    query += " OR LOWER(a.user_id) = LOWER(?)"
                    params.append(authenticated_user_email)
                
                query += ")"

                cursor.execute(query, params)
                record = cursor.fetchone()

                if not record:
                    logger.warning(f"Analysis {analysis_id} not found or access denied for user {authenticated_user_id}")
                    return None

                if not isinstance(record, dict):
                    columns = [
                        "id", "user_id", "name", "asset_type", "type",
                        "visibility", "applied_date_filter", "created_at", "updated_at"
                    ]
                    record = dict(zip(columns, record))

                # Deserialize applied_date_filter from JSON string to object
                record = self._deserialize_applied_date_filter(record)

                logger.info(
                    f"Retrieved analysis {analysis_id} with access control for user {authenticated_user_id} "
                    f"(is_super_admin={is_super_admin})"
                )
                return record

        except Exception as e:
            logger.error(f"Error fetching analysis {analysis_id} with access control: {e}")
            return None

    def _deserialize_applied_date_filter(self, record: dict) -> dict:
        """Helper method to deserialize applied_date_filter from JSON string to object"""
        if not record or not isinstance(record, dict):
            return record
        
        applied_date_filter = record.get("applied_date_filter")
        if applied_date_filter and isinstance(applied_date_filter, str):
            try:
                import json
                record["applied_date_filter"] = json.loads(applied_date_filter)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to deserialize applied_date_filter: {e}")
                # Keep the original string value if deserialization fails
                pass
        
        return record
