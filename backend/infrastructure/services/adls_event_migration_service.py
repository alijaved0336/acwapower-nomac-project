"""
ADLS Event Migration Service

Handles real-time migration of parquet files to ClickHouse when triggered by
Azure Event Grid events. Much faster than polling - only processes the exact
file that changed.

This service:
1. Parses blob path to extract site/table info
2. Determines the ClickHouse table name
3. Migrates only the specific file (create/update) or removes data (delete)
"""

import io
import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import pyarrow as pa
import pyarrow.parquet as pq
from azure.storage.filedatalake import DataLakeServiceClient

from config.clickhouse_connector import get_clickhouse_connector
from infrastructure.services.clickhouse_deletion_service import ClickHouseDataDeletionService

logger = logging.getLogger(__name__)

class ADLSEventMigrationService:
    """
    Service to handle real-time migration triggered by Event Grid events.
    """

    # Source file column names (support both for backward compatibility)
    SOURCE_FILE_COLUMN_NAMES = ['_source_file_path', '_source_file']
    DEFAULT_SOURCE_FILE_COLUMN = '_source_file_path'  # Match migration command

    def __init__(self):
        self.storage_account = os.getenv('AZURE_STORAGE_ACCOUNT', 'mpcswrosg')
        self.filesystem_name = os.getenv('AZURE_FILESYSTEM_NAME', 'swro')
        self.database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
        # Valid base paths for parquet files
        self.valid_base_paths = ['tables/gold', 'tables']
        
        self._init_clients()

    def _init_clients(self):
        """Initialize Azure and ClickHouse clients."""
        try:
            # Azure Data Lake client - use storage key for full access
            storage_key = os.getenv('AZURE_STORAGE_KEY')
            account_url = f"https://{self.storage_account}.dfs.core.windows.net"
            self.datalake_client = DataLakeServiceClient(
                account_url=account_url,
                credential=storage_key
            )
            self.filesystem_client = self.datalake_client.get_file_system_client(
                self.filesystem_name
            )
            
            # ClickHouse client
            self.clickhouse_client = get_clickhouse_connector(auto_create_database=True)
            
            logger.info("[EVENT_MIGRATION] Initialized Azure and ClickHouse clients")
        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Failed to initialize clients: {e}")
            raise

    def process_blob_created(self, container: str, blob_path: str, event_info: Dict) -> Dict:
        """
        Process a blob created event - migrate the new/updated file to ClickHouse.
        
        Args:
            container: Container name (e.g., 'swro')
            blob_path: Full blob path (e.g., 'tables/gold/SiteName/TableName/file.parquet')
            event_info: Additional event information
            
        Returns:
            Dict with processing result
        """
        result = {
            'success': False,
            'action': 'created',
            'blob_path': blob_path,
            'rows_imported': 0,
            'error': None
        }
        
        try:
            # Validate it's a parquet file
            if not blob_path.lower().endswith('.parquet'):
                result['error'] = 'Not a parquet file'
                return result
            
            # Parse blob path to get site and table info
            parsed = self._parse_blob_path(blob_path)
            if not parsed:
                result['error'] = f'Could not parse blob path: {blob_path}'
                logger.warning(f"[EVENT_MIGRATION] {result['error']}")
                return result
            
            site_name, table_name, base_path = parsed
            result['site_name'] = site_name
            result['table_name'] = table_name
            
            # Get or create ClickHouse table name
            clickhouse_table = self._sanitize_table_name(site_name, table_name)
            result['clickhouse_table'] = clickhouse_table
            
            logger.info(f"[EVENT_MIGRATION] Processing new file: {blob_path}")
            logger.info(f"[EVENT_MIGRATION] Site: {site_name}, Table: {table_name}")
            logger.info(f"[EVENT_MIGRATION] ClickHouse table: {clickhouse_table}")
            
            # Check if table exists, create if needed
            table_exists = self._check_table_exists(clickhouse_table)

            if not table_exists:
                logger.info(f"[EVENT_MIGRATION] Table {clickhouse_table} doesn't exist, creating...")
                self._create_table_from_parquet(blob_path, clickhouse_table, site_name, table_name, base_path)
            else:
                # Ensure source file tracking column exists (check for both column names)
                source_file_column = self._get_source_file_column(clickhouse_table)
                if not source_file_column:
                    logger.info(f"[EVENT_MIGRATION] Adding {self.DEFAULT_SOURCE_FILE_COLUMN} column to {clickhouse_table}")
                    self._add_source_file_column(clickhouse_table)
                    source_file_column = self.DEFAULT_SOURCE_FILE_COLUMN

                # Table exists - delete old data from this file before importing (handles updates)
                rows_deleted = self._delete_file_data(clickhouse_table, blob_path, source_file_column)
                if rows_deleted > 0:
                    logger.info(f"[EVENT_MIGRATION] Deleted {rows_deleted} old rows for file update")
                    result['rows_deleted'] = rows_deleted

            # Import the specific file
            rows_imported = self._import_single_file(blob_path, clickhouse_table)
            result['rows_imported'] = rows_imported
            
            # Track the file
            self._track_file(clickhouse_table, blob_path, rows_imported, event_info)
            
            # Update site_table_mapping to ensure table appears in endpoint
            self._update_mapping(site_name, table_name, clickhouse_table, base_path)
            
            result['success'] = True
            self._log_success('CREATED', result)
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[EVENT_MIGRATION] Error processing blob created: {e}", exc_info=True)
        
        return result

    def process_blob_deleted(self, container: str, blob_path: str, event_info: Dict) -> Dict:
        """
        Process a blob deleted event - remove data from ClickHouse.
        
        Args:
            container: Container name
            blob_path: Full blob path
            event_info: Additional event information
            
        Returns:
            Dict with processing result
        """
        result = {
            'success': False,
            'action': 'deleted',
            'blob_path': blob_path,
            'rows_deleted': 0,
            'error': None
        }
        
        
        try:
            if not blob_path.lower().endswith('.parquet'):
                result['error'] = 'Not a parquet file'
                return result
            
            parsed = self._parse_blob_path(blob_path)
            if not parsed:
                result['error'] = f'Could not parse blob path: {blob_path}'
                return result
            
            site_name, table_name, base_path = parsed
            result['site_name'] = site_name
            result['table_name'] = table_name
            
            clickhouse_table = self._sanitize_table_name(site_name, table_name)
            result['clickhouse_table'] = clickhouse_table
            
            
            logger.info(f"[EVENT_MIGRATION] Processing deleted file: {blob_path}")
            
            # Check if table has source file tracking column (support both column names)
            source_file_column = self._get_source_file_column(clickhouse_table)
            
            
            if source_file_column:
                # Table tracks source files - delete only rows from this file
                rows_deleted = self._delete_file_data(clickhouse_table, blob_path, source_file_column)
                result['rows_deleted'] = rows_deleted
            else:
                # Table doesn't track source files - trigger full resync
                logger.warning(
                    f"[EVENT_MIGRATION] Table {clickhouse_table} lacks source file tracking column. "
                    f"Triggering full table resync to rebuild with source tracking..."
                )
                
                
                resync_result = self._resync_table_with_source_tracking(
                    site_name, table_name, base_path, clickhouse_table
                )
                result['resync_triggered'] = True
                result['resync_result'] = resync_result
                result['rows_deleted'] = resync_result.get('rows_imported', 0)
            
            # Remove file tracking (if exists)
            self._untrack_file(clickhouse_table, blob_path)
            
            # Update site_table_mapping to ensure table appears in endpoint
            self._update_mapping(site_name, table_name, clickhouse_table, base_path)
            
            result['success'] = True
            self._log_success('DELETED', result)
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[EVENT_MIGRATION] Error processing blob deleted: {e}", exc_info=True)
        
        return result

    def _parse_blob_path(self, blob_path: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse blob path to extract site name, table name, and base path.
        
        Expected formats:
        - tables/gold/{site_name}/{table_name}/file.parquet
        - tables/{site_name}/{table_name}/file.parquet
        
        Returns:
            Tuple of (site_name, table_name, base_path) or None if invalid
        """
        parts = blob_path.split('/')
        
        # Try tables/gold/{site}/{table}/file.parquet
        if len(parts) >= 5 and parts[0] == 'tables' and parts[1] == 'gold':
            site_name = parts[2]
            table_name = parts[3]
            base_path = 'tables/gold'
            return site_name, table_name, base_path
        
        # Try tables/{site}/{table}/file.parquet
        if len(parts) >= 4 and parts[0] == 'tables':
            site_name = parts[1]
            table_name = parts[2]
            base_path = 'tables'
            return site_name, table_name, base_path
        
        logger.warning(f"[EVENT_MIGRATION] Unrecognized blob path format: {blob_path}")
        return None

    def _sanitize_table_name(self, site_name: str, table_name: str) -> str:
        """Create a valid ClickHouse table name from site and table names."""
        # Clean site name
        clean_site = site_name.strip()
        if '/' in clean_site:
            clean_site = clean_site.split('/')[-1]
        
        # Clean table name
        clean_table = table_name.strip()
        if '/' in clean_table:
            clean_table = clean_table.split('/')[-1]
        
        # Combine and sanitize
        combined = f"{clean_site}_{clean_table}"
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', combined)
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')
        
        if sanitized and sanitized[0].isdigit():
            sanitized = f"t_{sanitized}"
        elif not sanitized:
            sanitized = "unknown_table"
        
        return sanitized

    def _check_table_exists(self, table_name: str) -> bool:
        """Check if ClickHouse table exists."""
        try:
            query = f"EXISTS TABLE {self.database}.{table_name}"
            result = self.clickhouse_client.query(query)
            return result.result_rows[0][0] == 1
        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Error checking table existence: {e}")
            return False

    def _create_table_from_parquet(self, blob_path: str, clickhouse_table: str,
                                    site_name: str, table_name: str, base_path: str):
        """Create ClickHouse table from parquet schema."""
        try:
            # Download parquet file to get schema
            file_client = self.filesystem_client.get_file_client(blob_path)
            download = file_client.download_file()
            content = download.readall()
            
            # Read schema
            parquet_file = pq.ParquetFile(pa.BufferReader(content))
            schema = parquet_file.schema_arrow
            
            # Generate CREATE TABLE DDL
            create_sql = self._generate_clickhouse_ddl(clickhouse_table, schema)
            
            logger.info(f"[EVENT_MIGRATION] Creating table {clickhouse_table}")
            self.clickhouse_client.command(create_sql)
            
            # Update site_table_mapping
            self._update_mapping(site_name, table_name, clickhouse_table, base_path)
            
        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Error creating table: {e}")
            raise

    def _generate_clickhouse_ddl(self, table_name: str, schema: pa.Schema) -> str:
        """Generate ClickHouse CREATE TABLE statement from PyArrow schema."""
        columns = []
        
        type_mapping = {
            'int8': 'Int8',
            'int16': 'Int16',
            'int32': 'Int32',
            'int64': 'Int64',
            'uint8': 'UInt8',
            'uint16': 'UInt16',
            'uint32': 'UInt32',
            'uint64': 'UInt64',
            'float': 'Float32',
            'double': 'Float64',
            'float32': 'Float32',
            'float64': 'Float64',
            'bool': 'Bool',
            'boolean': 'Bool',
            'string': 'String',
            'large_string': 'String',
            'binary': 'String',
            'large_binary': 'String',
            'date32': 'Date',
            'date64': 'Date',
        }
        
        for field in schema:
            field_name = field.name
            field_type = str(field.type).lower()
            
            # Handle timestamp types
            if 'timestamp' in field_type:
                ch_type = 'DateTime64(6)'
            elif field_type in type_mapping:
                ch_type = type_mapping[field_type]
            else:
                ch_type = 'String'  # Default fallback
            
            # Make nullable
            ch_type = f"Nullable({ch_type})"
            columns.append(f"    `{field_name}` {ch_type}")
        
        # Add source file tracking column (use standard name to match migration command)
        columns.append(f"    `{self.DEFAULT_SOURCE_FILE_COLUMN}` String DEFAULT ''")
        
        columns_sql = ",\n".join(columns)
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{table_name}
        (
{columns_sql}
        )
        ENGINE = MergeTree()
        ORDER BY tuple()
        """
        
        return create_sql

    def _get_clickhouse_type(self, arrow_type: str) -> str:
        """Convert PyArrow type to ClickHouse type."""
        type_mapping = {
            'int8': 'Int8',
            'int16': 'Int16',
            'int32': 'Int32',
            'int64': 'Int64',
            'uint8': 'UInt8',
            'uint16': 'UInt16',
            'uint32': 'UInt32',
            'uint64': 'UInt64',
            'float': 'Float32',
            'double': 'Float64',
            'float32': 'Float32',
            'float64': 'Float64',
            'bool': 'Bool',
            'boolean': 'Bool',
            'string': 'String',
            'large_string': 'String',
            'binary': 'String',
            'large_binary': 'String',
            'date32': 'Date',
            'date64': 'Date',
        }

        field_type = arrow_type.lower()
        if 'timestamp' in field_type:
            return 'Nullable(DateTime64(6))'
        elif 'decimal' in field_type:
            return 'Nullable(Float64)'
        elif field_type in type_mapping:
            return f"Nullable({type_mapping[field_type]})"
        else:
            return 'Nullable(String)'

    def _get_table_columns(self, table_name: str) -> set:
        """Get existing column names from ClickHouse table."""
        try:
            query = f"""
                SELECT name FROM system.columns
                WHERE database = %(database)s AND table = %(table)s
            """
            result = self.clickhouse_client.query(
                query,
                parameters={'database': self.database, 'table': table_name}
            )
            return {row[0] for row in result.result_rows}
        except Exception as e:
            logger.warning(f"[EVENT_MIGRATION] Error getting table columns: {e}")
            return set()

    def _get_column_types(self, table_name: str) -> dict:
        """Get column names and their types from ClickHouse table."""
        try:
            query = f"""
                SELECT name, type FROM system.columns
                WHERE database = %(database)s AND table = %(table)s
            """
            result = self.clickhouse_client.query(
                query,
                parameters={'database': self.database, 'table': table_name}
            )
            return {row[0]: row[1] for row in result.result_rows}
        except Exception as e:
            logger.warning(f"[EVENT_MIGRATION] Error getting column types: {e}")
            return {}

    def _add_missing_columns(self, table_name: str, schema: pa.Schema):
        """Add missing columns or fix type mismatches in ClickHouse table (schema evolution)."""
        existing_column_types = self._get_column_types(table_name)

        for field in schema:
            expected_type = self._get_clickhouse_type(str(field.type))

            if field.name not in existing_column_types:
                # Column doesn't exist - add it
                try:
                    alter_query = f"""
                        ALTER TABLE {self.database}.{table_name}
                        ADD COLUMN IF NOT EXISTS `{field.name}` {expected_type}
                    """
                    self.clickhouse_client.command(alter_query)
                    logger.info(f"[EVENT_MIGRATION] Added new column '{field.name}' ({expected_type}) to {table_name}")
                except Exception as e:
                    logger.error(f"[EVENT_MIGRATION] Error adding column '{field.name}': {e}")
                    raise
            else:
                # Column exists - check if type needs to be fixed
                current_type = existing_column_types[field.name]
                if self._needs_type_fix(current_type, expected_type):
                    try:
                        # Drop the incorrectly typed column and recreate with correct type
                        logger.info(f"[EVENT_MIGRATION] Fixing column type: '{field.name}' from {current_type} to {expected_type}")
                        drop_query = f"ALTER TABLE {self.database}.{table_name} DROP COLUMN `{field.name}`"
                        self.clickhouse_client.command(drop_query)
                        add_query = f"ALTER TABLE {self.database}.{table_name} ADD COLUMN `{field.name}` {expected_type}"
                        self.clickhouse_client.command(add_query)
                        logger.info(f"[EVENT_MIGRATION] Fixed column '{field.name}' type to {expected_type}")
                    except Exception as e:
                        logger.error(f"[EVENT_MIGRATION] Error fixing column type '{field.name}': {e}")
                        raise

    def _needs_type_fix(self, current_type: str, expected_type: str) -> bool:
        """Check if column type needs to be fixed (e.g., String should be Float64)."""
        # Normalize types for comparison
        current = current_type.replace('Nullable(', '').replace(')', '').strip()
        expected = expected_type.replace('Nullable(', '').replace(')', '').strip()

        # If types are the same, no fix needed
        if current == expected:
            return False

        # If current is String but expected is numeric, fix needed
        if current == 'String' and expected in ('Float64', 'Float32', 'Int64', 'Int32', 'DateTime64(6)'):
            return True

        return False

    def _convert_value(self, value, column_name: str, column_types: dict):
        """Convert a value to be compatible with its ClickHouse column type."""
        import pandas as pd
        from decimal import Decimal

        if pd.isna(value):
            return None

        ch_type = column_types.get(column_name, '')

        # If column is String type, convert everything to string
        if 'String' in ch_type:
            if isinstance(value, (Decimal, float, int)):
                return str(value)
            elif isinstance(value, pd.Timestamp):
                return value.isoformat()
            return str(value) if value is not None else None

        # For numeric columns, convert appropriately
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        elif isinstance(value, Decimal):
            return float(value)

        return value

    def _import_single_file(self, blob_path: str, clickhouse_table: str) -> int:
        """Import a single parquet file to ClickHouse."""
        import pandas as pd

        try:
            # Download parquet file
            file_client = self.filesystem_client.get_file_client(blob_path)
            download = file_client.download_file()
            content = download.readall()

            # Read parquet file
            parquet_file = pq.ParquetFile(pa.BufferReader(content))

            # Schema evolution: add any new columns from parquet to ClickHouse
            self._add_missing_columns(clickhouse_table, parquet_file.schema_arrow)

            # Get source file column name (support both for backward compatibility)
            source_file_column = self._get_source_file_column(clickhouse_table)
            if not source_file_column:
                # Add the column if it doesn't exist
                self._add_source_file_column(clickhouse_table)
                source_file_column = self.DEFAULT_SOURCE_FILE_COLUMN

            # Get column types for proper value conversion
            column_types = self._get_column_types(clickhouse_table)

            total_rows = 0
            batch_size = 10000

            # Process in batches
            for batch in parquet_file.iter_batches(batch_size=batch_size):
                df = batch.to_pandas()

                if df.empty:
                    continue

                # Add source file column (use detected column name)
                df = df.copy()
                df[source_file_column] = blob_path

                # Convert DataFrame to list of tuples for ClickHouse
                columns = list(df.columns)
                data_rows = []
                for _, row in df.iterrows():
                    converted_row = []
                    for col_name, value in zip(columns, row):
                        converted_row.append(self._convert_value(value, col_name, column_types))
                    data_rows.append(tuple(converted_row))

                # Insert to ClickHouse
                self.clickhouse_client.insert(
                    f"{self.database}.{clickhouse_table}",
                    data_rows,
                    column_names=list(df.columns)
                )
                total_rows += len(data_rows)

            logger.info(f"[EVENT_MIGRATION] Imported {total_rows} rows from {blob_path}")
            return total_rows

        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Error importing file {blob_path}: {e}")
            raise

    def _delete_file_data(self, clickhouse_table: str, blob_path: str, source_file_column: str = None) -> int:
        """Delete data associated with a specific file from ClickHouse."""
        
        try:
            # Get source file column name if not provided
            if not source_file_column:
                source_file_column = self._get_source_file_column(clickhouse_table)
            
            if not source_file_column:
                logger.warning(
                    f"[EVENT_MIGRATION] Table {clickhouse_table} doesn't have source file tracking column. "
                    f"Cannot delete specific file data. This table was likely created by old migration. "
                    f"File tracking will be removed, but data remains in ClickHouse."
                )
                return 0
            
            # First count rows to be deleted
            count_query = f"""
                SELECT COUNT(*) FROM {self.database}.{clickhouse_table}
                WHERE `{source_file_column}` = %(file_path)s
            """
            result = self.clickhouse_client.query(
                count_query,
                parameters={'file_path': blob_path}
            )
            rows_to_delete = result.result_rows[0][0] if result.result_rows else 0
            
            
            if rows_to_delete > 0:
                # Delete the rows
                delete_query = f"""
                    ALTER TABLE {self.database}.{clickhouse_table}
                    DELETE WHERE `{source_file_column}` = %(file_path)s
                """
                self.clickhouse_client.command(
                    delete_query,
                    parameters={'file_path': blob_path}
                )
                logger.info(f"[EVENT_MIGRATION] Deleted {rows_to_delete} rows for {blob_path}")
            
            return rows_to_delete
            
        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Error deleting file data: {e}")
            return 0

    def _resync_table_with_source_tracking(self, site_name: str, table_name: str,
                                            base_path: str, clickhouse_table: str) -> Dict:
        """
        Full table resync - drop table, recreate with source file tracking, and re-import all remaining files.
        
        Used when a file is deleted from a table that doesn't have source file tracking column.
        After resync, the table will have source file tracking column and future deletions will work.
        """
        result = {'success': False, 'rows_imported': 0, 'files_processed': 0}
        
        try:
            # Get table path in ADLS
            table_path = f"{base_path}/{site_name}/{table_name}"
            
            # List all remaining parquet files
            remaining_files = self._list_parquet_files(table_path)
            
            
            # SAFETY CHECK: If listing failed (None), don't drop the table
            if remaining_files is None:
                logger.error(
                    f"[EVENT_MIGRATION] SAFETY: Could not list files in {table_path}. "
                    f"NOT dropping table {clickhouse_table} to prevent data loss. "
                    f"Manual intervention required."
                )
                result['error'] = 'Failed to list files - table preserved for safety'
                result['success'] = False
                return result
            
            if len(remaining_files) == 0:
                # Double-check by verifying the path exists
                logger.warning(
                    f"[EVENT_MIGRATION] No remaining files found in {table_path}. "
                    f"Table {clickhouse_table} will be preserved (not dropped) for safety. "
                    f"Run full migration to clean up if needed."
                )
                result['success'] = True
                result['note'] = 'No files found but table preserved for safety'
                return result
            
            logger.info(f"[EVENT_MIGRATION] Resync: Found {len(remaining_files)} remaining files in {table_path}")
            
            # Drop the existing table (will be recreated with source file tracking column)
            self._drop_table(clickhouse_table)
            
            # Get schema from first file and create table with source file tracking column
            first_file = remaining_files[0]
            self._create_table_from_parquet(first_file, clickhouse_table, site_name, table_name, base_path)
            
            # Re-import all remaining files
            total_rows = 0
            for file_path in remaining_files:
                try:
                    rows = self._import_single_file(file_path, clickhouse_table)
                    total_rows += rows
                    result['files_processed'] += 1
                except Exception as e:
                    logger.error(f"[EVENT_MIGRATION] Error importing {file_path} during resync: {e}")
            
            result['rows_imported'] = total_rows
            result['success'] = True
            
            # Update site_table_mapping to ensure table appears in endpoint
            self._update_mapping(site_name, table_name, clickhouse_table, base_path)
            
            logger.info(
                f"[EVENT_MIGRATION] Resync complete: {result['files_processed']} files, "
                f"{total_rows} rows imported to {clickhouse_table} (now with {self.DEFAULT_SOURCE_FILE_COLUMN} tracking)"
            )
            
        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Resync failed: {e}", exc_info=True)
            result['error'] = str(e)
            
        
        return result

    def _list_parquet_files(self, table_path: str) -> list:
        """List all parquet files in a table directory."""
        files = []
        try:
            
            paths = self.filesystem_client.get_paths(path=table_path, recursive=True)
            for path in paths:
                if not path.is_directory and path.name.endswith('.parquet'):
                    files.append(path.name)
            
            
        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Error listing files in {table_path}: {e}")
            # Return None to indicate error, not empty list
            return None
        return files

    def _drop_table(self, clickhouse_table: str):
        """Drop a ClickHouse table."""
        try:
            query = f"DROP TABLE IF EXISTS {self.database}.{clickhouse_table}"
            self.clickhouse_client.command(query)
            logger.info(f"[EVENT_MIGRATION] Dropped table {clickhouse_table}")
        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Error dropping table: {e}")
            raise
    
    def _check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in the ClickHouse table."""
        try:
            query = f"""
                SELECT name 
                FROM system.columns 
                WHERE database = %(database)s 
                  AND table = %(table)s 
                  AND name = %(column)s
            """
            result = self.clickhouse_client.query(
                query,
                parameters={
                    'database': self.database,
                    'table': table_name,
                    'column': column_name
                }
            )
            exists = len(result.result_rows) > 0
            
            
            return exists
        except Exception as e:
            logger.warning(f"[EVENT_MIGRATION] Error checking column existence: {e}")
            return False

    def _get_source_file_column(self, table_name: str) -> Optional[str]:
        """
        Get the source file tracking column name for a table.
        Checks for both _source_file_path and _source_file for backward compatibility.
        
        Returns:
            Column name if found, None otherwise
        """
        for column_name in self.SOURCE_FILE_COLUMN_NAMES:
            if self._check_column_exists(table_name, column_name):
                logger.debug(f"[EVENT_MIGRATION] Found source file column '{column_name}' in {table_name}")
                return column_name
        return None

    def _add_source_file_column(self, table_name: str):
        """Add source file tracking column to an existing table (uses standard name)."""
        try:
            alter_query = f"""
                ALTER TABLE {self.database}.{table_name}
                ADD COLUMN IF NOT EXISTS `{self.DEFAULT_SOURCE_FILE_COLUMN}` String DEFAULT ''
            """
            self.clickhouse_client.command(alter_query)
            logger.info(f"[EVENT_MIGRATION] Added {self.DEFAULT_SOURCE_FILE_COLUMN} column to {table_name}")
        except Exception as e:
            logger.error(f"[EVENT_MIGRATION] Error adding {self.DEFAULT_SOURCE_FILE_COLUMN} column: {e}")
            raise

    def _track_file(self, clickhouse_table: str, blob_path: str,
                    row_count: int, event_info: Dict):
        """Track imported file in parquet_file_tracking table."""
        try:
            # Use column names that match production schema
            insert_query = f"""
                INSERT INTO {self.database}.parquet_file_tracking
                (clickhouse_table_name, file_path, rows_imported, last_modified,
                 file_size, import_date, import_status)
                VALUES
                (%(clickhouse_table_name)s, %(file_path)s, %(rows_imported)s,
                 %(last_modified)s, %(file_size)s, %(import_date)s, %(import_status)s)
            """

            self.clickhouse_client.command(
                insert_query,
                parameters={
                    'clickhouse_table_name': clickhouse_table,
                    'file_path': blob_path,
                    'rows_imported': row_count,
                    'last_modified': datetime.now(timezone.utc),
                    'file_size': event_info.get('content_length', 0),
                    'import_date': datetime.now(timezone.utc),
                    'import_status': 'success'
                }
            )
        except Exception as e:
            logger.warning(f"[EVENT_MIGRATION] Could not track file: {e}")

    def _untrack_file(self, clickhouse_table: str, blob_path: str):
        """Remove file from tracking table."""
        try:
            delete_query = f"""
                ALTER TABLE {self.database}.parquet_file_tracking
                DELETE WHERE clickhouse_table_name = %(table)s AND file_path = %(path)s
            """
            self.clickhouse_client.command(
                delete_query,
                parameters={'table': clickhouse_table, 'path': blob_path}
            )
        except Exception as e:
            logger.warning(f"[EVENT_MIGRATION] Could not untrack file: {e}")

    def _update_mapping(self, site_name: str, table_name: str,
                        clickhouse_table: str, base_path: str):
        """Update site_table_mapping in ClickHouse."""
        try:
            insert_query = f"""
                INSERT INTO {self.database}.site_table_mapping
                (site_name, table_name, clickhouse_table_name, parquet_path, 
                 base_path, migration_status, row_count, migration_date)
                VALUES
                (%(site)s, %(table)s, %(ch_table)s, %(path)s, 
                 %(base_path)s, 'migrated', 0, now())
            """
            self.clickhouse_client.command(
                insert_query,
                parameters={
                    'site': site_name,
                    'table': table_name,
                    'ch_table': clickhouse_table,
                    'path': f"{base_path}/{site_name}/{table_name}",
                    'base_path': base_path
                }
            )
            logger.info(f"[EVENT_MIGRATION] Updated site_table_mapping for {site_name}.{table_name} -> {clickhouse_table}")
        except Exception as e:
            logger.warning(f"[EVENT_MIGRATION] Could not update mapping: {e}")

    def _log_success(self, action: str, result: Dict):
        """Log successful operation."""
        separator = "=" * 70
        emoji = "📁" if action == 'CREATED' else "🗑️"
        
        rows_affected = result.get('rows_imported', 0) or result.get('rows_deleted', 0)
        
        # Additional info for resync
        resync_info = ""
        if result.get('resync_triggered'):
            resync_result = result.get('resync_result', {})
            resync_info = f"""
Resync Triggered: Yes (table lacked source file tracking column)
Files Reprocessed:{resync_result.get('files_processed', 0)}
Rows Re-imported: {resync_result.get('rows_imported', 0)}
Note:             Future deletions will work correctly"""
            rows_affected = resync_result.get('rows_imported', 0)
        
        log_msg = f"""
{separator}
{emoji} EVENT MIGRATION: {action} - SUCCESS
{separator}
Blob Path:        {result.get('blob_path')}
Site:             {result.get('site_name')}
Table:            {result.get('table_name')}
ClickHouse Table: {result.get('clickhouse_table')}
Rows Affected:    {rows_affected}{resync_info}
{separator}
"""
        logger.info(log_msg)
        print(log_msg)

    def close(self):
        """Close connections."""
        if hasattr(self, 'clickhouse_client') and self.clickhouse_client:
            self.clickhouse_client.close()

def get_event_migration_service() -> ADLSEventMigrationService:
    """
    Create a new migration service instance for each request.

    IMPORTANT: Each request needs its own instance because ClickHouse's
    clickhouse_connect library does not support concurrent queries within
    the same session. When multiple Event Grid webhooks arrive simultaneously,
    each needs its own ClickHouse client to avoid "concurrent queries within
    the same session" errors.

    The caller should close the service when done using service.close().
    """
    return ADLSEventMigrationService()

