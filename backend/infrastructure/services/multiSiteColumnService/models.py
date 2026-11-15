"""
Data models and enums for the Multi-Site Column Data Service.
Defines the core data structures used for column requests and responses.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Any, Optional
from datetime import datetime


class FilterMode(Enum):
    """DateTime filtering modes based on endpoint parameters."""
    NONE = "none"        # No DateTime filtering - return all data
    EXACT = "exact"      # Exact timestamp match - single date/time provided
    RANGE = "range"      # DateTime range filtering - both dates provided


@dataclass
class ColumnRequest:
    """
    Represents a single column data request from the API payload.
    Matches the expected JSON structure from the endpoint.
    """
    columnName: str
    columnType: str
    tableName: str
    siteName: str

    def __post_init__(self):
        """Validate request data after initialization."""
        if not all([self.columnName, self.columnType, self.tableName, self.siteName]):
            raise ValueError("All fields (columnName, columnType, tableName, siteName) are required")
    
    @property
    def unique_key(self) -> str:
        """Generate unique key for this column request."""
        return f"{self.siteName}_{self.tableName}_{self.columnName}"


@dataclass
class ColumnResponse:
    """
    Represents a column response with data.
    Extends ColumnRequest with the actual data values.
    """
    columnName: str
    columnType: str
    tableName: str
    siteName: str
    dataSource: List[Any]
    racks: Optional[List[str]] = None

    @classmethod
    def from_request(cls, request: ColumnRequest, data: List[Any]) -> 'ColumnResponse':
        """Create response from request with data."""
        return cls(
            columnName=request.columnName,
            columnType=request.columnType,
            tableName=request.tableName,
            siteName=request.siteName,
            dataSource=data,
            racks=None
        )

    @classmethod
    def create_error_response(cls, request: ColumnRequest, error_message: str) -> 'ColumnResponse':
        """Create error response for failed column request."""
        return cls(
            columnName=request.columnName,
            columnType=request.columnType,
            tableName=request.tableName,
            siteName=request.siteName,
            dataSource=[],  # Empty data with error logged elsewhere
            racks=None
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "columnName": self.columnName,
            "columnType": self.columnType,
            "tableName": self.tableName,
            "siteName": self.siteName,
            "dataSource": self.dataSource
        }
        # Include racks if it's not None
        if self.racks is not None:
            result["racks"] = self.racks
        return result


@dataclass
class FileInfo:
    """Information about a parquet file for processing."""
    path: str
    name: str
    size: Optional[int] = None
    last_modified: Optional[datetime] = None

    def extract_date_from_path(self) -> Optional[datetime]:
        """
        Extract date from file path structure.
        Expected format: tables/gold/{site}/{table}/YYYY/MM/DD/file.parquet
        """
        try:
            path_parts = self.path.split('/')
            if len(path_parts) >= 7:
                year = int(path_parts[-4])
                month = int(path_parts[-3])
                day = int(path_parts[-2])
                return datetime(year, month, day)
        except (ValueError, IndexError):
            pass
        return None


@dataclass
class ProcessingStats:
    """Statistics for performance monitoring."""
    sites_processed: int = 0
    tables_processed: int = 0
    files_processed: int = 0
    rows_processed: int = 0
    total_columns: int = 0
    processing_time_seconds: float = 0.0
    filter_mode: str = "none"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "sites_processed": self.sites_processed,
            "tables_processed": self.tables_processed,
            "files_processed": self.files_processed,
            "rows_processed": self.rows_processed,
            "total_columns": self.total_columns,
            "processing_time_seconds": round(self.processing_time_seconds, 3),
            "filter_mode": self.filter_mode
        }


@dataclass
class TableProcessingResult:
    """Result of processing a single table."""
    site_name: str
    table_name: str
    column_responses: List[ColumnResponse]
    processing_time: float
    rows_processed: int
    success: bool
    error_message: Optional[str] = None