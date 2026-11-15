import json
import logging

from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.widgets import WidgetsService


logger = logging.getLogger(__name__)


class WidgetsView(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.service = WidgetsService()

    @swagger_auto_schema(
        operation_id="get_widgets_for_analysis",
        operation_summary="Get all widgets for a specific analysis",
        operation_description="Retrieve all widgets associated with a given analysis ID from Azure Data Lake Storage",
        manual_parameters=[
            openapi.Parameter(
                "analysisID",
                openapi.IN_PATH,
                description="Analysis identifier",
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
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "analysis_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "analysis_name": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "applied_date_filter": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "from_date": openapi.Schema(type=openapi.TYPE_STRING),
                                        "to_date": openapi.Schema(type=openapi.TYPE_STRING),
                                        "rack": openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "asset_type": openapi.Schema(type=openapi.TYPE_STRING),
                                "analysis_type": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "visibility": openapi.Schema(type=openapi.TYPE_STRING),
                                "analysis_created_at": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "analysis_updated_at": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "data": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                            "name": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                            "type": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                            "columns": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        "siteName": openapi.Schema(
                                                            type=openapi.TYPE_STRING
                                                        ),
                                                        "tableName": openapi.Schema(
                                                            type=openapi.TYPE_STRING
                                                        ),
                                                        "columnName": openapi.Schema(
                                                            type=openapi.TYPE_STRING
                                                        ),
                                                    },
                                                ),
                                            ),
                                            "data": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        "name": openapi.Schema(
                                                            type=openapi.TYPE_STRING
                                                        ),
                                                        "data": openapi.Schema(
                                                            type=openapi.TYPE_ARRAY,
                                                            items=openapi.Schema(
                                                                type=openapi.TYPE_NUMBER
                                                            ),
                                                        ),
                                                    },
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    },
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Retrieved 2 widgets for analysis 9cd8dc02-1a19-49ee-92c1-bb1022637845",
                        "data": {
                            "analysis_id": "9cd8dc02-1a19-49ee-92c1-bb1022637845",
                            "analysis_name": "Demo Analysis",
                            "applied_date_filter": {
                                "from_date": "2025-06-01 00:00:00",
                                "to_date": "2025-06-02 23:59:59",
                                "rack": "RACK_01"
                            },
                            "user_id": "aa2d6ecf-85e4-4d91-a310-e58458795cfb",
                            "asset_type": "asasa",
                            "analysis_type": "SWRO Plant",
                            "visibility": "private",
                            "analysis_created_at": "2025-09-03 20:30:30+00:00",
                            "analysis_updated_at": "2025-09-03 20:30:30.511917+00:00",
                            "data": [
                                {
                                    "id": "88a2f610-8b89-4764-a4d3-e6d38f1cc2d1",
                                    "name": "",
                                    "type": "scatter",
                                    "columns": [
                                        {
                                            "siteName": "UAQ",
                                            "tableName": "UAQ_SEC",
                                            "columnName": "DateTime",
                                        }
                                    ],
                                    "data": [{"name": "DateTime", "data": []}],
                                }
                            ],
                        },
                    }
                },
            ),
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, default=False
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                        ),
                    },
                ),
            ),
        },
        tags=["Widgets"],
    )
    def get(self, request, analysisID):
        try:
            # STEP 1: Extract JWT user (REQUIRED for access control)
            authenticated_user_id = None
            authenticated_user_email = None

            if hasattr(request, 'jwt_user') and request.jwt_user:
                authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
                authenticated_user_email = request.jwt_user.get('email')
            elif hasattr(request, 'jwt_payload') and request.jwt_payload:
                authenticated_user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
                authenticated_user_email = request.jwt_payload.get('email')

            if not authenticated_user_id:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=401
                )

            # STEP 2: Call service with authentication context
            response_data = self.service.get_all_widgets_for_analysis(
                analysis_id=analysisID,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email
            )

            # Extract widget count from the data array
            widget_count = len(response_data.get("data", []))

            return ResponseBuilder.success(
                data=response_data,
                message=f"Retrieved {widget_count} widgets for analysis {analysisID}",
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error in GET widgets: {str(e)}")
            return ResponseBuilder.error(message=str(e))

    @swagger_auto_schema(
        operation_id="create_widget",
        operation_summary="Create widget(s) for an analysis",
        operation_description="""Create one or multiple widgets for a specific analysis.
        
        **Single Widget Creation:**
        Send a single widget object to create one widget.
        
        **Bulk Widget Creation:**
        Send an array of widget objects to create multiple widgets.
        
        **Features (Array requests only):**
        - Batch processing with validation
        - Partial success mode (allow_partial=true)
        - Validation-only mode (validate_only=true)
        - Automatic UUID generation for widgets without IDs
        - Duplicate ID detection within batch and database
        - Detailed error reporting with widget indices
        """,
        manual_parameters=[
            openapi.Parameter(
                "analysisID",
                openapi.IN_PATH,
                description="Analysis identifier",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "allow_partial",
                openapi.IN_QUERY,
                description="Allow partial success when some widgets fail validation or creation (Array requests only)",
                type=openapi.TYPE_BOOLEAN,
                default=False,
                required=False,
            ),
            openapi.Parameter(
                "validate_only",
                openapi.IN_QUERY,
                description="Only validate widgets without creating them (Array requests only)",
                type=openapi.TYPE_BOOLEAN,
                default=False,
                required=False,
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Create widget(s) - supports single widgets, array of widgets, or combined analysis+widgets operations",
            oneOf=[
                # Single widget format
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Widget ID (optional, will be auto-generated if not provided)",
                        ),
                        "name": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Widget name (optional, defaults to 'Untitled Widget')",
                        ),
                        "type": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Widget type (e.g., line, bar, pie)",
                            enum=["line", "bar", "pie", "scatter", "area"],
                        ),
                        "columns": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="Column definitions",
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "siteName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "columnName": openapi.Schema(type=openapi.TYPE_STRING),
                                },
                            ),
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="Widget data series",
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "name": openapi.Schema(type=openapi.TYPE_STRING),
                                    "data": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_NUMBER),
                                    ),
                                },
                            ),
                        ),
                        "display_order": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Display order for widget sorting (0-based index). If not provided, will be auto-assigned.",
                            minimum=0,
                        ),
                        "yAxisOptions": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="Y-axis configuration options for chart series",
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "seriesName": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="Name of the series this Y-axis configuration applies to",
                                    ),
                                    "show": openapi.Schema(
                                        type=openapi.TYPE_BOOLEAN,
                                        description="Whether to show this Y-axis",
                                        default=True,
                                    ),
                                    "opposite": openapi.Schema(
                                        type=openapi.TYPE_BOOLEAN,
                                        description="Whether to display this Y-axis on the opposite side",
                                        default=False,
                                    ),
                                    "min": openapi.Schema(
                                        type=openapi.TYPE_NUMBER,
                                        description="Minimum value for this Y-axis",
                                    ),
                                    "max": openapi.Schema(
                                        type=openapi.TYPE_NUMBER,
                                        description="Maximum value for this Y-axis",
                                    ),
                                    "color": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="Color for this Y-axis (hex color code)",
                                        example="#c193c6",
                                    ),
                                },
                                required=["seriesName"],
                            ),
                        ),
                    },
                    required=["type", "columns", "data"],
                ),
            ],
        ),
        examples={
            "Single Widget": {
                "id": "optional-widget-id",
                "name": "Flow Rate Chart",
                "type": "line",
                "columns": [
                    {
                        "siteName": "Site1",
                        "tableName": "Table1",
                        "columnName": "Flow",
                    }
                ],
                "data": [{"name": "Flow Rate", "data": [10, 20, 30]}],
                "display_order": 0,
                "yAxisOptions": [
                    {
                        "seriesName": "Flow Rate",
                        "show": True,
                        "opposite": False,
                        "min": 0,
                        "max": 50,
                        "color": "#3b82f6"
                    }
                ],
            },
            "Array of Widgets": [
                {
                    "name": "Flow Rate Line Chart",
                    "type": "line",
                    "columns": [
                        {
                            "siteName": "Site1",
                            "tableName": "Table1",
                            "columnName": "Flow",
                        }
                    ],
                    "data": [{"name": "Flow Rate", "data": [10, 20, 30]}],
                    "display_order": 0,
                    "yAxisOptions": [
                        {
                            "seriesName": "Flow Rate",
                            "show": True,
                            "opposite": False,
                            "min": 0,
                            "max": 50,
                            "color": "#3b82f6"
                        }
                    ],
                },
                {
                    "name": "Pressure Bar Chart",
                    "type": "bar",
                    "columns": [
                        {
                            "siteName": "Site2",
                            "tableName": "Table2",
                            "columnName": "Pressure",
                        }
                    ],
                    "data": [{"name": "Pressure", "data": [50, 60, 70]}],
                    "display_order": 1,
                    "yAxisOptions": [
                        {
                            "seriesName": "Pressure",
                            "show": True,
                            "opposite": True,
                            "min": 0,
                            "max": 100,
                            "color": "#ef4444"
                        }
                    ],
                },
            ],
            "Combined Analysis + Widgets": {
                "analysis": {
                    "analysis_name": "SWRO Performance Analysis",
                    "user_id": "aa2d6ecf-85e4-4d91-a310-e58458795cfb",
                    "asset_type": "SWRO Plant",
                    "analysis_type": "Performance",
                    "visibility": "private",
                    "applied_date_filter": None,
                },
                "widgets": [
                    {
                        "name": "Flow Rate Trend",
                        "type": "line",
                        "columns": [
                            {
                                "siteName": "UAQ",
                                "tableName": "UAQ_SEC",
                                "columnName": "Flow_Rate",
                            }
                        ],
                        "data": [{"name": "Flow Rate", "data": [45.2, 47.8, 43.1]}],
                        "display_order": 0,
                        "yAxisOptions": [
                            {
                                "seriesName": "Flow Rate",
                                "show": True,
                                "opposite": False,
                                "min": 0,
                                "max": 60,
                                "color": "#3b82f6"
                            }
                        ],
                    },
                    {
                        "name": "Pressure Distribution",
                        "type": "bar",
                        "columns": [
                            {
                                "siteName": "UAQ",
                                "tableName": "UAQ_SEC",
                                "columnName": "Pressure",
                            }
                        ],
                        "data": [{"name": "Pressure", "data": [12.5, 13.2, 11.8]}],
                        "display_order": 1,
                        "yAxisOptions": [
                            {
                                "seriesName": "Pressure",
                                "show": True,
                                "opposite": True,
                                "min": 0,
                                "max": 20,
                                "color": "#ef4444"
                            }
                        ],
                    },
                ],
            },
        },
        responses={
            201: openapi.Response(
                "Created Successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Widget data or bulk operation results",
                        ),
                    },
                ),
                examples={
                    "Single Widget": {
                        "success": True,
                        "message": "Widget created successfully for analysis abc-123",
                        "data": {
                            "id": "ddf70143-af12-46ef-97e4-5d5fa462ff3f",
                            "type": "line",
                            "columns": [
                                {
                                    "siteName": "Site1",
                                    "tableName": "Table1",
                                    "columnName": "Flow",
                                }
                            ],
                            "data": [{"name": "Flow Rate", "data": [10, 20, 30]}],
                        },
                    },
                    "Bulk Widgets": {
                        "success": True,
                        "message": "Successfully created 2 widgets",
                        "data": {
                            "total_widgets": 2,
                            "total_created": 2,
                            "total_failed": 0,
                            "execution_time_seconds": 0.245,
                            "created_widgets": [
                                {"id": "widget1", "type": "line"},
                                {"id": "widget2", "type": "bar"},
                            ],
                            "failed_widgets": [],
                        },
                    },
                },
            ),
            207: openapi.Response(
                "Partial Success (Array requests only)",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, default=True
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "partial_success": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN, default=True
                                ),
                                "total_widgets": openapi.Schema(
                                    type=openapi.TYPE_INTEGER
                                ),
                                "total_created": openapi.Schema(
                                    type=openapi.TYPE_INTEGER
                                ),
                                "total_failed": openapi.Schema(
                                    type=openapi.TYPE_INTEGER
                                ),
                                "execution_time_seconds": openapi.Schema(
                                    type=openapi.TYPE_NUMBER
                                ),
                                "created_widgets": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                ),
                                "failed_widgets": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                ),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, default=False
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
        },
        tags=["Widgets"],
    )
    def post(self, request, analysisID):
        """Create widget(s) for an analysis - handles both single widgets and arrays"""
        try:
            # STEP 1: Extract JWT user (REQUIRED for access control)
            authenticated_user_id = None
            authenticated_user_email = None

            if hasattr(request, 'jwt_user') and request.jwt_user:
                authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
                authenticated_user_email = request.jwt_user.get('email')
            elif hasattr(request, 'jwt_payload') and request.jwt_payload:
                authenticated_user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
                authenticated_user_email = request.jwt_payload.get('email')

            if not authenticated_user_id:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=401
                )

            # Determine if request is single widget or array
            if isinstance(request.data, list):
                # Handle as array of widgets (use bulk logic)
                return self._handle_bulk_create(request, analysisID, authenticated_user_id, authenticated_user_email)
            else:
                # Handle as single widget (existing logic)
                return self._handle_single_create(request.data, analysisID, authenticated_user_id, authenticated_user_email)
        except Exception as e:
            logger.error(f"Error in POST widget: {str(e)}")
            return ResponseBuilder.error(message=str(e))

    def _handle_single_create(self, request_data, analysisID, authenticated_user_id, authenticated_user_email):
        """Handle single widget creation with optional analysis data"""
        try:
            # Check if this is a combined analysis+widget request
            if "analysis" in request_data and "widgets" in request_data:
                # Combined operation: analysis + widgets
                analysis_data = request_data["analysis"]
                widgets_data = request_data["widgets"]

                # Validate analysis data
                is_valid, validation_message = self.service.validate_analysis_data(
                    analysis_data
                )
                if not is_valid:
                    return ResponseBuilder.error(
                        message=f"Analysis validation failed: {validation_message}",
                        status_code=400,
                    )

                # Validate widgets data
                if not isinstance(widgets_data, list):
                    widgets_data = [widgets_data]  # Convert single widget to array

                for i, widget in enumerate(widgets_data):
                    is_valid, validation_message = self.service.validate_widget_data(
                        widget
                    )
                    if not is_valid:
                        return ResponseBuilder.error(
                            message=f"Widget {i} validation failed: {validation_message}",
                            status_code=400,
                        )

                # Call combined service method
                result = self.service.create_analysis_with_widgets(
                    analysis_data=analysis_data,
                    widgets_data=widgets_data,
                    analysis_id=analysisID,
                )

                # Return appropriate response
                if result.get("success"):
                    return ResponseBuilder.created(
                        data=result.get("data"), message=result.get("message")
                    )
                else:
                    status_type = result.get("status_type", "system")
                    status_code = (
                        400
                        if status_type == "validation"
                        else 422 if status_type == "business" else 500
                    )
                    return ResponseBuilder.error(
                        message=result.get("message"),
                        data=result,
                        status_code=status_code,
                    )

            else:
                # Traditional widget-only request
                is_valid, validation_message = self.service.validate_widget_data(
                    request_data
                )
                if not is_valid:
                    return ResponseBuilder.error(
                        message=validation_message, status_code=400
                    )

                created_widget = self.service.create_widget(
                    widget_data=request_data,
                    analysis_id=analysisID,
                    authenticated_user_id=authenticated_user_id,
                    authenticated_user_email=authenticated_user_email
                )

                return ResponseBuilder.created(
                    data=created_widget,
                    message=f"Widget created successfully for analysis {analysisID}",
                )

        except Exception as e:
            logger.error(f"Error in single widget creation: {str(e)}")
            raise

    def _handle_bulk_create(self, request, analysisID, authenticated_user_id, authenticated_user_email):
        """Handle array of widgets creation (bulk logic)"""
        try:
            # Content-Type validation
            content_type = request.content_type
            if content_type and not content_type.startswith("application/json"):
                return ResponseBuilder.error(
                    message="Content-Type must be application/json", status_code=400
                )

            # Extract query parameters
            allow_partial = (
                request.query_params.get("allow_partial", "false").lower() == "true"
            )
            validate_only = (
                request.query_params.get("validate_only", "false").lower() == "true"
            )

            # Check if this is a combined analysis+widget request
            if (
                isinstance(request.data, dict)
                and "analysis" in request.data
                and "widgets" in request.data
            ):
                # Combined operation - redirect to single create with combined data
                return self._handle_single_create(request.data, analysisID, authenticated_user_id, authenticated_user_email)

            # Extract widgets array from request data
            widgets_data = request.data

            # Request size validation at controller level
            max_size = getattr(settings, "WIDGET_BULK_CREATE_MAX_SIZE", 100)

            if len(widgets_data) > max_size:
                logger.warning(
                    f"Request size exceeded: {len(widgets_data)} widgets (max: {max_size})"
                )
                return ResponseBuilder.error(
                    message=f"Request exceeds maximum size of {max_size} widgets",
                    status_code=413,  # Payload Too Large
                )

            # Validate basic input
            if len(widgets_data) == 0:
                return ResponseBuilder.error(
                    message="At least one widget is required", status_code=400
                )

            if not isinstance(widgets_data, list):
                return ResponseBuilder.error(
                    message="Widgets must be an array", status_code=400
                )

            logger.info(
                f"Processing bulk create request: {len(widgets_data)} widgets for analysis {analysisID}"
            )

            # Call service layer for bulk creation
            logger.info(
                f"Calling service layer for bulk creation: analysis={analysisID}, allow_partial={allow_partial}, validate_only={validate_only}"
            )

            result = self.service.bulk_create_widgets(
                widgets_data=widgets_data,
                analysis_id=analysisID,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                allow_partial=allow_partial,
                validate_only=validate_only,
                stop_on_first_error=False,  # Default for bulk requests
            )

            logger.info(
                f"Service layer response: success={result.get('success')}, created={result.get('total_created', 0)}, failed={result.get('total_failed', 0)}"
            )

            # Determine response status code based on error type
            if not result.get("success"):
                status_type = result.get("status_type", "system")

                if status_type == "validation":
                    return ResponseBuilder.error(
                        message=result.get("message", "Validation failed"),
                        data=result,
                        status_code=400,  # Bad Request for validation errors
                    )
                elif status_type == "business":
                    return ResponseBuilder.error(
                        message=result.get("message", "Business logic violation"),
                        data=result,
                        status_code=422,  # Unprocessable Entity for business logic errors
                    )
                else:  # system errors
                    return ResponseBuilder.error(
                        message=result.get("message", "Internal server error"),
                        data=result,
                        status_code=500,  # Internal Server Error for system errors
                    )

            # Handle partial success
            if result.get("partial_success"):
                logger.info(
                    f"Returning partial success response for analysis {analysisID}"
                )
                return Response(
                    {"success": True, "message": result.get("message"), "data": result},
                    status=status.HTTP_207_MULTI_STATUS,
                )

            # Handle validation-only mode
            if validate_only:
                logger.info(
                    f"Returning validation-only response for analysis {analysisID}: {result.get('valid_widgets', 0)} valid widgets"
                )
                return ResponseBuilder.success(
                    data=result, message="Validation completed successfully"
                )

            # Full success
            logger.info(
                f"Returning full success response for analysis {analysisID}: {result.get('total_created', 0)} widgets created"
            )
            return ResponseBuilder.created(
                data=result,
                message=result.get(
                    "message", f"Successfully created widgets for analysis {analysisID}"
                ),
            )

        except ValueError as e:
            logger.error(f"Validation error in bulk create widgets: {str(e)}")
            return ResponseBuilder.error(
                message=f"Validation error: {str(e)}", status_code=400
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in bulk create widgets: {str(e)}")
            return ResponseBuilder.error(
                message="Invalid JSON format in request body", status_code=400
            )
        except Exception as e:
            logger.error(f"Unexpected error in bulk create widgets: {str(e)}")
            return ResponseBuilder.error(
                message="Internal server error occurred during bulk widget creation",
                status_code=500,
            )

    @swagger_auto_schema(
        operation_id="update_analysis_with_widgets",
        operation_summary="Complete replacement of analysis and widgets",
        operation_description="""Complete replacement of analysis metadata and widgets in a single operation.
        
        **Features:**
        - Update existing analysis or create new if doesn't exist
        - **COMPLETE WIDGET REPLACEMENT**: Payload defines the exact set of widgets for the analysis
        - Delete existing widgets that are NOT included in the payload
        - Update widgets in payload that have IDs and exist in database
        - Create new widgets for payload items without IDs or with non-existent IDs
        - Support zero widgets (deletes all existing widgets, updates analysis only)
        - Auto-generate UUIDs for new widgets
        - Bulk operations for optimal performance
        
        **Widget Processing Logic (Complete Replacement):**
        1. **Delete Phase**: Remove existing widgets not present in payload
        2. **Update Phase**: Update widgets with IDs that exist in payload and database  
        3. **Create Phase**: Create widgets without IDs or with IDs not found in database
        4. **Result**: Payload becomes the authoritative set of widgets for the analysis
        
        **Examples:**
        - Existing widgets: [A, B, C] + Payload: [B_updated, D] → Result: [B_updated, D] (A, C deleted)
        - Existing widgets: [A, B] + Payload: [] → Result: [] (all widgets deleted)
        - Existing widgets: [] + Payload: [X, Y] → Result: [X, Y] (new widgets created)
        
        **HTTP Status Codes:**
        - 200: Analysis and/or widgets replaced successfully
        - 201: New analysis created with widgets
        - 400: Validation errors in request data
        - 404: Analysis or widget not found (for updates)
        - 500: Internal server error
        """,
        manual_parameters=[
            openapi.Parameter(
                "analysisID",
                openapi.IN_PATH,
                description="Analysis identifier",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Analysis metadata and widgets for upsert operations",
            properties={
                "analysis_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Analysis name",
                ),
                "analysis_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Type of analysis (e.g., 'SWRO Plant')",
                ),
                "asset_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Asset type",
                ),
                "visibility": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["private", "public"],
                    description="Analysis visibility",
                ),
                "applied_date_filter": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Date filter configuration",
                    properties={
                        "from_date": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Start date (ISO format: YYYY-MM-DD HH:MM:SS)",
                        ),
                        "to_date": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="End date (ISO format: YYYY-MM-DD HH:MM:SS)",
                        ),
                        "rack": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Rack filter value",
                        ),
                    },
                ),
                "user_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User identifier",
                ),
                "widgets": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="Array of widgets for upsert operations",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Widget ID (optional - if provided, widget will be updated; if omitted, new widget will be created)",
                            ),
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Widget type",
                                enum=["line", "bar", "pie", "scatter", "area"],
                            ),
                            "columns": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description="Widget columns with metadata and data",
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "columnType": openapi.Schema(type=openapi.TYPE_STRING),
                                        "siteName": openapi.Schema(type=openapi.TYPE_STRING),
                                        "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                                        "columnName": openapi.Schema(type=openapi.TYPE_STRING),
                                        "dataSource": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(type=openapi.TYPE_NUMBER),
                                        ),
                                    },
                                ),
                            ),
                        },
                        required=["type", "columns"],
                    ),
                ),
            },
            required=["analysis_name", "analysis_type", "asset_type", "visibility", "user_id", "widgets"],
            example={
                "analysis_name": "New Test Analysis 100",
                "analysis_type": "SWRO Plant",
                "asset_type": "asasa",
                "visibility": "public",
                "applied_date_filter": {
                    "from_date": "2025-06-01 00:00:00",
                    "to_date": "2025-06-02 23:59:59",
                    "rack": "RACK_01"
                },
                "user_id": "aa2d6ecf-85e4-4d91-a310-e58458795cfb",
                "widgets": [
                    {
                        "type": "scatter",
                        "columns": [
                            {
                                "columnType": "timestamp[ns]",
                                "siteName": "Jubail-Jazlah",
                                "tableName": "Jubail-Jazlah_Normalization_pass_1",
                                "columnName": "DateTime",
                                "dataSource": []
                            }
                        ]
                    }
                ]
            },
        ),
        responses={
            200: openapi.Response(
                "Analysis and widgets updated successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "analysis_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "analysis_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "analysis_type": openapi.Schema(type=openapi.TYPE_STRING),
                                "asset_type": openapi.Schema(type=openapi.TYPE_STRING),
                                "visibility": openapi.Schema(type=openapi.TYPE_STRING),
                                "applied_date_filter": openapi.Schema(type=openapi.TYPE_OBJECT),
                                "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "operation_summary": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "analysis_operation": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            enum=["created", "updated"],
                                        ),
                                        "widgets_created": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "widgets_updated": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "widgets_deleted": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "total_widgets": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "execution_time_seconds": openapi.Schema(type=openapi.TYPE_NUMBER),
                                    },
                                ),
                                "widgets": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_STRING),
                                            "type": openapi.Schema(type=openapi.TYPE_STRING),
                                            "columns": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                            ),
                                            "data": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                            ),
                                            "operation": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                enum=["created", "updated"],
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    },
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Retrieved 2 widgets for analysis 9cd8dc02-1a19-49ee-92c1-bb1022637845",
                        "data": {
                            "analysis_id": "9cd8dc02-1a19-49ee-92c1-bb1022637845",
                            "analysis_name": "Demo Analysis",
                            "applied_date_filter": {
                                "from_date": "2025-06-01 00:00:00",
                                "to_date": "2025-06-02 23:59:59",
                                "rack": "RACK_01"
                            },
                            "user_id": "aa2d6ecf-85e4-4d91-a310-e58458795cfb",
                            "asset_type": "asasa",
                            "analysis_type": "SWRO Plant",
                            "visibility": "private",
                            "analysis_created_at": "2025-09-03 20:30:30+00:00",
                            "analysis_updated_at": "2025-09-03 20:30:30.511917+00:00",
                            "data": [
                                {
                                    "id": "88a2f610-8b89-4764-a4d3-e6d38f1cc2d1",
                                    "name": "Salt Passage Chart",
                                    "type": "scatter",
                                    "columns": [
                                        {
                                            "siteName": "UAQ",
                                            "tableName": "UAQ_SEC",
                                            "columnName": "DateTime",
                                        }
                                    ],
                                    "data": [{"name": "DateTime", "data": []}],
                                    "yAxisOptions": [
                                        {
                                            "seriesName": "Actual_Salt_Passage",
                                            "show": True,
                                            "opposite": False,
                                            "min": 0,
                                            "max": 0.07,
                                            "color": "#c193c6"
                                        }
                                    ],
                                }
                            ],
                        },
                    },
                },
            ),
            201: openapi.Response(
                "New analysis created with widgets",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request - Validation errors",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            404: openapi.Response(
                "Analysis or widget not found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
        },
        tags=["Widgets"],
    )
    def put(self, request, analysisID):
        """Update analysis and manage widgets (create/update) in a single operation"""
        try:
            # STEP 1: Extract JWT user (REQUIRED for access control)
            authenticated_user_id = None
            authenticated_user_email = None

            if hasattr(request, 'jwt_user') and request.jwt_user:
                authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
                authenticated_user_email = request.jwt_user.get('email')
            elif hasattr(request, 'jwt_payload') and request.jwt_payload:
                authenticated_user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
                authenticated_user_email = request.jwt_payload.get('email')

            if not authenticated_user_id:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=401
                )

            # Validate request data structure
            if not isinstance(request.data, dict):
                return ResponseBuilder.error(
                    message="Request body must be a JSON object", status_code=400
                )

            # Extract and validate required fields
            required_fields = [
                "analysis_name", "analysis_type", "asset_type",
                "visibility", "user_id", "widgets"
            ]
            missing_fields = [field for field in required_fields if field not in request.data]

            if missing_fields:
                return ResponseBuilder.error(
                    message=f"Missing required fields: {', '.join(missing_fields)}",
                    status_code=400
                )

            # Validate widgets is an array
            if not isinstance(request.data.get("widgets"), list):
                return ResponseBuilder.error(
                    message="'widgets' field must be an array", status_code=400
                )

            # Call service layer for PUT operation
            result = self.service.put_update_analysis_with_widgets(
                analysis_id=analysisID,
                analysis_data={
                    "analysis_name": request.data.get("analysis_name"),
                    "analysis_type": request.data.get("analysis_type"),
                    "asset_type": request.data.get("asset_type"),
                    "visibility": request.data.get("visibility"),
                    "user_id": request.data.get("user_id"),
                    "applied_date_filter": request.data.get("applied_date_filter"),
                },
                widgets_data=request.data.get("widgets", []),
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email
            )

            # Handle service response
            if result.get("success"):
                status_code = 201 if result.get("analysis_operation") == "created" else 200
                return Response(
                    {
                        "success": True, 
                        "message": result.get("message"),
                        "data": result.get("data")
                    },
                    status=status_code
                )
            else:
                # Handle different error types
                status_type = result.get("status_type", "system")
                if status_type == "validation":
                    status_code = 400
                elif status_type == "not_found":
                    status_code = 404
                else:
                    status_code = 500

                return ResponseBuilder.error(
                    message=result.get("message"),
                    data=result.get("data"),
                    status_code=status_code,
                )

        except json.JSONDecodeError:
            return ResponseBuilder.error(
                message="Invalid JSON format in request body", status_code=400
            )
        except Exception as e:
            logger.error(f"Unexpected error in PUT analysis with widgets: {str(e)}")
            return ResponseBuilder.error(
                message="Internal server error occurred during analysis and widget update",
                status_code=500,
            )

    @swagger_auto_schema(
        operation_id="reorder_widgets",
        operation_summary="Bulk reorder widgets within an analysis",
        operation_description="""Reorder multiple widgets within an analysis using drag-and-drop semantics.

        **Features:**
        - Bulk reordering with single API call for optimal performance
        - Conflict resolution: automatically handles duplicate display orders
        - Validation: ensures all widgets exist in the specified analysis
        - Cache invalidation: clears analysis cache after reordering
        - Real-time ordering: changes take effect immediately

        **Frontend Integration:**
        This endpoint is designed for drag-and-drop frontend implementations:
        1. User drags widget to new position
        2. Frontend calculates new display_order values
        3. Single API call reorders all affected widgets
        4. Immediate feedback with operation results

        **Conflict Resolution:**
        - Automatic gap handling: missing orders don't affect operation
        - Duplicate resolution: widgets with same order are auto-sequenced
        - Error recovery: partial failures are reported with specific widget details

        **Performance:**
        - Uses SQL CASE statement for bulk updates
        - Single database transaction for consistency
        - Optimized for large widget sets (100+ widgets per analysis)
        """,
        manual_parameters=[
            openapi.Parameter(
                "analysisID",
                openapi.IN_PATH,
                description="Analysis identifier containing the widgets to reorder",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "reorder_operations": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="List of reorder operations to apply",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "widget_id": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="ID of the widget to reorder",
                            ),
                            "new_display_order": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="New display order position (0-based index)",
                                minimum=0,
                            ),
                        },
                        required=["widget_id", "new_display_order"],
                    ),
                    minItems=1,
                ),
            },
            required=["reorder_operations"],
            example={
                "reorder_operations": [
                    {"widget_id": "widget-123", "new_display_order": 0},
                    {"widget_id": "widget-456", "new_display_order": 1},
                    {"widget_id": "widget-789", "new_display_order": 2},
                ]
            },
        ),
        responses={
            200: openapi.Response(
                "Widgets reordered successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Successfully reordered 3 widgets",
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "total_operations": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="Number of reorder operations requested",
                                ),
                                "reordered_widgets": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    description="List of widget IDs that were successfully reordered",
                                ),
                                "execution_time_seconds": openapi.Schema(
                                    type=openapi.TYPE_NUMBER,
                                    description="Time taken to complete the reordering operation",
                                ),
                            },
                        ),
                    },
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Successfully reordered 3 widgets",
                        "data": {
                            "total_operations": 3,
                            "reordered_widgets": ["widget-123", "widget-456", "widget-789"],
                            "execution_time_seconds": 0.156,
                        },
                    }
                },
            ),
            400: openapi.Response(
                "Bad Request - Invalid reorder operations",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Operation 1 new_display_order must be non-negative",
                        "data": None,
                    }
                },
            ),
            404: openapi.Response(
                "Analysis or widgets not found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Widgets not found in analysis abc-123: ['invalid-widget-id']",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
        },
        tags=["Widgets"],
    )
    def patch(self, request, analysisID):
        """Bulk reorder widgets within an analysis (drag-and-drop support)"""
        try:
            # STEP 1: Extract JWT user (REQUIRED for access control)
            authenticated_user_id = None
            authenticated_user_email = None

            if hasattr(request, 'jwt_user') and request.jwt_user:
                authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
                authenticated_user_email = request.jwt_user.get('email')
            elif hasattr(request, 'jwt_payload') and request.jwt_payload:
                authenticated_user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
                authenticated_user_email = request.jwt_payload.get('email')

            if not authenticated_user_id:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=401
                )

            # Validate request data structure
            if not isinstance(request.data, dict):
                return ResponseBuilder.error(
                    message="Request body must be a JSON object", status_code=400
                )

            reorder_operations = request.data.get("reorder_operations")
            if not reorder_operations:
                return ResponseBuilder.error(
                    message="reorder_operations is required", status_code=400
                )

            if not isinstance(reorder_operations, list):
                return ResponseBuilder.error(
                    message="reorder_operations must be an array", status_code=400
                )

            if len(reorder_operations) == 0:
                return ResponseBuilder.error(
                    message="At least one reorder operation is required", status_code=400
                )

            # Validate each operation
            for i, operation in enumerate(reorder_operations):
                if not isinstance(operation, dict):
                    return ResponseBuilder.error(
                        message=f"Operation {i} must be an object", status_code=400
                    )

                if "widget_id" not in operation:
                    return ResponseBuilder.error(
                        message=f"Operation {i} must include widget_id", status_code=400
                    )

                if "new_display_order" not in operation:
                    return ResponseBuilder.error(
                        message=f"Operation {i} must include new_display_order",
                        status_code=400,
                    )

                if not isinstance(operation["new_display_order"], int):
                    return ResponseBuilder.error(
                        message=f"Operation {i} new_display_order must be an integer",
                        status_code=400,
                    )

                if operation["new_display_order"] < 0:
                    return ResponseBuilder.error(
                        message=f"Operation {i} new_display_order must be non-negative",
                        status_code=400,
                    )

            logger.info(f"Processing reorder request for {len(reorder_operations)} widgets in analysis {analysisID}")

            # Call service layer
            result = self.service.reorder_widgets(
                analysis_id=analysisID,
                reorder_operations=reorder_operations,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email
            )

            return ResponseBuilder.success(
                data=result,
                message=f"Successfully reordered {result.get('total_operations', 0)} widgets"
            )

        except ValueError as e:
            logger.error(f"Validation error in reorder widgets: {str(e)}")
            return ResponseBuilder.error(message=str(e), status_code=400)

        except Exception as e:
            logger.error(f"Error in reorder widgets: {str(e)}")
            if "not found" in str(e).lower():
                return ResponseBuilder.error(message=str(e), status_code=404)
            return ResponseBuilder.error(
                message="Internal server error occurred during widget reordering",
                status_code=500,
            )


