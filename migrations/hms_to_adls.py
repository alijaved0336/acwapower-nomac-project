"""
Ready-to-Run Migration Script: Databricks HMS to Azure Data Lake Storage
Modified for Site-Based Directory Structure: swro/tables/gold/[site_name]/

Prerequisites:
pip install databricks-sql-connector azure-storage-file-datalake azure-identity pandas pyarrow python-dotenv

Environment Variables Required:
- AZURE_STORAGE_ACCOUNT
- AZURE_STORAGE_KEY (or use Service Principal credentials)
- AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID (alternative to storage key)
- SERVER_HOSTNAME
- HTTP_PATH  
- ACCESS_TOKEN
"""

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from databricks import sql as databricks_sql
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import ClientSecretCredential
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SiteMigrator:
    def __init__(self, site_name: Optional[str] = None):
        """Initialize migrator with site-specific configuration"""
        # Static configuration
        self.catalog = "hive_metastore"
        self.schema = "nomac_mpc_swro_gold_j3a"
        self.container = "swro"
        self.base_directory = "tables/gold"
        self.site_name = site_name
        self.target_directory = f"{self.base_directory}/{site_name}" if site_name else None
        
        # Connections
        self.databricks_connection = None
        self.adls_client = None
        self.storage_account = None
        
        # Get credentials from environment
        self.storage_account = os.getenv('AZURE_STORAGE_ACCOUNT')
        self.storage_key = os.getenv('AZURE_STORAGE_KEY')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.server_hostname = os.getenv('SERVER_HOSTNAME')
        self.http_path = os.getenv('HTTP_PATH')
        self.access_token = os.getenv('ACCESS_TOKEN')

    def set_site(self, site_name: str):
        """Set the target site for migration"""
        self.site_name = site_name
        self.target_directory = f"{self.base_directory}/{site_name}"
        logger.info(f"🎯 Target site set to: {site_name}")
        logger.info(f"📁 Target directory: {self.target_directory}")

    def setup_databricks_connection(self):
        """Setup Databricks connection using environment variables"""
        try:
            if not all([self.server_hostname, self.http_path, self.access_token]):
                logger.error("❌ Missing Databricks credentials in environment variables!")
                logger.error("Required: SERVER_HOSTNAME, HTTP_PATH, ACCESS_TOKEN")
                return False
            
            logger.info("🔐 Connecting to Databricks...")
            
            self.databricks_connection = databricks_sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token
            )
            
            # Test connection
            cursor = self.databricks_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            cursor.close()
            
            logger.info(f"✅ Databricks connected: {self.server_hostname}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Databricks connection failed: {str(e)}")
            return False

    def setup_adls_connection(self):
        """Setup ADLS connection using environment variables (tries multiple auth methods)"""
        if not self.storage_account:
            logger.error("❌ Missing AZURE_STORAGE_ACCOUNT environment variable!")
            return False
        
        # Method 1: Try Account Key first (simpler)
        if self.storage_key:
            return self._setup_adls_account_key()
        
        # Method 2: Try Service Principal
        elif all([self.client_id, self.client_secret, self.tenant_id]):
            return self._setup_adls_service_principal()
        
        else:
            logger.error("❌ Missing Azure Storage credentials!")
            logger.error("Provide either: AZURE_STORAGE_KEY")
            logger.error("Or all of: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
            return False

    def _setup_adls_account_key(self):
        """Setup ADLS using account key"""
        try:
            logger.info("🔐 Connecting to ADLS using Account Key...")
            
            account_url = f"https://{self.storage_account}.dfs.core.windows.net"
            self.adls_client = DataLakeServiceClient(
                account_url=account_url,
                credential=self.storage_key
            )
            
            # Test connection
            file_system_client = self.adls_client.get_file_system_client(self.container)
            file_system_client.get_file_system_properties()
            
            logger.info(f"✅ ADLS connected using Account Key: {self.storage_account}")
            return True
            
        except Exception as e:
            logger.error(f"❌ ADLS Account Key authentication failed: {str(e)}")
            return False

    def _setup_adls_service_principal(self):
        """Setup ADLS using Service Principal"""
        try:
            logger.info("🔐 Connecting to ADLS using Service Principal...")
            
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            account_url = f"https://{self.storage_account}.dfs.core.windows.net"
            self.adls_client = DataLakeServiceClient(
                account_url=account_url,
                credential=credential
            )
            
            # Test connection
            file_system_client = self.adls_client.get_file_system_client(self.container)
            file_system_client.get_file_system_properties()
            
            logger.info(f"✅ ADLS connected using Service Principal: {self.storage_account}")
            return True
            
        except Exception as e:
            logger.error(f"❌ ADLS Service Principal authentication failed: {str(e)}")
            return False

    def connect_all(self):
        """Setup all connections"""
        logger.info("🚀 Setting up connections...")
        
        # Setup Databricks
        if not self.setup_databricks_connection():
            return False
        
        # Setup ADLS
        if not self.setup_adls_connection():
            return False
        
        logger.info("🎉 All connections established successfully!")
        return True

    def get_all_tables(self) -> List[str]:
        """Get all table names from the schema"""
        try:
            cursor = self.databricks_connection.cursor()
            query = f"SHOW TABLES IN {self.catalog}.{self.schema}"
            cursor.execute(query)
            
            tables = [row[1] for row in cursor.fetchall()]
            cursor.close()
            
            logger.info(f"📊 Found {len(tables)} tables: {tables}")
            return tables
            
        except Exception as e:
            logger.error(f"❌ Error getting tables: {str(e)}")
            return []

    def list_available_sites(self) -> List[str]:
        """List all available sites under swro/tables/gold/"""
        try:
            logger.info("📋 Listing available sites...")
            
            file_system_client = self.adls_client.get_file_system_client(self.container)
            
            sites = []
            
            try:
                # Check if base directory exists
                base_dir_client = file_system_client.get_directory_client(self.base_directory)
                paths = base_dir_client.get_paths()
                
                for path in paths:
                    if path.is_directory:
                        site_name = path.name.split('/')[-1]  # Get the last part of the path
                        if site_name != self.base_directory.split('/')[-1]:  # Skip the parent directory itself
                            sites.append(site_name)
                
                if sites:
                    logger.info(f"🏢 Found {len(sites)} available sites:")
                    for i, site in enumerate(sites, 1):
                        logger.info(f"   {i}. {site}")
                else:
                    logger.info("📁 No sites found under tables/gold/")
                
                return sorted(sites)
                
            except Exception as e:
                if "PathNotFound" in str(e):
                    logger.info(f"📁 Directory {self.base_directory} doesn't exist yet")
                    return []
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Error listing sites: {str(e)}")
            return []

    def list_site_tables(self, site_name: str) -> List[str]:
        """List all tables that have been migrated to a specific site"""
        try:
            logger.info(f"📋 Listing migrated tables for site: {site_name}")
            
            site_directory = f"{self.base_directory}/{site_name}"
            file_system_client = self.adls_client.get_file_system_client(self.container)
            
            migrated_tables = []
            
            try:
                # List directories in the site directory (each directory is a table)
                directory_client = file_system_client.get_directory_client(site_directory)
                paths = directory_client.get_paths()
                
                for path in paths:
                    if path.is_directory:
                        # Extract table name from directory name
                        table_name = path.name.split('/')[-1]
                        if table_name != site_name:  # Skip the site directory itself
                            
                            # Check if parquet file exists in this table directory
                            parquet_file_path = f"{path.name}/{table_name}.parquet"
                            
                            try:
                                file_client = file_system_client.get_file_client(parquet_file_path)
                                properties = file_client.get_file_properties()
                                
                                migrated_tables.append({
                                    'table_name': table_name,
                                    'file_size': properties.size,
                                    'last_modified': properties.last_modified,
                                    'table_directory': path.name,
                                    'parquet_location': f"abfss://{self.container}@{self.storage_account}.dfs.core.windows.net/{parquet_file_path}"
                                })
                                
                            except Exception:
                                # Directory exists but no parquet file, or file access issue
                                logger.warning(f"⚠️  Table directory exists but parquet file missing: {table_name}")
                
                if migrated_tables:
                    logger.info(f"📊 Found {len(migrated_tables)} migrated tables in {site_name}:")
                    for table in migrated_tables:
                        logger.info(f"   - {table['table_name']}: {table['file_size']:,} bytes (Modified: {table['last_modified']})")
                        logger.info(f"     📁 Directory: {table['table_directory']}/")
                else:
                    logger.info(f"📁 No tables found in site: {site_name}")
                
                return [table['table_name'] for table in migrated_tables]
                
            except Exception as e:
                if "PathNotFound" in str(e):
                    logger.info(f"📁 Site directory {site_name} doesn't exist yet")
                    return []
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Error listing tables for site {site_name}: {str(e)}")
            return []

    def ensure_directory_exists(self, directory_path: str):
        """
        Check if directory exists in ADLS, create if it doesn't
        
        Args:
            directory_path (str): Directory path to check/create
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            file_system_client = self.adls_client.get_file_system_client(self.container)
            directory_client = file_system_client.get_directory_client(directory_path)
            
            # Check if directory exists
            try:
                directory_client.get_directory_properties()
                logger.info(f"📁 Directory exists: {directory_path}")
                return True
                
            except Exception:
                # Directory doesn't exist, create it
                logger.info(f"📁 Creating directory: {directory_path}")
                directory_client.create_directory()
                logger.info(f"✅ Directory created: {directory_path}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to ensure directory exists {directory_path}: {str(e)}")
            return False

    def migrate_table(self, table_name: str) -> Dict:
        """Migrate a single table from Databricks to ADLS"""
        if not self.target_directory:
            raise Exception("No site selected! Please set site name first.")
        
        try:
            logger.info(f"📦 Starting migration: {table_name} → {self.site_name}")
            
            # Step 1: Ensure target directory structure exists
            # Create site directory: swro/tables/gold/site_name/
            if not self.ensure_directory_exists(self.target_directory):
                raise Exception(f"Failed to create site directory: {self.target_directory}")
            
            # Create table directory: swro/tables/gold/site_name/table_name/
            table_directory = f"{self.target_directory}/{table_name}"
            if not self.ensure_directory_exists(table_directory):
                raise Exception(f"Failed to create table directory: {table_directory}")
            
            # Step 2: Extract data from Databricks
            source_table = f"{self.catalog}.{self.schema}.{table_name}"
            
            cursor = self.databricks_connection.cursor()
            cursor.execute(f"SELECT * FROM {source_table}")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch data in chunks
            chunk_size = 10000
            all_data = []
            
            while True:
                chunk = cursor.fetchmany(chunk_size)
                if not chunk:
                    break
                all_data.extend(chunk)
                
                # Log progress for large tables
                if len(all_data) % 50000 == 0:
                    logger.info(f"   Fetched {len(all_data):,} rows...")
            
            cursor.close()
            
            if not all_data:
                logger.warning(f"⚠️  Table {table_name} is empty")
                # Still create empty parquet file for consistency
                df = pd.DataFrame(columns=columns)
                row_count = 0
            else:
                # Step 3: Convert to DataFrame
                df = pd.DataFrame(all_data, columns=columns)
                row_count = len(df)
                logger.info(f"   Extracted {row_count:,} rows")
            
            # Step 4: Upload to ADLS as Parquet (inside table directory)
            # File path: swro/tables/gold/site_name/table_name/table_name.parquet
            file_name = f"{table_directory}/{table_name}.parquet"
            
            # Get file system client
            file_system_client = self.adls_client.get_file_system_client(self.container)
            
            # Convert DataFrame to Parquet
            table = pa.Table.from_pandas(df)
            parquet_buffer = pa.BufferOutputStream()
            pq.write_table(table, parquet_buffer, compression='snappy')
            parquet_data = parquet_buffer.getvalue().to_pybytes()
            
            # Check if parquet file already exists
            file_client = file_system_client.get_file_client(file_name)
            
            try:
                file_client.get_file_properties()
                logger.info(f"   📄 File exists, overwriting: {table_name}.parquet")
                file_client.upload_data(parquet_data, overwrite=True)
            except Exception:
                logger.info(f"   📄 Creating new file: {table_name}.parquet")
                file_client.create_file()
                file_client.upload_data(parquet_data, overwrite=True)
            
            target_url = f"abfss://{self.container}@{self.storage_account}.dfs.core.windows.net/{file_name}"
            
            logger.info(f"✅ SUCCESS: {table_name} ({row_count:,} rows)")
            logger.info(f"   📍 Location: {target_url}")
            logger.info(f"   📁 Directory: {table_directory}/")
            
            return {
                "table": table_name,
                "status": "success",
                "rows": row_count,
                "target_path": target_url,
                "table_directory": table_directory,
                "site": self.site_name
            }
            
        except Exception as e:
            logger.error(f"❌ FAILED: {table_name} - {str(e)}")
            return {
                "table": table_name,
                "status": "failed", 
                "error": str(e),
                "rows": 0,
                "site": self.site_name
            }

    def migrate_tables(self, table_names: List[str]) -> List[Dict]:
        """Migrate multiple tables to the selected site"""
        if not self.site_name:
            logger.error("❌ No site selected! Please set site name first.")
            return []
        
        results = []
        total_tables = len(table_names)
        
        logger.info(f"🚀 Starting batch migration of {total_tables} tables to site: {self.site_name}")
        logger.info(f"Source: {self.catalog}.{self.schema}")
        logger.info(f"Target: abfss://{self.container}@{self.storage_account}.dfs.core.windows.net/{self.target_directory}/")
        logger.info("="*80)
        
        for i, table_name in enumerate(table_names, 1):
            logger.info(f"[{i}/{total_tables}] Processing: {table_name}")
            result = self.migrate_table(table_name)
            results.append(result)
            logger.info("")  # Empty line for readability
        
        # Print summary
        self._print_migration_summary(results)
        return results

    def _print_migration_summary(self, results: List[Dict]):
        """Print migration summary"""
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "failed"]
        total_rows = sum(r.get("rows", 0) for r in successful)
        
        logger.info("="*80)
        logger.info("📊 MIGRATION SUMMARY")
        logger.info("="*80)
        logger.info(f"Target site: {self.site_name}")
        logger.info(f"Total tables processed: {len(results)}")
        logger.info(f"✅ Successful: {len(successful)}")
        logger.info(f"❌ Failed: {len(failed)}")
        logger.info(f"📈 Total rows migrated: {total_rows:,}")
        logger.info(f"🎯 Target location: abfss://{self.container}@{self.storage_account}.dfs.core.windows.net/{self.target_directory}/")
        logger.info(f"📁 Directory structure: {self.target_directory}/[table_name]/[table_name].parquet")
        
        if successful:
            logger.info("\n✅ Successful migrations:")
            for success in successful:
                table_dir = success.get('table_directory', f"{self.target_directory}/{success['table']}")
                logger.info(f"   - {success['table']}: {success['rows']:,} rows")
                logger.info(f"     📁 Directory: {table_dir}/")
        
        if failed:
            logger.info("\n❌ Failed migrations:")
            for failure in failed:
                logger.info(f"   - {failure['table']}: {failure['error']}")

    def verify_table(self, table_name: str):
        """Verify a migrated table exists in ADLS for the current site"""
        if not self.target_directory:
            logger.error("❌ No site selected!")
            return False
        
        try:
            # File path: swro/tables/gold/site_name/table_name/table_name.parquet
            file_name = f"{self.target_directory}/{table_name}/{table_name}.parquet"
            file_system_client = self.adls_client.get_file_system_client(self.container)
            file_client = file_system_client.get_file_client(file_name)
            
            properties = file_client.get_file_properties()
            file_size = properties.size
            
            logger.info(f"✅ Verified {table_name} in {self.site_name}: {file_size:,} bytes")
            logger.info(f"   📁 Directory: {self.target_directory}/{table_name}/")
            logger.info(f"   📍 Location: abfss://{self.container}@{self.storage_account}.dfs.core.windows.net/{file_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cannot verify {table_name} in {self.site_name}: {str(e)}")
            return False

    def close_connections(self):
        """Close all connections"""
        if self.databricks_connection:
            self.databricks_connection.close()
            logger.info("🔐 Databricks connection closed")

# =============================================================================
# SITE-BASED MIGRATION FUNCTIONS
# =============================================================================

def list_all_sites():
    """List all available sites under swro/tables/gold/"""
    migrator = SiteMigrator()
    
    if not migrator.connect_all():
        logger.error("❌ Connection setup failed!")
        return None
    
    try:
        sites = migrator.list_available_sites()
        return sites
    finally:
        migrator.close_connections()

def list_site_tables(site_name: str):
    """List tables in a specific site"""
    migrator = SiteMigrator()
    
    if not migrator.connect_all():
        logger.error("❌ Connection setup failed!")
        return None
    
    try:
        tables = migrator.list_site_tables(site_name)
        return tables
    finally:
        migrator.close_connections()

def migrate_to_site(site_name: str, table_names: List[str]):
    """Migrate specific tables to a site"""
    migrator = SiteMigrator()
    
    if not migrator.connect_all():
        logger.error("❌ Connection setup failed!")
        return None
    
    try:
        migrator.set_site(site_name)
        results = migrator.migrate_tables(table_names)
        return results
    finally:
        migrator.close_connections()

def migrate_all_to_site(site_name: str):
    """Migrate all available tables to a site"""
    migrator = SiteMigrator()
    
    if not migrator.connect_all():
        logger.error("❌ Connection setup failed!")
        return None
    
    try:
        # Get all table names from Databricks
        all_tables = migrator.get_all_tables()
        
        if not all_tables:
            logger.warning("⚠️  No tables found to migrate")
            return []
        
        # Set target site and migrate
        migrator.set_site(site_name)
        results = migrator.migrate_tables(all_tables)
        return results
        
    finally:
        migrator.close_connections()

def verify_site_tables(site_name: str, table_names: List[str]):
    """Verify multiple tables in a specific site"""
    migrator = SiteMigrator()
    
    if not migrator.connect_all():
        logger.error("❌ Connection setup failed!")
        return None
    
    try:
        migrator.set_site(site_name)
        
        results = []
        for table_name in table_names:
            success = migrator.verify_table(table_name)
            results.append({"table": table_name, "verified": success})
        
        successful_verifications = [r for r in results if r["verified"]]
        failed_verifications = [r for r in results if not r["verified"]]
        
        logger.info(f"\n📊 Verification Summary for {site_name}:")
        logger.info(f"✅ Verified: {len(successful_verifications)}")
        logger.info(f"❌ Failed: {len(failed_verifications)}")
        
        if failed_verifications:
            logger.info("Failed verifications:")
            for fail in failed_verifications:
                logger.info(f"   - {fail['table']}")
        
        return results
        
    finally:
        migrator.close_connections()

def show_directory_structure_example():
    """Show example of the directory structure that will be created"""
    print("\n📁 Directory Structure Example:")
    print("=" * 50)
    print("swro/")
    print("└── tables/")
    print("    └── gold/")
    print("        ├── site1/")
    print("        │   ├── customers/")
    print("        │   │   └── customers.parquet")
    print("        │   ├── orders/")
    print("        │   │   └── orders.parquet")
    print("        │   └── products/")
    print("        │       └── products.parquet")
    print("        ├── site2/")
    print("        │   ├── sales/")
    print("        │   │   └── sales.parquet")
    print("        │   └── inventory/")
    print("        │       └── inventory.parquet")
    print("        └── site3/")
    print("            └── transactions/")
    print("                └── transactions.parquet")
    print("\n✅ Each table gets its own directory under the site!")
    print("✅ Site name is entered by user")
    print("✅ Table names come from Databricks HMS")

def check_environment():
    """Check if all required environment variables are set"""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = [
        'AZURE_STORAGE_ACCOUNT',
        'SERVER_HOSTNAME', 
        'HTTP_PATH',
        'ACCESS_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    # Check for at least one Azure auth method
    has_storage_key = bool(os.getenv('AZURE_STORAGE_KEY'))
    has_service_principal = all([
        os.getenv('AZURE_CLIENT_ID'),
        os.getenv('AZURE_CLIENT_SECRET'), 
        os.getenv('AZURE_TENANT_ID')
    ])
    
    if not (has_storage_key or has_service_principal):
        logger.error("❌ Missing Azure authentication credentials!")
        logger.error("Provide either: AZURE_STORAGE_KEY")
        logger.error("Or all of: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
        return False
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✅ All required environment variables are set")
    
    # Show what we found
    logger.info(f"Storage Account: {os.getenv('AZURE_STORAGE_ACCOUNT')}")
    logger.info(f"Databricks Host: {os.getenv('SERVER_HOSTNAME')}")
    logger.info(f"Auth Method: {'Storage Key' if has_storage_key else 'Service Principal'}")
    
    return True

def interactive_site_selection():
    """Interactive function to help user select a site"""
    sites = list_all_sites()
    
    if not sites:
        print("❌ No sites found or connection failed!")
        return None
    
    print(f"\n🏢 Available Sites ({len(sites)} found):")
    for i, site in enumerate(sites, 1):
        print(f"   {i}. {site}")
    
    while True:
        try:
            choice = input(f"\nSelect site (1-{len(sites)}) or enter site name: ").strip()
            
            # Check if it's a number
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(sites):
                    return sites[index]
                else:
                    print(f"❌ Invalid selection. Please choose 1-{len(sites)}")
                    continue
            
            # Check if it's a site name
            if choice in sites:
                return choice
            
            # Check if it's a new site name (allow creating new sites)
            if choice and choice.replace('_', '').replace('-', '').isalnum():
                create_new = input(f"Site '{choice}' doesn't exist. Create it? (y/N): ").strip().lower()
                if create_new == 'y':
                    return choice
            
            print("❌ Invalid input. Please try again.")
            
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return None

def interactive_table_selection():
    """Interactive function to help user select tables"""
    migrator = SiteMigrator()
    
    if not migrator.connect_all():
        print("❌ Connection setup failed!")
        return None
    
    try:
        all_tables = migrator.get_all_tables()
        
        if not all_tables:
            print("❌ No tables found in Databricks!")
            return None
        
        print(f"\n📊 Available Tables ({len(all_tables)} found):")
        for i, table in enumerate(all_tables, 1):
            print(f"   {i}. {table}")
        
        print(f"\nTable Selection Options:")
        print(f"1. Enter table numbers (e.g., 1,3,5)")
        print(f"2. Enter table names (e.g., table1,table2)")
        print(f"3. Type 'all' for all tables")
        
        choice = input("Enter your selection: ").strip()
        
        if choice.lower() == 'all':
            return all_tables
        
        # Parse selection
        selected_tables = []
        
        # Check if it contains numbers
        if any(c.isdigit() for c in choice):
            # Assume it's table numbers
            numbers = [x.strip() for x in choice.split(',')]
            for num in numbers:
                try:
                    index = int(num) - 1
                    if 0 <= index < len(all_tables):
                        selected_tables.append(all_tables[index])
                    else:
                        print(f"⚠️  Skipping invalid table number: {num}")
                except ValueError:
                    print(f"⚠️  Skipping invalid input: {num}")
        else:
            # Assume it's table names
            table_names = [x.strip() for x in choice.split(',')]
            for table_name in table_names:
                if table_name in all_tables:
                    selected_tables.append(table_name)
                else:
                    print(f"⚠️  Table not found, skipping: {table_name}")
        
        if selected_tables:
            print(f"\n✅ Selected {len(selected_tables)} tables:")
            for table in selected_tables:
                print(f"   - {table}")
            return selected_tables
        else:
            print("❌ No valid tables selected!")
            return None
            
    finally:
        migrator.close_connections()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Site-Based Migration Script")
    print("Directory Structure: swro/tables/gold/[site_name]/")
    print("=" * 60)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed! Please set the required environment variables.")
        exit(1)
    
    print("\nChoose migration option:")
    print("1. List all available sites")
    print("2. List tables in a specific site")
    print("3. Migrate specific tables to a site")  
    print("4. Migrate ALL tables to a site")
    print("5. Verify tables in a site")
    print("6. Interactive migration (with site & table selection)")
    print("7. Just test connections")
    print("8. Show directory structure example")
    
    choice = input("\nEnter your choice (1-8): ").strip()
    
    if choice == "1":
        print("\n📋 Listing all available sites...")
        sites = list_all_sites()
        if sites:
            print(f"\nFound {len(sites)} sites under swro/tables/gold/")
        
    elif choice == "2":
        site_name = input("Enter site name: ").strip()
        if site_name:
            print(f"\n📋 Listing tables in site: {site_name}")
            tables = list_site_tables(site_name)
            if tables:
                print(f"Found {len(tables)} tables in {site_name}")
    
    elif choice == "3":
        site_name = input("Enter site name: ").strip()
        tables_input = input("Enter table names (comma-separated): ").strip()
        if site_name and tables_input:
            table_names = [t.strip() for t in tables_input.split(",")]
            print(f"\n📦 Migrating {len(table_names)} tables to site: {site_name}")
            results = migrate_to_site(site_name, table_names)
    
    elif choice == "4":
        site_name = input("Enter site name: ").strip()
        if site_name:
            print(f"\n📦 Migrating ALL tables to site: {site_name}")
            confirm = input("This will migrate all tables. Continue? (y/N): ").strip().lower()
            if confirm == 'y':
                results = migrate_all_to_site(site_name)
            else:
                print("Migration cancelled.")
    
    elif choice == "5":
        site_name = input("Enter site name: ").strip()
        tables_input = input("Enter table names to verify (comma-separated): ").strip()
        if site_name and tables_input:
            table_names = [t.strip() for t in tables_input.split(",")]
            print(f"\n🔍 Verifying {len(table_names)} tables in site: {site_name}")
            results = verify_site_tables(site_name, table_names)
    
    elif choice == "6":
        print("\n🎯 Interactive Migration")
        print("Step 1: Select target site")
        site_name = interactive_site_selection()
        
        if site_name:
            print(f"\n✅ Selected site: {site_name}")
            print("\nStep 2: Select tables to migrate")
            table_names = interactive_table_selection()
            
            if table_names:
                print(f"\n📦 Ready to migrate {len(table_names)} tables to {site_name}")
                confirm = input("Proceed with migration? (y/N): ").strip().lower()
                if confirm == 'y':
                    results = migrate_to_site(site_name, table_names)
                else:
                    print("Migration cancelled.")
            else:
                print("❌ No tables selected.")
        else:
            print("❌ No site selected.")
    
    elif choice == "7":
        print("\n🔍 Testing connections...")
        migrator = SiteMigrator()
        if migrator.connect_all():
            print("✅ Connections working!")
            sites = migrator.list_available_sites()
            tables = migrator.get_all_tables()
            print(f"Found {len(sites)} sites and {len(tables)} tables available.")
        migrator.close_connections()
    
    else:
        print("Invalid choice!")
    
    print("\n✨ Done!")

# =============================================================================
# QUICK EXAMPLES FOR DIRECT USE
# =============================================================================

# Example 1: Migrate specific tables to a site
# Creates: swro/tables/gold/site_name/table1/table1.parquet, etc.
# results = migrate_to_site("site_name", ["table1", "table2", "table3"])

# Example 2: Migrate all tables to a site
# Creates: swro/tables/gold/site_name/[table_name]/[table_name].parquet for all tables
# results = migrate_all_to_site("site_name")

# Example 3: List tables in a site
# Lists all table directories under swro/tables/gold/site_name/
# tables = list_site_tables("site_name")

# Example 4: List all available sites
# Lists all directories under swro/tables/gold/
# sites = list_all_sites()

# Example 5: Verify specific tables in a site
# Checks if swro/tables/gold/site_name/[table_name]/[table_name].parquet exists
# results = verify_site_tables("site_name", ["table1", "table2"])
