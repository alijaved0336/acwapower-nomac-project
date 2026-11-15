from typing import Optional, List, Dict, Union
from datetime import datetime
import logging

from config.spark_connection_optimized import SparkConnectionManager
from infrastructure.orm.repositories.sparkSqlRepository import SparkSqlRepository
from infrastructure.orm.repositories.pyarrowParallelProcessor import PyArrowParallelProcessor
from infrastructure.utils.queryOptimizer import QueryOptimizer
from infrastructure.utils.datetime_utils import DateTimeParser

logger = logging.getLogger(__name__)


class DataProcessingHierarchy:
    """
    Optimized data processing with Spark -> SparkSQL -> PyArrow fallback hierarchy.
    Automatically selects the best processing method based on data characteristics.
    """
    
    def __init__(self):
        self.spark = None  # Lazy initialization
        self.spark_sql_repo = None
        self.pyarrow_processor = None
        self.query_optimizer = QueryOptimizer()
        self.base_file_path = "wasbs://swro@mpcswrosg.blob.core.windows.net/tables"

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
    
    def _initialize_spark_components(self):
        """Lazy initialization of Spark components to avoid startup delays."""
        if self.spark is None:
            self.spark = SparkConnectionManager.get_spark_session()
            self.spark_sql_repo = SparkSqlRepository(self.spark)
            self.pyarrow_processor = PyArrowParallelProcessor(self.spark)
    
    def process_data_optimized(
        self,
        site_id: str,
        table_id: str,
        operation: str = "metadata",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None,  # ADD THIS
        coordinates: bool = False
    ) -> Dict:
        """
        Process data using optimal method based on operation and data characteristics.
        
        Args:
            site_id: Site identifier
            table_id: Table identifier
            operation: Type of operation ("metadata", "query", "analytics")
            from_date: Start date for filtering
            to_date: End date for filtering
            columns: Specific columns to process
            limit: Row limit for processing
            filters: Additional filters
            coordinates: If True, read from coordinates data; if False, read from gold data
            
        Returns:
            Processed data with method information
        """
        try:
            start_time = datetime.now()
            data_type = "coordinates" if coordinates else "gold"
            print(f"[DATA_HIERARCHY] Starting {operation} operation for {site_id}/{table_id} from {data_type} data")
            
            # Determine optimal processing method
            method = self._select_optimal_method(
                operation, from_date, to_date, columns, limit
            )
            
            print(f"[DATA_HIERARCHY] Selected method: {method}")
            
            # Process using selected method
            if method == "direct_spark":
                result = self._process_with_direct_spark(
                    site_id, table_id, from_date, to_date, columns, limit, filters, order_by, coordinates
                )
            elif method == "spark_sql":
                result = self._process_with_spark_sql(
                    site_id, table_id, from_date, to_date, columns, limit, filters, order_by, coordinates
                )
            else:  # pyarrow_fallback
                result = self._process_with_pyarrow(
                    site_id, table_id, from_date, to_date, columns, limit, filters, coordinates
                )
            
            # Add processing metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            result["processing_info"] = {
                "method_used": method,
                "processing_time_seconds": processing_time,
                "operation_type": operation,
                "data_source": data_type,
                "timestamp": DateTimeParser.format_datetime_without_timezone(start_time)
            }
            
            print(f"[DATA_HIERARCHY] Completed in {processing_time:.2f}s using {method}")
            return result
            
        except Exception as e:
            logger.error(f"Data processing failed: {e}")
            return self._create_error_response(str(e), site_id, table_id, coordinates)
    
    def _select_optimal_method(
        self,
        operation: str,
        from_date: Optional[str],
        to_date: Optional[str],
        columns: Optional[List[str]],
        limit: Optional[int]
    ) -> str:
        """Select the optimal processing method based on operation characteristics."""
        
        # For metadata operations, prefer direct Spark (fastest)
        if operation == "metadata":
            if limit and limit <= 100:
                return "direct_spark"
            elif from_date and to_date:
                # Date filtering works well with Spark SQL
                return "spark_sql"
            else:
                return "pyarrow_fallback"
        
        # For query operations
        elif operation == "query":
            complexity = self.query_optimizer.estimate_query_complexity(
                columns, from_date, to_date, limit
            )
            
            if complexity["score"] < 30:
                return "direct_spark"
            elif complexity["score"] < 60:
                return "spark_sql"
            else:
                return "pyarrow_fallback"
        
        # For analytics operations
        elif operation == "analytics":
            # Analytics typically need more processing power
            if limit and limit <= 1000:
                return "spark_sql"
            else:
                return "pyarrow_fallback"
        
        # Default fallback
        return "spark_sql"
    
    def _process_with_direct_spark(
        self,
        site_id: str,
        table_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        columns: Optional[List[str]],
        limit: Optional[int],
        filters: Optional[Dict],
        order_by: Optional[str],  # ADD THIS
        coordinates: bool = False
    ) -> Dict:
        try:
            self._initialize_spark_components()
            
            if coordinates:
                file_path = f"{self.base_file_path}/{site_id}/{table_id}/*.parquet"
            else:
                file_path = f"{self.base_file_path}/gold/{site_id}/{table_id}/*.parquet"
            
            # Read parquet with optimizations
            df = self.spark.read.option("mergeSchema", "false").parquet(file_path)
            
            # Apply filters
            if from_date and to_date:
                df = df.filter(
                    (df["datetime"] >= from_date) & (df["datetime"] <= to_date)
                )
            
            if columns:
                df = df.select(*columns)
            
            
            # Apply additional filters
            if filters:
                for col, value in filters.items():
                    df = df.filter(df[col] == value)
            
            # CRITICAL: Apply ORDER BY (this was missing!)
            if order_by:
                if "DESC" in order_by.upper():
                    col_name = order_by.replace(" DESC", "").replace(" desc", "").strip()
                    df = df.orderBy(df[col_name].desc())
                else:
                    df = df.orderBy(order_by)
            
            # Apply limit AFTER ordering (same as original LIMIT 1)
            if limit:
                df = df.limit(limit)
            
            # Collect results efficiently
            result_data = df.collect()
            
            return {
                "success": True,
                "data": [row.asDict() for row in result_data],
                "row_count": len(result_data),
                "schema": [field.json() for field in df.schema.fields]
            }
            
        except Exception as e:
            raise Exception(f"Direct Spark processing failed: {e}")

    
    def _process_with_spark_sql(
        self,
        site_id: str,
        table_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        columns: Optional[List[str]],
        limit: Optional[int],
        filters: Optional[Dict],
        order_by: Optional[str],  # ADD THIS
        coordinates: bool = False
    ) -> Dict:
        try:
            self._initialize_spark_components()
            
            # Create temporary view
            view_name = self.spark_sql_repo.create_optimized_temp_view(
                site_id, table_id, coordinates=coordinates
            )
            
            # Build SQL query EXACTLY like original database
            select_cols = ", ".join(f"`{col}`" for col in columns) if columns else "*"
            query = f"SELECT {select_cols} FROM {view_name}"
            
            conditions = []
            if from_date and to_date:
                conditions.append(f"`datetime` BETWEEN '{from_date}' AND '{to_date}'")
            
            if filters:
                for col, value in filters.items():
                    conditions.append(f"`{col}` = '{value}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # CRITICAL: Add ORDER BY (this replicates original "ORDER BY datetime DESC")
            if order_by:
                query += f" ORDER BY `{order_by.replace(' DESC', '').replace(' desc', '').strip()}`"
                if "DESC" in order_by.upper():
                    query += " DESC"
            
            # CRITICAL: Add LIMIT (this replicates original database LIMIT behavior)
            if limit:
                query += f" LIMIT {limit}"
            
            print(f"[DEBUG] Executing SQL that replicates original: {query}")
            
            # Execute query
            result_df = self.spark.sql(query)
            result_data = result_df.collect()
            
            # Cleanup
            self.spark_sql_repo.cleanup_temp_view(view_name)
            
            return {
                "success": True,
                "data": [row.asDict() for row in result_data],
                "row_count": len(result_data),
                "query": query,
                "schema": [field.json() for field in result_df.schema.fields]
            }
            
        except Exception as e:
            raise Exception(f"SparkSQL processing failed: {e}")

    
    def _process_with_pyarrow(
        self,
        site_id: str,
        table_id: str,
        from_date: Optional[str],
        to_date: Optional[str],
        columns: Optional[List[str]],
        limit: Optional[int],
        filters: Optional[Dict],
        coordinates: bool = False
    ) -> Dict:
        """Process using PyArrow parallel processing (best for large datasets)."""
        try:
            self._initialize_spark_components()
            
            # Use PyArrow parallel processor
            df = self.pyarrow_processor.process_parquet_files_parallel(
                siteName=site_id,
                tableName=table_id,
                from_date=from_date,
                to_date=to_date,
                columns=columns,
                max_files=5,  # Limit for performance
                coordinates=coordinates
            )
            
            # Apply additional filters
            if filters:
                for col, value in filters.items():
                    df = df.filter(df[col] == value)
            
            # Apply limit
            if limit:
                df = df.limit(limit)
            
            # Collect results
            result_data = df.collect()
            
            return {
                "success": True,
                "data": [row.asDict() for row in result_data],
                "row_count": len(result_data),
                "schema": [field.json() for field in df.schema.fields]
            }
            
        except Exception as e:
            raise Exception(f"PyArrow processing failed: {e}")
    
    def _create_error_response(
        self, 
        error_msg: str, 
        site_id: str, 
        table_id: str, 
        coordinates: bool = False
    ) -> Dict:
        """Create standardized error response."""
        data_type = "coordinates" if coordinates else "gold"
        return {
            "success": False,
            "error": error_msg,
            "site_id": site_id,
            "table_id": table_id,
            "data_source": data_type,
            "data": [],
            "row_count": 0
        }
    
    def get_processing_recommendations(
        self,
        site_id: str,
        table_id: str,
        operation: str,
        coordinates: bool = False
    ) -> Dict:
        """Get recommendations for optimal data processing."""
        try:
            data_type = "coordinates" if coordinates else "gold"
            recommendations = {
                "optimal_method": self._select_optimal_method(
                    operation, None, None, None, None
                ),
                "data_source": data_type,
                "performance_tips": []
            }
            
            if operation == "metadata":
                recommendations["performance_tips"].extend([
                    "Use date filtering for better performance",
                    "Limit columns to only what you need",
                    "Consider using small sample sizes"
                ])
            elif operation == "analytics":
                recommendations["performance_tips"].extend([
                    "Use PyArrow for large dataset analytics",
                    "Apply filters early in the pipeline",
                    "Consider data aggregation"
                ])
            
            if coordinates:
                recommendations["performance_tips"].append(
                    "Coordinates data typically has smaller file sizes - consider direct Spark for better performance"
                )
            
            return recommendations
            
        except Exception as e:
            return {"error": str(e)}