from datetime import datetime, timedelta

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from interface.schemas.dash_005_schemas import Dash005ResponseSchema
from infrastructure.services.dash_005 import Dash_005Service


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
            200: openapi.Response("Success", Dash005ResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-005"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        if not site:
            return ResponseBuilder.success(data="", message="site_id is required")

        try:
            with Dash_005Service() as svc:
                data = svc.get_pump_categories(site)
                return ResponseBuilder.success(data=data, message="Pump categories retrieved successfully")
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Pump Categories",
                data={"error": str(e), "site": site}
            )


class Card(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="cards_data",
        operation_summary="Get Cards Data with 24-hour Tendency",
        operation_description="Fetches Cards Data for exact datetime (if provided) or latest available. Includes 24-hour tendency calculation for power_kw and load_kw_m3 using weighted averages.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('date', openapi.IN_QUERY,
                              description="Exact DateTime (ISO format: 2025-09-02T12:00:00). If omitted, latest timestamp is used.",
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('pump_id', openapi.IN_QUERY, description="Pump id", type=openapi.TYPE_STRING,
                              required=False),
        ],
        responses={
            200: openapi.Response("Success", Dash005ResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-005"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        pump = request.GET.get('pump_id')
        date_str = request.GET.get('date')

        if not site or not pump:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id, pump_id")

        try:
            with Dash_005Service() as svc:
                payload = svc.get_cards_averages(site=site, pump_category=pump, date_str=date_str)
                data = payload.get("data")
                tendency = payload.get("tendency")
                final_payload = {"cards": data, "tendency": tendency}

                # Return complete payload including tendency
                return ResponseBuilder.success(
                    data=final_payload,
                     # Add tendency to response
                    message=payload["message"]
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Cards",
                data={"error": str(e), "site": site}
            )

class PumpKPIS(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="pump_kpis",
        operation_summary="Get Pump KPIS",
        operation_description="Fetches Pump KPIs Data",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('date', openapi.IN_QUERY, description="Date", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('pump_id', openapi.IN_QUERY, description="Pump id", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response("Success", Dash005ResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-005"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        pump_category = request.GET.get('pump_id')
        date_str = request.GET.get('date')

        if not site or not pump_category:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id, pump_id")

        try:
            with Dash_005Service() as svc:
                payload = svc.get_pump_kpis(site=site, pump_category=pump_category, date_str=date_str)
                return ResponseBuilder.success(data=payload, message=payload.get("message", "OK"))
        except Exception as e:
            return ResponseBuilder.server_error(data="", message=str(e))


class ActionsOverview(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_actions_overview",
        operation_summary="Pump start/stop transitions or full status records",
        operation_description=(
            "**No pumps selected**: Returns only START and STOP transitions (status changes) for ALL pumps "
            "within the date range. Shows when each pump started running and when it stopped. "
            "If no date range provided, uses trailing 24 hours from latest timestamp.\n\n"
            "**Specific pumps selected**: Returns ALL status records for those pumps within the provided "
            "24-hour window. If no window provided, auto-detects latest day and returns last 24h.\n\n"
            "This approach reduces data volume when viewing all pumps by showing only meaningful state changes."
        ),
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site (e.g., Rabigh3)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('pump_id', openapi.IN_QUERY, description="Pump category key from mapping", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('from_date', openapi.IN_QUERY, description="Start Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('to_date', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('pumps', openapi.IN_QUERY, description="Comma-separated pump names to filter (returns all records for these pumps)", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            200: openapi.Response("Success", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "data": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "mode": openapi.Schema(type=openapi.TYPE_STRING, description="Query mode: all_pumps_transitions_* or selected_pumps_*"),
                            "records": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "pump": openapi.Schema(type=openapi.TYPE_STRING),
                                        "statuses": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    "status": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "timestamp": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "modified": openapi.Schema(type=openapi.TYPE_BOOLEAN)
                                                }
                                            )
                                        )
                                    }
                                )
                            )
                        }
                    ),
                    "message": openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-005"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        category = request.GET.get('pump_id')
        pumps_str = request.GET.get('pumps')
        start_dt = request.GET.get('from_date')
        end_dt = request.GET.get('to_date')

        if not site or not category:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id, pump_id")

        selected_pumps = []
        if pumps_str:
            selected_pumps = [p.strip() for p in pumps_str.split(",") if p.strip()]

        try:
            with Dash_005Service() as svc:
                payload = svc.get_actions_overview(
                    site=site,
                    pump_category=category,
                    from_date=start_dt,
                    to_date=end_dt,
                    selected_pumps=selected_pumps
                )
                return ResponseBuilder.success(data=payload["data"], message=payload["message"])
        except Exception as e:
            return ResponseBuilder.server_error(data="", message=str(e))

class PumpFilter(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_unique_pumps_for_category",
        operation_summary="Get unique Pump names for a pump category",
        operation_description=(
            "Given site_id and pump_id (category), resolve the underlying table and return the DISTINCT list of Pump values. "
            "Pump names are cleaned (underscores → spaces)."
        ),
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site (e.g., Rabigh3)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('pump_id', openapi.IN_QUERY, description="Pump category key from mapping", type=openapi.TYPE_STRING, required=True),
        ],
        tags=["Dash-005"],
    )
    def get(self, request):
        site = request.GET.get('site_id')
        category = request.GET.get('pump_id')

        if not site or not category:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id, pump_id")

        try:
            with Dash_005Service() as svc:
                payload = svc.get_unique_pumps(site=site, pump_category=category)
                return ResponseBuilder.success(data=payload, message="Successfully fetched unique pumps for the category")
        except Exception as e:
            return ResponseBuilder.server_error(data="", message=str(e))
