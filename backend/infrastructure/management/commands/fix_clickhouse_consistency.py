"""
Django management command to fix ClickHouse replica consistency issues.
This command helps diagnose and fix the intermittent table visibility problem.
"""

import logging
import os
import time
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from config.clickhouse_connector import get_clickhouse_connector, execute_clickhouse_query

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Fix ClickHouse replica consistency issues.
    
    This command helps diagnose and resolve the intermittent table visibility problem
    where tables appear and disappear, and 'migration_log table does not exist' errors occur.
    
    Usage:
        python manage.py fix_clickhouse_consistency --check
        python manage.py fix_clickhouse_consistency --fix
        python manage.py fix_clickhouse_consistency --force-schema
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Check for consistency issues without making changes'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix consistency issues'
        )
        parser.add_argument(
            '--force-schema',
            action='store_true',
            help='Force recreation of schema tables'
        )
        parser.add_argument(
            '--retry-count',
            type=int,
            default=5,
            help='Number of times to retry operations (default: 5)'
        )
        parser.add_argument(
            '--migrate-data',
            action='store_true',
            help='Migrate data from populated replica to empty replicas'
        )
        parser.add_argument(
            '--check-data',
            action='store_true',
            help='Check data consistency across replicas'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.verbosity = options['verbosity']
        self.retry_count = options['retry_count']
        
        try:
            if options['check']:
                self._check_consistency()
            elif options['check_data']:
                self._check_data_consistency()
            elif options['fix']:
                self._fix_consistency()
            elif options['migrate_data']:
                self._migrate_data_across_replicas()
            elif options['force_schema']:
                self._force_schema_creation()
            else:
                self.stdout.write(
                    self.style.ERROR('Please specify --check, --check-data, --fix, --migrate-data, or --force-schema')
                )
                return

        except Exception as e:
            raise CommandError(f"Command failed: {str(e)}")

    def _check_consistency(self):
        """Check for ClickHouse consistency issues"""
        self.stdout.write(self.style.SUCCESS("🔍 Checking ClickHouse Consistency"))
        self.stdout.write("=" * 50)
        
        # Test multiple connections to see if we hit different replicas
        connection_results = []
        
        for i in range(self.retry_count):
            self.stdout.write(f"\n📡 Connection Test {i+1}/{self.retry_count}")
            
            try:
                client = get_clickhouse_connector()
                
                # Check basic connectivity
                version_result = client.query("SELECT version()")
                version = version_result.result_rows[0][0] if version_result.result_rows else "Unknown"
                
                # Check database
                db_result = client.query("SELECT currentDatabase()")
                current_db = db_result.result_rows[0][0] if db_result.result_rows else "Unknown"
                
                # Check for critical tables
                tables_result = client.query("SHOW TABLES")
                tables = [row[0] for row in tables_result.result_rows]
                
                has_migration_log = 'migration_log' in tables
                has_site_table_mapping = 'site_table_mapping' in tables
                
                result = {
                    'connection': i + 1,
                    'version': version,
                    'database': current_db,
                    'total_tables': len(tables),
                    'has_migration_log': has_migration_log,
                    'has_site_table_mapping': has_site_table_mapping,
                    'tables': tables[:10]  # First 10 tables
                }
                
                connection_results.append(result)
                
                self.stdout.write(f"  ✅ Version: {version}")
                self.stdout.write(f"  ✅ Database: {current_db}")
                self.stdout.write(f"  ✅ Tables: {len(tables)}")
                self.stdout.write(f"  {'✅' if has_migration_log else '❌'} migration_log table")
                self.stdout.write(f"  {'✅' if has_site_table_mapping else '❌'} site_table_mapping table")
                
                client.close()
                
            except Exception as e:
                self.stdout.write(f"  ❌ Connection failed: {str(e)}")
                connection_results.append({
                    'connection': i + 1,
                    'error': str(e)
                })
            
            # Small delay between connections
            time.sleep(1)
        
        # Analyze results
        self._analyze_consistency_results(connection_results)

    def _analyze_consistency_results(self, results: List[Dict]):
        """Analyze consistency check results"""
        self.stdout.write(f"\n📊 Analysis Results")
        self.stdout.write("=" * 30)
        
        successful_connections = [r for r in results if 'error' not in r]
        failed_connections = [r for r in results if 'error' in r]
        
        self.stdout.write(f"Successful connections: {len(successful_connections)}/{len(results)}")
        self.stdout.write(f"Failed connections: {len(failed_connections)}")
        
        if not successful_connections:
            self.stdout.write(self.style.ERROR("❌ No successful connections - ClickHouse is not accessible"))
            return
        
        # Check for inconsistencies
        versions = set(r['version'] for r in successful_connections)
        databases = set(r['database'] for r in successful_connections)
        migration_log_states = set(r['has_migration_log'] for r in successful_connections)
        site_mapping_states = set(r['has_site_table_mapping'] for r in successful_connections)
        table_counts = set(r['total_tables'] for r in successful_connections)
        
        issues_found = []
        
        if len(versions) > 1:
            issues_found.append(f"Multiple ClickHouse versions detected: {versions}")
        
        if len(databases) > 1:
            issues_found.append(f"Multiple databases detected: {databases}")
        
        if len(migration_log_states) > 1:
            issues_found.append("Inconsistent migration_log table presence")
        
        if len(site_mapping_states) > 1:
            issues_found.append("Inconsistent site_table_mapping table presence")
        
        if len(table_counts) > 1:
            issues_found.append(f"Inconsistent table counts: {table_counts}")
        
        if issues_found:
            self.stdout.write(self.style.ERROR("\n🚨 CONSISTENCY ISSUES DETECTED:"))
            for issue in issues_found:
                self.stdout.write(f"  ❌ {issue}")
            
            self.stdout.write(f"\n💡 This confirms you have multiple ClickHouse replicas in different states.")
            self.stdout.write(f"   Run with --fix to attempt automatic resolution.")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ No consistency issues detected"))
            self.stdout.write("   All connections returned consistent results.")

    def _fix_consistency(self):
        """Attempt to fix consistency issues"""
        self.stdout.write(self.style.SUCCESS("🔧 Fixing ClickHouse Consistency Issues"))
        self.stdout.write("=" * 50)
        
        # Strategy: Try to create missing tables on all replicas by retrying multiple times
        success_count = 0
        
        for attempt in range(self.retry_count):
            self.stdout.write(f"\n🔄 Fix Attempt {attempt + 1}/{self.retry_count}")
            
            try:
                success = self._ensure_schema_exists()
                if success:
                    success_count += 1
                    self.stdout.write(f"  ✅ Schema verification successful")
                else:
                    self.stdout.write(f"  ⚠️  Schema verification had issues")
                
            except Exception as e:
                self.stdout.write(f"  ❌ Fix attempt failed: {str(e)}")
            
            time.sleep(2)  # Wait between attempts
        
        self.stdout.write(f"\n📊 Fix Results: {success_count}/{self.retry_count} attempts successful")
        
        if success_count == self.retry_count:
            self.stdout.write(self.style.SUCCESS("✅ All fix attempts successful - consistency likely restored"))
        elif success_count > 0:
            self.stdout.write(self.style.WARNING("⚠️  Partial success - some replicas may still have issues"))
        else:
            self.stdout.write(self.style.ERROR("❌ All fix attempts failed - manual intervention required"))

    def _force_schema_creation(self):
        """Force recreation of schema tables"""
        self.stdout.write(self.style.SUCCESS("🔨 Force Schema Recreation"))
        self.stdout.write("=" * 40)
        
        database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
        
        # Drop and recreate tables multiple times to hit all replicas
        for attempt in range(self.retry_count):
            self.stdout.write(f"\n🔄 Schema Recreation Attempt {attempt + 1}/{self.retry_count}")
            
            try:
                client = get_clickhouse_connector()
                
                # Drop existing tables
                self.stdout.write("  🗑️  Dropping existing tables...")
                client.command(f"DROP TABLE IF EXISTS {database}.migration_log")
                client.command(f"DROP TABLE IF EXISTS {database}.site_table_mapping")
                
                # Create tables
                self.stdout.write("  🏗️  Creating tables...")
                self._create_migration_log_table(client, database)
                self._create_site_table_mapping_table(client, database)
                
                # Verify creation
                tables_result = client.query("SHOW TABLES")
                tables = [row[0] for row in tables_result.result_rows]
                
                has_migration_log = 'migration_log' in tables
                has_site_table_mapping = 'site_table_mapping' in tables
                
                if has_migration_log and has_site_table_mapping:
                    self.stdout.write("  ✅ Tables created successfully")
                else:
                    self.stdout.write("  ⚠️  Some tables missing after creation")
                
                client.close()
                
            except Exception as e:
                self.stdout.write(f"  ❌ Schema recreation failed: {str(e)}")
            
            time.sleep(1)
        
        self.stdout.write(self.style.SUCCESS("\n✅ Schema recreation completed"))

    def _check_data_consistency(self):
        """Check data consistency across replicas"""
        self.stdout.write(self.style.SUCCESS("📊 Checking Data Consistency Across Replicas"))
        self.stdout.write("=" * 60)
        
        # Check data in key tables across replicas
        key_tables = ['migration_log', 'site_table_mapping']
        connection_data = []
        
        for i in range(self.retry_count):
            self.stdout.write(f"\n📡 Data Check {i+1}/{self.retry_count}")
            
            try:
                client = get_clickhouse_connector()
                
                replica_data = {
                    'connection': i + 1,
                    'tables': {}
                }
                
                for table in key_tables:
                    try:
                        # Check if table exists and get row count
                        count_result = client.query(f"SELECT COUNT(*) FROM {table}")
                        row_count = count_result.result_rows[0][0] if count_result.result_rows else 0
                        
                        # Get sample data to verify content
                        sample_result = client.query(f"SELECT * FROM {table} LIMIT 3")
                        sample_rows = len(sample_result.result_rows)
                        
                        replica_data['tables'][table] = {
                            'row_count': row_count,
                            'sample_rows': sample_rows,
                            'has_data': row_count > 0
                        }
                        
                        self.stdout.write(f"  📋 {table}: {row_count} rows")
                        
                    except Exception as e:
                        replica_data['tables'][table] = {
                            'error': str(e),
                            'row_count': 0,
                            'has_data': False
                        }
                        self.stdout.write(f"  ❌ {table}: Error - {str(e)}")
                
                # Check a few data tables for more comprehensive analysis
                try:
                    tables_result = client.query("SHOW TABLES")
                    all_tables = [row[0] for row in tables_result.result_rows]
                    
                    # Find data tables (exclude system tables)
                    data_tables = [t for t in all_tables if not t.startswith('system') and t not in key_tables]
                    sample_data_tables = data_tables[:3]  # Check first 3 data tables
                    
                    total_data_rows = 0
                    for table in sample_data_tables:
                        try:
                            count_result = client.query(f"SELECT COUNT(*) FROM `{table}`")
                            table_rows = count_result.result_rows[0][0] if count_result.result_rows else 0
                            total_data_rows += table_rows
                        except:
                            pass
                    
                    replica_data['total_data_rows'] = total_data_rows
                    replica_data['sample_tables_checked'] = len(sample_data_tables)
                    
                    self.stdout.write(f"  📊 Sample data tables ({len(sample_data_tables)}): {total_data_rows} total rows")
                    
                except Exception as e:
                    replica_data['total_data_rows'] = 0
                    self.stdout.write(f"  ⚠️  Could not check data tables: {str(e)}")
                
                connection_data.append(replica_data)
                client.close()
                
            except Exception as e:
                self.stdout.write(f"  ❌ Connection failed: {str(e)}")
                connection_data.append({
                    'connection': i + 1,
                    'error': str(e)
                })
            
            time.sleep(1)
        
        # Analyze data consistency
        self._analyze_data_consistency(connection_data)

    def _analyze_data_consistency(self, data_results: List[Dict]):
        """Analyze data consistency results"""
        self.stdout.write(f"\n📈 Data Consistency Analysis")
        self.stdout.write("=" * 40)
        
        successful_connections = [r for r in data_results if 'error' not in r]
        
        if not successful_connections:
            self.stdout.write(self.style.ERROR("❌ No successful connections for data analysis"))
            return
        
        # Analyze migration_log consistency
        migration_log_counts = []
        site_mapping_counts = []
        total_data_counts = []
        
        for conn in successful_connections:
            if 'migration_log' in conn['tables']:
                migration_log_counts.append(conn['tables']['migration_log']['row_count'])
            if 'site_table_mapping' in conn['tables']:
                site_mapping_counts.append(conn['tables']['site_table_mapping']['row_count'])
            if 'total_data_rows' in conn:
                total_data_counts.append(conn['total_data_rows'])
        
        # Check for inconsistencies
        issues = []
        
        if len(set(migration_log_counts)) > 1:
            issues.append(f"migration_log row counts vary: {set(migration_log_counts)}")
        
        if len(set(site_mapping_counts)) > 1:
            issues.append(f"site_table_mapping row counts vary: {set(site_mapping_counts)}")
        
        if len(set(total_data_counts)) > 1:
            issues.append(f"Data table row counts vary: {set(total_data_counts)}")
        
        # Summary
        self.stdout.write(f"Migration log rows: {migration_log_counts}")
        self.stdout.write(f"Site mapping rows: {site_mapping_counts}")
        self.stdout.write(f"Sample data rows: {total_data_counts}")
        
        if issues:
            self.stdout.write(self.style.ERROR("\n🚨 DATA INCONSISTENCY DETECTED:"))
            for issue in issues:
                self.stdout.write(f"  ❌ {issue}")
            
            # Identify which replica has the most data
            if total_data_counts:
                max_data = max(total_data_counts)
                if max_data > 0:
                    self.stdout.write(f"\n💡 Replica with most data has {max_data} rows")
                    self.stdout.write("   Run with --migrate-data to sync data across replicas")
                else:
                    self.stdout.write("\n⚠️  All replicas appear to be empty")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Data appears consistent across replicas"))

    def _migrate_data_across_replicas(self):
        """Migrate data from populated replica to empty replicas"""
        self.stdout.write(self.style.SUCCESS("🔄 Migrating Data Across Replicas"))
        self.stdout.write("=" * 50)
        
        # First, identify which replica has the most data
        source_replica_data = self._find_source_replica()
        
        if not source_replica_data:
            self.stdout.write(self.style.ERROR("❌ Could not identify a source replica with data"))
            return
        
        self.stdout.write(f"📍 Source replica identified with {source_replica_data['total_rows']} rows")
        
        # Get the data from source replica
        source_data = self._extract_data_from_source()
        
        if not source_data:
            self.stdout.write(self.style.ERROR("❌ Could not extract data from source replica"))
            return
        
        # Migrate to other replicas
        success_count = 0
        for attempt in range(self.retry_count):
            self.stdout.write(f"\n🔄 Migration Attempt {attempt + 1}/{self.retry_count}")
            
            try:
                success = self._migrate_to_replica(source_data)
                if success:
                    success_count += 1
                    self.stdout.write("  ✅ Data migration successful")
                else:
                    self.stdout.write("  ⚠️  Data migration had issues")
                    
            except Exception as e:
                self.stdout.write(f"  ❌ Migration failed: {str(e)}")
            
            time.sleep(2)
        
        self.stdout.write(f"\n📊 Migration Results: {success_count}/{self.retry_count} attempts successful")
        
        if success_count >= self.retry_count // 2:
            self.stdout.write(self.style.SUCCESS("✅ Data migration completed successfully"))
            self.stdout.write("   Run --check-data to verify consistency")
        else:
            self.stdout.write(self.style.ERROR("❌ Data migration had issues - manual intervention may be required"))

    def _find_source_replica(self) -> Optional[Dict]:
        """Find the replica with the most data to use as source"""
        max_rows = 0
        source_replica = None
        
        for attempt in range(self.retry_count):
            try:
                client = get_clickhouse_connector()
                
                # Count rows in key tables
                migration_count = 0
                mapping_count = 0
                
                try:
                    result = client.query("SELECT COUNT(*) FROM migration_log")
                    migration_count = result.result_rows[0][0] if result.result_rows else 0
                except:
                    pass
                
                try:
                    result = client.query("SELECT COUNT(*) FROM site_table_mapping")
                    mapping_count = result.result_rows[0][0] if result.result_rows else 0
                except:
                    pass
                
                total_rows = migration_count + mapping_count
                
                if total_rows > max_rows:
                    max_rows = total_rows
                    source_replica = {
                        'migration_rows': migration_count,
                        'mapping_rows': mapping_count,
                        'total_rows': total_rows
                    }
                
                client.close()
                
            except Exception as e:
                logger.error(f"Error checking replica {attempt + 1}: {str(e)}")
            
            time.sleep(0.5)
        
        return source_replica

    def _extract_data_from_source(self) -> Optional[Dict]:
        """Extract data from the source replica"""
        try:
            client = get_clickhouse_connector()
            
            # Extract migration_log data
            migration_data = []
            try:
                result = client.query("SELECT * FROM migration_log")
                migration_data = result.result_rows
            except Exception as e:
                logger.warning(f"Could not extract migration_log: {str(e)}")
            
            # Extract site_table_mapping data
            mapping_data = []
            try:
                result = client.query("SELECT * FROM site_table_mapping")
                mapping_data = result.result_rows
            except Exception as e:
                logger.warning(f"Could not extract site_table_mapping: {str(e)}")
            
            client.close()
            
            return {
                'migration_log': migration_data,
                'site_table_mapping': mapping_data
            }
            
        except Exception as e:
            logger.error(f"Failed to extract source data: {str(e)}")
            return None

    def _migrate_to_replica(self, source_data: Dict) -> bool:
        """Migrate data to a replica"""
        try:
            client = get_clickhouse_connector()
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            # Clear existing data first
            try:
                client.command(f"TRUNCATE TABLE {database}.migration_log")
                client.command(f"TRUNCATE TABLE {database}.site_table_mapping")
            except Exception as e:
                logger.warning(f"Could not truncate tables: {str(e)}")
            
            # Insert migration_log data
            if source_data.get('migration_log'):
                for row in source_data['migration_log']:
                    try:
                        insert_sql = f"""
                        INSERT INTO {database}.migration_log VALUES (
                            '{row[0]}', '{row[1]}', '{row[2]}', {row[3]}, {row[4]}, 
                            {row[5]}, '{row[6]}', '{row[7]}', '{row[8]}', '{row[9]}'
                        )
                        """
                        client.command(insert_sql)
                    except Exception as e:
                        logger.warning(f"Failed to insert migration_log row: {str(e)}")
            
            # Insert site_table_mapping data
            if source_data.get('site_table_mapping'):
                for row in source_data['site_table_mapping']:
                    try:
                        insert_sql = f"""
                        INSERT INTO {database}.site_table_mapping VALUES (
                            '{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', 
                            '{row[4]}', '{row[5]}', {row[6]}, '{row[7]}'
                        )
                        """
                        client.command(insert_sql)
                    except Exception as e:
                        logger.warning(f"Failed to insert site_table_mapping row: {str(e)}")
            
            client.close()
            return True
            
        except Exception as e:
            logger.error(f"Migration to replica failed: {str(e)}")
            return False

    def _ensure_schema_exists(self) -> bool:
        """Ensure required schema tables exist"""
        try:
            client = get_clickhouse_connector()
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            
            # Check existing tables
            tables_result = client.query("SHOW TABLES")
            tables = [row[0] for row in tables_result.result_rows]
            
            # Create missing tables
            if 'migration_log' not in tables:
                self._create_migration_log_table(client, database)
            
            if 'site_table_mapping' not in tables:
                self._create_site_table_mapping_table(client, database)
            
            client.close()
            return True
            
        except Exception as e:
            logger.error(f"Schema creation failed: {str(e)}")
            return False

    def _create_migration_log_table(self, client, database: str):
        """Create migration_log table"""
        create_sql = f"""
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
        ORDER BY started_at
        SETTINGS index_granularity = 8192
        """
        client.command(create_sql)

    def _create_site_table_mapping_table(self, client, database: str):
        """Create site_table_mapping table"""
        create_sql = f"""
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
        ORDER BY (site_name, table_name)
        SETTINGS index_granularity = 8192
        """
        client.command(create_sql)
