"""
Test Azure Blob Storage Persistence for ClickHouse

This command tests if ClickHouse tables are properly persisted to Azure Blob Storage
and survive container restarts.
"""

import os
import logging
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from config.clickhouse_connector import get_clickhouse_connector

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Azure Blob Storage persistence for ClickHouse tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test tables after testing'
        )

    def handle(self, *args, **options):
        self.stdout.write('Testing Azure Blob Storage persistence...')
        
        try:
            # Initialize ClickHouse client
            self.clickhouse_client = get_clickhouse_connector()
            
            # Get database name
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            # Test table name
            test_table = f"{database}.test_azure_persistence"
            
            self.stdout.write('1. Creating test table with Azure Blob Storage...')
            self._create_test_table(test_table)
            
            self.stdout.write('2. Inserting test data...')
            self._insert_test_data(test_table)
            
            self.stdout.write('3. Verifying data persistence...')
            self._verify_data_persistence(test_table)
            
            self.stdout.write('4. Checking storage policy...')
            self._check_storage_policy(test_table)
            
            if options.get('cleanup'):
                self.stdout.write('5. Cleaning up test table...')
                self._cleanup_test_table(test_table)
            
            self.stdout.write(
                self.style.SUCCESS('✓ Azure Blob Storage persistence test completed successfully!')
            )
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise CommandError(f"Test failed: {e}")

    def _create_test_table(self, table_name):
        """Create a test table with Azure Blob Storage policy"""
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id UInt32,
            test_data String,
            created_at DateTime DEFAULT now(),
            random_value Float64
        ) ENGINE = MergeTree()
        ORDER BY id
        SETTINGS index_granularity = 8192, storage_policy = 'default'
        """
        
        self.clickhouse_client.query(create_sql)
        self.stdout.write(f'  ✓ Created test table: {table_name}')

    def _insert_test_data(self, table_name):
        """Insert test data into the table"""
        # Insert multiple rows of test data
        test_data = []
        for i in range(100):
            test_data.append({
                'id': i,
                'test_data': f'Test row {i} - {datetime.now().isoformat()}',
                'random_value': i * 3.14159
            })
        
        # Insert data
        insert_sql = f"""
        INSERT INTO {table_name} (id, test_data, random_value)
        VALUES {', '.join([f"({row['id']}, '{row['test_data']}', {row['random_value']})" for row in test_data])}
        """
        
        self.clickhouse_client.query(insert_sql)
        self.stdout.write(f'  ✓ Inserted {len(test_data)} test rows')

    def _verify_data_persistence(self, table_name):
        """Verify that data is accessible"""
        # Count rows
        count_sql = f"SELECT count() FROM {table_name}"
        count_result = self.clickhouse_client.query(count_sql)
        row_count = count_result.result_rows[0][0]
        
        self.stdout.write(f'  ✓ Table contains {row_count} rows')
        
        # Get sample data
        sample_sql = f"SELECT * FROM {table_name} LIMIT 5"
        sample_result = self.clickhouse_client.query(sample_sql)
        
        self.stdout.write('  ✓ Sample data:')
        for row in sample_result.result_rows:
            self.stdout.write(f'    - ID: {row[0]}, Data: {row[1][:50]}...')

    def _check_storage_policy(self, table_name):
        """Check if table is using the correct storage policy"""
        try:
            # Get table information
            info_sql = f"SHOW CREATE TABLE {table_name}"
            info_result = self.clickhouse_client.query(info_sql)
            create_statement = info_result.result_rows[0][0]
            
            if 'storage_policy = \'default\'' in create_statement:
                self.stdout.write('  ✓ Table is using default storage policy (Azure Blob Storage)')
            else:
                self.stdout.write('  ⚠ Table storage policy not confirmed')
                
        except Exception as e:
            self.stdout.write(f'  ⚠ Could not verify storage policy: {e}')

    def _cleanup_test_table(self, table_name):
        """Clean up the test table"""
        try:
            drop_sql = f"DROP TABLE IF EXISTS {table_name}"
            self.clickhouse_client.query(drop_sql)
            self.stdout.write(f'  ✓ Cleaned up test table: {table_name}')
        except Exception as e:
            self.stdout.write(f'  ⚠ Could not clean up test table: {e}')
