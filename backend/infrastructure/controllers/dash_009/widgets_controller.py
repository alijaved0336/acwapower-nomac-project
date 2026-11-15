from datetime import datetime, timedelta

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.dash_009_widget import Dash009WidgetsService
import logging

from interface.serializers.dash_029_serializer import WidgetSerializer

logger = logging.getLogger(__name__)

from django.http import Http404


class UserHeatmapWidgetView(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.service = Dash009WidgetsService()

    @swagger_auto_schema(
        operation_id="get_user_widget",
        operation_summary="Get widget for a specific user",
        operation_description="Retrieve the widget associated with a given user ID from Azure Data Lake Storage",
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_QUERY,
                description="Site ID",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "pump_id",
                openapi.IN_QUERY,
                description="Pump ID",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page",
                type=openapi.TYPE_STRING,
                required=True,
            ),


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
                                "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "widget": openapi.Schema(
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
                                                    "siteName": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "columnName": openapi.Schema(type=openapi.TYPE_STRING),
                                                },
                                            ),
                                        ),
                                        "data": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
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
                                        "created_at": openapi.Schema(type=openapi.TYPE_STRING),
                                        "updated_at": openapi.Schema(type=openapi.TYPE_STRING),
                                    },
                                ),
                            },
                        ),
                    },
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Widget retrieved successfully for user aa2d6ecf-85e4-4d91-a310-e58458795cfb",
                        "data": {
                            "user_id": "aa2d6ecf-85e4-4d91-a310-e58458795cfb",
                            "widget": {
                                "id": "88a2f610-8b89-4764-a4d3-e6d38f1cc2d1",
                                "name": "My Widget",
                                "columns": [
                                    {
                                        "siteName": "UAQ",
                                        "tableName": "UAQ_SEC",
                                        "columnName": "DateTime",
                                    }
                                ],
                                "data": [{"name": "DateTime", "data": []}],
                                "created_at": "2025-09-03 20:30:30+00:00",
                                "updated_at": "2025-09-03 20:30:30.511917+00:00",
                            },
                        },
                    }
                },
            ),
            404: openapi.Response(
                "Not Found",
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
        tags=["Dash-009-Heatmap-Widget"],
    )
    def get(self, request):
        """Get the widget for a specific user"""
        try:
            user = self.validate_authentication(request)
            user_id = user['id']
            site_id = request.query_params.get('site_id')
            pump_id = request.query_params.get('pump_id')
            page = request.query_params.get('page')

            widget_data = self.service.get_widget(site_id, pump_id,user_id, page)
            
            if not widget_data:
                return ResponseBuilder.success(
                    data=None,
                    message="No widget found for the specified criteria",
                )
            
            return ResponseBuilder.success(
                data=widget_data,
                message=f"Widget retrieved successfully for user",
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error in GET user widget: {str(e)}")
            return ResponseBuilder.error(message=str(e))

    @swagger_auto_schema(
        operation_id="create_or_update_user_widget",
        operation_summary="Create or update widget for a user",
        operation_description="Create or update a single widget for a specific user. If a widget already exists for the user, it will be replaced.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["columns", "data"],
            properties={
                "site_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Site ID for Heatmap Widget",
                ),
                "pump_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Pump ID for Heatmap Widget",
                ),
                "columns": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="Column definitions",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "columnName": openapi.Schema(type=openapi.TYPE_STRING),
                            "yAxisOptions": openapi.Schema(type=openapi.TYPE_OBJECT, )
                        },
                    ),
                ),
            },
        ),
        examples={
            "application/json": {
                "site_id": "Rabigh3",
                "pump_id": "Seawater Intake",
                "columns": [
                    {
                        "columnName": "Flow",
                        "yAxisOptions": {"min": 0, "max": 50, "colors": ["#3b82f6"], "reverse": False , "colorScheme": "RGB" }

                    }
                ]
               
            }
        },
        responses={
            201: openapi.Response(
                "Created/Updated Successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "widget": openapi.Schema(type=openapi.TYPE_OBJECT),
                            },
                        ),
                    },
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Widget created successfully for user aa2d6ecf-85e4-4d91-a310-e58458795cfb",
                        "data": {
                            "user_id": "aa2d6ecf-85e4-4d91-a310-e58458795cfb",
                            "widget": {
                                "id": "ddf70143-af12-46ef-97e4-5d5fa462ff3f",
                                "name": "Flow Rate Heatmap",
                                "columns": [
                                    {
                                        "siteName": "Site1",
                                        "tableName": "Table1",
                                        "columnName": "Flow",
                                    }
                                ],
                                "data": [{"name": "Flow Rate", "data": [10, 20, 30]}],
                                "created_at": "2025-10-15 12:00:00+00:00",
                                "updated_at": "2025-10-15 12:00:00+00:00",
                            },
                        },
                    }
                },
            ),
            400: openapi.Response(
                "Bad Request",
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
        tags=["Dash-009-Heatmap-Widget"],
    )
    def post(self, request):
        """Create or update a widget for a user"""
        try:
            user = self.validate_authentication(request)
            user_id = user['id']
            data  = request.data

            serializer = WidgetSerializer(data=data)
            if serializer.is_valid():
                widget_data = self.service.create_widget(request.data, user_id)

                return ResponseBuilder.success(
                    data=widget_data,
                    message=f"Widget created successfully for user ",
                    status_code=201,
                )
            else:
                return ResponseBuilder.error(
                    message="Invalid data",
                    data={"details": serializer.errors},
                    status_code=400,
                )
        except Exception as e:
            logger.error(f"Error in POST user widget: {str(e)}")
            return ResponseBuilder.error(message=str(e))

        
    def validate_authentication(self, request):
        """Validate JWT authentication and return user"""
        user = getattr(request, "jwt_user", None)
        if not user:
            raise PermissionError("Authentication required")
        return user

