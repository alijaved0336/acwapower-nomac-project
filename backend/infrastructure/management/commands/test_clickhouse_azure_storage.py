"""
Django management command to test ClickHouse Azure Storage integration.

This command:
1. Tests connection to ClickHouse
2. Tests Azure Storage configuration
3. Creates a test table using Azure Storage
4. Verifies data can be written and read from Azure Storage

Usage:
    python manage.py test_clickhouse_azure_storage
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from config.clickhouse_connector import get_clickhouse_connector
from config.clickhouse_azure_storage import get_azure_storage_config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test ClickHouse Azure Storage integration'

    def handle(self, *args, **options):
        self.stdout.write('Testing ClickHouse Azure Storage integration...')
        
        try:
            # Test 1: Azure Storage Configuration
            self.stdout.write('1. Testing Azure Storage configuration...')
            azure_config = get_azure_storage_config()
            
            if not azure_config.is_configured():
                raise CommandError("Azure Storage is not properly configured. Check environment variables.")
            
            storage_config = azure_config.get_storage_config()
            self.stdout.write(
                self.style.SUCCESS(f"✓ Azure Storage configured: {storage_config['storage_account']}")
            )
            
            # Test 2: ClickHouse Connection
            self.stdout.write('2. Testing ClickHouse connection...')
            clickhouse_client = get_clickhouse_connector()
            self.stdout.write(self.style.SUCCESS("✓ ClickHouse connection successful"))
            
            # Test 3: Create test table with Azure Storage
            self.stdout.write('3. Creating test table with Azure Storage...')
            test_table_name = "test_azure_storage"
            
            # Drop table if exists
            try:
                clickhouse_client.command(f"DROP TABLE IF EXISTS {test_table_name}")
            except:
                pass
            
            # Create table using Azure Storage
            create_table_sql = f"""
            CREATE TABLE {test_table_name} (
                id UInt32,
                name String,
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY id
            SETTINGS storage_policy = 'azure_policy'
            """
            
            clickhouse_client.command(create_table_sql)
            self.stdout.write(self.style.SUCCESS("✓ Test table created with Azure Storage policy"))
            
            # Test 4: Insert test data
            self.stdout.write('4. Testing data insertion...')
            insert_sql = f"""
            INSERT INTO {test_table_name} (id, name) VALUES
            (1, 'Test Record 1'),
            (2, 'Test Record 2'),
            (3, 'Test Record 3')
            """
            
            clickhouse_client.command(insert_sql)
            self.stdout.write(self.style.SUCCESS("✓ Test data inserted successfully"))
            
            # Test 5: Read test data
            self.stdout.write('5. Testing data retrieval...')
            result = clickhouse_client.query(f"SELECT * FROM {test_table_name} ORDER BY id")
            
            if result.result_rows:
                self.stdout.write(self.style.SUCCESS(f"✓ Retrieved {len(result.result_rows)} records"))
                for row in result.result_rows:
                    self.stdout.write(f"  - ID: {row[0]}, Name: {row[1]}, Created: {row[2]}")
            else:
                raise CommandError("No data retrieved from test table")
            
            # Test 6: Cleanup
            self.stdout.write('6. Cleaning up test table...')
            clickhouse_client.command(f"DROP TABLE {test_table_name}")
            self.stdout.write(self.style.SUCCESS("✓ Test table cleaned up"))
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 All tests passed! ClickHouse Azure Storage integration is working correctly.')
            )
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise CommandError(f"Test failed: {str(e)}")
        finally:
            if 'clickhouse_client' in locals():
                clickhouse_client.close()
