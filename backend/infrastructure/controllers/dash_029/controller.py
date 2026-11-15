from datetime import datetime, timedelta

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from interface.serializers.dash_028_serializer import Dash028FilterSerializer, OperationalStatusFilterSerializer
from infrastructure.services.dash_028 import Dash_028Service
from infrastructure.services.dash_029 import Dash_029Service



class WeightedROTable(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_RO_Quality_metrics",
        operation_summary="Get Racks Operation Quality Metrics",
        operation_description="Fetches Racks Operation Quality metrics for a given site_id and date.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('date', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('ro_identifier', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False)
        ],
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-029"],
    )
    def get(self, request):
        serializer = Dash028FilterSerializer(data=request.GET)

        # Validate input
        if not serializer.is_valid():
            return ResponseBuilder.error(serializer.errors, [])
        
        validated = serializer.validated_data
        site_id = validated.get("site_id")
        start_time = validated.get("start_time")
        end_time = validated.get("end_time")
        ro_identifier = validated.get("ro_identifier")

        if not site_id:
            return ResponseBuilder.success(data="", message="site_id is required")

        try:
            with Dash_029Service() as svc:
                result = svc.get_weighted_ro_conductivity_heatmap(site_id, ro_identifier, start_time, end_time)
                metadata = result.get("metadata", {})
                return ResponseBuilder.success(
                    data={
                        "data": result.get("data", []),
                        **metadata
                    },
                    message="RO Cards & Graphs for UAQ retrieved successfully" if site_id == "UAQ" else "RO Cards & Graphs retrieved successfully"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Cards & Graphs",
                data={"error": str(e), "site": site_id})
        

class AvgWeightedROTable(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_averaged_table_heatmap",
        operation_summary="Get Racks Operation Quality Metrics",
        operation_description="Fetches Racks Operation Quality metrics for a given site_id and date.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('date', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('ro_identifier', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False)
        ],
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-029"],
    )
    def get(self, request):
        serializer = Dash028FilterSerializer(data=request.GET)

        # Validate input
        if not serializer.is_valid():
            return ResponseBuilder.error(serializer.errors, [])
        
        validated = serializer.validated_data
        site_id = validated.get("site_id")
        start_time = validated.get("start_time")
        end_time = validated.get("end_time")
        ro_identifier = validated.get("ro_identifier")

        if not site_id:
            return ResponseBuilder.success(data="", message="site_id is required")

        try:
            with Dash_029Service() as svc:
                result = svc.get_averaged_ro_conductivity_heatmap(site_id, ro_identifier, start_time, end_time)
                metadata = result.get("metadata", {})
                return ResponseBuilder.success(
                    data={
                        "data": result.get("data", []),
                        **metadata
                    },
                    message="RO Cards & Graphs for UAQ retrieved successfully" if site_id == "UAQ" else "RO Cards & Graphs retrieved successfully"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Cards & Graphs",
                data={"error": str(e), "site": site_id})
        

class ROPowerConsumptionChart(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_RO_Power_Consumption_chart",
        operation_summary="Get RO Power Consumption Chart",
        operation_description="Fetches Power Consumption chart for a given site_id and date.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('date', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('ro_identifier', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False)
        ],
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-029"],
    )
    def get(self, request):
        serializer = Dash028FilterSerializer(data=request.GET)

        # Validate input
        if not serializer.is_valid():
            return ResponseBuilder.error(serializer.errors, [])
        
        validated = serializer.validated_data
        site_id = validated.get("site_id")
        start_time = validated.get("start_time")
        end_time = validated.get("end_time")
        ro_identifier = validated.get("ro_identifier")

        if not site_id:
            return ResponseBuilder.success(data="", message="site_id is required")

        try:
            with Dash_029Service() as svc:
                result = svc.get_ro_power_consumption_metrics(site_id, ro_identifier, start_time, end_time)
                metadata = result.get("metadata", {})
                return ResponseBuilder.success(
                    data={
                        "data": result.get("data", []),
                        **metadata
                    },
                    message="RO Cards & Graphs for UAQ retrieved successfully" if site_id == "UAQ" else "RO Cards & Graphs retrieved successfully"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Cards & Graphs",
                data={"error": str(e), "site": site_id})