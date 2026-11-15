"""
ClickHouse ADLS Service - Refactored to use repository pattern and utilities.
This service focuses on business logic and orchestration while delegating data access.
"""

from datetime import date, datetime
import logging
import re
import math
from typing import Dict, List, Optional, Union, Any
import pytz

from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.utils.clickhouse.clickhouse_utils import validate_date_range, build_date_filter
from infrastructure.services.multiSiteColumnService.models import ColumnResponse
from infrastructure.utils.clickhouse.clickhouse_utils import parse_datetime
from infrastructure.utils.number_formatting import format_decimal_value
from constants import ENABLE_FALLBACK_FOR_WIDGETS_APIS, ENABLE_FALLBACK_FOR_DASHBOARD_APIS

logger = logging.getLogger(__name__)


class ClickHouseADLSService:
    """Service to query migrated ADLS data from ClickHouse using repository pattern."""

    def __init__(self):
        self.repository = ClickHouseRepository()
        self.user_timezone = pytz.timezone('Asia/Dubai')
        self.utc_timezone = pytz.UTC

    def _convert_user_date_to_utc(self, user_date: Union[str, datetime, date]) -> Optional[str]:
        """
        Convert user-provided date from Asia/Dubai timezone to UTC.
        User dates are interpreted as Asia/Dubai and converted to UTC for database queries.
        
        Args:
            user_date: Date/datetime in string, datetime, or date format (interpreted as Asia/Dubai)
            
        Returns:
            UTC datetime string in format 'YYYY-MM-DD HH:MM:SS' or None
        """
        if not user_date:
            return None
        
        try:
            # Parse to datetime object if string
            if isinstance(user_date, str):
                dt = parse_datetime(user_date, return_datetime_object=True)
                if not dt:
                    logger.warning(f"Failed to parse date string: {user_date}")
                    return None
            elif isinstance(user_date, date) and not isinstance(user_date, datetime):
                dt = datetime.combine(user_date, datetime.min.time())
            else:
                dt = user_date
            
            # Ensure datetime is naive (no timezone info)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            
            # Localize to Asia/Dubai (user's timezone)
            dt_dubai = self.user_timezone.localize(dt)
            
            # Convert to UTC
            dt_utc = dt_dubai.astimezone(self.utc_timezone)
            
            # Return as string in UTC
            utc_string = dt_utc.strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f"Converted user date {user_date} (Asia/Dubai) -> {utc_string} (UTC)")
            return utc_string
            
        except Exception as e:
            logger.error(f"Error converting user date to UTC: {e}", exc_info=True)
            return None

    def _is_pump_table(self, table_name: str) -> bool:
        """
        Check if a table is a pump-related table by examining its name.
        
        Args:
            table_name: Table name to check
            
        Returns:
            True if table name contains pump-related patterns, False otherwise
        """
        if not table_name:
            return False
        
        table_name_lower = table_name.lower()
        
        # Check for pump-related patterns (case-insensitive)
        pump_patterns = ["pump", "pumps", "pumps_operational_performance"]
        
        for pattern in pump_patterns:
            if pattern in table_name_lower:
                return True
        
        return False

    def _extract_assigned_sites(self, user: Dict) -> set:
        """
        Extract and flatten sites from user's role clusters.
        Handles both string format: "{KSA, [Jubail-Jazlah, STPC]}"
        and dict format: {"name": "KSA", "sites": ["Jubail-Jazlah", "STPC"]}
        
        Args:
            user: User dictionary with role and clusters information
            
        Returns:
            Set of site names assigned to the user
        """
        role = user.get("role", {})
        if not role:
            logger.warning("User has no role information")
            return set()
            
        clusters = role.get("clusters", [])
        
        # Convert clusters to list if it's a numpy array or similar
        try:
            if hasattr(clusters, '__iter__') and not isinstance(clusters, (str, dict)):
                # Check if it's a numpy array or pandas Series
                if hasattr(clusters, 'tolist'):
                    clusters = clusters.tolist()
                else:
                    clusters = list(clusters)
        except Exception as e:
            logger.warning(f"Error converting clusters to list: {e}")
            clusters = []
        
        # Check if clusters is empty (now safe since it's a list)
        if not clusters or len(clusters) == 0:
            logger.warning(f"User role has no clusters. Role keys: {list(role.keys()) if isinstance(role, dict) else 'not a dict'}")
            return set()
            
        logger.debug(f"Processing clusters: {clusters}, type: {type(clusters)}")
        assigned_sites = set()
        
        # Handle if clusters is a string (might be JSON string)
        if isinstance(clusters, str):
            try:
                import json
                clusters = json.loads(clusters)
                # Ensure it's a list after JSON parsing
                if not isinstance(clusters, list):
                    clusters = [clusters] if clusters else []
            except (json.JSONDecodeError, ValueError):
                # If not JSON, treat as single cluster string
                clusters = [clusters]
        
        for cluster in clusters:
            if isinstance(cluster, dict):
                # Already parsed format: {"name": "KSA", "sites": [...]}
                sites = cluster.get("sites", [])
                if isinstance(sites, list):
                    assigned_sites.update(sites)
                elif sites:
                    assigned_sites.add(sites)
            elif isinstance(cluster, str):
                # String format: "{KSA, [Jubail-Jazlah, STPC]}"
                cluster = cluster.strip()
                match = re.match(r"\{([^,]+),\s*\[(.*)\]\}", cluster)
                if match:
                    sites_str = match.group(2).strip()
                    sites = [s.strip() for s in sites_str.split(",") if s.strip()]
                    assigned_sites.update(sites)
                    logger.debug(f"Parsed cluster string '{cluster}' -> sites: {sites}")
                else:
                    logger.debug(f"Failed to parse cluster string format: {cluster}")
            else:
                logger.warning(f"Unexpected cluster type: {type(cluster)}, value: {cluster}")
        
        logger.info(f"Extracted {len(assigned_sites)} assigned sites from user role clusters: {assigned_sites}")
        return assigned_sites

    def get_sites(self, user: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        Get all sites from ClickHouse using repository (equivalent to /analysis/sites/).
        Filters sites based on user's role-assigned sites if user is provided.

        Args:
            user: Optional user dictionary with role and clusters information
            
        Returns:
            List of sites with same format as analysis API (filtered by user assignment if user provided)
            
        Raises:
            Exception: If data retrieval fails
        """
        try:
            # Use repository method instead of direct query execution
            all_sites = self.repository.get_sites()
            
            # Filter by user's assigned sites if user is provided
            if user:
                logger.debug(f"User object received: {bool(user)}, has role key: {'role' in user if isinstance(user, dict) else False}")
                if user.get("role"):
                    logger.debug(f"User role structure: {type(user.get('role'))}, clusters: {user.get('role', {}).get('clusters', 'N/A')}")
                    assigned_sites = self._extract_assigned_sites(user)
                    logger.info(f"Extracted assigned sites: {assigned_sites}")
                    if not assigned_sites or len(assigned_sites) == 0:
                        logger.info("User has no assigned sites, returning empty list")
                        return []
                    
                    filtered_sites = [site for site in all_sites if site.get("name") in assigned_sites]
                    logger.info(f"Service: Filtered {len(filtered_sites)} of {len(all_sites)} sites based on user assignments")
                    return filtered_sites
                else:
                    logger.warning(f"User provided but no role found. User keys: {list(user.keys()) if isinstance(user, dict) else 'not a dict'}")
            else:
                logger.debug("No user provided, returning all sites")
            
            logger.info(f"Service: Retrieved {len(all_sites)} sites using repository (no user filter)")
            return all_sites
        except Exception as e:
            logger.error(f"Service error retrieving sites: {e}")
            raise Exception(f"Failed to retrieve sites: {str(e)}")

    def get_tables_for_site(self, site_name: str, user: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        Get all tables for a specific site (equivalent to /analysis/tables/{site}/).
        Validates user has access to the requested site if user is provided.

        Args:
            site_name: The site identifier
            user: Optional user dictionary with role and clusters information

        Returns:
            List of tables with same format as analysis API
            
        Raises:
            Exception: If data retrieval fails or user doesn't have access to the site
        """
        try:
            if not site_name or not site_name.strip():
                raise Exception("Site name is required")
            
            site_name = site_name.strip()
            
            # Validate user has access to the requested site
            if user and user.get("role"):
                assigned_sites = self._extract_assigned_sites(user)
                if assigned_sites and len(assigned_sites) > 0 and site_name not in assigned_sites:
                    logger.warning(f"User attempted to access site {site_name} without permission")
                    raise Exception(f"User does not have access to site: {site_name}")
            
            tables = self.repository.get_tables_for_site(site_name)
            logger.info(f"Service: Retrieved {len(tables)} tables for site {site_name}")
            return tables
        except Exception as e:
            logger.error(f"Service error retrieving tables for site {site_name}: {e}")
            raise Exception(f"Failed to retrieve tables for site {site_name}: {str(e)}")

    def get_migration_status(self) -> Dict:
        """
        Get overall migration status and statistics with business logic.

        Returns:
            Dict with formatted migration statistics
            
        Raises:
            Exception: If data retrieval fails
        """
        try:
            # Get raw data from repository
            raw_data = self.repository.get_migration_status_data()
            
            # Apply business logic for formatting and aggregation
            sites_stats = raw_data["sites_stats"]
            tables_stats = raw_data["tables_stats"]
            recent_logs = raw_data["recent_logs"]

            # Calculate total rows migrated
            total_rows = 0
            for status_info in tables_stats.values():
                total_rows += status_info["rows"]

            # Format response with business logic
            return {
                "sites": {
                    "total": sites_stats[0],
                    "migrated": sites_stats[1],
                    "completion_percentage": round((sites_stats[1] / sites_stats[0] * 100), 2) if sites_stats[0] > 0 else 0
                },
                "tables": tables_stats,
                "total_rows_migrated": total_rows,
                "recent_migrations": recent_logs,
                "summary": {
                    "migration_health": "Good" if sites_stats[1] / sites_stats[0] > 0.8 else "Needs Attention",
                    "last_migration": recent_logs[0]["started_at"] if recent_logs else "No recent migrations"
                }
            }

        except Exception as e:
            logger.error(f"Service error retrieving migration status: {e}")
            raise Exception(f"Failed to retrieve migration status: {str(e)}")

    def get_columns_for_tables(self, tables_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Get column information for multiple tables with business validation.

        Args:
            tables_list: List of dictionaries with siteName and tableName

        Returns:
            List of column information with parquet-equivalent types
            
        Raises:
            Exception: If validation fails or data retrieval fails
        """
        try:
            # Business validation
            if not tables_list:
                raise Exception("Tables list cannot be empty")
                
            valid_tables = []
            for table_request in tables_list:
                site_name = table_request.get('siteName')
                table_name = table_request.get('tableName')
                
                if not site_name or not table_name:
                    logger.warning(f"Skipping invalid table request: {table_request}")
                    continue
                    
                valid_tables.append(table_request)
            
            if not valid_tables:
                raise Exception("No valid table requests found")

            # Delegate to repository
            columns = self.repository.get_columns_for_tables(valid_tables)
            logger.info(f"Service: Retrieved columns for {len(valid_tables)} tables")
            return columns
            
        except Exception as e:
            logger.error(f"Service error retrieving columns for tables: {e}")
            raise Exception(f"Failed to retrieve columns: {str(e)}")

    def get_column_data_sources(self, columns_list: List[Dict[str, str]],
                              from_date: Optional[Union[str, datetime]] = None,
                              to_date: Optional[Union[str, datetime]] = None,
                              rack: Optional[str] = None,
                              filters: Optional[Dict[str, str]] = None,
                              enable_fallback: Optional[bool] = None) -> List[Dict]:
        """
        Get actual data values for specified columns with filtering and business logic.

        Args:
            columns_list: List of column specifications with siteName, tableName, columnName, columnType
            from_date: Start date/time for filtering (optional)
            to_date: End date/time for filtering (optional)
            rack: Rack/trailer filter value (optional, backward compatibility)
            filters: Generic column filters dictionary (optional, new feature)
                    Example: {"pump_status": "active", "rack": "R001,R002"}

        Returns:
            List of dictionaries with actual values (JSON serializable)

        Raises:
            Exception: If validation fails or data retrieval fails
        """
        try:
            # Business validation
            if not columns_list:
                raise Exception("Columns list cannot be empty")

            # Validate input types
            if not isinstance(columns_list, list):
                raise Exception(f"columns_list must be a list, got {type(columns_list)}")
            
            for idx, col in enumerate(columns_list):
                if not isinstance(col, dict):
                    raise Exception(f"Column at index {idx} must be a dict, got {type(col)}")

            # Validate date range if both dates provided
            if from_date and to_date:
                from_date_str = from_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(from_date, (datetime, date)) else from_date
                to_date_str = to_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(to_date, (datetime, date)) else to_date
                validate_date_range(from_date_str, to_date_str)

            # Backward compatibility: Merge rack parameter into filters
            merged_filters = filters.copy() if filters else {}

            if rack:
                # Detect rack column name automatically (will be done per table)
                # For backward compatibility, we keep rack as a separate parameter
                # and handle it in _build_query_conditions
                logger.info(f"Using rack parameter for backward compatibility: {rack}")

                # If filters also contains 'rack', log a warning about precedence
                if merged_filters.get('rack'):
                    logger.warning(f"Both 'rack' parameter and filters['rack'] provided. Using filters['rack'] = {merged_filters['rack']}")
                elif merged_filters.get('trailer'):
                    logger.warning(f"Both 'rack' parameter and filters['trailer'] provided. Using filters['trailer'] = {merged_filters['trailer']}")
                # Note: We keep rack separate for auto-detection of rack/trailer columns

            # Log filter information for debugging
            if merged_filters:
                logger.info(f"Applying generic filters: {merged_filters}")

            all_columns_data = []
            all_metadata = []  # Collect metadata from all tables

            # Group columns by table for efficient processing (business logic)
            table_groups = self._group_columns_by_table(columns_list)

            # Determine fallback setting: use provided value or default to Widgets API setting
            fallback_enabled = enable_fallback if enable_fallback is not None else ENABLE_FALLBACK_FOR_WIDGETS_APIS

            # Process each table group
            for table_key, table_columns in table_groups.items():
                site_name, table_name = table_key.split('.', 1)

                try:
                    table_data, table_metadata = self._get_table_column_data(
                        site_name, table_name, table_columns,
                        from_date, to_date, rack, merged_filters, fallback_enabled
                    )
                    all_columns_data.extend(table_data)
                    all_metadata.append(table_metadata)
                except Exception as e:
                    logger.warning(f"Failed to retrieve data for table {table_key}: {e}")
                    # Add empty data for failed table columns (business decision)
                    for column_spec in table_columns:
                        try:
                            all_columns_data.append(ColumnResponse(
                                columnName=column_spec.get('columnName'),
                                columnType=column_spec.get('columnType'),
                                tableName=table_name,
                                siteName=site_name,
                                dataSource=[],
                                racks=None
                            ))
                        except ImportError:
                            all_columns_data.append({
                                'columnName': column_spec.get('columnName'),
                                'columnType': column_spec.get('columnType'),
                                'tableName': table_name,
                                'siteName': site_name,
                                'dataSource': [],
                                'racks': None
                            })

            logger.info(f"Service: Retrieved data for {len(columns_list)} columns from {len(table_groups)} tables")

            # Convert ColumnResponse objects to dictionaries for JSON serialization
            serializable_data = []
            for column_response in all_columns_data:
                if hasattr(column_response, 'to_dict'):
                    serializable_data.append(column_response.to_dict())
                else:
                    # Fallback for any non-ColumnResponse objects
                    serializable_data.append(column_response)

            # Aggregate metadata from all tables (use first table's metadata or most recent)
            final_metadata = {
                "data_availability_for_given_date": all_metadata[0]["data_availability_for_given_date"] if all_metadata else True,
                "from_date": all_metadata[0]["from_date"] if all_metadata else from_date,
                "to_date": all_metadata[0]["to_date"] if all_metadata else to_date
            }

            return {
                "column_data": serializable_data,
                "metadata": final_metadata
            }

        except Exception as e:
            logger.error(f"Service error retrieving column data sources: {e}")
            raise Exception(f"Failed to retrieve column data sources: {str(e)}")

    def _group_columns_by_table(self, columns_list: List[Dict[str, str]]) -> Dict[str, List[Dict]]:
        """
        Group columns by table for efficient processing (business logic).
        
        Args:
            columns_list: List of column specifications
            
        Returns:
            Dictionary with table keys and grouped columns
        """
        table_groups = {}
        
        for column_spec in columns_list:
            site_name = column_spec.get('siteName')
            table_name = column_spec.get('tableName')

            if not site_name or not table_name:
                continue

            table_key = f"{site_name}.{table_name}"
            if table_key not in table_groups:
                table_groups[table_key] = []
            table_groups[table_key].append(column_spec)
            
        return table_groups

    def _get_table_column_data(self, site_name: str, table_name: str,
                             table_columns: List[Dict], from_date: Optional[str],
                             to_date: Optional[str], rack: Optional[str],
                             filters: Optional[Dict[str, str]] = None,
                             enable_fallback: bool = False) -> tuple:
        """
        Get data for multiple columns from a single table with business logic and filtering.

        Args:
            site_name: Site identifier
            table_name: Table identifier
            table_columns: List of column specifications for this table
            from_date: Optional start date
            to_date: Optional end date
            rack: Optional rack filter (backward compatibility)
            filters: Optional generic filters dictionary

        Returns:
            Tuple of (column_data_list, metadata_dict)
            - column_data_list: List of column data dictionaries
            - metadata_dict: Dictionary with data_availability_for_given_date, from_date, to_date

        Raises:
            Exception: If data retrieval fails
        """
        try:
            # Get ClickHouse table name from repository
            clickhouse_table_name = self.repository.get_clickhouse_table_name(site_name, table_name)
            if not clickhouse_table_name:
                raise Exception(f"No ClickHouse table found for {site_name}.{table_name}")

            # Extract column names for the query
            column_names = [col.get('columnName') for col in table_columns if col.get('columnName')]

            if not column_names:
                raise Exception("No valid column names found")

            # Find datetime and rack columns using repository
            datetime_column = self.repository.get_datetime_column(clickhouse_table_name)
            rack_column = self.repository.get_rack_trailer_column(clickhouse_table_name) if rack else None
            
            # Detect rack columns for data retrieval (not just filtering)
            rack_columns = self.repository.get_rack_columns_for_table(clickhouse_table_name)
            selected_rack_column = None
            if rack_columns:
                # Select the first rack column (best match based on RACK_CANDIDATES order)
                selected_rack_column = rack_columns[0]
                
                # Verify the rack column is actually a String type (safety check)
                try:
                    table_columns_info = self.repository.get_table_columns(clickhouse_table_name)
                    rack_col_info = next((col for col in table_columns_info if col.get('name') == selected_rack_column), None)
                    if rack_col_info:
                        col_type = rack_col_info.get('type', '').lower()
                        if 'string' not in col_type and 'fixedstring' not in col_type:
                            logger.warning(
                                f"Rack column '{selected_rack_column}' is not a String type (type: {rack_col_info.get('type')}). "
                                f"Skipping rack data extraction to avoid incorrect values."
                            )
                            selected_rack_column = None
                        else:
                            logger.info(f"Verified rack column '{selected_rack_column}' is String type: {rack_col_info.get('type')}")
                    else:
                        logger.warning(f"Could not verify type for rack column '{selected_rack_column}', proceeding with caution")
                except Exception as verify_error:
                    logger.warning(f"Error verifying rack column type: {verify_error}, proceeding with caution")
                
                # Include rack column in query if not already in column_names
                if selected_rack_column and selected_rack_column not in column_names:
                    column_names.append(selected_rack_column)
                    logger.info(f"Added rack column '{selected_rack_column}' to query for table {clickhouse_table_name}")

            # Check if this is a pump table and add PUMP_ID and PUMP_CATEGORY if needed
            is_pump_table = self._is_pump_table(clickhouse_table_name)
            pump_id_column = None
            pump_category_column = None
            
            if is_pump_table and selected_rack_column and selected_rack_column.lower() == "pump":
                # Get table columns to check if PUMP_ID and PUMP_CATEGORY exist
                try:
                    table_columns_info = self.repository.get_table_columns(clickhouse_table_name)
                    available_column_names = [col.get('name', '') for col in table_columns_info]
                    
                    # Check for PUMP_ID column (case-insensitive)
                    for col_name in available_column_names:
                        if col_name.upper() == "PUMP_ID":
                            pump_id_column = col_name
                            break
                    
                    # Check for PUMP_CATEGORY column (case-insensitive)
                    for col_name in available_column_names:
                        if col_name.upper() == "PUMP_CATEGORY":
                            pump_category_column = col_name
                            break
                    
                    # Add PUMP_ID to query if it exists and isn't already included
                    if pump_id_column and pump_id_column not in column_names:
                        column_names.append(pump_id_column)
                        logger.info(f"Added PUMP_ID column '{pump_id_column}' to query for pump table {clickhouse_table_name}")
                    
                    # Add PUMP_CATEGORY to query if it exists and isn't already included
                    if pump_category_column and pump_category_column not in column_names:
                        column_names.append(pump_category_column)
                        logger.info(f"Added PUMP_CATEGORY column '{pump_category_column}' to query for pump table {clickhouse_table_name}")
                    
                    if not pump_id_column and not pump_category_column:
                        logger.debug(f"Pump table {clickhouse_table_name} does not have PUMP_ID or PUMP_CATEGORY columns")
                    elif not pump_id_column:
                        logger.debug(f"Pump table {clickhouse_table_name} does not have PUMP_ID column")
                    elif not pump_category_column:
                        logger.debug(f"Pump table {clickhouse_table_name} does not have PUMP_CATEGORY column")
                        
                except Exception as pump_col_error:
                    logger.warning(f"Error checking for pump columns in table {clickhouse_table_name}: {pump_col_error}")

            # Build query conditions using business logic
            where_conditions, query_params = self._build_query_conditions(
                clickhouse_table_name, datetime_column, rack_column,
                from_date, to_date, rack, filters
            )

            # Get data from repository
            # Execute query using repository with enhanced error handling
            # Note: Fallback is DISABLED for Widgets APIs - returns empty result if no data found
            # Uses constant ENABLE_FALLBACK_FOR_WIDGETS_APIS from constants.py
            try:
                logger.info(f"Service: Executing query for table {clickhouse_table_name} with columns: {column_names}")
                logger.info(f"Service: WHERE conditions: {where_conditions}")
                logger.info(f"Service: Query params: {query_params}")
                logger.info(f"Service: Fallback enabled: {enable_fallback}")

                result_dict = self.repository.get_column_data_for_table(
                    clickhouse_table_name=clickhouse_table_name,
                    column_names=column_names,
                    datetime_column=datetime_column,
                    where_conditions=where_conditions,
                    query_params=query_params,
                    limit=None,
                    enable_fallback=enable_fallback
                )

                # Extract data and metadata from repository response
                result_rows = result_dict.get("result_rows", [])
                data_availability = result_dict.get("data_availability_for_given_date", True)
                from_date_used = result_dict.get("from_date")
                to_date_used = result_dict.get("to_date")

                logger.info(f"Service: Successfully retrieved {len(result_rows)} rows from {clickhouse_table_name}")
                logger.info(f"Service: Data availability for requested date: {data_availability}, range: {from_date_used} to {to_date_used}")

                # Store metadata for this table
                metadata = {
                    "data_availability_for_given_date": data_availability,
                    "from_date": from_date_used,
                    "to_date": to_date_used
                }

            except Exception as query_error:
                logger.error(f"Service: Query execution failed for {clickhouse_table_name}: {str(query_error)}")
                # Return empty data and default metadata for this table
                default_metadata = {
                    "data_availability_for_given_date": True,
                    "from_date": from_date,
                    "to_date": to_date
                }
                return [], default_metadata

            # Process results with business logic
            # Pass actual column_names (which includes rack column if added) for accurate index calculation
            processed_data = self._process_table_results(
                result_rows, table_columns, datetime_column, site_name, table_name,
                from_date=from_date, to_date=to_date, rack_column=selected_rack_column,
                actual_column_names=column_names,
                is_pump_table=is_pump_table,
                pump_id_column=pump_id_column,
                pump_category_column=pump_category_column
            )

            return processed_data, metadata

        except Exception as e:
            logger.error(f"Error getting table column data for {site_name}.{table_name}: {e}")
            raise Exception(f"Failed to get table column data: {str(e)}")

    def _build_query_conditions(self, clickhouse_table_name: str, datetime_column: Optional[str],
                               rack_column: Optional[str], from_date: Optional[str],
                               to_date: Optional[str], rack: Optional[str],
                               filters: Optional[Dict[str, str]] = None) -> tuple:
        """
        Build query conditions using business logic and date utilities.

        Args:
            clickhouse_table_name: ClickHouse table name
            datetime_column: DateTime column for date filtering
            rack_column: Rack column for rack filtering (backward compatibility)
            from_date: Start date for filtering
            to_date: End date for filtering
            rack: Rack value for filtering (backward compatibility)
            filters: Generic filters dictionary for any column

        Returns:
            Tuple of (where_conditions_list, query_parameters_list)
        """
        where_conditions = []
        query_params = {}
        param_counter = 0  # For unique parameter names

        # Add date filtering with ClickHouse parameters
        if datetime_column and (from_date or to_date):
            date_conditions, date_params = self._build_date_filter_clickhouse(
                datetime_column, from_date, to_date, param_counter
            )
            where_conditions.extend(date_conditions)
            query_params.update(date_params)
            param_counter += len(date_params)

        # Add rack filtering (backward compatibility)
        if rack and rack_column:
            rack_condition, rack_params = self._build_rack_filter_clickhouse(
                clickhouse_table_name, rack_column, rack, param_counter
            )
            if rack_condition:
                where_conditions.append(rack_condition)
                query_params.update(rack_params)
                param_counter += len(rack_params)

        # Add generic filters
        if filters:
            generic_conditions, generic_params = self._build_generic_filters_clickhouse(
                clickhouse_table_name, filters, param_counter
            )
            if generic_conditions:
                where_conditions.extend(generic_conditions)
                query_params.update(generic_params)

        return where_conditions, query_params

    def _build_date_filter_clickhouse(self, datetime_column: str, from_date: Optional[Union[str, datetime]],
                                    to_date: Optional[Union[str, datetime]], param_counter: int) -> tuple:
        """
        Build date filtering conditions with timezone-aware conversion.
        Converts input dates from Asia/Dubai timezone to UTC for ClickHouse.
        Data in ClickHouse is stored in UTC, so user-provided dates must be converted.

        Returns:
            Tuple of (conditions_list, parameters_dict)
        """
        
        conditions = []
        params = {}

        try:
            if from_date and to_date:
                # Convert user dates from Asia/Dubai to UTC
                from_datetime_utc = self._convert_user_date_to_utc(from_date)
                to_datetime_utc = self._convert_user_date_to_utc(to_date)

                if from_datetime_utc and to_datetime_utc:
                    logger.debug(f"Date filter - Original (Asia/Dubai): from={from_date}, to={to_date}")
                    logger.debug(f"Date filter - Converted to UTC: from={from_datetime_utc}, to={to_datetime_utc}")

                    # Use UTC timezone for comparison - data is stored in UTC
                    conditions.append(f"`{datetime_column}` >= {{from_date:String}}")
                    conditions.append(f"`{datetime_column}` <= {{to_date:String}}")
                    params["from_date"] = from_datetime_utc
                    params["to_date"] = to_datetime_utc
                else:
                    logger.warning(f"Failed to convert dates to UTC: from={from_date}, to={to_date}")

            elif from_date:
                # Single from date - convert from Asia/Dubai to UTC
                from_datetime_utc = self._convert_user_date_to_utc(from_date)
                    
                if from_datetime_utc:
                    logger.debug(f"Date filter - Original (Asia/Dubai): from={from_date}")
                    logger.debug(f"Date filter - Converted to UTC: from={from_datetime_utc}")

                    conditions.append(f"`{datetime_column}` >= {{from_date:String}}")
                    params["from_date"] = from_datetime_utc
                else:
                    logger.warning(f"Failed to convert from_date to UTC: {from_date}")

            elif to_date:
                # To date only - convert from Asia/Dubai to UTC
                to_datetime_utc = self._convert_user_date_to_utc(to_date)
                    
                if to_datetime_utc:
                    logger.debug(f"Date filter - Original (Asia/Dubai): to={to_date}")
                    logger.debug(f"Date filter - Converted to UTC: to={to_datetime_utc}")

                    conditions.append(f"`{datetime_column}` <= {{to_date:String}}")
                    params["to_date"] = to_datetime_utc
                else:
                    logger.warning(f"Failed to convert to_date to UTC: {to_date}")

        except Exception as e:
            logger.error(f"Error building date filter: {e}", exc_info=True)
            # Fallback to default 7 days
            conditions.append(f"`{datetime_column}` >= now() - INTERVAL 7 DAY")

        return conditions, params

    def _build_rack_filter_clickhouse(self, clickhouse_table_name: str, rack_column: str, 
                                     rack: str, param_counter: int) -> tuple:
        """
        Build rack filtering with ClickHouse parameter format.

        Returns:
            Tuple of (condition_string, params_dict)
        """
        try:
            # Parse comma-separated rack values
            if isinstance(rack, str):
                rack_values = [value.strip() for value in rack.split(',') if value.strip()]
            else:
                rack_values = rack

            if not rack_values:
                return "", {}

            # Get column type from repository
            rack_column_type = self.repository.get_column_type(clickhouse_table_name, rack_column)
            if not rack_column_type:
                rack_column_type = "String"

            is_numeric_column = any(int_type in rack_column_type.lower()
                                  for int_type in ['int', 'uint'])

            params = {}

            if len(rack_values) == 1:
                # Single value
                single_value = rack_values[0]
                param_name = f"rack_{param_counter}"

                if is_numeric_column:
                    try:
                        rack_int_value = int(single_value)
                        params[param_name] = rack_int_value
                        return f"`{rack_column}` = {{{param_name}:Int64}}", params
                    except ValueError:
                        params[param_name] = single_value
                        return f"toString(`{rack_column}`) = {{{param_name}:String}}", params
                else:
                    params[param_name] = single_value
                    return f"`{rack_column}` = {{{param_name}:String}}", params

            else:
                # Multiple values - use IN clause
                if is_numeric_column:
                    numeric_values = []
                    string_values = []

                    for value in rack_values:
                        try:
                            numeric_values.append(int(value))
                        except ValueError:
                            string_values.append(value)

                    conditions = []

                    if numeric_values:
                        param_name = f"rack_nums_{param_counter}"
                        params[param_name] = numeric_values
                        conditions.append(f"`{rack_column}` IN {{{param_name}:Array(Int64)}}")

                    if string_values:
                        param_name = f"rack_strs_{param_counter}"
                        params[param_name] = string_values
                        conditions.append(f"toString(`{rack_column}`) IN {{{param_name}:Array(String)}}")

                    if conditions:
                        return f"({' OR '.join(conditions)})", params
                else:
                    # String column with array
                    param_name = f"rack_vals_{param_counter}"
                    params[param_name] = rack_values
                    return f"`{rack_column}` IN {{{param_name}:Array(String)}}", params

            return "", {}

        except Exception as e:
            logger.warning(f"Error building rack filter: {e}")
            return "", {}

    def _build_generic_filters_clickhouse(self, clickhouse_table_name: str, 
                                         filters: Dict[str, str], param_counter: int) -> tuple:
        """
        Build generic filtering with ClickHouse parameter format.

        Returns:
            Tuple of (where_conditions_list, params_dict)
        """
        try:
            if not filters:
                return [], {}

            all_conditions = []
            all_params = {}
            local_counter = param_counter

            for column_name, filter_value in filters.items():
                if not filter_value or not str(filter_value).strip():
                    continue

                # Validate column exists
                if not self.repository.validate_column_exists(clickhouse_table_name, column_name):
                    logger.warning(f"Column '{column_name}' does not exist, skipping filter")
                    continue

                # Parse comma-separated values
                filter_values = [value.strip() for value in str(filter_value).split(',') if value.strip()]

                if not filter_values:
                    continue

                # Get column type
                column_type = self.repository.get_column_type(clickhouse_table_name, column_name)
                if not column_type:
                    column_type = "String"

                is_numeric_column = any(int_type in column_type.lower()
                                      for int_type in ['int', 'uint', 'float', 'double', 'decimal'])

                if len(filter_values) == 1:
                    # Single value filtering
                    single_value = filter_values[0]
                    param_name = f"filter_{column_name}_{local_counter}"
                    local_counter += 1

                    if is_numeric_column:
                        try:
                            if 'float' in column_type.lower() or 'double' in column_type.lower():
                                numeric_value = float(single_value)
                                all_params[param_name] = numeric_value
                                all_conditions.append(f"`{column_name}` = {{{param_name}:Float64}}")
                            else:
                                numeric_value = int(single_value)
                                all_params[param_name] = numeric_value
                                all_conditions.append(f"`{column_name}` = {{{param_name}:Int64}}")
                        except ValueError:
                            all_params[param_name] = single_value
                            all_conditions.append(f"toString(`{column_name}`) = {{{param_name}:String}}")
                    else:
                        all_params[param_name] = single_value
                        all_conditions.append(f"`{column_name}` = {{{param_name}:String}}")

                else:
                    # Multiple values
                    if is_numeric_column:
                        numeric_values = []
                        string_values = []

                        for value in filter_values:
                            try:
                                if 'float' in column_type.lower() or 'double' in column_type.lower():
                                    numeric_values.append(float(value))
                                else:
                                    numeric_values.append(int(value))
                            except ValueError:
                                string_values.append(value)

                        conditions = []

                        if numeric_values:
                            param_name = f"filter_{column_name}_nums_{local_counter}"
                            local_counter += 1
                            all_params[param_name] = numeric_values
                            
                            if 'float' in column_type.lower() or 'double' in column_type.lower():
                                conditions.append(f"`{column_name}` IN {{{param_name}:Array(Float64)}}")
                            else:
                                conditions.append(f"`{column_name}` IN {{{param_name}:Array(Int64)}}")

                        if string_values:
                            param_name = f"filter_{column_name}_strs_{local_counter}"
                            local_counter += 1
                            all_params[param_name] = string_values
                            conditions.append(f"toString(`{column_name}`) IN {{{param_name}:Array(String)}}")

                        if conditions:
                            all_conditions.append(f"({' OR '.join(conditions)})")

                    else:
                        param_name = f"filter_{column_name}_vals_{local_counter}"
                        local_counter += 1
                        all_params[param_name] = filter_values
                        all_conditions.append(f"`{column_name}` IN {{{param_name}:Array(String)}}")

            logger.info(f"Built {len(all_conditions)} generic filter conditions for table {clickhouse_table_name}")
            return all_conditions, all_params

        except Exception as e:
            logger.warning(f"Error building generic filters: {e}")
            return [], {}

    def _process_table_results(self, result_rows: List[List], table_columns: List[Dict],
                         datetime_column: Optional[str], site_name: str,
                         table_name: str, from_date: Optional[str] = None,
                         to_date: Optional[str] = None, rack_column: Optional[str] = None,
                         actual_column_names: Optional[List[str]] = None,
                         is_pump_table: bool = False,
                         pump_id_column: Optional[str] = None,
                         pump_category_column: Optional[str] = None):
        """
        Process query results into the expected format with business logic.

        Args:
            result_rows: Raw query results
            table_columns: Column specifications
            datetime_column: DateTime column name (if any)
            site_name: Site identifier
            table_name: Table identifier

        Returns:
            List of ColumnResponse objects with formatted data
        """
        # Post-filter rows by date range if dates are provided and DateTime column exists
        filtered_rows = result_rows
        if datetime_column and (from_date or to_date) and result_rows:
            try:
                from datetime import datetime as dt
                from infrastructure.utils.datetime_utils import parse_datetime
                
                # Parse date filters
                from_dt = None
                to_dt = None
                
                if from_date:
                    if isinstance(from_date, str):
                        from_dt = parse_datetime(from_date)
                    elif isinstance(from_date, dt):
                        from_dt = from_date
                
                if to_date:
                    if isinstance(to_date, str):
                        to_dt = parse_datetime(to_date)
                    elif isinstance(to_date, dt):
                        to_dt = to_date
                
                # DateTime column is always at index 0 (prepended by repository)
                datetime_index = 0
                
                if from_dt or to_dt:
                    filtered_rows = []
                    for row in result_rows:
                        if len(row) > datetime_index:
                            row_datetime_str = row[datetime_index]
                            
                            # Parse the row's datetime value
                            row_dt = None
                            if isinstance(row_datetime_str, dt):
                                row_dt = row_datetime_str
                            elif isinstance(row_datetime_str, str):
                                row_dt = parse_datetime(row_datetime_str)
                            
                            # Check if row datetime is within range
                            if row_dt:
                                include_row = True
                                
                                # Normalize timezones for comparison
                                # Make all datetimes timezone-aware for consistent comparison
                                from datetime import timezone as tz
                                
                                # Normalize row_dt
                                if not row_dt.tzinfo:
                                    row_dt_normalized = row_dt.replace(tzinfo=tz.utc)
                                else:
                                    row_dt_normalized = row_dt
                                
                                # Normalize from_dt and compare
                                if from_dt:
                                    if not from_dt.tzinfo:
                                        from_dt_normalized = from_dt.replace(tzinfo=tz.utc)
                                    else:
                                        from_dt_normalized = from_dt
                                    
                                    if row_dt_normalized < from_dt_normalized:
                                        include_row = False
                                
                                # Normalize to_dt and compare
                                if to_dt and include_row:
                                    if not to_dt.tzinfo:
                                        to_dt_normalized = to_dt.replace(tzinfo=tz.utc)
                                    else:
                                        to_dt_normalized = to_dt
                                    
                                    if row_dt_normalized > to_dt_normalized:
                                        include_row = False
                                
                                if include_row:
                                    filtered_rows.append(row)
                            else:
                                # If we can't parse datetime, exclude the row to be safe
                                logger.debug(f"Could not parse datetime value: {row_datetime_str}, excluding row")
                        else:
                            # Row doesn't have datetime, exclude it
                            logger.debug(f"Row missing datetime column at index {datetime_index}, excluding row")
                    
                    logger.info(f"Post-filtered rows: {len(result_rows)} -> {len(filtered_rows)} rows for date range {from_date} to {to_date}")
                else:
                    filtered_rows = result_rows
                    
            except Exception as filter_error:
                logger.warning(f"Error post-filtering rows by date range: {filter_error}, using all rows")
                filtered_rows = result_rows
        
        table_data = []
        expected_row_count = len(filtered_rows)
        
        if expected_row_count == 0:
            logger.warning(f"No rows returned for table {table_name} after filtering")

        for column_spec in table_columns:
            # SAFE EXTRACTION: Handle both dict and object types (defensive programming)
            try:
                if isinstance(column_spec, dict):
                    column_name = column_spec.get('columnName')
                    column_type = column_spec.get('columnType')
                else:
                    # If it's already a ColumnResponse object (shouldn't happen but handle it)
                    column_name = getattr(column_spec, 'columnName', None)
                    column_type = getattr(column_spec, 'columnType', None)
                    logger.warning(
                        f"Unexpected type in table_columns: {type(column_spec)}. "
                        f"Expected dict, got {type(column_spec).__name__}"
                    )

                if not column_name:
                    logger.warning(f"Skipping column spec with no name: {column_spec}")
                    continue

            except Exception as extract_error:
                logger.error(f"Error extracting column info from spec: {extract_error}")
                continue

            data_source = []

            # Find column index in result - SAFELY handle mixed types
            column_names = []
            for col in table_columns:
                try:
                    if isinstance(col, dict):
                        col_name = col.get('columnName')
                    else:
                        col_name = getattr(col, 'columnName', None)
                    if col_name:
                        column_names.append(col_name)
                except Exception as e:
                    logger.warning(f"Error extracting column name: {e}")
                    continue

            # Find the column index in the result rows
            # Determine if datetime is actually prepended by comparing row length to column count
            column_index = None
            
            # Check if datetime is actually in the results by comparing row length
            has_datetime_in_results = False
            if filtered_rows:
                first_row = filtered_rows[0] if filtered_rows else []
                actual_row_length = len(first_row)
                expected_column_count = len(column_names)
                
                # If row has one more column than expected, datetime is likely prepended
                if actual_row_length == expected_column_count + 1 and datetime_column:
                    has_datetime_in_results = True
                elif actual_row_length == expected_column_count:
                    has_datetime_in_results = False
                else:
                    # Mismatch - log warning but try to proceed
                    logger.warning(
                        f"Row length mismatch: actual={actual_row_length}, "
                        f"expected={expected_column_count} for table {table_name}"
                    )
                    # If datetime_column is set and row length suggests it's there, assume it's prepended
                    if datetime_column and actual_row_length > expected_column_count:
                        has_datetime_in_results = True
            
            if datetime_column and column_name == datetime_column:
                # DateTime column is at index 0 if it exists in results
                column_index = 0 if has_datetime_in_results else None
            else:
                # For other columns, find their position in column_names
                # Only adjust index if datetime is actually in the results
                for i, col_name in enumerate(column_names):
                    if col_name == column_name:
                        if has_datetime_in_results:
                            # DateTime is prepended at index 0, so all other columns are shifted by 1
                            column_index = i + 1
                        else:
                            # No datetime prepended, use position directly
                            column_index = i
                        break

            if column_index is None:
                logger.error(
                    f"Could not find column '{column_name}' in table columns list. "
                    f"Available columns: {column_names}"
                )
                # Create empty array with correct length
                data_source = [None] * expected_row_count
            else:
                logger.debug(
                    f"Column '{column_name}' in table '{table_name}': "
                    f"position in column_names={column_names.index(column_name) if column_name in column_names else 'N/A'}, "
                    f"calculated index={column_index}, "
                    f"datetime_column={datetime_column}, "
                    f"datetime_in_list={datetime_column in column_names if datetime_column else False}"
                )
            
            if filtered_rows and column_index is not None:
                # Process data rows - CRITICAL FIX: PRESERVE NULL VALUES
                for row_idx, row in enumerate(filtered_rows):
                    try:
                        if len(row) > column_index:
                            value = row[column_index]
                            
                            # CRITICAL: Process ALL values, including NULLs
                            # Do NOT skip null values - they represent missing data at specific timestamps
                            processed_value = self._convert_and_round_value(value, column_type)
                            
                            # CRITICAL: Always append, even if processed_value is None
                            data_source.append(processed_value)
                        else:
                            # Row doesn't have this column (defensive)
                            logger.warning(
                                f"Row {row_idx} in table {table_name} missing column index {column_index}. "
                                f"Row length: {len(row)}, Expected index: {column_index}"
                            )
                            data_source.append(None)
                            
                    except Exception as row_error:
                        logger.error(f"Error processing row {row_idx}: {row_error}")
                        data_source.append(None)
            
            # Validation: Ensure this column has the same length as expected
            if len(data_source) != expected_row_count:
                logger.warning(
                    f"Column '{column_name}' in table {table_name} has {len(data_source)} values "
                    f"but expected {expected_row_count}. Adjusting to match."
                )
                
                # Pad with None if too short
                if len(data_source) < expected_row_count:
                    padding_needed = expected_row_count - len(data_source)
                    data_source.extend([None] * padding_needed)
                    logger.debug(f"Padded column '{column_name}' with {padding_needed} None values")
                
                # Truncate if too long (shouldn't happen)
                elif len(data_source) > expected_row_count:
                    excess = len(data_source) - expected_row_count
                    data_source = data_source[:expected_row_count]
                    logger.warning(f"Truncated column '{column_name}' by {excess} values")

            # Create ColumnResponse object
            try:
                # Try to import and use the ColumnResponse class
                column_response = ColumnResponse(
                    columnName=column_name,
                    columnType=column_type,
                    tableName=table_name,
                    siteName=site_name,
                    dataSource=data_source
                )
                table_data.append(column_response)
                
            except ImportError:
                # Fallback to dict if ColumnResponse class not available
                logger.warning("ColumnResponse class not found, using dict instead")
                table_data.append({
                    'columnName': column_name,
                    'columnType': column_type,
                    'tableName': table_name,
                    'siteName': site_name,
                    'dataSource': data_source,
                    'racks': None  # Will be set later if rack column exists
                })

        # Final validation: All columns should have the same length
        if table_data:
            try:
                # Extract lengths safely
                lengths = []
                for col in table_data:
                    if hasattr(col, 'dataSource'):
                        lengths.append(len(col.dataSource))
                    elif isinstance(col, dict) and 'dataSource' in col:
                        lengths.append(len(col['dataSource']))
                
                unique_lengths = set(lengths)
                
                if len(unique_lengths) > 1:
                    # Create detailed length report
                    length_details = {}
                    for col in table_data:
                        if hasattr(col, 'columnName'):
                            col_name = col.columnName
                            col_len = len(col.dataSource)
                        else:
                            col_name = col.get('columnName', 'unknown')
                            col_len = len(col.get('dataSource', []))
                        length_details[col_name] = col_len
                        
                    logger.error(
                        f"Column length mismatch in table {table_name}: {length_details}. "
                        f"All columns must have the same length ({expected_row_count}) for proper temporal alignment."
                    )
                    
                    # Log details about which columns are wrong
                    for col in table_data:
                        col_name = getattr(col, 'columnName', col.get('columnName', 'unknown'))
                        col_data = getattr(col, 'dataSource', col.get('dataSource', []))
                        if len(col_data) != expected_row_count:
                            logger.error(
                                f"  - Column '{col_name}' has {len(col_data)} values, expected {expected_row_count}"
                            )
                else:
                    logger.info(
                        f"✓ Successfully processed {len(table_data)} columns for table {table_name}, "
                        f"each with {expected_row_count} values (including {sum(1 for col in table_data for v in (getattr(col, 'dataSource', [])) if v is None)} total null values)"
                    )
                    
            except Exception as validation_error:
                logger.error(f"Error during final validation: {validation_error}")

        # Extract rack data if rack column exists
        if rack_column and result_rows:
            try:
                # Use actual_column_names if provided (includes rack column if it was added)
                # Otherwise fall back to building from table_columns
                if actual_column_names:
                    query_column_names = actual_column_names
                else:
                    # Build column names list from table_columns
                    query_column_names = []
                    for col in table_columns:
                        if isinstance(col, dict):
                            query_column_names.append(col.get('columnName'))
                        else:
                            query_column_names.append(getattr(col, 'columnName', None))
                
                # Check if datetime is prepended (row length vs column count)
                has_datetime_in_results = False
                if result_rows:
                    first_row = result_rows[0] if result_rows else []
                    actual_row_length = len(first_row)
                    expected_column_count = len(query_column_names)
                    if actual_row_length == expected_column_count + 1 and datetime_column:
                        has_datetime_in_results = True
                
                # Find rack column index in the actual query column order
                rack_column_index = None
                if has_datetime_in_results:
                    # DateTime is at index 0, so we need to offset by 1
                    try:
                        # Find rack column in the actual query columns
                        rack_column_index = query_column_names.index(rack_column) + 1
                        logger.debug(f"Found rack column '{rack_column}' at query index {query_column_names.index(rack_column)}, result index {rack_column_index} (with datetime offset)")
                    except ValueError:
                        # Rack column not found in query columns (shouldn't happen, but handle gracefully)
                        logger.warning(f"Rack column '{rack_column}' not found in query columns {query_column_names}")
                        # Assume it's at the end: DateTime (0) + all query columns (1 to len) + rack (len+1)
                        rack_column_index = len(query_column_names) + 1
                else:
                    try:
                        # Find rack column in the actual query columns
                        rack_column_index = query_column_names.index(rack_column)
                        logger.debug(f"Found rack column '{rack_column}' at result index {rack_column_index} (no datetime)")
                    except ValueError:
                        # Rack column not found in query columns (shouldn't happen, but handle gracefully)
                        logger.warning(f"Rack column '{rack_column}' not found in query columns {query_column_names}")
                        # Assume it's at the end
                        rack_column_index = len(query_column_names)
                
                logger.info(
                    f"Rack extraction setup: column='{rack_column}', index={rack_column_index}, "
                    f"has_datetime={has_datetime_in_results}, query_columns={query_column_names}, "
                    f"row_length={len(result_rows[0]) if result_rows else 0}"
                )
                
                # Sample first few values to validate we're extracting from the right column
                sample_values = []
                if result_rows and len(result_rows) > 0:
                    first_row = result_rows[0]
                    if len(first_row) > rack_column_index:
                        sample_values.append(str(first_row[rack_column_index])[:50])  # First 50 chars
                    # Also log values at adjacent indices for debugging
                    for offset in [-1, 0, 1]:
                        check_idx = rack_column_index + offset
                        if 0 <= check_idx < len(first_row):
                            logger.debug(f"  Row[0][{check_idx}] = {str(first_row[check_idx])[:50]}")
                
                logger.info(f"Sample value at rack index {rack_column_index}: {sample_values[0] if sample_values else 'N/A'}")
                
                # Extract rack values from result rows
                # For pump tables, also extract PUMP_ID and PUMP_CATEGORY
                rack_values = []
                pump_id_values = []
                pump_category_values = []
                numeric_value_count = 0
                string_value_count = 0
                
                # Find indices for PUMP_ID and PUMP_CATEGORY columns if this is a pump table
                pump_id_index = None
                pump_category_index = None
                
                if is_pump_table and rack_column and rack_column.lower() == "pump":
                    if actual_column_names:
                        query_column_names = actual_column_names
                    else:
                        query_column_names = []
                        for col in table_columns:
                            if isinstance(col, dict):
                                query_column_names.append(col.get('columnName'))
                            else:
                                query_column_names.append(getattr(col, 'columnName', None))
                    
                    # Check if datetime is prepended
                    has_datetime_in_results = False
                    if result_rows:
                        first_row = result_rows[0] if result_rows else []
                        actual_row_length = len(first_row)
                        expected_column_count = len(query_column_names)
                        if actual_row_length == expected_column_count + 1 and datetime_column:
                            has_datetime_in_results = True
                    
                    # Find PUMP_ID column index
                    if pump_id_column:
                        try:
                            if has_datetime_in_results:
                                pump_id_index = query_column_names.index(pump_id_column) + 1
                            else:
                                pump_id_index = query_column_names.index(pump_id_column)
                            logger.debug(f"Found PUMP_ID column '{pump_id_column}' at result index {pump_id_index}")
                        except ValueError:
                            logger.warning(f"PUMP_ID column '{pump_id_column}' not found in query columns {query_column_names}")
                    
                    # Find PUMP_CATEGORY column index
                    if pump_category_column:
                        try:
                            if has_datetime_in_results:
                                pump_category_index = query_column_names.index(pump_category_column) + 1
                            else:
                                pump_category_index = query_column_names.index(pump_category_column)
                            logger.debug(f"Found PUMP_CATEGORY column '{pump_category_column}' at result index {pump_category_index}")
                        except ValueError:
                            logger.warning(f"PUMP_CATEGORY column '{pump_category_column}' not found in query columns {query_column_names}")
                
                # Extract rack, PUMP_ID, and PUMP_CATEGORY values
                for row_idx, row in enumerate(result_rows):
                    # Extract rack value
                    if len(row) > rack_column_index:
                        rack_value = row[rack_column_index]
                        # Convert to string, handle None/empty
                        if rack_value is None or (isinstance(rack_value, str) and not rack_value.strip()):
                            rack_values.append("NaN")
                        else:
                            rack_str = str(rack_value).strip()
                            # Validate that this looks like a rack name (not a numeric value)
                            # Rack names should not be purely numeric
                            try:
                                # Try to parse as float - if successful and it's a number, it's probably wrong
                                float_val = float(rack_str)
                                # If it's a valid number, this might be the wrong column
                                numeric_value_count += 1
                                rack_values.append("NaN")
                                if numeric_value_count <= 3:  # Log first 3 numeric values
                                    logger.warning(
                                        f"WARNING: Extracted numeric value '{rack_str}' from supposed rack column '{rack_column}' "
                                        f"at index {rack_column_index}, row {row_idx}. This suggests wrong column index."
                                    )
                            except (ValueError, TypeError):
                                # Not a number, so it's likely a valid rack name
                                string_value_count += 1
                                rack_values.append(rack_str)
                                if string_value_count <= 3:  # Log first 3 string values
                                    logger.debug(f"Extracted rack value '{rack_str}' from column '{rack_column}' at row {row_idx}")
                    else:
                        rack_values.append("NaN")
                    
                    # Extract PUMP_ID value if available
                    if pump_id_index is not None and len(row) > pump_id_index:
                        pump_id_value = row[pump_id_index]
                        if pump_id_value is None or (isinstance(pump_id_value, str) and not pump_id_value.strip()):
                            pump_id_values.append("NaN")
                        else:
                            pump_id_values.append(str(pump_id_value).strip())
                    else:
                        pump_id_values.append("NaN")
                    
                    # Extract PUMP_CATEGORY value if available
                    if pump_category_index is not None and len(row) > pump_category_index:
                        pump_category_value = row[pump_category_index]
                        if pump_category_value is None or (isinstance(pump_category_value, str) and not pump_category_value.strip()):
                            pump_category_values.append("NaN")
                        else:
                            pump_category_values.append(str(pump_category_value).strip())
                    else:
                        pump_category_values.append("NaN")
                
                # Validate extraction results
                if numeric_value_count > len(result_rows) * 0.5:  # More than 50% are numeric
                    logger.error(
                        f"ERROR: Extracted {numeric_value_count} numeric values out of {len(result_rows)} total "
                        f"from rack column '{rack_column}' at index {rack_column_index}. "
                        f"This indicates incorrect column index calculation. "
                        f"Query columns: {query_column_names}, "
                        f"Rack column position in query: {query_column_names.index(rack_column) if rack_column in query_column_names else 'NOT FOUND'}, "
                        f"Calculated result index: {rack_column_index}, "
                        f"First row sample (first 5 values): {[str(v)[:30] for v in (result_rows[0][:5] if result_rows else [])]}"
                    )
                    # Don't use these values - they're wrong
                    rack_values = ["NaN"] * len(result_rows)
                    selected_rack_column = None  # Mark as invalid
                elif numeric_value_count > 0:
                    logger.warning(
                        f"WARNING: Found {numeric_value_count} numeric values in rack extraction, "
                        f"but {string_value_count} string values. Using string values. "
                        f"Rack column: '{rack_column}', Index: {rack_column_index}"
                    )
                else:
                    logger.info(
                        f"Successfully extracted {len(rack_values)} rack values from column '{rack_column}' "
                        f"for table {table_name}. Sample values: {rack_values[:5] if rack_values else []}"
                    )
                
                # Add racks array to each ColumnResponse (except DateTime column)
                for column_data in table_data:
                    # Get column name
                    if hasattr(column_data, 'columnName'):
                        column_name = getattr(column_data, 'columnName', '')
                    elif isinstance(column_data, dict):
                        column_name = column_data.get('columnName', '')
                    else:
                        column_name = ''
                    
                    # Skip DateTime column
                    if column_name and column_name.lower() in ["datetime", "timestamp"]:
                        continue
                    
                    # Get dataSource to check for null values
                    if hasattr(column_data, 'dataSource'):
                        data_source = getattr(column_data, 'dataSource', [])
                    elif isinstance(column_data, dict):
                        data_source = column_data.get('dataSource', [])
                    else:
                        data_source = []
                    
                    # Create racks array aligned with dataSource
                    column_racks = []
                    for idx in range(len(data_source)):
                        # If dataSource value is null, rack should be NaN
                        if idx < len(data_source) and data_source[idx] is None:
                            column_racks.append("NaN")
                        elif idx < len(rack_values):
                            rack_value = rack_values[idx]
                            
                            # For pump tables with Pump column, format as pipe-delimited string
                            if is_pump_table and rack_column and rack_column.lower() == "pump":
                                # Get PUMP_ID and PUMP_CATEGORY values for this index
                                pump_id_val = pump_id_values[idx] if idx < len(pump_id_values) else "NaN"
                                pump_category_val = pump_category_values[idx] if idx < len(pump_category_values) else "NaN"
                                
                                # Format as pipe-delimited string: "Pump_04|PUMP_ID|CATEGORY"
                                formatted_rack = f"{rack_value}|{pump_id_val}|{pump_category_val}"
                                column_racks.append(formatted_rack)
                            else:
                                # For non-pump tables, use regular rack format
                                column_racks.append(rack_value)
                        else:
                            column_racks.append("NaN")
                    
                    # Ensure racks array matches dataSource length
                    if len(column_racks) != len(data_source):
                        if len(column_racks) < len(data_source):
                            column_racks.extend(["NaN"] * (len(data_source) - len(column_racks)))
                        else:
                            column_racks = column_racks[:len(data_source)]
                    
                    # Add racks to column data
                    if hasattr(column_data, 'racks'):
                        column_data.racks = column_racks
                    elif isinstance(column_data, dict):
                        column_data['racks'] = column_racks
                    else:
                        # Try to set as attribute
                        try:
                            setattr(column_data, 'racks', column_racks)
                        except:
                            pass
                    
                    logger.debug(f"Added {len(column_racks)} rack values to column '{column_name}'")
                    
            except Exception as rack_error:
                logger.warning(f"Error extracting rack data for table {table_name}: {rack_error}")
                # Continue without racks - backward compatibility

        return table_data

    def _convert_and_round_value(self, value, column_type: str):
        """
        Convert value to appropriate type based on column type.
        - Numeric types: Convert and round float values to 2 decimal places
        - String types: Return as-is
        - DateTime/Timestamp types: Convert to ISO format string

        Args:
            value: The raw value from database
            column_type: The column type (e.g., 'double', 'float', 'int', 'string', 'timestamp[ns]')

        Returns:
            Converted value appropriate for the column type, or None if value is None
        """
        if value is None:
            return None

        try:
            column_type_lower = column_type.lower() if column_type else ""

            # Handle string types - return as-is
            if any(str_type in column_type_lower for str_type in ['string', 'varchar', 'char', 'text']):
                return str(value) if value is not None else None

            # Handle datetime/timestamp types
            elif any(dt_type in column_type_lower for dt_type in ['datetime', 'timestamp', 'date', 'time']):
                # Convert UTC datetime to user timezone (Asia/Dubai) for display
                if isinstance(value, str):
                    # Parse the string value - assume it's in UTC from ClickHouse
                    # Convert to user timezone (Asia/Dubai) for display
                    try:
                        from datetime import datetime as dt
                        from infrastructure.utils.datetime_utils import DateTimeParser
                        
                        # Parse the datetime string (handles various formats)
                        dt_parsed = DateTimeParser.parse_datetime(value)
                        if dt_parsed:
                            # Assume parsed datetime is in UTC (from ClickHouse storage)
                            # Make it timezone-aware as UTC
                            dt_utc_tz = self.utc_timezone.localize(dt_parsed)
                            
                            # Convert to user timezone (Asia/Dubai)
                            dt_dubai = dt_utc_tz.astimezone(self.user_timezone)
                            
                            # Format in user timezone
                            return dt_dubai.strftime('%Y-%m-%dT%H:%M:%S')
                        else:
                            # Fallback: try direct parsing
                            value_clean = value.replace('T', ' ').split('.')[0].split('+')[0].split('-')[0].split('Z')[0]
                            dt_utc = dt.strptime(value_clean.strip(), '%Y-%m-%d %H:%M:%S')
                            dt_utc_tz = self.utc_timezone.localize(dt_utc)
                            dt_dubai = dt_utc_tz.astimezone(self.user_timezone)
                            return dt_dubai.strftime('%Y-%m-%dT%H:%M:%S')
                    except Exception as e:
                        logger.debug(f"Could not parse datetime string {value}: {e}, returning as-is")
                        # Clean up and return as-is if parsing fails
                        value = re.sub(r'[+-]\d{2}:\d{2}$', '', value)
                        value = re.sub(r'[+-]\d{4}$', '', value)
                        value = re.sub(r'Z$', '', value)
                        if ' ' in value and 'T' not in value:
                            value = value.replace(' ', 'T')
                        value = re.sub(r'\.\d+$', '', value)
                        return value.strip()
                
                elif hasattr(value, 'replace') and hasattr(value, 'strftime'):
                    # DateTime object from ClickHouse - toTimeZone already converted it to user timezone
                    # ClickHouse's toTimeZone returns a DateTime in the target timezone (but Python client may interpret as UTC)
                    # So we need to treat it as if it's already in user timezone
                    from datetime import datetime as dt
                    
                    # If timezone-aware, convert to user timezone
                    if hasattr(value, 'tzinfo') and value.tzinfo is not None:
                        # Timezone-aware datetime - convert to user timezone
                        dt_user = value.astimezone(self.user_timezone)
                        return dt_user.strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        # Naive datetime - ClickHouse's toTimeZone converted it, but Python client returns it as naive
                        # The value is already in user timezone (from toTimeZone), just format it
                        return value.strftime('%Y-%m-%dT%H:%M:%S')
                
                else:
                    return str(value)

            # Handle float/double types
            elif any(float_type in column_type_lower for float_type in ['double', 'float', 'decimal', 'real', 'numeric']):
                # Use centralized formatting: 2 decimals for |value| >= 1, 4 decimals for small values
                result = format_decimal_value(value)
                if result is None and value is not None:
                    logger.warning(f"Cannot convert value '{value}' to float for column type {column_type}")
                return result

            # Handle integer types
            elif any(int_type in column_type_lower for int_type in ['int', 'bigint', 'smallint', 'tinyint', 'integer']):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    try:
                        return int(float(value))
                    except:
                        logger.warning(f"Cannot convert value '{value}' to integer")
                        return None

            # Handle boolean types
            elif any(bool_type in column_type_lower for bool_type in ['bool', 'boolean']):
                if isinstance(value, bool):
                    return value
                elif isinstance(value, (int, float)):
                    return bool(value)
                elif isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                else:
                    return bool(value)

            # For unknown types, try to detect the type from the value itself
            else:
                return value

        except Exception as e:
            logger.warning(f"Error converting value: {e}")
            return None

    def validate_request(self, columns_list: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Validate column request with business rules.
        
        Args:
            columns_list: List of column specifications
            
        Returns:
            Validation result with business context
        """
        try:
            if not columns_list:
                return {
                    "valid": False,
                    "error": "No columns specified for data retrieval",
                    "business_impact": "Cannot proceed without column specifications"
                }

            # Business validation rules
            max_columns_per_request = 50  # Business limit
            if len(columns_list) > max_columns_per_request:
                return {
                    "valid": False,
                    "error": f"Too many columns requested ({len(columns_list)}). Maximum allowed: {max_columns_per_request}",
                    "business_impact": "Large requests may impact system performance"
                }

            # Check for required fields with business context
            invalid_specs = []
            for i, spec in enumerate(columns_list):
                missing_fields = []
                if not spec.get('siteName'):
                    missing_fields.append('siteName')
                if not spec.get('tableName'):
                    missing_fields.append('tableName')
                if not spec.get('columnName'):
                    missing_fields.append('columnName')
                
                if missing_fields:
                    invalid_specs.append({
                        "index": i,
                        "missing_fields": missing_fields,
                        "spec": spec
                    })

            if invalid_specs:
                return {
                    "valid": False,
                    "error": "Invalid column specifications found",
                    "invalid_specs": invalid_specs,
                    "business_impact": "Missing required identifiers prevent data retrieval"
                }

            return {
                "valid": True,
                "column_count": len(columns_list),
                "business_impact": "Request validated successfully"
            }

        except Exception as e:
            logger.error(f"Error validating request: {e}")
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "business_impact": "Cannot validate request due to system error"
            }