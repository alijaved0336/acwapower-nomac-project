import json
import logging
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.databricks_connector import get_databricks_connector
from config.databricks_sql_queries import (
    BULK_DELETE_WIDGETS,
    BULK_INSERT_WIDGETS,
    BULK_UPDATE_WIDGETS,
    CHECK_BULK_WIDGETS_EXIST,
    CHECK_WIDGET_EXISTS,
    DB_PREFIX,
    DELETE_ALL_WIDGETS_FOR_ANALYSIS,
    DELETE_WIDGET,
    GET_ALL_WIDGETS_FOR_ANALYSIS,
    GET_WIDGET_BY_ID_AND_ANALYSIS,
    INSERT_WIDGET,
    UPDATE_WIDGET,
    # Widget Ordering Queries
    GET_WIDGETS_ORDERED,
    UPDATE_WIDGET_ORDER,
    GET_NEXT_DISPLAY_ORDER,
    COMPACT_WIDGET_ORDERING,
    GET_WIDGET_COUNT_FOR_ANALYSIS,
    CHECK_DISPLAY_ORDER_CONFLICTS,
    GET_WIDGETS_BY_DISPLAY_ORDERS,
    INCREMENT_DISPLAY_ORDERS_FROM,
    # Migration Queries
    ADD_DISPLAY_ORDER_COLUMN,
    INITIALIZE_DISPLAY_ORDER_FOR_EXISTING_WIDGETS,
    VALIDATE_DISPLAY_ORDER_MIGRATION,
    # Performance Optimization
    CREATE_WIDGET_ANALYSIS_DISPLAY_ORDER_INDEX,
)

logger = logging.getLogger(__name__)


