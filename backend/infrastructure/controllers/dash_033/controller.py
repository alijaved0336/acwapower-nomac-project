from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import logging

from infrastructure.applevel.responseBuilder import ResponseBuilder
from interface.serializers.rack_serializers import RackFilterSerializer
from infrastructure.services.dash_033.main_service import Dash_033OptimizedService_CH
logger = logging.getLogger(__name__)


class RackRuntimeListView(APIView):
    """
    Rack Runtime List View with robust column handling, diagnostic support, and rack filtering.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()
    
    @swagger_auto_schema(
        operation_id="dash_033_list_rack_runtime",
        operation_summary="List rack runtime percentages",
        operation_description="Retrieve runtime percentages for all racks with robust column handling, diagnostics, and rack filtering",
        manual_parameters=[
            openapi.Parameter('site_name', openapi.IN_QUERY, description="Site name identifier", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('racks', openapi.IN_QUERY, description="Comma-separated rack IDs (e.g., '1,2,3')", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End Date and Time", type=openapi.TYPE_STRING, required=False)
        ],
        responses={
            200: openapi.Response("Success", examples={
                "application/json": {
                    "rackruntimestoptime": {
                        "G1": {
                            "x": [{"name": "Racks", "data": ["1", "2", "3"]}],
                            "y": [
                                {"name": "Runtime %", "data": ["75.50", "80.25", "65.75"]},
                                {"name": "Stoptime %", "data": ["24.50", "19.75", "34.25"]}
                            ]
                        }
                    }
                }
            }),
            400: openapi.Response("Bad Request", examples={
                "application/json": {"error": "Invalid parameters"}
            })
        },
        tags=["Dash-033"],
    )
    def get(self, request):
        try:
            # Use serializer to validate and process parameters
            serializer = RackFilterSerializer(data=request.GET)
            if not serializer.is_valid():
                return ResponseBuilder.error(
                    message="Invalid parameters", 
                    data={"errors": serializer.errors}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            user = getattr(request, 'jwt_user', None)

            logger.info(f"Processing runtime request for site: {validated_data.get('site_name')}, racks: {validated_data.get('racks')}")
            
            racks_data = self.service.get_racks_runtime_only(
                site_name=validated_data.get('site_name'),
                user=user,
                start_time=validated_data.get('start_date'),
                end_time=validated_data.get('end_date'),
                racks=validated_data.get('racks')
            )
            
            if "diagnostic_info" in racks_data:
                logger.warning(f"Runtime data diagnostic: {racks_data['diagnostic_info']['message']}")
                return ResponseBuilder.success(
                    data={
                        "message": "Data structure diagnostic information",
                        "diagnostic": racks_data["diagnostic_info"],
                        "rackruntimestoptime": {}
                    }, 
                    message="Runtime data retrieved with diagnostics"
                )
            
            return ResponseBuilder.success(
                data=racks_data, 
                message="Racks Runtime data retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in RackRuntimeListView: {e}")
            return ResponseBuilder.error(
                message="Failed to retrieve racks runtime data", 
                data={"error": str(e)}, 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RackCIPValidListView(APIView):
    """
    Rack CIP Valid List View with robust column handling, diagnostic support, and rack filtering.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()
    
    @swagger_auto_schema(
        operation_id="dash_033_list_cip",
        operation_summary="List rack CIP validated information",
        operation_description="Retrieve validated CIP information with robust column handling, diagnostics, and rack filtering",
        manual_parameters=[
            openapi.Parameter('site_name', openapi.IN_QUERY, description="Site Name/ID", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('racks', openapi.IN_QUERY, description="Comma-separated rack IDs (e.g., '1,2,3')", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter("page", openapi.IN_QUERY, description="Page number (default: 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("limit", openapi.IN_QUERY, description="Items per page (default: 25)", type=openapi.TYPE_INTEGER),            
        ],
        responses={
            200: openapi.Response("Success", examples={
                "application/json": {
                    "racks": {
                        "items": [
                            {
                                "Start_Time": "2025-08-20 10:00:00",
                                "End_Time": "2025-08-20 12:00:00", 
                                "Train": "Train_1",
                                "Duration_Hours": 2.5,
                                "Mode_Validated": "Validated CIP"
                            }
                        ],
                        "total": 100,
                        "page": 1,
                        "limit": 25,
                        "pages": 4
                    }
                }
            }),
            400: openapi.Response("Bad Request", examples={
                "application/json": {"error": "Invalid parameters"}
            })
        },
        tags=["Dash-033"],
    )
    def get(self, request):
        try:
            # Use serializer to validate and process parameters
            serializer = RackFilterSerializer(data=request.GET)
            if not serializer.is_valid():
                return ResponseBuilder.error(
                    message="Invalid parameters", 
                    data={"errors": serializer.errors}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            user = getattr(request, 'jwt_user', None)
            
            logger.info(f"Processing CIP validated request for site: {validated_data.get('site_name')}, racks: {validated_data.get('racks')}")
            
            # Use robust service
            racks_data = self.service.get_cip_validated_info(
                site_name=validated_data.get('site_name'),
                user=user, 
                start_time=validated_data.get('start_date'), 
                end_time=validated_data.get('end_date'), 
                page=validated_data.get('page', 1), 
                limit=validated_data.get('limit', 25),
                racks=validated_data.get('racks')
            )

            if "diagnostic_info" in racks_data:
                logger.warning(f"CIP validated diagnostic: {racks_data['diagnostic_info']['message']}")
                return ResponseBuilder.success(
                    data={
                        "racks": {
                            **racks_data,
                            "diagnostic": racks_data["diagnostic_info"]
                        }
                    }, 
                    message="CIP validated data retrieved with diagnostics"
                )
            
            return ResponseBuilder.success(
                data={"racks": racks_data}, 
                message="Racks CIP validated data retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in RackCIPValidListView: {e}")
            return ResponseBuilder.error(
                message="Failed to retrieve racks CIP validated data", 
                data={"error": str(e)}, 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RackCIPFlushingListView(APIView):
    """
    Rack CIP Flushing List View - WORKING VERSION with robust column handling and rack filtering.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()
    
    @swagger_auto_schema(
        operation_id="dash_033_list_cip_flushing_mode",
        operation_summary="List rack CIP in flushing mode",
        operation_description="Retrieve CIP flushing mode data with robust column handling, diagnostics, and rack filtering",
        manual_parameters=[
            openapi.Parameter('site_name', openapi.IN_QUERY, description="Site Name/ID", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('racks', openapi.IN_QUERY, description="Comma-separated rack IDs (e.g., '1,2,3')", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter("page", openapi.IN_QUERY, description="Page number (default: 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("limit", openapi.IN_QUERY, description="Items per page (default: 25)", type=openapi.TYPE_INTEGER),            
        ],
        responses={
            200: openapi.Response("Success", examples={
                "application/json": {
                    "racks": {
                        "items": [
                            {
                                "Start_Time": "2025-08-20 08:00:00",
                                "End_Time": "2025-08-20 10:00:00",
                                "Train": "Train_2", 
                                "Duration_Hours": 2.0,
                                "Mode_Validated": "Flushing"
                            }
                        ],
                        "total": 50,
                        "page": 1,
                        "limit": 25,
                        "pages": 2
                    }
                }
            }),
            400: openapi.Response("Bad Request", examples={
                "application/json": {"error": "Invalid parameters"}
            })
        },
        tags=["Dash-033"],
    )
    def get(self, request):
        try:
            # Use serializer to validate and process parameters
            serializer = RackFilterSerializer(data=request.GET)
            if not serializer.is_valid():
                return ResponseBuilder.error(
                    message="Invalid parameters", 
                    data={"errors": serializer.errors}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            user = getattr(request, 'jwt_user', None)
            
            logger.info(f"Processing CIP flushing request for site: {validated_data.get('site_name')}, racks: {validated_data.get('racks')}")
            
            # Use robust service (this is the working version)
            racks_data = self.service.get_cip_flushing_info(
                site_name=validated_data.get('site_name'),
                user=user, 
                start_time=validated_data.get('start_date'), 
                end_time=validated_data.get('end_date'), 
                page=validated_data.get('page', 1), 
                limit=validated_data.get('limit', 25),
                racks=validated_data.get('racks')
            )

            if "diagnostic_info" in racks_data:
                logger.warning(f"CIP flushing diagnostic: {racks_data['diagnostic_info']['message']}")
                return ResponseBuilder.success(
                    data={
                        "racks": {
                            **racks_data,
                            "diagnostic": racks_data["diagnostic_info"]
                        }
                    }, 
                    message="CIP flushing data retrieved with diagnostics"
                )
            
            return ResponseBuilder.success(
                data={"racks": racks_data}, 
                message="Racks CIP flushing data retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in RackCIPFlushingListView: {e}")
            return ResponseBuilder.error(
                message="Failed to retrieve racks CIP flushing data", 
                data={"error": str(e)}, 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RackCIPGraphView(APIView):
    """
    Rack CIP Graph View with robust column handling, diagnostic support, and rack filtering.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()
    
    @swagger_auto_schema(
        operation_id="dash_033_list_cip_summary",
        operation_summary="List rack Last CIP and DaysSinceCIP",
        operation_description="Retrieve CIP summary with robust column handling, diagnostics, and rack filtering",
        manual_parameters=[
            openapi.Parameter('site_name', openapi.IN_QUERY, description="Site Name/ID", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('racks', openapi.IN_QUERY, description="Comma-separated rack IDs (e.g., '1,2,3')", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End Date and Time", type=openapi.TYPE_STRING, required=False)                             
        ],
        responses={
            200: openapi.Response("Success", examples={
                "application/json": {
                    "racks": {
                        "rackcipstatus": {
                            "G1": {
                                "x": [{"name": "Days Since Last CIP", "data": [130, 63, 45]}],
                                "y": [{"name": "Train", "data": ["Train_1", "Train_2", "Train_3"]}]
                            }
                        }
                    }
                }
            }),
            400: openapi.Response("Bad Request", examples={
                "application/json": {"error": "Invalid parameters"}
            })
        },
        tags=["Dash-033"],
    )
    def get(self, request):
        try:
            # Use serializer to validate and process parameters
            serializer = RackFilterSerializer(data=request.GET)
            if not serializer.is_valid():
                return ResponseBuilder.error(
                    message="Invalid parameters", 
                    data={"errors": serializer.errors}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            user = getattr(request, 'jwt_user', None)
            
            logger.info(f"Processing CIP summary request for site: {validated_data.get('site_name')}, racks: {validated_data.get('racks')}")

            racks_data = self.service.get_cip_summary(
                site_name=validated_data.get('site_name'),
                user=user, 
                start_time=validated_data.get('start_date'), 
                end_time=validated_data.get('end_date'),
                racks=validated_data.get('racks')
            )

            if "diagnostic_info" in racks_data:
                logger.warning(f"CIP summary diagnostic: {racks_data['diagnostic_info']['message']}")
                return ResponseBuilder.success(
                    data={
                        "racks": {
                            "diagnostic": racks_data["diagnostic_info"],
                            "rackcipstatus": {}
                        }
                    }, 
                    message="CIP summary retrieved with diagnostics"
                )
            
            return ResponseBuilder.success(
                data={"racks": racks_data}, 
                message="Racks CIP summary retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in RackCIPGraphView: {e}")
            return ResponseBuilder.error(
                message="Failed to retrieve racks CIP summary", 
                data={"error": str(e)}, 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RackMembraneGraphView(APIView):
    """
    Rack Membrane Graph View with robust column handling, diagnostic support, and rack filtering.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()
    
    @swagger_auto_schema(
        operation_id="dash_033_list_membrance_graph_summary",
        operation_summary="List rack and Membrane details",
        operation_description="Retrieve membrane analytics with robust column handling, diagnostics, and rack filtering",
        manual_parameters=[
            openapi.Parameter('site_name', openapi.IN_QUERY, description="Site Name/ID", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('racks', openapi.IN_QUERY, description="Comma-separated rack IDs (e.g., '1,2,3')", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('col_pre', openapi.IN_QUERY, description="Column Pre (First Column)", type=openapi.TYPE_STRING, required=False, default="AVG_Salt_Passage_Normalized_Pre"),
            openapi.Parameter('col_post', openapi.IN_QUERY, description="Column Post (Second Column)", type=openapi.TYPE_STRING, required=False, default="AVG_Salt_Passage_Normalized_Post"),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End Date and Time", type=openapi.TYPE_STRING, required=False)                                                      
        ],
        responses={
            200: openapi.Response("Success", examples={
                "application/json": {
                    "racks": {
                        "rackmembrance": {
                            "G1": {
                                "x": [{"name": "Train", "data": ["Train_1", "Train_2"]}],
                                "y": [
                                    {
                                        "name": "AVG_Salt_Passage_Normalized_Pre",
                                        "data": {
                                            "value": ["85.50", "78.25"],
                                            "percentage": ["52.30", "48.75"]
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }),
            400: openapi.Response("Bad Request", examples={
                "application/json": {"error": "Invalid parameters"}
            })
        },
        tags=["Dash-033"],
    )
    def get(self, request):
        try:
            # Use serializer to validate and process parameters
            serializer = RackFilterSerializer(data=request.GET)
            if not serializer.is_valid():
                return ResponseBuilder.error(
                    message="Invalid parameters", 
                    data={"errors": serializer.errors}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            user = getattr(request, 'jwt_user', None)
            
            logger.info(f"Processing membrane graph request for site: {validated_data.get('site_name')}, racks: {validated_data.get('racks')}")
            
            racks_data = self.service.get_membrane_graph_averages(
                site_name=validated_data.get('site_name'),
                user=user, 
                col_pre=validated_data.get('col_pre', 'AVG_Salt_Passage_Normalized_Pre'), 
                col_post=validated_data.get('col_post', 'AVG_Salt_Passage_Normalized_Post'), 
                start_time=validated_data.get('start_date'), 
                end_time=validated_data.get('end_date'),
                racks=validated_data.get('racks')
            )

            if "diagnostic_info" in racks_data:
                logger.warning(f"Membrane graph diagnostic: {racks_data['diagnostic_info']['message']}")
                return ResponseBuilder.success(
                    data={
                        "racks": {
                            "diagnostic": racks_data["diagnostic_info"],
                            "rackmembrance": {}
                        }
                    }, 
                    message="Membrane graph data retrieved with diagnostics"
                )
            
            return ResponseBuilder.success(
                data={"racks": racks_data}, 
                message="Racks membrane graph data retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in RackMembraneGraphView: {e}")
            return ResponseBuilder.error(
                message="Failed to retrieve racks membrane data", 
                data={"error": str(e)}, 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RackMembraneTableView(APIView):
    """
    Rack Membrane Table View with robust column handling, diagnostic support, and rack filtering.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()
    
    @swagger_auto_schema(
        operation_id="dash_033_list_membrane_table",
        operation_summary="List rack and Membrane details",
        operation_description="Retrieve paginated membrane data with robust column handling, diagnostics, and rack filtering",
        manual_parameters=[
            openapi.Parameter('site_name', openapi.IN_QUERY, description="Site Name/ID", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('racks', openapi.IN_QUERY, description="Comma-separated rack IDs (e.g., '1,2,3')", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('modes', openapi.IN_QUERY, description="Comma-separated mode values (e.g., 'Conservation,Major Maintenance,Minor Maintenance')", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter("page", openapi.IN_QUERY, description="Page number (default: 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("limit", openapi.IN_QUERY, description="Items per page (default: 25)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End Date and Time", type=openapi.TYPE_STRING, required=False)              
        ],
        responses={
            200: openapi.Response("Success", examples={
                "application/json": {
                    "membrane": {
                        "items": {
                            "Train": {"name": "Train", "data": ["Train_1", "Train_2"]},
                            "Start_Time": {"name": "Start_Time", "data": ["2025-08-20 10:00:00", "2025-08-20 11:00:00"]}
                        },
                        "total": 150,
                        "page": 1,
                        "limit": 25,
                        "pages": 6
                    }
                }
            }),
            400: openapi.Response("Bad Request", examples={
                "application/json": {"error": "Invalid parameters"}
            })
        },
        tags=["Dash-033"],
    )
    def get(self, request):
        try:
            # Use serializer to validate and process parameters
            serializer = RackFilterSerializer(data=request.GET)
            if not serializer.is_valid():
                return ResponseBuilder.error(
                    message="Invalid parameters", 
                    data={"errors": serializer.errors}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            user = getattr(request, 'jwt_user', None)
            
            logger.info(f"Processing membrane table request for site: {validated_data.get('site_name')}, racks: {validated_data.get('racks')}, modes: {validated_data.get('modes')}")

            racks_data = self.service.get_membrane_info(
                site_name=validated_data.get('site_name'),
                user=user, 
                page=validated_data.get('page', 1), 
                limit=validated_data.get('limit', 25), 
                start_time=validated_data.get('start_date'), 
                end_time=validated_data.get('end_date'),
                racks=validated_data.get('racks'),
                modes=validated_data.get('modes')
            )

            if "diagnostic_info" in racks_data:
                logger.warning(f"Membrane table diagnostic: {racks_data.get('diagnostic_info', {}).get('message', 'Unknown diagnostic')}")
                return ResponseBuilder.success(
                    data={
                        "membrane": {
                            **racks_data,
                            "diagnostic": racks_data.get("diagnostic_info", {})
                        }
                    }, 
                    message="Membrane table data retrieved with diagnostics"
                )
            
            return ResponseBuilder.success(
                data={"membrane": racks_data}, 
                message="Racks membrane table data retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in RackMembraneTableView: {e}")
            return ResponseBuilder.error(
                message="Failed to retrieve racks membrane table data", 
                data={"error": str(e)}, 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RackMembranePercentageGraphView(APIView):
    """
    Rack Membrane Percentage Graph View with robust column handling, diagnostic support, and rack filtering.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()
    
    @swagger_auto_schema(
        operation_id="dash_033_list_membrance_graph_percentage_columns_summary",
        operation_summary="List rack and Membrane details for percentage columns",
        operation_description="Retrieve membrane percentage analytics with robust column handling, diagnostics, and rack filtering",
        manual_parameters=[
            openapi.Parameter('site_name', openapi.IN_QUERY, description="Site Name/ID", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('racks', openapi.IN_QUERY, description="Comma-separated rack IDs (e.g., '1,2,3')", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start Date and Time", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End Date and Time", type=openapi.TYPE_STRING, required=False)                                                                                       
        ],
        responses={
            200: openapi.Response("Success", examples={
                "application/json": {
                    "racks": {
                        "rackmembrance": {
                            "G1": {
                                "x": [{"name": "Train", "data": ["Train_1", "Train_2"]}],
                                "y": [
                                    {
                                        "name": "Diff_Salt_Passage_%",
                                        "data": ["12.50", "8.75"]
                                    }
                                ]
                            }
                        }
                    }
                }
            }),
            400: openapi.Response("Bad Request", examples={
                "application/json": {"error": "Invalid parameters"}
            })
        },
        tags=["Dash-033"],
    )
    def get(self, request):
        try:
            # Use serializer to validate and process parameters
            serializer = RackFilterSerializer(data=request.GET)
            if not serializer.is_valid():
                return ResponseBuilder.error(
                    message="Invalid parameters", 
                    data={"errors": serializer.errors}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            user = getattr(request, 'jwt_user', None)
            
            logger.info(f"Processing membrane percentage graph request for site: {validated_data.get('site_name')}, racks: {validated_data.get('racks')}")

            racks_data = self.service.get_membrane_graph_percentages(
                site_name=validated_data.get('site_name'),
                user=user,
                start_time=validated_data.get('start_date'),
                end_time=validated_data.get('end_date'),
                racks=validated_data.get('racks')
            )

            if "diagnostic_info" in racks_data:
                logger.warning(f"Membrane percentage diagnostic: {racks_data['diagnostic_info']['message']}")
                return ResponseBuilder.success(
                    data={
                        "racks": {
                            "diagnostic": racks_data["diagnostic_info"],
                            "rackmembrance": {}
                        }
                    }, 
                    message="Membrane percentage data retrieved with diagnostics"
                )
            
            return ResponseBuilder.success(
                data={"racks": racks_data}, 
                message="Racks membrane percentage data retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in RackMembranePercentageGraphView: {e}")
            return ResponseBuilder.error(
                message="Failed to retrieve racks membrane percentage data", 
                data={"error": str(e)}, 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

"""
Columns List Handler - Handles Azure Data Lake columns listing operations for specific tables
Enhanced with filtering options to reduce unnecessary data in responses.
"""

class ColumnsListView(APIView):
    """
    API View for listing columns in a specific table with enhanced filtering options.
    Supports various query parameters to customize the response and reduce unnecessary data.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()

    @swagger_auto_schema(
        operation_id="get_columns_for_table",
        operation_summary="Get columns for a specific table",
        operation_description="Retrieve column information for a specific table with optional filtering by date range, racks, and other parameters.",
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_PATH,
                description="Site identifier",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "from_date",
                openapi.IN_QUERY,
                description="Start date for filtering (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "to_date",
                openapi.IN_QUERY,
                description="End date for filtering (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "racks",
                openapi.IN_QUERY,
                description="Comma-separated rack IDs (e.g., '18,19,20')",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "include_samples",
                openapi.IN_QUERY,
                description="Include sample data in response",
                type=openapi.TYPE_BOOLEAN,
                required=False,
                default=True,
            ),
            openapi.Parameter(
                "exclude_null_calculated",
                openapi.IN_QUERY,
                description="Exclude columns with null/calculated values",
                type=openapi.TYPE_BOOLEAN,
                required=False,
                default=False,
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
                                "charts": openapi.Schema(type=openapi.TYPE_OBJECT),
                                "date_filter": openapi.Schema(type=openapi.TYPE_OBJECT),
                                "method_used": openapi.Schema(type=openapi.TYPE_STRING),
                                "performance": openapi.Schema(type=openapi.TYPE_OBJECT)
                            }
                        )
                    }
                )
            ),
            500: openapi.Response(
                "Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True)
                    }
                )
            )
        },
        tags=["Dash-033"],
    )
    def get(self, request, site_id):
        """
        GET /columns/{site_id}/
        Returns column information with filtering options including racks.
        """
        try:
            logger.info(f"Processing columns list request for site {site_id}")

            # Get query parameters
            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')
            include_samples = request.GET.get('include_samples', 'true').lower() == 'true'
            exclude_null_calculated = request.GET.get('exclude_null_calculated', 'false').lower() == 'true'
            
            # Parse racks parameter
            racks = None
            racks_param = request.GET.get('racks')
            if racks_param:
                # Split by comma and strip whitespace
                racks = [rack.strip() for rack in racks_param.split(',') if rack.strip()]
                logger.info(f"Parsed racks filter: {racks}")
            
            user = getattr(request, 'jwt_user', None)
            
            # Get column data using the enhanced service with racks filter
            columns_data = self.service.get_columns_metadata(
                site_name=site_id,
                user=user,
                from_date=from_date,
                to_date=to_date,
                include_samples=include_samples,
                exclude_calculated=exclude_null_calculated,
                exclude_null=exclude_null_calculated,
                include_performance=True,
                racks=racks  # Pass racks filter
            )

            
            logger.info(f"Successfully retrieved columns for site {site_id} with racks filter: {racks}")
            
            return ResponseBuilder.success(
                data=columns_data,
                message=f"Columns retrieved successfully for site {site_id}"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving columns for site {site_id}: {str(e)}")
            return ResponseBuilder.error(
                message=f"Failed to retrieve columns for site {site_id}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RacksListView(APIView):
    """
    API View for listing Train column data in a specific table with enhanced filtering options.
    """
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.service = Dash_033OptimizedService_CH()

    @swagger_auto_schema(
        operation_id="get_train_column_for_table",
        operation_summary="Get train column for a specific table",
        operation_description="Retrieve train column information for a specific table",
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_PATH,
                description="Site identifier",
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
                                "racks": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                                ),
                                "count": openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        )
                    }
                )
            ),
            500: openapi.Response(
                "Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True)
                    }
                )
            )
        },
        tags=["Dash-033"],
    )
    def get(self, request, site_id):
        """
        GET /racks/{site_id}/
        Returns unique Train column data.
        """
        try:
            logger.info(f"Processing racks list request for site {site_id}")
            
            user = getattr(request, 'jwt_user', None)
            
            # Get racks data using the enhanced service
            racks_data = self.service.get_racks_data(
                site_name=site_id,
                user=user
            )
            
            logger.info(f"Successfully retrieved racks for site {site_id}")
            
            return ResponseBuilder.success(
                data=racks_data,
                message=f"Racks retrieved successfully for site {site_id}"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving racks for site {site_id}: {str(e)}")
            return ResponseBuilder.error(
                message=f"Failed to retrieve racks for site {site_id}: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )