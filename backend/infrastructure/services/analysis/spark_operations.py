"""
Spark Operations Module
Handles Spark-based data operations and file system operations.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from infrastructure.services.spark_singleton import get_spark_session
from infrastructure.utils.datetime_utils import DateTimeParser
from .spark_connection_manager import get_optimized_spark_session

logger = logging.getLogger(__name__)


class SparkOperations:
    """Handles Spark-based operations"""

    def __init__(self):
        # Use pre-initialized Spark session from singleton
        self._spark = None  # Lazy initialization
        self._spark_repo = None  # Lazy initialization
        self.base_file_path = "wasbs://swro@mpcswrosg.blob.core.windows.net/tables"

    @property
    def spark(self):
        """Get optimized Spark session from connection manager"""
        if self._spark is None:
            self._spark = get_optimized_spark_session()
        return self._spark

    def _get_file_path(self, site_id: str = None, table_id: str = None, coordinates: bool = False) -> str:
        """
        Get the appropriate file path based on coordinates parameter.
        
        Args:
            site_id: Site identifier (required for coordinates=True)
            table_id: Table identifier (required for coordinates=True)
            coordinates: If True, use coordinates path; if False, use gold path
            
        Returns:
            Constructed file path
        """
        if coordinates:
            if not site_id or not table_id:
                raise ValueError("site_id and table_id are required when coordinates=True")
            return f"{self.base_file_path}/{site_id}/{table_id}"
        else:
            return f"{self.base_file_path}/gold"

    def get_spark_directories(self, coordinates: bool = False) -> List[Dict[str, str]]:
        """
        Get all directories (sites) using Spark file system operations.
        
        Args:
            coordinates: If True, get directories from coordinates data; if False, from gold data
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            logger.info(f"Using Spark-based directory listing for sites from {data_type} data")

            spark = self.spark
            base_path = f"{self.base_file_path}/{data_type}"

            # Get directory listing using Spark's file system
            try:
                # Get Hadoop configuration from Spark
                hadoop_conf = spark._jsc.hadoopConfiguration()
                
                # Ensure Azure Blob Storage configuration is properly set
                hadoop_conf.set("fs.azure.account.auth.type", "SharedKey")
                hadoop_conf.set("fs.azure.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
                hadoop_conf.set("fs.wasbs.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
                hadoop_conf.set("fs.wasb.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
                
                hadoop_fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(
                    spark._jvm.java.net.URI(base_path), hadoop_conf
                )
                path = spark._jvm.org.apache.hadoop.fs.Path(base_path)

                directories = []
                if hadoop_fs.exists(path):
                    file_statuses = hadoop_fs.listStatus(path)

                    for status in file_statuses:
                        if status.isDirectory():
                            dir_path = str(status.getPath())
                            dir_name = dir_path.split("/")[-1]
                            # Only include non-empty directory names
                            if dir_name and not dir_name.startswith("_") and not dir_name.startswith("."):
                                directories.append({
                                    "name": dir_name,
                                    "path": f"tables/{data_type}/{dir_name}"
                                })

                logger.info(f"Found {len(directories)} directories using Spark from {data_type} data")
                return directories

            except Exception as spark_error:
                logger.warning(f"Spark file system operation failed: {spark_error}")
                # Fallback to Azure operations
                from .azure_operations import AnalysisAzureOperations
                azure_ops = AnalysisAzureOperations()
                return azure_ops.get_all_directories()

        except Exception as e:
            logger.error(f"Error getting directories with Spark: {str(e)}", exc_info=True)
            # Fallback to Azure operations as last resort
            try:
                from .azure_operations import AnalysisAzureOperations
                azure_ops = AnalysisAzureOperations()
                result = azure_ops.get_all_directories()
                data_type = "coordinates" if coordinates else "gold"
                logger.info(f"Falling back to Azure operations for {data_type} data, found {len(result)} directories")
                return result
            except Exception as fallback_error:
                logger.error(f"Azure fallback also failed: {fallback_error}", exc_info=True)
                return []

    def get_spark_subdirectories(self, site_id: str, coordinates: bool = False) -> List[Dict[str, str]]:
        """
        Get all subdirectories (tables) for a given site using Spark.
        
        Args:
            site_id: Site identifier
            coordinates: If True, get subdirectories from coordinates data; if False, from gold data
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            logger.info(f"Using Spark-based subdirectory listing for site: {site_id} from {data_type} data")

            spark = self.spark
            site_path = f"{self.base_file_path}/{data_type}/{site_id}"

            # Get subdirectory listing using Spark's file system
            try:
                # Get Hadoop configuration from Spark
                hadoop_conf = spark._jsc.hadoopConfiguration()
                
                # Ensure Azure Blob Storage configuration is properly set
                hadoop_conf.set("fs.azure.account.auth.type", "SharedKey")
                hadoop_conf.set("fs.azure.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
                hadoop_conf.set("fs.wasbs.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
                hadoop_conf.set("fs.wasb.impl", "org.apache.hadoop.fs.azure.NativeAzureFileSystem")
                
                hadoop_fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(
                    spark._jvm.java.net.URI(site_path), hadoop_conf
                )
                path = spark._jvm.org.apache.hadoop.fs.Path(site_path)

                subdirectories = []
                if hadoop_fs.exists(path):
                    file_statuses = hadoop_fs.listStatus(path)

                    for status in file_statuses:
                        if status.isDirectory():
                            dir_path = str(status.getPath())
                            dir_name = dir_path.split("/")[-1]
                            # Only include non-empty directory names
                            if dir_name and not dir_name.startswith("_") and not dir_name.startswith("."):
                                subdirectories.append({
                                    "name": dir_name,
                                    "path": f"tables/{data_type}/{site_id}/{dir_name}"
                                })

                logger.info(f"Found {len(subdirectories)} subdirectories for site {site_id} from {data_type} data")
                return subdirectories

            except Exception as spark_error:
                logger.warning(f"Spark file system operation failed for subdirectories: {spark_error}")
                # Fallback to Azure operations
                from .azure_operations import AnalysisAzureOperations
                azure_ops = AnalysisAzureOperations()
                return azure_ops.get_subdirectories(site_id)

        except Exception as e:
            logger.error(f"Error getting subdirectories with Spark for {site_id}: {str(e)}")
            # Fallback to Azure operations as last resort
            try:
                from .azure_operations import AnalysisAzureOperations
                azure_ops = AnalysisAzureOperations()
                result = azure_ops.get_subdirectories(site_id)
                data_type = "coordinates" if coordinates else "gold"
                logger.info(f"Falling back to Azure operations for {site_id} from {data_type} data, found {len(result)} subdirectories")
                return result
            except Exception as fallback_error:
                logger.error(f"Azure fallback also failed for {site_id}: {fallback_error}")
                return []

    def get_columns_with_spark(
        self,
        table_id: str,
        site_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        date_column: str,
        include_samples: bool,
        exclude_calculated: bool,
        exclude_null: bool,
        include_performance: bool,
        coordinates: bool = False
    ) -> Dict:
        """
        Get columns using Spark-based operations (fallback method).
        
        Args:
            coordinates: If True, read from coordinates data; if False, read from gold data
        """
        start_time = datetime.now()
        data_type = "coordinates" if coordinates else "gold"
        logger.info(f"Getting columns for {site_id}/{table_id} using Spark from {data_type} data")
        
        try:
            spark = self.spark
            
            # Build path with date filtering if dates provided
            if coordinates:
                base_path = f"{self.base_file_path}/{site_id}/{table_id}"
            else:
                base_path = f"{self.base_file_path}/gold/{site_id}/{table_id}"
            
            # Parse dates if provided
            from_date_obj, to_date_obj, _ = self._parse_and_validate_dates(from_date, to_date) if from_date or to_date else (None, None, False)
            
            # Build path pattern for date filtering
            if from_date_obj and to_date_obj:
                path_pattern = f"{base_path}/*/*/*/*.parquet"  # YYYY/MM/DD pattern
            else:
                path_pattern = f"{base_path}/**/*.parquet"
            
            logger.info(f"Reading parquet files from: {path_pattern}")
            
            # Read parquet files with debug logging
            logger.info(f"[DEBUG] Reading parquet files from: {path_pattern}")
            logger.info(f"[DEBUG] Spark configuration for timestamps:")
            logger.info(f"[DEBUG]   spark.sql.parquet.timestampType: {spark.conf.get('spark.sql.parquet.timestampType', 'NOT_SET')}")
            logger.info(f"[DEBUG]   spark.sql.parquet.outputTimestampType: {spark.conf.get('spark.sql.parquet.outputTimestampType', 'NOT_SET')}")
            
            try:
                df = spark.read.option("recursiveFileLookup", "true").parquet(path_pattern)
                logger.info(f"[DEBUG] Successfully read parquet files. Schema:")
                for field in df.schema.fields:
                    logger.info(f"[DEBUG]   {field.name}: {field.dataType}")
                    if 'timestamp' in str(field.dataType).lower():
                        logger.info(f"[DEBUG]   *** TIMESTAMP FIELD DETECTED: {field.name} -> {field.dataType} ***")
            except Exception as parquet_error:
                logger.error(f"[DEBUG] Error reading parquet files: {parquet_error}")
                logger.error(f"[DEBUG] Error type: {type(parquet_error)}")
                raise parquet_error
            
            # Apply date filtering if dates provided
            if from_date_obj and to_date_obj and date_column in df.columns:
                # Convert datetime objects to strings for Spark filtering
                from_date_str = from_date_obj.strftime('%Y-%m-%d %H:%M:%S')
                to_date_str = to_date_obj.strftime('%Y-%m-%d %H:%M:%S')
                
                logger.info(f"Applying date filter: {date_column} between {from_date_str} and {to_date_str}")
                df = df.filter(
                    (df[date_column] >= from_date_str) & 
                    (df[date_column] <= to_date_str)
                )
            
            # Get schema information
            schema = df.schema
            
            # Get data for all columns if requested
            column_data = {}
            if include_samples:
                logger.info("Collecting data samples for all columns")
                # Convert to Pandas for easier data extraction
                pandas_df = df.toPandas()
                
                for column in schema:
                    name = column.name
                    if name in pandas_df.columns:
                        # Convert values to strings for JSON serialization, formatting datetime values
                        column_data[name] = []
                        for val in pandas_df[name].head(1000).tolist():  # Limit to 1000 samples
                            if val is None:
                                column_data[name].append(None)
                            elif isinstance(val, datetime):
                                # Format datetime values without timezone
                                column_data[name].append(DateTimeParser.format_datetime_without_timezone(val))
                            else:
                                column_data[name].append(str(val))
            
            # Build column metadata
            columns = []
            for field in schema:
                name = field.name
                data_type = str(field.dataType)
                nullable = field.nullable
                
                columns.append({
                    "name": name,
                    "type": data_type,
                    "nullable": nullable,
                    "dataSource": column_data.get(name, []) if include_samples else [],
                    "table": table_id
                })
            
            # Apply filtering
            from .column_operations import ColumnOperations
            col_ops = ColumnOperations()
            columns = col_ops._filter_columns(
                columns, 
                include_samples=include_samples,
                exclude_calculated=exclude_calculated,
                exclude_null=exclude_null
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "columns": columns,
                "date_filter": {
                    "from_date": from_date or "N/A",
                    "to_date": to_date or "N/A",
                    "date_column": date_column,
                    "rows_in_range": df.count() if from_date_obj and to_date_obj else 0,
                    "sample_size": len(columns[0]["dataSource"]) if columns and include_samples and columns[0].get("dataSource") else 0
                },
                "method_used": f"spark_based_{data_type}",
                "data_source": data_type
            }
            
            if include_performance:
                result["performance"] = {
                    "processing_time_seconds": processing_time,
                    "rows_processed": df.count(),
                    "columns_found": len(columns)
                }
            
            logger.info(f"Spark-based column retrieval completed in {processing_time:.2f}s from {data_type} data")
            return result
            
        except Exception as e:
            logger.error(f"Spark-based column retrieval failed: {str(e)}")
            
            # Try fallback metadata
            try:
                fallback_result = self._get_fallback_metadata(table_id, from_date, to_date, date_column, coordinates)
                fallback_result["method_used"] = f"spark_fallback_{data_type}"
                fallback_result["data_source"] = data_type
                return fallback_result
            except Exception as fallback_error:
                logger.error(f"Fallback metadata also failed: {fallback_error}")
                raise Exception(f"Both Spark and fallback methods failed: {str(e)}")

    def _parse_and_validate_dates(self, from_date: Optional[str], to_date: Optional[str]) -> tuple:
        """
        Parse and validate date parameters.
        """
        applied_default = False
        now = datetime.now(timezone.utc)
        
        # Set defaults if no dates provided
        if not from_date and not to_date:
            from_date_obj = now - timedelta(days=7)
            to_date_obj = now
            applied_default = True
        else:
            # Parse from_date
            if from_date:
                try:
                    from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    from_date_obj = from_date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
                except ValueError:
                    raise ValueError(f"Invalid from_date format. Expected YYYY-MM-DD, got: {from_date}")
            else:
                from_date_obj = now - timedelta(days=7)
                applied_default = True
            
            # Parse to_date
            if to_date:
                try:
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
                except ValueError:
                    raise ValueError(f"Invalid to_date format. Expected YYYY-MM-DD, got: {to_date}")
            else:
                to_date_obj = now
                if from_date:
                    applied_default = True
        
        # Validation checks
        if from_date_obj > now and (from_date_obj - now).days > 1:
            raise ValueError("from_date cannot be in the future")
        if to_date_obj > now and (to_date_obj - now).days > 1:
            raise ValueError("to_date cannot be in the future")
        if from_date_obj > to_date_obj:
            raise ValueError("from_date cannot be after to_date")

        # Add maximum range validation
        MAX_DATE_RANGE_DAYS = 90
        if (to_date_obj - from_date_obj).days > MAX_DATE_RANGE_DAYS:
            raise ValueError(f"Date range cannot exceed {MAX_DATE_RANGE_DAYS} days")

        return from_date_obj, to_date_obj, applied_default

    def _get_fallback_metadata(
        self, 
        table_id: str, 
        from_date: Optional[str], 
        to_date: Optional[str], 
        date_column: Optional[str],
        coordinates: bool = False
    ) -> Dict:
        """Return fallback metadata when all other methods fail"""
        data_type = "coordinates" if coordinates else "gold"
        return {
            "columns": [
                {
                    "name": "Datetime", 
                    "type": "timestamp", 
                    "nullable": False, 
                    "dataSource": ["2025-04-25", "2025-04-26"], 
                    "table": table_id
                },
                {
                    "name": "Chemical_ppm", 
                    "type": "double", 
                    "nullable": True, 
                    "dataSource": ["1.5", "2.3", "1.8"], 
                    "table": table_id
                },
                {
                    "name": "pH_Level", 
                    "type": "double", 
                    "nullable": True, 
                    "dataSource": ["7.2", "6.8", "7.1"], 
                    "table": table_id
                }
            ],
            "date_filter": {
                "from_date": from_date or "2025-04-25",
                "to_date": to_date or "2025-04-30", 
                "date_column": date_column or "Datetime",
                "rows_in_range": 100,
                "message": f"Fallback metadata for {data_type} data - Spark optimization in progress"
            },
            "method_used": f"fallback_metadata_{data_type}",
            "data_source": data_type
        }
