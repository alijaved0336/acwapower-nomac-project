"""
Django management command to migrate ADLS parquet data to ClickHouse.

This command:
1. Scans ADLS for sites and tables (parquet files) from multiple base paths
2. Extracts exact parquet schemas
3. Creates ClickHouse tables with identical schemas
4. Migrates actual parquet data to ClickHouse tables
5. Updates site-table mapping for easy lookup
6. Supports incremental migration for safe, efficient updates

Timezone Handling:
- Azure Data Lake Storage returns timestamps in UTC
- ClickHouse is configured with a session timezone (Asia/Dubai by default)
- When storing timestamps, they are converted from UTC to the ClickHouse session timezone
- When comparing timestamps, both are normalized to UTC for accurate comparison
- This ensures incremental migrations correctly detect unchanged files

Usage:
    python manage.py migrate_adls_to_clickhouse --mode=schema_only
    python manage.py migrate_adls_to_clickhouse --mode=data_only
    python manage.py migrate_adls_to_clickhouse --mode=full --site=Jubail-Jazlah
    python manage.py migrate_adls_to_clickhouse --mode=full --table=Jubail_Chemicals_ppm
    python manage.py migrate_adls_to_clickhouse --mode=full --base-paths=tables,tables/gold
    python manage.py migrate_adls_to_clickhouse --incremental

Environment Variables:
    CLICKHOUSE_TIMEZONE: Timezone for ClickHouse session (default: Asia/Dubai)
"""

import logging
import os
import uuid
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq
import pytz
from django.core.management.base import BaseCommand, CommandError
from azure.storage.filedatalake import DataLakeServiceClient

from config.clickhouse_connector import get_clickhouse_connector
from config.clickhouse_azure_storage import get_azure_storage_config
from infrastructure.services.analysis.azure_operations import AnalysisAzureOperations
from infrastructure.services.clickhouse_deletion_service import ClickHouseDataDeletionService
# from infrastructure.utils.scheduler_cache import SchedulerCache

logger = logging.getLogger(__name__)

# Timezone configuration constants
DEFAULT_CLICKHOUSE_TIMEZONE = 'Asia/Dubai'
TIMESTAMP_TOLERANCE_SECONDS = 1.0  # Tolerance for timestamp comparisons


