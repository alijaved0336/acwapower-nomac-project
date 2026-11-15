"""
ClickHouse Rack Service - Intelligent rack detection and retrieval using ClickHouse as data source
This service provides the same interface as SmartRackService but queries ClickHouse instead of ADLS/Spark.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig
from constants import (
    ClickHouseServiceConfig,
    ClickHouseColumnPatterns,
    ClickHouseDataValidation
)

logger = logging.getLogger(__name__)


class ClickHouseRackService:
    """ClickHouse-based rack service with intelligent column detection"""

    def __init__(self):
        self.repository = ClickHouseRepository()
        self.cache_service = CacheService()

    def get_unique_racks_from_clickhouse(self, site_id: str, table_ids: List[str]) -> Dict:
        """
        Get unique racks from ClickHouse for specified site and tables.

        Args:
            site_id (str): Site identifier
            table_ids (List[str]): List of table identifiers

        Returns:
            Dict: Dictionary with racks list

        Raises:
            Exception: If data retrieval fails
        """
        try:
            start_time = datetime.now()
            logger.info(f"ClickHouseRackService: Getting unique racks for site {site_id} from {len(table_ids)} tables")

            # Validate inputs
            if not site_id or not table_ids:
                raise ValueError("site_id and table_ids are required")

            if not isinstance(table_ids, list) or len(table_ids) == 0:
                raise ValueError("table_ids must be a non-empty list")

            # Limit to prevent excessive load
            if len(table_ids) > ClickHouseServiceConfig.MAX_TABLES_PER_REQUEST:
                raise ValueError(f"Maximum {ClickHouseServiceConfig.MAX_TABLES_PER_REQUEST} tables allowed per request")

            # Check Redis cache first
            cache_key = self._generate_rack_cache_key(site_id, table_ids)
            logger.info(f"ClickHouseRackService: Checking cache with key: {cache_key}")
            cached_result = self.cache_service.get(cache_key, prefix=ClickHouseServiceConfig.CACHE_PREFIX_RACK_DATA)

            if cached_result:
                cache_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"ClickHouseRackService Cache HIT: Retrieved {len(cached_result.get('racks', []))} racks for {site_id} from Redis cache in {cache_time:.3f}s")
                return cached_result

            logger.info(f"Cache MISS: Processing racks for {site_id} with ClickHouse")

            all_racks = []
            successful_tables = 0
            failed_tables = 0

            # Process tables
            for table_id in table_ids:
                try:
                    # Check per-table cache first
                    table_cache_key = f"{ClickHouseServiceConfig.CACHE_PREFIX_TABLE_RACKS}{site_id}_{table_id}"
                    cached_table_racks = self.cache_service.get(table_cache_key, prefix=ClickHouseServiceConfig.CACHE_PREFIX_RACK_DATA)

                    if cached_table_racks:
                        all_racks.extend(cached_table_racks)
                        successful_tables += 1
                        logger.info(f"ClickHouse Cache HIT: Retrieved {len(cached_table_racks)} racks for table {table_id} from cache")
                        continue

                    # Process with ClickHouse
                    table_racks = self._process_table_clickhouse(site_id, table_id)
                    if table_racks:
                        all_racks.extend(table_racks)
                        successful_tables += 1

                        # Cache results (15 minute TTL)
                        self.cache_service.set(
                            table_cache_key,
                            table_racks,
                            ttl=CacheConfig.MEDIUM_TTL,  # 15 minutes
                            prefix=ClickHouseServiceConfig.CACHE_PREFIX_RACK_DATA
                        )

                        logger.info(f"ClickHouse: Successfully processed table {table_id} with {len(table_racks)} racks")
                    else:
                        failed_tables += 1
                        logger.warning(f"ClickHouse: No racks found for table {table_id}")

                except Exception as e:
                    failed_tables += 1
                    logger.error(f"ClickHouse: Error processing table {table_id}: {str(e)}")
                    continue

            # Remove duplicates efficiently
            unique_racks = self._deduplicate_racks_smart(all_racks)

            processing_time = (datetime.now() - start_time).total_seconds()

            result = {
                "racks": unique_racks
            }

            # Cache the result (15 minute TTL)
            logger.info(f"ClickHouseRackService: Attempting to cache result for {site_id} with key: {cache_key}")
            cache_success = self.cache_service.set(
                cache_key,
                result,
                ttl=CacheConfig.MEDIUM_TTL,  # 15 minutes
                prefix=ClickHouseServiceConfig.CACHE_PREFIX_RACK_DATA
            )

            if cache_success:
                logger.info(f"ClickHouseRackService SUCCESS: Cached rack results for {site_id} (TTL: {CacheConfig.MEDIUM_TTL}s)")
            else:
                logger.error(f"ClickHouseRackService FAILED: Could not cache rack results for {site_id}")

            logger.info(f"ClickHouse processing completed in {processing_time:.2f}s: {len(unique_racks)} unique racks from {successful_tables} tables (failed: {failed_tables})")
            return result

        except Exception as e:
            logger.error(f"Error in ClickHouse rack retrieval: {str(e)}")
            raise

    def _process_table_clickhouse(self, site_id: str, table_id: str) -> List[Dict]:
        """
        Process a single table using ClickHouse intelligent rack detection.

        Args:
            site_id (str): Site identifier
            table_id (str): Table identifier

        Returns:
            List[Dict]: List of rack data dictionaries
        """
        try:
            logger.info(f"ClickHouse: Processing table {site_id}/{table_id}")

            # Get ClickHouse table name from mapping
            clickhouse_table_name = self.repository.get_clickhouse_table_name(site_id, table_id)
            if not clickhouse_table_name:
                logger.warning(f"ClickHouse: No table mapping found for {site_id}/{table_id}")
                return []

            logger.info(f"ClickHouse: Using table name '{clickhouse_table_name}' for {site_id}/{table_id}")

            # Get rack columns for this table
            rack_columns = self.repository.get_rack_columns_for_table(clickhouse_table_name)
            if not rack_columns:
                logger.info(f"ClickHouse: No rack columns found in table {clickhouse_table_name}")
                return []

            logger.info(f"ClickHouse: Found rack columns in {clickhouse_table_name}: {rack_columns}")

            # Get unique rack values from the best rack column
            best_rack_column = self._select_best_rack_column(rack_columns)
            logger.info(f"ClickHouse: Using best rack column '{best_rack_column}' for table {clickhouse_table_name}")

            rack_values_data = self.repository.get_unique_rack_values(
                clickhouse_table_name,
                [best_rack_column],
                limit=ClickHouseServiceConfig.DEFAULT_RACK_VALUES_LIMIT
            )

            if not rack_values_data:
                logger.warning(f"ClickHouse: No rack values found in column '{best_rack_column}' for table {clickhouse_table_name}")
                return []

            # Build result format compatible with existing API
            table_racks = []
            for rack_data in rack_values_data:
                rack_value = rack_data.get("rack_value")
                if rack_value and str(rack_value).strip():
                    table_racks.append({
                        "rackLabel": str(rack_value).strip(),
                        "siteName": site_id,
                        "tableName": table_id,
                        "rackValue": str(rack_value).strip()
                    })

            logger.info(f"ClickHouse: Extracted {len(table_racks)} rack values from table {clickhouse_table_name}")
            return table_racks

        except Exception as e:
            logger.error(f"ClickHouse: Error processing table {site_id}/{table_id}: {str(e)}")
            return []

    def _select_best_rack_column(self, rack_columns: List[str]) -> str:
        """
        Select the best rack column from available options using intelligent scoring.

        Args:
            rack_columns (List[str]): List of available rack columns

        Returns:
            str: Best rack column name
        """
        if not rack_columns:
            return None

        if len(rack_columns) == 1:
            return rack_columns[0]

        # Score each column based on name patterns
        column_scores = {}

        for column_name in rack_columns:
            score = self._score_column_name(column_name.lower())
            column_scores[column_name] = score
            logger.debug(f"ClickHouse: Column '{column_name}' scored {score}")

        # Find the column with the highest score
        best_column = max(column_scores.items(), key=lambda x: x[1])
        logger.info(f"ClickHouse: Selected column '{best_column[0]}' with score {best_column[1]}")
        return best_column[0]

    def _score_column_name(self, column_name: str) -> float:
        """
        Score a column name based on how likely it is to contain rack identifiers.

        Args:
            column_name (str): Column name (lowercase)

        Returns:
            float: Score from 0 to 100
        """
        # Explicit rack patterns (highest score)
        if any(pattern in column_name for pattern in ClickHouseColumnPatterns.EXPLICIT_RACK_PATTERNS):
            return ClickHouseColumnPatterns.SCORE_EXPLICIT_RACK

        # Good equipment patterns
        if any(pattern in column_name for pattern in ClickHouseColumnPatterns.GOOD_EQUIPMENT_PATTERNS):
            return ClickHouseColumnPatterns.SCORE_GOOD_EQUIPMENT

        # ID patterns
        if column_name.endswith('_id') or column_name.startswith('id_') or column_name == 'id':
            return ClickHouseColumnPatterns.SCORE_ID_PATTERN

        # Bad patterns (negative score)
        if any(bad_pattern in column_name for bad_pattern in ClickHouseColumnPatterns.BAD_COLUMN_PATTERNS):
            return ClickHouseColumnPatterns.SCORE_BAD_PATTERN

        # Neutral score for unknown patterns
        return ClickHouseColumnPatterns.SCORE_NEUTRAL

    def _generate_rack_cache_key(self, site_id: str, table_ids: List[str]) -> str:
        """Generate cache key for rack results"""
        import hashlib

        # Sort table_ids for consistent cache keys
        sorted_tables = sorted(table_ids)
        key_string = f"clickhouse_{site_id}_{'_'.join(sorted_tables)}"
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:12]

        return f"{ClickHouseServiceConfig.CACHE_PREFIX_RACKS}{site_id}_{key_hash}"

    def _deduplicate_racks_smart(self, all_racks: List[Dict]) -> List[Dict]:
        """
        Smart deduplication of racks.

        Args:
            all_racks (List[Dict]): List of rack dictionaries

        Returns:
            List[Dict]: Deduplicated list of racks
        """
        seen_rack_ids = set()
        unique_racks = []

        for rack in all_racks:
            rack_id = rack["rackValue"]
            if rack_id not in seen_rack_ids:
                unique_racks.append(rack)
                seen_rack_ids.add(rack_id)

        return unique_racks