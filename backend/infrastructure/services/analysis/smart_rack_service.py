"""
Smart Rack Service - Intelligent column detection with data validation
Uses data inspection to identify proper rack columns.
"""
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime

from infrastructure.utils.azure.blobStorageClient import BlobStorageClient
from infrastructure.services.cache_service import CacheService
from infrastructure.services.spark_singleton import get_spark_session
from .spark_connection_manager import get_optimized_spark_session
from config.redis_cache_config import CacheConfig

logger = logging.getLogger(__name__)


class SmartRackService:
    """Smart rack service with intelligent column detection"""

    def __init__(self):
        self.blob_client = BlobStorageClient()
        self.cache_service = CacheService()
        self._spark = None  # Lazy initialization
        
        # Legacy in-memory caches (keeping for backward compatibility)
        self._rack_column_cache = {}
        self._rack_values_cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 30 * 60  # 30 minutes in seconds
    
    @property
    def spark(self):
        """Get optimized Spark session from connection manager"""
        if self._spark is None:
            self._spark = get_optimized_spark_session()
        return self._spark

    def get_unique_racks_smart(self, site_id: str, table_ids: List[str]) -> Dict:
        """
        Smart rack retrieval with intelligent column detection using Spark SQL and Redis caching.
        """
        try:
            start_time = datetime.now()
            logger.info(f"Getting unique racks for site {site_id} from {len(table_ids)} tables (optimized with Spark + Redis)")
            
            # Validate inputs
            if not site_id or not table_ids:
                raise ValueError("site_id and table_ids are required")
            
            if not isinstance(table_ids, list) or len(table_ids) == 0:
                raise ValueError("table_ids must be a non-empty list")
            
            # Increased limit since we're using Spark SQL (much faster)
            MAX_TABLES = 15
            if len(table_ids) > MAX_TABLES:
                raise ValueError(f"Maximum {MAX_TABLES} tables allowed per request")
            
            # Check Redis cache first
            cache_key = self._generate_rack_cache_key(site_id, table_ids)
            logger.info(f"SmartRackService: Checking cache with key: {cache_key}")
            cached_result = self.cache_service.get(cache_key, prefix="rack_data")
            
            if cached_result:
                cache_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"SmartRackService Cache HIT: Retrieved {len(cached_result.get('racks', []))} racks for {site_id} from Redis cache in {cache_time:.3f}s")
                return cached_result
            
            logger.info(f"Cache MISS: Processing racks for {site_id} with Spark SQL")
            
            all_racks = []
            successful_tables = 0
            failed_tables = 0
            
            # Process tables with optimized Spark SQL approach (with per-table caching)
            for table_id in table_ids:
                try:
                    # Check per-table cache first
                    table_cache_key = f"table_racks_{site_id}_{table_id}"
                    cached_table_racks = self.cache_service.get(table_cache_key, prefix="rack_data")
                    
                    if cached_table_racks:
                        all_racks.extend(cached_table_racks)
                        successful_tables += 1
                        logger.info(f"Cache HIT: Retrieved {len(cached_table_racks)} racks for table {table_id} from cache")
                        continue
                    
                    # TEMPORARILY DISABLED: Process with Spark SQL (has column resolution issues)
                    # Skip Spark SQL and use blob-based approach directly
                    logger.info(f"Using blob-based approach for {table_id} (Spark SQL disabled due to column resolution issues)")
                    
                    # Use blob-based processing directly
                    table_racks = self._process_table_smart(site_id, table_id)
                    if table_racks:
                        all_racks.extend(table_racks)
                        successful_tables += 1
                        
                        # Cache results (15 minute TTL)
                        self.cache_service.set(
                            table_cache_key, 
                            table_racks, 
                            ttl=900,  # 15 minutes
                            prefix="rack_data"
                        )
                        
                        logger.info(f"Successfully processed table {table_id} with {len(table_racks)} racks using blob-based approach")
                    else:
                        # No results from blob-based approach
                        failed_tables += 1
                        logger.error(f"Failed to process table {table_id} with blob-based approach")
                except Exception as e:
                    failed_tables += 1
                    logger.error(f"Error processing table {table_id} with blob-based approach: {str(e)}")
                    # Try fallback method
                    try:
                        table_racks_fallback = self._process_table_smart(site_id, table_id)
                        if table_racks_fallback:
                            all_racks.extend(table_racks_fallback)
                            successful_tables += 1
                            failed_tables -= 1  # Correct the count since we succeeded with fallback
                            
                            # Cache fallback results
                            table_cache_key = f"table_racks_{site_id}_{table_id}"
                            self.cache_service.set(
                                table_cache_key, 
                                table_racks_fallback, 
                                ttl=900,  # 15 minutes
                                prefix="rack_data"
                            )
                            
                            logger.info(f"Fallback successful for table {table_id} with {len(table_racks_fallback)} racks")
                    except Exception as fallback_e:
                        logger.error(f"Fallback also failed for table {table_id}: {str(fallback_e)}")
            
            # Remove duplicates efficiently
            unique_racks = self._deduplicate_racks_smart(all_racks)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "racks": unique_racks
            }
            
            # Cache the result (15 minute TTL)
            logger.info(f"SmartRackService: Attempting to cache result for {site_id} with key: {cache_key}")
            cache_success = self.cache_service.set(
                cache_key, 
                result, 
                ttl=CacheConfig.MEDIUM_TTL,  # 15 minutes
                prefix="rack_data"
            )
            
            if cache_success:
                logger.info(f"SmartRackService SUCCESS: Cached rack results for {site_id} (TTL: {CacheConfig.MEDIUM_TTL}s)")
            else:
                logger.error(f"SmartRackService FAILED: Could not cache rack results for {site_id}")
            
            logger.info(f"Spark SQL processing completed in {processing_time:.2f}s: {len(unique_racks)} unique racks from {successful_tables} tables")
            return result
            
        except Exception as e:
            logger.error(f"Error in optimized rack retrieval: {str(e)}")
            raise e
    
    def _generate_rack_cache_key(self, site_id: str, table_ids: List[str]) -> str:
        """Generate cache key for rack results"""
        import hashlib
        
        # Sort table_ids for consistent cache keys
        sorted_tables = sorted(table_ids)
        key_string = f"{site_id}_{'_'.join(sorted_tables)}"
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:12]
        
        return f"racks_{site_id}_{key_hash}"
    
    def _process_table_with_spark(self, site_id: str, table_id: str) -> List[Dict]:
        """
        Process a single table using optimized Spark SQL instead of blob downloads.
        Much faster than the original blob-based approach.
        """
        try:
            logger.info(f"Processing table {site_id}/{table_id} with Spark SQL")
            
            # Build the table path for Spark
            table_path = f"wasbs://swro@mpcswrosg.blob.core.windows.net/tables/gold/{site_id}/{table_id}/"
            
            # Try to read the table with Spark
            try:
                df = self.spark.read.parquet(table_path)
                logger.info(f"Successfully loaded table {table_id} with Spark")
            except Exception as e:
                logger.warning(f"Could not load table {table_id} with Spark: {e}")
                return []
            
            # Get column names and find potential rack columns
            columns = df.columns
            logger.info(f"Table {table_id} has {len(columns)} columns: {columns}")
            
            # Debug: Show first few rows to understand the data structure
            try:
                sample_data = df.limit(3).collect()
                logger.info(f"Sample data from {table_id}: {[row.asDict() for row in sample_data]}")
            except Exception as e:
                logger.warning(f"Could not get sample data: {e}")
            
            # Find the best rack column using smart detection
            rack_column = self._find_best_rack_column_from_columns(columns)
            if not rack_column:
                logger.warning(f"No suitable rack column found in table {table_id}. Available columns: {columns}")
                return []
            
            # Verify the column actually exists in the DataFrame
            if rack_column not in columns:
                logger.error(f"Selected column '{rack_column}' not found in DataFrame columns: {columns}")
                # Try to find a similar column
                similar_columns = [col for col in columns if 'rack' in col.lower()]
                if similar_columns:
                    logger.info(f"Found similar columns: {similar_columns}")
                    rack_column = similar_columns[0]
                    logger.info(f"Using similar column '{rack_column}' instead")
                else:
                    return []
            
            logger.info(f"Using column '{rack_column}' for rack detection in table {table_id}")
            
            # Use Spark SQL to get unique rack values efficiently
            try:
                # Register the DataFrame as a temporary view
                temp_view_name = f"temp_{site_id}_{table_id}".replace("-", "_").replace(".", "_")
                df.createOrReplaceTempView(temp_view_name)
                
                # Execute optimized SQL query to get unique non-null rack values
                # Use backticks to handle column names with special characters or case sensitivity
                escaped_column = f"`{rack_column}`"
                sql_query = f"""
                    SELECT DISTINCT {escaped_column} as rack_value
                    FROM {temp_view_name}
                    WHERE {escaped_column} IS NOT NULL 
                    AND TRIM({escaped_column}) != ''
                    AND UPPER(TRIM({escaped_column})) NOT IN ('NULL', 'NAN', 'NONE', '')
                    ORDER BY {escaped_column}
                    LIMIT 100
                """
                
                logger.info(f"Executing SQL query for table {table_id}: {sql_query}")
                result_df = self.spark.sql(sql_query)
                rack_values = [row.rack_value for row in result_df.collect()]
                logger.info(f"Spark SQL returned {len(rack_values)} unique rack values for table {table_id}")
                
                # Clean up temporary view
                self.spark.catalog.dropTempView(temp_view_name)
                
                logger.info(f"Found {len(rack_values)} unique rack values in table {table_id}")
                
                if len(rack_values) == 0:
                    logger.warning(f"No rack values found in column '{rack_column}' for table {table_id}")
                
                # Build result format
                table_racks = []
                for rack_value in rack_values:
                    if rack_value and str(rack_value).strip():
                        table_racks.append({
                            "rackLabel": str(rack_value).strip(),
                            "siteName": site_id,
                            "tableName": table_id,
                            "rackValue": str(rack_value).strip()
                        })
                
                return table_racks
                
            except Exception as e:
                logger.error(f"Error executing Spark SQL for table {table_id} with column '{rack_column}': {e}")
                # Try to clean up the temporary view if it exists
                try:
                    self.spark.catalog.dropTempView(temp_view_name)
                except:
                    pass
                
                # Try alternative column names if the first attempt failed
                alternative_columns = [col for col in columns if 'rack' in col.lower() and col != rack_column]
                if alternative_columns:
                    logger.info(f"Trying alternative columns: {alternative_columns}")
                    for alt_column in alternative_columns:
                        try:
                            # Re-register the DataFrame as a temporary view
                            temp_view_name = f"temp_{site_id}_{table_id}_alt".replace("-", "_").replace(".", "_")
                            df.createOrReplaceTempView(temp_view_name)
                            
                            escaped_column = f"`{alt_column}`"
                            sql_query = f"""
                                SELECT DISTINCT {escaped_column} as rack_value
                                FROM {temp_view_name}
                                WHERE {escaped_column} IS NOT NULL 
                                AND TRIM({escaped_column}) != ''
                                AND UPPER(TRIM({escaped_column})) NOT IN ('NULL', 'NAN', 'NONE', '')
                                ORDER BY {escaped_column}
                                LIMIT 100
                            """
                            
                            logger.info(f"Trying alternative SQL query with column '{alt_column}': {sql_query}")
                            result_df = self.spark.sql(sql_query)
                            rack_values = [row.rack_value for row in result_df.collect()]
                            
                            # Clean up temporary view
                            self.spark.catalog.dropTempView(temp_view_name)
                            
                            if rack_values:
                                logger.info(f"Successfully found {len(rack_values)} rack values using alternative column '{alt_column}'")
                                break
                                
                        except Exception as alt_e:
                            logger.warning(f"Alternative column '{alt_column}' also failed: {alt_e}")
                            try:
                                self.spark.catalog.dropTempView(temp_view_name)
                            except:
                                pass
                            continue
                    else:
                        # All alternatives failed
                        return []
                else:
                    return []
                
        except Exception as e:
            logger.error(f"Error processing table {table_id} with Spark: {str(e)}")
            return []
    
    def _find_best_rack_column_from_columns(self, columns: List[str]) -> Optional[str]:
        """
        Find the best rack column from column names using intelligent scoring.
        Optimized version that doesn't need to read data.
        """
        if not columns:
            return None
        
        # Score each column based on name patterns only (faster)
        column_scores = {}
        
        for column_name in columns:
            score = self._score_column_name(column_name.lower())
            column_scores[column_name] = score
            logger.debug(f"Column '{column_name}' scored {score}")
        
        # Find the column with the highest score
        if not column_scores:
            return None
        
        best_column = max(column_scores.items(), key=lambda x: x[1])
        if best_column[1] > 0:  # Only return if score is positive
            logger.info(f"Selected column '{best_column[0]}' with score {best_column[1]}")
            return best_column[0]
        
        return None

    def _process_table_smart(self, site_id: str, table_id: str) -> List[Dict]:
        """
        Process a single table using smart column detection with optimized caching.
        """
        try:
            # Check table-level cache first
            table_cache_key = f"table_racks_{site_id}_{table_id}"
            cached_table_racks = self.cache_service.get(table_cache_key, prefix="rack_data")
            if cached_table_racks:
                logger.info(f"Table cache HIT: Retrieved {len(cached_table_racks)} racks for table {table_id}")
                return cached_table_racks
            
            logger.info(f"Table cache MISS: Processing table {table_id} with blob-based approach")
            
            # Get the first parquet file
            blob_prefix = f"tables/gold/{site_id}/{table_id}/"
            parquet_blobs = self.blob_client.list_parquet_files(blob_prefix)
            if not parquet_blobs:
                logger.warning(f"No parquet files found for {site_id}/{table_id}")
                return []
            
            blob = parquet_blobs[0]
            
            # Get all columns and their sample data
            columns_data = self._get_columns_with_samples(blob)
            if not columns_data:
                return []
            
            # Find the best rack column using smart detection
            rack_column = self._find_best_rack_column_smart(columns_data)
            if not rack_column:
                logger.warning(f"No suitable rack column found in table {table_id}")
                return []
            
            # Get unique rack values
            rack_values = self._get_unique_values_from_column(columns_data[rack_column])
            if not rack_values:
                logger.warning(f"No valid rack values found in column {rack_column} of table {table_id}")
                return []
            
            # Build result
            table_racks = []
            for rack_value in rack_values:
                table_racks.append({
                    "rackLabel": rack_value,
                    "siteName": site_id,
                    "tableName": table_id,
                    "rackValue": rack_value
                })
            
            # Cache the table results (30 minute TTL)
            self.cache_service.set(
                table_cache_key, 
                table_racks, 
                ttl=1800,  # 30 minutes
                prefix="rack_data"
            )
            logger.info(f"Cached {len(table_racks)} racks for table {table_id}")
            
            return table_racks
            
        except Exception as e:
            logger.error(f"Error processing table {table_id}: {str(e)}")
            return []

    def _get_columns_with_samples(self, blob) -> Dict[str, List]:
        """
        Get all columns with sample data for analysis.
        """
        try:
            import pyarrow.parquet as pq
            import io
            
            blob_client = self.blob_client.get_blob_client(blob.name)
            blob_data = blob_client.download_blob().readall()
            parquet_file = pq.ParquetFile(io.BytesIO(blob_data))
            
            # Read a small sample of all columns
            table = parquet_file.read(use_threads=True)
            
            # Convert to dictionary of column_name -> sample_values
            columns_data = {}
            for column_name in table.column_names:
                sample_values = table[column_name].to_pylist()[:100]  # First 100 values
                columns_data[column_name] = sample_values
            
            return columns_data
            
        except Exception as e:
            logger.warning(f"Error getting columns with samples: {str(e)}")
            return {}

    def _find_best_rack_column_smart(self, columns_data: Dict[str, List]) -> Optional[str]:
        """
        Find the best rack column using intelligent analysis of the data.
        """
        if not columns_data:
            return None
        
        # Score each column based on how likely it is to be a rack column
        column_scores = {}
        
        for column_name, sample_values in columns_data.items():
            score = self._score_column_for_racks(column_name, sample_values)
            column_scores[column_name] = score
            logger.debug(f"Column '{column_name}' scored {score}")
        
        # Find the column with the highest score
        if not column_scores:
            return None
        
        best_column = max(column_scores.items(), key=lambda x: x[1])
        if best_column[1] > 0:  # Only return if score is positive
            logger.info(f"Selected column '{best_column[0]}' with score {best_column[1]}")
            return best_column[0]
        
        return None

    def _score_column_for_racks(self, column_name: str, sample_values: List) -> float:
        """
        Score a column based on how likely it is to contain rack identifiers.
        Returns a score from 0 to 100.
        """
        if not sample_values:
            return 0.0
        
        score = 0.0
        column_lower = column_name.lower()
        
        # 1. Name-based scoring (40% of total score)
        name_score = self._score_column_name(column_lower)
        score += name_score * 0.4
        
        # 2. Data pattern scoring (60% of total score)
        data_score = self._score_data_patterns(sample_values)
        score += data_score * 0.6
        
        return min(score, 100.0)  # Cap at 100

    def _score_column_name(self, column_name: str) -> float:
        """
        Score based on column name patterns.
        """
        # Explicit rack patterns (highest score)
        explicit_rack_patterns = ['rack', 'rack_id', 'rackid', 'rack_name', 'rackname']
        if any(pattern in column_name for pattern in explicit_rack_patterns):
            return 100.0
        
        # Good equipment patterns
        good_patterns = ['unit', 'station', 'equipment', 'tank', 'vessel', 'pump', 'motor', 'generator']
        if any(pattern in column_name for pattern in good_patterns):
            return 80.0
        
        # ID patterns
        if column_name.endswith('_id') or column_name.startswith('id_') or column_name == 'id':
            return 70.0
        
        # Bad patterns (negative score)
        bad_patterns = {
            'datetime', 'timestamp', 'date', 'time', 'start_time', 'end_time', 'created_at', 'updated_at',
            'mode', 'status', 'state', 'condition', 'type', 'category', 'class', 'group', 'level',
            'value', 'measurement', 'reading', 'data', 'result', 'output', 'input', 'signal',
            'pressure', 'temperature', 'flow', 'speed', 'voltage', 'current', 'power', 'frequency',
            'maintenance', 'operation', 'process', 'system', 'control', 'monitor', 'alarm', 'warning',
            'validated', 'confirmed', 'approved', 'rejected', 'pending', 'active', 'inactive',
            'duration', 'hours', 'minutes', 'seconds', 'count', 'total', 'sum', 'average', 'max', 'min'
        }
        
        if any(bad_pattern in column_name for bad_pattern in bad_patterns):
            return -50.0
        
        # Neutral score for unknown patterns
        return 20.0

    def _score_data_patterns(self, sample_values: List) -> float:
        """
        Score based on data patterns in the sample values.
        """
        if not sample_values:
            return 0.0
        
        score = 0.0
        valid_values = [v for v in sample_values if v is not None and str(v).strip() != '']
        
        if not valid_values:
            return 0.0
        
        # Check for rack-like patterns
        rack_patterns = 0
        timestamp_patterns = 0
        numeric_patterns = 0
        text_patterns = 0
        
        for value in valid_values[:50]:  # Check first 50 values
            str_value = str(value).strip()
            
            # Rack-like patterns (RACK_01, Unit_A, Station_1, etc.)
            if any(pattern in str_value.upper() for pattern in ['RACK_', 'UNIT_', 'STATION_', 'TANK_', 'PUMP_']):
                rack_patterns += 1
            
            # Timestamp patterns
            if any(char in str_value for char in ['-', ':', '+']) and len(str_value) > 15:
                timestamp_patterns += 1
            
            # Numeric patterns (duration, measurements, etc.)
            try:
                float(str_value)
                numeric_patterns += 1
            except ValueError:
                pass
            
            # Text patterns (maintenance modes, statuses, etc.)
            if str_value.isalpha() or any(word in str_value.lower() for word in ['maintenance', 'operation', 'mode', 'status']):
                text_patterns += 1
        
        total_checked = len(valid_values[:50])
        
        # Calculate scores based on patterns
        if rack_patterns > 0:
            score += (rack_patterns / total_checked) * 100  # High score for rack patterns
        
        if timestamp_patterns > total_checked * 0.3:  # If >30% are timestamps
            score -= 50  # Heavy penalty for timestamp columns
        
        if numeric_patterns > total_checked * 0.7:  # If >70% are numeric
            score -= 30  # Penalty for numeric columns (likely measurements)
        
        if text_patterns > total_checked * 0.5:  # If >50% are text patterns
            score -= 20  # Penalty for text columns (likely status/mode)
        
        # Bonus for reasonable length and format
        avg_length = sum(len(str(v)) for v in valid_values[:20]) / min(20, len(valid_values))
        if 3 <= avg_length <= 20:  # Reasonable length for rack names
            score += 10
        
        return max(score, 0.0)  # Don't go below 0

    def _get_unique_values_from_column(self, sample_values: List) -> List[str]:
        """
        Get unique values from a column, filtering out invalid ones.
        """
        if not sample_values:
            return []
        
        unique_values = set()
        for value in sample_values:
            if value is not None and str(value).strip() != '':
                str_value = str(value).strip()
                if str_value.lower() not in ['nan', 'null', 'none', '']:
                    unique_values.add(str_value)
        
        return list(unique_values)

    def _deduplicate_racks_smart(self, all_racks: List[Dict]) -> List[Dict]:
        """
        Smart deduplication of racks.
        """
        seen_rack_ids = set()
        unique_racks = []
        
        for rack in all_racks:
            rack_id = rack["rackValue"]
            if rack_id not in seen_rack_ids:
                unique_racks.append(rack)
                seen_rack_ids.add(rack_id)
        
        return unique_racks
