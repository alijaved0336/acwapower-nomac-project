"""
Column Data Source Controller
Handles POST requests for retrieving column data from multiple sites/tables with DateTime filtering.
"""
import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from typing import List, Dict, Any, Optional

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.multiSiteColumnService import (
    MultiSiteColumnDataService, ColumnRequest, ColumnResponse
)
from infrastructure.utils.parameter_parsers import ParameterParsers
from infrastructure.utils.datetime_utils import DateTimeParser
from interface.serializers.columnDataSourceSerializers import (
    ColumnDataSourceRequestSerializer,
    ColumnDataSourceResponseSerializer,
    DateTimeParameterSerializer,
    EXAMPLE_REQUEST_PAYLOAD,
    EXAMPLE_RESPONSE_PAYLOAD
)

logger = logging.getLogger(__name__)


class ColumnDataSourceController(APIView):
    """
    Column Data Source API Controller

    Provides optimized column data retrieval across multiple sites and tables
    with flexible DateTime filtering capabilities.
    """
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multi_site_service = MultiSiteColumnDataService()

    # Removed: _parse_rack_parameter method - now using shared utility
    
    @swagger_auto_schema(
        operation_id="get_column_data_sources",
        operation_summary="Retrieve column data from multiple sites/tables",
        operation_description="""
        Retrieve actual data values for specified columns across multiple sites and tables with DateTime filtering.
        
        **DateTime Filtering Modes:**
        - **Range Filtering**: When both `from_date` and `to_date` are provided
        - **Exact Match**: When only one date parameter is provided
        - **Default Range**: When no dates are provided (last 7 days)
        
        **DateTime Formats Supported:**
        - Comma-separated: `2025-06-01,10:00:00`
        - Standard: `2025-06-01 10:00:00`  
        - Date-only: `2025-06-01`
        
        **Performance Characteristics:**
        - Concurrent processing across multiple sites and tables
        - Optimized file selection using directory structure
        - Single I/O operation per table for multiple columns
        - Memory-efficient streaming for large datasets
        
        **Request Limits:**
        - Maximum 100 column requests per call
        - Date range limits are configurable via MAX_DATE_RANGE_DAYS environment variable (no limit by default)
        - Automatic fallback to existing services on failure
        """,
        manual_parameters=[
            openapi.Parameter(
                'from_date',
                openapi.IN_QUERY,
                description="Start date/time for filtering. Formats: 'YYYY-MM-DD,HH:MM:SS' or 'YYYY-MM-DD'. "
                           "If only from_date provided, performs exact match.",
                type=openapi.TYPE_STRING,
                format='datetime',
                required=False,
                example="2025-06-01,10:00:00"
            ),
            openapi.Parameter(
                'to_date', 
                openapi.IN_QUERY,
                description="End date/time for filtering. Formats: 'YYYY-MM-DD,HH:MM:SS' or 'YYYY-MM-DD'. "
                           "If only to_date provided, performs exact match.",
                type=openapi.TYPE_STRING,
                format='datetime',
                required=False,
                example="2025-06-05,10:00:00"
            ),
            openapi.Parameter(
                'rack',
                openapi.IN_QUERY,
                description="Filter records by rack/trailer value. Supports single rack (e.g., 'rack_02') or "
                           "comma-separated multiple racks (e.g., 'rack_02,rack_03,rack_05'). "
                           "Will filter on 'rack' column if available, otherwise on 'trailer' column if available. "
                           "Multiple racks use OR logic (matches ANY specified rack).",
                type=openapi.TYPE_STRING,
                required=False,
                example="rack_02,rack_03,rack_05"
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'columnName': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Name of the column to retrieve data for",
                        example="INL_FL_TO_DMPF_12_MES"
                    ),
                    'columnType': openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        description="Data type of the column",
                        example="double"
                    ),
                    'tableName': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Name of the table containing the column",
                        example="Jubail_Chemicals_ppm"
                    ),
                    'siteName': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Name of the site containing the table", 
                        example="Jubail-Jazlah"
                    )
                },
                required=['columnName', 'columnType', 'tableName', 'siteName']
            ),
            description="Array of column requests to process",
            example=EXAMPLE_REQUEST_PAYLOAD
        ),
        responses={
            200: openapi.Response(
                description="Successfully retrieved column data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Column data retrieved successfully"),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'columnName': openapi.Schema(type=openapi.TYPE_STRING),
                                    'columnType': openapi.Schema(type=openapi.TYPE_STRING),
                                    'tableName': openapi.Schema(type=openapi.TYPE_STRING),
                                    'siteName': openapi.Schema(type=openapi.TYPE_STRING),
                                    'dataSource': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING),
                                        description="Array of actual column data values"
                                    )
                                }
                            ),
                            example=EXAMPLE_RESPONSE_PAYLOAD
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid request parameters or payload",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid request data"),
                        'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Internal server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Internal processing error")
                    }
                )
            )
        },
        tags=["Column Data"],
        examples={
            'application/json': {
                'summary': 'Example column data request',
                'value': EXAMPLE_REQUEST_PAYLOAD
            }
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Retrieve column data from multiple sites and tables with DateTime filtering.
        
        Processes an array of column requests and returns the actual data values
        for each requested column, filtered by the specified DateTime criteria.
        """
        try:
            logger.info(f"[COLUMN_DATA_CONTROLLER] Received request with {len(request.data) if hasattr(request.data, '__len__') else 'unknown'} column requests")
            
            # Step 1: Validate query parameters (datetime filters)
            query_serializer = DateTimeParameterSerializer(data=request.query_params)
            if not query_serializer.is_valid():
                logger.warning(f"[COLUMN_DATA_CONTROLLER] Invalid query parameters: {query_serializer.errors}")
                return ResponseBuilder.error(
                    message="Invalid query parameters",
                    errors=query_serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            from_date = query_serializer.validated_data.get('from_date')
            to_date = query_serializer.validated_data.get('to_date')
            rack_param = query_serializer.validated_data.get('rack')

            # Parse rack parameter to support multiple racks using shared utility
            rack_list = ParameterParsers.parse_rack_parameter(rack_param)

            logger.info(f"[COLUMN_DATA_CONTROLLER] Filters - DateTime: from={from_date}, to={to_date}, rack_param={rack_param}, rack_list={rack_list}")
            
            # Step 2: Validate request payload (column requests array)
            request_serializer = ColumnDataSourceRequestSerializer(data=request.data)
            if not request_serializer.is_valid():
                logger.warning(f"[COLUMN_DATA_CONTROLLER] Invalid request payload: {request_serializer.errors}")
                return ResponseBuilder.error(
                    message="Invalid request payload",
                    errors=request_serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_requests = request_serializer.validated_data
            logger.info(f"[COLUMN_DATA_CONTROLLER] Validated {len(validated_requests)} column requests")
            
            # Step 3: Convert to ColumnRequest objects
            column_requests = []
            for req_data in validated_requests:
                column_request = ColumnRequest(
                    columnName=req_data['columnName'],
                    columnType=req_data['columnType'], 
                    tableName=req_data['tableName'],
                    siteName=req_data['siteName']
                )
                column_requests.append(column_request)
            
            # Step 4: Process requests using MultiSiteColumnDataService
            logger.info(f"[COLUMN_DATA_CONTROLLER] Processing {len(column_requests)} column requests")
            
            column_responses = self.multi_site_service.get_column_data_sources(
                column_requests=column_requests,
                from_date=from_date,
                to_date=to_date,
                rack_list=rack_list
            )
            
            # Step 5: Convert responses to dictionaries for JSON serialization
            response_data = []
            for response in column_responses:
                if hasattr(response, 'to_dict'):
                    response_data.append(response.to_dict())
                else:
                    # Fallback for dictionary responses
                    response_data.append({
                        'columnName': response.columnName,
                        'columnType': response.columnType,
                        'tableName': response.tableName,
                        'siteName': response.siteName,
                        'dataSource': response.dataSource
                    })
            
            # Step 6: Log processing results
            total_data_points = sum(len(resp.get('dataSource', [])) for resp in response_data)
            logger.info(f"[COLUMN_DATA_CONTROLLER] Successfully processed {len(response_data)} columns with {total_data_points} total data points")
            
            # Step 7: Return successful response
            return ResponseBuilder.success(
                data=response_data,
                message=f"Column data retrieved successfully for {len(response_data)} columns"
            )
            
        except ValueError as ve:
            # Handle validation and parsing errors
            logger.error(f"[COLUMN_DATA_CONTROLLER] Validation error: {str(ve)}")
            return ResponseBuilder.error(
                message=f"Validation error: {str(ve)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"[COLUMN_DATA_CONTROLLER] Unexpected error: {str(e)}", exc_info=True)
            return ResponseBuilder.error(
                message="An unexpected error occurred while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # GET method removed - unnecessary API information endpoint


class ColumnDataSourceCacheController(APIView):
    """
    Cache management endpoint for Column Data Source service.
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multi_site_service = MultiSiteColumnDataService()
    
    @swagger_auto_schema(
        operation_id="clear_column_data_cache",
        operation_summary="Clear cache for Column Data Source service",
        operation_description="Clear cache entries for specific datetime ranges to ensure fresh data retrieval",
        manual_parameters=[
            openapi.Parameter(
                'from_date',
                openapi.IN_QUERY,
                description="Start date for cache clearing",
                type=openapi.TYPE_STRING,
                required=False,
                example="2025-06-01"
            ),
            openapi.Parameter(
                'to_date', 
                openapi.IN_QUERY,
                description="End date for cache clearing",
                type=openapi.TYPE_STRING,
                required=False,
                example="2025-06-05"
            ),
            openapi.Parameter(
                'rack',
                openapi.IN_QUERY,
                description="Rack filter for cache clearing. Supports single rack or comma-separated multiple racks.",
                type=openapi.TYPE_STRING,
                required=False,
                example="rack_02,rack_03,rack_05"
            )
        ],
        responses={
            200: openapi.Response(
                description="Cache cleared successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Cache cleared successfully"),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'cleared_entries': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                                'datetime_range': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'from_date': openapi.Schema(type=openapi.TYPE_STRING),
                                        'to_date': openapi.Schema(type=openapi.TYPE_STRING),
                                        'rack': openapi.Schema(type=openapi.TYPE_STRING)
                                    }
                                )
                            }
                        )
                    }
                )
            )
        },
        tags=["Column Data Cache"]
    )
    def delete(self, request):
        """
        Clear cache entries for Column Data Source service.
        """
        try:
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            rack_param = request.query_params.get('rack')

            # Parse rack parameter to support multiple racks using shared utility
            rack_list = ParameterParsers.parse_rack_parameter(rack_param)

            logger.info(f"[CACHE_CONTROLLER] Clearing cache for datetime range: {from_date} to {to_date}, rack_param: {rack_param}, rack_list: {rack_list}")

            cleared_count = self.multi_site_service.clear_cache_for_datetime_range(
                from_date=from_date,
                to_date=to_date,
                rack_list=rack_list
            )
            
            return ResponseBuilder.success(
                data={
                    'cleared_entries': cleared_count,
                    'datetime_range': {
                        'from_date': from_date,
                        'to_date': to_date,
                        'rack_param': rack_param,
                        'rack_list': rack_list
                    }
                },
                message=f"Cache cleared successfully. {cleared_count} entries removed."
            )
            
        except Exception as e:
            logger.error(f"[CACHE_CONTROLLER] Error clearing cache: {str(e)}", exc_info=True)
            return ResponseBuilder.error(
                message=f"Failed to clear cache: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ColumnDataSourceHealthController(APIView):
    """
    Health check endpoint for Column Data Source service.
    """
    
    @swagger_auto_schema(
        operation_id="column_data_source_health",
        operation_summary="Health check for Column Data Source service",
        operation_description="Check the operational status of the Column Data Source service and its dependencies",
        responses={
            200: openapi.Response(
                description="Service is healthy",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Service is healthy"),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'status': openapi.Schema(type=openapi.TYPE_STRING, example="healthy"),
                                'service': openapi.Schema(type=openapi.TYPE_STRING, example="MultiSiteColumnDataService"),
                                'dependencies': openapi.Schema(type=openapi.TYPE_OBJECT)
                            }
                        )
                    }
                )
            )
        },
        tags=["Column Data"]
    )
    def get(self, request):
        """Check service health and dependencies."""
        try:
            # Test service initialization
            service = MultiSiteColumnDataService()

            # Check dependencies
            dependencies = {
                "blob_storage": "unknown",
                "datetime_processor": "healthy",
                "file_processor": "healthy",
                "spark_processor": "unknown"
            }

            # Test blob storage connection
            try:
                service.blob_client.blob_service_client
                dependencies["blob_storage"] = "healthy"
            except Exception as e:
                dependencies["blob_storage"] = f"error: {str(e)}"
                logger.warning(f"[HEALTH_CHECK] Blob storage issue: {e}")

            # Test Spark processor (with lazy initialization)
            try:
                spark_processor = service.spark_file_processor
                if spark_processor is not None:
                    dependencies["spark_processor"] = "healthy"
                else:
                    dependencies["spark_processor"] = "not_available"
            except Exception as e:
                dependencies["spark_processor"] = f"error: {str(e)}"
                logger.warning(f"[HEALTH_CHECK] Spark processor issue: {e}")

            # Determine overall health status
            overall_status = "healthy"
            if any("error" in dep for dep in dependencies.values()):
                overall_status = "degraded"

            return ResponseBuilder.success(
                data={
                    "status": overall_status,
                    "service": "MultiSiteColumnDataService",
                    "dependencies": dependencies,
                    "timestamp": DateTimeParser.format_datetime_without_timezone(datetime.now())
                },
                message="Service is healthy" if overall_status == "healthy" else "Service is degraded but operational"
            )

        except Exception as e:
            logger.error(f"[HEALTH_CHECK] Service health check failed: {e}")
            return ResponseBuilder.error(
                message=f"Service health check failed: {str(e)}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )