"""
File Operations Module
Handles file system operations and parquet file processing.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)


class FileOperations:
    """Handles file system and parquet file operations"""

    def get_parquet_files_by_date_range(
        self,
        site_id: str,
        table_id: str,
        from_date: str,
        to_date: str
    ) -> List[Dict]:
        """
        Get parquet files within a specific date range.
        """
        try:
            # Parse dates
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            # Set to end of day
            to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Use the existing Azure operations for file listing
            from .azure_operations import AnalysisAzureOperations
            azure_ops = AnalysisAzureOperations()
            
            # Get all files for the table
            blob_prefix = f"tables/gold/{site_id}/{table_id}/"
            all_blobs = azure_ops._list_blobs_with_prefix(blob_prefix)
            
            # Filter by date range
            filtered_files = self._filter_parquet_files_by_date(
                all_blobs, from_date_obj, to_date_obj, f"{site_id}/{table_id}"
            )
            
            return filtered_files
            
        except Exception as e:
            logger.error(f"Error getting parquet files by date range: {str(e)}")
            return []

    def _filter_parquet_files_by_date(self, paths, from_date_obj: datetime, to_date_obj: datetime, table_path: str) -> List[Dict]:
        """
        Filter parquet files based on modification date and return sorted by most recent first.
        """
        parquet_files = []
        
        for path in paths:
            try:
                # Extract date from path
                # Expected format: tables/gold/{site}/{table}/YYYY/MM/DD/file.parquet
                path_str = str(path) if hasattr(path, '__str__') else path.name if hasattr(path, 'name') else str(path)
                
                # Skip if not a parquet file
                if not path_str.endswith('.parquet'):
                    continue
                
                # Extract date components from path
                parts = path_str.split('/')
                if len(parts) >= 7:  # Ensure we have enough path components
                    try:
                        year = int(parts[-4])
                        month = int(parts[-3])
                        day = int(parts[-2])
                        
                        # Create date object for the file
                        file_date = datetime(year, month, day, tzinfo=timezone.utc)
                        
                        # Check if file date is within range
                        if from_date_obj <= file_date <= to_date_obj:
                            parquet_files.append({
                                "path": path_str,
                                "date": file_date
                            })
                    except (ValueError, IndexError):
                        # If we can't parse the date, include the file to be safe
                        parquet_files.append({
                            "path": path_str,
                            "date": datetime.now(timezone.utc)  # Use current date as fallback
                        })
            except Exception as e:
                logger.warning(f"Error processing path {path}: {e}")
                # Include the file to be safe
                parquet_files.append({
                    "path": str(path) if hasattr(path, '__str__') else path.name if hasattr(path, 'name') else str(path),
                    "date": datetime.now(timezone.utc)  # Use current date as fallback
                })
        
        # Sort by date (most recent first)
        parquet_files.sort(key=lambda x: x["date"], reverse=True)
        logger.info(f"Found {len(parquet_files)} parquet files in date range for {table_path}")
        return parquet_files
