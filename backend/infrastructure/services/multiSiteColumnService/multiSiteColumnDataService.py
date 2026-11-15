"""
Multi-Site Column Data Service - Core Implementation with Rack Filtering Fix
Handles concurrent processing of column requests across multiple sites and tables.
"""
import logging
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from infrastructure.utils.azure.blobStorageClient import BlobStorageClient
from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig

from .models import (
    ColumnRequest, ColumnResponse, FilterMode, ProcessingStats, 
    TableProcessingResult, FileInfo
)
from .datetimeProcessor import DateTimeProcessor
from .fileProcessor import FileProcessor
from .sparkFileProcessor import SparkFileProcessor

logger = logging.getLogger(__name__)


class MultiSiteColumnDataService:
    """
    Main service for handling multi-site, multi-table column data requests.
    Optimized for concurrent processing with intelligent request grouping.
    """
    
    def __init__(self):
        # Core dependencies
        self.blob_client = BlobStorageClient()
        # Removed SparkRepository() - using Spark singleton instead
        self.datetime_processor = DateTimeProcessor()
        self.file_processor = FileProcessor()  # Fallback for non-Spark operations
        self.spark_file_processor = SparkFileProcessor()  # Primary processor (lazy initialization)
        
        # Redis cache service for performance optimization
        self.cache_service = CacheService()
        
        # Concurrency settings optimized for ADLS performance
        self.max_concurrent_sites = 3      # Balance between speed and resource usage
        self.max_concurrent_tables = 2     # Avoid overwhelming single site storage
        self.max_files_per_table = 20      # Limit for memory management
        self.batch_size = 10000           # Rows per processing batch
        
        # Timeout settings
        self.site_timeout_seconds = 300    # 5 minutes per site
        self.table_timeout_seconds = 120   # 2 minutes per table
        
        logger.info("[MULTI_SITE_SERVICE] Service initialized with Redis caching and optimized settings")
    
    def get_column_data_sources(
        self,
        column_requests: List[ColumnRequest],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        rack_list: Optional[List[str]] = None
    ) -> List[ColumnResponse]:
        """
        Main entry point for multi-site column data retrieval.
        Handles concurrent processing across sites and tables with Redis caching.

        Args:
            column_requests: List of column requests to process
            from_date: Start date for filtering
            to_date: End date for filtering
            rack_list: List of rack values for filtering
        """
        start_time = time.time()
        stats = ProcessingStats()

        try:
            # Ensure rack_list is initialized
            if rack_list is None:
                rack_list = []

            rack_summary = f" with {len(rack_list)} rack filters: {rack_list}" if rack_list else ""
            logger.info(f"[MULTI_SITE_SERVICE] Processing {len(column_requests)} column requests{rack_summary}")
            
            # Step 0: Check cache for individual column requests with validation
            cached_responses = []
            uncached_requests = []
            
            for request in column_requests:
                cache_key = self._generate_cache_key(request, from_date, to_date, rack_list)
                cached_response = self.cache_service.get(cache_key, prefix="column_data")

                if cached_response and self._validate_cached_response(cached_response, from_date, to_date, rack_list):
                    logger.debug(f"[CACHE_HIT] {request.siteName}/{request.tableName}/{request.columnName}")
                    # Convert cached dict back to ColumnResponse object
                    response_data = {
                        key: value for key, value in cached_response.items()
                        if key != 'filter_metadata'
                    }
                    cached_responses.append(ColumnResponse(**response_data))
                else:
                    if cached_response:
                        logger.debug(f"[CACHE_INVALID] {request.siteName}/{request.tableName}/{request.columnName} - filter mismatch")
                        # Invalidate the invalid cache entry
                        self.cache_service.delete(cache_key, prefix="column_data")
                    else:
                        logger.debug(f"[CACHE_MISS] {request.siteName}/{request.tableName}/{request.columnName}")
                    uncached_requests.append(request)
            
            # If all requests were cached, return immediately
            if not uncached_requests:
                logger.info(f"[MULTI_SITE_SERVICE] All {len(column_requests)} requests served from cache in {time.time() - start_time:.3f}s")
                return cached_responses
            
            logger.info(f"[MULTI_SITE_SERVICE] Cache: {len(cached_responses)} hits, {len(uncached_requests)} misses")
            
            # Step 1: Parse and validate DateTime parameters
            filter_mode, from_dt, to_dt = self.datetime_processor.parse_filter_params(
                from_date, to_date
            )
            stats.filter_mode = filter_mode.value
            
            # Log the filters being applied
            filter_summary = self.datetime_processor.get_filter_summary(filter_mode, from_dt, to_dt)
            rack_summary = f", rack_list={rack_list}" if rack_list else ""
            logger.info(f"[MULTI_SITE_SERVICE] Filters: {filter_summary}{rack_summary}")
            
            # Step 2: Validate and group uncached requests for optimization
            validated_requests = self._validate_column_requests(uncached_requests)
            grouped_requests = self._group_requests_for_optimal_processing(validated_requests)
            
            stats.sites_processed = len(grouped_requests)
            stats.tables_processed = sum(len(tables) for tables in grouped_requests.values())
            stats.total_columns = len(uncached_requests)
            
            logger.info(f"[MULTI_SITE_SERVICE] Grouped {len(uncached_requests)} uncached requests into {stats.sites_processed} sites, {stats.tables_processed} tables")
            
            # Step 3: Process groups concurrently (only uncached requests)
            fresh_responses = {}
            if grouped_requests:
                fresh_responses = self._process_request_groups_parallel(
                    grouped_requests, filter_mode, from_dt, to_dt, rack_list, stats
                )
            
            # Step 4: Cache fresh responses
            self._cache_fresh_responses(fresh_responses, from_date, to_date, rack_list)
            
            # Step 5: Combine cached and fresh responses, maintain original request order
            all_responses_dict = {}
            
            # Add cached responses
            for cached_response in cached_responses:
                response_key = f"{cached_response.siteName}_{cached_response.tableName}_{cached_response.columnName}"
                all_responses_dict[response_key] = cached_response
            
            # Add fresh responses
            all_responses_dict.update(fresh_responses)
            
            # Step 6: Maintain original request order
            ordered_responses = self._reorder_responses_to_match_requests(
                all_responses_dict, column_requests
            )
            
            # Step 5: Performance logging
            stats.processing_time_seconds = time.time() - start_time
            logger.info(f"[MULTI_SITE_SERVICE] Completed processing: {stats.to_dict()}")
            
            return ordered_responses
            
        except Exception as e:
            logger.error(f"[MULTI_SITE_SERVICE] Critical error: {str(e)}", exc_info=True)
            # Fallback to existing architecture on critical errors
            return self._fallback_to_existing_service(column_requests, from_date, to_date, rack_list)
    
    def _generate_cache_key(
        self,
        request: ColumnRequest,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        rack_list: Optional[List[str]] = None
    ) -> str:
        """
        Generate a cache key for a column request with all filter parameters.
        Enhanced to support multiple racks and prevent datetime filter collisions.
        """
        import hashlib

        # Create a deterministic key based on all request parameters
        # Include more specific datetime formatting to prevent collisions
        from_date_normalized = self._normalize_date_for_cache(from_date)
        to_date_normalized = self._normalize_date_for_cache(to_date)

        # Create deterministic rack key for multiple racks
        if rack_list:
            # Sort rack list for consistent cache keys regardless of input order
            sorted_racks = sorted(rack_list)
            rack_key = ",".join(sorted_racks)
        else:
            rack_key = "no_rack"

        key_components = [
            request.siteName,
            request.tableName,
            request.columnName,
            request.columnType,
            from_date_normalized,
            to_date_normalized,
            rack_key
        ]
        
        # Create hash for compact key
        key_string = "_".join(key_components)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]  # Increased to 16 chars for better uniqueness
        
        return f"column_{request.siteName}_{request.tableName}_{request.columnName}_{key_hash}"
    
    def _validate_cached_response(
        self,
        cached_response: dict,
        from_date: Optional[str],
        to_date: Optional[str],
        rack_list: Optional[List[str]]
    ) -> bool:
        """
        Validate that cached response matches current filter parameters.
        """
        try:
            # Check if cached response has filter metadata
            if 'filter_metadata' not in cached_response:
                logger.debug("[CACHE_VALIDATION] No filter metadata in cached response")
                return False
            
            filter_metadata = cached_response['filter_metadata']
            
            # Normalize dates for comparison
            cached_from = filter_metadata.get('from_date')
            cached_to = filter_metadata.get('to_date')
            cached_rack_key = filter_metadata.get('rack', filter_metadata.get('rack_key'))  # Support both old and new formats

            current_from = self._normalize_date_for_cache(from_date)
            current_to = self._normalize_date_for_cache(to_date)

            # Create consistent rack key for comparison
            if rack_list:
                current_rack_key = ",".join(sorted(rack_list))
            else:
                current_rack_key = "no_rack"

            # Compare filter parameters
            if (cached_from == current_from and
                cached_to == current_to and
                cached_rack_key == current_rack_key):
                return True
            else:
                logger.debug(f"[CACHE_VALIDATION] Filter mismatch - cached: {cached_from}/{cached_to}/{cached_rack_key}, current: {current_from}/{current_to}/{current_rack_key}")
                return False
                
        except Exception as e:
            logger.warning(f"[CACHE_VALIDATION] Error validating cached response: {e}")
            return False
    
    def _normalize_date_for_cache(self, date_str: Optional[str]) -> str:
        """
        Normalize date string for consistent cache key generation.
        """
        if not date_str:
            return "no_date"
        
        try:
            # Parse and reformat to ensure consistency
            from datetime import datetime
            # Handle different date formats
            if ',' in date_str:
                # Format: "2025-06-01,10:00:00"
                date_part, time_part = date_str.split(',', 1)
                normalized = f"{date_part}T{time_part}"
            elif ' ' in date_str:
                # Format: "2025-06-01 10:00:00"
                normalized = date_str.replace(' ', 'T')
            else:
                # Format: "2025-06-01"
                normalized = f"{date_str}T00:00:00"
            
            # Validate and return normalized format
            datetime.fromisoformat(normalized)
            return normalized
        except Exception:
            # If parsing fails, use original string
            return date_str
    
    def _cache_fresh_responses(
        self,
        fresh_responses: Dict[str, ColumnResponse],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        rack_list: Optional[List[str]] = None
    ) -> None:
        """
        Cache fresh responses with appropriate TTL.
        """
        if not fresh_responses:
            return
            
        cached_count = 0
        failed_count = 0
        
        for response_key, response in fresh_responses.items():
            try:
                # Create a ColumnRequest from the response to generate cache key
                request = ColumnRequest(
                    siteName=response.siteName,
                    tableName=response.tableName,
                    columnName=response.columnName,
                    columnType=response.columnType
                )
                
                cache_key = self._generate_cache_key(request, from_date, to_date, rack_list)
                
                # Convert ColumnResponse to dict for caching with filter metadata
                response_dict = {
                    'columnName': response.columnName,
                    'columnType': response.columnType,
                    'tableName': response.tableName,
                    'siteName': response.siteName,
                    'dataSource': response.dataSource,
                    'filter_metadata': {
                        'from_date': self._normalize_date_for_cache(from_date),
                        'to_date': self._normalize_date_for_cache(to_date),
                        'rack_key': ",".join(sorted(rack_list)) if rack_list else "no_rack",
                        'rack_list': rack_list or [],
                        'cached_at': time.time()
                    }
                }
                
                # Cache with 5-minute TTL (same as widget caching)
                success = self.cache_service.set(
                    cache_key, 
                    response_dict, 
                    ttl=CacheConfig.DEFAULT_TTL,  # 5 minutes
                    prefix="column_data"
                )
                
                if success:
                    cached_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to cache response for {response_key}: {e}")
                failed_count += 1
        
        logger.info(f"[MULTI_SITE_SERVICE] Cached {cached_count} responses, {failed_count} cache failures")
    
    def clear_cache_for_datetime_range(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        rack_list: Optional[List[str]] = None
    ) -> int:
        """
        Clear cache entries for a specific datetime range.
        Useful for debugging and ensuring fresh data.

        Args:
            from_date: Start date for cache clearing
            to_date: End date for cache clearing
            rack_list: List of rack values for cache filtering
        """
        try:
            # Ensure rack_list is initialized
            if rack_list is None:
                rack_list = []

            # Generate a pattern to match cache keys for this datetime range
            from_date_normalized = self._normalize_date_for_cache(from_date)
            to_date_normalized = self._normalize_date_for_cache(to_date)
            rack_key = ",".join(sorted(rack_list)) if rack_list else "no_rack"
            
            # Create a pattern that matches the datetime range
            pattern = f"column_*_{from_date_normalized}_{to_date_normalized}_{rack_key}"
            
            # Clear cache entries matching this pattern
            cleared_count = self.cache_service.clear_prefix("column_data")
            
            logger.info(f"[CACHE_CLEAR] Cleared {cleared_count} cache entries for datetime range {from_date} to {to_date}")
            return cleared_count
            
        except Exception as e:
            logger.error(f"[CACHE_CLEAR] Error clearing cache for datetime range: {e}")
            return 0
    
    def _validate_column_requests(self, requests: List[ColumnRequest]) -> List[ColumnRequest]:
        """Validate and filter column requests."""
        validated = []
        
        for request in requests:
            try:
                # Basic validation is handled in ColumnRequest.__post_init__
                # Additional validation can be added here
                if len(request.columnName) > 200:
                    logger.warning(f"Column name too long: {request.columnName[:50]}...")
                    continue
                    
                if len(request.tableName) > 100:
                    logger.warning(f"Table name too long: {request.tableName}")
                    continue
                    
                validated.append(request)
                
            except Exception as e:
                logger.warning(f"Invalid column request: {e}")
                continue
        
        logger.info(f"[MULTI_SITE_SERVICE] Validated {len(validated)}/{len(requests)} requests")
        return validated
    
    def _group_requests_for_optimal_processing(
        self, 
        requests: List[ColumnRequest]
    ) -> Dict[str, Dict[str, List[ColumnRequest]]]:
        """
        Group requests by site and table for optimal batch processing.
        Structure: {site_name: {table_name: [column_requests]}}
        """
        grouped = defaultdict(lambda: defaultdict(list))
        
        for request in requests:
            site_name = request.siteName
            table_name = request.tableName
            grouped[site_name][table_name].append(request)
        
        # Convert to regular dicts and optimize processing order
        regular_dict = {
            site: dict(tables) for site, tables in grouped.items()
        }
        
        optimized = self._optimize_processing_order(regular_dict)
        
        # Log grouping results
        for site_name, tables in optimized.items():
            table_counts = {table: len(columns) for table, columns in tables.items()}
            logger.info(f"[MULTI_SITE_SERVICE] Site {site_name}: {table_counts}")
        
        return optimized
    
    def _optimize_processing_order(
        self, 
        grouped_requests: Dict[str, Dict[str, List[ColumnRequest]]]
    ) -> Dict[str, Dict[str, List[ColumnRequest]]]:
        """
        Optimize processing order based on estimated table sizes and complexity.
        Process smaller/faster tables first for better perceived performance.
        """
        optimized = {}
        
        for site_name, tables in grouped_requests.items():
            # Sort tables by estimated complexity (fewer columns = simpler)
            sorted_tables = sorted(
                tables.items(), 
                key=lambda x: (len(x[1]), x[0])  # Sort by column count, then name
            )
            optimized[site_name] = dict(sorted_tables)
        
        # Sort sites by total request count (process smaller sites first)
        return dict(sorted(
            optimized.items(),
            key=lambda x: (sum(len(columns) for columns in x[1].values()), x[0])
        ))
    
    def _process_request_groups_parallel(
        self,
        grouped_requests: Dict[str, Dict[str, List[ColumnRequest]]],
        filter_mode: FilterMode,
        from_dt: Optional[str],
        to_dt: Optional[str],
        rack_list: Optional[List[str]],
        stats: ProcessingStats
    ) -> Dict[str, ColumnResponse]:
        """
        Process site groups in parallel with controlled concurrency.
        """
        all_responses = {}
        
        logger.info(f"[MULTI_SITE_SERVICE] Starting parallel processing of {len(grouped_requests)} sites")
        
        # Create thread pool for site-level parallelism
        with ThreadPoolExecutor(max_workers=self.max_concurrent_sites) as site_executor:
            
            # Submit site processing tasks
            site_futures = {
                site_executor.submit(
                    self._process_site_requests,
                    site_name,
                    site_tables,
                    filter_mode,
                    from_dt,
                    to_dt,
                    rack_list
                ): site_name for site_name, site_tables in grouped_requests.items()
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(site_futures, timeout=self.site_timeout_seconds * len(site_futures)):
                site_name = site_futures[future]
                try:
                    site_responses = future.result(timeout=self.site_timeout_seconds)
                    all_responses.update(site_responses)
                    
                    logger.info(f"[MULTI_SITE_SERVICE] Completed processing site: {site_name}")
                    
                except concurrent.futures.TimeoutError:
                    logger.error(f"[MULTI_SITE_SERVICE] Timeout processing site: {site_name}")
                    # Create timeout error responses
                    error_responses = self._create_error_responses_for_site(
                        site_name, grouped_requests[site_name], "Processing timeout"
                    )
                    all_responses.update(error_responses)
                    
                except Exception as e:
                    logger.error(f"[MULTI_SITE_SERVICE] Error processing site {site_name}: {e}")
                    # Create error responses for failed site
                    error_responses = self._create_error_responses_for_site(
                        site_name, grouped_requests[site_name], str(e)
                    )
                    all_responses.update(error_responses)
        
        logger.info(f"[MULTI_SITE_SERVICE] Parallel processing completed, {len(all_responses)} responses")
        return all_responses
    
    def _process_site_requests(
        self,
        site_name: str,
        site_tables: Dict[str, List[ColumnRequest]],
        filter_mode: FilterMode,
        from_dt: Optional[str],
        to_dt: Optional[str],
        rack_list: Optional[List[str]]
    ) -> Dict[str, ColumnResponse]:
        """
        Process all tables within a site with table-level parallelism.
        """
        site_responses = {}
        
        logger.info(f"[MULTI_SITE_SERVICE] Processing site: {site_name} with {len(site_tables)} tables")
        
        # Process tables within site in parallel
        with ThreadPoolExecutor(max_workers=self.max_concurrent_tables) as table_executor:
            
            table_futures = {
                table_executor.submit(
                    self._process_single_table,
                    site_name,
                    table_name,
                    column_requests,
                    filter_mode,
                    from_dt,
                    to_dt,
                    rack_list
                ): (site_name, table_name) for table_name, column_requests in site_tables.items()
            }
            
            # Collect table results
            for future in concurrent.futures.as_completed(table_futures, timeout=self.table_timeout_seconds * len(table_futures)):
                site_name_key, table_name = table_futures[future]
                try:
                    table_responses = future.result(timeout=self.table_timeout_seconds)
                    site_responses.update(table_responses)
                    
                    logger.info(f"[MULTI_SITE_SERVICE] Completed table: {site_name}/{table_name}")
                    
                except concurrent.futures.TimeoutError:
                    logger.error(f"[MULTI_SITE_SERVICE] Timeout processing table {site_name}/{table_name}")
                    # Create timeout error responses
                    error_responses = self._create_error_responses_for_table(
                        site_name, table_name, site_tables[table_name], "Processing timeout"
                    )
                    site_responses.update(error_responses)
                    
                except Exception as e:
                    logger.error(f"[MULTI_SITE_SERVICE] Error processing table {site_name}/{table_name}: {e}")
                    # Create error responses for failed table
                    error_responses = self._create_error_responses_for_table(
                        site_name, table_name, site_tables[table_name], str(e)
                    )
                    site_responses.update(error_responses)
        
        logger.info(f"[MULTI_SITE_SERVICE] Site {site_name} completed with {len(site_responses)} responses")
        return site_responses
    
    def _process_single_table(
        self,
        site_name: str,
        table_name: str,
        column_requests: List[ColumnRequest],
        filter_mode: FilterMode,
        from_dt: Optional[str],
        to_dt: Optional[str],
        rack_list: Optional[List[str]]
    ) -> Dict[str, ColumnResponse]:
        """
        Process all columns for a single table in one optimized operation.
        This is the core optimization: single I/O per table for multiple columns.
        """
        try:
            logger.info(f"[TABLE_PROCESSOR] Processing {len(column_requests)} columns for {site_name}/{table_name}")
            
            # Extract column names and ensure DateTime is included for filtering
            column_names = [req.columnName for req in column_requests]
            required_columns = list(set(column_names + ["DateTime"]))
            
            # Add potential rack columns for filtering
            potential_rack_columns = ["rack", "trailer", "Rack", "Trailer", "RACK", "TRAILER"]
            if rack_list:
                # Check which rack columns might exist and add them to required columns
                for rack_col in potential_rack_columns:
                    if rack_col not in required_columns:
                        required_columns.append(rack_col)
            
            # Create column type mapping
            column_types = {}
            for req in column_requests:
                column_types[req.columnName] = req.columnType
            # DateTime is always treated as string for ISO formatting
            column_types["DateTime"] = "string"
            for rack_col in potential_rack_columns:
                if rack_col in required_columns:
                    column_types[rack_col] = "string"
            
            # Single optimized read for all columns using SparkFileProcessor (5-10x faster)
            table_data = self.spark_file_processor.read_table_data_optimized(
                site_name=site_name,
                table_name=table_name,
                columns=required_columns,
                filter_mode=filter_mode,
                from_dt=from_dt,
                to_dt=to_dt,
                rack_list=rack_list,
                column_types=column_types
            )
            
            # REMOVED: Double filtering - SparkFileProcessor handles rack filtering optimally with predicate pushdown
            # Trust the SparkFileProcessor to handle rack filtering correctly
            
            # Convert to individual column responses
            responses = {}
            for request in column_requests:
                response_key = self._generate_response_key(request)
                column_data = table_data.get(request.columnName, [])
                
                responses[response_key] = ColumnResponse(
                    columnName=request.columnName,
                    columnType=request.columnType,
                    tableName=request.tableName,
                    siteName=request.siteName,
                    dataSource=column_data
                )
            
            total_rows = len(table_data.get('DateTime', table_data.get(column_names[0], [])))
            logger.info(f"[TABLE_PROCESSOR] Successfully processed {len(responses)} columns, {total_rows} rows")
            return responses
            
        except Exception as e:
            logger.error(f"[TABLE_PROCESSOR] Error processing table {site_name}/{table_name}: {e}")
            raise e
    
    # REMOVED: _apply_rack_filter_to_data method
    # This method is no longer needed as rack filtering is handled optimally
    # by SparkFileProcessor using Spark SQL predicate pushdown
    
    def _generate_response_key(self, request: ColumnRequest) -> str:
        """Generate unique key for response mapping."""
        return f"{request.siteName}_{request.tableName}_{request.columnName}"
    
    def _create_error_responses_for_site(
        self, 
        site_name: str, 
        site_tables: Dict[str, List[ColumnRequest]], 
        error_message: str
    ) -> Dict[str, ColumnResponse]:
        """Create error responses for all requests in a failed site."""
        error_responses = {}
        
        for table_name, requests in site_tables.items():
            table_errors = self._create_error_responses_for_table(
                site_name, table_name, requests, error_message
            )
            error_responses.update(table_errors)
        
        return error_responses
    
    def _create_error_responses_for_table(
        self, 
        site_name: str, 
        table_name: str, 
        requests: List[ColumnRequest], 
        error_message: str
    ) -> Dict[str, ColumnResponse]:
        """Create error responses for all requests in a failed table."""
        error_responses = {}
        
        for request in requests:
            response_key = self._generate_response_key(request)
            error_responses[response_key] = ColumnResponse.create_error_response(
                request, error_message
            )
        
        return error_responses
    
    def _reorder_responses_to_match_requests(
        self,
        responses: Dict[str, ColumnResponse],
        original_requests: List[ColumnRequest]
    ) -> List[ColumnResponse]:
        """Reorder responses to match original request order."""
        ordered_responses = []
        
        for request in original_requests:
            response_key = self._generate_response_key(request)
            if response_key in responses:
                ordered_responses.append(responses[response_key])
            else:
                # Create missing response (shouldn't happen, but safety check)
                logger.warning(f"Missing response for {response_key}")
                ordered_responses.append(
                    ColumnResponse.create_error_response(request, "Missing response")
                )
        
        return ordered_responses
    
    def _fallback_to_existing_service(
        self,
        column_requests: List[ColumnRequest],
        from_date: Optional[str],
        to_date: Optional[str],
        rack_list: Optional[List[str]]
    ) -> List[ColumnResponse]:
        """Fallback to existing service architecture on critical failures."""
        logger.warning("[MULTI_SITE_SERVICE] Falling back to existing service architecture")
        
        fallback_responses = []
        
        for request in column_requests:
            try:
                # Use existing FastMetadataService as fallback
                from infrastructure.services.analysis.data_operations import AnalysisDataOperations
                data_ops = AnalysisDataOperations()
                
                result = data_ops.get_parquet_columns(
                    table_id=request.tableName,
                    site_id=request.siteName,
                    from_date=from_date,
                    to_date=to_date
                )
                
                # Extract data for specific column
                column_data = []
                if 'columns' in result:
                    for col in result['columns']:
                        if col.get('name') == request.columnName:
                            column_data = col.get('dataSource', [])
                            break
                
                # Note: Rack filtering not implemented in fallback service
                # The fallback service is a last resort and may not have rack filtering capabilities
                if rack_list:
                    logger.warning(f"[FALLBACK] Rack filtering requested ({rack_list}) but not available in fallback service")
                
                fallback_responses.append(ColumnResponse.from_request(request, column_data))
                
            except Exception as e:
                logger.error(f"Fallback also failed for {request.columnName}: {e}")
                fallback_responses.append(
                    ColumnResponse.create_error_response(request, f"Fallback error: {str(e)}")
                )
        
        return fallback_responses
