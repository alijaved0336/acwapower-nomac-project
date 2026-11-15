"""
ClickHouse Data Deletion Service

Handles automatic deletion of ClickHouse data when source parquet files
are removed from ADLS. Uses source file tracking for precise row-level deletion.

Usage:
    from infrastructure.services.clickhouse_deletion_service import ClickHouseDataDeletionService

    service = ClickHouseDataDeletionService(clickhouse_client)
    result = service.delete_data_for_files(
        clickhouse_table_name='Rabigh3_Chemicals_ppm',
        file_paths=['tables/gold/Rabigh3/file1.parquet', 'tables/gold/Rabigh3/file2.parquet']
    )
"""

import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ClickHouseDataDeletionService:
    """
    Service for deleting ClickHouse data when source parquet files are removed from ADLS.

    Deletion Strategy:
    - Uses `_source_file_path` column for precise row-level deletion
    - Executes ALTER TABLE DELETE mutation
    - Monitors mutation progress with configurable timeout
    - Returns detailed result with rows deleted count

    Attributes:
        SOURCE_FILE_COLUMN: Column name used for source file tracking
        MAX_FILES_PER_BATCH: Maximum files per DELETE IN clause
        MUTATION_TIMEOUT_SECONDS: Maximum wait time for mutations
        MUTATION_CHECK_INTERVAL: Seconds between mutation status checks
    """

    SOURCE_FILE_COLUMN = '_source_file_path'
    MAX_FILES_PER_BATCH = 100
    MUTATION_TIMEOUT_SECONDS = 3600  # 1 hour
    MUTATION_CHECK_INTERVAL = 5  # seconds

    def __init__(self, clickhouse_client):
        """
        Initialize the deletion service.

        Args:
            clickhouse_client: ClickHouse connection client (clickhouse_connect)
        """
        self.client = clickhouse_client
        self.database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

    def delete_data_for_files(
        self,
        clickhouse_table_name: str,
        file_paths: List[str],
        wait_for_completion: bool = True
    ) -> Dict:
        """
        Delete ClickHouse data for specified source parquet files.

        Executes precise row-level deletion using the _source_file_path column.
        If the column doesn't exist, returns error with instructions.

        Args:
            clickhouse_table_name: Target ClickHouse table name
            file_paths: List of ADLS file paths whose data should be deleted
            wait_for_completion: Whether to wait for mutations to complete

        Returns:
            Dict with keys:
                - success (bool): Whether deletion completed successfully
                - rows_deleted (int): Number of rows deleted
                - method_used (str): Always 'source_file_column'
                - files_processed (int): Number of files processed
                - errors (List[str]): Any errors encountered
                - duration_seconds (float): Time taken for operation
                - mutation_ids (List[str]): IDs of submitted mutations
        """
        start_time = datetime.now()
        result = {
            'success': False,
            'rows_deleted': 0,
            'method_used': 'source_file_column',
            'files_processed': 0,
            'errors': [],
            'duration_seconds': 0,
            'mutation_ids': []
        }

        if not file_paths:
            result['success'] = True
            result['method_used'] = 'no_files'
            logger.info("No files to delete - empty file list provided")
            return result

        try:
            # Validate table exists
            if not self._table_exists(clickhouse_table_name):
                error_msg = f"Table {self.database}.{clickhouse_table_name} does not exist"
                result['errors'].append(error_msg)
                logger.error(error_msg)
                return result

            # Check for source file column
            if not self._has_source_file_column(clickhouse_table_name):
                error_msg = (
                    f"Table {clickhouse_table_name} does not have '{self.SOURCE_FILE_COLUMN}' column. "
                    f"Run 'python manage.py add_source_tracking --table={clickhouse_table_name}' first."
                )
                result['errors'].append(error_msg)
                logger.error(error_msg)
                return result

            logger.info(
                f"Starting deletion for {len(file_paths)} files from "
                f"{self.database}.{clickhouse_table_name}"
            )

            # Get row count before deletion
            count_before = self._get_row_count(clickhouse_table_name)
            logger.info(f"Row count before deletion: {count_before}")

            # Process files in batches
            mutation_ids = []
            for i in range(0, len(file_paths), self.MAX_FILES_PER_BATCH):
                batch = file_paths[i:i + self.MAX_FILES_PER_BATCH]
                batch_num = (i // self.MAX_FILES_PER_BATCH) + 1
                total_batches = (len(file_paths) + self.MAX_FILES_PER_BATCH - 1) // self.MAX_FILES_PER_BATCH

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)")

                mutation_id = self._submit_deletion_mutation(
                    clickhouse_table_name, batch
                )

                if mutation_id:
                    mutation_ids.append(mutation_id)
                    result['files_processed'] += len(batch)
                else:
                    result['errors'].append(f"Failed to submit deletion for batch {batch_num}")

            result['mutation_ids'] = mutation_ids

            # Wait for mutations to complete if requested
            if wait_for_completion and mutation_ids:
                logger.info(f"Waiting for {len(mutation_ids)} mutations to complete...")
                mutations_completed = self._wait_for_mutations(
                    clickhouse_table_name,
                    timeout_seconds=self.MUTATION_TIMEOUT_SECONDS
                )

                if not mutations_completed:
                    result['errors'].append(
                        f"Mutation timeout after {self.MUTATION_TIMEOUT_SECONDS} seconds. "
                        "Deletion may still be in progress."
                    )

            # Get row count after deletion
            count_after = self._get_row_count(clickhouse_table_name)
            result['rows_deleted'] = max(0, count_before - count_after)

            logger.info(
                f"Deletion complete: {result['rows_deleted']} rows deleted "
                f"(before: {count_before}, after: {count_after})"
            )

            result['success'] = len(result['errors']) == 0

        except Exception as e:
            error_msg = f"Deletion failed with exception: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result['errors'].append(error_msg)

        result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
        return result

    def _submit_deletion_mutation(
        self,
        table_name: str,
        file_paths: List[str]
    ) -> Optional[str]:
        """
        Submit a DELETE mutation for specified file paths.

        Args:
            table_name: ClickHouse table name
            file_paths: List of file paths to delete data for

        Returns:
            Mutation ID if successful, None otherwise
        """
        try:
            # Escape single quotes in paths
            escaped_paths = [p.replace("'", "''") for p in file_paths]
            paths_str = "', '".join(escaped_paths)

            delete_sql = f"""
            ALTER TABLE {self.database}.{table_name}
            DELETE WHERE `{self.SOURCE_FILE_COLUMN}` IN ('{paths_str}')
            """

            logger.debug(f"Executing deletion: {delete_sql[:200]}...")
            self.client.query(delete_sql)

            # Get the mutation ID from system.mutations
            mutation_query = f"""
            SELECT mutation_id
            FROM system.mutations
            WHERE database = '{self.database}'
              AND table = '{table_name}'
            ORDER BY create_time DESC
            LIMIT 1
            """

            result = self.client.query(mutation_query)
            if result.result_rows:
                mutation_id = result.result_rows[0][0]
                logger.debug(f"Submitted mutation: {mutation_id}")
                return mutation_id

            return "unknown"

        except Exception as e:
            logger.error(f"Failed to submit deletion mutation: {e}")
            return None

    def _wait_for_mutations(
        self,
        table_name: str,
        timeout_seconds: int = None
    ) -> bool:
        """
        Wait for all pending mutations on a table to complete.

        Args:
            table_name: ClickHouse table name
            timeout_seconds: Maximum wait time (uses class default if None)

        Returns:
            True if all mutations completed, False if timeout reached
        """
        timeout = timeout_seconds or self.MUTATION_TIMEOUT_SECONDS
        start_time = time.time()

        while time.time() - start_time < timeout:
            pending_count = self._get_pending_mutation_count(table_name)

            if pending_count == 0:
                logger.info("All mutations completed successfully")
                return True

            elapsed = int(time.time() - start_time)
            logger.debug(
                f"Waiting for {pending_count} mutations to complete "
                f"({elapsed}s elapsed)..."
            )
            time.sleep(self.MUTATION_CHECK_INTERVAL)

        logger.warning(f"Mutation timeout reached after {timeout} seconds")
        return False

    def _get_pending_mutation_count(self, table_name: str) -> int:
        """Get count of pending (not done) mutations for a table."""
        try:
            query = f"""
            SELECT COUNT(*)
            FROM system.mutations
            WHERE database = '{self.database}'
              AND table = '{table_name}'
              AND is_done = 0
            """
            result = self.client.query(query)
            return result.result_rows[0][0] if result.result_rows else 0
        except Exception as e:
            logger.warning(f"Could not check mutation status: {e}")
            return 0

    def _has_source_file_column(self, table_name: str) -> bool:
        """
        Check if table has the _source_file_path column.

        Args:
            table_name: ClickHouse table name

        Returns:
            True if column exists, False otherwise
        """
        try:
            query = f"""
            SELECT COUNT(*)
            FROM system.columns
            WHERE database = '{self.database}'
              AND table = '{table_name}'
              AND name = '{self.SOURCE_FILE_COLUMN}'
            """
            result = self.client.query(query)
            has_column = result.result_rows[0][0] > 0 if result.result_rows else False

            logger.debug(
                f"Table {table_name} {'has' if has_column else 'does not have'} "
                f"{self.SOURCE_FILE_COLUMN} column"
            )
            return has_column

        except Exception as e:
            logger.warning(f"Could not check for source column: {e}")
            return False

    def _table_exists(self, table_name: str) -> bool:
        """
        Check if a ClickHouse table exists.

        Args:
            table_name: ClickHouse table name

        Returns:
            True if table exists, False otherwise
        """
        try:
            query = f"EXISTS TABLE {self.database}.{table_name}"
            result = self.client.query(query)
            return bool(result.result_rows[0][0]) if result.result_rows else False
        except Exception as e:
            logger.warning(f"Could not check if table exists: {e}")
            return False

    def _get_row_count(self, table_name: str) -> int:
        """
        Get current row count for a ClickHouse table.

        Args:
            table_name: ClickHouse table name

        Returns:
            Row count, or 0 if error
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.database}.{table_name}"
            result = self.client.query(query)
            return result.result_rows[0][0] if result.result_rows else 0
        except Exception as e:
            logger.warning(f"Could not get row count for {table_name}: {e}")
            return 0

    def get_deletion_statistics(self, table_name: str) -> Dict:
        """
        Get statistics about recent deletion operations for a table.

        Args:
            table_name: ClickHouse table name

        Returns:
            Dict with mutation statistics
        """
        try:
            query = f"""
            SELECT
                mutation_id,
                command,
                create_time,
                is_done,
                parts_to_do_names,
                latest_fail_reason
            FROM system.mutations
            WHERE database = '{self.database}'
              AND table = '{table_name}'
              AND command LIKE '%{self.SOURCE_FILE_COLUMN}%'
            ORDER BY create_time DESC
            LIMIT 10
            """

            result = self.client.query(query)

            mutations = []
            for row in result.result_rows:
                mutations.append({
                    'mutation_id': row[0],
                    'command': row[1][:100] + '...' if len(row[1]) > 100 else row[1],
                    'create_time': row[2],
                    'is_done': row[3],
                    'parts_to_do': row[4],
                    'fail_reason': row[5]
                })

            return {
                'table': table_name,
                'recent_mutations': mutations,
                'pending_count': self._get_pending_mutation_count(table_name)
            }

        except Exception as e:
            logger.error(f"Could not get deletion statistics: {e}")
            return {'error': str(e)}

    def check_table_readiness(self, table_name: str) -> Dict:
        """
        Check if a table is ready for deletion operations.

        Args:
            table_name: ClickHouse table name

        Returns:
            Dict with readiness status and details
        """
        result = {
            'table': table_name,
            'exists': False,
            'has_source_column': False,
            'ready_for_deletion': False,
            'row_count': 0,
            'pending_mutations': 0,
            'message': ''
        }

        try:
            result['exists'] = self._table_exists(table_name)
            if not result['exists']:
                result['message'] = f"Table {table_name} does not exist"
                return result

            result['has_source_column'] = self._has_source_file_column(table_name)
            result['row_count'] = self._get_row_count(table_name)
            result['pending_mutations'] = self._get_pending_mutation_count(table_name)

            if not result['has_source_column']:
                result['message'] = (
                    f"Table missing {self.SOURCE_FILE_COLUMN} column. "
                    f"Run: python manage.py add_source_tracking --table={table_name}"
                )
            elif result['pending_mutations'] > 0:
                result['message'] = (
                    f"Table has {result['pending_mutations']} pending mutations. "
                    "Wait for completion before new deletions."
                )
                result['ready_for_deletion'] = True  # Can still submit, will queue
            else:
                result['ready_for_deletion'] = True
                result['message'] = "Table is ready for deletion operations"

        except Exception as e:
            result['message'] = f"Error checking table: {str(e)}"

        return result