class Command(BaseCommand):
    """
    Migrate ADLS parquet data to ClickHouse with timezone-aware incremental support.

    Timezone Handling Strategy:
    1. Storage: Timestamps are stored in ClickHouse's session timezone (Asia/Dubai)
       - Azure timestamps (UTC) are converted to session timezone before storage
       - ClickHouse interprets naive DateTime values as being in its session timezone

    2. Retrieval: ClickHouse returns timestamps in its session timezone
       - These are timezone-aware datetime objects with the session timezone

    3. Comparison: All timestamps are normalized to UTC for accurate comparison
       - This ensures incremental migrations correctly detect file changes
       - A small tolerance (1 second) accounts for precision differences
    """
    help = 'Migrate ADLS parquet data to ClickHouse with identical schemas from multiple base paths'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            choices=['schema_only', 'data_only', 'full'],
            default='full',
            help='Migration mode: schema_only, data_only, or full'
        )
        parser.add_argument(
            '--site',
            type=str,
            help='Process only specific site (optional)'
        )
        parser.add_argument(
            '--table',
            type=str,
            help='Process only specific table (optional)'
        )
        parser.add_argument(
            '--base-paths',
            type=str,
            default='tables/gold,tables',
            help='Comma-separated list of base paths to scan (default: tables/gold,tables)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually executing'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing tables'
        )
        parser.add_argument(
            '--cleanup-duplicates',
            action='store_true',
            help='Remove duplicate entries from site_table_mapping'
        )
        # New incremental migration arguments
        parser.add_argument(
            '--incremental',
            action='store_true',
            help='Perform incremental migration (creates tables if needed, then adds only new data)'
        )
        parser.add_argument(
            '--backup-existing',
            action='store_true',
            help='Create backup before dropping existing tables (only with --force)'
        )
        parser.add_argument(
            '--skip-existing-data',
            action='store_true',
            help='Skip data migration for tables that already contain data'
        )
        parser.add_argument(
            '--validate-schema',
            action='store_true',
            help='Validate that existing table schema matches parquet schema'
        )
        parser.add_argument(
            '--skip-schema-check',
            action='store_true',
            help='Skip schema table existence checks (use when tables were created by init_clickhouse_schema)'
        )
        parser.add_argument(
            '--backup-before-migration',
            action='store_true',
            help='Create backup of existing tables before migration (safety measure)'
        )
        # Phase 5: File tracking enhancements
        parser.add_argument(
            '--skip-hash-check',
            action='store_true',
            help='Skip file hash computation, use size+date for change detection (faster but less reliable)'
        )
        parser.add_argument(
            '--force-reimport',
            action='store_true',
            help='Force re-import of all files regardless of tracking status'
        )
        parser.add_argument(
            '--validate-files-only',
            action='store_true',
            help='Only validate and report file changes without importing data'
        )
        parser.add_argument(
            '--report-file-changes',
            action='store_true',
            help='Generate detailed report of file changes (new/updated/deleted)'
        )
        # NEW: Partitioning arguments
        parser.add_argument(
            '--enable-partitioning',
            action='store_true',
            help='Enable time-based partitioning for new tables (recommended for large datasets)'
        )
        parser.add_argument(
            '--partition-column',
            type=str,
            default=None,
            help='Specify timestamp column for partitioning (auto-detected if not provided)'
        )
        # NEW: File validation arguments
        parser.add_argument(
            '--validate-parquet-magic',
            action='store_true',
            help='Validate parquet files by checking magic number (more thorough but slower)'
        )
        # NEW: Retry failed tables priority
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='Priority retry for failed tables only (skip successfully imported tables)'
        )

    def handle(self, *args, **options):
        self.migration_id = str(uuid.uuid4())
        self.dry_run = options['dry_run']
        self.force = options['force']
        self.mode = options['mode']
        self.target_site = options.get('site')
        self.target_table = options.get('table')
        self.cleanup_duplicates = options.get('cleanup_duplicates', False)
        self.verbosity = options.get('verbosity', 1)  # Add verbosity option

        # Incremental options
        self.incremental = options.get('incremental', False)
        self.backup_existing = options.get('backup_existing', False)
        self.skip_existing_data = options.get('skip_existing_data', False)
        self.validate_schema = options.get('validate_schema', False)
        self.skip_schema_check = options.get('skip_schema_check', False)

        # Phase 5: File tracking options
        self.skip_hash = options.get('skip_hash_check', False)
        self.force_reimport = options.get('force_reimport', False)
        self.validate_files_only = options.get('validate_files_only', False)
        self.report_file_changes = options.get('report_file_changes', False)

        # NEW: Partitioning options
        self.enable_partitioning = options.get('enable_partitioning', False)
        self.partition_column = options.get('partition_column', None)

        # NEW: File validation options
        self.validate_parquet_magic = options.get('validate_parquet_magic', False)

        # NEW: Retry failed tables priority
        self.retry_failed = options.get('retry_failed', False)

        # Parse base paths
        base_paths_str = options.get('base_paths', 'tables/gold,tables')
        self.base_paths = [path.strip() for path in base_paths_str.split(',') if path.strip()]

        # Initialize progress tracking cache
        # self.cache = SchedulerCache()

        self.stdout.write(
            self.style.SUCCESS(f'Starting ADLS to ClickHouse migration (ID: {self.migration_id})')
        )
        self.stdout.write(f'Base paths to scan: {", ".join(self.base_paths)}')

        if self.incremental:
            self.stdout.write('Incremental migration mode enabled with file-level tracking')
            if self.skip_hash:
                self.stdout.write('  - Hash checking disabled (using size+date comparison)')
            if self.force_reimport:
                self.stdout.write('  - Force re-import enabled (will re-import all files)')
            if self.validate_files_only:
                self.stdout.write('  - Validation only mode (no data import)')
            if self.report_file_changes:
                self.stdout.write('  - Detailed file change reporting enabled')

        try:
            # Initialize connections with base paths
            self.azure_ops = AnalysisAzureOperations(base_paths=self.base_paths)
            self.clickhouse_client = get_clickhouse_connector(auto_create_database=True)

            # Initialize Azure Storage configuration
            self.azure_storage_config = get_azure_storage_config()
            if self.azure_storage_config.is_configured():
                self.stdout.write('Azure Storage integration enabled')
            else:
                self.stdout.write('Azure Storage not configured - using local storage')

            # Initialize ClickHouse schema
            self._initialize_clickhouse_schema()

            # Clean up duplicates if requested
            if self.cleanup_duplicates:
                self._cleanup_duplicate_mappings()

            # Set current execution in cache
            # command_type = "incremental" if self.incremental else self.mode
            # self.cache.set_current_execution(
            #     migration_id=self.migration_id,
            #     started_at=datetime.now(),
            #     command_type=command_type
            # )

            # Log migration start
            self._log_migration_start()

            # Update progress: Starting discovery
            # self.cache.update_progress("discovering", 5, {})

            # Get sites and tables from ADLS
            sites_data = self._discover_adls_structure()

            # Update progress after discovery
            total_sites = len(sites_data)
            total_tables = sum(len(site['tables']) for site in sites_data.values())
            # self.cache.update_progress("discovering", 20, {
            #     "total_sites_discovered": total_sites,
            #     "total_tables_discovered": total_tables
            # })

            # Handle incremental vs normal migration
            if self.incremental:
                self._handle_incremental_migration(sites_data)
            else:
                # Original logic
                if self.mode in ['schema_only', 'full']:
                    # self.cache.update_progress("schema_creation", 25, {})
                    self._create_clickhouse_schemas(sites_data)
                    # self.cache.update_progress("schema_creation", 40, {})

                if self.mode in ['data_only', 'full']:
                    # self.cache.update_progress("data_migration", 45, {})
                    self._migrate_data(sites_data)
                    # self.cache.update_progress("data_migration", 95, {})

            # Log migration completion
            self._log_migration_completion(sites_data)

            # Update progress to completed
            # self.cache.update_progress("completed", 100, {})

            self.stdout.write(
                self.style.SUCCESS(f'Migration completed successfully!')
            )

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            self._log_migration_failure(str(e))
            raise CommandError(f"Migration failed: {str(e)}")
        finally:
            # Clear current execution from cache
            # if hasattr(self, 'cache'):
            #     self.cache.clear_execution()

            if hasattr(self, 'clickhouse_client') and self.clickhouse_client:
                self.clickhouse_client.close()

    def _handle_incremental_migration(self, sites_data: Dict):
        """Handle incremental migration logic - creates tables if needed, then migrates only new data."""
        # Check if we're only retrying failed tables
        failed_tables = set()
        if self.retry_failed:
            failed_tables = self._get_failed_tables()
            if not failed_tables:
                self.stdout.write(self.style.SUCCESS("No failed tables to retry. All tables are healthy!"))
                return
            self.stdout.write(f"Retry-failed mode: Processing only {len(failed_tables)} failed tables...")
        else:
            self.stdout.write("Processing incremental migration...")

        # Calculate totals for progress tracking
        total_sites = len(sites_data)
        total_tables = sum(len(site_info['tables']) for site_info in sites_data.values())
        processed_sites = 0
        processed_tables = 0
        skipped_tables = 0

        for site_name, site_info in sites_data.items():
            for table_info in site_info['tables']:
                table_name = table_info['name']
                table_path = table_info['path']
                base_path = table_info.get('base_path', '')

                # Skip non-failed tables if in retry-failed mode
                if self.retry_failed:
                    if (site_name, table_name) not in failed_tables:
                        skipped_tables += 1
                        continue

                try:
                    self._process_table_incremental(site_name, table_name, table_path, base_path)
                    processed_tables += 1

                    # Update progress based on tables processed
                    # Range: 40-95% for data migration
                    # progress_pct = 40 + ((processed_tables / total_tables) * 55)
                    # self.cache.update_progress("data_migration", progress_pct, {
                    #     "current_site": site_name,
                    #     "current_table": table_name,
                    #     "sites_processed": processed_sites + 1,
                    #     "tables_processed": processed_tables
                    # })

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed incremental processing for {site_name}.{table_name}: {e}")
                    )

            processed_sites += 1

        if self.retry_failed:
            self.stdout.write(f"Retry-failed mode: Processed {processed_tables} failed tables, skipped {skipped_tables} healthy tables")

    def _process_table_incremental(self, site_name: str, table_name: str, table_path: str, base_path: str = ''):
        """Process a single table for incremental migration."""
        clickhouse_table_name = self._sanitize_table_name(site_name, table_name)

        self.stdout.write(f"Processing {site_name}.{table_name} -> {clickhouse_table_name}")

        # Step 1: Check if table exists
        if not self.dry_run:
            # Get database name from environment
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            exists_query = f"EXISTS TABLE {database}.{clickhouse_table_name}"
            table_exists = self.clickhouse_client.query(exists_query).result_rows[0][0]
        else:
            table_exists = False  # Assume doesn't exist for dry run

        # Get current parquet schema
        schema = self._get_parquet_schema(table_path)

        # Handle case where no parquet files exist
        if not schema:
            if not table_exists:
                # No files and no table - nothing to do
                self.stdout.write(f"  No parquet files found and table doesn't exist, skipping")
                return
            else:
                # Table exists but no parquet files - still process deletions
                self.stdout.write(f"  No parquet files found, checking for file deletions...")
                if not self.dry_run:
                    self._migrate_table_data_incremental(site_name, table_name, table_path, base_path)
                else:
                    self.stdout.write(f"  DRY RUN: Would check for deleted files")
                return

        if not table_exists:
            self.stdout.write(f"  Table doesn't exist, creating schema first...")
            # Create table schema using existing method
            self._create_table_schema_safe(site_name, table_name, table_path, base_path)
        else:
            self.stdout.write(f"  Table exists, checking for schema changes...")

            # NEW: Always validate and evolve schema in incremental mode
            evolution_result = self._handle_schema_evolution(clickhouse_table_name, schema)

            if evolution_result['evolved']:
                if evolution_result['requires_rebuild']:
                    # Type changes or removed columns - rebuild required
                    self.stdout.write(f"  Schema rebuild required, recreating table...")
                    if not self.force and not self.dry_run:
                        self.stdout.write(f"  ERROR: Schema changes require table rebuild. Use --force to proceed.")
                        return
                    # Rebuild table schema
                    self._create_table_schema_safe(site_name, table_name, table_path, base_path)
                    # Reset file tracking so all files get re-imported
                    if not self.dry_run:
                        self._reset_file_tracking_for_table(clickhouse_table_name)
                else:
                    # Only new columns added - continue with migration
                    self.stdout.write(f"  Schema evolved successfully: {len(evolution_result['new_columns'])} column(s) added")
                    # Log schema change for audit
                    self._log_schema_change(site_name, table_name, evolution_result)

        # Step 2: Perform incremental data migration
        if not self.dry_run:
            self._migrate_table_data_incremental(site_name, table_name, table_path, base_path)
        else:
            self.stdout.write(f"  DRY RUN: Would perform incremental data migration")

    def _create_table_schema_safe(self, site_name: str, table_name: str, table_path: str, base_path: str = ''):
        """Create table schema with safe existing table handling."""
        clickhouse_table_name = self._sanitize_table_name(site_name, table_name)

        # Get MERGED parquet schema from ALL files
        # This prevents "Unrecognized column" errors when files have different schemas
        schema = self._get_merged_parquet_schema(table_path)
        if not schema:
            raise Exception(f"Could not extract schema from {table_path}")

        # Convert to ClickHouse DDL
        create_sql = self._generate_clickhouse_ddl(clickhouse_table_name, schema)

        if self.dry_run:
            self.stdout.write(f"  DRY RUN: Would create table {clickhouse_table_name}")
            return

        # Check if table exists
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        exists_query = f"EXISTS TABLE {database}.{clickhouse_table_name}"
        table_exists = self.clickhouse_client.query(exists_query).result_rows[0][0]

        if table_exists:
            if not self.force:
                # Get row count to show table status
                try:
                    count_query = f"SELECT COUNT(*) FROM {database}.{clickhouse_table_name}"
                    result = self.clickhouse_client.query(count_query)
                    row_count = result.result_rows[0][0]
                    self.stdout.write(f"  Table {clickhouse_table_name} already exists with {row_count:,} rows (use --force to recreate)")
                except Exception:
                    self.stdout.write(f"  Table {clickhouse_table_name} already exists (use --force to recreate)")
                return

            # Force recreation - handle backup if requested
            if self.backup_existing:
                self._create_table_backup(clickhouse_table_name)

            # Drop existing table
            drop_sql = f"DROP TABLE IF EXISTS {clickhouse_table_name}"
            self.clickhouse_client.query(drop_sql)
            self.stdout.write(f"  Dropped existing table {clickhouse_table_name}")

        # Create new table
        self.clickhouse_client.query(create_sql)
        self.stdout.write(f"  Created table: {clickhouse_table_name}")

        # Update mapping table
        self._update_site_table_mapping(
            site_name, table_name, clickhouse_table_name,
            table_path, base_path, 'schema_created'
        )

    def _create_table_backup(self, table_name: str) -> str:
        """Create backup of existing table before dropping."""
        timestamp = int(datetime.now().timestamp())
        backup_name = f"{table_name}_backup_{timestamp}"
        
        try:
            # Create backup table
            backup_sql = f"CREATE TABLE {backup_name} AS {table_name}"
            self.clickhouse_client.query(backup_sql)
            
            # Get row count for confirmation
            count_query = f"SELECT COUNT(*) FROM {backup_name}"
            result = self.clickhouse_client.query(count_query)
            row_count = result.result_rows[0][0]
            
            self.stdout.write(f"  Created backup table: {backup_name} ({row_count:,} rows)")
            return backup_name
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to create backup for {table_name}: {e}"))
            raise

    def _validate_existing_schema(self, table_name: str, new_schema: pa.Schema) -> bool:
        """Validate if existing ClickHouse table schema matches new parquet schema."""
        try:
            # Get existing table schema
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            desc_query = f"DESCRIBE TABLE {database}.{table_name}"
            result = self.clickhouse_client.query(desc_query)
            
            existing_columns = {}
            for row in result.result_rows:
                col_name = row[0]
                col_type = row[1]
                existing_columns[col_name] = col_type

            # Convert new schema to expected ClickHouse types
            expected_columns = {}
            for field in new_schema:
                clickhouse_type = self._convert_arrow_to_clickhouse_type(field.type)
                if field.nullable:
                    clickhouse_type = f"Nullable({clickhouse_type})"
                expected_columns[field.name] = clickhouse_type

            # Compare schemas
            schema_matches = True
            for col_name, expected_type in expected_columns.items():
                if col_name not in existing_columns:
                    self.stdout.write(f"    Missing column: {col_name}")
                    schema_matches = False
                elif existing_columns[col_name] != expected_type:
                    self.stdout.write(f"    Type mismatch for {col_name}: existing={existing_columns[col_name]}, expected={expected_type}")
                    schema_matches = False

            return schema_matches

        except Exception as e:
            self.stdout.write(f"    Could not validate schema: {e}")
            return False

    def _get_table_columns_with_types(self, table_name: str) -> dict:
        """Get column names and types from ClickHouse table."""
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            desc_query = f"DESCRIBE TABLE {database}.{table_name}"
            result = self.clickhouse_client.query(desc_query)

            columns = {}
            for row in result.result_rows:
                columns[row[0]] = row[1]  # col_name: col_type
            return columns
        except Exception as e:
            logger.error(f"Error getting table columns with types for {table_name}: {e}")
            return {}

    def _reset_file_tracking_for_table(self, clickhouse_table_name: str) -> int:
        """
        Reset file tracking records for a table when it's force-rebuilt.

        This ensures that after dropping and recreating a table, all files
        will be re-imported during incremental migration.

        Args:
            clickhouse_table_name: The ClickHouse table name

        Returns:
            Number of tracking records deleted
        """
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # First count how many records will be affected
            count_query = f"""
            SELECT COUNT(*)
            FROM {database}.parquet_file_tracking
            WHERE clickhouse_table_name = '{clickhouse_table_name}'
            """
            result = self.clickhouse_client.query(count_query)
            count = result.result_rows[0][0] if result.result_rows else 0

            if count > 0:
                # Delete tracking records for this table
                delete_query = f"""
                ALTER TABLE {database}.parquet_file_tracking
                DELETE WHERE clickhouse_table_name = '{clickhouse_table_name}'
                """
                self.clickhouse_client.query(delete_query)
                self.stdout.write(f"  Reset {count} file tracking records for table rebuild")

            return count

        except Exception as e:
            logger.warning(f"Could not reset file tracking for {clickhouse_table_name}: {e}")
            self.stdout.write(f"  WARNING: Could not reset file tracking: {e}")
            return 0

    def _handle_schema_evolution(self, clickhouse_table_name: str, new_schema: pa.Schema) -> dict:
        """
        Detect and handle schema changes between parquet and ClickHouse table.
        Automatically adds new columns to existing tables.

        Returns:
            dict with keys:
            - evolved (bool): Whether schema was changed
            - requires_rebuild (bool): Whether table needs to be dropped and recreated
            - new_columns (list): List of new column names added
            - removed_columns (list): List of removed column names
            - type_changes (list): List of columns with type changes
        """
        try:
            # Get current ClickHouse table schema
            existing_columns = self._get_table_columns_with_types(clickhouse_table_name)

            if not existing_columns:
                return {'evolved': False, 'requires_rebuild': True, 'new_columns': [],
                        'removed_columns': [], 'type_changes': []}

            # Convert parquet schema to ClickHouse types
            expected_columns = {}
            for field in new_schema:
                clickhouse_type = self._convert_arrow_to_clickhouse_type(field.type)
                if field.nullable:
                    clickhouse_type = f"Nullable({clickhouse_type})"
                expected_columns[field.name] = clickhouse_type

            # Identify differences
            # Note: _source_file_path is added during import, not in parquet files, so exclude from comparison
            new_columns = [col for col in expected_columns if col not in existing_columns]
            removed_columns = [col for col in existing_columns if col not in expected_columns and col != '_source_file_path']
            type_changes = [
                col for col in expected_columns
                if col in existing_columns and expected_columns[col] != existing_columns[col]
            ]

            # Apply schema changes
            changes_made = False

            # Add new columns
            if new_columns and not self.dry_run:
                import os
                database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

                for col_name in new_columns:
                    col_type = expected_columns[col_name]
                    try:
                        alter_sql = f"ALTER TABLE {database}.{clickhouse_table_name} ADD COLUMN `{col_name}` {col_type}"
                        self.clickhouse_client.query(alter_sql)
                        self.stdout.write(f"    Added column: {col_name} ({col_type})")
                        changes_made = True
                    except Exception as e:
                        self.stdout.write(f"    ERROR: Failed to add column {col_name}: {e}")
                        # If we can't add columns, require full rebuild
                        return {'evolved': True, 'requires_rebuild': True, 'new_columns': new_columns,
                                'removed_columns': removed_columns, 'type_changes': type_changes}
            elif new_columns and self.dry_run:
                self.stdout.write(f"    DRY RUN: Would add {len(new_columns)} new columns: {new_columns}")
                changes_made = True

            # Handle type changes and removed columns - require table rebuild
            if type_changes or removed_columns:
                self.stdout.write(f"    WARNING: Schema changes require table rebuild!")
                if type_changes:
                    self.stdout.write(f"      Type changes: {type_changes}")
                if removed_columns:
                    self.stdout.write(f"      Removed columns: {removed_columns}")
                return {'evolved': True, 'requires_rebuild': True, 'new_columns': new_columns,
                        'removed_columns': removed_columns, 'type_changes': type_changes}

            return {'evolved': changes_made, 'requires_rebuild': False, 'new_columns': new_columns,
                    'removed_columns': [], 'type_changes': []}

        except Exception as e:
            logger.error(f"Error handling schema evolution for {clickhouse_table_name}: {e}")
            self.stdout.write(f"    ERROR: Schema evolution failed: {e}")
            return {'evolved': False, 'requires_rebuild': True, 'new_columns': [],
                    'removed_columns': [], 'type_changes': []}

    def _log_schema_change(self, site_name: str, table_name: str, evolution_result: dict):
        """Log schema changes to schema_evolution_log table for audit trail."""
        if self.dry_run:
            return

        try:
            import os
            import json
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Escape single quotes for SQL safety
            site_name_escaped = site_name.replace("'", "''")
            table_name_escaped = table_name.replace("'", "''")
            changes_json = json.dumps(evolution_result).replace("'", "''")
            migration_id_escaped = self.migration_id.replace("'", "''")

            insert_sql = f"""
            INSERT INTO {database}.schema_evolution_log
            (site_name, table_name, change_date, change_type, changes_detail, migration_id)
            VALUES ('{site_name_escaped}', '{table_name_escaped}', now(),
                    'column_addition', '{changes_json}', '{migration_id_escaped}')
            """

            self.clickhouse_client.query(insert_sql)
            self.stdout.write(f"    Schema change logged for audit")

        except Exception as e:
            # Don't fail migration if logging fails
            logger.warning(f"Could not log schema change for {site_name}.{table_name}: {e}")
            self.stdout.write(f"    Warning: Could not log schema change: {e}")

    def _get_partition_from_file(self, file_path: str, timestamp_column: str = None) -> str:
        """
        Extract partition identifier from parquet file based on data timestamps.
        Returns partition in format 'YYYYMM' for monthly partitioning.

        Args:
            file_path: Full ADLS path to parquet file
            timestamp_column: Name of timestamp column (optional, will try to detect)

        Returns:
            Partition ID string in 'YYYYMM' format, or 'unknown' if detection fails
        """
        try:
            service_client = self.azure_ops.service_client
            filesystem_client = service_client.get_file_system_client(self.azure_ops.filesystem_name)
            file_client = filesystem_client.get_file_client(file_path)

            # Read parquet file metadata
            download_data = file_client.download_file()
            content = download_data.readall()

            parquet_file = pq.ParquetFile(pa.BufferReader(content))

            # Try to read only first row group for efficiency
            try:
                table = parquet_file.read_row_group(0)
            except Exception:
                # Fallback: read entire file (slower but more reliable)
                table = parquet_file.read()

            # Find timestamp column if not specified
            if not timestamp_column:
                for field in table.schema:
                    if pa.types.is_timestamp(field.type):
                        timestamp_column = field.name
                        break

            if timestamp_column and timestamp_column in table.column_names:
                # Get minimum timestamp from data
                # Use PyArrow compute function for ChunkedArray compatibility
                import pyarrow.compute as pc

                try:
                    min_date_scalar = pc.min(table[timestamp_column])
                    min_date = min_date_scalar.as_py()

                    if min_date:
                        partition_id = min_date.strftime('%Y%m')
                        return partition_id
                except Exception as compute_error:
                    logger.warning(f"Could not compute min for {file_path}: {compute_error}")
                    # Fall through to file modification date fallback

            # Fallback: use file modification date
            try:
                properties = file_client.get_file_properties()
                partition_id = properties.last_modified.strftime('%Y%m')
                return partition_id
            except Exception as fallback_error:
                logger.warning(f"Could not get file properties for {file_path}: {fallback_error}")
                # Last resort: return None instead of 'unknown'
                return None

        except Exception as e:
            logger.warning(f"Could not extract partition from {file_path}: {e}")
            # Return None instead of 'unknown' to signal extraction failure
            return None

    def _is_table_partitioned(self, table_name: str) -> bool:
        """Check if ClickHouse table uses partitioning."""
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            query = f"SELECT partition_key FROM system.tables WHERE database = '{database}' AND name = '{table_name}'"
            result = self.clickhouse_client.query(query)

            if result.result_rows and result.result_rows[0][0]:
                return True
            return False
        except Exception as e:
            logger.warning(f"Could not check if table {table_name} is partitioned: {e}")
            return False

    def _drop_partition(self, table_name: str, partition_id: str) -> bool:
        """Drop a specific partition from ClickHouse table."""
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            drop_sql = f"ALTER TABLE {database}.{table_name} DROP PARTITION '{partition_id}'"
            self.clickhouse_client.query(drop_sql)
            self.stdout.write(f"    Dropped partition: {partition_id}")
            return True
        except Exception as e:
            logger.error(f"Error dropping partition {partition_id} from {table_name}: {e}")
            self.stdout.write(f"    ERROR: Failed to drop partition {partition_id}: {e}")
            return False

    def _drop_table(self, table_name: str) -> bool:
        """Drop entire ClickHouse table."""
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            drop_sql = f"DROP TABLE IF EXISTS {database}.{table_name}"
            self.clickhouse_client.query(drop_sql)
            self.stdout.write(f"    Dropped table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error dropping table {table_name}: {e}")
            self.stdout.write(f"    ERROR: Failed to drop table: {e}")
            return False

    def _is_valid_parquet_file(self, file_path: str) -> bool:
        """
        Validate that file is actually a parquet file by checking magic number.
        Parquet files start with the magic bytes 'PAR1'.

        Args:
            file_path: Full ADLS path to file

        Returns:
            True if file is valid parquet, False otherwise
        """
        try:
            service_client = self.azure_ops.service_client
            filesystem_client = service_client.get_file_system_client(self.azure_ops.filesystem_name)
            file_client = filesystem_client.get_file_client(file_path)

            # Read only first 4 bytes to check magic number (very fast)
            download_data = file_client.download_file()
            first_bytes = download_data.readall()[:4]

            # Parquet magic number: 'PAR1' (in ASCII bytes)
            return first_bytes == b'PAR1'

        except Exception as e:
            logger.warning(f"Could not validate parquet file {file_path}: {e}")
            return False

    def _get_parquet_row_count(self, file_path: str) -> Optional[int]:
        """
        Get row count from parquet file metadata without loading data.
        This is very fast as it only reads metadata.

        Args:
            file_path: Full ADLS path to parquet file

        Returns:
            Number of rows in the parquet file, or None if error
        """
        try:
            service_client = self.azure_ops.service_client
            filesystem_client = service_client.get_file_system_client(self.azure_ops.filesystem_name)
            file_client = filesystem_client.get_file_client(file_path)

            # Download file to read metadata
            download_data = file_client.download_file()
            content = download_data.readall()

            # Read only metadata (fast)
            parquet_file = pq.ParquetFile(pa.BufferReader(content))
            return parquet_file.metadata.num_rows

        except Exception as e:
            logger.warning(f"Could not get row count for {file_path}: {e}")
            return None

    def _migrate_table_data_incremental(self, site_name: str, table_name: str, table_path: str, base_path: str = ''):
        """
        Perform incremental data migration with file-level tracking.
        Uses the new file tracking system to detect and handle file changes.
        """
        clickhouse_table_name = self._sanitize_table_name(site_name, table_name)

        # Check existing data
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        count_query = f"SELECT COUNT(*) FROM {database}.{clickhouse_table_name}"
        existing_count = self.clickhouse_client.query(count_query).result_rows[0][0]

        self.stdout.write(f"  Current row count: {existing_count:,}")

        try:
            self.stdout.write(f"  Starting intelligent incremental migration with file tracking...")

            # Get skip_hash setting from command options
            skip_hash = getattr(self, 'skip_hash', False)

            # Step 1: Get all current files with metadata
            self.stdout.write(f"  Scanning ADLS files (quick scan without hashes)...")
            current_files = self._get_all_parquet_files_with_metadata(table_path, skip_hash=skip_hash)

            # Note: Don't return early even if no files found - we need to check for deletions
            if not current_files:
                self.stdout.write(f"  No parquet files found in ADLS - checking for deleted files...")
                current_files = []  # Empty list for comparison
            else:
                self.stdout.write(f"  Found {len(current_files)} total files in ADLS")

            # Report hash mode
            if self.skip_hash:
                self.stdout.write(f"  Using size+date comparison (--skip-hash-check enabled)")
            else:
                self.stdout.write(f"  Using intelligent hash comparison (computing only when needed)")

            # Step 2: Get tracked files from ClickHouse
            self.stdout.write(f"  Retrieving file tracking information...")
            tracked_files = self._get_tracked_files(site_name, table_name)
            self.stdout.write(f"  Found {len(tracked_files)} previously tracked files")

            # Step 3: Compare files to detect changes
            file_comparison = self._compare_files(current_files, tracked_files)

            # Step 4: Process file changes
            stats = self._process_file_changes(
                site_name, table_name, clickhouse_table_name,
                table_path, file_comparison, skip_hash
            )

            # Step 5: Update final statistics
            if stats['total_rows_imported'] > 0 or stats['files_processed'] > 0:
                # Get final row count
                final_count_result = self.clickhouse_client.query(count_query)
                final_count = final_count_result.result_rows[0][0]

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Migration complete: {final_count:,} total rows (added {stats['total_rows_imported']:,})"
                    )
                )

                # Update mapping status
                self._update_site_table_mapping(
                    site_name, table_name, clickhouse_table_name,
                    table_path, base_path, 'migrated', row_count=final_count
                )
            elif stats['new_files_count'] == 0 and stats['updated_files_count'] == 0:
                self.stdout.write(f"  No changes detected - all files are up to date")
            else:
                self.stdout.write(f"  Migration completed with {len(stats['errors'])} errors")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  Incremental migration failed for {clickhouse_table_name}: {e}")
            )
            # Update status as failed
            self._update_site_table_mapping(
                site_name, table_name, clickhouse_table_name,
                table_path, base_path, 'incremental_failed', row_count=existing_count
            )
            raise

    def _get_last_migration_info(self, site_name: str, table_name: str) -> Optional[Dict]:
        """Get information about the last successful migration."""
        # Escape single quotes for SQL safety
        site_name_escaped = site_name.replace("'", "''")
        table_name_escaped = table_name.replace("'", "''")
        
        # Get database name from environment
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
        query = f"""
        SELECT migration_date, row_count, migration_status
        FROM {database}.site_table_mapping
        WHERE site_name = '{site_name_escaped}' 
        AND table_name = '{table_name_escaped}'
        AND migration_status IN ('migrated', 'incremental_migrated')
        ORDER BY migration_date DESC
        LIMIT 1
        """
        
        try:
            result = self.clickhouse_client.query(query)
            if result.result_rows:
                row = result.result_rows[0]
                return {
                    'migration_date': row[0],
                    'row_count': row[1],
                    'migration_status': row[2]
                }
        except Exception as e:
            logger.warning(f"Could not get last migration info: {e}")
        
        return None

    def _get_parquet_files_for_incremental(self, table_path: str, last_migration_date: Optional[datetime]) -> List[Dict]:
        """Get parquet files that are newer than the last migration date."""
        try:
            service_client = self.azure_ops.service_client
            filesystem_client = service_client.get_file_system_client(self.azure_ops.filesystem_name)

            # List all parquet files in the directory
            paths = filesystem_client.get_paths(path=table_path, recursive=True)

            files_to_process = []

            for path in paths:
                if not path.is_directory and path.name.endswith('.parquet'):
                    file_info = {
                        'name': path.name,
                        'path': path.name,
                        'last_modified': path.last_modified,
                        'size': getattr(path, 'content_length', 0)
                    }

                    # If no last migration date, include all files
                    if last_migration_date is None:
                        files_to_process.append(file_info)
                    # If file is newer than last migration, include it
                    elif path.last_modified and path.last_modified > last_migration_date:
                        files_to_process.append(file_info)

            # Sort by last modified date
            files_to_process.sort(key=lambda x: x['last_modified'] or datetime.min)

            return files_to_process

        except Exception as e:
            logger.error(f"Error getting parquet files for incremental migration: {e}")
            return []

    def _get_all_parquet_files_with_metadata(self, table_path: str, skip_hash: bool = False) -> List[Dict]:
        """
        Get all parquet files in a table directory with metadata.

        OPTIMIZATION: Don't compute hash for all files upfront - only get basic metadata.
        Hash will be computed later only for new or potentially changed files.

        Enhanced with validation to ensure only valid parquet files are processed.

        Args:
            table_path: ADLS path to the table directory
            skip_hash: If True, skip hash computation

        Returns:
            List of dictionaries with file metadata (only valid parquet files)
        """
        try:
            service_client = self.azure_ops.service_client
            filesystem_client = service_client.get_file_system_client(self.azure_ops.filesystem_name)

            # List all parquet files in the directory
            paths = filesystem_client.get_paths(path=table_path, recursive=True)

            files_with_metadata = []
            non_parquet_files = []  # Track non-parquet files for logging
            invalid_parquet_files = []  # Track files with .parquet extension but invalid format

            for path in paths:
                if path.is_directory:
                    continue

                # VALIDATION: Only process .parquet files
                if not path.name.endswith('.parquet'):
                    non_parquet_files.append(path.name)
                    continue

                # Additional validation: Check if file is actually a valid parquet file
                validate_parquet_magic = getattr(self, 'validate_parquet_magic', False)
                if validate_parquet_magic:
                    if not self._is_valid_parquet_file(path.name):
                        invalid_parquet_files.append(path.name)
                        self.stdout.write(f"    WARNING: File {path.name} has .parquet extension but is not valid parquet format")
                        continue

                # OPTIMIZATION: Always skip hash in initial scan
                # We'll compute hash later ONLY for new/changed files
                metadata = self._get_file_metadata(path.name, skip_hash=True)

                if metadata:
                    files_with_metadata.append(metadata)

            # Log non-parquet files found
            if non_parquet_files:
                self.stdout.write(f"  INFO: Skipped {len(non_parquet_files)} non-parquet files in {table_path}")
                if len(non_parquet_files) <= 5:
                    for file in non_parquet_files:
                        self.stdout.write(f"    - {file}")
                else:
                    self.stdout.write(f"    (showing first 5 of {len(non_parquet_files)})")
                    for file in non_parquet_files[:5]:
                        self.stdout.write(f"    - {file}")

            # Log invalid parquet files
            if invalid_parquet_files:
                self.stdout.write(f"  WARNING: Found {len(invalid_parquet_files)} files with .parquet extension that are not valid parquet format")

            return files_with_metadata

        except Exception as e:
            logger.error(f"Error getting parquet files with metadata: {e}")
            return []

    def _get_failed_tables(self) -> set:
        """
        Get tables that have failed imports from parquet_file_tracking.

        Returns:
            Set of tuples (site_name, table_name) that have failed imports
        """
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Find tables with failed imports
            query = f"""
            SELECT DISTINCT site_name, table_name
            FROM {database}.parquet_file_tracking
            WHERE import_status = 'failed'
            """

            result = self.clickhouse_client.query(query)

            failed_tables = set()
            for row in result.result_rows:
                failed_tables.add((row[0], row[1]))

            if failed_tables:
                logger.info(f"Found {len(failed_tables)} tables with failed imports")

            return failed_tables

        except Exception as e:
            logger.warning(f"Could not get failed tables (table may not exist yet): {e}")
            return set()

    def _get_tracked_files(self, site_name: str, table_name: str) -> Dict[str, Dict]:
        """
        Get all tracked files for a specific site and table from ClickHouse.

        Args:
            site_name: Site identifier
            table_name: Table identifier

        Returns:
            Dictionary mapping file_path to file metadata
        """
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Escape single quotes
            site_name_escaped = site_name.replace("'", "''")
            table_name_escaped = table_name.replace("'", "''")

            query = f"""
            SELECT file_path, file_size, file_hash, last_modified, rows_imported, import_status
            FROM {database}.parquet_file_tracking
            WHERE site_name = '{site_name_escaped}'
            AND table_name = '{table_name_escaped}'
            AND import_status != 'deleted'
            """

            result = self.clickhouse_client.query(query)

            tracked_files = {}
            for row in result.result_rows:
                file_path = row[0]
                tracked_files[file_path] = {
                    'file_path': file_path,
                    'file_size': row[1],
                    'file_hash': row[2],
                    'last_modified': row[3],  # Timestamp in ClickHouse session timezone
                    'rows_imported': row[4],
                    'import_status': row[5]
                }

            return tracked_files

        except Exception as e:
            logger.error(f"Error getting tracked files: {e}")
            return {}

    def _normalize_timestamp_to_utc(self, timestamp, source='azure'):
        """
        Normalize a timestamp to UTC timezone for comparison.

        Handles the timezone difference between Azure ADLS (UTC) and ClickHouse (session timezone).
        - Azure ADLS returns timestamps in UTC
        - ClickHouse returns timestamps in its session timezone (Asia/Dubai by default)

        Args:
            timestamp: datetime object (timezone-aware or naive)
            source: 'azure' for timestamps from Azure ADLS, 'clickhouse' for timestamps from ClickHouse

        Returns:
            datetime object in UTC timezone, or None if input is None
        """
        if timestamp is None:
            return None

        # Handle timezone-aware timestamps
        if timestamp.tzinfo is not None:
            # Simply convert to UTC regardless of source
            return timestamp.astimezone(timezone.utc)

        # Handle naive timestamps based on source
        if source == 'clickhouse':
            # ClickHouse naive timestamps are in session timezone
            clickhouse_tz = self._get_clickhouse_timezone()
            localized = clickhouse_tz.localize(timestamp)
            return localized.astimezone(timezone.utc)
        else:
            # Azure naive timestamps are already in UTC
            return timestamp.replace(tzinfo=timezone.utc)

    def _get_clickhouse_timezone(self):
        """Get the configured ClickHouse timezone as a pytz timezone object."""
        timezone_str = os.getenv('CLICKHOUSE_TIMEZONE', DEFAULT_CLICKHOUSE_TIMEZONE)
        return pytz.timezone(timezone_str)

    def _timestamps_differ(self, timestamp1, timestamp2):
        """
        Check if two timestamps differ by more than the configured tolerance.

        Args:
            timestamp1: First datetime object (in UTC)
            timestamp2: Second datetime object (in UTC)

        Returns:
            bool: True if timestamps differ by more than tolerance, False otherwise
        """
        if not timestamp1 or not timestamp2:
            return False

        time_diff = abs((timestamp1 - timestamp2).total_seconds())
        differs = time_diff > TIMESTAMP_TOLERANCE_SECONDS

        if differs and self.verbosity >= 2:
            logger.debug(f"Timestamp difference detected: {time_diff:.2f} seconds")

        return differs

    def _format_timestamp_for_clickhouse(self, timestamp):
        """
        Format a timestamp for storage in ClickHouse.

        ClickHouse stores naive DateTime values and interprets them as being in the
        session timezone. This method converts UTC timestamps to the ClickHouse
        session timezone before formatting.

        Args:
            timestamp: datetime object (timezone-aware or naive in UTC)

        Returns:
            str: Formatted timestamp string for ClickHouse insertion
        """
        if not timestamp:
            return '1970-01-01 00:00:00.000'

        # Normalize to UTC first
        if timestamp.tzinfo is not None:
            timestamp_utc = timestamp.astimezone(timezone.utc)
        else:
            # Assume naive timestamps are in UTC
            timestamp_utc = timestamp.replace(tzinfo=timezone.utc)

        # Convert to ClickHouse session timezone
        clickhouse_tz = self._get_clickhouse_timezone()
        timestamp_in_ch_tz = timestamp_utc.astimezone(clickhouse_tz)

        # Format as string without timezone info (ClickHouse will interpret as session timezone)
        return timestamp_in_ch_tz.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Millisecond precision

    def _compare_files(self, current_files: List[Dict], tracked_files: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """
        Compare current ADLS files with tracked files to identify changes.

        OPTIMIZED: Only compute hash when necessary for potentially changed files.

        Args:
            current_files: List of current file metadata from ADLS
            tracked_files: Dictionary of tracked files from ClickHouse

        Returns:
            Dictionary with keys: 'new', 'updated', 'unchanged', 'deleted'
        """
        new_files = []
        updated_files = []
        unchanged_files = []

        for current_file in current_files:
            file_path = current_file['file_path']

            if file_path not in tracked_files:
                # File exists in ADLS but not tracked - it's new
                new_files.append(current_file)
            else:
                tracked_file = tracked_files[file_path]

                # First check size and modified date (cheap operations)
                size_changed = current_file['file_size'] != tracked_file['file_size']

                # Normalize timestamps to UTC for accurate comparison
                current_time = self._normalize_timestamp_to_utc(current_file['last_modified'], source='azure')
                tracked_time = self._normalize_timestamp_to_utc(tracked_file['last_modified'], source='clickhouse')

                # Check if timestamps have changed (with tolerance for precision differences)
                time_changed = self._timestamps_differ(current_time, tracked_time)

                if size_changed or time_changed:
                    # File might be updated - now compute hash if not skipping
                    if not self.skip_hash and tracked_file.get('file_hash'):
                        # Compute hash only for potentially changed files
                        self.stdout.write(f"    Computing hash for potentially changed file: {file_path}")
                        file_with_hash = self._get_file_metadata(file_path, skip_hash=False)

                        if file_with_hash and file_with_hash.get('file_hash'):
                            if file_with_hash['file_hash'] != tracked_file['file_hash']:
                                # Hash confirmed the file changed
                                updated_files.append({
                                    **file_with_hash,
                                    'previous_hash': tracked_file['file_hash'],
                                    'previous_rows': tracked_file['rows_imported']
                                })
                            else:
                                # Hash shows file unchanged (false positive from timestamp)
                                unchanged_files.append(current_file)
                        else:
                            # Hash computation failed, fall back to size/time
                            updated_files.append({
                                **current_file,
                                'previous_size': tracked_file['file_size'],
                                'previous_rows': tracked_file['rows_imported']
                            })
                    else:
                        # Skip hash mode or no previous hash - use size/time
                        updated_files.append({
                            **current_file,
                            'previous_size': tracked_file['file_size'],
                            'previous_rows': tracked_file['rows_imported']
                        })
                else:
                    # Size and time unchanged - file is definitely unchanged
                    unchanged_files.append(current_file)

        # Find deleted files (tracked but not in current ADLS)
        current_file_paths = {f['file_path'] for f in current_files}
        deleted_files = [
            tracked_file
            for file_path, tracked_file in tracked_files.items()
            if file_path not in current_file_paths
        ]

        return {
            'new': new_files,
            'updated': updated_files,
            'unchanged': unchanged_files,
            'deleted': deleted_files
        }

    def _process_file_changes(self, site_name: str, table_name: str,
                              clickhouse_table_name: str, table_path: str,
                              file_comparison: Dict[str, List[Dict]], skip_hash: bool = False) -> Dict[str, Any]:
        """
        Process file changes: import new files, re-import updated files, skip unchanged.

        Args:
            site_name: Site identifier
            table_name: Table identifier
            clickhouse_table_name: ClickHouse table name
            table_path: ADLS table path
            file_comparison: Result from _compare_files()
            skip_hash: Whether hash computation was skipped

        Returns:
            Dictionary with processing statistics
        """
        new_files = file_comparison['new']
        updated_files = file_comparison['updated']
        unchanged_files = file_comparison['unchanged']
        deleted_files = file_comparison['deleted']

        stats = {
            'new_files_count': len(new_files),
            'updated_files_count': len(updated_files),
            'unchanged_files_count': len(unchanged_files),
            'deleted_files_count': len(deleted_files),
            'total_rows_imported': 0,
            'files_processed': 0,
            'errors': []
        }

        # Log summary
        self.stdout.write(f"  File Analysis:")
        self.stdout.write(f"    New files: {len(new_files)}")
        self.stdout.write(f"    Updated files: {len(updated_files)}")
        self.stdout.write(f"    Unchanged files: {len(unchanged_files)}")
        self.stdout.write(f"    Deleted files: {len(deleted_files)}")

        # Detailed reporting if requested
        if self.report_file_changes:
            self._print_detailed_file_report(new_files, updated_files, unchanged_files, deleted_files)

        # Validation-only mode - just report and exit
        if self.validate_files_only:
            self.stdout.write(self.style.WARNING("  Validation-only mode: No data will be imported"))
            return stats

        # Force re-import mode - treat all files as new
        if self.force_reimport:
            self.stdout.write(f"  Force re-import enabled: Re-importing all {len(new_files) + len(updated_files) + len(unchanged_files)} files")
            new_files = new_files + updated_files + unchanged_files
            updated_files = []
            unchanged_files = []

        # Handle unchanged files - just skip
        if unchanged_files:
            self.stdout.write(f"  Skipping {len(unchanged_files)} unchanged files")

        # Handle deleted files - DELETE DATA from ClickHouse and update tracking
        if deleted_files:
            self.stdout.write(f"  Processing {len(deleted_files)} deleted files")

            if self.dry_run:
                # In dry-run mode, just report what would be deleted
                total_rows = sum(f.get('rows_imported', 0) for f in deleted_files)
                self.stdout.write(f"    DRY RUN: Would delete data for {len(deleted_files)} files (~{total_rows} rows)")
                for f in deleted_files[:5]:  # Show first 5
                    self.stdout.write(f"      - {f['file_path']} ({f.get('rows_imported', 0)} rows)")
                if len(deleted_files) > 5:
                    self.stdout.write(f"      ... and {len(deleted_files) - 5} more files")
            else:
                # Actually delete data from ClickHouse
                deletion_service = ClickHouseDataDeletionService(self.clickhouse_client)
                deleted_file_paths = [f['file_path'] for f in deleted_files]

                # Check if table has source file tracking column
                readiness = deletion_service.check_table_readiness(clickhouse_table_name)

                if readiness['ready_for_deletion']:
                    self.stdout.write(f"    Deleting data for {len(deleted_files)} files from {clickhouse_table_name}...")

                    deletion_result = deletion_service.delete_data_for_files(
                        clickhouse_table_name=clickhouse_table_name,
                        file_paths=deleted_file_paths,
                        wait_for_completion=True
                    )

                    if deletion_result['success']:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"    Deleted {deletion_result['rows_deleted']} rows "
                                f"in {deletion_result['duration_seconds']:.1f}s"
                            )
                        )
                        # Update tracking records
                        for deleted_file in deleted_files:
                            self._update_file_tracking(
                                deleted_file['file_path'],
                                rows_imported=0,
                                status='deleted',
                                error_message='Data deleted from ClickHouse'
                            )
                    else:
                        # Deletion failed - mark for retry
                        error_msg = '; '.join(deletion_result['errors'])
                        self.stdout.write(
                            self.style.WARNING(
                                f"    Deletion failed: {error_msg}"
                            )
                        )
                        for deleted_file in deleted_files:
                            self._update_file_tracking(
                                deleted_file['file_path'],
                                rows_imported=deleted_file.get('rows_imported', 0),
                                status='deletion_failed',
                                error_message=error_msg[:500]  # Truncate long errors
                            )
                else:
                    # Table not ready for deletion (missing column)
                    self.stdout.write(
                        self.style.WARNING(
                            f"    Skipping deletion: {readiness['message']}"
                        )
                    )
                    # Mark files as deleted in tracking without data deletion
                    for deleted_file in deleted_files:
                        self._update_file_tracking(
                            deleted_file['file_path'],
                            rows_imported=0,
                            status='deleted',
                            error_message='File deleted from ADLS (data not deleted - missing source tracking)'
                        )

        # Handle updated files - Partition-aware or full table drop strategy
        if updated_files:
            self.stdout.write(f"  Detected {len(updated_files)} updated files")

            if self.dry_run:
                self.stdout.write(f"    DRY RUN: Would handle table updates")
            else:
                # Check if table is partitioned
                is_partitioned = self._is_table_partitioned(clickhouse_table_name)

                if is_partitioned:
                    # OPTIMIZATION: Drop only affected partitions
                    self.stdout.write(f"  Table is partitioned - identifying affected partitions...")

                    affected_partitions = set()
                    partition_column = getattr(self, 'partition_column', None)
                    has_unknown_partitions = False

                    # Get affected partitions from all files
                    for file_metadata in new_files + updated_files + unchanged_files:
                        partition_id = self._get_partition_from_file(file_metadata['file_path'], partition_column)
                        if partition_id is None:
                            has_unknown_partitions = True
                        else:
                            affected_partitions.add(partition_id)

                    # If we couldn't determine some partitions, do full rebuild instead
                    if has_unknown_partitions or not affected_partitions:
                        self.stdout.write(f"  WARNING: Could not determine partitions for some files")
                        self.stdout.write(f"  Falling back to full table rebuild")

                        # Drop entire table and recreate
                        self._drop_table(clickhouse_table_name)
                        self._clear_table_file_mappings(clickhouse_table_name)

                        # Recreate table with MERGED schema from ALL files
                        schema = self._get_merged_parquet_schema(table_path)
                        if schema:
                            create_sql = self._generate_clickhouse_ddl(clickhouse_table_name, schema)
                            self.clickhouse_client.query(create_sql)
                            self.stdout.write(f"  Recreated table: {clickhouse_table_name}")
                        else:
                            self.stdout.write(f"  ERROR: Could not get schema to recreate table")
                            return stats

                        # Re-import ALL files
                        files_to_reimport = new_files + updated_files + unchanged_files
                        self.stdout.write(f"  Re-importing {len(files_to_reimport)} files to new table")

                    else:
                        # We have valid partitions - drop only affected ones
                        self.stdout.write(f"  Affected partitions: {affected_partitions}")

                        # Drop affected partitions
                        for partition_id in affected_partitions:
                            self._drop_partition(clickhouse_table_name, partition_id)

                        # Re-import only files in affected partitions
                        files_to_reimport = [
                            f for f in new_files + updated_files + unchanged_files
                            if self._get_partition_from_file(f['file_path'], partition_column) in affected_partitions
                        ]

                        self.stdout.write(f"  Re-importing {len(files_to_reimport)} files in affected partitions")

                else:
                    # STRATEGY: Drop entire table and recreate (as requested)
                    self.stdout.write(f"  Table not partitioned - dropping and recreating entire table")

                    # Drop entire table
                    self._drop_table(clickhouse_table_name)

                    # Clear file mappings
                    self._clear_table_file_mappings(clickhouse_table_name)

                    # Clear file tracking records to ensure fresh timestamps
                    self._clear_file_tracking_for_table(site_name, table_name)

                    # Recreate table with MERGED schema from ALL files
                    # This prevents "Unrecognized column" errors when files have different schemas
                    schema = self._get_merged_parquet_schema(table_path)
                    if schema:
                        create_sql = self._generate_clickhouse_ddl(clickhouse_table_name, schema)
                        self.clickhouse_client.query(create_sql)
                        self.stdout.write(f"  Recreated table: {clickhouse_table_name}")
                    else:
                        self.stdout.write(f"  ERROR: Could not get schema to recreate table")
                        return stats

                    # Re-import ALL files
                    files_to_reimport = new_files + updated_files + unchanged_files
                    self.stdout.write(f"  Re-importing {len(files_to_reimport)} files to new table")

                # Import files
                file_paths = [f['file_path'] for f in files_to_reimport]

                import_result = self._import_files(
                    site_name, table_name, clickhouse_table_name,
                    file_paths, files_to_reimport
                )

                stats['total_rows_imported'] = import_result['total_rows']
                stats['files_processed'] = import_result['files_processed']
                stats['errors'] = import_result['errors']

                self.stdout.write(f"  Re-imported {import_result['total_rows']} rows from {import_result['files_processed']} files")

        # Handle only new files if no updates
        elif new_files:
            self.stdout.write(f"  Importing {len(new_files)} new files")

            if self.dry_run:
                self.stdout.write(f"    DRY RUN: Would import {len(new_files)} new files")
            else:
                file_paths = [f['file_path'] for f in new_files]

                import_result = self._import_files(
                    site_name, table_name, clickhouse_table_name,
                    file_paths, new_files
                )

                stats['total_rows_imported'] = import_result['total_rows']
                stats['files_processed'] = import_result['files_processed']
                stats['errors'] = import_result['errors']

                self.stdout.write(f"  Imported {import_result['total_rows']} rows from {import_result['files_processed']} new files")

        return stats

    def _print_detailed_file_report(self, new_files: List[Dict], updated_files: List[Dict],
                                   unchanged_files: List[Dict], deleted_files: List[Dict]):
        """Print detailed report of file changes."""
        self.stdout.write("\n  Detailed File Change Report:")
        self.stdout.write("  " + "=" * 80)

        if new_files:
            self.stdout.write(f"\n  NEW FILES ({len(new_files)}):")
            for f in new_files[:10]:  # Show first 10
                size_mb = f['file_size'] / (1024 * 1024)
                self.stdout.write(f"    + {f['file_path']} ({size_mb:.2f} MB)")
            if len(new_files) > 10:
                self.stdout.write(f"    ... and {len(new_files) - 10} more")

        if updated_files:
            self.stdout.write(f"\n  UPDATED FILES ({len(updated_files)}):")
            for f in updated_files[:10]:
                size_mb = f['file_size'] / (1024 * 1024)
                prev_rows = f.get('previous_rows', 'unknown')
                self.stdout.write(f"    * {f['file_path']} ({size_mb:.2f} MB, prev rows: {prev_rows})")
            if len(updated_files) > 10:
                self.stdout.write(f"    ... and {len(updated_files) - 10} more")

        if deleted_files:
            self.stdout.write(f"\n  DELETED FILES ({len(deleted_files)}):")
            for f in deleted_files[:10]:
                prev_rows = f.get('rows_imported', 'unknown')
                self.stdout.write(f"    - {f['file_path']} (had {prev_rows} rows)")
            if len(deleted_files) > 10:
                self.stdout.write(f"    ... and {len(deleted_files) - 10} more")

        self.stdout.write("  " + "=" * 80 + "\n")

    def _truncate_table(self, clickhouse_table_name: str) -> bool:
        """
        Truncate a ClickHouse table.

        Args:
            clickhouse_table_name: Table name to truncate

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            self.stdout.write(f"    DRY RUN: Would truncate table {clickhouse_table_name}")
            return True

        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            truncate_sql = f"TRUNCATE TABLE {database}.{clickhouse_table_name}"
            self.clickhouse_client.query(truncate_sql)

            self.stdout.write(f"    Truncated table {clickhouse_table_name}")
            return True

        except Exception as e:
            logger.error(f"Error truncating table {clickhouse_table_name}: {e}")
            return False

    def _import_files(self, site_name: str, table_name: str,
                     clickhouse_table_name: str, file_paths: List[str],
                     file_metadata_list: List[Dict]) -> Dict[str, Any]:
        """
        Import specific files into ClickHouse.

        Args:
            site_name: Site identifier
            table_name: Table identifier
            clickhouse_table_name: ClickHouse table name
            file_paths: List of file paths to import
            file_metadata_list: List of file metadata dictionaries

        Returns:
            Dictionary with import statistics
        """
        from .migrate_parquet_data import ParquetDataMigrator

        migrator = ParquetDataMigrator(self.azure_ops, self.clickhouse_client)

        batch_size = 5000
        max_files = len(file_paths)  # Import all specified files

        # Call migrator with specific file list
        migration_result = migrator.migrate_table_data_batch(
            site_name, table_name, '',  # Empty table_path since we're providing file_list
            clickhouse_table_name, batch_size, max_files,
            file_list=file_paths
        )

        total_rows = migration_result['total_rows']
        file_details = migration_result['file_details']

        # VALIDATION: Check imported row counts against parquet file row counts
        for file_path, imported_rows in file_details.items():
            if imported_rows > 0:
                expected_rows = self._get_parquet_row_count(file_path)
                if expected_rows and expected_rows != imported_rows:
                    self.stdout.write(
                        self.style.WARNING(
                            f"    Row count mismatch: {file_path} - expected {expected_rows}, imported {imported_rows}"
                        )
                    )

        # Track file-to-row-count mappings
        for file_path, row_count in file_details.items():
            self._insert_data_file_mapping(clickhouse_table_name, file_path, row_count)

        # Track individual files in parquet_file_tracking
        for file_metadata in file_metadata_list:
            file_path = file_metadata['file_path']
            row_count = file_details.get(file_path, 0)

            # Check if file tracking exists
            tracked_files = self._get_tracked_files(site_name, table_name)

            # If file doesn't have hash and we're not skipping, compute it now
            # This happens for new files where we didn't compute hash upfront
            if not file_metadata.get('file_hash') and not self.skip_hash and row_count > 0:
                hash_metadata = self._get_file_metadata(file_path, skip_hash=False)
                if hash_metadata and hash_metadata.get('file_hash'):
                    file_metadata['file_hash'] = hash_metadata['file_hash']

            if file_path in tracked_files:
                # Update existing tracking
                self._update_file_tracking(
                    file_path,
                    rows_imported=row_count,
                    status='imported' if row_count > 0 else 'failed',
                    error_message='' if row_count > 0 else 'No rows imported'
                )
            else:
                # Insert new tracking
                self._insert_file_tracking(
                    site_name, table_name, clickhouse_table_name,
                    file_metadata, row_count,
                    status='imported' if row_count > 0 else 'failed'
                )

        return {
            'total_rows': total_rows,
            'files_processed': len([r for r in file_details.values() if r > 0]),
            'errors': [f for f, r in file_details.items() if r == 0]
        }

    def _get_file_metadata(self, file_path: str, skip_hash: bool = False) -> Optional[Dict]:
        """
        Extract metadata from a parquet file including hash.

        Args:
            file_path: Full ADLS path to the parquet file
            skip_hash: If True, skip hash computation for faster processing

        Returns:
            Dictionary with file metadata or None if error occurs
        """
        try:
            import hashlib

            service_client = self.azure_ops.service_client
            filesystem_client = service_client.get_file_system_client(self.azure_ops.filesystem_name)
            file_client = filesystem_client.get_file_client(file_path)

            # Get file properties
            properties = file_client.get_file_properties()

            # Download file content for hash computation
            file_hash = ''
            if not skip_hash:
                download_data = file_client.download_file()
                content = download_data.readall()

                # Compute MD5 hash
                file_hash = hashlib.md5(content).hexdigest()

            return {
                'file_path': file_path,
                'file_size': properties.size,
                'last_modified': properties.last_modified,
                'file_hash': file_hash
            }

        except Exception as e:
            logger.error(f"Error getting file metadata for {file_path}: {e}")
            return None

    def _insert_file_tracking(self, site_name: str, table_name: str,
                             clickhouse_table_name: str, file_metadata: Dict,
                             rows_imported: int = 0, status: str = 'imported',
                             error_message: str = '') -> bool:
        """
        Insert a file tracking record into parquet_file_tracking table.

        Args:
            site_name: Site identifier
            table_name: Table identifier
            clickhouse_table_name: Target ClickHouse table name
            file_metadata: Dict with file_path, file_size, last_modified, file_hash
            rows_imported: Number of rows imported from this file
            status: Import status ('imported', 'failed', 'deleted')
            error_message: Error message if status is 'failed'

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            return True

        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Escape single quotes for SQL safety
            site_name_escaped = site_name.replace("'", "''")
            table_name_escaped = table_name.replace("'", "''")
            clickhouse_table_name_escaped = clickhouse_table_name.replace("'", "''")
            file_path_escaped = file_metadata['file_path'].replace("'", "''")
            file_hash_escaped = file_metadata.get('file_hash', '').replace("'", "''")
            status_escaped = status.replace("'", "''")
            error_message_escaped = error_message.replace("'", "''")
            migration_id_escaped = self.migration_id.replace("'", "''")

            # Format timestamp for ClickHouse storage
            last_modified_str = self._format_timestamp_for_clickhouse(file_metadata['last_modified'])

            insert_sql = f"""
            INSERT INTO {database}.parquet_file_tracking
            (file_path, site_name, table_name, clickhouse_table_name,
             file_size, file_hash, last_modified, rows_imported,
             import_date, import_status, migration_id, error_message)
            VALUES ('{file_path_escaped}', '{site_name_escaped}', '{table_name_escaped}',
                    '{clickhouse_table_name_escaped}', {file_metadata['file_size']},
                    '{file_hash_escaped}', '{last_modified_str}', {rows_imported},
                    now(), '{status_escaped}', '{migration_id_escaped}', '{error_message_escaped}')
            """

            self.clickhouse_client.query(insert_sql)
            return True

        except Exception as e:
            logger.error(f"Error inserting file tracking record: {e}")
            return False

    def _update_file_tracking(self, file_path: str, rows_imported: int = 0,
                             status: str = 'imported', error_message: str = '') -> bool:
        """
        Update an existing file tracking record.

        Args:
            file_path: File path to update
            rows_imported: Updated row count
            status: Updated status
            error_message: Error message if applicable

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            return True

        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Escape single quotes
            file_path_escaped = file_path.replace("'", "''")
            status_escaped = status.replace("'", "''")
            error_message_escaped = error_message.replace("'", "''")
            migration_id_escaped = self.migration_id.replace("'", "''")

            update_sql = f"""
            ALTER TABLE {database}.parquet_file_tracking UPDATE
            rows_imported = {rows_imported},
            import_status = '{status_escaped}',
            import_date = now(),
            migration_id = '{migration_id_escaped}',
            error_message = '{error_message_escaped}'
            WHERE file_path = '{file_path_escaped}'
            """

            self.clickhouse_client.query(update_sql)
            return True

        except Exception as e:
            logger.error(f"Error updating file tracking record: {e}")
            return False

    def _insert_data_file_mapping(self, clickhouse_table_name: str, file_path: str, row_count: int) -> bool:
        """
        Insert file-to-row-count mapping in data_to_file_mapping table.

        Args:
            clickhouse_table_name: ClickHouse table name
            file_path: Source file path
            row_count: Number of rows from this file

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            return True

        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Escape single quotes
            clickhouse_table_name_escaped = clickhouse_table_name.replace("'", "''")
            file_path_escaped = file_path.replace("'", "''")
            migration_id_escaped = self.migration_id.replace("'", "''")

            insert_sql = f"""
            INSERT INTO {database}.data_to_file_mapping
            (clickhouse_table_name, file_path, row_count, import_date, migration_id)
            VALUES ('{clickhouse_table_name_escaped}', '{file_path_escaped}',
                    {row_count}, now(), '{migration_id_escaped}')
            """

            self.clickhouse_client.query(insert_sql)
            return True

        except Exception as e:
            logger.error(f"Error inserting data file mapping: {e}")
            return False

    def _clear_file_tracking_for_table(self, site_name: str, table_name: str) -> bool:
        """
        Clear file tracking records for a specific site and table.

        This method is called when a table is being dropped and recreated to ensure
        that old tracking records with potentially incorrect timestamps are removed.
        This prevents timestamp comparison issues during incremental migrations.

        Args:
            site_name: Site identifier (e.g., 'Jubail-Jazlah')
            table_name: Table identifier (e.g., 'Jubail-Jazlah_Assest_NLP_Data')

        Returns:
            True if successful, False otherwise
        """
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Escape single quotes for safety
            site_name_escaped = site_name.replace("'", "''")
            table_name_escaped = table_name.replace("'", "''")

            delete_sql = f"""
            ALTER TABLE {database}.parquet_file_tracking DELETE
            WHERE site_name = '{site_name_escaped}'
              AND table_name = '{table_name_escaped}'
            """

            self.clickhouse_client.query(delete_sql)
            self.stdout.write(f"    Cleared file tracking for {site_name}.{table_name}")
            return True

        except Exception as e:
            logger.error(f"Error clearing file tracking: {e}")
            self.stdout.write(f"    WARNING: Could not clear file tracking: {e}")
            return False

    def _clear_table_file_mappings(self, clickhouse_table_name: str) -> bool:
        """
        Clear all file mappings for a table (used before re-import).

        Args:
            clickhouse_table_name: ClickHouse table name

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            return True

        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

            # Escape single quotes
            clickhouse_table_name_escaped = clickhouse_table_name.replace("'", "''")

            delete_sql = f"""
            DELETE FROM {database}.data_to_file_mapping
            WHERE clickhouse_table_name = '{clickhouse_table_name_escaped}'
            """

            self.clickhouse_client.query(delete_sql)
            return True

        except Exception as e:
            logger.error(f"Error clearing table file mappings: {e}")
            return False

    # All existing methods remain unchanged below this point
    def _initialize_clickhouse_schema(self):
        """Initialize ClickHouse schema tables with proper migration handling."""
        if self.dry_run:
            self.stdout.write("DRY RUN: Would initialize ClickHouse schema")
            return

        try:
            # Skip schema checks if requested (when tables were created by init_clickhouse_schema)
            if self.skip_schema_check:
                self.stdout.write("Skipping schema table checks (using --skip-schema-check)")
                existing_columns = set()
            else:
                # First, check if migration_log table exists and get its schema
                try:
                    existing_columns = self._get_table_columns("migration_log")
                    
                    if existing_columns:
                        # Table exists, check if it has the base_paths column
                        if "base_paths" not in existing_columns:
                            self.stdout.write("Updating migration_log table schema...")
                            # Add the missing column
                            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
                            alter_sql = f"ALTER TABLE {database}.migration_log ADD COLUMN base_paths String DEFAULT ''"
                            self.clickhouse_client.query(alter_sql)
                            self.stdout.write("Added base_paths column to migration_log table")
                except Exception as e:
                    # If we can't check the table, assume it doesn't exist and create it
                    self.stdout.write(f"Could not check migration_log table: {e}")
                    existing_columns = set()
            
            # Now create/update the schema
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            schema_sql = f"""
            CREATE TABLE IF NOT EXISTS {database}.site_table_mapping (
                site_name String,
                table_name String,
                clickhouse_table_name String,
                parquet_path String,
                base_path String DEFAULT '',
                migration_status String,
                row_count UInt64 DEFAULT 0,
                migration_date DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY (site_name, table_name);

            CREATE TABLE IF NOT EXISTS {database}.migration_log (
                migration_id String,
                command_type String,
                base_paths String DEFAULT '',
                sites_processed UInt32 DEFAULT 0,
                tables_processed UInt32 DEFAULT 0,
                rows_migrated UInt64 DEFAULT 0,
                status String,
                error_message String DEFAULT '',
                started_at DateTime DEFAULT now(),
                completed_at DateTime DEFAULT '1970-01-01 00:00:00'
            ) ENGINE = MergeTree()
            ORDER BY started_at;

            CREATE TABLE IF NOT EXISTS {database}.parquet_file_tracking (
                file_path String,
                site_name String,
                table_name String,
                clickhouse_table_name String,
                file_size UInt64,
                file_hash String,
                last_modified DateTime64(3),
                rows_imported UInt64 DEFAULT 0,
                import_date DateTime DEFAULT now(),
                import_status String DEFAULT 'imported',
                migration_id String DEFAULT '',
                error_message String DEFAULT ''
            ) ENGINE = MergeTree()
            ORDER BY (site_name, table_name, file_path);

            CREATE TABLE IF NOT EXISTS {database}.data_to_file_mapping (
                clickhouse_table_name String,
                file_path String,
                row_count UInt64,
                import_date DateTime DEFAULT now(),
                migration_id String DEFAULT ''
            ) ENGINE = MergeTree()
            ORDER BY (clickhouse_table_name, file_path);

            CREATE TABLE IF NOT EXISTS {database}.schema_evolution_log (
                site_name String,
                table_name String,
                change_date DateTime DEFAULT now(),
                change_type String,
                changes_detail String,
                migration_id String DEFAULT ''
            ) ENGINE = MergeTree()
            ORDER BY (site_name, table_name, change_date);
            """

            for statement in schema_sql.strip().split(';'):
                if statement.strip():
                    self.clickhouse_client.query(statement.strip())

            # Check if site_table_mapping needs base_path column
            existing_mapping_columns = self._get_table_columns("site_table_mapping")
            if existing_mapping_columns and "base_path" not in existing_mapping_columns:
                self.stdout.write("Updating site_table_mapping table schema...")
                database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
                alter_mapping_sql = f"ALTER TABLE {database}.site_table_mapping ADD COLUMN base_path String DEFAULT ''"
                self.clickhouse_client.query(alter_mapping_sql)
                self.stdout.write("Added base_path column to site_table_mapping table")

            self.stdout.write("Initialized ClickHouse schema tables")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to initialize schema: {e}"))
            raise

    def _get_table_columns(self, table_name: str) -> set:
        """Get the column names of a table, returns empty set if table doesn't exist."""
        try:
            # Check if table exists first
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            exists_query = f"EXISTS TABLE {database}.{table_name}"
            table_exists = self.clickhouse_client.query(exists_query).result_rows[0][0]
            
            if not table_exists:
                return set()
                
            # Get column names
            desc_query = f"DESCRIBE TABLE {database}.{table_name}"
            result = self.clickhouse_client.query(desc_query)
            
            columns = set()
            for row in result.result_rows:
                columns.add(row[0])  # Column name is first element
                
            return columns
            
        except Exception as e:
            logger.warning(f"Could not get columns for table {table_name}: {e}")
            return set()

    def _cleanup_duplicate_mappings(self):
        """Remove duplicate entries from site_table_mapping table."""
        if self.dry_run:
            self.stdout.write("DRY RUN: Would cleanup duplicate mappings")
            return

        self.stdout.write("Cleaning up duplicate mappings...")

        # Get database name from environment
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   # First, get a count of duplicates
        count_query = f"""
        SELECT
            site_name,
            table_name,
            COUNT(*) as duplicate_count
        FROM {database}.site_table_mapping
        GROUP BY site_name, table_name
        HAVING COUNT(*) > 1
        """

        result = self.clickhouse_client.query(count_query)
        duplicate_count = len(result.result_rows)

        if duplicate_count == 0:
            self.stdout.write("No duplicates found.")
            return

        self.stdout.write(f"Found {duplicate_count} duplicate site-table combinations.")

        # Create a temporary table with unique records
        # Keep the most recent record (highest migration_date) for each site-table combination
        cleanup_sql = f"""
        CREATE TABLE temp_site_table_mapping AS
        SELECT
            site_name,
            table_name,
            argMax(clickhouse_table_name, migration_date) as clickhouse_table_name,
            argMax(parquet_path, migration_date) as parquet_path,
            argMax(base_path, migration_date) as base_path,
            argMax(migration_status, migration_date) as migration_status,
            argMax(row_count, migration_date) as row_count,
            max(migration_date) as migration_date
        FROM {database}.site_table_mapping
        GROUP BY site_name, table_name;

        RENAME TABLE {database}.site_table_mapping TO {database}.site_table_mapping_backup;
        RENAME TABLE temp_site_table_mapping TO {database}.site_table_mapping;
        """

        # Execute cleanup
        for statement in cleanup_sql.strip().split(';'):
            if statement.strip():
                self.clickhouse_client.query(statement.strip())

        self.stdout.write(
            self.style.SUCCESS(f"Successfully cleaned up {duplicate_count} duplicate mappings")
        )
        self.stdout.write("Original table backed up as 'site_table_mapping_backup'")

    def _discover_adls_structure(self) -> Dict:
        """Discover sites and tables from ADLS across all base paths."""
        self.stdout.write("Discovering ADLS structure across all base paths...")

        sites_data = {}

        # Get sites from ADLS (now from all base paths)
        sites = self.azure_ops.get_all_directories()

        for site in sites:
            site_name = site['name']
            site_path = site['path']
            site_base_path = site.get('base_path', '')

            # Debug: Show what we're getting from Azure
            if self.incremental:
                self.stdout.write(f"Debug: Raw site data - name: '{site_name}', path: '{site_path}', base_path: '{site_base_path}'")

            # Skip 'gold' directory if it appears as a site name - it's a path component, not a site
            if site_name.lower() in ['gold', 'silver', 'bronze']:
                self.stdout.write(f"Skipping '{site_name}' as it's a data tier directory, not a site")
                continue

            # Clean the site name to remove any path components
            clean_site_name = site_name.strip()
            if '/' in clean_site_name:
                clean_site_name = clean_site_name.split('/')[-1]
            
            # Additional cleaning for site names that might have dots or other separators
            if '.' in clean_site_name:
                # If we have something like "gold.Jubail-Jazlah", take the part after the dot
                parts = clean_site_name.split('.')
                if len(parts) > 1 and parts[0].lower() in ['gold', 'silver', 'bronze', 'tables']:
                    clean_site_name = parts[1]
                else:
                    clean_site_name = parts[-1]  # Take the last meaningful part
            
            # Filter by target site if specified (use cleaned name for filtering)
            if self.target_site and clean_site_name != self.target_site:
                continue

            self.stdout.write(f"Processing site: {clean_site_name} (from {site_base_path})")
            
            # Initialize site data if not already present (use clean name as key)
            if clean_site_name not in sites_data:
                sites_data[clean_site_name] = {
                    'tables': [],
                    'base_path': site_base_path,
                    'site_path': site_path,
                    'original_name': site_name  # Keep original for reference
                }

            # Get tables for this site (use original site_name for Azure operations)
            tables = self.azure_ops.get_subdirectories(site_name, site_base_path)

            for table in tables:
                table_name = table['name']

                # Filter by target table if specified
                if self.target_table and table_name != self.target_table:
                    continue

                # Clean the table name too
                clean_table_name = table_name.strip()
                if '/' in clean_table_name:
                    clean_table_name = clean_table_name.split('/')[-1]

                self.stdout.write(f"  Found table: {clean_table_name}")
                
                # Debug: Show table name processing
                if self.incremental:
                    sanitized_name = self._sanitize_table_name(clean_site_name, clean_table_name)
                    self.stdout.write(f"  Debug: Will create ClickHouse table: {sanitized_name}")
                
                # Check if this table already exists (from another base path)
                existing_table = next(
                    (t for t in sites_data[clean_site_name]['tables'] if t['name'] == clean_table_name), 
                    None
                )
                
                if existing_table:
                    self.stdout.write(f"    Table {clean_table_name} already found in another base path, skipping duplicate")
                    continue
                
                sites_data[clean_site_name]['tables'].append({
                    'name': clean_table_name,  # Use clean name
                    'path': table['path'],
                    'site_path': table.get('site_path', ''),
                    'base_path': site_base_path,
                    'original_table_name': table_name  # Keep original for reference
                })

        # Report summary
        total_sites = len(sites_data)
        total_tables = sum(len(site['tables']) for site in sites_data.values())
        self.stdout.write(f"Discovery complete: {total_sites} sites, {total_tables} tables")
        
        return sites_data

    def _create_clickhouse_schemas(self, sites_data: Dict):
        """Create ClickHouse tables based on parquet schemas."""
        self.stdout.write("Creating ClickHouse schemas...")

        for site_name, site_info in sites_data.items():
            for table_info in site_info['tables']:
                table_name = table_info['name']
                table_path = table_info['path']
                base_path = table_info.get('base_path', '')

                try:
                    self._create_table_schema(site_name, table_name, table_path, base_path)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to create schema for {site_name}.{table_name}: {e}")
                    )

    def _create_table_schema(self, site_name: str, table_name: str, table_path: str, base_path: str = ''):
        """Create a single ClickHouse table based on parquet schema."""
        clickhouse_table_name = self._sanitize_table_name(site_name, table_name)

        # Get parquet schema from first file
        schema = self._get_parquet_schema(table_path)
        if not schema:
            raise Exception(f"Could not extract schema from {table_path}")

        # Convert to ClickHouse DDL
        create_sql = self._generate_clickhouse_ddl(clickhouse_table_name, schema)

        if self.dry_run:
            self.stdout.write(f"DRY RUN: Would create table {clickhouse_table_name}")
            self.stdout.write(create_sql)
            return

        # Check if table exists
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        exists_query = f"EXISTS TABLE {database}.{clickhouse_table_name}"
        table_exists = self.clickhouse_client.query(exists_query).result_rows[0][0]

        if table_exists and not self.force:
            self.stdout.write(f"Table {clickhouse_table_name} already exists (use --force to recreate)")
            return

        if table_exists and self.force:
            # Safety check: Only drop tables in schema_only mode
            if self.mode == 'schema_only':
                drop_sql = f"DROP TABLE IF EXISTS {database}.{clickhouse_table_name}"
                self.clickhouse_client.query(drop_sql)
                self.stdout.write(f"Dropped existing table {database}.{clickhouse_table_name}")
            else:
                self.stdout.write(f"WARNING: Table {clickhouse_table_name} already exists. Use --mode=schema_only with --force to recreate tables.")
                return

        # Create table
        self.clickhouse_client.query(create_sql)
        self.stdout.write(f"Created table: {clickhouse_table_name}")

        # Update mapping table
        self._update_site_table_mapping(
            site_name, table_name, clickhouse_table_name,
            table_path, base_path, 'schema_created'
        )

    def _get_parquet_schema(self, table_path: str) -> Optional[pa.Schema]:
        """Extract schema from first parquet file in the table directory."""
        try:
            # Get Azure Data Lake client
            service_client = self.azure_ops.service_client
            filesystem_client = service_client.get_file_system_client(self.azure_ops.filesystem_name)

            # List files in the table directory
            paths = filesystem_client.get_paths(path=table_path, recursive=True)

            for path in paths:
                if not path.is_directory and path.name.endswith('.parquet'):
                    # Download first parquet file to get schema
                    file_client = filesystem_client.get_file_client(path.name)
                    download_data = file_client.download_file()
                    content = download_data.readall()

                    # Read schema using pyarrow
                    parquet_file = pq.ParquetFile(pa.BufferReader(content))
                    return parquet_file.schema_arrow

            return None

        except Exception as e:
            logger.error(f"Error extracting schema from {table_path}: {e}")
            return None

    def _get_merged_parquet_schema(self, table_path: str) -> Optional[pa.Schema]:
        """
        Extract and merge schemas from ALL parquet files in a directory.
        This creates a UNION of all columns from all files, handling schema evolution.

        Args:
            table_path: ADLS path to the table directory

        Returns:
            PyArrow Schema with merged fields from all parquet files, or None if error
        """
        try:
            service_client = self.azure_ops.service_client
            filesystem_client = service_client.get_file_system_client(self.azure_ops.filesystem_name)
            paths = filesystem_client.get_paths(path=table_path, recursive=True)

            schemas = []
            files_processed = 0

            self.stdout.write(f"    Scanning parquet files to merge schemas...")

            for path in paths:
                if not path.is_directory and path.name.endswith('.parquet'):
                    try:
                        # Download file to read schema
                        file_client = filesystem_client.get_file_client(path.name)
                        download_data = file_client.download_file()
                        content = download_data.readall()

                        # Read schema using pyarrow
                        parquet_file = pq.ParquetFile(pa.BufferReader(content))
                        schemas.append(parquet_file.schema_arrow)
                        files_processed += 1

                    except Exception as e:
                        logger.warning(f"Could not read schema from {path.name}: {e}")
                        continue

            if not schemas:
                logger.error(f"No valid parquet schemas found in {table_path}")
                return None

            self.stdout.write(f"    Found {files_processed} parquet files, merging schemas...")

            # Merge all schemas using PyArrow's unify_schemas
            # This creates a union of all fields, handling nullable differences
            try:
                merged_schema = pa.unify_schemas(schemas)

                # Log schema details
                self.stdout.write(f"    Merged schema has {len(merged_schema)} columns")

                # Log any new columns found (comparing first schema with merged)
                if len(schemas) > 1:
                    first_schema_cols = set(schemas[0].names)
                    merged_cols = set(merged_schema.names)
                    new_cols = merged_cols - first_schema_cols

                    if new_cols:
                        self.stdout.write(f"    Additional columns found in other files: {new_cols}")

                return merged_schema

            except Exception as e:
                logger.error(f"Error merging schemas: {e}")
                # Fallback: return first schema if merge fails
                self.stdout.write(f"    WARNING: Schema merge failed, using first file's schema")
                return schemas[0] if schemas else None

        except Exception as e:
            logger.error(f"Error extracting merged schema from {table_path}: {e}")
            return None

    def _generate_clickhouse_ddl(self, table_name: str, schema: pa.Schema) -> str:
        """Generate ClickHouse CREATE TABLE DDL from PyArrow schema with optional partitioning."""
        # Determine partitioning and ordering strategy FIRST
        enable_partitioning = getattr(self, 'enable_partitioning', False)
        partition_column = getattr(self, 'partition_column', None)
        timestamp_column = None

        # Find timestamp column for partitioning (if enabled)
        if enable_partitioning:
            if partition_column:
                timestamp_column = partition_column
            else:
                # Auto-detect first timestamp column
                for field in schema:
                    if pa.types.is_timestamp(field.type):
                        timestamp_column = field.name
                        break

        # Build column definitions
        columns = []
        for field in schema:
            clickhouse_type = self._convert_arrow_to_clickhouse_type(field.type)

            # CRITICAL FIX: Partition columns MUST be non-nullable
            # ClickHouse doesn't allow nullable columns in partition keys
            if enable_partitioning and field.name == timestamp_column:
                # Force partition column to be non-nullable
                columns.append(f"    `{field.name}` {clickhouse_type}")
                if field.nullable:
                    self.stdout.write(f"    NOTE: Partition column '{field.name}' forced to non-nullable")
            else:
                # Other columns can be nullable
                nullable = "Nullable(" + clickhouse_type + ")" if field.nullable else clickhouse_type
                columns.append(f"    `{field.name}` {nullable}")

        # Add source file tracking column for deletion support
        # This column stores the ADLS path of the parquet file that contained each row
        columns.append(f"    `_source_file_path` String DEFAULT ''")

        columns_sql = ",\n".join(columns)

        if enable_partitioning and timestamp_column:
            # Use monthly partitioning by timestamp column
            partition_by = f"toYYYYMM(`{timestamp_column}`)"
            order_by = f"(`{timestamp_column}`)"
            self.stdout.write(f"    Using partitioning by {timestamp_column} (monthly)")
        else:
            # No partitioning - use tuple() for simple ordering
            partition_by = None
            order_by = "tuple()"

        # Add database context to the table name
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

        partition_clause = f"PARTITION BY {partition_by}" if partition_by else ""

        ddl = f"""
        CREATE TABLE IF NOT EXISTS {database}.{table_name} (
{columns_sql}
        ) ENGINE = MergeTree()
        {partition_clause}
        ORDER BY {order_by}
        SETTINGS index_granularity = 8192
        """

        return ddl.strip()

    def _convert_arrow_to_clickhouse_type(self, arrow_type) -> str:
        """Convert PyArrow data type to ClickHouse data type."""
        type_mapping = {
            pa.bool_(): "UInt8",
            pa.int8(): "Int8",
            pa.int16(): "Int16",
            pa.int32(): "Int32",
            pa.int64(): "Int64",
            pa.uint8(): "UInt8",
            pa.uint16(): "UInt16",
            pa.uint32(): "UInt32",
            pa.uint64(): "UInt64",
            pa.float32(): "Float32",
            pa.float64(): "Float64",
            pa.string(): "String",
            pa.binary(): "String",
            pa.date32(): "Date",
            pa.date64(): "Date",
            pa.timestamp('us'): "DateTime64(6)",
            pa.timestamp('ms'): "DateTime64(3)",
            pa.timestamp('ns'): "DateTime64(9)",
        }

        # Handle timestamp with timezone
        if pa.types.is_timestamp(arrow_type):
            if arrow_type.unit == 'us':
                return "DateTime64(6)"
            elif arrow_type.unit == 'ms':
                return "DateTime64(3)"
            elif arrow_type.unit == 'ns':
                return "DateTime64(9)"
            else:
                return "DateTime64(6)"  # Default

        # Default mapping
        for arrow_t, clickhouse_t in type_mapping.items():
            if arrow_type.equals(arrow_t):
                return clickhouse_t

        # Fallback to String for unknown types
        return "String"

    def _migrate_data(self, sites_data: Dict):
        """Migrate actual parquet data to ClickHouse tables."""
        self.stdout.write("Migrating data...")

        for site_name, site_info in sites_data.items():
            for table_info in site_info['tables']:
                table_name = table_info['name']
                table_path = table_info['path']
                base_path = table_info.get('base_path', '')

                try:
                    self._migrate_table_data(site_name, table_name, table_path, base_path)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to migrate data for {site_name}.{table_name}: {e}")
                    )

    def _migrate_table_data(self, site_name: str, table_name: str, table_path: str, base_path: str = ''):
        """Migrate data for a single table."""
        clickhouse_table_name = self._sanitize_table_name(site_name, table_name)

        if self.dry_run:
            self.stdout.write(f"DRY RUN: Would migrate data to {clickhouse_table_name}")
            return

        # Enhanced data migration with safety checks
        if not self.dry_run and self.skip_existing_data:
            # Check if table already has data
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            count_query = f"SELECT COUNT(*) FROM {database}.{clickhouse_table_name}"
            try:
                existing_count = self.clickhouse_client.query(count_query).result_rows[0][0]
                if existing_count > 0:
                    self.stdout.write(f"Skipping data migration for {clickhouse_table_name} (already has {existing_count:,} rows)")
                    return
            except Exception:
                pass  # Continue with migration if count fails

        try:
            self.stdout.write(f"Starting data migration for {clickhouse_table_name}...")

            # Import the data migrator
            from .migrate_parquet_data import ParquetDataMigrator

            # Initialize data migrator
            migrator = ParquetDataMigrator(self.azure_ops, self.clickhouse_client)

            # Migrate data with configurable batch size
            batch_size = 5000  # Adjust based on memory constraints
            max_files = 50     # Process maximum 50 files per table for safety

            migration_result = migrator.migrate_table_data_batch(
                site_name, table_name, table_path,
                clickhouse_table_name, batch_size, max_files
            )

            total_rows = migration_result['total_rows']
            file_details = migration_result['file_details']

            if total_rows > 0:
                # Track file-to-row-count mappings
                for file_path, row_count in file_details.items():
                    self._insert_data_file_mapping(clickhouse_table_name, file_path, row_count)

                # Validate migration
                validation_result = migrator.validate_data_migration(clickhouse_table_name)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully migrated {total_rows} rows from {len(file_details)} files to {clickhouse_table_name}"
                    )
                )

                if validation_result.get("validation_status") == "warning":
                    self.stdout.write(
                        self.style.WARNING(
                            f"Migration completed but validation shows potential issues"
                        )
                    )

                # Update mapping status with actual row count
                self._update_site_table_mapping(
                    site_name, table_name, clickhouse_table_name,
                    table_path, base_path, 'migrated', row_count=total_rows
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"No data migrated for {clickhouse_table_name}")
                )
                self._update_site_table_mapping(
                    site_name, table_name, clickhouse_table_name,
                    table_path, base_path, 'schema_only', row_count=0
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Data migration failed for {clickhouse_table_name}: {e}")
            )
            # Update status as failed
            self._update_site_table_mapping(
                site_name, table_name, clickhouse_table_name,
                table_path, base_path, 'failed', row_count=0
            )

    def _sanitize_table_name(self, site_name: str, table_name: str) -> str:
        """Create a valid ClickHouse table name."""
        # Clean site name to remove any path components or base path references
        clean_site_name = site_name.strip()
        
        # Remove any "gold", "tables", or path components that might have been included
        # Split by common separators and take the last meaningful part
        if '/' in clean_site_name:
            clean_site_name = clean_site_name.split('/')[-1]
        
        # Remove "gold", "tables" prefixes if they somehow got included
        prefixes_to_remove = ['gold_', 'tables_', 'gold', 'tables']
        for prefix in prefixes_to_remove:
            if clean_site_name.lower().startswith(prefix.lower()):
                if prefix.endswith('_'):
                    clean_site_name = clean_site_name[len(prefix):]
                else:
                    # Only remove if followed by separator or if it's the whole name
                    if len(clean_site_name) > len(prefix) and clean_site_name[len(prefix)] in ['_', '-']:
                        clean_site_name = clean_site_name[len(prefix) + 1:]
        
        # Clean table name similarly
        clean_table_name = table_name.strip()
        if '/' in clean_table_name:
            clean_table_name = clean_table_name.split('/')[-1]
            
        # Combine site and table name, sanitize for ClickHouse
        combined = f"{clean_site_name}_{clean_table_name}"
        
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', combined)
        
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure it starts with letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = f"t_{sanitized}"
        elif not sanitized:
            sanitized = "unknown_table"
            
        return sanitized

    def _update_site_table_mapping(self, site_name: str, table_name: str,
                                   clickhouse_table_name: str, parquet_path: str,
                                   base_path: str, status: str, row_count: int = 0):
        """Update the site-table mapping in ClickHouse using UPSERT logic."""
        if self.dry_run:
            return

        # Escape single quotes in strings for SQL safety
        site_name_escaped = site_name.replace("'", "''")
        table_name_escaped = table_name.replace("'", "''")
        clickhouse_table_name_escaped = clickhouse_table_name.replace("'", "''")
        parquet_path_escaped = parquet_path.replace("'", "''")
        base_path_escaped = base_path.replace("'", "''")
        status_escaped = status.replace("'", "''")

        # Get database name from environment
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
        # Use a more robust approach: check if record exists first, then either update or insert
        try:
            # First, ensure the site_table_mapping table exists
            exists_sql = f"EXISTS TABLE {database}.site_table_mapping"
            exists_result = self.clickhouse_client.query(exists_sql)
            table_exists = exists_result.result_rows[0][0]
            
            if not table_exists:
                logger.warning(f"site_table_mapping table does not exist, skipping update for {site_name}.{table_name}")
                return
            
            # Check if record exists
            check_sql = f"""
            SELECT COUNT(*) FROM {database}.site_table_mapping
            WHERE site_name = '{site_name_escaped}' AND table_name = '{table_name_escaped}'
            """
            result = self.clickhouse_client.query(check_sql)
            record_exists = result.result_rows[0][0] > 0
            
            if record_exists:
                # Update existing record
                update_sql = f"""
                ALTER TABLE {database}.site_table_mapping UPDATE
                clickhouse_table_name = '{clickhouse_table_name_escaped}',
                parquet_path = '{parquet_path_escaped}',
                base_path = '{base_path_escaped}',
                migration_status = '{status_escaped}',
                row_count = {row_count},
                migration_date = now()
                WHERE site_name = '{site_name_escaped}' AND table_name = '{table_name_escaped}'
                """
                self.clickhouse_client.query(update_sql)
            else:
                # Insert new record
                insert_sql = f"""
                INSERT INTO {database}.site_table_mapping
                (site_name, table_name, clickhouse_table_name, parquet_path, base_path, migration_status, row_count, migration_date)
                VALUES ('{site_name_escaped}', '{table_name_escaped}', '{clickhouse_table_name_escaped}',
                        '{parquet_path_escaped}', '{base_path_escaped}', '{status_escaped}', {row_count}, now())
                """
                self.clickhouse_client.query(insert_sql)
                
        except Exception as e:
            # Fallback: try simple insert (might fail if duplicate, but that's okay)
            try:
                insert_sql = f"""
                INSERT INTO {database}.site_table_mapping
                (site_name, table_name, clickhouse_table_name, parquet_path, base_path, migration_status, row_count, migration_date)
                VALUES ('{site_name_escaped}', '{table_name_escaped}', '{clickhouse_table_name_escaped}',
                        '{parquet_path_escaped}', '{base_path_escaped}', '{status_escaped}', {row_count}, now())
                """
                self.clickhouse_client.query(insert_sql)
            except Exception as insert_error:
                # Log the error but don't fail the entire migration
                logger.warning(f"Failed to update site_table_mapping for {site_name}.{table_name}: {insert_error}")

    def _log_migration_start(self):
        """Log migration start."""
        if self.dry_run:
            return

        base_paths_str = ",".join(self.base_paths)
        mode_str = "incremental" if self.incremental else self.mode
        
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
        log_sql = f"""
        INSERT INTO {database}.migration_log
        (migration_id, command_type, base_paths, status, started_at)
        VALUES ('{self.migration_id}', '{mode_str}', '{base_paths_str}', 'started', now())
        """
        self.clickhouse_client.query(log_sql)

    def _log_migration_completion(self, sites_data: Dict):
        """Log successful migration completion."""
        if self.dry_run:
            return

        sites_count = len(sites_data)
        tables_count = sum(len(site['tables']) for site in sites_data.values())

        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
        update_sql = f"""
        ALTER TABLE {database}.migration_log UPDATE
        sites_processed = {sites_count},
        tables_processed = {tables_count},
        status = 'completed',
        completed_at = now()
        WHERE migration_id = '{self.migration_id}'
        """
        self.clickhouse_client.query(update_sql)

    def _log_migration_failure(self, error_message: str):
        """Log migration failure."""
        if self.dry_run:
            return

        # Escape single quotes in error message
        escaped_error = error_message.replace("'", "''")

        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
        update_sql = f"""
        ALTER TABLE {database}.migration_log UPDATE
        status = 'failed',
        error_message = '{escaped_error}',
        completed_at = now()
        WHERE migration_id = '{self.migration_id}'
        """
        try:
            self.clickhouse_client.query(update_sql)
        except Exception:
            pass  # Don't fail if logging fails