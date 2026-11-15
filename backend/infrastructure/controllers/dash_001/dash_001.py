from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.dash_001 import Dash_001Service
from interface.schemas.dash_001_schemas import (clusters_response_schema,
                                                error_response_schema,
                                                groups_response_schema,
                                                legacy_response_schema,
                                                mapdata_response_schema,
                                                plants_response_schema)


class PlantListView(APIView):
    @swagger_auto_schema(
        operation_id="dash_list_plants_by_cluster",
        operation_summary="List plants by cluster",
        operation_description="Retrieve all plants belonging to a specific cluster",
        manual_parameters=[
            openapi.Parameter(
                "cluster",
                openapi.IN_QUERY,
                description="Cluster name",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                "Success",
                plants_response_schema,
                examples={"application/json": {"plants": ["Plant-A", "Plant-B"]}},
            ),
            400: openapi.Response(
                "Bad Request",
                error_response_schema,
                examples={
                    "application/json": {"error": "Cluster parameter is required"}
                },
            ),
        },
        tags=["Common"],
    )
    def get(self, request):
        cluster = request.GET.get("cluster", None)

        # Extract user from JWT (added by middleware)
        user = getattr(request, "jwt_user", None)
        if not user:
            return ResponseBuilder.error(
                message="Authentication required",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Get user's role_id
        role_id = user.get("role_id")

        if not cluster:
            return ResponseBuilder.error(
                message="Cluster parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with Dash_001Service() as service:
                plants = service.get_plants_by_cluster_for_role(cluster, role_id)
                return ResponseBuilder.success(
                    data={"plants": plants}, message="Plants retrieved successfully"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve plants", data={"error": str(e)}
            )


class ClusterListView(APIView):
    @swagger_auto_schema(
        operation_id="dash_list_all_clusters",
        operation_summary="List all clusters",
        operation_description="Retrieve all available clusters in the system",
        responses={
            200: openapi.Response(
                "Success",
                clusters_response_schema,
                examples={
                    "application/json": {"clusters": ["North", "South", "East", "West"]}
                },
            ),
            500: openapi.Response(
                "Internal Server Error",
                error_response_schema,
                examples={"application/json": {"error": "Database connection failed"}},
            ),
        },
        tags=["Common"],
    )
    def get(self, request):
        try:
            # Extract user from JWT (added by middleware)
            user = getattr(request, "jwt_user", None)
            if not user:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            # Get user's role_id
            role_id = user.get("role_id")

            with Dash_001Service() as service:
                # Use role-based filtering
                clusters = service.get_clusters_for_role(role_id)

                # Determine appropriate message
                if not role_id:
                    message = "User has no role assigned"
                elif not clusters:
                    message = "No clusters assigned to your role"
                else:
                    message = "Clusters retrieved successfully"

                return ResponseBuilder.success(
                    data={"clusters": clusters}, message=message
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve clusters", data={"error": str(e)}
            )


class ClusterSitesListView(APIView):
    @swagger_auto_schema(
        operation_id="dash_list_all_clusters_sites",
        operation_summary="List all clusters with sites",
        operation_description="Retrieve all available clusters in the system",
        responses={
            200: openapi.Response(
                "Success",
                clusters_response_schema,
                examples={
                    "application/json": {"clusters": ["North", "South", "East", "West"]}
                },
            ),
            500: openapi.Response(
                "Internal Server Error",
                error_response_schema,
                examples={"application/json": {"error": "Database connection failed"}},
            ),
        },
        tags=["Common"],
    )
    def get(self, request):
        try:
            # Extract user from JWT (added by middleware)
            user = getattr(request, "jwt_user", None)
            if not user:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )


            with Dash_001Service() as service:
                # Use role-based filtering
                clusters = service.get_all_clusters_with_sites()

                return ResponseBuilder.success(
                    data={"clusters": clusters}, message="Clusters with sites retrieved successfully"
                )
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve clusters", data={"error": str(e)}
            )

