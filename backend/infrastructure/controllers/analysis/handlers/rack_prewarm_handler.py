"""
Rack Prewarm Handler - Manual cache warming for testing
Allows manual prewarming of rack cache for testing purposes.
"""
import logging
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from infrastructure.services.analysis.analysis_base_service import AnalysisService
from infrastructure.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class RackPrewarmView(APIView):
    """
    API View for manually prewarming rack cache.
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache_service = None
    
    @property
    def cache_service(self):
        """Get cache service with lazy initialization"""
        if self._cache_service is None:
            self._cache_service = CacheService()
        return self._cache_service

    @swagger_auto_schema(
        operation_id="prewarm_racks",
        operation_summary="Prewarm rack cache",
        operation_description="Manually prewarm rack cache for specified site and tables",
        manual_parameters=[
            openapi.Parameter(
                "site_id",
                openapi.IN_QUERY,
                description="Site identifier",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "table_ids",
                openapi.IN_QUERY,
                description="Comma-separated table IDs",
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
                        "cache_available": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "processing_time": openapi.Schema(type=openapi.TYPE_NUMBER),
                        "racks_found": openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    )
    def get(self, request):
        """
        GET /prewarm-racks/?site_id=STPC&table_ids=table1,table2
        Prewarm rack cache for testing
        """
        try:
            start_time = time.time()
            
            site_id = request.GET.get('site_id')
            table_ids_param = request.GET.get('table_ids', '')
            
            if not site_id or not table_ids_param:
                return Response({
                    "success": False,
                    "message": "site_id and table_ids parameters are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            table_ids = [t.strip() for t in table_ids_param.split(',') if t.strip()]
            
            logger.info(f"Prewarming cache for site {site_id} with tables: {table_ids}")
            
            # Test cache availability
            cache_available = self.cache_service.is_available
            use_fallback = getattr(self.cache_service, 'use_fallback', False)
            
            logger.info(f"Cache status: available={cache_available}, use_fallback={use_fallback}")
            
            # Force process racks to warm cache
            analysis_service = AnalysisService()
            racks_data = analysis_service.get_unique_racks(site_id, table_ids)
            racks = racks_data.get("racks", [])
            
            processing_time = time.time() - start_time
            
            return Response({
                "success": True,
                "message": f"Cache prewarmed successfully for {site_id}",
                "cache_available": cache_available,
                "use_fallback": use_fallback,
                "processing_time": processing_time,
                "racks_found": len(racks),
                "sample_racks": racks[:5] if racks else []
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in rack prewarm: {str(e)}")
            return Response({
                "success": False,
                "message": f"Prewarm failed: {str(e)}",
                "cache_available": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
