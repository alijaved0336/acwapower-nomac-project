"""
Cache Diagnostic Handler - Test cache functionality
Quick endpoint to test if Redis caching is working properly.
"""
import logging
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from infrastructure.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class CacheDiagnosticView(APIView):
    """
    API View for testing cache functionality.
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
        operation_id="test_cache",
        operation_summary="Test cache functionality",
        operation_description="Test if Redis cache is working properly",
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "cache_available": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "tests": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    )
    def get(self, request):
        """
        GET /cache-test/
        Test cache functionality
        """
        try:
            start_time = time.time()
            test_results = {}
            
            # Test 1: Basic cache availability
            cache_available = self.cache_service.is_available
            test_results["cache_available"] = cache_available
            logger.info(f"Cache availability: {cache_available}")
            
            # Test 2: Simple set/get test
            test_key = "diagnostic_test"
            test_value = {"timestamp": time.time(), "data": "test_cache_value"}
            
            set_success = self.cache_service.set(test_key, test_value, ttl=60, prefix="test")
            test_results["set_operation"] = set_success
            logger.info(f"Cache set test: {set_success}")
            
            if set_success:
                get_result = self.cache_service.get(test_key, prefix="test")
                get_success = get_result is not None and get_result.get("data") == "test_cache_value"
                test_results["get_operation"] = get_success
                test_results["retrieved_value"] = get_result
                logger.info(f"Cache get test: {get_success}, value: {get_result}")
            else:
                test_results["get_operation"] = False
                test_results["retrieved_value"] = None
            
            # Test 3: Different prefixes
            prefix_test_key = "prefix_test"
            prefix_test_value = "prefix_test_value"
            
            set_prefix_success = self.cache_service.set(prefix_test_key, prefix_test_value, ttl=60, prefix="rack_data")
            get_prefix_result = self.cache_service.get(prefix_test_key, prefix="rack_data")
            prefix_test_success = get_prefix_result == prefix_test_value
            
            test_results["prefix_test"] = {
                "set_success": set_prefix_success,
                "get_success": prefix_test_success,
                "value": get_prefix_result
            }
            
            # Test 4: Cache configuration
            test_results["cache_config"] = {
                "has_cache_instance": hasattr(self.cache_service, 'cache') and self.cache_service.cache is not None,
                "config_available": hasattr(self.cache_service, 'config') and bool(self.cache_service.config)
            }
            
            processing_time = time.time() - start_time
            
            overall_success = (
                cache_available and 
                test_results.get("set_operation", False) and 
                test_results.get("get_operation", False) and
                test_results.get("prefix_test", {}).get("get_success", False)
            )
            
            return Response({
                "success": overall_success,
                "message": f"Cache diagnostic completed in {processing_time:.3f}s",
                "cache_available": cache_available,
                "processing_time_seconds": processing_time,
                "tests": test_results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in cache diagnostic: {str(e)}")
            return Response({
                "success": False,
                "message": f"Cache diagnostic failed: {str(e)}",
                "cache_available": False,
                "tests": {"error": str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
