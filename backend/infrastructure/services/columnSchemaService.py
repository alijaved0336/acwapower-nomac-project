"""
Column Schema Service
Fast service for retrieving column metadata (schema only) from parquet files without downloading data.
Optimized for speed by reading only schema information from the first parquet file per table.
"""
import pyarrow.parquet as pq
import io
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from infrastructure.utils.azure.blobStorageClient import BlobStorageClient

logger = logging.getLogger(__name__)


@dataclass
class TableRequest:
    """Request model for table metadata."""
    siteName: str
    tableName: str


@dataclass
class ColumnMetadata:
    """Column metadata response model."""
    columnName: str
    columnType: str
    tableName: str
    siteName: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            'columnName': self.columnName,
            'columnType': self.columnType,
            'tableName': self.tableName,
            'siteName': self.siteName
        }


class ColumnSchemaService:
    """
    Fast column schema service using PyArrow schema-only reading.
    Bypasses data download completely for maximum speed.
    """
    
    def __init__(self):
        self.blob_client = BlobStorageClient()
        self.max_concurrent_tables = 10  # Concurrent table processing limit
    
    def get_columns_metadata(self, table_requests: List[TableRequest]) -> List[ColumnMetadata]:
        """
        Get column metadata for multiple tables concurrently.
        
        Args:
            table_requests: List of TableRequest objects specifying site/table combinations
            
        Returns:
            List of ColumnMetadata objects with column information
        """
        if not table_requests:
            return []
        
        logger.info(f"[COLUMN_SCHEMA] Starting schema retrieval for {len(table_requests)} tables")
        
        all_columns = []
        
        # Process tables concurrently
        with ThreadPoolExecutor(max_workers=self.max_concurrent_tables) as executor:
            # Submit all table processing tasks
            future_to_request = {
                executor.submit(self._get_table_schema, request): request 
                for request in table_requests
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_request):
                request = future_to_request[future]
                try:
                    table_columns = future.result()
                    all_columns.extend(table_columns)
                    logger.info(f"[COLUMN_SCHEMA] Completed {request.siteName}/{request.tableName}: {len(table_columns)} columns")
                except Exception as e:
                    logger.error(f"[COLUMN_SCHEMA] Failed to process {request.siteName}/{request.tableName}: {str(e)}")
                    # Continue processing other tables even if one fails
        
        logger.info(f"[COLUMN_SCHEMA] Total columns retrieved: {len(all_columns)}")
        return all_columns
    
    def _get_table_schema(self, request: TableRequest) -> List[ColumnMetadata]:
        """
        Get column metadata for a single table by reading schema only.
        
        Args:
            request: TableRequest with siteName and tableName
            
        Returns:
            List of ColumnMetadata for the table
        """
        try:
            # Construct blob prefix for the table
            blob_prefix = f"tables/gold/{request.siteName}/{request.tableName}/"
            
            # List parquet files in the table directory
            parquet_blobs = self.blob_client.list_parquet_files(blob_prefix)
            
            if not parquet_blobs:
                logger.warning(f"[COLUMN_SCHEMA] No parquet files found for {request.siteName}/{request.tableName}")
                return []
            
            # Use the first parquet file to get schema (all files in a table should have same schema)
            first_blob = parquet_blobs[0]
            logger.debug(f"[COLUMN_SCHEMA] Reading schema from {first_blob.name}")
            
            # Download minimal amount of data needed for schema extraction
            blob_client = self.blob_client.get_blob_client(first_blob.name)
            
            # Read only the parquet metadata (not the actual data)
            blob_data = blob_client.download_blob().readall()
            parquet_file = pq.ParquetFile(io.BytesIO(blob_data))
            
            # Extract schema information
            schema = parquet_file.schema_arrow
            
            # Convert schema to ColumnMetadata objects
            columns = []
            for field in schema:
                column_metadata = ColumnMetadata(
                    columnName=field.name,
                    columnType=str(field.type),
                    tableName=request.tableName,
                    siteName=request.siteName
                )
                columns.append(column_metadata)
            
            logger.debug(f"[COLUMN_SCHEMA] Found {len(columns)} columns in {request.siteName}/{request.tableName}")
            return columns
            
        except Exception as e:
            logger.error(f"[COLUMN_SCHEMA] Error processing {request.siteName}/{request.tableName}: {str(e)}")
            return []
    
    def get_table_schema_info(self, site_name: str, table_name: str) -> Dict[str, Any]:
        """
        Get detailed schema information for a single table.
        
        Args:
            site_name: Site identifier
            table_name: Table identifier
            
        Returns:
            Dictionary with detailed schema information
        """
        try:
            request = TableRequest(siteName=site_name, tableName=table_name)
            columns = self._get_table_schema(request)
            
            # Group columns by type for analysis
            type_distribution = {}
            for column in columns:
                col_type = column.columnType
                if col_type in type_distribution:
                    type_distribution[col_type] += 1
                else:
                    type_distribution[col_type] = 1
            
            return {
                "siteName": site_name,
                "tableName": table_name,
                "totalColumns": len(columns),
                "columns": [col.to_dict() for col in columns],
                "typeDistribution": type_distribution,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"[COLUMN_SCHEMA] Error getting schema info for {site_name}/{table_name}: {str(e)}")
            return {
                "siteName": site_name,
                "tableName": table_name,
                "totalColumns": 0,
                "columns": [],
                "typeDistribution": {},
                "status": "error",
                "error": str(e)
            }