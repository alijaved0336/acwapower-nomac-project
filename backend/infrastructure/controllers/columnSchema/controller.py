"""
Column Schema Controller
Handles POST requests for retrieving column schema metadata from multiple sites/tables.
Fast endpoint that only returns column names and types without downloading data.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from typing import List

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.columnSchemaService import (
    ColumnSchemaService, TableRequest, ColumnMetadata
)
from interface.serializers.columnSchemaSerializers import (
    ColumnSchemaRequestSerializer,
    ColumnSchemaResponseListSerializer,
    TableRequestSerializer,
    EXAMPLE_REQUEST_PAYLOAD,
    EXAMPLE_RESPONSE_PAYLOAD
)

logger = logging.getLogger(__name__)


class ColumnSchemaController(APIView):
    """
    Column Schema API Controller
    
    Provides fast column schema retrieval across multiple sites and tables
    without downloading actual data - only schema metadata.
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.column_schema_service = ColumnSchemaService()
    
    @swagger_auto_schema(
        operation_id="get_column_schemas",
        operation_summary="Retrieve column schema metadata from multiple sites/tables",
        operation_description="""
        Retrieve column names and types for specified tables across multiple sites.
        
        **Performance Characteristics:**
        - Schema-only reading (no data download)
        - Concurrent processing across multiple sites and tables
        - Uses only first parquet file per table for schema consistency
        - Optimized for maximum speed with PyArrow direct schema access
        
        **Request Limits:**
        - Maximum 50 table requests per call
        - Each table request specifies siteName and tableName
        - Returns all columns found in each table
        
        **Use Cases:**
        - Frontend dropdown population
        - Dynamic form generation
        - Table structure discovery
        - Column availability checking
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'siteName': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Name of the site containing the table",
                        example="Jubail-Jazlah"
                    ),
                    'tableName': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Name of the table to get columns for",
                        example="Jubail_Chemicals_ppm"
                    )
                },
                required=['siteName', 'tableName']
            ),
            description="Array of site/table combinations to get column schemas for",
            example=EXAMPLE_REQUEST_PAYLOAD
        ),
        responses={
            200: openapi.Response(
                description="Successfully retrieved column schemas",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Column schemas retrieved successfully"),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'columnName': openapi.Schema(type=openapi.TYPE_STRING),
                                    'columnType': openapi.Schema(type=openapi.TYPE_STRING),
                                    'tableName': openapi.Schema(type=openapi.TYPE_STRING),
                                    'siteName': openapi.Schema(type=openapi.TYPE_STRING)
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
                'summary': 'Example table requests',
                'value': EXAMPLE_REQUEST_PAYLOAD
            }
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Retrieve column schema metadata from multiple sites and tables.
        
        Processes an array of site/table requests and returns column names and types
        for each requested table without downloading actual data.
        """
        try:
            logger.info(f"[COLUMN_SCHEMA_CONTROLLER] Received request with {len(request.data) if hasattr(request.data, '__len__') else 'unknown'} table requests")
            
            # Step 1: Validate request payload (table requests array)
            request_serializer = ColumnSchemaRequestSerializer(data=request.data)
            if not request_serializer.is_valid():
                logger.warning(f"[COLUMN_SCHEMA_CONTROLLER] Invalid request payload: {request_serializer.errors}")
                return ResponseBuilder.error(
                    message="Invalid request payload",
                    errors=request_serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_requests = request_serializer.validated_data
            logger.info(f"[COLUMN_SCHEMA_CONTROLLER] Validated {len(validated_requests)} table requests")
            
            # Step 2: Convert to TableRequest objects
            table_requests = []
            for req_data in validated_requests:
                table_request = TableRequest(
                    siteName=req_data['siteName'],
                    tableName=req_data['tableName']
                )
                table_requests.append(table_request)
            
            # Step 3: Process requests using ColumnSchemaService
            logger.info(f"[COLUMN_SCHEMA_CONTROLLER] Processing {len(table_requests)} table requests for schema")
            
            column_schemas = self.column_schema_service.get_columns_metadata(
                table_requests=table_requests
            )
            
            # Step 4: Convert responses to dictionaries for JSON serialization
            response_data = []
            for column_schema in column_schemas:
                if hasattr(column_schema, 'to_dict'):
                    response_data.append(column_schema.to_dict())
                else:
                    # Fallback for dictionary responses
                    response_data.append({
                        'columnName': column_schema.columnName,
                        'columnType': column_schema.columnType,
                        'tableName': column_schema.tableName,
                        'siteName': column_schema.siteName
                    })
            
            # Step 5: Log processing results
            unique_tables = set(f"{col['siteName']}/{col['tableName']}" for col in response_data)
            logger.info(f"[COLUMN_SCHEMA_CONTROLLER] Successfully processed {len(unique_tables)} tables with {len(response_data)} total columns")
            
            # Step 6: Return successful response
            return ResponseBuilder.success(
                data=response_data,
                message=f"Column schemas retrieved successfully for {len(response_data)} columns from {len(unique_tables)} tables"
            )
            
        except ValueError as ve:
            # Handle validation and parsing errors
            logger.error(f"[COLUMN_SCHEMA_CONTROLLER] Validation error: {str(ve)}")
            return ResponseBuilder.error(
                message=f"Validation error: {str(ve)}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"[COLUMN_SCHEMA_CONTROLLER] Unexpected error: {str(e)}", exc_info=True)
            return ResponseBuilder.error(
                message="An unexpected error occurred while processing your request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # GET method removed - unnecessary API information endpoint