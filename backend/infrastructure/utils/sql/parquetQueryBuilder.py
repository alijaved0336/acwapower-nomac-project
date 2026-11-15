from typing import Optional, List


class ParquetQueryBuilder:
    """
    Builds SQL queries for direct parquet file access.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def create_parquet_table_sql(
        self,
        siteName: str,
        tableName: str,
        table_alias: str = "parquet_data"
    ) -> str:
        """
        Create SQL statement to directly query parquet files with timestamp compatibility.
        """
        parquet_path = f"{self.file_path}/{siteName}/{tableName}"
        
        # Enhanced SQL with timestamp compatibility options
        sql_statement = f"""
        CREATE OR REPLACE TEMPORARY VIEW {table_alias}
        USING PARQUET
        OPTIONS (
            path '{parquet_path}',
            timestampFormat 'yyyy-MM-dd HH:mm:ss.SSSSSS',
            timestampNTZFormat 'yyyy-MM-dd HH:mm:ss.SSSSSS',
            mergeSchema 'false',
            recursiveFileLookup 'true',
            'spark.sql.parquet.outputTimestampType' 'TIMESTAMP_MICROS',
            'spark.sql.parquet.timestampType' 'TIMESTAMP_MICROS',
            'spark.sql.parquet.enableVectorizedReader' 'false',
            'spark.sql.parquet.readLegacyFormat' 'true',
            'spark.sql.parquet.int96RebaseModeInRead' 'CORRECTED',
            'spark.sql.parquet.datetimeRebaseModeInRead' 'CORRECTED'
        )
        """
        
        return sql_statement.strip()
    
    def create_timestamp_safe_parquet_query(
        self,
        siteName: str,
        tableName: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        columns: Optional[List[str]] = None,
        limit: int = 100
    ) -> str:
        """
        Create timestamp-safe direct parquet query bypassing views.
        """
        parquet_path = f"{self.file_path}/{siteName}/{tableName}"
        
        # Column selection
        if columns:
            select_cols = ", ".join([f"`{col}`" for col in columns])
        else:
            select_cols = "*"
        
        # Build where clause with timestamp casting for safety
        where_conditions = []
        if from_date:
            where_conditions.append(f"CAST(`Datetime` AS STRING) >= '{from_date} 00:00:00'")
        if to_date:
            where_conditions.append(f"CAST(`Datetime` AS STRING) <= '{to_date} 23:59:59'")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        # Direct parquet query with timestamp safety
        query = f"""
        SELECT {select_cols}
        FROM parquet.`{parquet_path}`
        {where_clause}
        ORDER BY CAST(`Datetime` AS STRING) DESC
        LIMIT {limit}
        """
        
        return query.strip()
    
    def build_optimized_column_query(
        self,
        table_alias: str,
        columns: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: str = "Datetime",
        sample_size: int = 100
    ) -> str:
        """
        Build optimized query for column metadata retrieval.
        """
        # Column selection
        if columns:
            select_cols = ", ".join([f"`{col}`" for col in columns])
        else:
            select_cols = "*"
        
        # Date filtering
        where_conditions = []
        if from_date:
            where_conditions.append(f"CAST(`{date_column}` AS STRING) >= '{from_date} 00:00:00'")
        if to_date:
            where_conditions.append(f"CAST(`{date_column}` AS STRING) <= '{to_date} 23:59:59'")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        return f"""
        SELECT {select_cols}
        FROM {table_alias}
        {where_clause}
        ORDER BY CAST(`{date_column}` AS STRING) DESC
        LIMIT {sample_size}
        """.strip()
    
    def get_table_schema_sql(self, table_alias: str) -> str:
        """
        Get table schema information.
        """
        return f"DESCRIBE {table_alias}"
    
    def get_fast_count_sql(
        self,
        table_alias: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: str = "Datetime"
    ) -> str:
        """
        Get fast row count with optional date filtering.
        """
        where_conditions = []
        if from_date:
            where_conditions.append(f"CAST(`{date_column}` AS STRING) >= '{from_date} 00:00:00'")
        if to_date:
            where_conditions.append(f"CAST(`{date_column}` AS STRING) <= '{to_date} 23:59:59'")
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        return f"SELECT COUNT(*) as row_count FROM {table_alias} {where_clause}"
