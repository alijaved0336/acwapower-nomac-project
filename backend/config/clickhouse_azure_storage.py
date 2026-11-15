"""
ClickHouse Azure Storage Configuration
Configures ClickHouse to use Azure Storage for data migration and storage
"""
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ClickHouseAzureStorageConfig:
    """Configuration for ClickHouse Azure Storage integration"""
    
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "mpcswrosg")
        self.storage_key = os.getenv("AZURE_STORAGE_KEY")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "swro")
        self.blob_endpoint = f"https://{self.storage_account}.blob.core.windows.net"
        self.dfs_endpoint = f"https://{self.storage_account}.dfs.core.windows.net"
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get Azure Storage configuration for ClickHouse"""
        if not self.storage_key:
            raise ValueError("AZURE_STORAGE_KEY environment variable is required")
        
        return {
            "storage_account": self.storage_account,
            "storage_key": self.storage_key,
            "container_name": self.container_name,
            "blob_endpoint": self.blob_endpoint,
            "dfs_endpoint": self.dfs_endpoint,
            "connection_string": f"DefaultEndpointsProtocol=https;AccountName={self.storage_account};AccountKey={self.storage_key};EndpointSuffix=core.windows.net"
        }
    
    def get_clickhouse_storage_disk_config(self) -> str:
        """Generate ClickHouse storage disk configuration for Azure Blob Storage"""
        config = self.get_storage_config()
        
        return f"""
        <clickhouse>
            <storage_configuration>
                <disks>
                    <azure_blob_storage>
                        <type>azure_blob_storage</type>
                        <storage_account_url>{config['blob_endpoint']}</storage_account_url>
                        <container_name>{config['container_name']}</container_name>
                        <account_name>{config['storage_account']}</account_name>
                        <account_key>{config['storage_key']}</account_key>
                    </azure_blob_storage>
                </disks>
                <policies>
                    <azure_policy>
                        <volumes>
                            <azure_volume>
                                <disk>azure_blob_storage</disk>
                            </azure_volume>
                        </volumes>
                    </azure_policy>
                </policies>
            </storage_configuration>
        </clickhouse>
        """
    
    def get_azure_table_engine_config(self, table_name: str, path: str) -> str:
        """Generate ClickHouse table engine configuration for Azure Storage"""
        config = self.get_storage_config()
        
        return f"""
        CREATE TABLE {table_name} (
            -- Table columns will be defined dynamically based on parquet schema
        ) ENGINE = AzureBlobStorage(
            '{config['blob_endpoint']}/{config['container_name']}/{path}',
            '{config['storage_account']}',
            '{config['storage_key']}',
            'Parquet'
        )
        """
    
    def is_configured(self) -> bool:
        """Check if Azure Storage is properly configured"""
        return bool(self.storage_key and self.storage_account)


def get_azure_storage_config() -> ClickHouseAzureStorageConfig:
    """Get Azure Storage configuration instance"""
    return ClickHouseAzureStorageConfig()
