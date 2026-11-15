import logging
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from infrastructure.services.dash_030 import Dash_030Service
from infrastructure.applevel.responseBuilder import ResponseBuilder

logger = logging.getLogger(__name__)


class Dash030BaseView(APIView):
    """Base view with shared validation logic for Dash-030 endpoints"""
    
    service = Dash_030Service()

    def validate_authentication(self, request):
        """Validate JWT authentication and return user"""
        user = getattr(request, "jwt_user", None)
        if not user:
            raise PermissionError("Authentication required")
        return user

    def validate_and_parse_params(self, request, require_racks=False):
        """
        Extract and validate common query parameters
        
        Args:
            request: Django request object
            require_racks: Whether racks parameter is required
            
        Returns:
            dict: Validated parameters
            
        Raises:
            ValueError: If validation fails
        """
        site_name = request.GET.get("site_name")
        if not site_name:
            raise ValueError("Site name is required")

        stream = self._validate_stream(request.GET.get("stream"), site_name)
        racks = self._parse_racks(request.GET.get("racks"))
        
        if require_racks and not racks:
            raise ValueError("Racks parameter is required")

        return {
            "site_name": site_name,
            "stream": stream,
            "racks": racks,
            "from_date": request.GET.get("from_date"),
            "to_date": request.GET.get("to_date")
        }

    def _validate_stream(self, stream, site_name):
        """Validate stream parameter based on site"""
        if site_name == "UAQ":
            if stream and stream not in ["Stream1", "Stream2", "Stream3"]:
                raise ValueError("For UAQ site, stream must be one of: Stream1, Stream2, Stream3")
            return stream or "Stream1"
        elif stream:
            raise ValueError("Stream parameter is only valid for UAQ site")
        return None

    def _parse_racks(self, racks_param):
        """Parse comma-separated racks parameter"""
        if not racks_param:
            return None
        return [rack.strip() for rack in racks_param.split(',') if rack.strip()]

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


class ROSummaryMergedView(Dash030BaseView):
    """
    RO Summary Merged View for merging three RO Summary tables based on site name and datetime.
    """
    
    @swagger_auto_schema(
        operation_id="dash_030_ro_summary_merged",
        operation_summary="Get merged RO Summary data from three tables",
        operation_description="Retrieve and merge data from RO_Summary_Weighted_Total_1stPass, 2ndPass, and 1st_2ndPass tables based on site name and datetime filtering",
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
                name="stream",
                in_=openapi.IN_QUERY,
                description="Stream identifier (only for UAQ site: 'Stream1', 'Stream2', 'Stream3'). Defaults to 'Stream1' for UAQ.",
                type=openapi.TYPE_STRING,
                required=False,
                example="Stream1",
                enum=["Stream1", "Stream2", "Stream3"]
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
                        "message": "RO Summary merged data retrieved successfully",
                        "data": {
                            "merged_data": [
                                {
                                    "columnName": "merged_datetime",
                                    "columnType": "timestamp",
                                    "tableName": "RO_Summary_Merged",
                                    "siteName": "Jubail-Jazlah",
                                    "dataSource": ["2025-05-01T10:00:00Z", "2025-05-01T11:00:00Z"]
                                },
                                {
                                    "columnName": "first_pass_value",
                                    "columnType": "double",
                                    "tableName": "RO_Summary_Merged",
                                    "siteName": "Jubail-Jazlah",
                                    "dataSource": [1.25, 1.87]
                                }
                            ]
                        }
                    }
                }
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-030"],
    )
    def get(self, request):
        try:
            user = self.validate_authentication(request)
            params = self.validate_and_parse_params(request)

            logger.info(f"Processing RO Summary merge request for site: {params['site_name']}, stream: {params['stream']}, from_date: {params['from_date']}, to_date: {params['to_date']}")

            result = self.service.get_ro_summary_merged_data(
                site_name=params["site_name"],
                stream=params["stream"],
                start_date=params["from_date"],
                end_date=params["to_date"],
                user=user
            )

            return ResponseBuilder.success(
                data=result,
                message="RO Summary merged data retrieved successfully"
            )

        except Exception as e:
            return self.handle_exceptions(e, "ROSummaryMergedView")


