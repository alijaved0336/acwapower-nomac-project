import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.http import Http404

from config.databricks_connector import get_databricks_connector
from config.databricks_sql_queries import CHECK_ANALYSIS_EXISTS
from constants import ClickHouseColumnPatterns
from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.orm.repositories.widgets import WidgetsRepository
from infrastructure.orm.repositories.analysis import AnalysisRepo
from infrastructure.services.analysis.analysis_crud_operations import (
    AnalysisCrudOperations,
)
from infrastructure.services.multiSiteColumnService import MultiSiteColumnDataService, ColumnRequest
from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService
from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig

logger = logging.getLogger(__name__)


class WidgetsService:

    def __init__(self):
        # Repository instances are now lightweight since they use connection-per-operation
        self.cache_service = CacheService()
        self.clickhouse_service = ClickHouseADLSService()
        logger.info("WidgetsService initialized with Redis caching support")

    def _get_repository(self) -> WidgetsRepository:
        """Get a fresh repository instance for each operation"""
        return WidgetsRepository()

    def _get_analysis_repository(self) -> AnalysisRepo:
        """Get a fresh repository instance for each operation"""
        return AnalysisRepo()

    def _get_analysis_service(self) -> AnalysisCrudOperations:
        """Get analysis service instance for operations"""
        return AnalysisCrudOperations()

    def _normalize_timestamp_for_matching(self, timestamp) -> str:
        """
        Normalize timestamp to a common format for matching.
        Handles ISO format, datetime strings, and other formats.
        Converts to "YYYY-MM-DD HH:MM:SS" format for consistent matching.
        """
        if not timestamp:
            return ""
        
        timestamp_str = str(timestamp)
        
        # Remove timezone info and microseconds for matching
        # Handle ISO format: "2025-05-31T20:59:00" or "2025-05-31T20:59:00+00:00"
        if 'T' in timestamp_str:
            # Split on T, take date and time parts
            parts = timestamp_str.split('T')
            if len(parts) == 2:
                date_part = parts[0]
                time_part = parts[1].split('+')[0].split('-')[0].split('Z')[0].split('.')[0]
                # Ensure time part has seconds (HH:MM:SS format)
                time_parts = time_part.split(':')
                if len(time_parts) == 2:
                    time_part = f"{time_part}:00"
                return f"{date_part} {time_part}"
        
        # Handle space-separated format: "2025-05-31 20:59:00"
        if ' ' in timestamp_str:
            parts = timestamp_str.split(' ')
            if len(parts) >= 2:
                date_part = parts[0]
                time_part = parts[1].split('+')[0].split('.')[0]
                # Ensure time part has seconds (HH:MM:SS format)
                time_parts = time_part.split(':')
                if len(time_parts) == 2:
                    time_part = f"{time_part}:00"
                return f"{date_part} {time_part}"
        
        # Fallback: try to extract date and time
        cleaned = timestamp_str.split('+')[0].split('.')[0].split('Z')[0]
        return cleaned

    # _validate_analysis_exists method was removed for consistency
    # Both single and bulk widget operations now have consistent behavior
    # Database constraints will handle any invalid analysis IDs if needed

    def _format_error_response(
        self,
        validation_errors: List[Dict],
        creation_errors: List[Dict],
        status_type: str,
    ) -> Dict:
        """Format standardized error response

        Args:
            validation_errors: List of validation error dictionaries
            creation_errors: List of creation error dictionaries
            status_type: Type of error ('validation', 'business', 'system')

        Returns:
            Standardized error response dictionary
        """
        return {
            "success": False,
            "status_type": status_type,  # 'validation', 'business', 'system'
            "validation_errors": validation_errors or [],
            "creation_errors": creation_errors or [],
            "total_errors": len(validation_errors or []) + len(creation_errors or []),
        }

    def get_widget(
        self,
        widget_id: str,
        analysis_id: str,
        authenticated_user_id: str,
        authenticated_user_email: str = None
    ):
        """
        Retrieve a widget by ID for a specific analysis with access control
        Returns: dict with widget data or raises exception if not found
        """
        try:
            # STEP 1: Import access control utilities
            from infrastructure.services.analysis.analysis_crud_operations import (
                AnalysisCrudOperations
            )

            analysis_service = AnalysisCrudOperations()

            # STEP 2: Check super admin status
            is_super_admin, role_type = analysis_service._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            # STEP 3: Verify access to analysis
            analysisRepo = self._get_analysis_repository()
            analysis = analysisRepo.get_analysis_by_id_with_access_control(
                analysis_id=analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin
            )

            if not analysis:
                raise Exception("Analysis not found or access denied")

            # STEP 4: Audit logging for super admin (REQUIRED)
            if is_super_admin:
                user_id_match = analysis.get("user_id") == authenticated_user_id
                email_match = authenticated_user_email and analysis.get("user_id") == authenticated_user_email

                if not (user_id_match or email_match) and analysis.get("visibility") == "private":
                    logger.info(
                        f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                        f"({authenticated_user_email}) accessed widget {widget_id} in private analysis {analysis_id} "
                        f"owned by {analysis.get('user_id')} "
                        f"(analysis name: '{analysis.get('name', 'N/A')}')"
                    )

            # STEP 5: Fetch widget (after access control passes)
            repository = self._get_repository()
            widget = repository.get_widget(widget_id, analysis_id)

            if not widget:
                raise Exception(
                    f"Widget {widget_id} not found for analysis {analysis_id}"
                )

            # Fetch column data from ClickHouse (similar to get_all_widgets_for_analysis)
            columns = widget.get("columns", [])
            
            if columns:
                # Get analysis data for date filters
                analysis_data = widget.get("analysis_data", {})
                from_date = None
                to_date = None
                rack = None
                if isinstance(analysis_data.get("applied_date_filter"), dict):
                    from_date = analysis_data.get("applied_date_filter", {}).get("from_date")
                    to_date = analysis_data.get("applied_date_filter", {}).get("to_date")
                    rack = analysis_data.get("applied_date_filter", {}).get("rack")
                    # Handle rack filter - convert to list if it's a string, or keep as list
                    if rack:
                        if isinstance(rack, str):
                            rack = [rack]
                        elif isinstance(rack, list):
                            rack = rack  # Keep as list
                        else:
                            rack = None
                
                # Build column request
                column_request = [
                    {
                        'siteName': column.get("siteName", ""),
                        'tableName': column.get("tableName", ""),
                        'columnName': column.get("columnName", ""),
                        'columnType': column.get("columnType", "double")
                    }
                    for column in columns
                    if column.get("siteName") and column.get("tableName") and column.get("columnName")
                ]
                
                if column_request:
                    logger.debug(f"Fetching data for {len(column_request)} columns for widget {widget_id}")
                    
                    # Convert rack list to comma-separated string for get_column_data_sources
                    rack_param = None
                    if rack:
                        if isinstance(rack, list):
                            rack_param = ",".join(rack)
                        else:
                            rack_param = str(rack)
                    
                    column_responses_result = self.clickhouse_service.get_column_data_sources(
                        columns_list=column_request,
                        from_date=from_date,
                        to_date=to_date,
                        rack=rack_param
                    )
                    
                    # Extract column_data from the response (get_column_data_sources returns dict with column_data and metadata)
                    column_responses = column_responses_result.get("column_data", []) if isinstance(column_responses_result, dict) else column_responses_result
                    
                    logger.debug(f"Received {len(column_responses)} column responses from ClickHouse for widget {widget_id}")
                    
                    # Create columns array with column metadata and data
                    columns_data = []
                    for i, column_response in enumerate(column_responses):
                        # Find the corresponding column metadata
                        column_metadata = columns[i] if i < len(columns) else {}
                        
                        datasource = column_response.get("dataSource", [])
                        logger.debug(f"Column {i}: {column_response.get('columnName')} has {len(datasource)} data points")
                        
                        column_data = {
                            "columnType": column_response.get("columnType"),
                            "siteName": column_metadata.get("siteName", ""),
                            "tableName": column_metadata.get("tableName", ""),
                            "columnName": column_response.get("columnName"),
                            "dataSource": datasource,
                            "racks": []  # Initialize empty racks array for each column
                        }
                        columns_data.append(column_data)
                    
                    # Update widget with fetched column data
                    widget["columns"] = columns_data

                    # Detect and retrieve racks for this widget
                    rack_timestamp_map = {}
                    try:
                        from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
                        clickhouse_repo = ClickHouseRepository()

                        # Find DateTime column to get timestamps for alignment
                        datetime_column = None
                        for col_data in columns_data:
                            if col_data.get("columnName", "").lower() in ["datetime", "timestamp"]:
                                datetime_column = col_data
                                break
                        
                        # Get timestamps from DateTime column if available
                        timestamps = []
                        if datetime_column:
                            timestamps = datetime_column.get("dataSource", [])
                            logger.debug(f"Found {len(timestamps)} timestamps from DateTime column for rack alignment")

                        # Check tables for rack columns (use first table that has racks)
                        for i, column_response in enumerate(column_responses):
                            column_metadata = columns[i] if i < len(columns) else {}
                            site_name = column_metadata.get("siteName")
                            table_name = column_metadata.get("tableName")

                            if site_name and table_name:
                                # Get ClickHouse table name
                                clickhouse_table_name = clickhouse_repo.get_clickhouse_table_name(site_name, table_name)

                                if clickhouse_table_name:
                                    # Get rack columns for this table
                                    rack_columns = clickhouse_repo.get_rack_columns_for_table(clickhouse_table_name)

                                    if rack_columns:
                                        # Get rack data with timestamps (same date range and rack filter as other columns)
                                        rack_data_list = clickhouse_repo.get_rack_data_with_timestamps(
                                            clickhouse_table_name,
                                            rack_columns,
                                            from_date=from_date,
                                            to_date=to_date,
                                            rack=rack if rack else None
                                        )

                                        if timestamps and rack_data_list:
                                            # Align rack values with column data timestamps
                                            # Create a map of timestamp -> rack value from the first rack column
                                            if rack_data_list:
                                                first_rack_data = rack_data_list[0]
                                                for dp in first_rack_data.get("data", []):
                                                    rack_timestamp = dp.get("timestamp")
                                                    rack_value = dp.get("value")
                                                    if rack_timestamp and rack_value:
                                                        # Normalize timestamp format for matching
                                                        normalized_ts = self._normalize_timestamp_for_matching(rack_timestamp)
                                                        rack_timestamp_map[normalized_ts] = str(rack_value).strip()
                                            
                                            logger.debug(f"Created rack timestamp map with {len(rack_timestamp_map)} entries for single widget {widget_id}")
                                        else:
                                            logger.warning(f"No timestamps or rack data available for single widget {widget_id}")

                                        if rack_timestamp_map:
                                            logger.debug(f"Found rack data for single widget {widget_id} from table {clickhouse_table_name}")
                                            break  # Use racks from first table that has them
                    except Exception as rack_error:
                        logger.warning(f"Error retrieving racks for single widget {widget_id}: {rack_error}")
                        rack_timestamp_map = {}

                    # Add racks array to each column (matching timestamps)
                    if timestamps and rack_timestamp_map:
                        for column_data in columns_data:
                            # Skip DateTime column - it doesn't need racks
                            if column_data.get("columnName", "").lower() in ["datetime", "timestamp"]:
                                continue
                            
                            # Get timestamps for this column (should match DateTime column)
                            column_racks = []
                            for timestamp in timestamps:
                                normalized_ts = self._normalize_timestamp_for_matching(timestamp)
                                rack_value = rack_timestamp_map.get(normalized_ts)
                                column_racks.append(rack_value if rack_value else "NaN")
                            
                            # Ensure racks array matches dataSource length
                            if len(column_racks) != len(column_data.get("dataSource", [])):
                                logger.warning(f"Rack count mismatch for column {column_data.get('columnName')}: {len(column_racks)} racks vs {len(column_data.get('dataSource', []))} data points")
                                # Trim or pad to match
                                data_length = len(column_data.get("dataSource", []))
                                if len(column_racks) > data_length:
                                    column_racks = column_racks[:data_length]
                                else:
                                    column_racks.extend(["NaN"] * (data_length - len(column_racks)))
                            
                            column_data["racks"] = column_racks
                            logger.debug(f"Added {len(column_racks)} rack values to column {column_data.get('columnName')}")

            return widget

        except Exception as e:
            logger.error(f"Error in get_widget service: {str(e)}")
            raise

    def get_all_widgets_for_analysis(
        self,
        analysis_id: str,
        authenticated_user_id: str,
        authenticated_user_email: str = None
    ):
        """
        Get all widgets for a specific analysis with access control and Redis caching optimization
        Returns: restructured response with analysis data at root level
        """
        try:
            # STEP 1: Import access control utilities
            from infrastructure.services.analysis.analysis_crud_operations import (
                AnalysisCrudOperations
            )

            analysis_service = AnalysisCrudOperations()

            # STEP 2: Check super admin status
            is_super_admin, role_type = analysis_service._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            # STEP 3: Verify access to analysis
            analysisRepo = self._get_analysis_repository()
            analysis = analysisRepo.get_analysis_by_id_with_access_control(
                analysis_id=analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin
            )

            if not analysis:
                raise Http404({"message": "Analysis not found or access denied"})

            # STEP 4: Audit logging for super admin (REQUIRED)
            if is_super_admin:
                user_id_match = analysis.get("user_id") == authenticated_user_id
                email_match = authenticated_user_email and analysis.get("user_id") == authenticated_user_email

                if not (user_id_match or email_match) and analysis.get("visibility") == "private":
                    logger.info(
                        f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                        f"({authenticated_user_email}) accessed private analysis {analysis_id} "
                        f"owned by {analysis.get('user_id')} "
                        f"(analysis name: '{analysis.get('name', 'N/A')}')"
                    )

            # STEP 5: Check Redis cache for widget data (after access control)
            cache_key = f"widgets_analysis_{analysis_id}"
            cached_result = self.cache_service.get(cache_key, prefix="parquet_data")

            if cached_result:
                logger.info(f"Cache HIT: Retrieved widgets for analysis {analysis_id} from Redis cache")
                return cached_result

            logger.info(f"Cache MISS: Processing widgets for analysis {analysis_id} - will cache result")

            # STEP 6: Fetch widgets (after access control passes)
            repository = self._get_repository()
            widgets_data = repository.list_widgets_for_analysis(analysis_id)

            # Extract analysis data from first widget (all have same analysis data)
            analysis_info = {}
            widget_list = []

            if widgets_data:
                # Get analysis data from first widget
                first_widget = widgets_data[0]
                if first_widget.get("analysis_data"):
                    analysis_info = first_widget["analysis_data"]
                    from_date = None
                    to_date = None
                    rack = None
                    if isinstance(analysis_info["applied_date_filter"], dict):
                        from_date = analysis_info.get("applied_date_filter", {}).get("from_date")
                        to_date = analysis_info.get("applied_date_filter", {}).get("to_date")
                        rack = analysis_info.get("applied_date_filter", {}).get("rack")
                        # Handle rack filter - convert to list if it's a string, or keep as list
                        if rack:
                            if isinstance(rack, str):
                                rack = [rack]
                            elif isinstance(rack, list):
                                rack = rack  # Keep as list
                            else:
                                rack = None

                # Process widgets in parallel for better performance with proper response structure
                import concurrent.futures
                from concurrent.futures import ThreadPoolExecutor
                
                def process_widget(widget):
                    """Process a single widget's data with caching"""
                    try:
                        columns = widget.get("columns", [])

                        # Check cache for individual widget data first
                        widget_cache_key = f"widget_{widget.get('id')}_{from_date}_{to_date}_{rack}"
                        cached_widget_data = self.cache_service.get(widget_cache_key, prefix="widget_data")

                        if cached_widget_data:
                            logger.debug(f"Cache HIT: Widget {widget.get('id')} data from cache")
                            return cached_widget_data

                        # Process widget data if not cached
                        logger.debug(f"Widget {widget.get('id')} columns from DB: {columns}")

                        column_request = [
                            {
                                'siteName': column.get("siteName", ""),
                                'tableName': column.get("tableName", ""),
                                'columnName': column.get("columnName", ""),
                                'columnType': column.get("columnType", "double")
                            }
                            for column in columns
                            if column.get("siteName") and column.get("tableName") and column.get("columnName")
                        ]

                        if not column_request:
                            logger.warning(f"Widget {widget.get('id')} has no valid columns to fetch data for")
                            return {
                                "id": widget.get("id"),
                                "name": widget.get("name", ""),
                                "type": widget.get("type"),
                                "columns": columns,
                                "display_order": widget.get("display_order", 0),
                                "yAxisOptions": widget.get("yAxisOptions", []),
                                "selectedRacks": widget.get("selectedRacks"),
                                "racks": []
                            }

                        logger.debug(f"Fetching data for {len(column_request)} columns: {column_request}")

                        # Convert rack list to comma-separated string for get_column_data_sources
                        rack_param = None
                        if rack:
                            if isinstance(rack, list):
                                rack_param = ",".join(rack)
                            else:
                                rack_param = str(rack)

                        column_responses_result = self.clickhouse_service.get_column_data_sources(
                            columns_list=column_request,
                            from_date=from_date,
                            to_date=to_date,
                            rack=rack_param
                        )

                        # Extract column_data from the response (get_column_data_sources returns dict with column_data and metadata)
                        column_responses = column_responses_result.get("column_data", []) if isinstance(column_responses_result, dict) else column_responses_result

                        logger.debug(f"Received {len(column_responses)} column responses from ClickHouse")

                        # Create columns array with column metadata and data (keeping the response structure)
                        # Verify rack columns exist using RACK_CANDIDATES from constants
                        from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
                        clickhouse_repo = ClickHouseRepository()
                        
                        # Check if any table has rack columns using RACK_CANDIDATES
                        has_rack_columns = False
                        for column_req in column_request:
                            site_name = column_req.get('siteName')
                            table_name = column_req.get('tableName')
                            
                            if site_name and table_name:
                                clickhouse_table_name = clickhouse_repo.get_clickhouse_table_name(site_name, table_name)
                                if clickhouse_table_name:
                                    # Use RACK_CANDIDATES from constants.py for rack column detection
                                    rack_columns = clickhouse_repo.get_rack_columns_for_table(clickhouse_table_name)
                                    if rack_columns:
                                        has_rack_columns = True
                                        logger.debug(f"Found rack columns using RACK_CANDIDATES in table {clickhouse_table_name}: {rack_columns}")
                                        break
                        
                        if not has_rack_columns:
                            logger.debug(f"No rack columns found using RACK_CANDIDATES for widget {widget.get('id')}. Returning empty racks arrays.")
                        
                        columns_data = []
                        for i, column_response in enumerate(column_responses):
                            # Find the corresponding column metadata
                            column_metadata = columns[i] if i < len(columns) else {}

                            datasource = column_response.get("dataSource", [])
                            # Only use racks if rack columns exist (based on RACK_CANDIDATES)
                            racks = column_response.get("racks", []) if has_rack_columns else []
                            logger.debug(f"Column {i}: {column_response.get('columnName')} has {len(datasource)} data points and {len(racks)} rack values")

                            # Ensure racks array matches dataSource length (racks are already aligned from get_column_data_sources)
                            column_racks = racks if racks else []
                            if len(column_racks) != len(datasource):
                                logger.debug(f"Rack count mismatch for column {column_response.get('columnName')}: {len(column_racks)} racks vs {len(datasource)} data points. Aligning...")
                                # Trim or pad to match dataSource length
                                if len(column_racks) > len(datasource):
                                    column_racks = column_racks[:len(datasource)]
                                else:
                                    column_racks.extend(["NaN"] * (len(datasource) - len(column_racks)))

                            column_data = {
                                "columnType": column_response.get("columnType"),
                                "siteName": column_metadata.get("siteName", ""),
                                "tableName": column_metadata.get("tableName", ""),
                                "columnName": column_response.get("columnName"),
                                "dataSource": datasource,
                                "racks": column_racks  # Extract racks directly from get_column_data_sources response (only if rack columns exist per RACK_CANDIDATES)
                            }
                            columns_data.append(column_data)
                            logger.debug(f"Added {len(column_racks)} rack values to column {column_response.get('columnName')}")

                        simplified_widget = {
                            "id": widget.get("id"),
                            "name": widget.get("name", ""),
                            "type": widget.get("type"),
                            "columns": columns_data,
                            "display_order": widget.get("display_order", 0),
                            "yAxisOptions": widget.get("yAxisOptions", []),
                            "selectedRacks": widget.get("selectedRacks")
                        }

                        # Cache individual widget data (5 minute TTL)
                        self.cache_service.set(
                            widget_cache_key,
                            simplified_widget,
                            ttl=CacheConfig.DEFAULT_TTL,
                            prefix="widget_data"
                        )

                        return simplified_widget

                    except Exception as e:
                        logger.error(f"Error processing widget {widget.get('id')}: {str(e)}")
                        # Return widget with empty data on error
                        return {
                            "id": widget.get("id"),
                            "name": widget.get("name", ""),
                            "type": widget.get("type"),
                            "columns": [],
                            "display_order": widget.get("display_order", 0),
                            "yAxisOptions": widget.get("yAxisOptions", []),
                            "selectedRacks": widget.get("selectedRacks"),
                            "racks": []
                        }
                
                # Process widgets in parallel (max 3 concurrent widgets)
                logger.info(f"Processing {len(widgets_data)} widgets in parallel with caching")
                with ThreadPoolExecutor(max_workers=3) as executor:
                    widget_list = list(executor.map(process_widget, widgets_data))
            else:
                # No widgets found, but we need to get analysis data directly
                # from the analysis repository
                analysis_record = analysisRepo.get_by_id(analysis_id)
                if analysis_record:
                    analysis_info = {
                        "analysis_id": analysis_record.get("id"),
                        "analysis_name": analysis_record.get("name"),
                        "user_id": analysis_record.get("user_id"),
                        "asset_type": analysis_record.get("asset_type"),
                        "analysis_type": analysis_record.get("type"),
                        "visibility": analysis_record.get("visibility"),
                        "applied_date_filter": analysis_record.get("applied_date_filter"),
                        "analysis_created_at": (
                            str(analysis_record.get("created_at"))
                            if analysis_record.get("created_at")
                            else None
                        ),
                        "analysis_updated_at": (
                            str(analysis_record.get("updated_at"))
                            if analysis_record.get("updated_at")
                            else None
                        ),
                    }

            # Build the restructured response
            response = {
                "analysis_id": analysis_info.get("analysis_id"),
                "analysis_name": analysis_info.get("analysis_name"),
                "applied_date_filter": analysis_info.get("applied_date_filter"),
                "user_id": analysis_info.get("user_id"),
                "asset_type": analysis_info.get("asset_type"),
                "analysis_type": analysis_info.get("analysis_type"),
                "visibility": analysis_info.get("visibility"),
                "analysis_created_at": analysis_info.get("analysis_created_at"),
                "analysis_updated_at": analysis_info.get("analysis_updated_at"),
                "data": widget_list,
            }

            # Cache the result in Redis for future requests (15 minute TTL)
            cache_success = self.cache_service.set(
                cache_key, 
                response, 
                ttl=CacheConfig.MEDIUM_TTL,
                prefix="parquet_data"
            )
            
            if cache_success:
                logger.info(f"Cached widgets result for analysis {analysis_id} (TTL: {CacheConfig.MEDIUM_TTL}s)")
            else:
                logger.warning(f"Failed to cache widgets result for analysis {analysis_id}")

            return response

        except Exception as e:
            logger.error(f"Error in get_all_widgets_for_analysis service: {str(e)}")
            raise

    def create_widget(
        self,
        widget_data: Dict,
        analysis_id: str,
        authenticated_user_id: str,
        authenticated_user_email: str = None
    ):
        """
        Create a new widget for a specific analysis with access control
        Returns: dict with created widget data
        """
        try:
            # STEP 1: Verify write access to analysis
            from infrastructure.services.analysis.analysis_crud_operations import (
                AnalysisCrudOperations
            )

            analysis_service = AnalysisCrudOperations()
            is_super_admin, role_type = analysis_service._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            analysisRepo = self._get_analysis_repository()
            analysis = analysisRepo.get_analysis_by_id_with_access_control(
                analysis_id=analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin
            )

            if not analysis:
                raise Exception("Analysis not found or access denied")

            # STEP 2: Audit logging for super admin
            if is_super_admin:
                user_id_match = analysis.get("user_id") == authenticated_user_id
                email_match = authenticated_user_email and analysis.get("user_id") == authenticated_user_email

                if not (user_id_match or email_match) and analysis.get("visibility") == "private":
                    logger.info(
                        f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                        f"({authenticated_user_email}) created widget in private analysis {analysis_id} "
                        f"owned by {analysis.get('user_id')}"
                    )

            # STEP 3: Proceed with widget creation
            if not widget_data.get("id"):
                widget_data["id"] = str(uuid.uuid4())

            if not widget_data.get("type"):
                raise ValueError("Widget type is required")

            repository = self._get_repository()
            created_widget = repository.create_widget(widget_data, analysis_id)

            return created_widget

        except Exception as e:
            logger.error(f"Error in create_widget service: {str(e)}")
            raise

    def update_widget(self, widget_data: Dict, analysis_id: str):
        """
        Update an existing widget or create a new one (upsert behavior)
        If widget ID is provided and exists: performs update
        If widget ID is missing or doesn't exist: creates new widget with auto-generated ID
        Returns: dict with updated/created widget data
        """
        try:
            repository = self._get_repository()
            widget_id = widget_data.get("id")

            if widget_id:
                # Check if widget exists for this analysis
                existing_widget = repository.get_widget(widget_id, analysis_id)
                if existing_widget:
                    # Widget exists, perform update
                    logger.info(f"Updating existing widget {widget_id} for analysis {analysis_id}")
                    updated_widget = repository.update_widget(widget_data, analysis_id)
                    return updated_widget
                else:
                    # Widget ID provided but doesn't exist, create new with provided ID
                    logger.info(f"Widget {widget_id} not found, creating new widget for analysis {analysis_id}")
                    created_widget = repository.create_widget(widget_data, analysis_id)
                    return created_widget
            else:
                # No ID provided, generate new ID and create widget
                widget_data["id"] = str(uuid.uuid4())
                logger.info(f"No widget ID provided, creating new widget {widget_data['id']} for analysis {analysis_id}")
                created_widget = repository.create_widget(widget_data, analysis_id)
                return created_widget

        except Exception as e:
            logger.error(f"Error in update_widget service: {str(e)}")
            raise

    def delete_widget(self, widget_id: str, analysis_id: str):
        """
        Delete a widget for a specific analysis
        Returns: dict with deletion status
        """
        try:
            repository = self._get_repository()
            deleted = repository.delete_widget(widget_id, analysis_id)

            if deleted:
                return {"deleted": True}

            raise Exception(f"Failed to delete widget {widget_id}")

        except Exception as e:
            logger.error(f"Error in delete_widget service: {str(e)}")
            raise

    def bulk_delete_widgets(
        self,
        widget_ids: List[str],
        authenticated_user_id: str,
        authenticated_user_email: str = None
    ) -> Dict:
        """
        Delete multiple widgets by their IDs with per-widget access control

        Args:
            widget_ids: List of widget IDs to delete
            authenticated_user_id: ID of authenticated user
            authenticated_user_email: Email of authenticated user (optional)

        Returns:
            Dict with structured deletion results and counts
        """
        try:
            # Validate input
            if not widget_ids:
                raise ValueError("Widget IDs list cannot be empty")

            if not isinstance(widget_ids, list):
                raise ValueError("widget_ids must be a list")

            # Remove empty strings and None values
            clean_widget_ids = [
                wid for wid in widget_ids if wid and isinstance(wid, str)
            ]

            if not clean_widget_ids:
                raise ValueError("No valid widget IDs provided")

            logger.info(
                f"Starting bulk deletion service for {len(clean_widget_ids)} widgets"
            )

            # STEP 1: Check super admin status
            from infrastructure.services.analysis.analysis_crud_operations import (
                AnalysisCrudOperations
            )

            analysis_service = AnalysisCrudOperations()
            is_super_admin, role_type = analysis_service._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            # STEP 2: Verify access to each widget's parent analysis
            repository = self._get_repository()
            analysisRepo = self._get_analysis_repository()

            verified_widget_ids = []
            failed_widget_ids = []
            start_time = time.time()

            for widget_id in clean_widget_ids:
                try:
                    # Get widget to find its analysis
                    widget = repository.get_widget_by_id_only(widget_id)
                    if not widget:
                        failed_widget_ids.append({
                            "widget_id": widget_id,
                            "error": "Widget not found"
                        })
                        continue

                    analysis_id = widget.get("analysis_id")

                    # Verify delete access to the analysis
                    analysis = analysisRepo.get_analysis_by_id_with_access_control(
                        analysis_id=analysis_id,
                        authenticated_user_id=authenticated_user_id,
                        authenticated_user_email=authenticated_user_email,
                        is_super_admin=is_super_admin
                    )

                    if not analysis:
                        failed_widget_ids.append({
                            "widget_id": widget_id,
                            "error": "Analysis not found or access denied"
                        })
                        continue

                    # Audit logging for super admin
                    if is_super_admin:
                        user_id_match = analysis.get("user_id") == authenticated_user_id
                        email_match = authenticated_user_email and analysis.get("user_id") == authenticated_user_email

                        if not (user_id_match or email_match) and analysis.get("visibility") == "private":
                            logger.info(
                                f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                                f"({authenticated_user_email}) deleted widget {widget_id} from private analysis {analysis_id} "
                                f"owned by {analysis.get('user_id')}"
                            )

                    verified_widget_ids.append(widget_id)

                except Exception as e:
                    logger.error(f"Access control check failed for widget {widget_id}: {str(e)}")
                    failed_widget_ids.append({
                        "widget_id": widget_id,
                        "error": str(e)
                    })

            # STEP 3: Delete only verified widgets
            if not verified_widget_ids:
                execution_time = time.time() - start_time
                return {
                    "success": True,
                    "message": f"No widgets deleted: {len(failed_widget_ids)} failed access control",
                    "data": {
                        "total_requested": len(clean_widget_ids),
                        "successfully_deleted": 0,
                        "failed_deletions": len(failed_widget_ids),
                        "deleted_widget_ids": [],
                        "failed_widget_ids": failed_widget_ids,
                        "execution_time_seconds": round(execution_time, 3)
                    }
                }

            # Delete verified widgets
            result = repository.bulk_delete_widgets(verified_widget_ids)

            # Combine repository failures with access control failures
            deleted_widget_ids = result.get("deleted_widget_ids", [])
            repo_failed = result.get("failed_widget_ids", [])
            all_failed = failed_widget_ids + repo_failed

            execution_time = time.time() - start_time

            # Format response message with combined counts
            total_requested = len(clean_widget_ids)
            successfully_deleted = len(deleted_widget_ids)
            failed_deletions = len(all_failed)

            if failed_deletions == 0:
                message = f"Successfully deleted all {successfully_deleted} widgets"
            elif successfully_deleted == 0:
                message = f"Failed to delete any widgets. {failed_deletions} failures"
            else:
                message = f"Partially successful: {successfully_deleted} deleted, {failed_deletions} failed out of {total_requested} requested"

            return {
                "success": True,
                "message": message,
                "data": {
                    "total_requested": total_requested,
                    "successfully_deleted": successfully_deleted,
                    "failed_deletions": failed_deletions,
                    "deleted_widget_ids": deleted_widget_ids,
                    "failed_widget_ids": all_failed,
                    "execution_time_seconds": round(execution_time, 3)
                }
            }

        except Exception as e:
            logger.error(f"Error in bulk_delete_widgets service: {str(e)}")
            return {
                "success": False,
                "message": f"Bulk deletion failed: {str(e)}",
                "data": {
                    "total_requested": len(widget_ids) if widget_ids else 0,
                    "successfully_deleted": 0,
                    "failed_deletions": len(widget_ids) if widget_ids else 0,
                    "deleted_widget_ids": [],
                    "failed_widget_ids": [
                        {"widget_id": wid, "error": str(e)}
                        for wid in (widget_ids or [])
                    ],
                },
            }

    def validate_widget_data(self, widget_data: Dict) -> tuple[bool, str]:
        """
        Validate widget data structure including yAxisOptions
        """
        if not isinstance(widget_data, dict):
            return False, "Widget data must be a dictionary"

        if not widget_data.get("type"):
            return False, "Widget type is required"

        if "columns" not in widget_data:
            return False, "Columns field is required"

        if not isinstance(widget_data.get("columns"), list):
            return False, "Columns must be a list"

        for column in widget_data.get("columns", []):
            if not isinstance(column, dict):
                return False, "Each column must be a dictionary"
            if "columnName" not in column:
                return False, "Each column must have a columnName"

        # Validate display_order if provided
        display_order = widget_data.get("display_order")
        if display_order is not None:
            if not isinstance(display_order, int):
                return False, "Display order must be an integer"
            if display_order < 0:
                return False, "Display order must be non-negative"

        # NEW: Validate yAxisOptions if provided
        yaxis_options = widget_data.get("yAxisOptions")
        if yaxis_options is not None:
            if not isinstance(yaxis_options, list):
                return False, "yAxisOptions must be a list"
            
            # Validate each yAxis option
            for i, option in enumerate(yaxis_options):
                if not isinstance(option, dict):
                    return False, f"yAxisOptions[{i}] must be an object"
                
                # Validate required fields for yAxis option
                if "seriesName" not in option:
                    return False, f"yAxisOptions[{i}] must have a seriesName"
                
                # Validate optional fields if present
                if "show" in option and not isinstance(option["show"], bool):
                    return False, f"yAxisOptions[{i}].show must be a boolean"
                
                if "opposite" in option and not isinstance(option["opposite"], bool):
                    return False, f"yAxisOptions[{i}].opposite must be a boolean"
                
                if "min" in option and not isinstance(option["min"], (int, float)):
                    return False, f"yAxisOptions[{i}].min must be a number"
                
                if "max" in option and not isinstance(option["max"], (int, float)):
                    return False, f"yAxisOptions[{i}].max must be a number"
                
                if "color" in option and not isinstance(option["color"], str):
                    return False, f"yAxisOptions[{i}].color must be a string"

        return True, "Valid"

    def create_widgets(self, widget_data, analysis_id: str, **options) -> Dict:
        """
        Unified method that handles both single widgets and arrays of widgets

        Args:
            widget_data: Either a single widget dict or list of widget dicts
            analysis_id: Analysis identifier
            **options: Optional parameters for bulk operations (allow_partial, validate_only, etc.)

        Returns:
            Dict with creation results in consistent format
        """
        try:
            if isinstance(widget_data, list):
                # Handle as array of widgets (use bulk logic)
                logger.info(
                    f"Processing array of {len(widget_data)} widgets for analysis {analysis_id}"
                )
                return self.bulk_create_widgets(
                    widgets_data=widget_data,
                    analysis_id=analysis_id,
                    allow_partial=options.get("allow_partial", False),
                    validate_only=options.get("validate_only", False),
                    stop_on_first_error=options.get("stop_on_first_error", False),
                )
            else:
                # Handle as single widget and format response to match bulk structure when needed
                logger.info(f"Processing single widget for analysis {analysis_id}")
                created_widget = self.create_widget(widget_data, analysis_id)

                # Return in single widget format (preserves existing behavior)
                return created_widget

        except Exception as e:
            logger.error(f"Error in create_widgets service: {str(e)}")
            raise

    def bulk_create_widgets(
        self,
        widgets_data: List[Dict],
        analysis_id: str,
        authenticated_user_id: str,
        authenticated_user_email: str = None,
        allow_partial: bool = False,
        validate_only: bool = False,
        stop_on_first_error: bool = False,
    ) -> Dict:
        """
        Bulk create widgets for a specific analysis with access control

        Args:
            widgets_data: List of widget dictionaries
            analysis_id: Analysis identifier
            authenticated_user_id: ID of authenticated user
            authenticated_user_email: Email of authenticated user (optional)
            allow_partial: Whether to allow partial success
            validate_only: Only validate without creating
            stop_on_first_error: Stop processing on first error

        Returns: Dict with creation results, execution time, and statistics
        """
        start_time = time.time()

        # STEP 1: Verify write access to analysis
        from infrastructure.services.analysis.analysis_crud_operations import (
            AnalysisCrudOperations
        )

        analysis_service = AnalysisCrudOperations()
        is_super_admin, role_type = analysis_service._check_super_admin_status(
            authenticated_user_id, authenticated_user_email
        )

        analysisRepo = self._get_analysis_repository()
        analysis = analysisRepo.get_analysis_by_id_with_access_control(
            analysis_id=analysis_id,
            authenticated_user_id=authenticated_user_id,
            authenticated_user_email=authenticated_user_email,
            is_super_admin=is_super_admin
        )

        if not analysis:
            return {
                "success": False,
                "message": "Analysis not found or access denied",
                "status_type": "not_found"
            }

        # STEP 2: Audit logging for super admin
        if is_super_admin:
            user_id_match = analysis.get("user_id") == authenticated_user_id
            email_match = authenticated_user_email and analysis.get("user_id") == authenticated_user_email

            if not (user_id_match or email_match) and analysis.get("visibility") == "private":
                logger.info(
                    f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                    f"({authenticated_user_email}) bulk created widgets in private analysis {analysis_id} "
                    f"owned by {analysis.get('user_id')}"
                )

        # STEP 3: Proceed with bulk creation
        logger.info(
            f"Starting bulk create widgets: {len(widgets_data)} widgets, analysis={analysis_id}, allow_partial={allow_partial}, validate_only={validate_only}"
        )

        try:
            # Remove analysis validation to match single widget behavior
            # Database foreign key constraints will handle invalid analysis IDs
            # This ensures consistent behavior between single and bulk operations

            # Check bulk size limit
            max_size = getattr(settings, "WIDGET_BULK_CREATE_MAX_SIZE", 100)
            if len(widgets_data) > max_size:
                return self._format_error_response(
                    validation_errors=[
                        {
                            "widget_index": None,
                            "error": f"Bulk operation exceeds maximum size limit of {max_size} widgets",
                        }
                    ],
                    creation_errors=[],
                    status_type="validation",
                )

            # Validate batch
            logger.debug(f"Starting batch validation for {len(widgets_data)} widgets")
            validation_errors = self._validate_batch(
                widgets_data, analysis_id, stop_on_first_error
            )
            logger.info(
                f"Batch validation completed: {len(validation_errors)} validation errors found"
            )

            if validation_errors and not allow_partial:
                execution_time = time.time() - start_time
                response = self._format_error_response(
                    validation_errors=validation_errors,
                    creation_errors=[],
                    status_type="validation",
                )
                response.update(
                    {
                        "total_widgets": len(widgets_data),
                        "execution_time_seconds": round(execution_time, 3),
                    }
                )
                return response

            # If validate_only mode, return validation results
            if validate_only:
                execution_time = time.time() - start_time
                valid_widgets = len(widgets_data) - len(validation_errors)
                logger.info(
                    f"Validation-only mode: {valid_widgets} valid widgets out of {len(widgets_data)} in {execution_time:.3f}s"
                )
                return {
                    "success": len(validation_errors) == 0,
                    "validation_only": True,
                    "total_widgets": len(widgets_data),
                    "valid_widgets": valid_widgets,
                    "validation_errors": validation_errors,
                    "execution_time_seconds": round(execution_time, 3),
                }

            # Filter out invalid widgets if partial success is allowed
            valid_widgets = []
            failed_validations = []

            if allow_partial and validation_errors:
                error_indices = {error["widget_index"] for error in validation_errors}
                for i, widget in enumerate(widgets_data):
                    if i not in error_indices:
                        valid_widgets.append(widget)
                    else:
                        failed_validations.extend(
                            [e for e in validation_errors if e["widget_index"] == i]
                        )
            else:
                valid_widgets = widgets_data
                failed_validations = validation_errors

            # Generate UUIDs for widgets without IDs and check duplicates within batch
            self._prepare_widget_ids(valid_widgets)

            # Perform bulk creation
            repository = self._get_repository()
            creation_result = repository.bulk_create_widgets(valid_widgets, analysis_id)

            execution_time = time.time() - start_time

            # Build response based on results
            total_created = creation_result["total_created"]
            total_failed = creation_result["total_failed"] + len(failed_validations)

            logger.info(
                f"Bulk operation statistics: total_widgets={len(widgets_data)}, created={total_created}, failed={total_failed}"
            )

            response = {
                "total_widgets": len(widgets_data),
                "total_created": total_created,
                "total_failed": total_failed,
                "execution_time_seconds": round(execution_time, 3),
                "created_widgets": creation_result["created_widgets"],
                "failed_widgets": creation_result["failed_widgets"]
                + failed_validations,
            }

            if total_failed == 0:
                response["success"] = True
                response["message"] = f"Successfully created {total_created} widgets"
                logger.info(
                    f"Bulk create completed successfully: {total_created} widgets created"
                )
            elif total_created > 0 and allow_partial:
                response["success"] = True
                response["partial_success"] = True
                response["message"] = (
                    f"Partially successful: created {total_created} widgets, failed {total_failed} widgets"
                )
                logger.info(
                    f"Bulk create partially successful: {total_created} created, {total_failed} failed"
                )
            else:
                response["success"] = False
                response["message"] = f"Failed to create widgets: {total_failed} errors"
                logger.warning(
                    f"Bulk create failed: {total_failed} errors, {total_created} created"
                )

            return response

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in bulk_create_widgets service: {str(e)}")

            # Categorize the error type for proper status code handling
            error_type = "system"
            if "ValueError" in str(type(e)) or "validation" in str(e).lower():
                error_type = "validation"
            elif "exists" in str(e).lower() or "not found" in str(e).lower():
                error_type = "business"

            response = self._format_error_response(
                validation_errors=[],
                creation_errors=[{"error": str(e)}],
                status_type=error_type,
            )
            response.update(
                {
                    "message": str(e),
                    "total_widgets": len(widgets_data) if widgets_data else 0,
                    "total_created": 0,
                    "total_failed": len(widgets_data) if widgets_data else 0,
                    "execution_time_seconds": round(execution_time, 3),
                }
            )
            return response

    def _validate_batch(
        self,
        widgets_data: List[Dict],
        analysis_id: str,
        stop_on_first_error: bool = False,
    ) -> List[Dict]:
        """
        Validate entire batch of widgets

        Returns: List of validation errors with widget indices
        """
        validation_errors = []
        logger.debug(
            f"Validating batch of {len(widgets_data)} widgets for analysis {analysis_id}"
        )

        if not widgets_data:
            error = {"widget_index": None, "error": "Widgets array is empty"}
            validation_errors.append(error)
            logger.debug("Validation failed: empty widgets array")
            return validation_errors

        if not analysis_id:
            error = {"widget_index": None, "error": "Analysis ID is required"}
            validation_errors.append(error)
            logger.debug("Validation failed: missing analysis ID")
            return validation_errors

        # Track widget IDs for duplicate detection within batch
        widget_ids_in_batch = set()

        for i, widget in enumerate(widgets_data):
            # Individual widget validation
            is_valid, validation_message = self.validate_widget_data(widget)
            if not is_valid:
                error = {
                    "widget_index": i,
                    "widget_id": widget.get("id"),
                    "error": validation_message,
                }
                validation_errors.append(error)

                if stop_on_first_error:
                    return validation_errors
                continue

            # Check for duplicate IDs within the batch
            widget_id = widget.get("id")
            if widget_id:
                if widget_id in widget_ids_in_batch:
                    error = {
                        "widget_index": i,
                        "widget_id": widget_id,
                        "error": f"Duplicate widget ID '{widget_id}' within the batch",
                    }
                    validation_errors.append(error)

                    if stop_on_first_error:
                        return validation_errors
                else:
                    widget_ids_in_batch.add(widget_id)

        return validation_errors

    def _prepare_widget_ids(self, widgets_data: List[Dict]) -> None:
        """
        Generate UUIDs for widgets without IDs
        Modifies the widgets_data in place
        """
        for widget in widgets_data:
            if not widget.get("id"):
                widget["id"] = str(uuid.uuid4())

    def bulk_update_widgets(
        self,
        widgets_data: List[Dict],
        analysis_id: str,
        allow_partial: bool = False,
        validate_only: bool = False,
        stop_on_first_error: bool = False,
    ) -> Dict:
        """
        Bulk update widgets for a specific analysis

        Args:
            widgets_data: List of widget dictionaries (each must have 'id' field)
            analysis_id: Analysis identifier
            allow_partial: Whether to allow partial success
            validate_only: Only validate without updating
            stop_on_first_error: Stop processing on first error

        Returns: Dict with update results, execution time, and statistics
        """
        start_time = time.time()
        logger.info(
            f"Starting bulk update widgets: {len(widgets_data)} widgets, analysis={analysis_id}, allow_partial={allow_partial}, validate_only={validate_only}"
        )

        try:
            # Check bulk size limit
            max_size = getattr(settings, "WIDGET_BULK_UPDATE_MAX_SIZE", 100)
            if len(widgets_data) > max_size:
                return self._format_error_response(
                    validation_errors=[
                        {
                            "widget_index": None,
                            "error": f"Bulk operation exceeds maximum size limit of {max_size} widgets",
                        }
                    ],
                    creation_errors=[],
                    status_type="validation",
                )

            # Validate batch for updates (includes ID requirement check)
            logger.debug(f"Starting batch validation for {len(widgets_data)} widgets")
            validation_errors = self._validate_update_batch(
                widgets_data, analysis_id, stop_on_first_error
            )
            logger.info(
                f"Batch validation completed: {len(validation_errors)} validation errors found"
            )

            if validation_errors and not allow_partial:
                execution_time = time.time() - start_time
                response = self._format_error_response(
                    validation_errors=validation_errors,
                    creation_errors=[],
                    status_type="validation",
                )
                response.update(
                    {
                        "total_widgets": len(widgets_data),
                        "execution_time_seconds": round(execution_time, 3),
                    }
                )
                return response

            # If validate_only mode, return validation results
            if validate_only:
                execution_time = time.time() - start_time
                valid_widgets = len(widgets_data) - len(validation_errors)
                logger.info(
                    f"Validation-only mode: {valid_widgets} valid widgets out of {len(widgets_data)} in {execution_time:.3f}s"
                )
                return {
                    "success": len(validation_errors) == 0,
                    "validation_only": True,
                    "total_widgets": len(widgets_data),
                    "valid_widgets": valid_widgets,
                    "validation_errors": validation_errors,
                    "execution_time_seconds": round(execution_time, 3),
                }

            # Filter out invalid widgets if partial success is allowed
            valid_widgets = []
            failed_validations = []

            if allow_partial and validation_errors:
                error_indices = {error["widget_index"] for error in validation_errors}
                for i, widget in enumerate(widgets_data):
                    if i not in error_indices:
                        valid_widgets.append(widget)
                    else:
                        failed_validations.extend(
                            [e for e in validation_errors if e["widget_index"] == i]
                        )
            else:
                valid_widgets = widgets_data
                failed_validations = validation_errors

            # Perform bulk update
            repository = self._get_repository()
            update_result = repository.bulk_update_widgets(valid_widgets, analysis_id)

            execution_time = time.time() - start_time

            # Build response based on results
            total_updated = update_result["total_updated"]
            total_failed = update_result["total_failed"] + len(failed_validations)

            logger.info(
                f"Bulk update statistics: total_widgets={len(widgets_data)}, updated={total_updated}, failed={total_failed}"
            )

            response = {
                "total_widgets": len(widgets_data),
                "total_updated": total_updated,
                "total_failed": total_failed,
                "execution_time_seconds": round(execution_time, 3),
                "updated_widgets": update_result["updated_widgets"],
                "failed_widgets": update_result["failed_widgets"] + failed_validations,
            }

            if total_failed == 0:
                response["success"] = True
                response["message"] = f"Successfully updated {total_updated} widgets"
                logger.info(
                    f"Bulk update completed successfully: {total_updated} widgets updated"
                )
            elif total_updated > 0 and allow_partial:
                response["success"] = True
                response["partial_success"] = True
                response["message"] = (
                    f"Partially successful: updated {total_updated} widgets, failed {total_failed} widgets"
                )
                logger.info(
                    f"Bulk update partially successful: {total_updated} updated, {total_failed} failed"
                )
            else:
                response["success"] = False
                response["message"] = f"Failed to update widgets: {total_failed} errors"
                logger.warning(
                    f"Bulk update failed: {total_failed} errors, {total_updated} updated"
                )

            return response

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in bulk_update_widgets service: {str(e)}")

            # Categorize the error type for proper status code handling
            error_type = "system"
            if "ValueError" in str(type(e)) or "validation" in str(e).lower():
                error_type = "validation"
            elif "exists" in str(e).lower() or "not found" in str(e).lower():
                error_type = "business"

            response = self._format_error_response(
                validation_errors=[],
                creation_errors=[{"error": str(e)}],
                status_type=error_type,
            )
            response.update(
                {
                    "message": str(e),
                    "total_widgets": len(widgets_data) if widgets_data else 0,
                    "total_updated": 0,
                    "total_failed": len(widgets_data) if widgets_data else 0,
                    "execution_time_seconds": round(execution_time, 3),
                }
            )
            return response

    def _validate_update_batch(
        self,
        widgets_data: List[Dict],
        analysis_id: str,
        stop_on_first_error: bool = False,
    ) -> List[Dict]:
        """
        Validate entire batch of widgets for update operations
        Includes additional validation for required 'id' field

        Returns: List of validation errors with widget indices
        """
        validation_errors = []
        logger.debug(
            f"Validating update batch of {len(widgets_data)} widgets for analysis {analysis_id}"
        )

        if not widgets_data:
            error = {"widget_index": None, "error": "Widgets array is empty"}
            validation_errors.append(error)
            logger.debug("Validation failed: empty widgets array")
            return validation_errors

        if not analysis_id:
            error = {"widget_index": None, "error": "Analysis ID is required"}
            validation_errors.append(error)
            logger.debug("Validation failed: missing analysis ID")
            return validation_errors

        # Track widget IDs for duplicate detection within batch
        widget_ids_in_batch = set()

        for i, widget in enumerate(widgets_data):
            # Check for required ID field in updates
            if not widget.get("id"):
                error = {
                    "widget_index": i,
                    "widget_id": None,
                    "error": "Widget ID is required for update operations",
                }
                validation_errors.append(error)

                if stop_on_first_error:
                    return validation_errors
                continue

            # Individual widget validation
            is_valid, validation_message = self.validate_widget_data(widget)
            if not is_valid:
                error = {
                    "widget_index": i,
                    "widget_id": widget.get("id"),
                    "error": validation_message,
                }
                validation_errors.append(error)

                if stop_on_first_error:
                    return validation_errors
                continue

            # Check for duplicate IDs within the batch
            widget_id = widget.get("id")
            if widget_id in widget_ids_in_batch:
                error = {
                    "widget_index": i,
                    "widget_id": widget_id,
                    "error": f"Duplicate widget ID '{widget_id}' within the batch",
                }
                validation_errors.append(error)

                if stop_on_first_error:
                    return validation_errors
            else:
                widget_ids_in_batch.add(widget_id)

        return validation_errors

    def create_analysis_with_widgets(
        self,
        analysis_data: Dict,
        widgets_data: List[Dict],
        analysis_id: str,
        **widget_options,
    ) -> Dict:
        """
        Create or update analysis and create widgets in a single transaction

        Args:
            analysis_data: Analysis information (user_id, analysis_name, etc.)
            widgets_data: List of widget dictionaries
            analysis_id: Analysis identifier
            **widget_options: Additional options for widget operations

        Returns:
            Combined response with analysis data at root level and widgets
        """
        start_time = time.time()
        logger.info(
            f"Starting combined analysis+widgets creation for analysis {analysis_id}"
        )

        try:
            # Step 1: Create or update analysis
            analysis_service = self._get_analysis_service()
            analysis_repo = self._get_analysis_repository()

            # Check if analysis exists
            analysis_exists = analysis_repo.check_analysis_exists(analysis_id)

            if analysis_exists:
                logger.info(f"Analysis {analysis_id} exists, updating it")
                # Update existing analysis
                update_data = {
                    "analysis_id": analysis_id,
                    "user_id": analysis_data.get("user_id"),
                    "name": analysis_data.get("analysis_name"),
                    "asset_type": analysis_data.get("asset_type"),
                    "type_value": analysis_data.get("analysis_type"),
                    "visibility": analysis_data.get("visibility"),
                    "applied_date_filter": analysis_data.get("applied_date_filter"),
                }
                # Filter out None values
                update_data = {k: v for k, v in update_data.items() if v is not None}
                analysis_result = analysis_service.update_analysis(update_data)
            else:
                logger.info(f"Creating new analysis {analysis_id}")
                # Create new analysis
                create_data = {
                    "id": analysis_id,
                    "user_id": analysis_data.get("user_id"),
                    "name": analysis_data.get("analysis_name"),
                    "asset_type": analysis_data.get("asset_type"),
                    "type_value": analysis_data.get("analysis_type"),
                    "visibility": analysis_data.get("visibility", "private"),
                    "applied_date_filter": analysis_data.get("applied_date_filter"),
                }
                analysis_result = analysis_service.create_analysis(create_data)

            # Check if analysis operation was successful
            if not analysis_result.get("success"):
                logger.error(
                    f"Analysis operation failed: {analysis_result.get('message')}"
                )
                return {
                    "success": False,
                    "message": f"Failed to create/update analysis: {analysis_result.get('message')}",
                    "status_type": "business",
                    "execution_time_seconds": round(time.time() - start_time, 3),
                }

            logger.info(f"Analysis operation successful for {analysis_id}")

            # Step 2: Create widgets
            if widgets_data:
                widget_result = self.bulk_create_widgets(
                    widgets_data=widgets_data,
                    analysis_id=analysis_id,
                    allow_partial=widget_options.get("allow_partial", False),
                    validate_only=widget_options.get("validate_only", False),
                    stop_on_first_error=widget_options.get(
                        "stop_on_first_error", False
                    ),
                )

                # Check if widget creation was successful
                if not widget_result.get("success") and not widget_options.get(
                    "allow_partial", False
                ):
                    logger.error(
                        f"Widget creation failed, but analysis was created/updated"
                    )
                    return {
                        "success": False,
                        "message": f"Analysis created/updated successfully, but widget creation failed: {widget_result.get('message')}",
                        "status_type": widget_result.get("status_type", "system"),
                        "analysis_created": True,
                        "widget_errors": widget_result.get("failed_widgets", []),
                        "execution_time_seconds": round(time.time() - start_time, 3),
                    }
            else:
                # No widgets to create
                widget_result = {
                    "success": True,
                    "total_created": 0,
                    "created_widgets": [],
                }

            # Step 3: Build response data without reading parquet files (PUT optimization)
            response_data = self._build_put_response_metadata(analysis_id)

            execution_time = time.time() - start_time
            logger.info(
                f"Combined analysis+widgets operation completed in {execution_time:.3f}s"
            )

            # Build success response
            message_parts = []
            if analysis_exists:
                message_parts.append("Analysis updated")
            else:
                message_parts.append("Analysis created")

            if widgets_data:
                widget_count = widget_result.get("total_created", 0)
                message_parts.append(f"{widget_count} widgets created")

            return {
                "success": True,
                "message": " and ".join(message_parts) + " successfully",
                "data": response_data,
                "execution_time_seconds": round(execution_time, 3),
                "widget_summary": {
                    "total_widgets": len(widgets_data) if widgets_data else 0,
                    "created_widgets": widget_result.get("total_created", 0),
                    "failed_widgets": widget_result.get("total_failed", 0),
                },
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in create_analysis_with_widgets: {str(e)}")
            return {
                "success": False,
                "message": f"Combined operation failed: {str(e)}",
                "status_type": "system",
                "execution_time_seconds": round(execution_time, 3),
            }

    def update_analysis_with_widgets(
        self,
        analysis_data: Dict,
        widgets_data: List[Dict],
        analysis_id: str,
        **widget_options,
    ) -> Dict:
        """
        Update analysis and replace all widgets in a single operation

        Args:
            analysis_data: Analysis information to update
            widgets_data: List of widget dictionaries to replace existing widgets
            analysis_id: Analysis identifier (must exist)
            **widget_options: Additional options for widget operations

        Returns:
            Combined response with analysis data at root level and widgets
        """
        start_time = time.time()
        logger.info(
            f"Starting combined analysis+widgets update for analysis {analysis_id}"
        )

        try:
            # Step 1: Update analysis (create if not exists as fallback)
            analysis_service = self._get_analysis_service()
            analysis_repo = self._get_analysis_repository()

            analysis_exists = analysis_repo.check_analysis_exists(analysis_id)

            if analysis_exists:
                logger.info(f"Updating existing analysis {analysis_id}")
                # Update existing analysis
                update_data = {
                    "analysis_id": analysis_id,
                    "user_id": analysis_data.get("user_id"),
                    "name": analysis_data.get("analysis_name"),
                    "asset_type": analysis_data.get("asset_type"),
                    "type_value": analysis_data.get("analysis_type"),
                    "visibility": analysis_data.get("visibility"),
                    "applied_date_filter": analysis_data.get("applied_date_filter"),
                }
                # Filter out None values
                update_data = {k: v for k, v in update_data.items() if v is not None}
                analysis_result = analysis_service.update_analysis(update_data)
            else:
                logger.info(
                    f"Analysis {analysis_id} doesn't exist, creating it as fallback"
                )
                # Create new analysis as fallback
                create_data = {
                    "id": analysis_id,
                    "user_id": analysis_data.get("user_id"),
                    "name": analysis_data.get("analysis_name"),
                    "asset_type": analysis_data.get("asset_type"),
                    "type_value": analysis_data.get("analysis_type"),
                    "visibility": analysis_data.get("visibility", "private"),
                    "applied_date_filter": analysis_data.get("applied_date_filter"),
                }
                analysis_result = analysis_service.create_analysis(create_data)

            # Check if analysis operation was successful
            if not analysis_result.get("success"):
                logger.error(
                    f"Analysis operation failed: {analysis_result.get('message')}"
                )
                return {
                    "success": False,
                    "message": f"Failed to update/create analysis: {analysis_result.get('message')}",
                    "status_type": "business",
                    "execution_time_seconds": round(time.time() - start_time, 3),
                }

            logger.info(f"Analysis update operation successful for {analysis_id}")

            # Step 2: Delete existing widgets for this analysis
            widget_repo = self._get_repository()
            try:
                widget_repo.delete_all_widgets_for_analysis(analysis_id)
                logger.info(f"Deleted existing widgets for analysis {analysis_id}")
            except Exception as e:
                logger.warning(f"Error deleting existing widgets: {str(e)}")

            # Step 3: Create new widgets
            if widgets_data:
                widget_result = self.bulk_create_widgets(
                    widgets_data=widgets_data,
                    analysis_id=analysis_id,
                    allow_partial=widget_options.get("allow_partial", False),
                    validate_only=widget_options.get("validate_only", False),
                    stop_on_first_error=widget_options.get(
                        "stop_on_first_error", False
                    ),
                )

                # Check if widget creation was successful
                if not widget_result.get("success") and not widget_options.get(
                    "allow_partial", False
                ):
                    logger.error(f"Widget replacement failed, but analysis was updated")
                    return {
                        "success": False,
                        "message": f"Analysis updated successfully, but widget replacement failed: {widget_result.get('message')}",
                        "status_type": widget_result.get("status_type", "system"),
                        "analysis_updated": True,
                        "widget_errors": widget_result.get("failed_widgets", []),
                        "execution_time_seconds": round(time.time() - start_time, 3),
                    }
            else:
                # No widgets to create (just delete existing ones)
                widget_result = {
                    "success": True,
                    "total_created": 0,
                    "created_widgets": [],
                }

            # Step 4: Build response data without reading parquet files (PUT optimization)
            response_data = self._build_put_response_metadata(analysis_id)

            execution_time = time.time() - start_time
            logger.info(
                f"Combined analysis+widgets update completed in {execution_time:.3f}s"
            )

            # Build success response
            message_parts = []
            if analysis_exists:
                message_parts.append("Analysis updated")
            else:
                message_parts.append("Analysis created")

            if widgets_data:
                widget_count = widget_result.get("total_created", 0)
                message_parts.append(f"all widgets replaced ({widget_count} widgets)")
            else:
                message_parts.append("all existing widgets removed")

            return {
                "success": True,
                "message": " and ".join(message_parts) + " successfully",
                "data": response_data,
                "execution_time_seconds": round(execution_time, 3),
                "widget_summary": {
                    "total_widgets": len(widgets_data) if widgets_data else 0,
                    "created_widgets": widget_result.get("total_created", 0),
                    "failed_widgets": widget_result.get("total_failed", 0),
                },
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in update_analysis_with_widgets: {str(e)}")
            return {
                "success": False,
                "message": f"Combined update operation failed: {str(e)}",
                "status_type": "system",
                "execution_time_seconds": round(execution_time, 3),
            }

    def validate_analysis_data(self, analysis_data: Dict) -> Tuple[bool, str]:
        """
        Validate analysis data structure

        Args:
            analysis_data: Analysis data dictionary

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not isinstance(analysis_data, dict):
            return False, "Analysis data must be a dictionary"

        # Required fields for analysis
        required_fields = ["user_id", "analysis_name", "asset_type", "analysis_type"]

        for field in required_fields:
            if not analysis_data.get(field):
                return False, f"Analysis field '{field}' is required"

        # Optional fields validation
        visibility = analysis_data.get("visibility")
        if visibility and visibility not in ["private", "public"]:
            return False, "Analysis visibility must be 'private' or 'public'"

        return True, "Valid"

    def copy_widget(
        self,
        widget_id: str,
        target_analysis_id: str,
        new_name: Optional[str] = None,
        authenticated_user_id: str = None,
        authenticated_user_email: str = None
    ) -> Dict:
        """
        Copy a widget from its current analysis to a target analysis with dual access control

        Args:
            widget_id: ID of the widget to copy
            target_analysis_id: Analysis ID where widget will be copied
            new_name: Optional new name for the copied widget
            authenticated_user_id: ID of authenticated user
            authenticated_user_email: Email of authenticated user (optional)

        Returns:
            Dict with created widget data
        """
        try:
            # Step 1: Get the source widget (will find which analysis it belongs to)
            repository = self._get_repository()
            source_widget = repository.get_widget_by_id_only(widget_id)

            if not source_widget:
                raise Exception(f"Widget {widget_id} not found")

            source_analysis_id = source_widget.get("analysis_id")

            # STEP 2: Verify READ access to source analysis
            from infrastructure.services.analysis.analysis_crud_operations import (
                AnalysisCrudOperations
            )

            analysis_service = AnalysisCrudOperations()
            is_super_admin, role_type = analysis_service._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            analysisRepo = self._get_analysis_repository()
            source_analysis = analysisRepo.get_analysis_by_id_with_access_control(
                analysis_id=source_analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin
            )

            if not source_analysis:
                raise Exception("Source analysis not found or access denied")

            # STEP 3: Verify WRITE access to target analysis
            target_analysis = analysisRepo.get_analysis_by_id_with_access_control(
                analysis_id=target_analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin
            )

            if not target_analysis:
                raise Exception("Target analysis not found or access denied")

            # STEP 4: Audit logging for super admin
            if is_super_admin:
                user_id_match_source = source_analysis.get("user_id") == authenticated_user_id
                email_match_source = authenticated_user_email and source_analysis.get("user_id") == authenticated_user_email
                user_id_match_target = target_analysis.get("user_id") == authenticated_user_id
                email_match_target = authenticated_user_email and target_analysis.get("user_id") == authenticated_user_email

                if not (user_id_match_source or email_match_source) and source_analysis.get("visibility") == "private":
                    logger.info(
                        f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                        f"({authenticated_user_email}) copied widget {widget_id} from private analysis {source_analysis_id} "
                        f"owned by {source_analysis.get('user_id')} to analysis {target_analysis_id}"
                    )

                if not (user_id_match_target or email_match_target) and target_analysis.get("visibility") == "private":
                    logger.info(
                        f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                        f"({authenticated_user_email}) copied widget {widget_id} to private analysis {target_analysis_id} "
                        f"owned by {target_analysis.get('user_id')}"
                    )

            # Step 2: Validate target analysis exists
            analysis_repo = self._get_analysis_repository()
            if not analysis_repo.check_analysis_exists(target_analysis_id):
                raise Exception(f"Target analysis {target_analysis_id} not found")

            # Step 3: Prepare copied widget data
            copied_widget = {
                "id": str(uuid.uuid4()),  # Generate new UUID
                "name": (
                    new_name if new_name is not None else source_widget.get("name", "")
                ),
                "type": source_widget["type"],
                "columns": source_widget["columns"],
                "data": source_widget["data"],
            }

            # Step 4: Create widget in target analysis
            created_widget = self.create_widget(
                widget_data=copied_widget,
                analysis_id=target_analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email
            )

            logger.info(
                f"Widget {widget_id} copied successfully to analysis {target_analysis_id} as {created_widget['id']}"
            )
            return created_widget

        except Exception as e:
            logger.error(f"Error copying widget {widget_id}: {str(e)}")
            raise

    def put_update_analysis_with_widgets(
        self,
        analysis_id: str,
        analysis_data: Dict,
        widgets_data: List[Dict],
        authenticated_user_id: str,
        authenticated_user_email: str = None
    ) -> Dict:
        """
        Update analysis and manage widgets with upsert operations with access control

        This method handles:
        - Analysis updates (create if doesn't exist)
        - Widget upsert operations:
          - Widgets without 'id' → Generate UUID and create as new
          - Widgets with 'id' → Update existing widget
          - Support for 0 widgets (analysis-only updates)

        Args:
            analysis_id: Analysis identifier from URL path
            analysis_data: Analysis information to update
            widgets_data: List of widget dictionaries for upsert operations
            authenticated_user_id: ID of authenticated user
            authenticated_user_email: Email of authenticated user (optional)

        Returns:
            Dict with success status, operation summary, and combined data
        """
        start_time = time.time()
        logger.info(f"Starting PUT analysis+widgets operation for analysis {analysis_id}")

        try:
            # Step 1: Verify write access to analysis
            from infrastructure.services.analysis.analysis_crud_operations import (
                AnalysisCrudOperations
            )

            analysis_service = AnalysisCrudOperations()
            is_super_admin, role_type = analysis_service._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            analysisRepo = self._get_analysis_repository()
            analysis = analysisRepo.get_analysis_by_id_with_access_control(
                analysis_id=analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin
            )

            if not analysis:
                return {
                    "success": False,
                    "message": "Analysis not found or access denied",
                    "status_type": "not_found"
                }

            # Step 2: Audit logging for super admin
            if is_super_admin:
                user_id_match = analysis.get("user_id") == authenticated_user_id
                email_match = authenticated_user_email and analysis.get("user_id") == authenticated_user_email

                if not (user_id_match or email_match) and analysis.get("visibility") == "private":
                    logger.info(
                        f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                        f"({authenticated_user_email}) updated private analysis {analysis_id} with widgets "
                        f"owned by {analysis.get('user_id')}"
                    )

            # Step 3: Validate input data
            is_valid, validation_message = self.validate_put_request_data(analysis_data, widgets_data)
            if not is_valid:
                return {
                    "success": False,
                    "message": f"Validation failed: {validation_message}",
                    "status_type": "validation",
                    "execution_time_seconds": round(time.time() - start_time, 3),
                }
                
            # Step 2 & 3: Handle analysis + widget operations in single optimized transaction
            widget_results = self.process_analysis_and_widget_replacement(
                analysis_id=analysis_id,
                analysis_data=analysis_data,
                widgets_data=widgets_data or []
            )
            
            widgets_created = widget_results.get("widgets_created", 0)
            widgets_updated = widget_results.get("widgets_updated", 0)
            widgets_deleted = widget_results.get("widgets_deleted", 0)
            processed_widgets = widget_results.get("processed_widgets", [])
            failed_operations = widget_results.get("failed_operations", [])
            analysis_operation = widget_results.get("analysis_operation", "updated")
            
            # If there were failures and no successes, return error
            if failed_operations and widgets_created == 0 and widgets_updated == 0 and widgets_deleted == 0:
                return {
                    "success": False,
                    "message": "Widget operations failed",
                    "status_type": "business",
                    "failed_operations": failed_operations,
                    "execution_time_seconds": round(time.time() - start_time, 3),
                }
            
            # Step 4: Invalidate cache for this analysis (since widgets changed)
            cache_key = f"widgets_analysis_{analysis_id}"
            cache_deleted = self.cache_service.delete(cache_key, prefix="parquet_data")
            if cache_deleted:
                logger.info(f"Invalidated cache for analysis {analysis_id} after PUT operation")
            
            # Step 5: Build response data without reading parquet files (PUT optimization)
            response_data = self._build_put_response_metadata(analysis_id)
            
            execution_time = time.time() - start_time
            logger.info(f"PUT analysis+widgets operation completed in {execution_time:.3f}s")
            
            # Build success response with operation summary
            total_widgets = widgets_created + widgets_updated
            
            # Create comprehensive message including deletions
            message_parts = [f"Analysis {analysis_operation} successfully"]
            
            # Build widget operation parts
            widget_ops = []
            if widgets_created > 0:
                widget_ops.append(f"{widgets_created} widget{'s' if widgets_created != 1 else ''} created")
            if widgets_updated > 0:
                widget_ops.append(f"{widgets_updated} widget{'s' if widgets_updated != 1 else ''} updated")
            if widgets_deleted > 0:
                widget_ops.append(f"{widgets_deleted} widget{'s' if widgets_deleted != 1 else ''} deleted")
            
            if widget_ops:
                message_parts.append(", ".join(widget_ops))
            elif total_widgets == 0 and widgets_deleted == 0:
                message_parts.append("no widget changes")
                
            # Add operation summary to response data
            if isinstance(response_data, dict):
                response_data["operation_summary"] = {
                    "analysis_operation": analysis_operation,
                    "widgets_created": widgets_created,
                    "widgets_updated": widgets_updated,
                    "widgets_deleted": widgets_deleted,
                    "total_widgets": total_widgets,
                    "execution_time_seconds": round(execution_time, 3),
                }
                
                # Add operation info to individual widgets
                if "data" in response_data and isinstance(response_data["data"], list):
                    for widget in response_data["data"]:
                        widget_id = widget.get("id")
                        # Find operation type for this widget
                        for processed_widget in processed_widgets:
                            if processed_widget.get("id") == widget_id:
                                widget["operation"] = processed_widget.get("operation", "unknown")
                                break
            
            return {
                "success": True,
                "message": " with ".join(message_parts),
                "data": response_data,
                "analysis_operation": analysis_operation,
                "execution_time_seconds": round(execution_time, 3),
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in PUT analysis+widgets operation: {str(e)}")
            return {
                "success": False,
                "message": f"PUT operation failed: {str(e)}",
                "status_type": "system",
                "execution_time_seconds": round(execution_time, 3),
            }
    
    def validate_put_request_data(self, analysis_data: Dict, widgets_data: List[Dict]) -> Tuple[bool, str]:
        """
        Validate PUT request data for analysis and widgets
        
        Args:
            analysis_data: Analysis data dictionary
            widgets_data: List of widget dictionaries
            
        Returns:
            Tuple of (is_valid, validation_message)
        """
        # Validate analysis data
        is_valid, validation_message = self.validate_analysis_data(analysis_data)
        if not is_valid:
            return False, f"Analysis validation: {validation_message}"
            
        # Validate widgets array
        if not isinstance(widgets_data, list):
            return False, "Widgets must be an array"
            
        # Validate individual widgets
        for i, widget in enumerate(widgets_data):
            is_valid, validation_message = self.validate_widget_data(widget)
            if not is_valid:
                return False, f"Widget {i}: {validation_message}"
                
        return True, "Valid"
    
    def _build_put_response_metadata(self, analysis_id: str) -> Dict:
        """
        Build response data for PUT operations without reading parquet files.
        Returns only analysis metadata and widget configuration (no actual data).
        Uses optimized single-session approach.
        """
        try:
            # Use single connection for both analysis and widget queries
            widget_repo = self._get_repository()
            
            with widget_repo._get_connection() as cursor:
                # Get analysis data
                analysis_table = f"{widget_repo._get_table_name().split('.')[0]}.{widget_repo._get_table_name().split('.')[1]}.analysis"
                cursor.execute(f"SELECT * FROM {analysis_table} WHERE id = ?", [analysis_id])
                analysis_record = cursor.fetchone()
                
                if not analysis_record:
                    raise Exception(f"Analysis {analysis_id} not found after update")
                
                # Build analysis info
                analysis_info = {
                    "analysis_id": analysis_record["id"],
                    "analysis_name": analysis_record["name"],
                    "user_id": analysis_record["user_id"],
                    "asset_type": analysis_record["asset_type"],
                    "analysis_type": analysis_record["type"],
                    "visibility": analysis_record["visibility"],
                    "applied_date_filter": analysis_record["applied_date_filter"],
                    "analysis_created_at": analysis_record["created_at"],
                    "analysis_updated_at": analysis_record["updated_at"],
                }
                
                # Get widget metadata in the same session (include yaxis_option and selected_racks)
                cursor.execute(
                    f"SELECT id, type, name, columns, yaxis_option, selected_racks FROM {widget_repo._get_table_name()} WHERE analysis_id = ?", 
                    [analysis_id]
                )
                widgets_data = cursor.fetchall()
                
                # Build widget list with empty data arrays (data will be fetched on GET)
                widget_list = []
                for widget in widgets_data:
                    # Parse columns JSON
                    columns = []
                    if widget["columns"]:
                        try:
                            columns = json.loads(widget["columns"]) if isinstance(widget["columns"], str) else widget["columns"]
                        except (json.JSONDecodeError, TypeError):
                            columns = []
                    
                    # FIX: Parse yAxisOptions JSON - handle both dict and row access patterns
                    yaxis_options = []
                    try:
                        # Try dictionary-style access first
                        yaxis_data = widget.get("yaxis_option") if hasattr(widget, "get") else widget["yaxis_option"]
                        
                        if yaxis_data:
                            # Parse JSON string to array
                            if isinstance(yaxis_data, str):
                                yaxis_options = json.loads(yaxis_data)
                            elif isinstance(yaxis_data, list):
                                yaxis_options = yaxis_data
                    except (KeyError, AttributeError, json.JSONDecodeError, TypeError) as e:
                        # If any error occurs, default to empty array
                        logger.warning(f"Error parsing yaxis_option for widget {widget['id']}: {e}")
                        yaxis_options = []
                    
                    # Detect and retrieve racks for this widget
                    widget_racks = []
                    try:
                        from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
                        clickhouse_repo = ClickHouseRepository()

                        # Check tables for rack columns (use first table that has racks)
                        for column in columns:
                            site_name = column.get('siteName')
                            table_name = column.get('tableName')

                            if site_name and table_name:
                                # Get ClickHouse table name
                                clickhouse_table_name = clickhouse_repo.get_clickhouse_table_name(site_name, table_name)

                                if clickhouse_table_name:
                                    # Get rack columns for this table
                                    rack_columns = clickhouse_repo.get_rack_columns_for_table(clickhouse_table_name)

                                    if rack_columns:
                                        # PUT response doesn't have date range, so racks will be empty
                                        # Racks are only populated on GET requests with date filtering
                                        logger.debug(f"Rack columns exist for widget {widget['id']} but PUT response doesn't include data")
                                        break
                    except Exception as rack_error:
                        logger.warning(f"Error retrieving racks for widget {widget['id']} in PUT response: {rack_error}")
                        widget_racks = []

                    # Parse selectedRacks JSON
                    selected_racks = None
                    try:
                        selected_racks_data = widget.get("selected_racks") if hasattr(widget, "get") else widget["selected_racks"]
                        if selected_racks_data:
                            if isinstance(selected_racks_data, str):
                                selected_racks = json.loads(selected_racks_data)
                            elif isinstance(selected_racks_data, list):
                                selected_racks = selected_racks_data
                    except (KeyError, AttributeError, json.JSONDecodeError, TypeError):
                        selected_racks = None

                    widget_list.append({
                        "id": widget["id"],
                        "name": widget["name"] or "",
                        "type": widget["type"],
                        "columns": columns,
                        "data": [],  # Empty data array - will be populated on GET
                        "yAxisOptions": yaxis_options,
                        "selectedRacks": selected_racks,
                        "racks": widget_racks
                    })
                
                # Combine analysis and widget data
                response_data = {
                    **analysis_info,
                    "data": widget_list
                }
                
                logger.info(f"Built PUT response with {len(widget_list)} widgets (single session, no parquet reading)")
                return response_data
            
        except Exception as e:
            logger.error(f"Error building PUT response metadata: {str(e)}")
            raise
    
    def process_analysis_and_widget_replacement(self, analysis_id: str, analysis_data: Dict, widgets_data: List[Dict]) -> Dict:
        """
        Process analysis update/create and widget replacement in a single optimized transaction.
        
        This combines analysis operations with widget operations for maximum performance:
        1. Check if analysis exists and update/create it
        2. Delete ALL existing widgets for the analysis
        3. Create ALL new widgets from payload
        
        All operations use a single database connection for optimal performance.
        
        Args:
            analysis_id: Analysis identifier
            analysis_data: Analysis data to update/create
            widgets_data: List of widget dictionaries from payload
            
        Returns:
            Dict with operation results
        """
        widgets_created = 0
        widgets_deleted = 0
        processed_widgets = []
        failed_operations = []
        analysis_operation = "updated"
        
        widget_repo = self._get_repository()
        
        # Single transaction approach for maximum performance
        try:
            with widget_repo._get_connection() as cursor:
                # Step 1: Handle analysis operation (check exists, then update/create)
                analysis_table = f"{widget_repo._get_table_name().split('.')[0]}.{widget_repo._get_table_name().split('.')[1]}.analysis"
                
                # Check if analysis exists
                cursor.execute(f"SELECT COUNT(*) as count FROM {analysis_table} WHERE id = ?", [analysis_id])
                result = cursor.fetchone()
                analysis_exists = result["count"] > 0 if result else False
                
                if analysis_exists:
                    # Update existing analysis
                    logger.info(f"Updating existing analysis {analysis_id}")
                    
                    # Build update query dynamically based on provided fields
                    update_fields = []
                    update_values = []
                    
                    if analysis_data.get("analysis_name"):
                        update_fields.append("name = ?")
                        update_values.append(analysis_data["analysis_name"])
                    if analysis_data.get("asset_type"):
                        update_fields.append("asset_type = ?")
                        update_values.append(analysis_data["asset_type"])
                    if analysis_data.get("analysis_type"):
                        update_fields.append("type = ?")
                        update_values.append(analysis_data["analysis_type"])
                    if analysis_data.get("visibility"):
                        update_fields.append("visibility = ?")
                        update_values.append(analysis_data["visibility"])
                    if analysis_data.get("applied_date_filter"):
                        update_fields.append("applied_date_filter = ?")
                        update_values.append(json.dumps(analysis_data["applied_date_filter"]))
                    
                    # Always update the updated_at timestamp
                    from datetime import datetime, timezone
                    current_time = datetime.now(timezone.utc)
                    update_fields.append("updated_at = ?")
                    update_values.append(current_time)
                    
                    # Add analysis_id for WHERE clause
                    update_values.append(analysis_id)
                    
                    if update_fields:
                        update_query = f"UPDATE {analysis_table} SET {', '.join(update_fields)} WHERE id = ?"
                        cursor.execute(update_query, update_values)
                        logger.info(f"Successfully updated analysis {analysis_id}")
                    
                    analysis_operation = "updated"
                else:
                    # Create new analysis
                    logger.info(f"Creating new analysis {analysis_id}")
                    
                    from datetime import datetime, timezone
                    current_time = datetime.now(timezone.utc)
                    
                    insert_query = f"""
                        INSERT INTO {analysis_table} 
                        (id, user_id, name, asset_type, type, visibility, applied_date_filter, created_at, updated_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, [
                        analysis_id,
                        analysis_data.get("user_id"),
                        analysis_data.get("analysis_name"),
                        analysis_data.get("asset_type"),
                        analysis_data.get("analysis_type"),
                        analysis_data.get("visibility", "private"),
                        json.dumps(analysis_data.get("applied_date_filter")) if analysis_data.get("applied_date_filter") else None,
                        current_time,
                        current_time
                    ])
                    logger.info(f"Successfully created analysis {analysis_id}")
                    
                    analysis_operation = "created"
                
                # Step 2: Count existing widgets before deletion (for reporting)
                cursor.execute(f"SELECT COUNT(*) as count FROM {widget_repo._get_table_name()} WHERE analysis_id = ?", [analysis_id])
                result = cursor.fetchone()
                widgets_deleted = result["count"] if result else 0
                
                # Step 3: Delete ALL existing widgets for this analysis (simple and fast)
                if widgets_deleted > 0:
                    logger.info(f"Deleting {widgets_deleted} existing widgets for analysis {analysis_id}")
                    cursor.execute(f"DELETE FROM {widget_repo._get_table_name()} WHERE analysis_id = ?", [analysis_id])
                    logger.info(f"Successfully deleted {widgets_deleted} widgets for analysis {analysis_id}")
                else:
                    logger.info(f"No existing widgets to delete for analysis {analysis_id}")
                
                # Step 4: Create ALL new widgets from payload (batch insert)
                if widgets_data:
                    logger.info(f"Creating {len(widgets_data)} new widgets for analysis {analysis_id}")
                    
                    from datetime import datetime, timezone
                    current_time = datetime.now(timezone.utc)
                    
                    # Prepare batch insert data
                    insert_data = []
                    for i, widget_data in enumerate(widgets_data):
                        try:
                            # Ensure widget has an ID
                            widget_id = widget_data.get("id") or str(uuid.uuid4())
                            
                            # Prepare widget data for insertion
                            # Strip dataSource from columns to avoid Databricks 1MB parameter limit
                            columns = widget_data.get("columns", [])
                            columns_without_data = []
                            for col in columns:
                                col_copy = col.copy()
                                # Remove dataSource if it exists (data fetched dynamically on GET)
                                col_copy.pop("dataSource", None)
                                columns_without_data.append(col_copy)
                            
                            columns_json = json.dumps(columns_without_data)
                            data_json = json.dumps([])  # Empty data array - will be populated on GET
                            
                            # Serialize yAxisOptions and selectedRacks
                            yaxis_options_json = json.dumps(widget_data.get("yAxisOptions", []))
                            selected_racks_json = json.dumps(widget_data.get("selectedRacks")) if widget_data.get("selectedRacks") is not None else None

                            # Get display_order from widget data or auto-assign
                            display_order = widget_data.get("display_order")
                            if display_order is None:
                                display_order = i  # Use index as default if not provided

                            insert_data.append((
                                widget_id,
                                analysis_id,
                                widget_data.get("type", ""),
                                widget_data.get("name", ""),
                                columns_json,
                                data_json,
                                display_order,
                                current_time,
                                current_time,
                                yaxis_options_json,
                                selected_racks_json,
                            ))
                            
                            processed_widgets.append({
                                "id": widget_id,
                                "operation": "created",
                                "index": i
                            })
                            
                        except Exception as e:
                            failed_operations.append({
                                "widget_index": i,
                                "widget_id": widget_data.get("id"),
                                "operation": "create",
                                "error": str(e)
                            })
                            logger.error(f"Error preparing widget at index {i}: {str(e)}")
                    
                    # Batch insert all widgets at once
                    if insert_data:
                        insert_query = f"""
                            INSERT INTO {widget_repo._get_table_name()}
                            (id, analysis_id, type, name, columns, data, display_order, created_at, updated_at, yaxis_option, selected_racks)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        cursor.executemany(insert_query, insert_data)
                        widgets_created = len(insert_data)
                        logger.info(f"Successfully created {widgets_created} widgets for analysis {analysis_id}")
                
        except Exception as e:
            logger.error(f"Error during optimized analysis+widget operation: {str(e)}")
            failed_operations.append({
                "widget_index": None,
                "widget_id": None,
                "operation": "combined_operation",
                "error": f"Failed to process analysis+widget operation: {str(e)}"
            })
        
        logger.info(f"Optimized analysis+widget operation completed: Analysis {analysis_operation}, {widgets_created} widgets created, {widgets_deleted} widgets deleted")
        
        return {
            "widgets_created": widgets_created,
            "widgets_updated": 0,  # No updates in replacement mode
            "widgets_deleted": widgets_deleted,
            "processed_widgets": processed_widgets,
            "failed_operations": failed_operations,
            "analysis_operation": analysis_operation,
        }
    
    def process_widget_replacement_operations(self, analysis_id: str, widgets_data: List[Dict]) -> Dict:
        """
        Process complete widget replacement for analysis using optimized single-transaction approach.
        
        For PUT operations, this implements true replacement semantics:
        1. Delete ALL existing widgets for the analysis
        2. Create ALL new widgets from payload
        
        This minimizes database sessions and is much faster.
        
        Args:
            analysis_id: Analysis identifier
            widgets_data: List of widget dictionaries from payload
            
        Returns:
            Dict with operation results
        """
        widgets_created = 0
        widgets_deleted = 0
        processed_widgets = []
        failed_operations = []
        
        widget_repo = self._get_repository()
        
        # Single transaction approach for maximum performance
        try:
            with widget_repo._get_connection() as cursor:
                # Step 1: Count existing widgets before deletion (for reporting)
                cursor.execute(f"SELECT COUNT(*) as count FROM {widget_repo._get_table_name()} WHERE analysis_id = ?", [analysis_id])
                result = cursor.fetchone()
                widgets_deleted = result["count"] if result else 0
                
                # Step 2: Delete ALL existing widgets for this analysis (simple and fast)
                if widgets_deleted > 0:
                    logger.info(f"Deleting {widgets_deleted} existing widgets for analysis {analysis_id}")
                    cursor.execute(f"DELETE FROM {widget_repo._get_table_name()} WHERE analysis_id = ?", [analysis_id])
                    logger.info(f"Successfully deleted {widgets_deleted} widgets for analysis {analysis_id}")
                else:
                    logger.info(f"No existing widgets to delete for analysis {analysis_id}")
                
                # Step 3: Create ALL new widgets from payload (batch insert)
                if widgets_data:
                    logger.info(f"Creating {len(widgets_data)} new widgets for analysis {analysis_id}")
                    
                    from datetime import datetime, timezone
                    current_time = datetime.now(timezone.utc)
                    
                    # Prepare batch insert data
                    insert_data = []
                    for i, widget_data in enumerate(widgets_data):
                        try:
                            # Ensure widget has an ID
                            widget_id = widget_data.get("id") or str(uuid.uuid4())
                            
                            # Prepare widget data for insertion
                            # Strip dataSource from columns to avoid Databricks 1MB parameter limit
                            columns = widget_data.get("columns", [])
                            columns_without_data = []
                            for col in columns:
                                col_copy = col.copy()
                                # Remove dataSource if it exists (data fetched dynamically on GET)
                                col_copy.pop("dataSource", None)
                                columns_without_data.append(col_copy)
                            
                            columns_json = json.dumps(columns_without_data)
                            data_json = json.dumps([])  # Empty data array - will be populated on GET

                            # Get display_order from widget data or auto-assign
                            display_order = widget_data.get("display_order")
                            if display_order is None:
                                display_order = i  # Use index as default if not provided

                            insert_data.append((
                                widget_id,
                                analysis_id,
                                widget_data.get("type", ""),
                                widget_data.get("name", ""),
                                columns_json,
                                data_json,
                                display_order,
                                current_time,
                                current_time
                            ))
                            
                            processed_widgets.append({
                                "id": widget_id,
                                "operation": "created",
                                "index": i
                            })
                            
                        except Exception as e:
                            failed_operations.append({
                                "widget_index": i,
                                "widget_id": widget_data.get("id"),
                                "operation": "create",
                                "error": str(e)
                            })
                            logger.error(f"Error preparing widget at index {i}: {str(e)}")
                    
                    # Batch insert all widgets at once
                    if insert_data:
                        insert_query = f"""
                            INSERT INTO {widget_repo._get_table_name()}
                            (id, analysis_id, type, name, columns, data, display_order, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        cursor.executemany(insert_query, insert_data)
                        widgets_created = len(insert_data)
                        logger.info(f"Successfully created {widgets_created} widgets for analysis {analysis_id}")
                
        except Exception as e:
            logger.error(f"Error during widget replacement operation: {str(e)}")
            failed_operations.append({
                "widget_index": None,
                "widget_id": None,
                "operation": "replacement",
                "error": f"Failed to process widget replacement: {str(e)}"
            })
        
        logger.info(f"Optimized widget replacement completed: {widgets_created} created, {widgets_deleted} deleted")
        
        return {
            "widgets_created": widgets_created,
            "widgets_updated": 0,  # No updates in replacement mode
            "widgets_deleted": widgets_deleted,
            "processed_widgets": processed_widgets,
            "failed_operations": failed_operations,
        }

    # Widget Ordering Service Methods

    def get_next_display_order(self, analysis_id: str) -> int:
        """Get the next available display order for new widgets"""
        try:
            repository = self._get_repository()
            return repository.get_next_display_order(analysis_id)
        except Exception as e:
            logger.error(f"Error in get_next_display_order service: {str(e)}")
            raise

    def reorder_widgets(
        self,
        analysis_id: str,
        reorder_operations: List[Dict],
        authenticated_user_id: str,
        authenticated_user_email: str = None
    ) -> Dict:
        """
        Bulk reorder widgets within an analysis with access control

        Args:
            analysis_id: Target analysis ID
            reorder_operations: List of {widget_id, new_display_order} operations
            authenticated_user_id: ID of authenticated user
            authenticated_user_email: Email of authenticated user (optional)

        Returns:
            Operation result with success status and details
        """
        try:
            # STEP 1: Verify write access to analysis
            from infrastructure.services.analysis.analysis_crud_operations import (
                AnalysisCrudOperations
            )

            analysis_service = AnalysisCrudOperations()
            is_super_admin, role_type = analysis_service._check_super_admin_status(
                authenticated_user_id, authenticated_user_email
            )

            analysisRepo = self._get_analysis_repository()
            analysis = analysisRepo.get_analysis_by_id_with_access_control(
                analysis_id=analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                is_super_admin=is_super_admin
            )

            if not analysis:
                raise ValueError("Analysis not found or access denied")

            # STEP 2: Audit logging for super admin
            if is_super_admin:
                user_id_match = analysis.get("user_id") == authenticated_user_id
                email_match = authenticated_user_email and analysis.get("user_id") == authenticated_user_email

                if not (user_id_match or email_match) and analysis.get("visibility") == "private":
                    logger.info(
                        f"SUPER ADMIN ACCESS: User {authenticated_user_id} "
                        f"({authenticated_user_email}) reordered widgets in private analysis {analysis_id} "
                        f"owned by {analysis.get('user_id')}"
                    )

            # Validate input
            if not analysis_id:
                raise ValueError("Analysis ID is required")

            if not reorder_operations:
                raise ValueError("Reorder operations are required")

            if not isinstance(reorder_operations, list):
                raise ValueError("Reorder operations must be a list")

            # Validate each operation
            for i, operation in enumerate(reorder_operations):
                if not isinstance(operation, dict):
                    raise ValueError(f"Operation {i} must be a dictionary")

                if "widget_id" not in operation:
                    raise ValueError(f"Operation {i} must include widget_id")

                if "new_display_order" not in operation:
                    raise ValueError(f"Operation {i} must include new_display_order")

                if not isinstance(operation["new_display_order"], int):
                    raise ValueError(f"Operation {i} new_display_order must be an integer")

                if operation["new_display_order"] < 0:
                    raise ValueError(f"Operation {i} new_display_order must be non-negative")

            # Call repository method
            repository = self._get_repository()
            result = repository.bulk_reorder_widgets(reorder_operations, analysis_id)

            # Invalidate cache for this analysis
            cache_key = f"widgets_analysis_{analysis_id}"
            cache_deleted = self.cache_service.delete(cache_key, prefix="parquet_data")
            if cache_deleted:
                logger.info(f"Invalidated cache for analysis {analysis_id} after reordering")

            return result

        except Exception as e:
            logger.error(f"Error in reorder_widgets service: {str(e)}")
            raise

    def resolve_ordering_conflicts(self, analysis_id: str) -> Dict:
        """Resolve duplicate display_order values by compacting gaps"""
        try:
            repository = self._get_repository()
            result = repository.compact_widget_ordering(analysis_id)

            # Invalidate cache for this analysis
            cache_key = f"widgets_analysis_{analysis_id}"
            cache_deleted = self.cache_service.delete(cache_key, prefix="parquet_data")
            if cache_deleted:
                logger.info(f"Invalidated cache for analysis {analysis_id} after conflict resolution")

            return result

        except Exception as e:
            logger.error(f"Error in resolve_ordering_conflicts service: {str(e)}")
            raise

    def validate_display_order(self, display_order: Optional[int], analysis_id: str) -> Tuple[bool, str]:
        """Validate display_order value and suggest alternatives"""
        try:
            if display_order is None:
                return True, "Display order will be auto-assigned"

            if not isinstance(display_order, int):
                return False, "Display order must be an integer"

            if display_order < 0:
                return False, "Display order must be non-negative"

            # Check if there are conflicts
            repository = self._get_repository()
            conflicts = repository.check_display_order_conflicts(analysis_id)

            conflict_orders = [conflict["display_order"] for conflict in conflicts]
            if display_order in conflict_orders:
                return False, f"Display order {display_order} already has conflicts in analysis {analysis_id}"

            return True, "Valid display order"

        except Exception as e:
            logger.error(f"Error in validate_display_order service: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def check_ordering_conflicts(self, analysis_id: str) -> Dict:
        """Check for ordering conflicts in an analysis"""
        try:
            repository = self._get_repository()
            conflicts = repository.check_display_order_conflicts(analysis_id)

            return {
                "analysis_id": analysis_id,
                "has_conflicts": len(conflicts) > 0,
                "conflict_count": len(conflicts),
                "conflicts": conflicts,
            }

        except Exception as e:
            logger.error(f"Error in check_ordering_conflicts service: {str(e)}")
            raise

    def migrate_widget_ordering(self) -> Dict:
        """
        Perform complete widget ordering migration (add column and initialize)

        Returns:
            Dict with migration results
        """
        try:
            repository = self._get_repository()

            # Step 1: Add display_order column
            logger.info("Starting widget ordering migration: adding display_order column")
            column_result = repository.migrate_add_display_order_column()

            # Step 2: Initialize display_order for existing widgets
            logger.info("Initializing display_order for existing widgets")
            init_result = repository.migrate_initialize_display_order()

            # Step 3: Validate migration
            logger.info("Validating display_order migration")
            validation_result = repository.validate_display_order_migration()

            # Clear all widget caches after migration
            logger.info("Clearing widget caches after migration")
            # Note: We can't clear all caches easily, but they'll expire naturally

            migration_success = column_result.get("success", False) and init_result.get("success", False)

            return {
                "success": migration_success,
                "message": "Widget ordering migration completed" if migration_success else "Widget ordering migration encountered issues",
                "column_addition": column_result,
                "initialization": init_result,
                "validation": validation_result,
            }

        except Exception as e:
            logger.error(f"Error in migrate_widget_ordering service: {str(e)}")
            raise