class MapDataView(APIView):
    @swagger_auto_schema(
        operation_id="dash_get_plants_with_kpis_for_role",
        operation_summary="Get plants with KPIs based on user role",
        operation_description="Retrieve plants with coordinates and KPIs filtered by user's role-assigned clusters. Requires authentication.",
        responses={
            200: openapi.Response(
                "Success",
                mapdata_response_schema,
                examples={
                    "application/json": {
                        "plants": [
                            {
                                "name": "Plant-A",
                                "coordinates": {"lat": 24.8607, "lon": 67.0011},
                                "kpis": {"production": 123.4, "efficiency": 0.91},
                            }
                        ]
                    }
                },
            ),
            401: openapi.Response(
                "Unauthorized",
                error_response_schema,
                examples={"application/json": {"error": "Authentication required"}},
            ),
            500: openapi.Response(
                "Internal Server Error",
                error_response_schema,
                examples={"application/json": {"error": "Database connection failed"}},
            ),
        },
        tags=["Dash-001"],
    )
    def get(self, request):
        try:
            # Extract user from JWT (added by middleware)
            user = getattr(request, "jwt_user", None)
            if not user:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            # Get user's role_id
            role_id = user.get("role_id")

            with Dash_001Service() as service:
                # Use role-based filtering
                map_data = service.get_plants_with_kpis_for_role(role_id)

                # Determine appropriate message
                if not role_id:
                    message = "User has no role assigned - no plants available"
                elif not map_data.get("plants"):
                    message = "No plants available in your assigned clusters"
                else:
                    message = "Map data retrieved successfully"

                return ResponseBuilder.success(data=map_data, message=message)
        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve map data", data={"error": str(e)}
            )


class DailyDispatchGraphData(APIView):
    @swagger_auto_schema(
        operation_id="dash_get_daily_dispatch_graph_data",
        operation_summary="Get daily dispatch graph data for last 3 days",
        operation_description="Retrieve the latest available record for each of the last 3 days, filtered by user's role-assigned clusters. Optionally filter by specific cluster and site.",
        manual_parameters=[
            openapi.Parameter(
                "cluster",
                openapi.IN_QUERY,
                description="Optional cluster name to filter by (e.g., 'Cluster: KSA' or 'KSA')",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "site",
                openapi.IN_QUERY,
                description="Optional site name to filter by (e.g., 'Jubail-Jazlah')",
                type=openapi.TYPE_STRING,
                required=False,
            )
        ],
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "date": openapi.Schema(type=openapi.TYPE_STRING,
                                                           description="Date in YYYY-MM-DD format"),
                                    "plant_name": openapi.Schema(type=openapi.TYPE_STRING),
                                    "daily_dispatch": openapi.Schema(type=openapi.TYPE_NUMBER),
                                    "daily_dispatch_percent": openapi.Schema(type=openapi.TYPE_NUMBER),
                                }
                            )
                        )
                    }
                ),
                examples={
                    "application/json": {
                        "data": [
                            {
                                "date": "2025-11-09",
                                "plant_name": "Plant-A",
                                "daily_dispatch": 1234.5,
                                "daily_dispatch_percent": 85.2
                            },
                            {
                                "date": "2025-11-10",
                                "plant_name": "Plant-A",
                                "daily_dispatch": 1456.7,
                                "daily_dispatch_percent": 92.1
                            }
                        ]
                    }
                },
            ),
            401: openapi.Response(
                "Unauthorized",
                error_response_schema,
                examples={"application/json": {"error": "Authentication required"}},
            ),
            400: openapi.Response(
                "Bad Request",
                error_response_schema,
                examples={"application/json": {"error": "Invalid cluster or site parameter"}},
            ),
            500: openapi.Response(
                "Internal Server Error",
                error_response_schema,
                examples={"application/json": {"error": "Failed to retrieve data"}},
            ),
        },
        tags=["Dash-001"],
    )
    def get(self, request):
        try:
            # Extract user from JWT (added by middleware)
            user = getattr(request, "jwt_user", None)
            if not user:
                return ResponseBuilder.error(
                    message="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            # Get user's role_id
            role_id = user.get("role_id")

            # Get optional cluster and site filters from query params
            cluster_filter = request.GET.get("cluster", None)
            site_filter = request.GET.get("site", None)

            with Dash_001Service() as service:
                # Get daily dispatch data for last 3 days
                graph_data = service.get_daily_dispatch_graph_data(
                    role_id=role_id,
                    cluster_filter=cluster_filter,
                    site_filter=site_filter
                )

                # Determine appropriate message
                if not role_id:
                    message = "User has no role assigned - no data available"
                elif not graph_data:
                    if site_filter and cluster_filter:
                        message = f"No daily dispatch data available for site {site_filter} in cluster {cluster_filter}"
                    elif cluster_filter:
                        message = f"No daily dispatch data available for cluster {cluster_filter}"
                    else:
                        message = "No daily dispatch data available for the last 3 days"
                else:
                    if site_filter and cluster_filter:
                        message = f"Daily dispatch graph data retrieved successfully for site {site_filter} in cluster {cluster_filter}"
                    elif cluster_filter:
                        message = f"Daily dispatch graph data retrieved successfully for cluster {cluster_filter}"
                    else:
                        message = "Daily dispatch graph data retrieved successfully"

                return ResponseBuilder.success(
                    data=graph_data,
                    message=message
                )

        except Exception as e:
            return ResponseBuilder.server_error(
                message="Failed to retrieve daily dispatch graph data",
                data={"error": str(e)}
            )