class ConductivitiesPass1View(Dash030BaseView):
    """
    Conductivities Pass 1 View for grouped rack-based averages.
    """
    
    @swagger_auto_schema(
        operation_id="dash_030_conductivities_pass1",
        operation_summary="Get averaged conductivities data grouped by racks",
        operation_description="Retrieve Rear_Permeate_Weighted_Conductivity and Front_Permeate_Weighted_Conductivity data from RO_Summary_Conductivities_pass1 table, grouped by racks with averages calculated based on date range and rack filters",
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
                name="stream",
                in_=openapi.IN_QUERY,
                description="Stream identifier (only for UAQ site: 'Stream1', 'Stream2', 'Stream3'). Defaults to 'Stream1' for UAQ.",
                type=openapi.TYPE_STRING,
                required=False,
                example="Stream1",
                enum=["Stream1", "Stream2", "Stream3"]
            ),
            openapi.Parameter(
                name="racks",
                in_=openapi.IN_QUERY,
                description="Comma-separated rack names for filtering (e.g., 'Rack_1,Rack_10,Rack_5')",
                type=openapi.TYPE_STRING,
                required=False,
                example="Rack_1,Rack_10",
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
            200: openapi.Response(description="Success"),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-030"],
    )
    def get(self, request):
        try:
            user = self.validate_authentication(request)
            params = self.validate_and_parse_params(request)

            logger.info(f"Processing conductivities pass1 request for site: {params['site_name']}, stream: {params['stream']}, racks: {params['racks']}, from_date: {params['from_date']}, to_date: {params['to_date']}")

            conductivities_data = self.service.get_conductivities_pass1_data(
                site_name=params["site_name"],
                stream=params["stream"],
                racks=params["racks"],
                from_date=params["from_date"],
                to_date=params["to_date"],
                user=user
            )

            return ResponseBuilder.success(
                data=conductivities_data,
                message="Conductivities Pass 1 data retrieved successfully"
            )

        except Exception as e:
            return self.handle_exceptions(e, "ConductivitiesPass1View")


class ConductivitiesPass2View(Dash030BaseView):
    """
    Conductivities Pass 2 View for grouped rack-based averages.
    """
    
    @swagger_auto_schema(
        operation_id="dash_030_conductivities_pass_2",
        operation_summary="Get averaged conductivities data grouped by racks",
        operation_description="Retrieve Rear_Permeate_Weighted_Conductivity and Front_Permeate_Weighted_Conductivity data from RO_Summary_Conductivities_pass1 table, grouped by racks with averages calculated based on date range and rack filters",
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
                name="stream",
                in_=openapi.IN_QUERY,
                description="Stream identifier (only for UAQ site: 'Stream1', 'Stream2', 'Stream3'). Defaults to 'Stream1' for UAQ.",
                type=openapi.TYPE_STRING,
                required=False,
                example="Stream1",
                enum=["Stream1", "Stream2", "Stream3"]
            ),
            openapi.Parameter(
                name="racks",
                in_=openapi.IN_QUERY,
                description="Comma-separated rack names for filtering (e.g., 'Rack_1,Rack_10,Rack_5')",
                type=openapi.TYPE_STRING,
                required=False,
                example="Rack_1,Rack_10",
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
            200: openapi.Response(description="Success"),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-030"],
    )
    def get(self, request):
        try:
            user = self.validate_authentication(request)
            params = self.validate_and_parse_params(request)

            logger.info(f"Processing conductivities pass2 request for site: {params['site_name']}, stream: {params['stream']}, racks: {params['racks']}, from_date: {params['from_date']}, to_date: {params['to_date']}")

            conductivities_data = self.service.get_conductivities_pass2_data(
                site_name=params["site_name"],
                stream=params["stream"],
                racks=params["racks"],
                from_date=params["from_date"],
                to_date=params["to_date"],
                user=user
            )

            return ResponseBuilder.success(
                data=conductivities_data,
                message="Conductivities Pass 2 data retrieved successfully"
            )

        except Exception as e:
            return self.handle_exceptions(e, "ConductivitiesPass2View")


class ConductivitiesPass1RawDataView(Dash030BaseView):
    """
    Conductivities Pass 1 Raw Data View - returns raw table data without aggregation.
    """
    
    @swagger_auto_schema(
        operation_id="dash_030_conductivities_pass1_raw",
        operation_summary="Get raw conductivities Pass 1 table data",
        operation_description="Retrieve raw data from RO_Summary_Conductivities_pass1 table with filtering by site, stream, date range, and racks. Returns all columns without aggregation.",
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
                name="stream",
                in_=openapi.IN_QUERY,
                description="Stream identifier (only for UAQ site: 'Stream1', 'Stream2', 'Stream3'). Defaults to 'Stream1' for UAQ.",
                type=openapi.TYPE_STRING,
                required=False,
                example="Stream1",
                enum=["Stream1", "Stream2", "Stream3"]
            ),
            openapi.Parameter(
                name="racks",
                in_=openapi.IN_QUERY,
                description="Comma-separated rack names for filtering (e.g., 'Rack_1,Rack_10,Rack_5')",
                type=openapi.TYPE_STRING,
                required=False,
                example="Rack_1,Rack_10",
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
            200: openapi.Response(description="Success"),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-030"],
    )
    def get(self, request):
        try:
            user = self.validate_authentication(request)
            params = self.validate_and_parse_params(request)

            logger.info(f"Processing conductivities pass1 raw data request for site: {params['site_name']}, stream: {params['stream']}, racks: {params['racks']}, from_date: {params['from_date']}, to_date: {params['to_date']}")

            raw_data = self.service.get_conductivities_pass1_raw_data(
                site_name=params["site_name"],
                stream=params["stream"],
                racks=params["racks"],
                from_date=params["from_date"],
                to_date=params["to_date"],
                user=user
            )

            return ResponseBuilder.success(
                data=raw_data,
                message="Conductivities Pass 1 raw data retrieved successfully"
            )

        except Exception as e:
            return self.handle_exceptions(e, "ConductivitiesPass1RawDataView")


