"""
Refactored Widgets Controller - Under 250 lines
Uses modular components for validation, operations, and schemas.
Follows single responsibility principle for better maintainability.
"""
import json
import logging

from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.controllers.widgets.crud_operations import WidgetCrudOperations
from infrastructure.controllers.widgets.bulk_operations import WidgetBulkOperations
from infrastructure.controllers.widgets.swagger_schemas import WidgetSwaggerSchemas

logger = logging.getLogger(__name__)


class WidgetsView(APIView):
    """
    Optimized widgets controller with modular architecture.
    Handles widget CRUD operations for analysis dashboards.
    """
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.bulk_operations = WidgetBulkOperations()
        self.crud_operations = WidgetCrudOperations()
        self.schemas = WidgetSwaggerSchemas()

    @swagger_auto_schema(
        operation_id="get_widgets_for_analysis",
        operation_summary="Get all widgets for a specific analysis",
        operation_description="Retrieve all widgets associated with a given analysis ID from Azure Data Lake Storage",
        manual_parameters=[WidgetSwaggerSchemas.ANALYSIS_ID_PARAMETER],
        responses={
            200: WidgetSwaggerSchemas.WIDGET_LIST_RESPONSE,
            400: WidgetSwaggerSchemas.ERROR_RESPONSE,
            500: WidgetSwaggerSchemas.ERROR_RESPONSE
        },
        examples={
            "application/json": WidgetSwaggerSchemas.WIDGET_LIST_EXAMPLE
        },
        tags=["Widgets"]
    )
    def get(self, request, analysisID):
        """Get all widgets for an analysis."""
        try:
            result = self.bulk_operations.get_widgets_for_analysis(analysisID)
            
            if result["success"]:
                return ResponseBuilder.success(
                    data=result["data"],
                    message=result["message"]
                )
            else:
                return ResponseBuilder.error(message=result["message"])
                
        except Exception as e:
            logger.error(f"Unexpected error in get widgets: {e}")
            return ResponseBuilder.error(message="Internal server error")

    @swagger_auto_schema(
        operation_id="create_single_widget",
        operation_summary="Create a new widget",
        operation_description="Create a new widget for the specified analysis",
        manual_parameters=[WidgetSwaggerSchemas.ANALYSIS_ID_PARAMETER],
        request_body=WidgetSwaggerSchemas.CREATE_WIDGET_REQUEST,
        responses={
            201: WidgetSwaggerSchemas.CREATE_RESPONSE,
            400: WidgetSwaggerSchemas.ERROR_RESPONSE,
            500: WidgetSwaggerSchemas.ERROR_RESPONSE
        },
        examples={
            "application/json": WidgetSwaggerSchemas.CREATE_WIDGET_EXAMPLE
        },
        tags=["Widgets"]
    )
    def post(self, request, analysisID):
        """Create a single widget."""
        try:
            widget_data = request.data
            result = self.crud_operations.create_single_widget(analysisID, widget_data)
            
            if result["success"]:
                return ResponseBuilder.success(
                    data=result["data"],
                    message=result["message"],
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return ResponseBuilder.error(
                    message=result["message"],
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in create widget: {e}")
            return ResponseBuilder.error(message="Internal server error")


class WidgetsBulkView(APIView):
    """Handle bulk widget operations."""
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.operations = WidgetOperations()

    @swagger_auto_schema(
        operation_id="create_bulk_widgets",
        operation_summary="Create multiple widgets",
        operation_description="Create multiple widgets in a single request",
        manual_parameters=[WidgetSwaggerSchemas.ANALYSIS_ID_PARAMETER],
        request_body=WidgetSwaggerSchemas.BULK_CREATE_REQUEST,
        responses={
            201: WidgetSwaggerSchemas.BULK_CREATE_RESPONSE,
            400: WidgetSwaggerSchemas.ERROR_RESPONSE,
            500: WidgetSwaggerSchemas.ERROR_RESPONSE
        },
        tags=["Widgets"]
    )
    def post(self, request, analysisID):
        """Create multiple widgets."""
        try:
            widgets_data = request.data.get('widgets', [])
            result = self.bulk_operations.create_bulk_widgets(analysisID, widgets_data)
            
            if result["success"]:
                return ResponseBuilder.success(
                    data=result["data"],
                    message=result["message"],
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return ResponseBuilder.error(
                    message=result["message"],
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in bulk create widgets: {e}")
            return ResponseBuilder.error(message="Internal server error")


class WidgetDetailView(APIView):
    """Handle individual widget operations."""
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.crud_operations = WidgetCrudOperations()

    @swagger_auto_schema(
        operation_id="get_widget_by_id",
        operation_summary="Get specific widget",
        operation_description="Retrieve a specific widget by ID",
        manual_parameters=[
            WidgetSwaggerSchemas.ANALYSIS_ID_PARAMETER,
            WidgetSwaggerSchemas.WIDGET_ID_PARAMETER
        ],
        responses={
            200: WidgetSwaggerSchemas.CREATE_RESPONSE,
            404: WidgetSwaggerSchemas.ERROR_RESPONSE,
            500: WidgetSwaggerSchemas.ERROR_RESPONSE
        },
        tags=["Widgets"]
    )
    def get(self, request, analysisID, widgetId):
        """Get a specific widget."""
        try:
            result = self.crud_operations.get_widget_by_id(analysisID, widgetId)
            
            if result["success"]:
                return ResponseBuilder.success(
                    data=result["data"],
                    message=result["message"]
                )
            else:
                return ResponseBuilder.error(
                    message=result["message"],
                    status_code=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in get widget: {e}")
            return ResponseBuilder.error(message="Internal server error")

    @swagger_auto_schema(
        operation_id="update_widget",
        operation_summary="Update widget",
        operation_description="Update a specific widget",
        manual_parameters=[
            WidgetSwaggerSchemas.ANALYSIS_ID_PARAMETER,
            WidgetSwaggerSchemas.WIDGET_ID_PARAMETER
        ],
        request_body=WidgetSwaggerSchemas.UPDATE_WIDGET_REQUEST,
        responses={
            200: WidgetSwaggerSchemas.CREATE_RESPONSE,
            400: WidgetSwaggerSchemas.ERROR_RESPONSE,
            404: WidgetSwaggerSchemas.ERROR_RESPONSE,
            500: WidgetSwaggerSchemas.ERROR_RESPONSE
        },
        tags=["Widgets"]
    )
    def put(self, request, analysisID, widgetId):
        """Update a widget."""
        try:
            update_data = request.data
            result = self.crud_operations.update_widget(analysisID, widgetId, update_data)
            
            if result["success"]:
                return ResponseBuilder.success(
                    data=result["data"],
                    message=result["message"]
                )
            else:
                return ResponseBuilder.error(
                    message=result["message"],
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in update widget: {e}")
            return ResponseBuilder.error(message="Internal server error")

    @swagger_auto_schema(
        operation_id="delete_widget",
        operation_summary="Delete widget",
        operation_description="Delete a specific widget",
        manual_parameters=[
            WidgetSwaggerSchemas.ANALYSIS_ID_PARAMETER,
            WidgetSwaggerSchemas.WIDGET_ID_PARAMETER
        ],
        responses={
            200: WidgetSwaggerSchemas.CREATE_RESPONSE,
            404: WidgetSwaggerSchemas.ERROR_RESPONSE,
            500: WidgetSwaggerSchemas.ERROR_RESPONSE
        },
        tags=["Widgets"]
    )
    def delete(self, request, analysisID, widgetId):
        """Delete a widget."""
        try:
            result = self.crud_operations.delete_widget(analysisID, widgetId)
            
            if result["success"]:
                return ResponseBuilder.success(
                    data=result["data"],
                    message=result["message"]
                )
            else:
                return ResponseBuilder.error(
                    message=result["message"],
                    status_code=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in delete widget: {e}")
            return ResponseBuilder.error(message="Internal server error")


class WidgetsHealthView(APIView):
    """Health check endpoint for widgets service."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="widgets_health_check",
        operation_summary="Widgets service health check",
        operation_description="Check if widgets service is operational",
        responses={
            200: WidgetSwaggerSchemas.CREATE_RESPONSE,
            500: WidgetSwaggerSchemas.ERROR_RESPONSE
        },
        tags=["Widgets"]
    )
    def get(self, request):
        """Health check for widgets service."""
        try:
            return ResponseBuilder.success(
                data={"status": "healthy", "service": "widgets"},
                message="Widgets service is operational"
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ResponseBuilder.error(message="Service unhealthy")
