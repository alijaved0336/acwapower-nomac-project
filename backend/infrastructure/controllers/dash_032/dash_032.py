from pickle import FALSE

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.dash_032 import Dash032Service
from interface.schemas.dash_002_schema import ProcessOverviewResponseSchema


class NormalizedData(APIView):
    
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="normalized-data-pass-1",
        operation_summary="Get Normalized Data Pass 1",
        operation_description="Fetches Normalized Data Pass 1.",
        manual_parameters=[
            openapi.Parameter('site_id', openapi.IN_QUERY, description="Site", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('from_date', openapi.IN_QUERY, description="From date", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('to_date', openapi.IN_QUERY, description="To date", type=openapi.TYPE_STRING,
                              required=False),
            openapi.Parameter('pass', openapi.IN_QUERY, description="Pass", type=openapi.TYPE_STRING,
                              required=False),
        ],
        responses={
            200: openapi.Response("Success", ProcessOverviewResponseSchema),
            400: openapi.Response("Bad Request", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
        },
        tags=["Dash-032"],
    )
    def get(self, request):

        site = request.GET.get('site_id', None)
        from_date = request.GET.get('from_date', None)
        to_date = request.GET.get('to_date', None)
        norm_pass = request.GET.get('pass', None)

        if not site:
            return ResponseBuilder.success(data="", message="Missing required query params: site_id")
        try:
            with Dash032Service() as service:
                data = service.get_normalized_data_pass_1(site_id=site, from_date=from_date, to_date=to_date, norm_pass=norm_pass)

                return ResponseBuilder.success(
                    data=data,
                    message=f"Successfully retrieved Normalized {norm_pass} data."
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message=f"Failed to retrieved Normalized {norm_pass} data",
                data={"error": str(e), "site": site}
            )



class StreamFilter(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_id="stream-filter",
        operation_summary="Get Stream Filter",
        operation_description="Fetches Stream Filter.",
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
        tags=["Dash-032"],
    )
    def get(self, request):
        site = request.GET.get('site_id', None)
        try:
            with Dash032Service() as service:
                data = service.stream_filter(site_id=site)

                return ResponseBuilder.success(
                    data=data,
                    message="Successfully retrieved Streams."
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve Streams",
                data={"error": str(e), "site": site}
            )