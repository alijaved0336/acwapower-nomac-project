import re
from pyspark.sql import functions as F, DataFrame
from pyspark.sql import SparkSession
from typing import Optional, Dict, List
from datetime import datetime
import os
from infrastructure.utils.sqlQueryOptimizer import SqlQueryOptimizer


class SparkSqlRepository:
    """
    Modular SparkSQL repository for optimized query execution.
    Handles SparkSQL operations with predicate pushdown and performance optimizations.
    """
    
    def __init__(self, spark_session: SparkSession):
        self.spark = spark_session
        self.base_file_path = "wasbs://swro@mpcswrosg.blob.core.windows.net/tables"
        self.sql_optimizer = SqlQueryOptimizer(spark_session)

    def _sanitize_view_name(self, name: str) -> str:
        """
        Sanitize view name to be valid SQL identifier.
        Replace special characters with underscores.
        """
        # Replace hyphens, spaces, and other special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Ensure it starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = f"view_{sanitized}"
        
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove trailing underscores
        sanitized = sanitized.rstrip('_')
        
        print(f"[SPARKSQL] Sanitized view name: '{name}' -> '{sanitized}'")
        return sanitized

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
    
    def get_metadata_with_direct_sql(
        self,
        siteName: str,
        tableName: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: str = "Datetime",
        sample_size: int = 100,
        coordinates: bool = False
    ) -> Dict:
        """
        Get metadata using direct SQL optimization - fastest method.
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            print(f"[SPARKSQL] Using direct SQL optimization for {siteName}/{tableName} from {data_type} data")
            
            result = self.sql_optimizer.execute_metadata_query_optimized(
                siteName=siteName,
                tableName=tableName,
                from_date=from_date,
                to_date=to_date,
                date_column=date_column,
                sample_size=sample_size,
                coordinates=coordinates
            )
            
            print(f"[SPARKSQL] Direct SQL optimization successful")
            return result
            
        except Exception as e:
            print(f"[SPARKSQL] Direct SQL failed: {e}")
            raise e

    def create_optimized_temp_view(
        self,
        siteName: str,
        tableName: str,
        view_name: Optional[str] = None,
        coordinates: bool = False
    ) -> str:
        """
        Create a temporary view with optimized read settings and sanitized view name.
        Returns the view name for use in SQL queries.
        """
        try:
            parquet_path = self._get_parquet_path(siteName, tableName, coordinates)
            
            # Read with optimized settings
            df = (self.spark.read
                  .option("timestampType", "TIMESTAMP_MICROS")
                  .option("datetimeRebaseMode", "CORRECTED")
                  .option("int96RebaseMode", "CORRECTED")
                  .option("mergeSchema", "false")
                  .option("recursiveFileLookup", "true")
                  .parquet(parquet_path))
            
            # Generate sanitized view name if not provided
            if not view_name:
                data_suffix = "_coord" if coordinates else "_gold"
                # CRITICAL FIX: Sanitize the site and table names
                safe_site_name = self._sanitize_view_name(siteName)
                safe_table_name = self._sanitize_view_name(tableName)
                view_name = f"{safe_site_name}_{safe_table_name}{data_suffix}_view"
            else:
                # Also sanitize provided view names
                view_name = self._sanitize_view_name(view_name)
            
            # Create temporary view with sanitized name
            df.createOrReplaceTempView(view_name)
            data_type = "coordinates" if coordinates else "gold"
            print(f"[SPARKSQL] Created optimized temp view: {view_name} for {data_type} data")
            
            return view_name
            
        except Exception as e:
            print(f"[SPARKSQL] Failed to create temp view: {str(e)}")
            raise e

    def _get_parquet_path(self, siteName: str, tableName: str, coordinates: bool = False) -> str:
        """
        Get the full parquet path for reading data.
        
        Args:
            siteName: Site name
            tableName: Table name
            coordinates: If True, use coordinates path; if False, use gold path
            
        Returns:
            Full parquet path
        """
        if coordinates:
            return f"{self.base_file_path}/{siteName}/{tableName}"
        else:
            return f"{self.base_file_path}/gold/{siteName}/{tableName}"
    
    def execute_filtered_query(
        self,
        view_name: str,
        columns: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: str = "Datetime",
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> DataFrame:
        """
        Execute optimized SQL query with predicate pushdown.
        """
        try:
            # Ensure view name is sanitized (defensive programming)
            sanitized_view_name = self._sanitize_view_name(view_name)
            
            # Build SELECT clause with column pruning
            if columns:
                select_clause = ", ".join([f"`{col}`" for col in columns])
            else:
                select_clause = "*"
            
            # Build WHERE clause for date filtering
            where_conditions = []
            if from_date:
                from_ts = self._normalize_date_bound(from_date, is_start=True)
                where_conditions.append(f"`{date_column}` >= timestamp('{from_ts}')")
            if to_date:
                to_ts = self._normalize_date_bound(to_date, is_start=False)
                where_conditions.append(f"`{date_column}` <= timestamp('{to_ts}')")
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            
            # Build ORDER BY clause
            if not order_by and date_column:
                order_clause = f"ORDER BY `{date_column}` DESC"
            elif order_by:
                order_clause = f"ORDER BY {order_by}"
            else:
                order_clause = ""
            
            # Build LIMIT clause
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            # Construct optimized SQL query with sanitized view name
            sql_query = f"""
                SELECT {select_clause}
                FROM {sanitized_view_name}
                {where_clause}
                {order_clause}
                {limit_clause}
            """.strip()
            
            print(f"[SPARKSQL] Executing optimized query: {sql_query}")
            
            # Execute with automatic optimization
            result_df = self.spark.sql(sql_query)
            
            # Apply post-execution optimizations
            result_df = result_df.coalesce(2).cache()
            
            print(f"[SPARKSQL] Query executed successfully with optimizations")
            return result_df
            
        except Exception as e:
            print(f"[SPARKSQL] Query execution failed: {str(e)}")
            raise e
    
    def get_table_metadata(self, view_name: str) -> List[Dict]:
        """
        Get table schema metadata efficiently using SparkSQL.
        """
        try:
            # Sanitize view name for safety
            sanitized_view_name = self._sanitize_view_name(view_name)
            
            schema_df = self.spark.sql(f"DESCRIBE {sanitized_view_name}")
            schema_info = schema_df.collect()
            
            metadata = []
            for row in schema_info:
                if hasattr(row, 'col_name') and hasattr(row, 'data_type'):
                    metadata.append({
                        "name": row.col_name,
                        "type": row.data_type,
                        "nullable": True  # Default assumption
                    })
            
            print(f"[SPARKSQL] Retrieved metadata for {len(metadata)} columns")
            return metadata
            
        except Exception as e:
            print(f"[SPARKSQL] Failed to get metadata: {str(e)}")
            raise e
    
    def get_sample_data(
        self,
        view_name: str,
        columns: Optional[List[str]] = None,
        sample_size: int = 50,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: str = "Datetime"
    ) -> List:
        """
        Get sample data efficiently with minimal memory usage.
        """
        try:
            # Execute filtered query for sample
            sample_df = self.execute_filtered_query(
                view_name=view_name,
                columns=columns,
                from_date=from_date,
                to_date=to_date,
                date_column=date_column,
                limit=sample_size
            )
            
            # Collect sample data
            sample_data = sample_df.collect()
            print(f"[SPARKSQL] Retrieved {len(sample_data)} sample rows")
            
            return sample_data
            
        except Exception as e:
            print(f"[SPARKSQL] Failed to get sample data: {str(e)}")
            return []
    
    def cleanup_temp_view(self, view_name: str) -> None:
        """
        Clean up temporary view to free memory.
        """
        try:
            # Sanitize view name before cleanup
            sanitized_view_name = self._sanitize_view_name(view_name)
            
            if self.spark.catalog.tableExists(sanitized_view_name):
                self.spark.catalog.dropTempView(sanitized_view_name)
                print(f"[SPARKSQL] Cleaned up temp view: {sanitized_view_name}")
        except Exception as e:
            print(f"[SPARKSQL] Warning: Failed to cleanup view {view_name}: {str(e)}")
    
    def _normalize_date_bound(self, date_str: str, is_start: bool) -> str:
        """
        Normalize date bounds for SQL queries.
        """
        fmt_date = "%Y-%m-%d"
        
        def _is_date_only(s: str) -> bool:
            try:
                datetime.strptime(s, fmt_date)
                return True
            except:
                return False
        
        if _is_date_only(date_str):
            if is_start:
                return f"{date_str} 00:00:00"
            else:
                return f"{date_str} 23:59:59.999999"
        else:
            return date_str
    
    def execute_count_query(
        self,
        view_name: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: str = "Datetime"
    ) -> int:
        """
        Execute count query with date filtering for metadata.
        """
        try:
            # Sanitize view name
            sanitized_view_name = self._sanitize_view_name(view_name)
            
            where_conditions = []
            if from_date:
                from_ts = self._normalize_date_bound(from_date, is_start=True)
                where_conditions.append(f"`{date_column}` >= timestamp('{from_ts}')")
            if to_date:
                to_ts = self._normalize_date_bound(to_date, is_start=False)
                where_conditions.append(f"`{date_column}` <= timestamp('{to_ts}')")
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            
            count_query = f"SELECT COUNT(*) as row_count FROM {sanitized_view_name} {where_clause}"
            result = self.spark.sql(count_query).collect()
            
            count = result[0].row_count if result else 0
            print(f"[SPARKSQL] Count query result: {count} rows")
            
            return count
            
        except Exception as e:
            print(f"[SPARKSQL] Count query failed: {str(e)}")
            return 0
