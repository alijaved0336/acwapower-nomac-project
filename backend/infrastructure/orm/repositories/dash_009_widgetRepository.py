import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pyasn1_modules.rfc3279 import primeCurve

from config.databricks_connector import get_databricks_connector
from config.databricks_sql_queries import (
    INSERT_HEATMAP_WIDGET,
    UPDATE_HEATMAP_WIDGET,
    UPDATE_HEATMAP_WIDGET_NO_PUMP,
    GET_HEATMAP_WIDGET_BY_USER_SITE_PUMP,
    CHECK_HEATMAP_WIDGET_EXISTS,
    CHECK_HEATMAP_WIDGET_EXISTS_NO_PUMP,
    GET_HEATMAP_WIDGET_BY_USER_SITE
)
import uuid

logger = logging.getLogger(__name__)


class HeatmapWidgetsRepository:
    """
    Repository for heatmap widgets data access layer.
    Uses Databricks with connection-per-operation pattern.
    """

    def __init__(self):
        # self.connector = get_databricks_connector()
        logger.debug("HeatmapWidgetsRepository initialized")

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
        """Open a fresh Databricks connection each time (autocommit mode)"""
        connection = None
        cursor = None
        try:
            connection = get_databricks_connector()  # :white_check_mark: open new connection each time
            if hasattr(connection, "autocommit"):
                connection.autocommit = True

            cursor = connection.cursor()
            yield cursor

        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise

        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if connection:
                try:
                    connection.close()
                except Exception:
                    pass

    def _get_table_name(self) -> str:
        """Get the fully qualified table name"""
        # Assuming same database structure as analysis widgets
        # Format: catalog.schema.widget_heatmaps
        return f"{self.connector.catalog}.{self.connector.schema}.widget_heatmaps"

    def get_heatmap_widget(self, site_id: str, pump_id: str, user_id: str, page: str) -> Optional[Dict]:
        """
        Retrieve a single heatmap widget by ID and user_id

        Args:
            widget_id: Widget identifier
            user_id: User identifier

        Returns:
            Widget dictionary or None if not found
        """
        try:

            with self._get_connection() as cursor:
                if pump_id and pump_id.strip():
                    cursor.execute(GET_HEATMAP_WIDGET_BY_USER_SITE_PUMP, [user_id, site_id, pump_id, page])
                else:
                    cursor.execute(GET_HEATMAP_WIDGET_BY_USER_SITE, [user_id, site_id, page])

                result = cursor.fetchone()

                if not result:
                    logger.debug(
                        f"Widget {user_id} not found for analysis {user_id}"
                    )
                    return None

                return self._convert_db_row_to_heatmap_widget_format(result)

        except Exception as e:
            logger.error(f"Error fetching heatmap widget {user_id}: {str(e)}")
            raise

    def create_or_update_heatmap_widget(self, widget_data: Dict, user_id: str) -> Dict:
        """
        Create a new heatmap widget or update if it already exists

        Args:
            widget_data: Widget configuration data
            user_id: User identifier

        Returns:
            Created or updated widget dictionary
        """
        if not user_id:
            raise ValueError("user_id is required to create a heatmap widget")

        try:
            with self._get_connection() as cursor:
                widget_id = widget_data.get("id")
                site_id = widget_data.get("site_id")
                pump_id = widget_data.get("pump_id")
                # Normalize empty string to None
                if pump_id and not pump_id.strip():
                    pump_id = None
                page = widget_data.get("page")
                if not widget_id:
                    widget_id = str(uuid.uuid4())
                    widget_data["id"] = widget_id  # Set back to input data

                columns = self._strip_datasource_from_columns(widget_data.get("columns", []))
                columns_json = json.dumps(columns)
                updated_at = datetime.now(timezone.utc)

                # Check if widget exists - use appropriate query based on pump_id
                if pump_id and pump_id.strip():
                    cursor.execute(CHECK_HEATMAP_WIDGET_EXISTS, [user_id, site_id, pump_id, page])
                else:
                    cursor.execute(CHECK_HEATMAP_WIDGET_EXISTS_NO_PUMP, [user_id, site_id, page])
                result = cursor.fetchone()

                widget_exists = result and result[0] > 0

                if widget_exists:
                    logger.info(f"Widget {widget_id} already exists, updating...")

                    # Update existing widget - use appropriate query based on pump_id
                    if pump_id and pump_id.strip():
                        cursor.execute(
                            UPDATE_HEATMAP_WIDGET,
                            [
                                columns_json,
                                updated_at,
                                user_id,
                                site_id,
                                pump_id,
                                page
                            ],
                        )
                    else:
                        cursor.execute(
                            UPDATE_HEATMAP_WIDGET_NO_PUMP,
                            [
                                columns_json,
                                updated_at,
                                user_id,
                                site_id,
                                page
                            ],
                        )

                    logger.info(f"Updated heatmap widget {widget_id} for user {user_id}")

                else:
                    logger.info(f"Widget {widget_id} not found, creating new one...")

                    widget_id = str(uuid.uuid4())
                    created_at = datetime.now(timezone.utc)

                    # Insert new widget
                    cursor.execute(
                        INSERT_HEATMAP_WIDGET,
                        [
                            widget_id,
                            user_id,
                            site_id,
                            pump_id,
                            columns_json,
                            page,
                            created_at,
                            updated_at
                        ],
                    )

                    logger.info(f"Created heatmap widget {widget_id} for user {user_id}")

            # Return created/updated widget after closing connection
            return self.get_heatmap_widget(site_id, pump_id, user_id, page)

        except Exception as e:
            logger.error(f"Error creating/updating heatmap widget: {str(e)}")
            raise Exception(f"Failed to create/update heatmap widget: {str(e)}")

    def _convert_db_row_to_heatmap_widget_format(self, row: Dict) -> Dict:
        """Convert database row from widget_heatmaps table into heatmap widget format"""

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
            """Safely extract value from row regardless of dict or object format"""
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
            result_dict = {
                "site_id": safe_str(_get_row_value(row, "site_id", "")),
                "columns": safe_json_loads(_get_row_value(row, "columns")),
                "page": safe_str(_get_row_value(row, "page")),
            }
            if getattr(row, "pump_id"):
                result_dict["pump_id"] = safe_str(_get_row_value(row, "pump_id"))
            return result_dict

        except Exception as e:
            logger.error(f"Error converting heatmap widget row: {str(e)}")
            return {
                "site_id": "",
                "pump_id": "",
                "columns": []
            }