"""
Sites List Handler - Handles Azure Data Lake sites listing operations
Now using Spark-based operations for consistency with the rest of the system.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from infrastructure.services.analysis.analysis_base_service import AnalysisService
from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig

logger = logging.getLogger(__name__)


class SitesListView(APIView):
    """
    API View for listing all available sites (directories) in Azure Data Lake.
    Now uses Spark-based operations with Redis caching for optimal performance.
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache_service = CacheService()

    @swagger_auto_schema(
        operation_id="get_all_sites",
        operation_summary="Get all available sites",
        operation_description="Retrieve all available sites (directories) in Azure Data Lake using Spark-based directory listing.",
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
                                "sites": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "name": openapi.Schema(type=openapi.TYPE_STRING),
                                            "path": openapi.Schema(type=openapi.TYPE_STRING)
                                        }
                                    )
                                ),
                                "method_used": openapi.Schema(type=openapi.TYPE_STRING),
                                "count": openapi.Schema(type=openapi.TYPE_INTEGER)
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
        }
    )
    def get(self, request):
        """
        GET /sites/
        Returns list of all available sites using Spark-based directory listing.
        
        Response format:
        {
            "success": true,
            "message": "Sites retrieved successfully using spark based",
            "data": {
                "sites": [
                    {"name": "site1", "path": "tables/gold/site1"},
                    {"name": "site2", "path": "tables/gold/site2"}
                ],
                "method_used": "spark_based",
                "count": 2
            }
        }
        """
        try:
            logger.info("Processing sites list request with Redis caching")
            
            # Check Redis cache first (sites don't change often)
            cache_key = "all_sites_directories"
            cached_sites = self.cache_service.get(cache_key, prefix="directory_data")
            
            if cached_sites:
                logger.info(f"Cache HIT: Retrieved {cached_sites.get('count', 0)} sites from Redis cache")
                return Response({
                    "success": True,
                    "message": f"Sites retrieved successfully from cache",
                    "data": cached_sites
                }, status=status.HTTP_200_OK)
            
            logger.info("Cache MISS: Fetching sites using Spark-based operations")
            
            # Get directories using the new Spark-based method
            analysis_service = AnalysisService()
            directories = analysis_service.get_all_directories()
            
            # Determine which method was actually used
            method_used = "spark_based"  # Default assumption
            
            # If we got results, format the response
            sites_data = {
                "sites": directories,
                "method_used": method_used,
                "count": len(directories)
            }
            
            # Cache the result for 1 hour (directories don't change often)
            cache_success = self.cache_service.set(
                cache_key, 
                sites_data, 
                ttl=4800,  # 1 hour
                prefix="directory_data"
            )
            
            if cache_success:
                logger.info(f"Cached {len(directories)} sites (TTL: 1 hour)")
            
            logger.info(f"Successfully retrieved {len(directories)} sites using {method_used}")
            
            return Response({
                "success": True,
                "message": f"Sites retrieved successfully using {method_used.replace('_', ' ')}",
                "data": sites_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving sites: {str(e)}")
            return Response({
                "success": False,
                "message": f"Failed to retrieve sites: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)