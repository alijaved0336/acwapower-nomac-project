"""
ClickHouse Startup Restore Command

This command should be run when the container starts to automatically
restore data from backups if tables are missing.
"""

import os
import logging
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically restore ClickHouse data on container startup'

    def handle(self, *args, **options):
        # Check if auto-restore is enabled
        auto_restore_enabled = os.getenv('AUTO_RESTORE_ENABLED', 'false').lower() == 'true'
        
        if not auto_restore_enabled:
            self.stdout.write('Auto-restore is disabled. Skipping startup restore.')
            return
        
        self.stdout.write('Starting ClickHouse startup restore process...')
        
        try:
            # Check if ClickHouse is ready
            self._wait_for_clickhouse()
            
            # Check current table status
            self._check_table_status()
            
            # Restore if needed
            self._restore_if_needed()
            
            self.stdout.write(
                self.style.SUCCESS('✓ ClickHouse startup restore completed')
            )
            
        except Exception as e:
            logger.error(f"Startup restore failed: {e}")
            # Don't raise error - let the container start even if restore fails
            self.stdout.write(
                self.style.WARNING(f'⚠ Startup restore failed: {e}')
            )

    def _wait_for_clickhouse(self):
        """Wait for ClickHouse to be ready"""
        import time
        from config.clickhouse_connector import get_clickhouse_connector
        
        self.stdout.write('Waiting for ClickHouse to be ready...')
        
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                client = get_clickhouse_connector()
                # Simple query to test connection
                client.query("SELECT 1")
                self.stdout.write('✓ ClickHouse is ready')
                return
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.stdout.write(f'  Attempt {attempt + 1}/{max_attempts}: ClickHouse not ready yet...')
                    time.sleep(10)
                else:
                    raise CommandError(f"ClickHouse not ready after {max_attempts} attempts: {e}")

    def _check_table_status(self):
        """Check current table status"""
        try:
            from config.clickhouse_connector import get_clickhouse_connector
            
            client = get_clickhouse_connector()
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            # Check if database exists
            try:
                client.query(f"USE {database}")
            except:
                self.stdout.write(f'Database {database} does not exist')
                return
            
            # Get table count
            query = f"SHOW TABLES FROM {database}"
            result = client.query(query)
            table_count = len(result.result_rows)
            
            self.stdout.write(f'Current tables in {database}: {table_count}')
            
            if table_count == 0:
                self.stdout.write('⚠ No tables found - restore may be needed')
            else:
                self.stdout.write('✓ Tables found - no restore needed')
                
        except Exception as e:
            logger.error(f"Failed to check table status: {e}")

    def _restore_if_needed(self):
        """Restore data if tables are missing"""
        try:
            from config.clickhouse_connector import get_clickhouse_connector
            
            client = get_clickhouse_connector()
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            # Check if tables exist
            try:
                query = f"SHOW TABLES FROM {database}"
                result = client.query(query)
                table_count = len(result.result_rows)
                
                if table_count > 0:
                    self.stdout.write('✓ Tables exist - skipping restore')
                    return
                    
            except:
                # Database or tables don't exist
                pass
            
            self.stdout.write('No tables found - attempting restore...')
            
            # Run restore command
            try:
                call_command('backup_clickhouse_automated', action='restore')
                self.stdout.write('✓ Restore completed successfully')
            except Exception as e:
                self.stdout.write(f'⚠ Restore failed: {e}')
                # Continue - don't fail the startup
                
        except Exception as e:
            logger.error(f"Restore check failed: {e}")
            # Continue - don't fail the startup