class WidgetDetailView(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.service = WidgetsService()

    @swagger_auto_schema(
        operation_id="get_widget_by_id",
        operation_summary="Get a specific widget by ID",
        operation_description="Retrieve a specific widget by its ID for a given analysis",
        manual_parameters=[
            openapi.Parameter(
                "analysisID",
                openapi.IN_PATH,
                description="Analysis identifier",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "widgetID",
                openapi.IN_PATH,
                description="Widget identifier",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response("Success"),
            404: openapi.Response("Widget not found"),
        },
        tags=["Widgets"],
    )
    def get(self, request, analysisID, widgetID):
        try:
            # STEP 1: Extract JWT user (REQUIRED for access control)
            authenticated_user_id = None
            authenticated_user_email = None

            if hasattr(request, 'jwt_user') and request.jwt_user:
                authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
                authenticated_user_email = request.jwt_user.get('email')
            elif hasattr(request, 'jwt_payload') and request.jwt_payload:
                authenticated_user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
                authenticated_user_email = request.jwt_payload.get('email')

            if not authenticated_user_id:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=401
                )

            # STEP 2: Call service with authentication context
            widget_data = self.service.get_widget(
                widget_id=widgetID,
                analysis_id=analysisID,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email
            )

            return ResponseBuilder.success(
                data=widget_data, message="Widget retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error in GET widget by ID: {str(e)}")
            if "not found" in str(e).lower() or "access denied" in str(e).lower():
                return ResponseBuilder.not_found(message=str(e))
            return ResponseBuilder.error(message=str(e))



class WidgetCopyView(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.service = WidgetsService()

    @swagger_auto_schema(
        operation_id="copy_widget",
        operation_summary="Copy a widget to another analysis",
        operation_description="Copy a widget from its current analysis to a target analysis without affecting the original widget",
        manual_parameters=[
            openapi.Parameter(
                "widgetID",
                openapi.IN_PATH,
                description="Widget identifier to copy",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "target_analysis_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Target analysis ID where widget will be copied",
                ),
                "new_widget_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Optional new name for the copied widget. If not provided, original name is used.",
                ),
            },
            required=["target_analysis_id"],
            example={
                "target_analysis_id": "9cd8dc02-1a19-49ee-92c1-bb1022637845",
                "new_widget_name": "Copied Flow Rate Chart",
            },
        ),
        responses={
            201: openapi.Response(
                "Widget copied successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_STRING),
                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                "type": openapi.Schema(type=openapi.TYPE_STRING),
                                "columns": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "siteName": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                            "tableName": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                            "columnName": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                        },
                                    ),
                                ),
                                "data": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "name": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                            "data": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_NUMBER
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    },
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Widget copied successfully to analysis 9cd8dc02-1a19-49ee-92c1-bb1022637845",
                        "data": {
                            "id": "new-uuid-here",
                            "name": "Copied Flow Rate Chart",
                            "type": "line",
                            "columns": [
                                {
                                    "siteName": "Site1",
                                    "tableName": "Table1",
                                    "columnName": "Flow",
                                }
                            ],
                            "data": [{"name": "Flow Rate", "data": [10, 20, 30]}],
                        },
                    }
                },
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, default=False
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
            404: openapi.Response(
                "Widget or target analysis not found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, default=False
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, default=False
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
        },
        tags=["Widgets"],
    )
    def post(self, request, widgetID):
        try:
            # STEP 1: Extract JWT user (REQUIRED for access control)
            authenticated_user_id = None
            authenticated_user_email = None

            if hasattr(request, 'jwt_user') and request.jwt_user:
                authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
                authenticated_user_email = request.jwt_user.get('email')
            elif hasattr(request, 'jwt_payload') and request.jwt_payload:
                authenticated_user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
                authenticated_user_email = request.jwt_payload.get('email')

            if not authenticated_user_id:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=401
                )

            # Validate request data
            target_analysis_id = request.data.get("target_analysis_id")
            if not target_analysis_id:
                return ResponseBuilder.error(
                    message="target_analysis_id is required", status_code=400
                )

            new_name = request.data.get("new_widget_name")

            # Copy widget
            copied_widget = self.service.copy_widget(
                widget_id=widgetID,
                target_analysis_id=target_analysis_id,
                new_name=new_name,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email
            )

            return ResponseBuilder.created(
                data=copied_widget,
                message=f"Widget copied successfully to analysis {target_analysis_id}",
            )

        except Exception as e:
            logger.error(f"Error copying widget {widgetID}: {str(e)}")
            if "not found" in str(e).lower() or "access denied" in str(e).lower():
                return ResponseBuilder.not_found(message=str(e))
            return ResponseBuilder.error(message=str(e))


