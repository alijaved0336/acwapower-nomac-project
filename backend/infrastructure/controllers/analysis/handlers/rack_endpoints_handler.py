"""
Rack Endpoints Handler - Handles unique rack retrieval operations
Uses efficient Spark/SparkSQL operations without pandas for optimal performance.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from typing import List, Dict, Optional

from infrastructure.services.analysis.analysis_base_service import AnalysisService
from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig
from interface.serializers.rack_serializers import RackRequestListSerializer
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class RackEndpointsView(APIView):
    """
    API View for retrieving unique racks from specified tables.
    Uses ClickHouse as primary data source with Spark fallback, Redis caching and parallel processing for optimal performance.
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
            logger.info("Cache service initialized in rack endpoints handler")
        return self._cache_service

    @swagger_auto_schema(
        operation_id="fetch_unique_racks",
        operation_summary="Fetch unique racks from specified tables",
        operation_description="Retrieve unique racks from the specified sites and tables using ClickHouse as primary data source with Spark fallback for optimal performance.",
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['siteName', 'tableName'],
                properties={
                    'siteName': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Name of the site containing the table',
                        example='STPC'
                    ),
                    'tableName': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Name of the table to get racks for',
                        example='STPC_Normalization_pass_1'
                    )
                }
            ),
            description='Array of rack requests with site and table information',
            example=[
                {
                    "siteName": "STPC",
                    "tableName": "STPC_Normalization_pass_1"
                }
            ]
        ),
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
                                    "rackLabel": openapi.Schema(type=openapi.TYPE_STRING),
                                    "siteName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "tableName": openapi.Schema(type=openapi.TYPE_STRING),
                                    "rackValue": openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True)
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
    def post(self, request):
        """
        POST /fetch-racks/
        Returns unique racks from the specified sites and tables using ClickHouse as primary data source with Spark fallback.
        
        Request body:
        [
            {
                "siteName": "STPC",
                "tableName": "STPC_Normalization_pass_1"
            }
        ]
        
        Response format:
        {
            "success": true,
            "message": "Unique racks retrieved successfully",
            "data": [
                {
                    "rackLabel": "RACK_05",
                    "siteName": "STPC",
                    "tableName": "STPC_Normalization_pass_1",
                    "rackValue": "RACK_05"
                }
            ]
        }
        """
        try:
            start_time = time.time()

            # Fix 1: Handle empty payload
            if not request.data or len(request.data) == 0:
                logger.warning("Empty payload received in rack endpoints request")
                return Response({
                    "success": False,
                    "message": "Request payload cannot be empty",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Fix 2: Enforce 15-table limit
            MAX_TABLES = 15
            if len(request.data) > MAX_TABLES:
                logger.warning(f"Request exceeds maximum table limit: {len(request.data)} > {MAX_TABLES}")
                return Response({
                    "success": False,
                    "message": f"Maximum {MAX_TABLES} tables allowed per request",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate request data using serializer
            serializer = RackRequestListSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Invalid request data",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            validated_requests = serializer.validated_data
            logger.info(f"Processing rack endpoints request with {len(validated_requests)} site-table pairs")
            
            # Quick cache test
            test_key = "cache_test"
            self.cache_service.set(test_key, "test_value", ttl=60, prefix="test")
            test_result = self.cache_service.get(test_key, prefix="test")
            logger.info(f"Cache test: set 'test_value', got '{test_result}' - Cache working: {test_result == 'test_value'}")
            
            # Step 1: Check global cache for entire request
            cache_key = self._generate_request_cache_key(validated_requests)
            logger.info(f"Checking cache with key: {cache_key}")
            logger.info(f"Cache service available: {self.cache_service.is_available}")
            logger.info(f"Cache service using fallback: {getattr(self.cache_service, 'use_fallback', 'unknown')}")
            
            cached_result = self.cache_service.get(cache_key, prefix="rack_requests")
            logger.info(f"Cache get result: {type(cached_result)} - {cached_result is not None}")
            
            if cached_result:
                logger.info(f"Cache HIT: Found cached result with {len(cached_result)} racks")
                cache_time = time.time() - start_time
                logger.info(f"Cache HIT: Retrieved {len(cached_result)} racks from Redis cache in {cache_time:.3f}s")
                return Response({
                    "success": True,
                    "message": f"Unique racks retrieved successfully from cache ({cache_time:.3f}s)",
                    "data": cached_result
                }, status=status.HTTP_200_OK)
            
            logger.info(f"Cache MISS: Processing rack request with parallel optimization. Cache service available: {self.cache_service.is_available if hasattr(self.cache_service, 'is_available') else 'unknown'}")
            
            # Step 2: Group requests by site for parallel processing
            site_table_map = {}
            for request_item in validated_requests:
                site_name = request_item['siteName']
                table_name = request_item['tableName']
                
                if site_name not in site_table_map:
                    site_table_map[site_name] = []
                site_table_map[site_name].append(table_name)
            
            # Step 3: Process sites in parallel (max 3 concurrent sites)
            all_racks = []
            total_processed = 0
            
            with ThreadPoolExecutor(max_workers=min(3, len(site_table_map))) as executor:
                # Submit all site processing tasks
                future_to_site = {
                    executor.submit(self._process_site_racks, site_id, table_ids): site_id 
                    for site_id, table_ids in site_table_map.items()
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_site, timeout=120):  # 120 second timeout per site
                    site_id = future_to_site[future]
                    try:
                        site_racks, processed_count = future.result()
                        all_racks.extend(site_racks)
                        total_processed += processed_count
                        logger.info(f"Successfully processed site {site_id} with {len(site_racks)} racks")
                    except Exception as e:
                        logger.error(f"Error processing site {site_id}: {str(e)}")
                        # Continue processing other sites
            
            # Step 4: Cache the result (10 minute TTL)
            logger.info(f"Attempting to cache result with key: {cache_key}, {len(all_racks)} racks")
            cache_success = self.cache_service.set(
                cache_key, 
                all_racks, 
                ttl=600,  # 10 minutes - racks don't change frequently
                prefix="rack_requests"
            )
            
            if cache_success:
                logger.info(f"SUCCESS: Cached rack request result with {len(all_racks)} racks")
            else:
                logger.error(f"FAILED: Could not cache rack request result with {len(all_racks)} racks")
            
            processing_time = time.time() - start_time
            logger.info(f"Successfully retrieved {len(all_racks)} unique racks from {total_processed} tables in {processing_time:.3f}s")
            
            return Response({
                "success": True,
                "message": f"Unique racks retrieved successfully ({processing_time:.3f}s)",
                "data": all_racks
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving rack endpoints: {str(e)}")
            return Response({
                "success": False,
                "message": f"Failed to retrieve rack endpoints: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_request_cache_key(self, validated_requests: List[Dict]) -> str:
        """Generate cache key for the entire rack request"""
        # Sort requests for consistent cache keys
        sorted_requests = sorted(
            validated_requests, 
            key=lambda x: (x['siteName'], x['tableName'])
        )
        
        # Create hash from request content
        request_string = "_".join([
            f"{req['siteName']}:{req['tableName']}" 
            for req in sorted_requests
        ])
        
        request_hash = hashlib.md5(request_string.encode()).hexdigest()[:16]
        return f"rack_request_{request_hash}"
    
    def _process_site_racks(self, site_id: str, table_ids: List[str]) -> tuple:
        """
        Process racks for a single site (used in parallel processing).
        Returns tuple of (racks_list, processed_count)
        """
        try:
            logger.info(f"Processing site {site_id} with {len(table_ids)} tables in parallel")
            analysis_service = AnalysisService()
            racks_data = analysis_service.get_unique_racks(site_id, table_ids)
            site_racks = racks_data.get("racks", [])
            return site_racks, len(table_ids)
        except Exception as e:
            logger.error(f"Error in parallel processing for site {site_id}: {str(e)}")
            return [], len(table_ids)
