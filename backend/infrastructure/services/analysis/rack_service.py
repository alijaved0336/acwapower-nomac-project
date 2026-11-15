"""
Rack Service - Optimized service for fetching unique racks
Uses efficient Spark operations with minimal data reading for maximum performance.
"""
import logging
from typing import Dict, List, Optional
from infrastructure.orm.repositories.sparkRepository import SparkRepository

logger = logging.getLogger(__name__)


class RackService:
    """Optimized service for rack operations with minimal data processing"""

    def __init__(self):
        self._spark_repo = None  # Lazy initialization

    @property
    def spark_repo(self):
        """Get Spark repository instance with lazy initialization"""
        if self._spark_repo is None:
            self._spark_repo = SparkRepository()
        return self._spark_repo

    def get_unique_racks_optimized(self, site_id: str, table_ids: List[str]) -> Dict:
        """
        Get unique racks using ultra-fast FastMetadataService approach.
        Leverages existing optimized metadata service for maximum performance.
        """
        try:
            logger.info(f"Getting unique racks for site {site_id} from {len(table_ids)} tables (ultra-fast)")
            
            # Validate inputs
            if not site_id or not table_ids:
                raise ValueError("site_id and table_ids are required")
            
            if not isinstance(table_ids, list) or len(table_ids) == 0:
                raise ValueError("table_ids must be a non-empty list")
            
            # Limit tables to prevent timeout
            MAX_TABLES = 10
            if len(table_ids) > MAX_TABLES:
                raise ValueError(f"Maximum {MAX_TABLES} tables allowed per request")
            
            all_racks = []
            successful_tables = 0
            failed_tables = 0
            
            # Use FastMetadataService for ultra-fast column detection
            from infrastructure.services.fastMetadataService import FastMetadataService
            fast_service = FastMetadataService()
            
            # Process each table with ultra-fast approach
            for table_id in table_ids:
                try:
                    logger.info(f"Processing table {table_id} for unique racks (ultra-fast)")
                    
                    # Get column metadata using FastMetadataService (already optimized)
                    result = fast_service.get_fast_column_metadata(
                        site_id=site_id,
                        table_id=table_id,
                        max_rows=50  # Very small sample for speed
                    )
                    
                    if result and 'columns' in result:
                        columns = result['columns']
                        
                        # Find rack column quickly
                        rack_column = self._find_rack_column_fast([col.get('name', '') for col in columns])
                        
                        if rack_column:
                            # Get sample data from the rack column
                            rack_column_data = None
                            for col in columns:
                                if col.get('name') == rack_column and 'dataSource' in col:
                                    rack_column_data = col['dataSource']
                                    break
                            
                            if rack_column_data:
                                # Extract unique values from sample data
                                rack_values = []
                                for value in rack_column_data:
                                    if value is not None and str(value).strip() != '':
                                        str_value = str(value)
                                        if str_value.lower() not in ['nan', 'null', 'none']:
                                            rack_values.append(str_value)
                                
                                # Remove duplicates
                                unique_rack_values = list(set(rack_values))
                                
                                logger.info(f"Found {len(unique_rack_values)} unique racks in table {table_id} from sample data")
                                
                                # Add to results
                                for rack_value in unique_rack_values:
                                    all_racks.append({
                                        "rack_id": rack_value,
                                        "site_id": site_id,
                                        "table_id": table_id,
                                        "columnName": rack_column
                                    })
                                
                                successful_tables += 1
                                logger.info(f"Successfully processed table {table_id} with {len(unique_rack_values)} unique racks")
                            else:
                                logger.warning(f"No sample data found for rack column '{rack_column}' in table {table_id}")
                                failed_tables += 1
                        else:
                            logger.warning(f"No rack column found in table {table_id}")
                            failed_tables += 1
                    else:
                        logger.warning(f"No column metadata found for table {table_id}")
                        failed_tables += 1
                        
                except Exception as e:
                    logger.error(f"Error processing table {table_id}: {str(e)}")
                    failed_tables += 1
                    continue
            
            # Remove duplicates based on rack_id (keep the first occurrence)
            unique_racks = []
            seen_rack_ids = set()
            
            for rack in all_racks:
                rack_id = rack["rack_id"]
                if rack_id not in seen_rack_ids:
                    unique_racks.append(rack)
                    seen_rack_ids.add(rack_id)
            
            # Build response
            result = {
                "racks": unique_racks
            }
            
            logger.info(f"Successfully retrieved {len(unique_racks)} unique racks from {successful_tables} tables (ultra-fast)")
            return result
            
        except Exception as e:
            logger.error(f"Error getting unique racks (ultra-fast): {str(e)}")
            raise e

    def _find_rack_column_fast(self, columns: List[str]) -> Optional[str]:
        """
        Fast rack column detection using optimized pattern matching.
        """
        # 1. Look for explicit rack columns (highest priority)
        explicit_rack_patterns = ['rack', 'rack_id', 'rackid', 'rack_name', 'rackname']
        for col in columns:
            if any(pattern in col.lower() for pattern in explicit_rack_patterns):
                return col
        
        # 2. Look for ID columns that might represent racks
        id_patterns = ['id', '_id', 'identifier', 'name', 'location', 'position', 'unit', 'station', 'equipment']
        for col in columns:
            if any(pattern in col.lower() for pattern in id_patterns):
                return col
        
        # 3. Use any non-datetime column as fallback
        for col in columns:
            if col.lower() not in ['datetime', 'timestamp', 'date', 'time']:
                return col
        
        return None
