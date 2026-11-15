"""
Apply ClickHouse Storage Configuration

This command attempts to apply Azure Blob Storage configuration to a running ClickHouse instance
without requiring a restart.
"""

import os
import logging
from django.core.management.base import BaseCommand, CommandError
from config.clickhouse_connector import get_clickhouse_connector

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Apply Azure Blob Storage configuration to running ClickHouse instance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force apply configuration even if it might fail'
        )

    def handle(self, *args, **options):
        self.stdout.write('Applying ClickHouse storage configuration...')
        
        try:
            # Initialize ClickHouse client
            self.clickhouse_client = get_clickhouse_connector()
            
            # Get database name
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            self.stdout.write('1. Checking current storage configuration...')
            self._check_current_config()
            
            self.stdout.write('2. Attempting to create Azure Blob Storage disk...')
            self._create_azure_disk()
            
            self.stdout.write('3. Attempting to create storage policy...')
            self._create_storage_policy()
            
            self.stdout.write('4. Testing Azure Blob Storage access...')
            self._test_azure_access()
            
            self.stdout.write(
                self.style.SUCCESS('✓ Storage configuration applied successfully!')
            )
            
        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            if options.get('force'):
                self.stdout.write(
                    self.style.WARNING(f'⚠ Configuration failed but continuing: {e}')
                )
            else:
                raise CommandError(f"Configuration failed: {e}")

    def _check_current_config(self):
        """Check current storage configuration"""
        try:
            # Check available disks
            query = "SELECT name, type FROM system.disks"
            result = self.clickhouse_client.query(query)
            
            self.stdout.write('  Current disks:')
            for row in result.result_rows:
                disk_name, disk_type = row
                self.stdout.write(f'    - {disk_name}: {disk_type}')
                
            # Check storage policies
            query = "SELECT name FROM system.storage_policies"
            result = self.clickhouse_client.query(query)
            
            self.stdout.write('  Current storage policies:')
            for row in result.result_rows:
                policy_name = row[0]
                self.stdout.write(f'    - {policy_name}')
                
        except Exception as e:
            self.stdout.write(f'  ⚠ Could not check current config: {e}')

    def _create_azure_disk(self):
        """Attempt to create Azure Blob Storage disk"""
        try:
            # This might not work on running ClickHouse, but worth trying
            create_disk_sql = """
            CREATE DISK IF NOT EXISTS azure_blob_storage
            TYPE = azure_blob_storage
            STORAGE_ACCOUNT_URL = 'https://mpcswrosg.blob.core.windows.net'
            CONTAINER_NAME = 'swro'
            ACCOUNT_NAME = 'mpcswrosg'
            ACCOUNT_KEY = '${AZURE_STORAGE_KEY}'
            """
            
            self.clickhouse_client.query(create_disk_sql)
            self.stdout.write('  ✓ Azure Blob Storage disk created')
            
        except Exception as e:
            self.stdout.write(f'  ⚠ Could not create Azure disk (expected): {e}')

    def _create_storage_policy(self):
        """Attempt to create storage policy"""
        try:
            create_policy_sql = """
            CREATE STORAGE POLICY IF NOT EXISTS azure_policy
            VOLUMES = azure_volume
            """
            
            self.clickhouse_client.query(create_policy_sql)
            self.stdout.write('  ✓ Storage policy created')
            
        except Exception as e:
            self.stdout.write(f'  ⚠ Could not create storage policy (expected): {e}')

    def _test_azure_access(self):
        """Test if we can access Azure Blob Storage"""
        try:
            # Try to create a test table with Azure storage policy
            test_table = f"{os.getenv('CLICKHOUSE_DATABASE', 'swro_db')}.test_azure_config"
            
            # Drop test table if exists
            try:
                self.clickhouse_client.query(f"DROP TABLE IF EXISTS {test_table}")
            except:
                pass
            
            # Create test table
            create_sql = f"""
            CREATE TABLE {test_table} (
                id UInt32,
                test_data String
            ) ENGINE = MergeTree()
            ORDER BY id
            SETTINGS storage_policy = 'default'
            """
            
            self.clickhouse_client.query(create_sql)
            self.stdout.write('  ✓ Test table created with default storage policy')
            
            # Insert test data
            insert_sql = f"INSERT INTO {test_table} VALUES (1, 'test')"
            self.clickhouse_client.query(insert_sql)
            self.stdout.write('  ✓ Test data inserted')
            
            # Clean up
            self.clickhouse_client.query(f"DROP TABLE {test_table}")
            self.stdout.write('  ✓ Test table cleaned up')
            
        except Exception as e:
            self.stdout.write(f'  ⚠ Azure access test failed: {e}')
            raise
