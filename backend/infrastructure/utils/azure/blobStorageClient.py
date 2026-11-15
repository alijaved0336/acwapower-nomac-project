import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential


class BlobStorageClient:
    """
    Azure Blob Storage client wrapper.
    """
    
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "mpcswrosg")
        self.storage_key = os.getenv("AZURE_STORAGE_KEY")
        self.container_name = "swro"
        self._init_blob_client()
    
    def _init_blob_client(self):
        """Initialize Azure Blob Storage client."""
        try:
            account_url = f"https://{self.storage_account}.blob.core.windows.net"
            if self.storage_key:
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url, 
                    credential=self.storage_key
                )
            else:
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url, 
                    credential=credential
                )
            print(f"[BLOB_CLIENT] Initialized blob client for {self.storage_account}")
        except Exception as e:
            print(f"[BLOB_CLIENT] Failed to initialize blob client: {e}")
            self.blob_service_client = None
    
    def list_parquet_files(self, blob_prefix: str):
        """List parquet files in the given prefix."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blobs = list(container_client.list_blobs(name_starts_with=blob_prefix))
            return [blob for blob in blobs if blob.name.endswith('.parquet')]
        except Exception as e:
            print(f"[BLOB_CLIENT] Error listing files: {e}")
            return []
    
    def get_blob_client(self, blob_name: str):
        """Get blob client for specific file."""
        return self.blob_service_client.get_blob_client(
            container=self.container_name, 
            blob=blob_name
        )
