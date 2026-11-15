from pickle import FALSE

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.dash_002 import Dash002Service
from interface.schemas.dash_002_schema import ProcessOverviewResponseSchema


class CardsAndGraph(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="cards_data_process_overview",
        operation_summary="Get Cards Data",
        operation_description="Fetches Cards Data.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
        ],
        responses={
            200: openapi.Response("Success", ProcessOverviewResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-002"],
    )

    def get(self, request):
        site = request.GET.get('site_id')
        if not site:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id")
        try:
            with Dash002Service() as service:
                data = service.get_cards_and_graph_data(site_id=site)

                return ResponseBuilder.success(
                    data=data,
                    message="Successfully retrieved Card and Graph Data."
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Cards and Graph",
                data={"error": str(e), "site": site}
            )

class ProcessOverview(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="process_overview",
        operation_summary="Get Process overview Table Data",
        operation_description="Fetches Process overview Table Data.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
        ],
        responses={
            200: openapi.Response("Success", ProcessOverviewResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-002"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        if not site:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id")
        try:
            with Dash002Service() as service:
                data = service.get_process_condition_and_unit_in_service_data(site_id=site)

                return ResponseBuilder.success(
                    data=data,
                    message="Successfully retrieved process Overview Data"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Process Overview",
                data={"error": str(e), "site": site}
            )

class OperationalStatus(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="operational_status",
        operation_summary="Get Operational Status Table Data",
        operation_description="Fetches Operational Status Table Data.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('to_date', openapi.IN_QUERY, description="To date", type=openapi.TYPE_STRING),
            openapi.Parameter('area', openapi.IN_QUERY, description="Area", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response("Success", ProcessOverviewResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-002"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        to_date = request.GET.get('to_date')
        area = request.GET.get('area')
        if not site:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id")
        try:
            with Dash002Service() as service:
                data = service.get_operational_status_data(site_id=site, to_date=to_date, area=area)

                return ResponseBuilder.success(
                    data=data,
                    message="Successfully retrieved Operational Status Data"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Operational Status Data",
                data={"error": str(e), "site": site}
            )

class DailyReport(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_id="daily_report",
        operation_summary="Get Daily report Table Data",
        operation_description="Fetches daily report Table Data.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('date', openapi.IN_QUERY, description="Date", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response("Success", ProcessOverviewResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-002"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        date = request.GET.get('date')
        if not site:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id")
        try:
            with Dash002Service() as service:
                data = service.get_daily_report_table_data(site_id=site, date=date)

                return ResponseBuilder.success(
                    data=data,
                    message="Successfully retrieved Daily Report Data"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Daily Report Data",
                data={"error": str(e), "site": site}
            )

class AreaFilter(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="area_filter",
        operation_summary="Get Area Filter",
        operation_description="Fetches Area Filter Data.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
        ],
        responses={
            200: openapi.Response("Success", ProcessOverviewResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-002"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        if not site:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id")
        try:
            with Dash002Service() as service:
                data = service.get_area_filter(site_id=site)

                return ResponseBuilder.success(
                    data=data,
                    message="Successfully retrieved Daily Report Data"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Daily Report Data",
                data={"error": str(e), "site": site}
            )
