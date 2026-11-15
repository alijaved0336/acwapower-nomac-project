from datetime import datetime, timedelta

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from interface.serializers.dash_028_serializer import Dash028FilterSerializer, OperationalStatusFilterSerializer
from infrastructure.services.dash_028 import Dash_028Service



class ROQuality(APIView):
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
        tags=["Dash-028"],
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
            with Dash_028Service() as svc:
                if site_id == "UAQ":
                    data = svc.UAQ_get_performance_RO_overall(site_id, ro_identifier, start_time, end_time)
                    return ResponseBuilder.success(data=data, message="RO Cards & Graphs for UAQ retrieved successfully")
                else:
                    data = svc.get_rack_performance_RO_overall(site_id, ro_identifier, start_time, end_time)
                    return ResponseBuilder.success(data=data, message="RO Cards & Graphs retrieved successfully")
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Cards & Graphs",
                data={"error": str(e), "site": site_id}
            )

class ROQualityRacksTable(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_RO_Quality_Racks_Table",
        operation_summary="Get Racks Operation Quality Racks Table",
        operation_description="Fetches Racks Operation Rack performance metrics for a given site_id and date.",
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
        tags=["Dash-028"],
    )
    def get(self, request):

        serializer = Dash028FilterSerializer(data=request.GET)

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
            with Dash_028Service() as svc:
                if site_id == "UAQ":
                    data = svc.UAQ_get_performance_RO_table(site_id, ro_identifier, start_time, end_time)
                    return ResponseBuilder.success(data=data, message="RO Quality Table for UAQ retrieved successfully")
                else:
                    data = svc.get_rack_performance_RO_table(site_id, ro_identifier, start_time, end_time)
                    return ResponseBuilder.success(data=data, message="RO Quality Table retrieved successfully")
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve RO Quality Table",
                data={"error": str(e), "site": site_id}
            )


class ROQualityRacksOperationalStatus(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="get_RO_Quality_Racks_Operational_Status",
        operation_summary="Get Racks Operation Quality Racks Operational Status",
        operation_description="Fetches Racks Operation Rack Operational Status for a given site_id and date range.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('ro_identifier', openapi.IN_QUERY, description="End Date (ISO 8601)", type=openapi.TYPE_STRING, required=False)
        ],
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-028"],
    )
    def get(self, request):
        serializer = OperationalStatusFilterSerializer(data=request.GET)

        if not serializer.is_valid():
            return ResponseBuilder.error(serializer.errors, [])

        validated = serializer.validated_data
        site_id = validated.get("site_id")
        start_time = validated.get("start_date")
        end_time = validated.get("end_date")
        ro_identifier = validated.get("ro_identifier")

        if not site_id:
            return ResponseBuilder.success(data="", message="site_id is required")

        try:
            with Dash_028Service() as svc:
                if site_id == "UAQ":
                    data = svc.UAQ_get_rack_performance_RO_operational_status(site_id, ro_identifier, start_time, end_time)
                    return ResponseBuilder.success(data=data, message="RO Operational Status for UAQ retrieved successfully")
                else:
                    data = svc.get_rack_performance_RO_operational_status(site_id, ro_identifier, start_time, end_time)
                    return ResponseBuilder.success(data=data, message="RO Operational Status retrieved successfully")
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve RO Operational Status",
                data={"error": str(e), "site": site_id}
            )
