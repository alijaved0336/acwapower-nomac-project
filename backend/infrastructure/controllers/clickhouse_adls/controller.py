"""
ClickHouse ADLS Controllers - API endpoints for querying migrated ADLS data from ClickHouse.
These controllers provide the same interface as analysis APIs but query ClickHouse instead.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService

logger = logging.getLogger(__name__)


class ClickHouseSitesView(APIView):
    """
    API View for listing all migrated sites from ClickHouse.
    Provides same interface as /analysis/sites/ but queries ClickHouse.
    Requires JWT authentication - relies on JWT middleware for authentication.
    """
    permission_classes = [AllowAny]  # Rely on JWT middleware for authentication

    @swagger_auto_schema(
        operation_id="get_clickhouse_sites",
        operation_summary="Get all migrated sites from ClickHouse",
        operation_description="Retrieve all sites that have been migrated to ClickHouse from ADLS.",
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "sites": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                                            "path": openapi.Schema(type=openapi.TYPE_STRING)
                                        }
                                    )
                                ),
                                "method_used": openapi.Schema(type=openapi.TYPE_STRING),
                                "count": openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    }
                )
            ),
            500: openapi.Response("Error")
        },
        tags=["ClickHouse ADLS"]
    )
    def get(self, request):
        """
        GET /clickhouse/sites/
        Returns list of all migrated sites from ClickHouse.
        Filters sites based on authenticated user's role-assigned sites.
        """
        try:
            logger.info("Processing ClickHouse sites request")

            # Extract authenticated user from JWT middleware
            user = getattr(request, "jwt_user", None)
            if not user:
                logger.warning("No jwt_user found in request - authentication required")
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            logger.info(f"User extracted: {user.get('email', 'unknown')}, has role: {bool(user.get('role'))}")

            service = ClickHouseADLSService()
            sites = service.get_sites(user=user)

            response_data = {
                "sites": sites,
                "method_used": "clickhouse_direct",
                "count": len(sites)
            }

            logger.info(f"Successfully retrieved {len(sites)} sites from ClickHouse")

            return ResponseBuilder.success(
                data=response_data,
                message="Sites retrieved successfully from ClickHouse"
            )

        except Exception as e:
            logger.error(f"Error retrieving sites from ClickHouse: {str(e)}")
            return ResponseBuilder.error(
                message=f"Failed to retrieve sites: {str(e)}"
            )


class ClickHouseTablesView(APIView):
    """
    API View for listing tables for a specific site from ClickHouse.
    Provides same interface as /analysis/tables/{site}/ but queries ClickHouse.
    Requires JWT authentication - relies on JWT middleware for authentication.
    """
    permission_classes = [AllowAny]  # Rely on JWT middleware for authentication

    @swagger_auto_schema(
        operation_id="get_clickhouse_tables_for_site",
        operation_summary="Get migrated tables for a site from ClickHouse",
        operation_description="Retrieve all tables for a specific site that have been migrated to ClickHouse.",
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_PATH,
                description="Site identifier",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "siteName": openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            ),
            500: openapi.Response("Error")
        },
        tags=["ClickHouse ADLS"]
    )
    def get(self, request, site_id):
        """
        GET /clickhouse/tables/{site_id}/
        Returns list of all migrated tables for the specified site.
        Validates user has access to the requested site.
        """
        try:
            logger.info(f"Processing ClickHouse tables request for site {site_id}")

            # Extract authenticated user from JWT middleware
            user = getattr(request, "jwt_user", None)
            if not user:
                logger.warning("No jwt_user found in request - authentication required")
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            service = ClickHouseADLSService()
            tables = service.get_tables_for_site(site_id, user=user)

            logger.info(f"Successfully retrieved {len(tables)} tables for site {site_id} from ClickHouse")

            return ResponseBuilder.success(
                data=tables,
                message="Tables retrieved successfully from ClickHouse"
            )

        except Exception as e:
            logger.error(f"Error retrieving tables for site {site_id}: {str(e)}")
            return ResponseBuilder.error(
                message=f"Failed to retrieve tables for site {site_id}: {str(e)}"
            )



class ClickHouseMigrationStatusView(APIView):
    """
    API View for getting migration status and statistics.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_migration_status",
        operation_summary="Get ADLS to ClickHouse migration status",
        operation_description="Retrieve overall migration status and statistics.",
        responses={
            200: openapi.Response("Success"),
            500: openapi.Response("Error")
        },
        tags=["ClickHouse ADLS"]
    )
    def get(self, request):
        """
        GET /clickhouse/migration-status/
        Returns migration status and statistics.
        """
        try:
            logger.info("Processing migration status request")

            service = ClickHouseADLSService()
            status_data = service.get_migration_status()

            logger.info("Successfully retrieved migration status")

            return ResponseBuilder.success(
                data=status_data,
                message="Migration status retrieved successfully"
            )

        except Exception as e:
            logger.error(f"Error retrieving migration status: {str(e)}")
            return ResponseBuilder.error(
                message=f"Failed to retrieve migration status: {str(e)}"
            )


