"""
Django management command to add source file tracking to existing ClickHouse tables.

This command adds the `_source_file_path` column to existing ClickHouse tables,
enabling automatic data deletion when parquet files are removed from ADLS.

Usage:
    # Add column to all tables
    python manage.py add_source_tracking

    # Add column to specific table
    python manage.py add_source_tracking --table=Rabigh3_Chemicals_ppm

    # Preview changes without executing
    python manage.py add_source_tracking --dry-run

    # Drop and re-import tables with full source tracking
    python manage.py add_source_tracking --rebuild

    # Check status of all tables
    python manage.py add_source_tracking --status-only

Note:
    After adding the column, existing rows will have empty `_source_file_path`.
    Only NEW imports will have source file tracking.
    Use --rebuild to re-import all data with proper tracking.
"""

import logging
import os
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from config.clickhouse_connector import get_clickhouse_connector

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add source file tracking column (_source_file_path) to existing ClickHouse tables'

    SOURCE_FILE_COLUMN = '_source_file_path'

    def add_arguments(self, parser):
        parser.add_argument(
            '--table',
            type=str,
            help='Specific table name to update (e.g., Rabigh3_Chemicals_ppm)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without executing'
        )
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Drop and re-import tables with full source tracking'
        )
        parser.add_argument(
            '--status-only',
            action='store_true',
            help='Only check and report status, do not make changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force add column even if it appears to exist'
        )

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run', False)
        self.rebuild = options.get('rebuild', False)
        self.status_only = options.get('status_only', False)
        self.force = options.get('force', False)
        self.specific_table = options.get('table')

        self.database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

        try:
            self.clickhouse_client = get_clickhouse_connector()
        except Exception as e:
            raise CommandError(f"Failed to connect to ClickHouse: {e}")

        self.stdout.write(self.style.HTTP_INFO(
            f"{'[DRY RUN] ' if self.dry_run else ''}Add Source File Tracking to ClickHouse Tables"
        ))
        self.stdout.write("=" * 70)

        # Get tables to process
        tables = self._get_tables_to_process()

        if not tables:
            self.stdout.write(self.style.WARNING("No tables found to process"))
            return

        self.stdout.write(f"\nFound {len(tables)} table(s) to check\n")

        # Process tables
        results = {
            'already_has_column': [],
            'column_added': [],
            'rebuilt': [],
            'errors': []
        }

        for table_info in tables:
            table_name = table_info['clickhouse_table_name']
            site_name = table_info.get('site_name', 'unknown')
            original_table = table_info.get('table_name', 'unknown')

            self.stdout.write(f"\nProcessing: {table_name}")
            self.stdout.write(f"  Site: {site_name}, Table: {original_table}")

            try:
                # Check if table exists
                if not self._table_exists(table_name):
                    self.stdout.write(self.style.WARNING(f"  Table does not exist, skipping"))
                    continue

                # Check if column already exists
                has_column = self._has_source_column(table_name)

                if has_column and not self.force:
                    self.stdout.write(self.style.SUCCESS(f"  Already has {self.SOURCE_FILE_COLUMN} column"))
                    results['already_has_column'].append(table_name)
                    continue

                if self.status_only:
                    self.stdout.write(self.style.WARNING(f"  Missing {self.SOURCE_FILE_COLUMN} column"))
                    continue

                # Handle based on mode
                if self.rebuild:
                    success = self._rebuild_table(table_name, site_name, original_table)
                    if success:
                        results['rebuilt'].append(table_name)
                    else:
                        results['errors'].append(table_name)
                else:
                    success = self._add_column(table_name)
                    if success:
                        results['column_added'].append(table_name)
                    else:
                        results['errors'].append(table_name)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))
                results['errors'].append(table_name)
                logger.error(f"Error processing {table_name}: {e}", exc_info=True)

        # Print summary
        self._print_summary(results)

    def _get_tables_to_process(self) -> List[Dict]:
        """Get list of tables to process from site_table_mapping."""
        try:
            if self.specific_table:
                # Check if specific table exists in mapping
                query = f"""
                SELECT site_name, table_name, clickhouse_table_name, parquet_path
                FROM {self.database}.site_table_mapping
                WHERE clickhouse_table_name = '{self.specific_table}'
                """
            else:
                # Get all tables
                query = f"""
                SELECT site_name, table_name, clickhouse_table_name, parquet_path
                FROM {self.database}.site_table_mapping
                ORDER BY site_name, table_name
                """

            result = self.clickhouse_client.query(query)

            tables = []
            for row in result.result_rows:
                tables.append({
                    'site_name': row[0],
                    'table_name': row[1],
                    'clickhouse_table_name': row[2],
                    'parquet_path': row[3]
                })

            # If specific table not in mapping, still try to process it
            if self.specific_table and not tables:
                self.stdout.write(self.style.WARNING(
                    f"Table {self.specific_table} not found in site_table_mapping, "
                    "will attempt to add column directly"
                ))
                tables.append({
                    'site_name': 'unknown',
                    'table_name': 'unknown',
                    'clickhouse_table_name': self.specific_table,
                    'parquet_path': ''
                })

            return tables

        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            # If site_table_mapping doesn't exist, try direct table listing
            return self._get_tables_from_system()

    def _get_tables_from_system(self) -> List[Dict]:
        """Fallback: Get tables directly from system.tables."""
        try:
            query = f"""
            SELECT name
            FROM system.tables
            WHERE database = '{self.database}'
              AND name NOT IN ('site_table_mapping', 'parquet_file_tracking',
                              'data_to_file_mapping', 'migration_log', 'schema_evolution_log')
              AND name NOT LIKE '.%'
            ORDER BY name
            """

            result = self.clickhouse_client.query(query)

            tables = []
            for row in result.result_rows:
                table_name = row[0]
                if self.specific_table and table_name != self.specific_table:
                    continue
                tables.append({
                    'site_name': 'unknown',
                    'table_name': 'unknown',
                    'clickhouse_table_name': table_name,
                    'parquet_path': ''
                })

            return tables

        except Exception as e:
            logger.error(f"Error getting tables from system: {e}")
            return []

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            query = f"EXISTS TABLE {self.database}.{table_name}"
            result = self.clickhouse_client.query(query)
            return bool(result.result_rows[0][0]) if result.result_rows else False
        except Exception:
            return False

    def _has_source_column(self, table_name: str) -> bool:
        """Check if table has the _source_file_path column."""
        try:
            query = f"""
            SELECT COUNT(*)
            FROM system.columns
            WHERE database = '{self.database}'
              AND table = '{table_name}'
              AND name = '{self.SOURCE_FILE_COLUMN}'
            """
            result = self.clickhouse_client.query(query)
            return result.result_rows[0][0] > 0 if result.result_rows else False
        except Exception as e:
            logger.warning(f"Could not check column existence: {e}")
            return False

    def _add_column(self, table_name: str) -> bool:
        """Add _source_file_path column to table."""
        if self.dry_run:
            self.stdout.write(f"  DRY RUN: Would add {self.SOURCE_FILE_COLUMN} column")
            return True

        try:
            alter_sql = f"""
            ALTER TABLE {self.database}.{table_name}
            ADD COLUMN IF NOT EXISTS `{self.SOURCE_FILE_COLUMN}` String DEFAULT ''
            """

            self.stdout.write(f"  Adding {self.SOURCE_FILE_COLUMN} column...")
            self.clickhouse_client.query(alter_sql)
            self.stdout.write(self.style.SUCCESS(f"  Column added successfully"))

            # Get row count
            row_count = self._get_row_count(table_name)
            self.stdout.write(
                self.style.NOTICE(
                    f"  Note: {row_count} existing rows have empty {self.SOURCE_FILE_COLUMN}. "
                    f"New imports will have source tracking."
                )
            )

            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to add column: {e}"))
            logger.error(f"Failed to add column to {table_name}: {e}")
            return False

    def _rebuild_table(self, table_name: str, site_name: str, original_table: str) -> bool:
        """Rebuild table with source tracking by triggering full re-import."""
        if self.dry_run:
            self.stdout.write(f"  DRY RUN: Would rebuild table {table_name}")
            return True

        self.stdout.write(f"  Rebuilding table with source tracking...")
        self.stdout.write(self.style.WARNING(
            f"  WARNING: This will drop and re-import all data for {table_name}"
        ))

        try:
            # Call migrate_adls_to_clickhouse with force flag for this table
            call_command(
                'migrate_adls_to_clickhouse',
                '--mode=full',
                f'--table={table_name}',
                '--force',
                verbosity=1
            )

            self.stdout.write(self.style.SUCCESS(f"  Table rebuilt successfully"))
            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to rebuild table: {e}"))
            logger.error(f"Failed to rebuild {table_name}: {e}")
            return False

    def _get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        try:
            query = f"SELECT COUNT(*) FROM {self.database}.{table_name}"
            result = self.clickhouse_client.query(query)
            return result.result_rows[0][0] if result.result_rows else 0
        except Exception:
            return 0

    def _print_summary(self, results: Dict):
        """Print summary of operations."""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.HTTP_INFO("Summary"))
        self.stdout.write("=" * 70)

        if results['already_has_column']:
            self.stdout.write(self.style.SUCCESS(
                f"\nAlready have column ({len(results['already_has_column'])}):"
            ))
            for t in results['already_has_column']:
                self.stdout.write(f"  - {t}")

        if results['column_added']:
            self.stdout.write(self.style.SUCCESS(
                f"\nColumn added ({len(results['column_added'])}):"
            ))
            for t in results['column_added']:
                self.stdout.write(f"  - {t}")

        if results['rebuilt']:
            self.stdout.write(self.style.SUCCESS(
                f"\nRebuilt with tracking ({len(results['rebuilt'])}):"
            ))
            for t in results['rebuilt']:
                self.stdout.write(f"  - {t}")

        if results['errors']:
            self.stdout.write(self.style.ERROR(
                f"\nErrors ({len(results['errors'])}):"
            ))
            for t in results['errors']:
                self.stdout.write(f"  - {t}")

        # Total
        total = (
            len(results['already_has_column']) +
            len(results['column_added']) +
            len(results['rebuilt']) +
            len(results['errors'])
        )
        self.stdout.write(f"\nTotal tables processed: {total}")

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                "\n[DRY RUN] No changes were made. Remove --dry-run to apply changes."
            ))