class ConductivitiesPass2RawDataView(Dash030BaseView):
    """
    Conductivities Pass 2 Raw Data View - returns raw table data without aggregation.
    """
    
    @swagger_auto_schema(
        operation_id="dash_030_conductivities_pass2_raw",
        operation_summary="Get raw conductivities Pass 2 table data",
        operation_description="Retrieve raw data from RO_Summary_Conductivities_Pass2 table with filtering by site, stream, date range, and racks. Returns all columns without aggregation.",
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
                name="stream",
                in_=openapi.IN_QUERY,
                description="Stream identifier (only for UAQ site: 'Stream1', 'Stream2', 'Stream3'). Defaults to 'Stream1' for UAQ.",
                type=openapi.TYPE_STRING,
                required=False,
                example="Stream1",
                enum=["Stream1", "Stream2", "Stream3"]
            ),
            openapi.Parameter(
                name="racks",
                in_=openapi.IN_QUERY,
                description="Comma-separated rack names for filtering (e.g., 'Rack_1,Rack_10,Rack_5')",
                type=openapi.TYPE_STRING,
                required=False,
                example="Rack_1,Rack_10",
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
            200: openapi.Response(description="Success"),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-030"],
    )
    def get(self, request):
        try:
            user = self.validate_authentication(request)
            params = self.validate_and_parse_params(request)

            logger.info(f"Processing conductivities pass2 raw data request for site: {params['site_name']}, stream: {params['stream']}, racks: {params['racks']}, from_date: {params['from_date']}, to_date: {params['to_date']}")

            raw_data = self.service.get_conductivities_pass2_raw_data(
                site_name=params["site_name"],
                stream=params["stream"],
                racks=params["racks"],
                from_date=params["from_date"],
                to_date=params["to_date"],
                user=user
            )

            return ResponseBuilder.success(
                data=raw_data,
                message="Conductivities Pass 2 raw data retrieved successfully"
            )

        except Exception as e:
            return self.handle_exceptions(e, "ConductivitiesPass2RawDataView")
    
class FetchRacksView(Dash030BaseView):
    """
    Fetch Racks View - returns unique rack values from conductivities tables.
    """
    
    @swagger_auto_schema(
        operation_id="dash_030_fetch_racks",
        operation_summary="Get unique rack values for a site",
        operation_description="Retrieve unique rack values from RO_Summary_Conductivities_pass1 and RO_Summary_Conductivities_Pass2 tables based on site name",
        manual_parameters=[
            openapi.Parameter(
                name="site_name",
                in_=openapi.IN_QUERY,
                description="Site name identifier (e.g., 'Jubail-Jazlah', 'Rabigh3', 'STPC', 'UAQ')",
                type=openapi.TYPE_STRING,
                required=True,
                example="STPC",
            ),
            openapi.Parameter(
                name="stream",
                in_=openapi.IN_QUERY,
                description="Stream identifier (only for UAQ site: 'Stream1', 'Stream2', 'Stream3'). Defaults to 'Stream1' for UAQ.",
                type=openapi.TYPE_STRING,
                required=False,
                example="Stream1",
                enum=["Stream1", "Stream2", "Stream3"]
            ),
        ],
        responses={
            200: openapi.Response(
                description="Success",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Unique racks retrieved successfully",
                        "data": [
                            {
                                "rackLabel": "RACK_01",
                                "siteName": "STPC",
                                "tableName": "RO_Summary_Conductivities",
                                "rackValue": "RACK_01"
                            }
                        ]
                    }
                }
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(description="Internal Server Error"),
        },
        tags=["Dash-030"],
    )
    def get(self, request):
        try:
            user = self.validate_authentication(request)
            params = self.validate_and_parse_params(request, require_racks=False)

            logger.info(f"Fetching unique racks for site: {params['site_name']}, stream: {params['stream']}")

            unique_racks = self.service.get_unique_racks(
                site_name=params["site_name"],
                stream=params["stream"],
                user=user
            )

            return ResponseBuilder.success(
                data=unique_racks,
                message="Unique racks retrieved successfully"
            )

        except Exception as e:
            return self.handle_exceptions(e, "FetchRacksView")