from datetime import datetime, timedelta

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from interface.serializers.dash_009_serializer import Dash009ResponseSchema
from infrastructure.services.dash_009 import Dash_009Service


class PumpCategoryFilter(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_pump_categories",
        operation_summary="Get Pump Categories for filter",
        operation_description="Fetches Pump Categories for filters",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
        ],
        responses={
            200: openapi.Response("Success", Dash009ResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-009"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        if not site:
            return ResponseBuilder.success(data="", message="site_id is required")

        try:
            with Dash_009Service() as svc:
                data = svc.get_pump_categories(site)
                return ResponseBuilder.success(data=data, message="Pump categories retrieved successfully")
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Pump Categories",
                data={"error": str(e), "site": site}
            )




class PumpKPISHeatMap(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="pump_kpis_heatmap",
        operation_summary="Get Pump KPIS for Heatmap for a Date Range",
        operation_description="Fetches Pump KPIs Data for the latest available record within the specified date range, for heatmap visualization.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('pump_id', openapi.IN_QUERY, description="Pump id", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('from_date', openapi.IN_QUERY, description="Start Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('to_date', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response("Success", Dash009ResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-009"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        pump_category = request.GET.get('pump_id')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if not site or not pump_category:
            return ResponseBuilder.success(data=[], message="Missing required query params: site_id, pump_id")

        try:
            with Dash_009Service() as svc:
                payload = svc.get_pump_kpis_range(
                    site=site, 
                    pump_category=pump_category, 
                    from_date=from_date,
                    to_date=to_date
                )

                # Extract metadata
                data_availability = payload.get("data_availability_for_given_date", False)
                from_date_used = payload.get("from_date")
                to_date_used = payload.get("to_date")

                # Build response with consistent naming
                data = {
                    "columnData": payload.get("data", []),
                    "data_availability_for_given_date": data_availability,
                    "from_date": from_date_used,
                    "to_date": to_date_used
                }
                
                return ResponseBuilder.success(
                    data=data,
                    message=payload.get("message", "OK")
                )
        except Exception as e:
            return ResponseBuilder.server_error(data=[], message=str(e))


