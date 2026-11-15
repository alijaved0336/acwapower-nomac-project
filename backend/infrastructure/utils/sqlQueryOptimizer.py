from typing import Optional, Dict
from pyspark.sql import SparkSession
from infrastructure.utils.sql.parquetQueryBuilder import ParquetQueryBuilder
from infrastructure.utils.sql.columnMetadataBuilder import ColumnMetadataBuilder


class SqlQueryOptimizer:
    """
    Production-ready SQL query optimizer.
    """
    
    def __init__(self, spark_session: SparkSession):
        self.spark = spark_session
        self.base_file_path = "wasbs://swro@mpcswrosg.blob.core.windows.net/tables"
        self.query_builder = ParquetQueryBuilder(self.base_file_path)
        self.metadata_builder = ColumnMetadataBuilder()

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
    
    def execute_metadata_query_optimized(
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
        Execute optimized metadata query using timestamp-safe direct SQL.
        
        Args:
            coordinates: If True, read from coordinates data; if False, read from gold data
        """
        try:
            data_type = "coordinates" if coordinates else "gold"
            print(f"[SQL_OPTIMIZER] Using timestamp-safe direct parquet query for {data_type} data")
            
            # Try timestamp-safe direct query first
            try:
                timestamp_safe_query = self.query_builder.create_timestamp_safe_parquet_query(
                    siteName=siteName,
                    tableName=tableName,
                    from_date=from_date,
                    to_date=to_date,
                    columns=None,
                    limit=sample_size,
                    coordinates=coordinates
                )
                
                print(f"[SQL_OPTIMIZER] Executing timestamp-safe query for {data_type} data")
                sample_df = self.spark.sql(timestamp_safe_query)
                sample_data = sample_df.collect()
                
                # Get schema from the result
                schema_info = []
                if sample_data:
                    for field in sample_df.schema.fields:
                        schema_info.append({
                            'col_name': field.name,
                            'data_type': str(field.dataType),
                            'nullable': field.nullable
                        })
                
                print(f"[SQL_OPTIMIZER] Timestamp-safe query successful: {len(sample_data)} rows from {data_type} data")
                
                # Build column metadata
                columns = self.metadata_builder.build_column_metadata_from_schema(schema_info, sample_data, tableName)
                
                return {
                    "columns": columns,
                    "date_filter": {
                        "from_date": from_date,
                        "to_date": to_date,
                        "date_column": date_column,
                        "rows_in_range": len(sample_data),
                        "sample_size": len(sample_data),
                        "method": f"timestamp_safe_sql_{data_type}",
                        "data_source": data_type
                    },
                    "performance": {
                        "query_method": f"timestamp_safe_parquet_sql_{data_type}",
                        "optimization_level": "maximum",
                        "data_source": data_type
                    }
                }
                
            except Exception as timestamp_error:
                print(f"[SQL_OPTIMIZER] Timestamp-safe query failed: {timestamp_error}")
                
                # Fallback to view-based approach
                data_suffix = "_coord" if coordinates else "_gold"
                table_alias = f"{siteName}_{tableName}{data_suffix}_sql"
                
                print(f"[SQL_OPTIMIZER] Falling back to view-based approach: {table_alias} for {data_type} data")
                
                # Step 1: Create parquet table
                create_table_sql = self.query_builder.create_parquet_table_sql(
                    siteName, tableName, table_alias, coordinates=coordinates
                )
                self.spark.sql(create_table_sql)
                
                # Step 2: Get schema efficiently
                schema_df = self.spark.sql(self.query_builder.get_table_schema_sql(table_alias))
                schema_info = schema_df.collect()
                
                # Step 3: Get sample data with optimized query
                sample_query = self.query_builder.build_optimized_column_query(
                    table_alias=table_alias,
                    columns=None,
                    from_date=from_date,
                    to_date=to_date,
                    date_column=date_column,
                    sample_size=sample_size
                )
                
                print(f"[SQL_OPTIMIZER] Executing view-based sample query for {data_type} data")
                sample_df = self.spark.sql(sample_query)
                sample_data = sample_df.collect()
                
                # Step 4: Build column metadata
                columns = self.metadata_builder.build_column_metadata(schema_info, sample_data, tableName)
                
                # Cleanup
                self.spark.sql(f"DROP VIEW IF EXISTS {table_alias}")
                
                print(f"[SQL_OPTIMIZER] View-based approach successful: {len(sample_data)} rows from {data_type} data")
                
                return {
                    "columns": columns,
                    "date_filter": {
                        "from_date": from_date,
                        "to_date": to_date,
                        "date_column": date_column,
                        "rows_in_range": len(sample_data),
                        "sample_size": len(sample_data),
                        "method": f"view_based_sql_{data_type}",
                        "data_source": data_type
                    },
                    "performance": {
                        "query_method": f"view_based_parquet_sql_{data_type}",
                        "optimization_level": "high",
                        "data_source": data_type
                    }
                }
            
        except Exception as e:
            # Cleanup on error
            try:
                data_suffix = "_coord" if coordinates else "_gold"
                table_alias = f"{siteName}_{tableName}{data_suffix}_sql"
                self.spark.sql(f"DROP VIEW IF EXISTS {table_alias}")
            except:
                pass
            raise Exception(f"SQL optimization failed: {str(e)}")