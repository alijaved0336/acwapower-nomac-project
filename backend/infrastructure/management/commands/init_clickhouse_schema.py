"""
Django management command to initialize ClickHouse database schema.

This command:
1. Creates the required database if it doesn't exist
2. Creates the site_table_mapping table
3. Creates the migration_log table
4. Verifies the schema is properly initialized

Usage:
    python manage.py init_clickhouse_schema
"""
import logging
import os
from django.core.management.base import BaseCommand, CommandError
from config.clickhouse_connector import get_clickhouse_connector

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize ClickHouse database schema for ADLS migration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing tables'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually executing'
        )

    def handle(self, *args, **options):
        self.force = options['force']
        self.dry_run = options['dry_run']
        
        self.stdout.write('Initializing ClickHouse database schema...')
        
        try:
            # Connect to ClickHouse with auto-create database
            self.clickhouse_client = get_clickhouse_connector(auto_create_database=True)
            self.stdout.write('✓ Connected to ClickHouse successfully')
            
            # Initialize schema
            self._create_database()
            self._create_site_table_mapping()
            self._create_migration_log()
            
            # Verify schema
            self._verify_schema()
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 ClickHouse schema initialized successfully!')
            )
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {str(e)}")
            raise CommandError(f"Schema initialization failed: {str(e)}")
        finally:
            if hasattr(self, 'clickhouse_client') and self.clickhouse_client:
                self.clickhouse_client.close()

    def _create_database(self):
        """Create the database if it doesn't exist"""
        self.stdout.write('1. Creating database...')
        
        # Get database name from environment
        import os
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
        if self.dry_run:
            self.stdout.write(f'  DRY RUN: Would create database {database}')
            return
        
        try:
            self.clickhouse_client.command(f"CREATE DATABASE IF NOT EXISTS {database}")
            self.stdout.write(f'  ✓ Database {database} created/verified')
        except Exception as e:
            raise CommandError(f"Failed to create database: {str(e)}")

    def _create_site_table_mapping(self):
        """Create the site_table_mapping table"""
        self.stdout.write('2. Creating site_table_mapping table...')
        
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {database}.site_table_mapping (
            site_name String,
            table_name String,
            clickhouse_table_name String,  -- Sanitized table name for ClickHouse
            parquet_path String,
            migration_status String,       -- 'pending', 'migrated', 'failed'
            row_count UInt64 DEFAULT 0,
            migration_date DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (site_name, table_name)
        SETTINGS index_granularity = 8192
        """
        
        if self.dry_run:
            self.stdout.write('  DRY RUN: Would create site_table_mapping table')
            return
        
        try:
            if self.force:
                database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
                self.clickhouse_client.command(f"DROP TABLE IF EXISTS {database}.site_table_mapping")
                self.stdout.write(f'  ✓ Dropped existing {database}.site_table_mapping table')
            
            self.clickhouse_client.command(create_table_sql)
            self.stdout.write('  ✓ site_table_mapping table created/verified')
        except Exception as e:
            raise CommandError(f"Failed to create site_table_mapping table: {str(e)}")

    def _create_migration_log(self):
        """Create the migration_log table"""
        self.stdout.write('3. Creating migration_log table...')
        
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {database}.migration_log (
            migration_id String,
            command_type String,           -- 'schema_creation', 'data_migration'
            sites_processed UInt32,
            tables_processed UInt32,
            rows_migrated UInt64,
            status String,                 -- 'started', 'completed', 'failed'
            error_message String DEFAULT '',
            started_at DateTime DEFAULT now(),
            completed_at DateTime DEFAULT '1970-01-01 00:00:00'
        ) ENGINE = MergeTree()
        ORDER BY started_at
        SETTINGS index_granularity = 8192
        """
        
        if self.dry_run:
            self.stdout.write('  DRY RUN: Would create migration_log table')
            return
        
        try:
            if self.force:
                database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
                self.clickhouse_client.command(f"DROP TABLE IF EXISTS {database}.migration_log")
                self.stdout.write(f'  ✓ Dropped existing {database}.migration_log table')
            
            self.clickhouse_client.command(create_table_sql)
            self.stdout.write('  ✓ migration_log table created/verified')
        except Exception as e:
            raise CommandError(f"Failed to create migration_log table: {str(e)}")

    def _verify_schema(self):
        """Verify that the schema was created correctly"""
        self.stdout.write('4. Verifying schema...')
        
        if self.dry_run:
            self.stdout.write('  DRY RUN: Would verify schema')
            return
        
        try:
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            # Check if tables exist using EXISTS TABLE with database context
            required_tables = ['site_table_mapping', 'migration_log']
            missing_tables = []
            
            for table in required_tables:
                exists_query = f"EXISTS TABLE {database}.{table}"
                exists_result = self.clickhouse_client.query(exists_query)
                if not exists_result.result_rows[0][0]:
                    missing_tables.append(table)
            
            if missing_tables:
                raise CommandError(f"Missing required tables: {missing_tables}")
            
            self.stdout.write(f'  ✓ All required tables exist: {required_tables}')
            
            # Check table structures using database context
            for table in required_tables:
                desc_query = f"DESCRIBE TABLE {database}.{table}"
                desc_result = self.clickhouse_client.query(desc_query)
                column_count = len(desc_result.result_rows)
                self.stdout.write(f'  ✓ {table} has {column_count} columns')
                
        except Exception as e:
            raise CommandError(f"Schema verification failed: {str(e)}")
