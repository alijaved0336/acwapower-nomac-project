"""
Tables List Handler - Handles Azure Data Lake tables listing operations for specific sites
Now using Spark-based operations for consistency with the rest of the system.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from infrastructure.services.analysis.analysis_base_service import AnalysisService
from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig

logger = logging.getLogger(__name__)


class TablesListView(APIView):
    """
    API View for listing all available tables in a specific site.
    Now uses Spark-based operations with Redis caching for optimal performance.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache_service = CacheService()

    @swagger_auto_schema(
        operation_id="get_tables_for_site",
        operation_summary="Get tables for a specific site",
        operation_description="Retrieve all available tables in the specified site. Returns table names with their corresponding site names.",
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_PATH,
                description="Site identifier",
                type=openapi.TYPE_STRING,
                required=True,
            )
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
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "siteName": openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
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
        }
    )
    def get(self, request, site_id):
        """
        GET /tables/{site_id}/
        Returns list of all available tables in the specified site using Spark-based operations.
        
        Args:
            site_id (str): The site identifier
            
        Response format:
        {
            "success": true,
            "message": "Tables retrieved successfully",
            "data": [
                {
                    "tableName": "Jubail-Jazlah_Normalization_pass_1",
                    "siteName": "Jubail-Jazlah"
                },
                {
                    "tableName": "Jubail_Chemicals_ppm",
                    "siteName": "Jubail-Jazlah"
                }
            ]
        }
        """
        try:
            logger.info(f"Processing tables list request for site {site_id} with Redis caching")
            
            # Check Redis cache first (tables don't change often)
            cache_key = f"tables_site_{site_id}"
            cached_tables = self.cache_service.get(cache_key, prefix="directory_data")
            
            if cached_tables:
                logger.info(f"Cache HIT: Retrieved {len(cached_tables)} tables for site {site_id} from Redis cache")
                return Response({
                    "success": True,
                    "message": "Tables retrieved successfully from cache",
                    "data": cached_tables
                }, status=status.HTTP_200_OK)
            
            logger.info(f"Cache MISS: Fetching tables for site {site_id} using Spark-based operations")
            
            # Get subdirectories (tables) using the new Spark-based method
            analysis_service = AnalysisService()
            subdirectories = analysis_service.get_subdirectories(site_id)
            
            # Determine which method was actually used
            method_used = "spark_based"  # Default assumption
            
            # Transform the response format to match the desired structure
            transformed_tables = []
            for table in subdirectories:
                transformed_tables.append({
                    "tableName": table.get("name", ""),
                    "siteName": site_id
                })
            
            # Cache the result for 30 minutes (tables don't change often)
            cache_success = self.cache_service.set(
                cache_key, 
                transformed_tables, 
                ttl=4800,  # 30 minutes
                prefix="directory_data"
            )
            
            if cache_success:
                logger.info(f"Cached {len(transformed_tables)} tables for site {site_id} (TTL: 30 minutes)")
            
            logger.info(f"Successfully retrieved {len(subdirectories)} tables for site {site_id} using {method_used}")
            
            return Response({
                "success": True,
                "message": "Tables retrieved successfully",
                "data": transformed_tables
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving tables for site {site_id}: {str(e)}")
            return Response({
                "success": False,
                "message": f"Failed to retrieve tables for site {site_id}: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)