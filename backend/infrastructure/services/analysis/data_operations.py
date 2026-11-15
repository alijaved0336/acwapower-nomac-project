"""
Analysis Data Operations Module - Refactored
Coordinates between specialized operation modules for better maintainability.
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalysisDataOperations:
    """Coordinates data processing operations using specialized modules"""

    def __init__(self):
        # Lazy initialization of specialized modules
        self._column_ops = None
        self._spark_ops = None
        self._file_ops = None

    @property
    def column_ops(self):
        """Get column operations instance"""
        if self._column_ops is None:
            from .column_operations import ColumnOperations
            self._column_ops = ColumnOperations()
        return self._column_ops

    @property
    def spark_ops(self):
        """Get spark operations instance"""
        if self._spark_ops is None:
            from .spark_operations import SparkOperations
            self._spark_ops = SparkOperations()
        return self._spark_ops

    @property
    def file_ops(self):
        """Get file operations instance"""
        if self._file_ops is None:
            from .file_operations import FileOperations
            self._file_ops = FileOperations()
        return self._file_ops

    # Column Operations - Delegated to ColumnOperations
    def get_parquet_columns(
        self,
        table_id: str,
        site_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: Optional[str] = "Datetime",
        date_format: Optional[str] = None,
        include_samples: bool = True,
        exclude_calculated: bool = True,
        exclude_null: bool = True,
        include_performance: bool = False
    ) -> Dict:
        """Get parquet columns - delegated to ColumnOperations"""
        return self.column_ops.get_parquet_columns(
            table_id=table_id,
            site_id=site_id,
            from_date=from_date,
            to_date=to_date,
            date_column=date_column,
            date_format=date_format,
            include_samples=include_samples,
            exclude_calculated=exclude_calculated,
            exclude_null=exclude_null,
            include_performance=include_performance
        )

    def get_bulk_parquet_columns(
        self,
        table_requests: List[Dict],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: Optional[str] = "Datetime",
        include_samples: bool = True,
        exclude_calculated: bool = True,
        exclude_null: bool = True,
        include_performance: bool = False
    ) -> Dict:
        """Get bulk parquet columns - delegated to ColumnOperations"""
        return self.column_ops.get_bulk_parquet_columns(
            table_requests=table_requests,
            from_date=from_date,
            to_date=to_date,
            date_column=date_column,
            include_samples=include_samples,
            exclude_calculated=exclude_calculated,
            exclude_null=exclude_null,
            include_performance=include_performance
        )

    # Spark Operations - Delegated to SparkOperations
    def get_spark_directories(self) -> List[Dict[str, str]]:
        """Get directories using Spark - delegated to SparkOperations"""
        return self.spark_ops.get_spark_directories()

    def get_spark_subdirectories(self, site_id: str) -> List[Dict[str, str]]:
        """Get subdirectories using Spark - delegated to SparkOperations"""
        return self.spark_ops.get_spark_subdirectories(site_id)

    # File Operations - Delegated to FileOperations
    def get_parquet_files_by_date_range(
        self,
        site_id: str,
        table_id: str,
        from_date: str,
        to_date: str
    ) -> List[Dict]:
        """Get parquet files by date range - delegated to FileOperations"""
        return self.file_ops.get_parquet_files_by_date_range(
            site_id=site_id,
            table_id=table_id,
            from_date=from_date,
            to_date=to_date
        )

    # Legacy method for backward compatibility
    def get_unique_racks(self, site_id: str, table_ids: List[str]) -> Dict:
        """
        Legacy method - now handled by dedicated RackService.
        This method is kept for backward compatibility but should not be used.
        """
        logger.warning("get_unique_racks called on AnalysisDataOperations - this should use RackService instead")
        raise NotImplementedError("Use RackService.get_unique_racks_optimized() instead")