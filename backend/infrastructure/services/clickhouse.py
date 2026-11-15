"""
ClickHouse service module for handling business logic related to ClickHouse tables and columns.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from config.optimized_clickhouse_connector import execute_optimized_clickhouse_query, get_optimized_clickhouse_connector
from constants import ErrorMessages

logger = logging.getLogger(__name__)


class ClickHouseService:
    """
    Service class for managing ClickHouse-related business logic.
    Handles data processing and coordination between controller and repository layers.
    """

    @staticmethod
    def get_tables_with_columns() -> List[Dict[str, Any]]:
        """
        Retrieve all ClickHouse tables with their column information in flattened format using optimized connector.

        Returns:
            List[Dict[str, Any]]: List of column objects with columnName, columnType, tableName, siteName

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.info("Service: Fetching all ClickHouse tables with columns using optimized connector")

            # Use optimized connector to get tables and columns directly
            query = """
                SELECT 
                    table AS table_name,
                    name AS column_name,
                    type AS column_type
                FROM system.columns 
                WHERE database = currentDatabase()
                AND table NOT LIKE '.%'
                ORDER BY table, position
            """
            
            result = execute_optimized_clickhouse_query(
                query,
                use_cache=True,
                cache_ttl=1800  # Cache table schema for 30 minutes
            )
            
            tables_data = []
            current_table = None
            current_columns = []
            
            # Group columns by table
            for row in result.result_rows:
                table_name, column_name, column_type = row
                
                if current_table != table_name:
                    # Save previous table if exists
                    if current_table and current_columns:
                        tables_data.append({
                            'table_name': current_table,
                            'columns': current_columns.copy()
                        })
                    
                    # Start new table
                    current_table = table_name
                    current_columns = []
                
                current_columns.append({
                    'column_name': column_name,
                    'column_type': column_type
                })
            
            # Add last table
            if current_table and current_columns:
                tables_data.append({
                    'table_name': current_table,
                    'columns': current_columns
                })

            # Transform data to flattened column format
            flattened_columns = ClickHouseService._transform_to_flattened_columns(tables_data)

            logger.info(f"Service: Successfully processed {len(flattened_columns)} columns from {len(tables_data)} tables using optimized connector")
            return flattened_columns

        except Exception as e:
            logger.error(f"Service: Error fetching ClickHouse tables with columns - {str(e)}", exc_info=True)
            raise Exception(f"Failed to fetch ClickHouse tables and columns: {str(e)}")

    @staticmethod
    def _transform_to_flattened_columns(tables_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform table-column structure to flattened column format.

        Args:
            tables_data: List of table dictionaries from repository

        Returns:
            List of flattened column dictionaries with columnName, columnType, tableName, siteName
        """
        flattened_columns = []

        for table in tables_data:
            try:
                table_name = table.get("table_name", "")
                columns = table.get("columns", [])

                # Determine site name based on table name or use a default
                site_name = ClickHouseService._determine_site_name(table_name)

                for column in columns:
                    try:
                        # Transform each column to the required format
                        flattened_column = {
                            "columnName": str(column.get("name", "")),
                            "columnType": ClickHouseService._map_clickhouse_type_to_standard(column.get("type", "")),
                            "tableName": table_name,
                            "siteName": site_name
                        }

                        flattened_columns.append(flattened_column)

                    except Exception as column_error:
                        logger.warning(f"Service: Error processing column {column.get('name', 'unknown')} in table {table_name}: {str(column_error)}")
                        # Include the column with safe defaults if there's an error
                        flattened_column = {
                            "columnName": str(column.get("name", "unknown")),
                            "columnType": "unknown",
                            "tableName": table_name,
                            "siteName": site_name
                        }
                        flattened_columns.append(flattened_column)

                logger.debug(f"Service: Processed table '{table_name}' with {len(columns)} columns")

            except Exception as table_error:
                logger.warning(f"Service: Error processing table {table.get('table_name', 'unknown')}: {str(table_error)}")
                # Skip this table if there's an error

        return flattened_columns

    @staticmethod
    def _determine_site_name(table_name: str) -> str:
        """
        Determine the site name based on the table name.

        Args:
            table_name: Name of the table

        Returns:
            Site name string
        """
        # Extract site name from table name patterns
        table_name_lower = table_name.lower()
        
        # Define site name mappings based on table naming patterns
        site_mappings = {
            'jubail': 'Jubail-Jazlah',
            'rabigh': 'Rabigh3',
            'yanbu': 'Yanbu',
            'jeddah': 'Jeddah',
            'riyadh': 'Riyadh',
            'dammam': 'Dammam'
        }
        
        # Check for site name patterns in table name
        for key, site_name in site_mappings.items():
            if key in table_name_lower:
                return site_name
        
        # Default site name if no pattern matches
        return 'Default-Site'

    @staticmethod
    def _map_clickhouse_type_to_standard(clickhouse_type: str) -> str:
        """
        Map ClickHouse data types to standardized type names.

        Args:
            clickhouse_type: ClickHouse column type

        Returns:
            Standardized type name
        """
        if not clickhouse_type:
            return "unknown"
        
        # Convert to lowercase for comparison
        type_lower = clickhouse_type.lower()
        
        # Handle nullable types
        if type_lower.startswith('nullable('):
            # Extract inner type from Nullable(Type)
            inner_type = clickhouse_type[9:-1] if clickhouse_type.endswith(')') else clickhouse_type[9:]
            return ClickHouseService._map_clickhouse_type_to_standard(inner_type)
        
        # Type mappings
        type_mappings = {
            # Integer types
            'int8': 'int',
            'int16': 'int',
            'int32': 'int',
            'int64': 'int',
            'uint8': 'int',
            'uint16': 'int',
            'uint32': 'int',
            'uint64': 'int',
            
            # Float types
            'float32': 'double',
            'float64': 'double',
            'double': 'double',
            
            # String types
            'string': 'string',
            'fixedstring': 'string',
            
            # Date/Time types
            'date': 'timestamp[ns, tz=Etc/UTC]',
            'datetime': 'timestamp[ns, tz=Etc/UTC]',
            'datetime64': 'timestamp[ns, tz=Etc/UTC]',
            'timestamp': 'timestamp[ns, tz=Etc/UTC]',
            
            # Boolean
            'boolean': 'boolean',
            'bool': 'boolean',
            
            # UUID
            'uuid': 'string'
        }
        
        # Check for exact matches first
        for clickhouse_type_pattern, standard_type in type_mappings.items():
            if clickhouse_type_pattern in type_lower:
                return standard_type
        
        # Special handling for complex types
        if 'array' in type_lower:
            return 'array'
        elif 'tuple' in type_lower:
            return 'object'
        elif 'enum' in type_lower:
            return 'string'
        
        # Return original type if no mapping found
        return clickhouse_type

    @staticmethod
    def get_tables_only() -> List[str]:
        """
        Retrieve only the table names (without column information) for lighter operations.

        Returns:
            List[str]: List of table names

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.info("Service: Fetching ClickHouse table names only")

            repository = ClickHouseRepository()
            table_names = repository.get_all_tables()

            logger.info(f"Service: Successfully retrieved {len(table_names)} table names")
            return table_names

        except Exception as e:
            logger.error(f"Service: Error fetching ClickHouse table names - {str(e)}", exc_info=True)
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to fetch ClickHouse table names: {str(e)}"))

    @staticmethod
    def get_table_columns_only(table_name: str) -> List[Dict[str, Any]]:
        """
        Retrieve columns for a specific table only.

        Args:
            table_name: Name of the table to get columns for

        Returns:
            List[Dict[str, Any]]: List of column information

        Raises:
            Exception: If database operation fails or table doesn't exist
        """
        try:
            logger.info(f"Service: Fetching columns for table '{table_name}'")

            repository = ClickHouseRepository()

            # Check if table exists first
            if not repository.table_exists(table_name):
                raise Exception(f"Table '{table_name}' does not exist")

            columns = repository.get_table_columns(table_name)
            processed_columns = ClickHouseService._process_columns_data(columns)

            logger.info(f"Service: Successfully retrieved {len(processed_columns)} columns for table '{table_name}'")
            return processed_columns

        except Exception as e:
            logger.error(f"Service: Error fetching columns for table '{table_name}' - {str(e)}", exc_info=True)
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to fetch columns for table '{table_name}': {str(e)}"))

    @staticmethod
    def _process_columns_data(columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and transform raw column data to ensure consistent format.

        Args:
            columns: List of column dictionaries from repository

        Returns:
            List of processed column dictionaries with consistent format
        """
        processed_columns = []

        for column in columns:
            try:
                # Ensure all required fields are present and properly formatted
                processed_column = {
                    "name": str(column.get("name", "")),
                    "type": str(column.get("type", "")),
                    "nullable": bool(column.get("nullable", False))
                }

                processed_columns.append(processed_column)

            except Exception as e:
                logger.warning(f"Service: Error processing column {column.get('name', 'unknown')}: {str(e)}")
                # Include the column with safe defaults if there's an error
                processed_column = {
                    "name": str(column.get("name", "unknown")),
                    "type": "unknown",
                    "nullable": False
                }
                processed_columns.append(processed_column)

        return processed_columns

    @staticmethod
    def get_database_information() -> Dict[str, Any]:
        """
        Get general information about the ClickHouse database.

        Returns:
            Dict[str, Any]: Database information including name and statistics

        Raises:
            Exception: If database operation fails
        """
        try:
            logger.info("Service: Fetching ClickHouse database information")

            repository = ClickHouseRepository()
            db_info = repository.get_database_info()

            # Enhance with additional computed information
            enhanced_info = {
                "database_name": db_info.get("database_name", "unknown"),
                "total_tables": db_info.get("table_count", 0),
                "has_tables": db_info.get("table_count", 0) > 0
            }

            logger.info(f"Service: Successfully retrieved database information for '{enhanced_info['database_name']}'")
            return enhanced_info

        except Exception as e:
            logger.error(f"Service: Error fetching ClickHouse database information - {str(e)}", exc_info=True)
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to fetch ClickHouse database information: {str(e)}"))

    @staticmethod
    def get_database_health() -> Dict[str, Any]:
        """
        Check ClickHouse database health with timing measurement.

        Returns:
            Dict[str, Any]: Health status including response time, connection status, and error details

        Raises:
            Exception: If health check encounters critical errors
        """
        start_time = time.time()
        try:
            logger.info("Service: Checking ClickHouse database health")

            # Get database info which includes connection test
            repository = ClickHouseRepository()
            db_info = repository.get_database_info()
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            health_status = {
                "status": "healthy" if db_info.get("connection_successful") else "unhealthy",
                "database_name": db_info.get("database_name"),
                "connection_successful": db_info.get("connection_successful", False),
                "response_time_ms": round(response_time, 2),
                "table_count": db_info.get("table_count", 0)
            }

            # Add error details if connection failed
            if not db_info.get("connection_successful"):
                health_status["error"] = db_info.get("error", "Unknown connection error")

            logger.info(f"Service: Database health check completed - Status: {health_status['status']}, Response time: {health_status['response_time_ms']}ms")
            return health_status

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Service: Error during database health check - {str(e)}", exc_info=True)

            error_health_status = {
                "status": "unhealthy",
                "connection_successful": False,
                "response_time_ms": round(response_time, 2),
                "error": str(e)
            }

            return error_health_status

    @staticmethod
    def get_columns_data(columns_specs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Retrieve actual data for multiple columns across multiple tables using optimized queries.

        Args:
            columns_specs: List of dictionaries with 'table_name', 'column_name', 'column_type', and 'site_name' keys

        Returns:
            List[Dict[str, Any]]: List containing column data with only the required fields

        Raises:
            Exception: If validation fails or database operations fail
        """
        try:
            logger.info(f"Service: Processing request for {len(columns_specs)} column data specifications")

            # Validation
            if not columns_specs or not isinstance(columns_specs, list):
                raise Exception("Invalid input: columns must be a non-empty array")

            if len(columns_specs) > 50:  # Max 50 columns per request
                raise Exception("Too many columns requested. Maximum 50 columns allowed per request")

            results = []

            # Process column specifications using optimized connector with batching
            for spec in columns_specs:
                try:
                    table_name = spec.get('table_name')
                    column_name = spec.get('column_name')
                    column_type = spec.get('column_type', 'unknown')
                    site_name = spec.get('site_name', 'Default-Site')

                    # Use optimized connector to get column data directly
                    query = f"""
                        SELECT `{column_name}`
                        FROM `{table_name}`
                        WHERE `{column_name}` IS NOT NULL
                        ORDER BY `{column_name}` DESC
                        LIMIT 1000
                    """
                    
                    result = execute_optimized_clickhouse_query(
                        query,
                        use_cache=True,
                        cache_ttl=300  # Cache column data for 5 minutes
                    )
                    
                    # Extract data from result
                    data_source = [row[0] for row in result.result_rows if row[0] is not None]

                    # Create result with only the required 5 fields
                    result_item = {
                        "columnName": column_name,
                        "columnType": column_type,
                        "tableName": table_name,
                        "siteName": site_name,
                        "dataSource": data_source
                    }

                    results.append(result_item)

                    logger.debug(f"Service: Successfully processed column '{column_name}' from table '{table_name}' with {len(data_source)} rows using optimized connector")

                except Exception as column_error:
                    logger.error(f"Service: Error processing column '{table_name}.{column_name}': {str(column_error)}")
                    raise Exception(f"Error processing column '{table_name}.{column_name}': {str(column_error)}")

            logger.info(f"Service: Successfully processed {len(results)} column data requests")
            return results

        except Exception as e:
            logger.error(f"Service: Error retrieving columns data - {str(e)}", exc_info=True)
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to retrieve columns data: {str(e)}"))

    @staticmethod
    def get_columns_data_with_filters(columns_specs: List[Dict[str, str]], filter_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve filtered data for multiple columns across multiple tables with enhanced date and rack filtering.

        Enhanced DateTime Filtering Modes:
        - Range Filtering: When both start_date and end_date are provided
        - Exact Match: When only one date parameter is provided
        - Default Range: When no dates are provided (last 7 days)

        Args:
            columns_specs: List of dictionaries with 'table_name', 'column_name', 'column_type', and 'site_name' keys
            filter_params: Dictionary containing 'start_date', 'end_date', 'racks', and 'filtering_mode' parameters

        Returns:
            List[Dict[str, Any]]: List containing filtered column data with only the required fields

        Raises:
            Exception: If validation fails or database operations fail
        """
        try:
            start_date = filter_params.get('start_date')
            end_date = filter_params.get('end_date')
            racks_list = filter_params.get('racks', [])
            filtering_mode = filter_params.get('filtering_mode', 'default')

            logger.info(f"Service: Processing filtered request for {len(columns_specs)} column data specifications")
            logger.info(f"Service: Filters - mode: {filtering_mode}, start_date: {start_date}, end_date: {end_date}, racks: {racks_list}")

            # Validation
            if not columns_specs or not isinstance(columns_specs, list):
                raise Exception("Invalid input: columns must be a non-empty array")

            if len(columns_specs) > 50:  # Max 50 columns per request
                raise Exception("Too many columns requested. Maximum 50 columns allowed per request")

            # Validate enhanced filter parameters
            ClickHouseService._validate_enhanced_filter_params(filter_params)

            repository = ClickHouseRepository()

            # Convert column specs to the format expected by repository (legacy format)
            legacy_specs = []
            processed_specs = []
            
            for spec in columns_specs:
                site_name = spec.get('site_name', '')
                table_name = spec.get('table_name', '')
                
                # Convert siteName to table prefix format (replace hyphens with underscores)
                site_prefix = site_name.replace('-', '_') if site_name else ''
                
                # Construct full table name: siteName_tableName
                full_table_name = f"{site_prefix}_{table_name}" if site_prefix else table_name
                
                logger.info(f"Service: Converting siteName '{site_name}' + tableName '{table_name}' -> full table '{full_table_name}'")
                
                # Store processed spec with full table name for validation
                legacy_specs.append({
                    'table_name': full_table_name,
                    'column_name': spec.get('column_name')
                })
                
                # Keep original spec with full table name for later use
                processed_specs.append({
                    'table_name': full_table_name,
                    'column_name': spec.get('column_name'),
                    'column_type': spec.get('column_type', 'unknown'),
                    'site_name': site_name,
                    'original_table_name': table_name  # Keep original for response
                })

            # Use optimized batch validation to reduce queries
            validation_result = repository.batch_validate_columns(legacy_specs)

            if not validation_result["valid"]:
                # Provide detailed error messages
                error_messages = validation_result.get("errors", ["Validation failed"])
                raise Exception(f"Validation failed: {'; '.join(error_messages)}")

            results = []

            # Process only valid column specifications using enhanced filtered method
            valid_legacy_specs = validation_result["valid_specs"]
            for i, legacy_spec in enumerate(valid_legacy_specs):
                try:
                    full_table_name = legacy_spec["table_name"]
                    column_name = legacy_spec["column_name"]
                    
                    # Get original processed spec to access additional fields
                    original_spec = processed_specs[i]
                    column_type = original_spec.get('column_type', 'unknown')
                    site_name = original_spec.get('site_name', 'jubail_data')
                    original_table_name = original_spec.get('original_table_name', full_table_name)

                    logger.info(f"Service: Querying full table '{full_table_name}' for column '{column_name}'")

                    # Use enhanced filtered method for data retrieval with FULL table name
                    column_data = repository.get_column_data_with_enhanced_filters(
                        full_table_name,  # Use the constructed full table name
                        column_name, 
                        start_date=start_date,
                        end_date=end_date,
                        racks=racks_list,
                        filtering_mode=filtering_mode,
                        limit=1000
                    )

                    # Create result with only the required 5 fields
                    result_item = {
                        "columnName": column_name,
                        "columnType": column_type,
                        "tableName": original_table_name,  # Return original table name without prefix
                        "siteName": site_name,
                        "dataSource": column_data["data_source"]
                    }

                    results.append(result_item)

                    logger.debug(f"Service: Successfully processed filtered column '{column_name}' from table '{table_name}' using {filtering_mode} mode")

                except Exception as column_error:
                    logger.error(f"Service: Error processing filtered column '{table_name}.{column_name}': {str(column_error)}")
                    raise Exception(f"Error processing filtered column '{table_name}.{column_name}': {str(column_error)}")

            logger.info(f"Service: Successfully processed {len(results)} filtered column data requests using {filtering_mode} filtering mode")
            return results

        except Exception as e:
            logger.error(f"Service: Error retrieving filtered columns data - {str(e)}", exc_info=True)
            raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=f"Failed to retrieve filtered columns data: {str(e)}"))

    @staticmethod
    def _validate_enhanced_filter_params(filter_params: Dict[str, Any]) -> None:
        """
        Validate enhanced filter parameters for consistency and safety.

        Args:
            filter_params: Dictionary containing filter parameters including filtering_mode

        Raises:
            Exception: If filter parameters are invalid
        """
        start_date = filter_params.get('start_date')
        end_date = filter_params.get('end_date')
        racks_list = filter_params.get('racks', [])
        filtering_mode = filter_params.get('filtering_mode', 'default')

        # Validate filtering mode
        valid_modes = ['range', 'exact', 'default']
        if filtering_mode not in valid_modes:
            raise Exception(f"Invalid filtering mode '{filtering_mode}'. Valid modes: {', '.join(valid_modes)}")

        # Date validation (these should already be processed by the serializer)
        if filtering_mode == 'range' and start_date and end_date:
            if start_date >= end_date:
                raise Exception("start_date must be earlier than end_date in range filtering mode")
                
            # Check for reasonable date range
            date_diff = end_date - start_date
            if date_diff.days > 1825:  # 5 years
                raise Exception("Date range cannot exceed 5 years")
        
        elif filtering_mode == 'exact':
            if not (start_date and end_date):
                raise Exception("Both start_date and end_date must be set for exact match filtering mode")

        elif filtering_mode == 'default':
            if not (start_date and end_date):
                raise Exception("Default filtering mode should have both dates set by serializer")

        # Racks validation
        if racks_list:
            if not isinstance(racks_list, list):
                raise Exception("racks must be a list")
                
            if len(racks_list) > 100:
                raise Exception("Maximum 100 racks allowed per request")
                
            # Validate each rack name
            import re
            for rack in racks_list:
                if not isinstance(rack, str):
                    raise Exception("All rack names must be strings")
                if not re.match(r'^[a-zA-Z0-9_-]+$', rack):
                    raise Exception(f"Invalid rack name '{rack}'. Rack names must contain only alphanumeric characters, underscores, and hyphens")

        logger.debug(f"Service: Enhanced filter parameters validation passed for {filtering_mode} mode")

    @staticmethod
    def validate_columns_request(columns_specs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Validate a columns data request without executing queries.

        Args:
            columns_specs: List of column specifications to validate

        Returns:
            Dict[str, Any]: Validation results with details about each column specification
        """
        try:
            logger.info(f"Service: Validating {len(columns_specs) if columns_specs else 0} column specifications")

            validation_results = {
                "valid": True,
                "errors": [],
                "column_validations": []
            }

            if not columns_specs or not isinstance(columns_specs, list):
                validation_results["valid"] = False
                validation_results["errors"].append("Columns must be a non-empty array")
                return validation_results

            if len(columns_specs) > 50:
                validation_results["valid"] = False
                validation_results["errors"].append("Too many columns requested. Maximum 50 columns allowed per request")
                return validation_results

            # Validate each column specification
            for i, column_spec in enumerate(columns_specs):
                column_validation = {
                    "index": i + 1,
                    "valid": True,
                    "errors": []
                }

                try:
                    if not isinstance(column_spec, dict):
                        column_validation["valid"] = False
                        column_validation["errors"].append("Must be an object")
                        continue

                    table_name = column_spec.get("table_name")
                    column_name = column_spec.get("column_name")
                    column_type = column_spec.get("column_type")
                    site_name = column_spec.get("site_name")

                    if not all([table_name, column_name, column_type, site_name]):
                        column_validation["valid"] = False
                        column_validation["errors"].append("Must contain 'table_name', 'column_name', 'column_type', and 'site_name'")
                        continue

                    repository = ClickHouseRepository()

                    # Check table existence
                    if not repository.table_exists(table_name):
                        column_validation["valid"] = False
                        column_validation["errors"].append(f"Table '{table_name}' does not exist")

                    # Check column existence
                    elif not repository.validate_column_exists(table_name, column_name):
                        column_validation["valid"] = False
                        column_validation["errors"].append(f"Column '{column_name}' does not exist in table '{table_name}'")

                    column_validation["table_name"] = table_name
                    column_validation["column_name"] = column_name
                    column_validation["column_type"] = column_type
                    column_validation["site_name"] = site_name

                except Exception as e:
                    column_validation["valid"] = False
                    column_validation["errors"].append(f"Validation error: {str(e)}")

                validation_results["column_validations"].append(column_validation)

                if not column_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend([f"Column {i+1}: {error}" for error in column_validation["errors"]])

            logger.info(f"Service: Validation completed - Valid: {validation_results['valid']}, Total errors: {len(validation_results['errors'])}")
            return validation_results

        except Exception as e:
            logger.error(f"Service: Error validating columns request - {str(e)}", exc_info=True)
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "column_validations": []
            }