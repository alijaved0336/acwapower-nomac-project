"""
Column Operations Module
Handles column metadata operations and filtering with Redis caching.
"""
import logging
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig

logger = logging.getLogger(__name__)


class ColumnOperations:
    """Handles column metadata operations with Redis caching"""
    
    def __init__(self):
        self.cache_service = CacheService()

    def get_parquet_columns(
        self,
        table_id: str,
        site_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: Optional[str] = "Datetime",
        date_format: Optional[str] = None,
        include_samples: bool = True,
        exclude_calculated: bool = True,
        exclude_null: bool = True,
        include_performance: bool = False
    ) -> Dict:
        """
        Get parquet columns with enhanced filtering options and Redis caching.
        Returns ALL data rows for live analysis (no sample size limitation).
        """
        try:
            # Generate cache key based on all parameters
            cache_key = self._generate_column_cache_key(
                site_id, table_id, from_date, to_date, date_column,
                include_samples, exclude_calculated, exclude_null
            )
            
            # Check Redis cache first
            cached_result = self.cache_service.get(cache_key, prefix="column_metadata")
            if cached_result:
                logger.info(f"Cache HIT: Retrieved column metadata for {site_id}/{table_id} from Redis")
                # Add performance flag handling for cached results
                if not include_performance:
                    cached_result.pop('performance', None)
                    if 'date_filter' in cached_result:
                        cached_result['date_filter'].pop('processing_time_seconds', None)
                return cached_result
            
            logger.info(f"Cache MISS: Processing column metadata for {site_id}/{table_id}")
            
            # Try fast metadata service first (bypasses Spark completely)
            from infrastructure.services.fastMetadataService import FastMetadataService

            fast_service = FastMetadataService()
            result = fast_service.get_fast_column_metadata(
                site_id=site_id,
                table_id=table_id,
                from_date=from_date,
                to_date=to_date,
                max_rows=None  # No limit - return ALL data for live analysis
            )

            logger.info(f"Fast metadata service completed in {result.get('performance', {}).get('processing_time_seconds', 'unknown')}s")

            # Apply filtering to clean up the response
            if 'columns' in result:
                result['columns'] = self._filter_columns(
                    result['columns'],
                    include_samples=include_samples,
                    exclude_calculated=exclude_calculated,
                    exclude_null=exclude_null
                )

            # Cache the result (10 minute TTL for column metadata)
            cache_success = self.cache_service.set(
                cache_key, 
                result, 
                ttl=CacheConfig.MEDIUM_TTL // 2,  # 7.5 minutes
                prefix="column_metadata"
            )
            
            if cache_success:
                logger.info(f"Cached column metadata for {site_id}/{table_id}")

            # Remove performance data if not requested
            if not include_performance:
                result.pop('performance', None)
                if 'date_filter' in result:
                    result['date_filter'].pop('processing_time_seconds', None)

            return result

        except Exception as fast_error:
            logger.warning(f"Fast metadata service failed: {fast_error}")

            # Fallback to Spark-based approach (also check cache for fallback)
            fallback_cache_key = f"{cache_key}_spark_fallback"
            cached_fallback = self.cache_service.get(fallback_cache_key, prefix="column_metadata")
            
            if cached_fallback:
                logger.info(f"Cache HIT: Retrieved Spark fallback result for {site_id}/{table_id}")
                return cached_fallback
            
            result = self._get_columns_with_spark(
                table_id=table_id,
                site_id=site_id,
                from_date=from_date,
                to_date=to_date,
                date_column=date_column,
                include_samples=include_samples,
                exclude_calculated=exclude_calculated,
                exclude_null=exclude_null,
                include_performance=include_performance
            )
            
            # Cache fallback result too (shorter TTL)
            self.cache_service.set(
                fallback_cache_key, 
                result, 
                ttl=CacheConfig.DEFAULT_TTL,  # 5 minutes
                prefix="column_metadata"
            )
            
            return result
    
    def _generate_column_cache_key(
        self, 
        site_id: str, 
        table_id: str, 
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: Optional[str] = "Datetime",
        include_samples: bool = True,
        exclude_calculated: bool = True,
        exclude_null: bool = True
    ) -> str:
        """Generate cache key for column metadata"""
        key_components = [
            site_id,
            table_id,
            from_date or "no_from",
            to_date or "no_to",
            date_column,
            str(include_samples),
            str(exclude_calculated),
            str(exclude_null)
        ]
        
        key_string = "_".join(key_components)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:12]
        
        return f"columns_{site_id}_{table_id}_{key_hash}"

    def get_bulk_parquet_columns(
        self,
        table_requests: List[Dict],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: Optional[str] = "Datetime",
        include_samples: bool = True,
        exclude_calculated: bool = True,
        exclude_null: bool = True,
        include_performance: bool = False
    ) -> Dict:
        """
        Get column metadata for multiple tables using optimized approach.
        Uses FastMetadataService (PyArrow direct) with SparkSQL fallback.
        """
        try:
            logger.info(f"Processing bulk columns request for {len(table_requests)} tables")
            
            # Validate input
            if not table_requests or not isinstance(table_requests, list):
                raise ValueError("table_requests must be a non-empty list")
            
            # Limit bulk operations to prevent timeout
            MAX_BULK_TABLES = 50
            if len(table_requests) > MAX_BULK_TABLES:
                raise ValueError(f"Maximum {MAX_BULK_TABLES} tables allowed per bulk request")
            
            results = []
            successful_count = 0
            failed_count = 0
            total_columns = 0
            
            # Process each table request
            for i, request in enumerate(table_requests):
                try:
                    # Validate request structure
                    if not isinstance(request, dict):
                        raise ValueError(f"Request {i} must be a dictionary")
                    
                    site_name = request.get('siteName')
                    table_name = request.get('tableName')
                    
                    if not site_name or not table_name:
                        raise ValueError(f"Request {i} missing 'siteName' or 'tableName'")
                    
                    logger.info(f"Processing table {i+1}/{len(table_requests)}: {site_name}/{table_name}")
                    
                    # Get column data for this table
                    table_result = self.get_parquet_columns(
                        table_id=table_name,
                        site_id=site_name,
                        from_date=from_date,
                        to_date=to_date,
                        date_column=date_column,
                        include_samples=include_samples,
                        exclude_calculated=exclude_calculated,
                        exclude_null=exclude_null,
                        include_performance=include_performance
                    )
                    
                    # Transform to match expected response format
                    columns = table_result.get('columns', [])
                    transformed_columns = []
                    
                    for col in columns:
                        transformed_columns.append({
                            "columnName": col.get('name', ''),
                            "columnType": col.get('type', ''),
                            "tableName": table_name,
                            "siteName": site_name
                        })
                    
                    results.extend(transformed_columns)
                    successful_count += 1
                    total_columns += len(transformed_columns)
                    
                    logger.info(f"Successfully processed {site_name}/{table_name}: {len(transformed_columns)} columns")
                    
                except Exception as table_error:
                    logger.error(f"Failed to process table {i+1} ({request.get('siteName', 'unknown')}/{request.get('tableName', 'unknown')}): {str(table_error)}")
                    failed_count += 1
                    continue
            
            # Build response
            response_data = {
                "success": successful_count > 0,
                "message": f"Processed {successful_count} tables successfully, {failed_count} failed",
                "data": results,
                "summary": {
                    "total_tables_requested": len(table_requests),
                    "successful_tables": successful_count,
                    "failed_tables": failed_count,
                    "total_columns_retrieved": total_columns,
                    "filters_applied": {
                        "from_date": from_date,
                        "to_date": to_date,
                        "date_column": date_column,
                        "include_samples": include_samples,
                        "exclude_calculated": exclude_calculated,
                        "exclude_null": exclude_null
                    }
                }
            }
            
            logger.info(f"Bulk columns request completed: {successful_count} successful, {failed_count} failed, {total_columns} total columns")
            return response_data
            
        except Exception as e:
            logger.error(f"Error in bulk columns request: {str(e)}")
            return {
                "success": False,
                "message": f"Bulk columns request failed: {str(e)}",
                "data": [],
                "summary": {
                    "total_tables_requested": len(table_requests) if table_requests else 0,
                    "successful_tables": 0,
                    "failed_tables": len(table_requests) if table_requests else 0,
                    "total_columns_retrieved": 0,
                    "filters_applied": {
                        "from_date": from_date,
                        "to_date": to_date,
                        "date_column": date_column,
                        "include_samples": include_samples,
                        "exclude_calculated": exclude_calculated,
                        "exclude_null": exclude_null
                    }
                }
            }

    def _filter_columns(self, columns: List[Dict], include_samples: bool = True, 
                       exclude_calculated: bool = True, exclude_null: bool = True) -> List[Dict]:
        """
        Filter columns based on specified criteria.
        """
        filtered_columns = []
        
        for column in columns:
            # Skip null type columns if requested
            if exclude_null and column.get('type', '').lower() == 'null':
                continue
            
            # Skip calculated columns if requested
            if exclude_calculated:
                name = column.get('name', '')
                if any(name.endswith(suffix) for suffix in ['_DQ', '_RAW', '_CALC', '_DERIVED']):
                    continue
            
            # Remove data samples if not requested
            if not include_samples and 'dataSource' in column:
                column = column.copy()  # Don't modify original
                column['dataSource'] = []  # Return empty array instead of removing completely
            
            filtered_columns.append(column)
        
        return filtered_columns

    def _get_columns_with_spark(
        self,
        table_id: str,
        site_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        date_column: str,
        include_samples: bool,
        exclude_calculated: bool,
        exclude_null: bool,
        include_performance: bool
    ) -> Dict:
        """
        Get columns using Spark-based operations (fallback method).
        """
        # Import here to avoid circular imports
        from .spark_operations import SparkOperations
        spark_ops = SparkOperations()
        return spark_ops.get_columns_with_spark(
            table_id=table_id,
            site_id=site_id,
            from_date=from_date,
            to_date=to_date,
            date_column=date_column,
            include_samples=include_samples,
            exclude_calculated=exclude_calculated,
            exclude_null=exclude_null,
            include_performance=include_performance
        )
