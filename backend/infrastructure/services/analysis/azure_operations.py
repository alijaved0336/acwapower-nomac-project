"""
Analysis Azure Operations Module
Handles Azure Data Lake Storage operations for analysis service.
"""
import logging
import os
from typing import Dict, List, Optional

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
from django.conf import settings

logger = logging.getLogger(__name__)


class AnalysisAzureOperations:
    """Handles Azure Data Lake Storage operations"""

    def __init__(self, base_paths: Optional[List[str]] = None):
        # Initialize Azure Data Lake client
        self.account_name = (
            os.getenv("AZURE_ACCOUNT_NAME")
            or os.getenv("AZURE_STORAGE_ACCOUNT")
            or "mpcswrosg"
        )
        self.filesystem_name = "swro"
        self.account_url = f"https://{self.account_name}.dfs.core.windows.net"
        self.filesystem_client = None
        
        # Set default base paths if not provided
        self.base_paths = base_paths or ["tables/gold", "tables"]

        try:
            # Try DefaultAzureCredential first, fall back to account key if available
            account_key = os.getenv("AZURE_ACCOUNT_KEY") or os.getenv(
                "AZURE_STORAGE_KEY"
            )

            if account_key:
                self.service_client = DataLakeServiceClient(
                    account_url=self.account_url, credential=account_key
                )
            else:
                credential = DefaultAzureCredential()
                self.service_client = DataLakeServiceClient(
                    account_url=self.account_url, credential=credential
                )

            self.filesystem_client = self.service_client.get_file_system_client(
                file_system=self.filesystem_name
            )
            logger.info("Azure Data Lake client initialized successfully")
            logger.info(f"Base paths configured: {self.base_paths}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Data Lake client: {e}")
            self.service_client = None
            self.filesystem_client = None

    def get_all_directories(self) -> List[Dict[str, str]]:
        """
        Get all directories in the Azure Data Lake Storage container.
        Returns a list of directory names (sites).
        """
        if not self.filesystem_client:
            raise Exception(
                "Azure Data Lake client not initialized. Check your environment variables."
            )

        try:
            all_directories = []
            seen_directories = set()  # To avoid duplicates

            for base_path in self.base_paths:
                logger.info(f"Scanning base path: {base_path}")
                directories = self._get_directories_from_path(base_path)
                
                for directory in directories:
                    # Use directory name as key to avoid duplicates
                    dir_key = directory["name"]
                    if dir_key not in seen_directories:
                        seen_directories.add(dir_key)
                        all_directories.append(directory)
                    else:
                        logger.info(f"Duplicate directory found: {dir_key} (skipping)")

            logger.info(f"Found {len(all_directories)} unique directories across all base paths")
            return all_directories
        except Exception as e:
            logger.error(f"Error getting directories: {str(e)}", exc_info=True)
            # Return generic message in production to avoid path disclosure
            if settings.DEBUG:
                raise Exception(f"Failed to retrieve directories: {str(e)}")
            else:
                # Instead of raising an exception, return an empty list
                return []

    def _get_directories_from_path(self, base_path: str) -> List[Dict[str, str]]:
        """
        Get directories from a specific base path.
        """
        directories = []
        
        try:
            paths = self.filesystem_client.get_paths(
                path=base_path, recursive=False
            )

            for path in paths:
                if path.is_directory:
                    # Extract just the directory name from the full path
                    dir_name = path.name.split("/")[-1]
                    
                    # Skip hidden directories and system directories
                    if (base_path == "tables" and 
                        dir_name.lower() in ['gold', 'silver', 'bronze']):
                        continue

                    if not dir_name.startswith(".") and not dir_name.startswith("_"):
                        directories.append({
                            "name": dir_name,
                            "path": path.name,
                            "base_path": base_path
                        })

            logger.info(f"Found {len(directories)} directories in {base_path}")
            return directories
            
        except Exception as e:
            logger.warning(f"Could not access path {base_path}: {str(e)}")
            return []

    def get_subdirectories(self, site_id: str, site_base_path: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get all subdirectories (tables) for a given site directory.
        If site_base_path is provided, use it; otherwise try all base paths.
        """
        if not self.filesystem_client:
            raise Exception(
                "Azure Data Lake client not initialized. Check your environment variables."
            )

        # If a specific base path is provided, use only that
        if site_base_path:
            paths_to_check = [site_base_path]
        else:
            # Try all base paths to find where this site exists
            paths_to_check = self.base_paths

        all_subdirectories = []
        found_in_paths = []

        for base_path in paths_to_check:
            try:
                site_path = f"{base_path}/{site_id}"
                subdirectories = self._get_subdirectories_from_path(site_path)
                
                if subdirectories:
                    all_subdirectories.extend(subdirectories)
                    found_in_paths.append(base_path)
                    
            except Exception as e:
                logger.warning(f"Could not access {base_path}/{site_id}: {str(e)}")
                continue

        if not all_subdirectories:
            error_msg = f"No subdirectories found for site {site_id} in any base path: {paths_to_check}"
            logger.error(error_msg)
            if settings.DEBUG:
                raise Exception(error_msg)
            else:
                raise Exception("Failed to retrieve table information. Please try again later.")

        logger.info(f"Found {len(all_subdirectories)} subdirectories for {site_id} in paths: {found_in_paths}")
        return all_subdirectories

    def _get_subdirectories_from_path(self, site_path: str) -> List[Dict[str, str]]:
        """
        Get subdirectories from a specific site path.
        """
        subdirectories = []
        
        try:
            paths = self.filesystem_client.get_paths(
                path=site_path, recursive=False
            )

            for path in paths:
                if path.is_directory:
                    # Extract just the subdirectory name from the full path
                    subdir_name = path.name.split("/")[-1]
                    # Skip hidden directories and system directories
                    if not subdir_name.startswith(".") and not subdir_name.startswith("_"):
                        subdirectories.append({
                            "name": subdir_name,
                            "path": path.name,
                            "site_path": site_path
                        })

            return subdirectories
            
        except Exception as e:
            logger.warning(f"Could not access site path {site_path}: {str(e)}")
            return []

    def find_site_base_path(self, site_id: str) -> Optional[str]:
        """
        Find which base path contains the given site.
        Returns the first base path where the site is found.
        """
        if not self.filesystem_client:
            return None
            
        for base_path in self.base_paths:
            try:
                site_path = f"{base_path}/{site_id}"
                paths = self.filesystem_client.get_paths(
                    path=site_path, recursive=False
                )
                # If we can list the path without error, it exists
                next(paths, None)  # Try to get first item
                return base_path
            except Exception:
                continue
                
        return None

    def _list_blobs_with_prefix(self, blob_prefix: str):
        """
        List all blobs with the given prefix.
        
        Args:
            blob_prefix: Prefix to filter blobs
            
        Returns:
            List of blob paths
        """
        if not self.filesystem_client:
            raise Exception(
                "Azure Data Lake client not initialized. Check your environment variables."
            )

        try:
            blobs = []
            paths = self.filesystem_client.get_paths(path=blob_prefix, recursive=True)
            
            for path in paths:
                if not path.is_directory:
                    blobs.append(path)
                    
            logger.info(f"Found {len(blobs)} blobs with prefix {blob_prefix}")
            return blobs
        except Exception as e:
            logger.error(f"Error listing blobs with prefix {blob_prefix}: {str(e)}")
            # Return generic message in production to avoid path disclosure
            if settings.DEBUG:
                raise Exception(f"Failed to list blobs with prefix {blob_prefix}: {str(e)}")
            else:
                raise Exception("Failed to retrieve file information. Please try again later.")