class ClickHouseColumnsView(APIView):
    """
    API View for getting column information for multiple tables.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_columns_for_tables",
        operation_summary="Get column information for multiple tables",
        operation_description="Retrieve column schema information for specified tables with parquet-equivalent types.",
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "siteName": openapi.Schema(type=openapi.TYPE_STRING),
                    "tableName": openapi.Schema(type=openapi.TYPE_STRING)
                },
                required=["siteName", "tableName"]
            )
        ),
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "columnName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "columnType": openapi.Schema(type=openapi.TYPE_STRING),
                                    "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "siteName": openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            ),
            500: openapi.Response("Error")
        },
        tags=["ClickHouse ADLS"]
    )
    def post(self, request):
        """
        POST /clickhouse/columns/
        Returns column information for specified tables.
        """
        try:
            logger.info("Processing columns request for multiple tables")

            tables_list = request.data
            if not isinstance(tables_list, list):
                return ResponseBuilder.error(
                    message="Request body must be an array of table objects"
                )

            service = ClickHouseADLSService()
            columns_data = service.get_columns_for_tables(tables_list)

            logger.info(f"Successfully retrieved columns for {len(tables_list)} tables")

            return ResponseBuilder.success(
                data=columns_data,
                message="Columns retrieved successfully"
            )

        except Exception as e:
            logger.error(f"Error retrieving columns: {str(e)}")
            return ResponseBuilder.error(
                message=f"Failed to retrieve columns: {str(e)}"
            )


class ClickHouseColumnDataSourceView(APIView):
    """
    API View for retrieving actual column data from multiple sites/tables with DateTime filtering.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_column_data_sources",
        operation_summary="Retrieve column data from multiple sites/tables",
        operation_description=(
            "Retrieve actual data values for specified columns across multiple sites and tables with DateTime and generic column filtering.\n\n"
            "**DateTime Filtering Modes:**\n"
            "- Range Filtering: When both from_date and to_date are provided\n"
            "- Exact Match: When only one date parameter is provided\n"
            "- Default Range: When no dates are provided (last 7 days)\n\n"
            "**DateTime Formats Supported:**\n"
            "- Comma-separated: 2025-06-01,10:00:00\n"
            "- Standard: 2025-06-01 10:00:00\n"
            "- Date-only: 2025-06-01\n\n"
            "**Generic Column Filtering (NEW):**\n"
            "- Filter on any column using the 'filters' parameter\n"
            "- Automatic column type detection (numeric, string, etc.)\n"
            "- Support for single values and IN clauses (comma-separated)\n"
            "- Example: ?filters={\"pump_status\": \"active\", \"rack\": \"R001,R002\"}\n"
            "- Backward compatible: 'rack' parameter still supported\n\n"
            "**Performance Characteristics:**\n"
            "- Concurrent processing across multiple sites and tables\n"
            "- Optimized file selection using directory structure\n"
            "- Single I/O operation per table for multiple columns\n"
            "- Memory-efficient streaming for large datasets\n\n"
            "**Request Limits:**\n"
            "- Maximum 100 column requests per call\n"
            "- Maximum 90-day date range for performance\n"
            "- Automatic fallback to existing services on failure"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "columnName": openapi.Schema(type=openapi.TYPE_STRING),
                    "columnType": openapi.Schema(type=openapi.TYPE_STRING),
                    "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                    "siteName": openapi.Schema(type=openapi.TYPE_STRING)
                },
                required=["columnName", "columnType", "tableName", "siteName"]
            ),
            example=[
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
        ),
        manual_parameters=[
            openapi.Parameter(
                "from_date",
                openapi.IN_QUERY,
                description="Start date/time for filtering. Formats: 'YYYY-MM-DD,HH:MM:SS' or 'YYYY-MM-DD'. If only from_date provided, performs exact match.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                example="2025-06-01,10:00:00"
            ),
            openapi.Parameter(
                "to_date",
                openapi.IN_QUERY,
                description="End date/time for filtering. Formats: 'YYYY-MM-DD,HH:MM:SS' or 'YYYY-MM-DD'. If only to_date provided, performs exact match.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                example="2025-06-05,10:00:00"
            ),
            openapi.Parameter(
                "rack",
                openapi.IN_QUERY,
                description="[BACKWARD COMPATIBILITY] Filter records by rack/trailer value. Will filter on 'rack' column if available, otherwise on 'trailer' column if available. For more flexibility, use the 'filters' parameter instead.",
                type=openapi.TYPE_STRING,
                example="R001"
            ),
            openapi.Parameter(
                "filters",
                openapi.IN_QUERY,
                description=(
                    "Generic column filters as JSON object. Allows filtering on any column in the table.\n\n"
                    "**Format**: JSON string with column_name: filter_value pairs\n\n"
                    "**Features**:\n"
                    "- Filter on any column (auto-detects column type)\n"
                    "- Single value: {\"pump_status\": \"active\"} -> pump_status = 'active'\n"
                    "- Multiple values (comma-separated): {\"rack\": \"R001,R002\"} -> rack IN ('R001', 'R002')\n"
                    "- Numeric columns: {\"pressure\": \"150\"} -> pressure = 150\n"
                    "- Multiple filters: {\"pump_status\": \"active\", \"rack\": \"R001,R002\"}\n\n"
                    "**Column Validation**: Invalid columns are logged and skipped (graceful degradation)\n\n"
                    "**Note**: If both 'rack' parameter and filters['rack'] are provided, filters takes precedence"
                ),
                type=openapi.TYPE_STRING,
                example='{"pump_status": "active", "rack": "R001,R002"}'
            )
        ],
        responses={
            200: openapi.Response(
                "Successfully retrieved column data",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "columnName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "columnType": openapi.Schema(type=openapi.TYPE_STRING),
                                    "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "siteName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "dataSource": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_NUMBER),
                                        description="Array of numeric values (floats rounded to 2 decimal places)"
                                    ),
                                    "racks": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING),
                                        description="Array of rack values aligned with dataSource by index. Returns 'NaN' when dataSource value is null or rack value is missing."
                                    )
                                }
                            )
                        )
                    }
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Column data retrieved successfully",
                        "data": [
                            {
                                "columnName": "INL_FL_TO_DMPF_12_MES",
                                "columnType": "double",
                                "tableName": "Jubail_Chemicals_ppm",
                                "siteName": "Jubail-Jazlah",
                                "dataSource": [1.25, 1.87, 2.34, 1.92],
                                "racks": ["Rack_01", "Rack_02", "Rack_01", "Rack_03"]
                            },
                            {
                                "columnName": "INL_FL_TO_DMPF_13_MES",
                                "columnType": "double",
                                "tableName": "Jubail_Chemicals_ppm",
                                "siteName": "Jubail-Jazlah",
                                "dataSource": [2.45, 0.21, 2.78, 3.15],
                                "racks": ["Rack_01", "Rack_02", "Rack_01", "Rack_03"]
                            }
                        ]
                    }
                }
            ),
            400: openapi.Response("Bad Request - Invalid parameters or limits exceeded"),
            500: openapi.Response("Internal Server Error")
        },
        tags=["ClickHouse ADLS"]
    )
    def post(self, request):
        """
        POST /clickhouse/columns/data-source/
        Returns actual data values for specified columns with DateTime filtering and generic filters.
        """
        try:
            logger.info("Processing column data source request for multiple columns")

            # Extract query parameters
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            rack = request.query_params.get('rack')
            filters_param = request.query_params.get('filters')

            # Parse filters parameter (JSON string)
            filters = None
            if filters_param:
                try:
                    import json
                    filters = json.loads(filters_param)
                    if not isinstance(filters, dict):
                        return ResponseBuilder.error(
                            message="Filters parameter must be a JSON object/dictionary"
                        )
                    logger.info(f"Parsed filters: {filters}")
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse filters parameter: {json_err}")
                    return ResponseBuilder.error(
                        message=f"Invalid JSON in filters parameter: {str(json_err)}"
                    )

            # Extract and validate request body
            columns_list = request.data
            if not isinstance(columns_list, list):
                return ResponseBuilder.error(
                    message="Request body must be an array of column objects"
                )

            # Validate request limits
            if len(columns_list) > 100:
                return ResponseBuilder.error(
                    message="Maximum 100 column requests per call allowed"
                )

            if not columns_list:
                return ResponseBuilder.error(
                    message="At least one column must be specified"
                )

            service = ClickHouseADLSService()
            columns_data = service.get_column_data_sources(
                columns_list, from_date, to_date, rack, filters
            )

            logger.info(f"Successfully retrieved data for {len(columns_list)} columns")

            return ResponseBuilder.success(
                data=columns_data,
                message="Column data retrieved successfully"
            )

        except Exception as e:
            logger.error(f"Error retrieving column data: {str(e)}")
            return ResponseBuilder.error(
                message=f"Failed to retrieve column data: {str(e)}"
            )
