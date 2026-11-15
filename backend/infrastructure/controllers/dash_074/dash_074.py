import logging
import re
from datetime import datetime
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.dash_074 import Dash074Service
#from interface.schemas.dash_074_schema import ProcessOverviewResponseSchema

logger = logging.getLogger(__name__)


class Dash074BaseView(APIView):
    """Base view with shared validation logic for Dash-074 endpoints"""
    
    service = Dash074Service()
    
    def validate_and_parse_params(self, request):
        """
        Extract and validate common query parameters
        
        Args:
            request: Django request object
            
        Returns:
            dict: Validated parameters
            
        Raises:
            ValueError: If validation fails
        """
        site_name = request.GET.get("site_name")
        if not site_name:
            raise ValueError("Site name is required")
        
        
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

          
        # Validate date format (YYYY-MM-DD)
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if from_date and not re.match(date_pattern, from_date):
            logger.warning(f"Invalid from_date format: {from_date}")
            return ResponseBuilder.error(
                message="Invalid from_date format. Expected YYYY-MM-DD",
                data={"from_date": from_date},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if to_date and not re.match(date_pattern, to_date):
            logger.warning(f"Invalid to_date format: {to_date}")
            return ResponseBuilder.error(
                message="Invalid to_date format. Expected YYYY-MM-DD",
                data={"to_date": to_date},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Validate date range
        if from_date and to_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')

                if from_date_obj > to_date_obj:
                    logger.warning(f"Invalid date range: from_date {from_date} is after to_date {to_date}")
                    return ResponseBuilder.error(
                        message="Invalid date range: from_date cannot be after to_date",
                        data={"from_date": from_date, "to_date": to_date},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError as ve:
                logger.warning(f"Invalid date values: {str(ve)}")
                return ResponseBuilder.error(
                    message=f"Invalid date values: {str(ve)}",
                    data={"from_date": from_date, "to_date": to_date},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        return {
            "site_name": site_name,
            "from_date": from_date,
            "to_date": to_date
        }
        
        
    def validate_and_parse_params_graph_data(self, request):
        """
        Extract and validate common query parameters
        
        Args:
            request: Django request object
            
        Returns:
            dict: Validated parameters
            
        Raises:
            ValueError: If validation fails
        """
        site_name = request.GET.get("site_name")
        if not site_name:
            raise ValueError("Site name is required")
        
        
        asset_name = request.query_params.get('asset_name')
        if not asset_name:
            raise ValueError("Asset name is required")
        
        to_date = request.query_params.get('to_date')

          
        # Validate date format (YYYY-MM-DD)
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'

        if to_date and not re.match(date_pattern, to_date):
            logger.warning(f"Invalid to_date format: {to_date}")
            return ResponseBuilder.error(
                message="Invalid to_date format. Expected YYYY-MM-DD",
                data={"to_date": to_date},
                status_code=status.HTTP_400_BAD_REQUEST
            )


        return {
            "site_name": site_name,
            "asset_name": asset_name,
            "to_date": to_date
        }
        
    def validate_and_parse_params_history_data(request):
        """
        Extract and validate common query parameters
        
        Args:
            request: Django request object
            
        Returns:
            dict: Validated parameters
            
        Raises:
            ValueError: If validation fails
        """
        site_name = request.GET.get("site_name")
        if not site_name:
            raise ValueError("Site name is required")
        
        return {
            "site_name": site_name
        }
        
        
    
    def handle_exceptions(self, e, view_name):
        """Centralized exception handling"""
        if isinstance(e, ValueError):
            logger.warning(f"Validation error in {view_name}: {e}")
            return ResponseBuilder.error(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(e, PermissionError):
            logger.warning(f"Permission denied in {view_name}: {e}")
            return ResponseBuilder.error(
                message=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        else:
            logger.exception(f"Unexpected error in {view_name}")
            return ResponseBuilder.error(
                message="Internal server error",
                data={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertsTableView(Dash074BaseView):
    """
    Displays the Alerts Table based on site name and datetime.
    """
    
    @swagger_auto_schema(
        operation_id="dash_074_alerts_table",
        operation_summary="Get data from SS Alerts table",
        operation_description="Retrieve data from SS Assets ALerts based on site name and datetime filtering",
        manual_parameters=[
            openapi.Parameter(
                name="site_name",
                in_=openapi.IN_QUERY,
                description="Site name identifier (e.g., 'Jubail-Jazlah', 'Rabigh3', 'STPC', 'UAQ')",
                type=openapi.TYPE_STRING,
                required=True,
                example="Jubail-Jazlah",
            ),
            openapi.Parameter(
                name="from_date",
                in_=openapi.IN_QUERY,
                description="Start Date and Time (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)",
                type=openapi.TYPE_STRING,
                required=False,
                example="2025-05-01T00:00:00Z",
            ),
            openapi.Parameter(
                name="to_date",
                in_=openapi.IN_QUERY,
                description="End Date and Time (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)",
                type=openapi.TYPE_STRING,
                required=False,
                example="2025-05-31T23:59:59Z",
            ),
        ],
        responses={
            200: openapi.Response(
                description="Success",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "SS Alerts data retrieved successfully",
                        "data": {
                            "alerts_data": {
                                    "columnName": "datetime",
                                    "columnType": "timestamp",
                                    "tableName": "SS_Assets_Alerts",
                                    "siteName": "Jubail-Jazlah",
                                    "dataSource": ["2025-05-01T10:00:00Z", "2025-05-01T11:00:00Z"]
                                            }
                                 }
                                        }
                }
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-074"],
    )
    def get(self, request):
        try:
            params = self.validate_and_parse_params(request)

            logger.info(f"Processing Alerts Data request for site: {params['site_name']}, from_date: {params['from_date']}, to_date: {params['to_date']}")

            result = self.service.get_alerts_table_data(
                site_id=params["site_name"],
                from_date=params["from_date"],
                to_date=params["to_date"],
            )

            return ResponseBuilder.success(
                data=result,
                message="Alerts data retrieved successfully"
            )

        except Exception as e:
            return self.handle_exceptions(e, "AlertsTableView")
        
        
class AlertsGraphView(Dash074BaseView):
    """
    Displays the Alerts Graph based on site name and datetime.
    """
    
    @swagger_auto_schema(
        operation_id="dash_074_alerts_graph",
        operation_summary="Get data from SS Assets Data table for data graph",
        operation_description="Retrieve data from SS Assets Alerts and SS Assets Data tables for Alerts Graph based on site name and datetime filtering",
        manual_parameters=[
            openapi.Parameter(
                name="site_name",
                in_=openapi.IN_QUERY,
                description="Site name identifier (e.g., 'Jubail-Jazlah', 'Rabigh3', 'STPC', 'UAQ')",
                type=openapi.TYPE_STRING,
                required=True,
                example="Jubail-Jazlah",
            ),
            openapi.Parameter(
                name="asset_name",
                in_=openapi.IN_QUERY,
                description="Asset name identifier (e.g., 'Filter', 'Pump', 'Pass1', 'Pass2')",
                type=openapi.TYPE_STRING,
                required=True,
                example="Filter",
            ),
            openapi.Parameter(
                name="to_date",
                in_=openapi.IN_QUERY,
                description="End Date and Time (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)",
                type=openapi.TYPE_STRING,
                required=False,
                example="2025-05-31T23:59:59Z",
            ),
        ],
        responses={
            200: openapi.Response(
                description="Success",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "SS Alerts data for Alerts graph retrieved successfully",
                        "data": {
                            "alerts_graph_data": [
                                # {
                                #     "columnName": "merged_datetime",
                                #     "columnType": "timestamp",
                                #     "tableName": "RO_Summary_Merged",
                                #     "siteName": "Jubail-Jazlah",
                                #     "dataSource": ["2025-05-01T10:00:00Z", "2025-05-01T11:00:00Z"]
                                # },
                                # {
                                #     "columnName": "first_pass_value",
                                #     "columnType": "double",
                                #     "tableName": "RO_Summary_Merged",
                                #     "siteName": "Jubail-Jazlah",
                                #     "dataSource": [1.25, 1.87]
                                # }
                            ]
                        }
                    }
                }
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-074"],
    )
    def get(self, request):
        try:
            params = self.validate_and_parse_params_graph_data(request)

            logger.info(f"Processing Alerts Data request for site: {params['site_name']}, asset_name: {params['asset_name']}, to_date: {params['to_date']}")

            result = self.service.get_alerts_graph_data(
                site_name=params["site_name"],
                asset_name=params["asset_name"],
                to_date=params["to_date"]
            )

            return ResponseBuilder.success(
                data=result,
                message="Alerts graph data retrieved successfully"
            )

        except Exception as e:
            return self.handle_exceptions(e, "AlertsGraphView")
        
        
        
class AssetHistoryView(Dash074BaseView):
    """
    Displays the Asset history based on site name.
    """
    
    @swagger_auto_schema(
        operation_id="dash_074_asset_history",
        operation_summary="Get data from Assets history table",
        operation_description="Retrieve data from SS Asset History based on site name",
        manual_parameters=[
            openapi.Parameter(
                name="site_name",
                in_=openapi.IN_QUERY,
                description="Site name identifier (e.g., 'Jubail-Jazlah', 'Rabigh3', 'STPC', 'UAQ')",
                type=openapi.TYPE_STRING,
                required=True,
                example="Jubail-Jazlah",
            )
        ],
        
        responses={
            200: openapi.Response(
                description="Success",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "SS Asset History data retrieved successfully",
                        "data": {
                            "asset_history_data": [
                                # {
                                #     "columnName": "merged_datetime",
                                #     "columnType": "timestamp",
                                #     "tableName": "RO_Summary_Merged",
                                #     "siteName": "Jubail-Jazlah",
                                #     "dataSource": ["2025-05-01T10:00:00Z", "2025-05-01T11:00:00Z"]
                                # },
                                # {
                                #     "columnName": "first_pass_value",
                                #     "columnType": "double",
                                #     "tableName": "RO_Summary_Merged",
                                #     "siteName": "Jubail-Jazlah",
                                #     "dataSource": [1.25, 1.87]
                                # }
                            ]
                        }
                    }
                }
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-074"],
    )
    def get(self, request):
            
        site_name = request.GET.get("site_name")
        if not site_name:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id")
        try:
    
            data = self.service.get_asset_history_data(site_name =site_name)

            return ResponseBuilder.success(
                data=data,
                message="Successfully retrieved Asset History Data"
            )

        except Exception as e:
            return self.handle_exceptions(e, "AssetHistoryView")
    
        
       
        

