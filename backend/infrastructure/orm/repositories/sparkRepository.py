from pyspark.sql import functions as F, DataFrame
from typing import Optional, Dict, List
from datetime import datetime
from config.spark_connection import get_spark_connection
from infrastructure.orm.repositories.sparkSqlRepository import SparkSqlRepository
from infrastructure.orm.repositories.pyarrowParallelProcessor import PyArrowParallelProcessor
from infrastructure.utils.queryOptimizer import QueryOptimizer

class SparkRepository:
    """
    Main Spark repository using modular components for optimized performance.
    Delegates to specialized components based on query characteristics.
    """
    
    def __init__(self):
        self.base_file_path = "wasbs://swro@mpcswrosg.blob.core.windows.net/tables"
        print(f"[SPARK_REPO] Initializing Spark repository...")
        self.spark = get_spark_connection()
        print(f"[SPARK_REPO] Spark session created successfully")
        print(f"[SPARK_REPO] Spark configuration for timestamps:")
        print(f"[SPARK_REPO]   spark.sql.parquet.timestampType: {self.spark.conf.get('spark.sql.parquet.timestampType', 'NOT_SET')}")
        print(f"[SPARK_REPO]   spark.sql.parquet.outputTimestampType: {self.spark.conf.get('spark.sql.parquet.outputTimestampType', 'NOT_SET')}")
        print(f"[SPARK_REPO]   spark.sql.parquet.enableVectorizedReader: {self.spark.conf.get('spark.sql.parquet.enableVectorizedReader', 'NOT_SET')}")
        
        # Initialize modular components
        self.spark_sql_repo = SparkSqlRepository(self.spark)
        self.pyarrow_processor = PyArrowParallelProcessor(self.spark)
        self.query_optimizer = QueryOptimizer()
        
    def _get_file_path(self, siteName: str = None, tableName: str = None, coordinates: bool = False) -> str:
        """
        Get the appropriate file path based on coordinates parameter.
        
        Args:
            siteName: Site name (required for coordinates=True)
            tableName: Table name (required for coordinates=True)
            coordinates: If True, use coordinates path; if False, use gold path
            
        Returns:
            Constructed file path
        """
        if coordinates:
            if not siteName or not tableName:
                raise ValueError("siteName and tableName are required when coordinates=True")
            return f"{self.base_file_path}/{siteName}/{tableName}"
        else:
            return f"{self.base_file_path}/gold"

    def _normalize_bounds(self, from_date: Optional[str], to_date: Optional[str]):
        """
        Delegate to query optimizer for consistent date normalization.
        """
        return self.query_optimizer.normalize_date_bounds(from_date, to_date)

    def _detect_date_column(self, siteName: str, tableName: str, coordinates: bool = False) -> str:
        """
        Detect the appropriate date column for the given table.
        Returns the best available date column name.
        """
        try:
            # Quick schema check to detect available timestamp columns
            parquet_path = self._get_parquet_path_for_detection(siteName, tableName, coordinates)
            
            # Read schema only (no data) for fast detection
            df_schema = (self.spark.read
                        .option("timestampType", "TIMESTAMP_MICROS")
                        .option("mergeSchema", "false")
                        .parquet(parquet_path)
                        .limit(0))  # Get schema without reading data
            
            available_columns = df_schema.columns
            print(f"[SPARK_REPO] Available columns for date detection: {available_columns}")
            
            # Define date column priority order
            date_column_candidates = [
                "Start_Time",      # Primary choice for most tables
                "End_Time",        # Secondary choice
                "Datetime",        # Legacy/fallback choice
                "datetime", "timestamp", "date", "created_at", "updated_at"
            ]
            
            # Find the first available date column
            for candidate in date_column_candidates:
                if candidate in available_columns:
                    print(f"[SPARK_REPO] Detected date column: {candidate}")
                    return candidate
            
            # If no standard date column found, return None for no date filtering
            print(f"[SPARK_REPO] No date column detected, will skip date-based operations")
            return None
            
        except Exception as e:
            print(f"[SPARK_REPO] Date column detection failed: {e}, using fallback")
            return "Start_Time"  # Safe fallback
    
    def _get_parquet_path_for_detection(self, siteName: str, tableName: str, coordinates: bool = False) -> str:
        """Get parquet path for schema detection."""
        if coordinates:
            return f"{self.base_file_path}/{siteName}/{tableName}"
        else:
            return f"{self.base_file_path}/gold/{siteName}/{tableName}"

    def read_parquet_optimized(
        self,
        siteName: str,
        tableName: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        columns: Optional[List[str]] = None,
        date_column: str = "Datetime",
        limit: Optional[int] = None,
        coordinates: bool = False
    ) -> DataFrame:
        """
        Optimized parquet reading using the best available method.
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            print(f"[SPARK_REPO] Starting optimized read for {siteName}/{tableName} from {data_type} data")
            
            # Assess query complexity
            complexity = self.query_optimizer.estimate_query_complexity(
                columns=columns,
                from_date=from_date,
                to_date=to_date,
                limit=limit
            )
            
            print(f"[SPARK_REPO] Query complexity: {complexity['estimated_time']}")
            
            # Try SparkSQL first for most cases
            try:
                return self._read_with_sparksql(
                    siteName, tableName, from_date, to_date, 
                    columns, date_column, limit, coordinates
                )
            except Exception as sparksql_error:
                print(f"[SPARK_REPO] SparkSQL failed: {sparksql_error}")
                
                # Fallback to PyArrow parallel processing
                return self._read_with_pyarrow_fallback(
                    siteName, tableName, from_date, to_date, columns, coordinates
                )
                
        except Exception as e:
            print(f"[SPARK_REPO] All read methods failed: {e}")
            raise e
    
    def _read_with_sparksql(
        self,
        siteName: str,
        tableName: str,
        from_date: Optional[str],
        to_date: Optional[str],
        columns: Optional[List[str]],
        date_column: str,
        limit: Optional[int],
        coordinates: bool = False
    ) -> DataFrame:
        """
        Read using optimized SparkSQL approach.
        """
        view_name = None
        try:
            # Create optimized temporary view
            view_name = self.spark_sql_repo.create_optimized_temp_view(
                siteName=siteName,
                tableName=tableName,
                coordinates=coordinates
            )
            
            # Execute optimized filtered query
            result_df = self.spark_sql_repo.execute_filtered_query(
                view_name=view_name,
                columns=columns,
                from_date=from_date,
                to_date=to_date,
                date_column=date_column,
                limit=limit
            )
            
            print(f"[SPARK_REPO] SparkSQL read successful")
            return result_df
            
        except Exception as e:
            raise e
        finally:
            if view_name:
                self.spark_sql_repo.cleanup_temp_view(view_name)
    
    def _read_with_pyarrow_fallback(
        self,
        siteName: str,
        tableName: str,
        from_date: Optional[str],
        to_date: Optional[str],
        columns: Optional[List[str]],
        coordinates: bool = False
    ) -> DataFrame:
        """
        Fallback to PyArrow parallel processing.
        """
        try:
            print(f"[SPARK_REPO] Using PyArrow parallel fallback")
            
            result_df = self.pyarrow_processor.process_parquet_files_parallel(
                siteName=siteName,
                tableName=tableName,
                from_date=from_date,
                to_date=to_date,
                columns=columns,
                max_files=5,
                coordinates=coordinates
            )
            
            print(f"[SPARK_REPO] PyArrow fallback successful")
            return result_df
            
        except Exception as e:
            print(f"[SPARK_REPO] PyArrow fallback failed: {e}")
            # Return empty DataFrame rather than crashing
            from pyspark.sql.types import StructType, StructField, StringType, TimestampType
            minimal_schema = StructType([
                StructField("Datetime", TimestampType(), True),
                StructField("error", StringType(), True)
            ])
            return self.spark.createDataFrame([], minimal_schema)

    def _read_parquet_with_pyarrow(
        self, 
        siteName: str, 
        tableName: str, 
        coordinates: bool = False
    ) -> DataFrame:
        """
        Legacy method - delegates to new PyArrow parallel processor.
        """
        return self.pyarrow_processor.process_parquet_files_parallel(
            siteName=siteName,
            tableName=tableName,
            max_files=3,  # Legacy compatibility with limited files
            coordinates=coordinates
        )

    def read_parquet(
        self,
        siteName: str,
        tableName: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: str = "Datetime",
        date_format: Optional[str] = None,
        coordinates: bool = False
    ) -> DataFrame:
        """
        Backward compatible parquet reader using optimized methods.
        
        Args:
            coordinates: If True, read from coordinates data; if False, read from gold data
        """
        data_type = "coordinates" if coordinates else "gold"
        print(f"[SPARK_READ] Legacy read_parquet called for {siteName}/{tableName} from {data_type} data")
        
        # Use optimized read method
        return self.read_parquet_optimized(
            siteName=siteName,
            tableName=tableName,
            from_date=from_date,
            to_date=to_date,
            columns=None,  # Backward compatibility - read all columns
            date_column=date_column,
            limit=None,    # No limit for backward compatibility
            coordinates=coordinates
        )