class WidgetBulkDeleteView(APIView):
    """Controller for bulk widget deletion (without analysisID dependency)"""

    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.service = WidgetsService()

    @swagger_auto_schema(
        operation_id="bulk_delete_widgets",
        operation_summary="Delete multiple widgets",
        operation_description="""Delete multiple widgets by providing an array of widget IDs.
        
        This endpoint removes the dependency on analysisID and allows deletion of widgets
        across different analyses in a single request.
        
        **Features:**
        - Accepts array of widget IDs in request body
        - Returns detailed count of successful and failed deletions
        - Provides specific error information for failed deletions
        - No analysisID parameter required
        
        **Response Format:**
        - total_requested: Total number of widget IDs provided
        - successfully_deleted: Number of widgets successfully deleted
        - failed_deletions: Number of widgets that failed to delete
        - deleted_widget_ids: Array of successfully deleted widget IDs
        - failed_widget_ids: Array of objects with widget_id and error details
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "widget_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Array of widget IDs to delete",
                    example=["widget-id-1", "widget-id-2", "widget-id-3"],
                )
            },
            required=["widget_ids"],
            example={
                "widget_ids": [
                    "88a2f610-8b89-4764-a4d3-e6d38f1cc2d1",
                    "bef80254-bg23-57fg-98f5-6e6gb573gg4g",
                    "invalid-widget-id",
                ]
            },
        ),
        responses={
            200: openapi.Response(
                "Bulk deletion completed",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "total_requested": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="Total number of widget IDs provided",
                                ),
                                "successfully_deleted": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="Number of widgets successfully deleted",
                                ),
                                "failed_deletions": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    description="Number of widgets that failed to delete",
                                ),
                                "deleted_widget_ids": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    description="Array of successfully deleted widget IDs",
                                ),
                                "failed_widget_ids": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "widget_id": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                            "error": openapi.Schema(
                                                type=openapi.TYPE_STRING
                                            ),
                                        },
                                    ),
                                    description="Array of widgets that failed to delete with error details",
                                ),
                                "execution_time_seconds": openapi.Schema(
                                    type=openapi.TYPE_NUMBER,
                                    description="Time taken for the operation",
                                ),
                            },
                        ),
                    },
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Partially successful: 2 deleted, 1 failed out of 3 requested",
                        "data": {
                            "total_requested": 3,
                            "successfully_deleted": 2,
                            "failed_deletions": 1,
                            "deleted_widget_ids": [
                                "88a2f610-8b89-4764-a4d3-e6d38f1cc2d1",
                                "bef80254-bg23-57fg-98f5-6e6gb573gg4g",
                            ],
                            "failed_widget_ids": [
                                {
                                    "widget_id": "invalid-widget-id",
                                    "error": "Widget not found",
                                }
                            ],
                            "execution_time_seconds": 0.125,
                        },
                    }
                },
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, default=False
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
                examples={
                    "application/json": {
                        "success": False,
                        "message": "widget_ids is required and must be a non-empty array",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, default=False
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
        },
        tags=["Widgets"],
    )
    def delete(self, request):
        """Delete multiple widgets by their IDs"""
        try:
            # STEP 1: Extract JWT user (REQUIRED for access control)
            authenticated_user_id = None
            authenticated_user_email = None

            if hasattr(request, 'jwt_user') and request.jwt_user:
                authenticated_user_id = request.jwt_user.get('id') or request.jwt_user.get('email')
                authenticated_user_email = request.jwt_user.get('email')
            elif hasattr(request, 'jwt_payload') and request.jwt_payload:
                authenticated_user_id = request.jwt_payload.get('email') or request.jwt_payload.get('user_id')
                authenticated_user_email = request.jwt_payload.get('email')

            if not authenticated_user_id:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=401
                )

            # Validate request data
            widget_ids = request.data.get("widget_ids")

            if not widget_ids:
                return ResponseBuilder.error(
                    message="widget_ids is required and must be provided",
                    status_code=400,
                )

            if not isinstance(widget_ids, list):
                return ResponseBuilder.error(
                    message="widget_ids must be an array", status_code=400
                )

            if len(widget_ids) == 0:
                return ResponseBuilder.error(
                    message="widget_ids array cannot be empty", status_code=400
                )

            # Validate that all items are strings
            invalid_ids = [
                wid for wid in widget_ids if not isinstance(wid, str) or not wid.strip()
            ]
            if invalid_ids:
                return ResponseBuilder.error(
                    message=f"All widget IDs must be non-empty strings. Invalid items found: {invalid_ids}",
                    status_code=400,
                )

            logger.info(f"Processing bulk delete request for {len(widget_ids)} widgets")

            # Call service layer
            result = self.service.bulk_delete_widgets(
                widget_ids=widget_ids,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email
            )

            if result.get("success"):
                return ResponseBuilder.success(
                    data=result.get("data"), message=result.get("message")
                )
            else:
                return ResponseBuilder.error(
                    message=result.get("message"),
                    data=result.get("data"),
                    status_code=500,
                )

        except json.JSONDecodeError:
            return ResponseBuilder.error(
                message="Invalid JSON format in request body", status_code=400
            )
        except Exception as e:
            logger.error(f"Unexpected error in bulk delete widgets: {str(e)}")
            return ResponseBuilder.error(
                message="Internal server error occurred during bulk widget deletion",
                status_code=500,
            )
