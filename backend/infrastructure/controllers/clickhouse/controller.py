import logging

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.clickhouse import ClickHouseService
from interface.schemas.clickhouse_schemas import (
    clickhouse_tables_response_schema,
    error_response_schema,
    column_data_request_schema,
    column_data_responses
)
from interface.serializers.clickhouse_serializers import (
    ColumnDataRequestSerializer,
    ColumnSpecSerializer,
    ClickHouseQueryParamsSerializer
)
from constants import ResponseMessages, ErrorMessages

logger = logging.getLogger(__name__)


class ClickHouseTablesController(APIView):
    """Controller for ClickHouse tables and columns operations"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_id="get_clickhouse_tables",
        operation_summary="Get all ClickHouse tables with columns",
        operation_description="""Retrieve all ClickHouse tables from the current database along with their column metadata in flattened format.

        This endpoint provides comprehensive information about the ClickHouse database structure as a flattened list where each column is returned as a separate object.

        **Features:**
        - Public endpoint (no authentication required)
        - Returns flattened JSON response format with each column as separate object
        - Includes comprehensive error handling
        - Provides standardized column type mapping
        - Handles empty databases gracefully
        - Automatically determines site names based on table naming patterns

        **Response Format:**
        The response includes an array of column objects, where each object contains:
        - columnName: Name of the column
        - columnType: Standardized data type (e.g., double, string, timestamp[ns, tz=Etc/UTC])
        - tableName: Name of the table containing the column
        - siteName: Site name determined from table name or default value

        **Column Type Mapping:**
        ClickHouse types are mapped to standardized types:
        - UInt8, UInt16, UInt32, UInt64, Int8, Int16, Int32, Int64 → int
        - Float32, Float64 → double
        - String, FixedString → string
        - Date, DateTime, DateTime64 → timestamp[ns, tz=Etc/UTC]
        - Array types → array
        - Boolean types → boolean
        - And other specialized mappings

        **Site Name Detection:**
        Site names are automatically determined from table names:
        - Tables containing 'jubail' → Jubail-Jazlah
        - Tables containing 'rabigh' → Rabigh3
        - Other patterns → appropriate site names
        - Default → Default-Site if no pattern matches
        """,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(
                        type=openapi.TYPE_BOOLEAN,
                        description="Operation success status",
                        default=True
                    ),
                    'message': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Response message",
                        example="Column schemas retrieved successfully for 141 columns from 1 tables"
                    ),
                    'data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'columnName': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Name of the column",
                                    example="DateTime"
                                ),
                                'columnType': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Standardized data type of the column",
                                    example="timestamp[ns, tz=Etc/UTC]"
                                ),
                                'tableName': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Name of the table containing the column",
                                    example="Jubail_Chemicals_ppm"
                                ),
                                'siteName': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Site name determined from table name",
                                    example="Jubail-Jazlah"
                                ),
                            },
                            required=['columnName', 'columnType', 'tableName', 'siteName']
                        ),
                        description="Array of column objects with metadata"
                    ),
                },
                required=["success", "message", "data"]
            ),
            500: error_response_schema
        },
        tags=["ClickHouse"]
    )
    def get(self, request):
        """Get all ClickHouse tables with their column metadata in flattened format"""
        try:
            logger.info("Controller: Processing GET request for ClickHouse tables")

            # Call service layer to get tables with columns in flattened format (static method)
            columns_data = ClickHouseService.get_tables_with_columns()

            # Count columns and tables for response message
            column_count = len(columns_data)
            
            # Count unique tables
            unique_tables = set()
            for column in columns_data:
                unique_tables.add(column.get('tableName', ''))
            table_count = len(unique_tables)

            logger.info(f"Controller: Successfully retrieved {column_count} columns from {table_count} ClickHouse tables")

            return ResponseBuilder.success(
                data=columns_data,
                message=f"Column schemas retrieved successfully for {column_count} columns from {table_count} tables"
            )

        except Exception as e:
            logger.error(f"Controller: Error retrieving ClickHouse tables - {str(e)}", exc_info=True)

            # Determine if this is a connection error or other type of error
            error_message = str(e)
            if "connection" in error_message.lower() or "clickhouse" in error_message.lower():
                return ResponseBuilder.error(
                    message=ErrorMessages.CLICKHOUSE_CONNECTION_FAILED.format(error=error_message),
                    status_code=500
                )
            else:
                return ResponseBuilder.error(
                    message=ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=error_message),
                    status_code=500
                )


@method_decorator(csrf_exempt, name='dispatch')
class ClickHouseColumnDataController(APIView):
    """Controller for ClickHouse column data retrieval operations"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_id="get_clickhouse_column_data",
        operation_summary="Retrieve filtered data from ClickHouse table columns",
        operation_description="""Retrieve actual data values from specified ClickHouse table columns with optional filtering.

        This endpoint accepts a direct array of column specifications and returns the actual data stored in those columns,
        with support for date range filtering and rack-based filtering.

        **Request Format:**
        Send a JSON array directly containing column specifications (no wrapper object):
        ```json
        [
          {
            "columnName": "INL_FL_TO_DMPF_12_MES",
            "columnType": "double",
            "tableName": "Jubail_Chemicals_ppm",
            "siteName": "Jubail-Jazlah"
          },
          {
            "columnName": "INL_FL_TO_DMPF_13_MES",
            "columnType": "double",
            "tableName": "Jubail_Chemicals_ppm",
            "siteName": "Jubail-Jazlah"
          }
        ]
        ```

        **Query Parameters:**
        - start_date: Filter data from this date onwards (supports multiple formats)
        - end_date: Filter data up to this date (supports multiple formats)
        - racks: Comma-separated list of rack names to filter by (e.g., "rack1,rack2,rack3")

        **Enhanced DateTime Filtering Modes:**
        - Range Filtering: When both start_date and end_date are provided
        - Exact Match: When only one date parameter is provided (filters entire day)
        - Default Range: When no dates are provided (automatically uses last 7 days)

        **DateTime Formats Supported:**
        - Comma-separated: 2025-06-01,10:00:00
        - Standard: 2025-06-01 10:00:00  
        - Date-only: 2025-06-01
        - ISO format: 2025-04-03T00:59:00Z

        **Example URLs:**
        ```
        # Range filtering
        POST /api/clickhouse/column-data/?start_date=2025-01-01&end_date=2025-09-15
        
        # Exact match (single date - filters entire day)
        POST /api/clickhouse/column-data/?start_date=2025-06-01
        
        # With racks filtering
        POST /api/clickhouse/column-data/?start_date=2025-01-01,00:00:00&end_date=2025-09-15,23:59:00&racks=rack1,rack2,rack3
        
        # Default mode (no dates = last 7 days)
        POST /api/clickhouse/column-data/
        ```

        **Features:**
        - Supports multiple column specifications in a single request
        - Returns actual column data values (up to 1000 rows per column)
        - Date range filtering support
        - Rack-based filtering (comma-separated values)
        - Includes data type information and metadata
        - Comprehensive validation of table and column existence
        - Performance limits: maximum 50 columns per request, 1000 rows per column

        **Response Format:**
        Returns a structured response with success flag, message, and data array:
        ```json
        {
          "success": true,
          "message": "Column data retrieved successfully for N columns",
          "data": [
            {
              "columnName": "INL_FL_TO_DMPF_12_MES",
              "columnType": "double",
              "tableName": "Jubail_Chemicals_ppm",
              "siteName": "Jubail-Jazlah",
              "dataSource": [...]
            }
          ]
        }
        ```

        **Performance Considerations:**
        - Limited to 1000 rows per column to ensure reasonable response times
        - Maximum 50 columns per request to prevent resource exhaustion
        - Date range cannot exceed 5 years
        - Maximum 100 racks per request
        - Uses parameterized queries for security and performance

        **Error Handling:**
        - Validates table and column existence before data retrieval
        - Validates date ranges and rack names
        - Returns specific error messages for invalid table/column combinations
        - Handles ClickHouse connection and query execution errors gracefully

        **Data Types:**
        Supports all ClickHouse data types including:
        - Numeric types (UInt8-64, Int8-64, Float32/64, Double)
        - String types (String, FixedString)
        - Date/Time types (Date, DateTime, DateTime64)
        - Complex types (Array, Tuple, Nested)
        - Nullable variants of all types
        """,
        manual_parameters=[
            openapi.Parameter(
                'start_date',
                openapi.IN_QUERY,
                description='Start date for filtering data (ISO format: YYYY-MM-DD HH:MM:SS)',
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'end_date',
                openapi.IN_QUERY,
                description='End date for filtering data (ISO format: YYYY-MM-DD HH:MM:SS)',
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                'racks',
                openapi.IN_QUERY,
                description='Comma-separated list of rack names for filtering',
                type=openapi.TYPE_STRING,
                required=False
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'columnName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the column'),
                    'columnType': openapi.Schema(type=openapi.TYPE_STRING, description='Data type of the column'),
                    'tableName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the table'),
                    'siteName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the site'),
                },
                required=['columnName', 'columnType', 'tableName', 'siteName']
            ),
            description="Array of column specifications"
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'columnName': openapi.Schema(type=openapi.TYPE_STRING),
                                'columnType': openapi.Schema(type=openapi.TYPE_STRING),
                                'tableName': openapi.Schema(type=openapi.TYPE_STRING),
                                'siteName': openapi.Schema(type=openapi.TYPE_STRING),
                                'dataSource': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                            }
                        )
                    )
                }
            ),
            400: error_response_schema,
            500: error_response_schema
        },
        tags=["ClickHouse"]
    )
    def post(self, request):
        """Retrieve filtered data from specified ClickHouse table columns"""
        try:
            logger.info("Controller: Processing POST request for ClickHouse column data with filters")

            # Validate query parameters first
            query_params_serializer = ClickHouseQueryParamsSerializer(data=request.query_params)
            if not query_params_serializer.is_valid():
                logger.warning(f"Controller: Query parameter validation failed: {query_params_serializer.errors}")
                
                # Format query parameter validation errors
                error_messages = []
                for field, errors in query_params_serializer.errors.items():
                    if isinstance(errors, list):
                        for error in errors:
                            error_messages.append(f"{field}: {error}")
                    else:
                        error_messages.append(f"{field}: {errors}")

                return ResponseBuilder.error(
                    message=f"Query parameter validation failed: {'; '.join(error_messages)}",
                    status_code=400
                )

            # Extract validated query parameters
            validated_query_params = query_params_serializer.validated_data
            start_date = validated_query_params.get('start_date')
            end_date = validated_query_params.get('end_date')
            racks_list = validated_query_params.get('racks', [])
            filtering_mode = validated_query_params.get('filtering_mode', 'default')

            logger.info(f"Controller: Validated query parameters - mode: {filtering_mode}, start_date: {start_date}, end_date: {end_date}, racks: {racks_list}")

            # Validate request body data as a direct array using ListSerializer
            body_serializer = ColumnDataRequestSerializer(data=request.data)

            if not body_serializer.is_valid():
                logger.warning(f"Controller: Request body validation failed: {body_serializer.errors}")

                # Format validation errors for response
                error_messages = []
                if hasattr(body_serializer, 'errors'):
                    if isinstance(body_serializer.errors, list):
                        # Handle array-level errors
                        for i, item_errors in enumerate(body_serializer.errors):
                            if isinstance(item_errors, dict):
                                for field, errors in item_errors.items():
                                    if isinstance(errors, list):
                                        for error in errors:
                                            error_messages.append(f"Item {i+1} - {field}: {error}")
                                    else:
                                        error_messages.append(f"Item {i+1} - {field}: {errors}")
                    elif isinstance(body_serializer.errors, dict):
                        # Handle non-field errors
                        for field, errors in body_serializer.errors.items():
                            if isinstance(errors, list):
                                for error in errors:
                                    error_messages.append(f"{field}: {error}")
                            else:
                                error_messages.append(f"{field}: {errors}")
                    else:
                        error_messages.append(str(body_serializer.errors))

                return ResponseBuilder.error(
                    message=f"Request body validation failed: {'; '.join(error_messages)}",
                    status_code=400
                )

            # Extract validated body data
            validated_data = body_serializer.validated_data
            logger.info(f"Controller: Processing request for {len(validated_data)} validated column specifications with filtering")

            # Convert to format expected by service layer
            columns_specs = []
            for spec in validated_data:
                columns_specs.append({
                    'table_name': spec['tableName'],
                    'column_name': spec['columnName'],
                    'column_type': spec['columnType'],
                    'site_name': spec['siteName']
                })

            # Prepare filter parameters for service layer
            filter_params = {
                'start_date': start_date,
                'end_date': end_date,
                'racks': racks_list,
                'filtering_mode': filtering_mode
            }

            # Call service layer to get filtered column data
            response_data = ClickHouseService.get_columns_data_with_filters(columns_specs, filter_params)

            logger.info(f"Controller: Successfully retrieved filtered data for {len(response_data)} columns")

            # Create response message with enhanced filter info
            filter_info = []
            if filtering_mode == 'default':
                filter_info.append("with default 7-day range")
            elif filtering_mode == 'exact':
                if start_date:
                    filter_info.append(f"for exact date {start_date.strftime('%Y-%m-%d')}")
            elif filtering_mode == 'range':
                if start_date and end_date:
                    filter_info.append(f"from {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
            
            if racks_list:
                filter_info.append(f"for {len(racks_list)} racks")
            
            filter_description = f" ({', '.join(filter_info)})" if filter_info else ""
            message = f"Column data retrieved successfully for {len(response_data)} columns{filter_description}"

            # Return response using existing ResponseBuilder
            return ResponseBuilder.success(
                data=response_data,
                message=message
            )

        except Exception as e:
            logger.error(f"Controller: Error retrieving ClickHouse column data - {str(e)}", exc_info=True)

            # Determine error type and return appropriate response
            error_message = str(e)

            # Check for validation errors (these should return 400)
            if any(phrase in error_message.lower() for phrase in [
                "invalid input", "does not exist", "column specification",
                "too many columns", "must contain", "must be an",
                "validation failed", "invalid date", "invalid rack"
            ]):
                return ResponseBuilder.error(
                    message=error_message,
                    status_code=400
                )

            # Check for connection errors (these should return 500)
            elif "connection" in error_message.lower() or "clickhouse" in error_message.lower():
                return ResponseBuilder.error(
                    message=ErrorMessages.CLICKHOUSE_CONNECTION_FAILED.format(error=error_message),
                    status_code=500
                )

            # All other errors are query-related (500)
            else:
                return ResponseBuilder.error(
                    message=ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=error_message),
                    status_code=500
                )