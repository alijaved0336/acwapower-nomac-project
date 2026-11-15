"""
Automated ClickHouse Backup Command

This command automatically backs up ClickHouse data to Azure Blob Storage
and can restore it when needed. Designed to work with Container Apps.
"""

import os
import json
import logging
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from config.clickhouse_connector import get_clickhouse_connector
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automated backup and restore for ClickHouse data in Container Apps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            choices=['backup', 'restore', 'check'],
            default='backup',
            help='Action to perform: backup, restore, or check backup status'
        )
        parser.add_argument(
            '--backup-name',
            help='Specific backup name to restore (optional)'
        )
        parser.add_argument(
            '--auto-restore',
            action='store_true',
            help='Automatically restore from latest backup if tables are missing'
        )

    def handle(self, *args, **options):
        action = options.get('action', 'backup')
        
        try:
            if action == 'backup':
                self._perform_backup()
            elif action == 'restore':
                self._perform_restore(options.get('backup_name'))
            elif action == 'check':
                self._check_backup_status()
                
        except Exception as e:
            logger.error(f"Command failed: {e}")
            raise CommandError(f"Command failed: {e}")

    def _perform_backup(self):
        """Perform automated backup of ClickHouse data"""
        self.stdout.write('Starting automated ClickHouse backup...')
        
        try:
            # Initialize clients
            self.clickhouse_client = get_clickhouse_connector()
            self.blob_client = BlobServiceClient.from_connection_string(
                os.getenv('AZURE_CONNECTION_STRING')
            )
            
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Check if tables exist
            tables = self._get_all_tables(database)
            if not tables:
                self.stdout.write('No tables found to backup')
                return
            
            self.stdout.write(f'Found {len(tables)} tables to backup')
            
            # Backup each table
            backup_data = {
                'timestamp': timestamp,
                'database': database,
                'tables': {},
                'backup_metadata': {
                    'total_tables': len(tables),
                    'backup_time': datetime.now().isoformat()
                }
            }
            
            for table in tables:
                self.stdout.write(f'Backing up table: {table}')
                table_data = self._backup_table(database, table)
                backup_data['tables'][table] = table_data
            
            # Upload backup to Azure Blob Storage
            backup_name = f"clickhouse_auto_backup_{timestamp}.json"
            self._upload_backup(backup_name, backup_data)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Backup completed: {backup_name}')
            )
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    def _perform_restore(self, backup_name=None):
        """Restore ClickHouse data from backup"""
        self.stdout.write('Starting ClickHouse restore...')
        
        try:
            # Initialize clients
            self.clickhouse_client = get_clickhouse_connector()
            self.blob_client = BlobServiceClient.from_connection_string(
                os.getenv('AZURE_CONNECTION_STRING')
            )
            
            # Get backup to restore
            if not backup_name:
                backup_name = self._get_latest_backup()
            
            if not backup_name:
                raise CommandError("No backup found to restore")
            
            self.stdout.write(f'Restoring from backup: {backup_name}')
            
            # Download backup
            backup_data = self._download_backup(backup_name)
            
            # Restore tables
            database = backup_data['database']
            for table_name, table_data in backup_data['tables'].items():
                self.stdout.write(f'Restoring table: {table_name}')
                self._restore_table(database, table_name, table_data)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Restore completed from: {backup_name}')
            )
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise

    def _check_backup_status(self):
        """Check backup status and table existence"""
        self.stdout.write('Checking ClickHouse backup status...')
        
        try:
            # Check current tables
            self.clickhouse_client = get_clickhouse_connector()
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            current_tables = self._get_all_tables(database)
            
            self.stdout.write(f'Current tables in {database}: {len(current_tables)}')
            for table in current_tables:
                self.stdout.write(f'  - {table}')
            
            # Check available backups
            self.blob_client = BlobServiceClient.from_connection_string(
                os.getenv('AZURE_CONNECTION_STRING')
            )
            
            backups = self._list_backups()
            self.stdout.write(f'Available backups: {len(backups)}')
            for backup in backups:
                self.stdout.write(f'  - {backup}')
            
            # Check if restore is needed
            if len(current_tables) == 0 and len(backups) > 0:
                self.stdout.write(
                    self.style.WARNING('⚠ No tables found but backups available. Consider running restore.')
                )
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise

    def _get_all_tables(self, database):
        """Get all tables in the database"""
        try:
            query = f"SHOW TABLES FROM {database}"
            result = self.clickhouse_client.query(query)
            return [row[0] for row in result.result_rows]
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []

    def _backup_table(self, database, table):
        """Backup a single table"""
        try:
            # Get table schema
            schema_query = f"SHOW CREATE TABLE {database}.{table}"
            schema_result = self.clickhouse_client.query(schema_query)
            table_schema = schema_result.result_rows[0][0]
            
            # Get table data
            data_query = f"SELECT * FROM {database}.{table} FORMAT JSONEachRow"
            data_result = self.clickhouse_client.query(data_query)
            table_data = data_result.result_rows
            
            return {
                'schema': table_schema,
                'data': table_data,
                'row_count': len(table_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to backup table {table}: {e}")
            return None

    def _restore_table(self, database, table_name, table_data):
        """Restore a single table"""
        try:
            # Drop existing table if exists
            try:
                self.clickhouse_client.query(f"DROP TABLE IF EXISTS {database}.{table_name}")
            except:
                pass
            
            # Create table from schema
            create_sql = table_data['schema']
            self.clickhouse_client.query(create_sql)
            
            # Insert data if exists
            if table_data['data']:
                # Convert data to INSERT format
                data_rows = table_data['data']
                if data_rows:
                    # Get column names from first row
                    columns = list(data_rows[0].keys())
                    columns_str = ', '.join([f'`{col}`' for col in columns])
                    
                    # Insert data in batches
                    batch_size = 1000
                    for i in range(0, len(data_rows), batch_size):
                        batch = data_rows[i:i + batch_size]
                        
                        # Create VALUES clause
                        values_list = []
                        for row in batch:
                            values = []
                            for col in columns:
                                value = row.get(col)
                                if value is None:
                                    values.append('NULL')
                                elif isinstance(value, str):
                                    values.append(f"'{value.replace("'", "''")}'")
                                else:
                                    values.append(str(value))
                            values_list.append(f"({', '.join(values)})")
                        
                        insert_sql = f"""
                        INSERT INTO {database}.{table_name} ({columns_str})
                        VALUES {', '.join(values_list)}
                        """
                        
                        self.clickhouse_client.query(insert_sql)
            
            self.stdout.write(f'  ✓ Restored {table_name} with {len(table_data["data"])} rows')
            
        except Exception as e:
            logger.error(f"Failed to restore table {table_name}: {e}")
            raise

    def _upload_backup(self, backup_name, backup_data):
        """Upload backup to Azure Blob Storage"""
        try:
            blob_client = self.blob_client.get_blob_client(
                container="swro",
                blob=f"clickhouse_backups/{backup_name}"
            )
            
            blob_client.upload_blob(
                json.dumps(backup_data, indent=2),
                overwrite=True
            )
            
        except Exception as e:
            logger.error(f"Failed to upload backup: {e}")
            raise

    def _download_backup(self, backup_name):
        """Download backup from Azure Blob Storage"""
        try:
            blob_client = self.blob_client.get_blob_client(
                container="swro",
                blob=f"clickhouse_backups/{backup_name}"
            )
            
            backup_content = blob_client.download_blob().readall()
            return json.loads(backup_content)
            
        except Exception as e:
            logger.error(f"Failed to download backup: {e}")
            raise

    def _list_backups(self):
        """List available backups"""
        try:
            container_client = self.blob_client.get_container_client("swro")
            blobs = container_client.list_blobs(name_starts_with="clickhouse_backups/")
            
            backups = []
            for blob in blobs:
                if blob.name.endswith('.json'):
                    backups.append(blob.name.split('/')[-1])
            
            return sorted(backups, reverse=True)  # Latest first
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    def _get_latest_backup(self):
        """Get the latest backup name"""
        backups = self._list_backups()
        return backups[0] if backups else None