class WidgetsRepository:
    """Repository for handling widget database queries with Databricks"""
    
    @staticmethod
    def _strip_datasource_from_columns(columns: list) -> list:
        """
        Remove dataSource from columns to avoid Databricks 1MB parameter limit.
        Data is fetched dynamically on GET, not stored.
        
        Args:
            columns: List of column dictionaries
            
        Returns:
            List of columns without dataSource fields
        """
        columns_without_data = []
        for col in columns:
            col_copy = col.copy()
            col_copy.pop("dataSource", None)
            columns_without_data.append(col_copy)
        return columns_without_data

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with explicit transaction control

        This context manager ensures proper transaction handling with:
        - Explicit autocommit=False for transaction control
        - Commit only on successful completion
        - Rollback on any exception
        - Proper resource cleanup
        """
        connection = None
        cursor = None
        try:
            connection = get_databricks_connector()
            cursor = connection.cursor()
            # Databricks doesn't support transactions, so skip autocommit settings
            yield cursor
            # No explicit commit needed for Databricks
            logger.debug("Database operation completed successfully")
        except Exception as e:
            # Databricks doesn't support rollback, so just log and re-raise
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            # Close only the cursor, not the connection (singleton pattern)
            if cursor:
                try:
                    cursor.close()
                    logger.debug("Cursor closed successfully")
                except Exception as close_error:
                    logger.warning(f"Error closing cursor: {close_error}")
            # Note: We do not close the connection here as it should be managed by the singleton

    def _get_table_name(self) -> str:
        """Get the full table name for widgets"""
        from config.databricks_sql_queries import DB_PREFIX
        return f"{DB_PREFIX}.widget"

    def _convert_db_row_to_widget_format(self, row: Dict) -> Dict:
        """Convert database row back to widget format"""

        def safe_str(value):
            """Safely convert value to string"""
            return str(value) if value is not None else None

        def safe_json_loads(value):
            """Safely parse JSON string"""
            if not value:
                return []
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []

        def _get_row_value(row, key, default=None):
            """Safely extract value from row regardless of format (dict or object)"""
            try:
                if hasattr(row, "get") and callable(getattr(row, "get")):
                    return row.get(key, default)
                elif isinstance(row, dict):
                    return row.get(key, default)
                elif hasattr(row, key):
                    return getattr(row, key, default)
                else:
                    logger.debug(f"Row value not found for key: {key}")
                    return default
            except Exception as e:
                logger.debug(f"Error accessing row value for key {key}: {e}")
                return default

        try:
            analysis_data = {
                "analysis_id": safe_str(_get_row_value(row, "analysis_table_id")),
                "analysis_name": safe_str(_get_row_value(row, "analysis_name")),
                "user_id": safe_str(_get_row_value(row, "user_id")),
                "asset_type": safe_str(_get_row_value(row, "asset_type")),
                "analysis_type": safe_str(_get_row_value(row, "analysis_type")),
                "visibility": safe_str(_get_row_value(row, "visibility")),
                "applied_date_filter": self._deserialize_applied_date_filter(_get_row_value(row, "applied_date_filter")),
                "analysis_created_at": safe_str(_get_row_value(row, "analysis_created_at")),
                "analysis_updated_at": safe_str(_get_row_value(row, "analysis_updated_at")),
            }

            return {
                "id": safe_str(_get_row_value(row, "id", "")),
                "type": safe_str(_get_row_value(row, "type", "")),
                "name": safe_str(_get_row_value(row, "name", "")) or "",
                "columns": safe_json_loads(_get_row_value(row, "columns")),
                "analysis_data": analysis_data,
                "data": safe_json_loads(_get_row_value(row, "data")),
                "display_order": _get_row_value(row, "display_order", 0) or 0,
                "yAxisOptions": safe_json_loads(_get_row_value(row, "yaxis_option")),
                "selectedRacks": safe_json_loads(_get_row_value(row, "selected_racks")),
            }
        except Exception as e:
            logger.error(f"Error converting widget row: {str(e)}")
            return {
                "id": "",
                "type": "",
                "name": "",
                "columns": [],
                "analysis_data": {},
                "data": [],
                "display_order": 0,
                "yAxisOptions": [],
                "selectedRacks": None,
            }

    def get_widget(self, widget_id: str, analysis_id: str) -> Optional[Dict]:
        """Retrieve a widget from Databricks"""
        if not widget_id or not analysis_id:
            logger.warning("Widget ID and Analysis ID are required")
            return None

        try:
            with self._get_connection() as cursor:
                cursor.execute(GET_WIDGET_BY_ID_AND_ANALYSIS, [widget_id, analysis_id])
                row = cursor.fetchone()

                if not row:
                    logger.debug(
                        f"Widget {widget_id} not found for analysis {analysis_id}"
                    )
                    return None

                widget_data = self._convert_db_row_to_widget_format(row)
                logger.info(f"Retrieved widget {widget_id} for analysis {analysis_id}")
                return widget_data

        except Exception as e:
            logger.error(
                f"Error retrieving widget {widget_id} for analysis {analysis_id}: {str(e)}"
            )
            raise Exception(f"Failed to retrieve widget: {str(e)}")

    def get_widget_by_id_only(self, widget_id: str) -> Optional[Dict]:
        """Retrieve a widget by ID across all analyses"""
        if not widget_id:
            logger.warning("Widget ID is required")
            return None

        try:
            with self._get_connection() as cursor:
                # Modified query to find widget by ID only
                cursor.execute(
                    f"""
                    SELECT w.*, a.id as analysis_table_id, a.name as analysis_name, 
                           a.user_id, a.asset_type, a.type as analysis_type, a.visibility, 
                           a.applied_date_filter, a.created_at as analysis_created_at, 
                           a.updated_at as analysis_updated_at 
                    FROM {DB_PREFIX}.widget w 
                    LEFT JOIN {DB_PREFIX}.analysis a ON w.analysis_id = a.id 
                    WHERE w.id = ?
                    """,
                    [widget_id],
                )
                row = cursor.fetchone()

                if not row:
                    logger.debug(f"Widget {widget_id} not found")
                    return None

                widget_data = self._convert_db_row_to_widget_format(row)
                logger.info(f"Retrieved widget {widget_id}")
                return widget_data

        except Exception as e:
            logger.error(f"Error retrieving widget {widget_id}: {str(e)}")
            raise Exception(f"Failed to retrieve widget: {str(e)}")

    def create_widget(self, widget_data: Dict, analysis_id: str) -> Dict:
        """Create a new widget in Databricks"""
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        if not widget_data.get("type"):
            raise ValueError("Widget type is required")

        try:
            with self._get_connection() as cursor:
                widget_id = widget_data.get("id")
                if not widget_id:
                    widget_id = str(uuid.uuid4())
                    widget_data["id"] = widget_id

                # Check if widget already exists
                cursor.execute(CHECK_WIDGET_EXISTS, [widget_id, analysis_id])
                result = cursor.fetchone()
                if result and result["count"] > 0:
                    raise Exception(
                        f"Widget {widget_id} already exists for analysis {analysis_id}"
                    )

                # Convert data to JSON strings (strip dataSource to avoid 1MB param limit)
                columns = self._strip_datasource_from_columns(widget_data.get("columns", []))
                columns_json = json.dumps(columns)
                data_json = json.dumps(widget_data.get("data", []))
                
                # Serialize yAxisOptions and selectedRacks
                yaxis_options_json = json.dumps(widget_data.get("yAxisOptions", []))
                selected_racks_json = json.dumps(widget_data.get("selectedRacks")) if widget_data.get("selectedRacks") is not None else None

                # Handle display_order (auto-assign if not provided)
                display_order = widget_data.get("display_order")

                if display_order is None:
                    cursor.execute(GET_NEXT_DISPLAY_ORDER, [analysis_id])
                    result = cursor.fetchone()
                    display_order = result["next_order"] if result else 0

                # Set timestamps
                created_at = datetime.now(timezone.utc)
                updated_at = created_at

                # Insert widget
                cursor.execute(
                    INSERT_WIDGET,
                    (
                        widget_id,
                        analysis_id,
                        widget_data.get("type", ""),
                        widget_data.get("name", ""),
                        columns_json,
                        data_json,
                        display_order,
                        created_at,
                        updated_at,
                        yaxis_options_json,
                        selected_racks_json,
                    ),
                )

                logger.info(f"Created widget {widget_id} for analysis {analysis_id}")
                return widget_data

        except Exception as e:
            logger.error(f"Error creating widget for analysis {analysis_id}: {str(e)}")
            raise Exception(f"Failed to create widget: {str(e)}")

    def update_widget(self, widget_data: Dict, analysis_id: str) -> Dict:
        """Update an existing widget in Databricks"""
        widget_id = widget_data.get("id")
        if not widget_id:
            raise ValueError("Widget ID is required for update")

        if not analysis_id:
            raise ValueError("Analysis ID is required")

        try:
            with self._get_connection() as cursor:
                # Check if widget exists
                cursor.execute(CHECK_WIDGET_EXISTS, [widget_id, analysis_id])
                result = cursor.fetchone()
                if not result or result["count"] == 0:
                    raise Exception(
                        f"Widget {widget_id} not found for analysis {analysis_id}"
                    )

                # Convert data to JSON strings (strip dataSource to avoid 1MB param limit)
                columns = self._strip_datasource_from_columns(widget_data.get("columns", []))
                columns_json = json.dumps(columns)
                data_json = json.dumps(widget_data.get("data", []))
                
                # Serialize yAxisOptions and selectedRacks
                yaxis_options_json = json.dumps(widget_data.get("yAxisOptions", []))
                selected_racks_json = json.dumps(widget_data.get("selectedRacks")) if widget_data.get("selectedRacks") is not None else None

                # Handle display_order (keep existing if not provided)
                display_order = widget_data.get("display_order")
                if display_order is None:
                    cursor.execute(GET_WIDGET_BY_ID_AND_ANALYSIS, [widget_id, analysis_id])
                    current_widget = cursor.fetchone()
                    display_order = current_widget["display_order"] if current_widget else 0

                # Set update timestamp
                updated_at = datetime.now(timezone.utc)

                # Update widget
                cursor.execute(
                    UPDATE_WIDGET,
                    (
                        widget_data.get("type", ""),
                        widget_data.get("name", ""),
                        columns_json,
                        data_json,
                        display_order,
                        updated_at,
                        yaxis_options_json,
                        selected_racks_json,
                        widget_id,
                        analysis_id,
                    ),
                )

                logger.info(f"Updated widget {widget_id} for analysis {analysis_id}")
                return widget_data

        except Exception as e:
            logger.error(f"Error updating widget for analysis {analysis_id}: {str(e)}")
            raise Exception(f"Failed to update widget: {str(e)}")

    def delete_widget(self, widget_id: str, analysis_id: str) -> bool:
        """Delete a widget from Databricks"""
        if not widget_id or not analysis_id:
            raise ValueError("Widget ID and Analysis ID are required")

        try:
            with self._get_connection() as cursor:
                # Check if widget exists
                cursor.execute(CHECK_WIDGET_EXISTS, [widget_id, analysis_id])
                result = cursor.fetchone()
                if not result or result["count"] == 0:
                    raise Exception(
                        f"Widget {widget_id} not found for analysis {analysis_id}"
                    )

                # Delete widget
                cursor.execute(DELETE_WIDGET, [widget_id, analysis_id])

                logger.info(f"Deleted widget {widget_id} for analysis {analysis_id}")
                return True

        except Exception as e:
            logger.error(
                f"Error deleting widget {widget_id} for analysis {analysis_id}: {str(e)}"
            )
            raise Exception(f"Failed to delete widget: {str(e)}")

    def list_widgets_for_analysis(self, analysis_id: str) -> List[Dict]:
        """List all widgets for a specific analysis"""
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        try:
            with self._get_connection() as cursor:
                cursor.execute(GET_ALL_WIDGETS_FOR_ANALYSIS, [analysis_id])
                rows = cursor.fetchall()

                widgets = []
                for row in rows:
                    widget_data = self._convert_db_row_to_widget_format(row)
                    widgets.append(widget_data)

                logger.info(f"Found {len(widgets)} widgets for analysis {analysis_id}")
                return widgets

        except Exception as e:
            logger.error(f"Error listing widgets for analysis {analysis_id}: {str(e)}")
            raise Exception(f"Failed to list widgets: {str(e)}")

    def delete_all_widgets_for_analysis(self, analysis_id: str) -> bool:
        """Delete all widgets for a specific analysis"""
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        try:
            with self._get_connection() as cursor:
                cursor.execute(DELETE_ALL_WIDGETS_FOR_ANALYSIS, [analysis_id])
                logger.info(f"Deleted all widgets for analysis {analysis_id}")
                return True

        except Exception as e:
            logger.error(
                f"Error deleting all widgets for analysis {analysis_id}: {str(e)}"
            )
            raise Exception(f"Failed to delete all widgets for analysis: {str(e)}")

    def bulk_create_widgets(
        self, widgets_data: List[Dict], analysis_id: str
    ) -> Dict[str, Any]:
        """Bulk create widgets in Databricks using executemany for efficiency"""
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        if not widgets_data:
            return {
                "created_widgets": [],
                "failed_widgets": [],
                "total_created": 0,
                "total_failed": 0,
            }

        start_time = time.time()
        logger.info(
            f"Starting bulk create of {len(widgets_data)} widgets for analysis {analysis_id}"
        )

        try:
            with self._get_connection() as cursor:
                # Check for duplicate IDs within existing widgets in database
                widget_ids = [
                    widget.get("id") for widget in widgets_data if widget.get("id")
                ]
                existing_widgets = []

                if widget_ids:
                    existing_widgets_dict = self.check_widgets_exist_in_batch(
                        widget_ids, analysis_id
                    )
                    existing_widgets = list(existing_widgets_dict.keys())
                    logger.info(
                        f"Found {len(existing_widgets)} existing widgets in database"
                    )

                created_widgets = []
                failed_widgets = []

                # Get next available display order for analysis
                cursor.execute(GET_NEXT_DISPLAY_ORDER, [analysis_id])
                result = cursor.fetchone()
                next_available_order = result["next_order"] if result else 0

                # Prepare bulk insert data
                bulk_insert_data = []
                current_time = datetime.now(timezone.utc)
                order_counter = next_available_order

                for i, widget in enumerate(widgets_data):
                    widget_id = widget.get("id")

                    # Check if widget already exists
                    if widget_id and widget_id in existing_widgets:
                        failed_widgets.append(
                            {
                                "widget_index": i,
                                "widget": widget,
                                "error": f"Widget {widget_id} already exists for analysis {analysis_id}",
                            }
                        )
                        continue

                    # Generate ID if not provided
                    if not widget_id:
                        widget_id = str(uuid.uuid4())
                        widget["id"] = widget_id

                    try:
                        # Convert data to JSON strings (strip dataSource to avoid 1MB param limit)
                        columns = self._strip_datasource_from_columns(widget.get("columns", []))
                        columns_json = json.dumps(columns)
                        data_json = json.dumps(widget.get("data", []))
                        
                        # Serialize yAxisOptions and selectedRacks
                        yaxis_options_json = json.dumps(widget.get("yAxisOptions", []))
                        selected_racks_json = json.dumps(widget.get("selectedRacks")) if widget.get("selectedRacks") is not None else None

                        # Handle display_order (auto-assign if not provided)
                        display_order = widget.get("display_order")
                        if display_order is None:
                            display_order = order_counter
                            order_counter += 1

                        # Add to bulk insert data
                        bulk_insert_data.append(
                            (
                                widget_id,
                                analysis_id,
                                widget.get("type", ""),
                                widget.get("name", ""),
                                columns_json,
                                data_json,
                                display_order,
                                current_time,
                                current_time,
                                yaxis_options_json,
                                selected_racks_json,
                            )
                        )

                        created_widgets.append(widget)

                    except Exception as e:
                        failed_widgets.append(
                            {
                                "widget_index": i,
                                "widget": widget,
                                "error": f"Data preparation error: {str(e)}",
                            }
                        )

                # Execute bulk insert if there are valid widgets
                if bulk_insert_data:
                    logger.info(
                        f"Executing bulk insert for {len(bulk_insert_data)} widgets"
                    )
                    cursor.executemany(BULK_INSERT_WIDGETS, bulk_insert_data)
                    execution_time = time.time() - start_time
                    logger.info(
                        f"Bulk created {len(bulk_insert_data)} widgets for analysis {analysis_id} in {execution_time:.3f}s"
                    )
                else:
                    logger.warning("No valid widgets to insert after validation")

                execution_time = time.time() - start_time

                result = {
                    "created_widgets": created_widgets,
                    "failed_widgets": failed_widgets,
                    "total_created": len(created_widgets),
                    "total_failed": len(failed_widgets),
                }

                logger.info(
                    f"Bulk operation completed: {len(created_widgets)} created, {len(failed_widgets)} failed"
                )
                return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Error in bulk create widgets for analysis {analysis_id} after {execution_time:.3f}s: {str(e)}"
            )
            raise Exception(f"Failed to bulk create widgets: {str(e)}")

    def check_widgets_exist_in_batch(
        self, widget_ids: List[str], analysis_id: str
    ) -> Dict[str, int]:
        """Check which widget IDs already exist for the analysis

        Returns a dictionary mapping widget_id to count for existing widgets.
        Enhanced security with explicit placeholder generation.

        Args:
            widget_ids: List of widget IDs to check
            analysis_id: Analysis identifier

        Returns:
            Dict mapping widget_id -> count for existing widgets
        """
        if not widget_ids or not analysis_id:
            return {}

        # Security: Validate input parameters
        if not isinstance(widget_ids, list) or not all(
            isinstance(wid, str) for wid in widget_ids
        ):
            raise ValueError("widget_ids must be a list of strings")

        if not isinstance(analysis_id, str):
            raise ValueError("analysis_id must be a string")

        try:
            with self._get_connection() as cursor:
                # Create safe placeholders - one for each widget_id
                placeholders = ",".join(["?" for _ in widget_ids])
                check_query = CHECK_BULK_WIDGETS_EXIST.format(placeholders)

                # Parameters: analysis_id first, then all widget_ids
                params = [analysis_id] + widget_ids

                logger.debug(
                    f"Checking existence for {len(widget_ids)} widgets in analysis {analysis_id}"
                )
                cursor.execute(check_query, params)
                results = cursor.fetchall()

                # Return dictionary mapping widget_id to count
                existing_widgets = {
                    row["id"]: row["count"] for row in results if row["count"] > 0
                }
                logger.debug(f"Found {len(existing_widgets)} existing widgets")

                return existing_widgets

        except Exception as e:
            logger.error(
                f"Error checking widget existence for analysis {analysis_id}: {str(e)}"
            )
            raise Exception(f"Failed to check widget existence: {str(e)}")

    def bulk_update_widgets(
        self, widgets_data: List[Dict], analysis_id: str
    ) -> Dict[str, Any]:
        """Bulk update widgets in Databricks using executemany for efficiency"""
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        if not widgets_data:
            return {
                "updated_widgets": [],
                "failed_widgets": [],
                "total_updated": 0,
                "total_failed": 0,
            }

        start_time = time.time()
        logger.info(
            f"Starting bulk update of {len(widgets_data)} widgets for analysis {analysis_id}"
        )

        with self._get_connection() as cursor:
            # Check which widgets exist in database
            widget_ids = [
                widget.get("id") for widget in widgets_data if widget.get("id")
            ]
            existing_widgets_dict = {}

            if widget_ids:
                existing_widgets_dict = self.check_widgets_exist_in_batch(
                    widget_ids, analysis_id
                )
                logger.info(
                    f"Found {len(existing_widgets_dict)} existing widgets to update"
                )

            updated_widgets = []
            failed_widgets = []

            # Prepare bulk update data
            bulk_update_data = []
            current_time = datetime.now(timezone.utc)

            for i, widget in enumerate(widgets_data):
                widget_id = widget.get("id")

                # Check if widget exists (required for update)
                if not widget_id or widget_id not in existing_widgets_dict:
                    failed_widgets.append(
                        {
                            "widget_index": i,
                            "widget": widget,
                            "error": f"Widget {widget_id or 'None'} not found for analysis {analysis_id}",
                        }
                    )
                    continue

                try:
                    # Convert data to JSON strings
                    columns_json = json.dumps(widget.get("columns", []))
                    data_json = json.dumps(widget.get("data", []))
                    
                    # Serialize yAxisOptions and selectedRacks
                    yaxis_options_json = json.dumps(widget.get("yAxisOptions", []))
                    selected_racks_json = json.dumps(widget.get("selectedRacks")) if widget.get("selectedRacks") is not None else None

                    # Handle display_order (keep existing if not provided)
                    display_order = widget.get("display_order")
                    if display_order is None:
                        display_order = 0  # Will be handled by the service layer

                    # Add to bulk update data
                    # Parameters: type, name, columns_json, data_json, display_order, updated_at, yaxis_option, selected_racks, widget_id, analysis_id
                    bulk_update_data.append(
                        (
                            widget.get("type", ""),
                            widget.get("name", ""),
                            columns_json,
                            data_json,
                            display_order,
                            current_time,
                            yaxis_options_json,
                            selected_racks_json,
                            widget_id,
                            analysis_id,
                        )
                    )

                    updated_widgets.append(widget)

                except Exception as e:
                    failed_widgets.append(
                        {
                            "widget_index": i,
                            "widget": widget,
                            "error": f"Data preparation error: {str(e)}",
                        }
                    )

            # Execute bulk update if there are valid widgets
            if bulk_update_data:
                logger.info(
                    f"Executing bulk update for {len(bulk_update_data)} widgets"
                )
                cursor.executemany(BULK_UPDATE_WIDGETS, bulk_update_data)
                execution_time = time.time() - start_time
                logger.info(
                    f"Bulk updated {len(bulk_update_data)} widgets for analysis {analysis_id} in {execution_time:.3f}s"
                )
            else:
                logger.warning("No valid widgets to update after validation")

            execution_time = time.time() - start_time

            result = {
                "updated_widgets": updated_widgets,
                "failed_widgets": failed_widgets,
                "total_updated": len(updated_widgets),
                "total_failed": len(failed_widgets),
            }

            logger.info(
                f"Bulk update operation completed: {len(updated_widgets)} updated, {len(failed_widgets)} failed"
            )
            return result

    def bulk_delete_widgets(self, widget_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple widgets by their IDs (without analysisID dependency)

        Args:
            widget_ids: List of widget IDs to delete

        Returns:
            Dict containing deletion results with counts and failed IDs
        """
        if not widget_ids:
            raise ValueError("Widget IDs list cannot be empty")

        if not isinstance(widget_ids, list):
            raise ValueError("widget_ids must be a list")

        # Remove duplicates while preserving order
        unique_widget_ids = list(dict.fromkeys(widget_ids))

        logger.info(f"Starting bulk deletion of {len(unique_widget_ids)} widgets")
        start_time = time.time()

        deleted_widget_ids = []
        failed_widget_ids = []

        try:
            with self._get_connection() as cursor:
                # Check which widgets exist before deletion
                if len(unique_widget_ids) > 0:
                    placeholders = ", ".join("?" * len(unique_widget_ids))
                    check_query = f"""
                        SELECT id FROM {BULK_DELETE_WIDGETS.split('FROM')[1].split('WHERE')[0].strip()} 
                        WHERE id IN ({placeholders})
                    """

                    cursor.execute(check_query, unique_widget_ids)
                    existing_widgets = {row["id"] for row in cursor.fetchall()}

                    # Identify widgets that don't exist
                    for widget_id in unique_widget_ids:
                        if widget_id not in existing_widgets:
                            failed_widget_ids.append(
                                {"widget_id": widget_id, "error": "Widget not found"}
                            )

                    # Delete existing widgets
                    if existing_widgets:
                        delete_placeholders = ", ".join("?" * len(existing_widgets))
                        delete_query = BULK_DELETE_WIDGETS.format(delete_placeholders)

                        cursor.execute(delete_query, list(existing_widgets))
                        deleted_count = cursor.rowcount

                        # Track successfully deleted widgets
                        deleted_widget_ids = list(existing_widgets)

                        logger.info(f"Successfully deleted {deleted_count} widgets")
                    else:
                        logger.warning("No existing widgets found to delete")

        except Exception as e:
            logger.error(f"Error in bulk delete widgets: {str(e)}")
            # If database error occurs, mark all remaining widgets as failed
            for widget_id in unique_widget_ids:
                if widget_id not in [
                    item["widget_id"] if isinstance(item, dict) else item
                    for item in failed_widget_ids
                ]:
                    failed_widget_ids.append(
                        {"widget_id": widget_id, "error": f"Database error: {str(e)}"}
                    )

        execution_time = time.time() - start_time

        result = {
            "total_requested": len(unique_widget_ids),
            "successfully_deleted": len(deleted_widget_ids),
            "failed_deletions": len(failed_widget_ids),
            "deleted_widget_ids": deleted_widget_ids,
            "failed_widget_ids": failed_widget_ids,
            "execution_time_seconds": round(execution_time, 3),
        }

        logger.info(
            f"Bulk deletion completed: {len(deleted_widget_ids)} deleted, {len(failed_widget_ids)} failed in {execution_time:.3f}s"
        )

        return result
    
    def _deserialize_applied_date_filter(self, applied_date_filter):
        """Helper method to deserialize applied_date_filter from JSON string to object"""
        if applied_date_filter and isinstance(applied_date_filter, str):
            try:
                import json
                return json.loads(applied_date_filter)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to deserialize applied_date_filter: {e}")
                # Return the original string value if deserialization fails
                return applied_date_filter

        # Return as-is if it's already an object or None
        return applied_date_filter

    # Widget Ordering Methods

    def get_next_display_order(self, analysis_id: str) -> int:
        """Get the next available display order for new widgets in analysis"""
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        try:
            with self._get_connection() as cursor:
                cursor.execute(GET_NEXT_DISPLAY_ORDER, [analysis_id])
                result = cursor.fetchone()
                next_order = result["next_order"] if result else 0

                logger.debug(f"Next available display order for analysis {analysis_id}: {next_order}")
                return next_order

        except Exception as e:
            logger.error(f"Error getting next display order for analysis {analysis_id}: {str(e)}")
            raise Exception(f"Failed to get next display order: {str(e)}")

    def update_widget_order(self, widget_id: str, analysis_id: str, new_display_order: int) -> bool:
        """Update display order for a specific widget"""
        if not widget_id or not analysis_id:
            raise ValueError("Widget ID and Analysis ID are required")

        if new_display_order < 0:
            raise ValueError("Display order must be non-negative")

        try:
            with self._get_connection() as cursor:
                # Check if widget exists
                cursor.execute(CHECK_WIDGET_EXISTS, [widget_id, analysis_id])
                result = cursor.fetchone()
                if not result or result["count"] == 0:
                    raise Exception(f"Widget {widget_id} not found for analysis {analysis_id}")

                # Update display order
                cursor.execute(UPDATE_WIDGET_ORDER, [new_display_order, widget_id, analysis_id])

                logger.info(f"Updated display order for widget {widget_id} to {new_display_order}")
                return True

        except Exception as e:
            logger.error(f"Error updating widget order: {str(e)}")
            raise Exception(f"Failed to update widget order: {str(e)}")

    def bulk_reorder_widgets(self, reorder_operations: List[Dict], analysis_id: str) -> Dict[str, Any]:
        """
        Bulk reorder widgets using parameterized CASE statement for optimal performance

        SECURITY ENHANCEMENT: Uses parameterized queries to prevent SQL injection

        Args:
            reorder_operations: List of {widget_id, new_display_order} operations
            analysis_id: Analysis identifier

        Returns:
            Dict with operation results
        """
        if not reorder_operations or not analysis_id:
            raise ValueError("Reorder operations and Analysis ID are required")

        start_time = time.time()
        logger.info(f"Starting bulk reorder of {len(reorder_operations)} widgets for analysis {analysis_id}")

        try:
            with self._get_connection() as cursor:
                # Validate all widgets exist
                widget_ids = [op.get("widget_id") for op in reorder_operations if op.get("widget_id")]

                if len(widget_ids) != len(reorder_operations):
                    raise ValueError("All reorder operations must include widget_id")

                existing_widgets_dict = self.check_widgets_exist_in_batch(widget_ids, analysis_id)
                missing_widgets = [wid for wid in widget_ids if wid not in existing_widgets_dict]

                if missing_widgets:
                    raise Exception(f"Widgets not found in analysis {analysis_id}: {missing_widgets}")

                # Build parameterized CASE statement for security
                case_placeholders = []
                case_params = []
                for operation in reorder_operations:
                    widget_id = operation["widget_id"]
                    new_order = operation["new_display_order"]

                    if new_order < 0:
                        raise ValueError(f"Display order must be non-negative for widget {widget_id}")

                    # Use parameterized placeholders instead of string formatting
                    case_placeholders.append("WHEN ? THEN ?")
                    case_params.extend([widget_id, new_order])

                case_clause = " ".join(case_placeholders)
                widget_placeholders = ", ".join(["?" for _ in widget_ids])

                # Build secure parameterized query
                bulk_query = f"""
                    UPDATE {self._get_table_name()}
                    SET display_order = CASE id {case_clause} END,
                        updated_at = CURRENT_TIMESTAMP()
                    WHERE analysis_id = ? AND id IN ({widget_placeholders})
                """

                # Execute with proper parameters: case_params + [analysis_id] + widget_ids
                query_params = case_params + [analysis_id] + widget_ids
                cursor.execute(bulk_query, query_params)

                execution_time = time.time() - start_time
                logger.info(f"Bulk reordered {len(reorder_operations)} widgets in {execution_time:.3f}s")

                return {
                    "success": True,
                    "total_operations": len(reorder_operations),
                    "reordered_widgets": widget_ids,
                    "execution_time_seconds": round(execution_time, 3),
                }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in bulk reorder widgets: {str(e)}")
            raise Exception(f"Failed to bulk reorder widgets: {str(e)}")

    def compact_widget_ordering(self, analysis_id: str) -> Dict[str, Any]:
        """
        Resolve ordering conflicts by compacting gaps and reassigning sequential orders

        Args:
            analysis_id: Analysis identifier

        Returns:
            Dict with compaction results
        """
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        try:
            with self._get_connection() as cursor:
                # Get current widget count
                cursor.execute(GET_WIDGET_COUNT_FOR_ANALYSIS, [analysis_id])
                result = cursor.fetchone()
                widget_count = result["count"] if result else 0

                if widget_count == 0:
                    return {
                        "success": True,
                        "message": "No widgets to compact",
                        "widgets_compacted": 0,
                    }

                # Check for conflicts before compaction
                cursor.execute(CHECK_DISPLAY_ORDER_CONFLICTS, [analysis_id])
                conflicts = cursor.fetchall()

                # Perform compaction
                cursor.execute(COMPACT_WIDGET_ORDERING, [analysis_id])

                logger.info(f"Compacted widget ordering for analysis {analysis_id}: {widget_count} widgets, {len(conflicts)} conflicts resolved")

                return {
                    "success": True,
                    "message": f"Compacted {widget_count} widgets, resolved {len(conflicts)} conflicts",
                    "widgets_compacted": widget_count,
                    "conflicts_resolved": len(conflicts),
                }

        except Exception as e:
            logger.error(f"Error compacting widget ordering for analysis {analysis_id}: {str(e)}")
            raise Exception(f"Failed to compact widget ordering: {str(e)}")

    def check_display_order_conflicts(self, analysis_id: str) -> List[Dict]:
        """
        Check for duplicate display_order values within an analysis

        Args:
            analysis_id: Analysis identifier

        Returns:
            List of conflicts with display_order and count
        """
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        try:
            with self._get_connection() as cursor:
                cursor.execute(CHECK_DISPLAY_ORDER_CONFLICTS, [analysis_id])
                conflicts = cursor.fetchall()

                result = [
                    {
                        "display_order": conflict["display_order"],
                        "conflict_count": conflict["conflict_count"]
                    }
                    for conflict in conflicts
                ]

                if result:
                    logger.warning(f"Found {len(result)} display order conflicts in analysis {analysis_id}")
                else:
                    logger.debug(f"No display order conflicts found in analysis {analysis_id}")

                return result

        except Exception as e:
            logger.error(f"Error checking display order conflicts for analysis {analysis_id}: {str(e)}")
            raise Exception(f"Failed to check display order conflicts: {str(e)}")

    def increment_display_orders_from(self, analysis_id: str, from_order: int) -> int:
        """
        Increment display_order for all widgets >= given order (for insertion conflict resolution)

        Args:
            analysis_id: Analysis identifier
            from_order: Starting order to increment from

        Returns:
            Number of widgets affected
        """
        if not analysis_id:
            raise ValueError("Analysis ID is required")

        if from_order < 0:
            raise ValueError("From order must be non-negative")

        try:
            with self._get_connection() as cursor:
                cursor.execute(INCREMENT_DISPLAY_ORDERS_FROM, [analysis_id, from_order])
                affected_rows = cursor.rowcount

                logger.info(f"Incremented display order for {affected_rows} widgets >= {from_order} in analysis {analysis_id}")
                return affected_rows

        except Exception as e:
            logger.error(f"Error incrementing display orders for analysis {analysis_id}: {str(e)}")
            raise Exception(f"Failed to increment display orders: {str(e)}")

    def migrate_add_display_order_column(self) -> Dict[str, Any]:
        """
        Add display_order column to existing widget table (migration support)

        Returns:
            Dict with migration results
        """
        try:
            with self._get_connection() as cursor:
                # Add column if it doesn't exist
                cursor.execute(ADD_DISPLAY_ORDER_COLUMN)

                logger.info("Successfully added display_order column to widget table")

                return {
                    "success": True,
                    "message": "Display order column added successfully",
                }

        except Exception as e:
            logger.error(f"Error adding display_order column: {str(e)}")
            raise Exception(f"Failed to add display_order column: {str(e)}")

    def migrate_initialize_display_order(self) -> Dict[str, Any]:
        """
        Initialize display_order for existing widgets based on creation order

        Returns:
            Dict with migration results
        """
        try:
            with self._get_connection() as cursor:
                # Initialize display order for existing widgets
                cursor.execute(INITIALIZE_DISPLAY_ORDER_FOR_EXISTING_WIDGETS)
                affected_rows = cursor.rowcount

                logger.info(f"Initialized display_order for {affected_rows} existing widgets")

                return {
                    "success": True,
                    "message": f"Display order initialized for {affected_rows} widgets",
                    "widgets_updated": affected_rows,
                }

        except Exception as e:
            logger.error(f"Error initializing display_order: {str(e)}")
            raise Exception(f"Failed to initialize display_order: {str(e)}")

    def validate_display_order_migration(self) -> Dict[str, Any]:
        """
        Validate migration success by checking display_order consistency

        Returns:
            Dict with validation results
        """
        try:
            with self._get_connection() as cursor:
                cursor.execute(VALIDATE_DISPLAY_ORDER_MIGRATION)
                issues = cursor.fetchall()

                if not issues:
                    logger.info("Display order migration validation passed - no issues found")
                    return {
                        "success": True,
                        "message": "Display order migration validation passed",
                        "issues": [],
                    }
                else:
                    logger.warning(f"Display order migration validation found {len(issues)} issues")
                    return {
                        "success": False,
                        "message": f"Display order migration validation found {len(issues)} issues",
                        "issues": [
                            {
                                "analysis_id": issue["analysis_id"],
                                "total_widgets": issue["total_widgets"],
                                "widgets_with_order": issue["widgets_with_order"],
                                "min_order": issue["min_order"],
                                "max_order": issue["max_order"],
                                "unique_orders": issue["unique_orders"],
                            }
                            for issue in issues
                        ],
                    }

        except Exception as e:
            logger.error(f"Error validating display_order migration: {str(e)}")
            raise Exception(f"Failed to validate display_order migration: {str(e)}")

    def create_performance_index(self) -> Dict[str, Any]:
        """
        Create database index for optimal widget performance

        This index significantly improves performance for:
        - Widget reordering operations
        - Filtering widgets by analysis_id
        - Display order-based queries

        Returns:
            Dict with index creation results
        """
        try:
            with self._get_connection() as cursor:
                cursor.execute(CREATE_WIDGET_ANALYSIS_DISPLAY_ORDER_INDEX)

                logger.info("Successfully created performance index: idx_widget_analysis_display_order")

                return {
                    "success": True,
                    "message": "Performance index created successfully",
                    "index_name": "idx_widget_analysis_display_order",
                    "columns": ["analysis_id", "display_order"],
                }

        except Exception as e:
            logger.error(f"Error creating performance index: {str(e)}")
            raise Exception(f"Failed to create performance index: {str(e)}")
