"""
Analysis Service - Main service coordinating between different operation modules
"""
import logging
from typing import Dict, List, Optional

from .analysis_crud_operations import AnalysisCrudOperations
from .azure_operations import AnalysisAzureOperations
from .data_operations import AnalysisDataOperations

logger = logging.getLogger(__name__)


class AnalysisService:
    """Main Analysis Service that coordinates between different operation modules"""

    def __init__(self):
        self.crud_ops = AnalysisCrudOperations()
        self.azure_ops = AnalysisAzureOperations()
        self.data_ops = AnalysisDataOperations()

    # CRUD Operations
    def get_analysis(
        self,
        analysis_id: int = None,
        authenticated_user_id: str = None,
        authenticated_user_email: str = None,
        authenticated_user_name: str = None,
        user_id: str = None,
        page: int = 1,
        limit: int = 10,
        name: str = None,
        from_date: str = None,
        to_date: str = None,
        visibility: str = None
    ):
        """Get analysis by ID or list analyses with filtering and access control"""
        if analysis_id:
            # Get single analysis by ID with access control
            return self.crud_ops.get_analysis_by_id_with_access_control(
                analysis_id=analysis_id,
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                authenticated_user_name=authenticated_user_name
            )
        else:
            # Get list of analyses with filtering and access control
            return self.crud_ops.get_analysis_with_access_control(
                authenticated_user_id=authenticated_user_id,
                authenticated_user_email=authenticated_user_email,
                authenticated_user_name=authenticated_user_name,
                user_id=user_id,
                page=page,
                limit=limit,
                name=name,
                from_date=from_date,
                to_date=to_date,
                visibility=visibility
            )

    def create_analysis(self, analysis_data: Dict):
        """Create new analysis"""
        return self.crud_ops.create_analysis(analysis_data)

    def update_analysis(self, analysis_data: Dict):
        """Update existing analysis"""
        return self.crud_ops.update_analysis(analysis_data)

    def delete_analysis(
        self,
        analysis_id: int,
        authenticated_user_id: str,
        authenticated_user_email: str = None
    ):
        """Delete analysis by ID with authorization"""
        return self.crud_ops.delete_analysis(
            analysis_id=analysis_id,
            authenticated_user_id=authenticated_user_id,
            authenticated_user_email=authenticated_user_email
        )

    # Directory Operations - Docker-aware with Azure primary
    def get_all_directories(self) -> List[Dict[str, str]]:
        """
        Get all directories (sites) using Azure operations as primary method in Docker.
        Falls back to Spark only in non-Docker environments.
        """
        import os
        is_docker = os.getenv('DOCKER_CONTAINER') or os.path.exists('/.dockerenv')

        if is_docker:
            # In Docker containers, use Azure operations directly (more reliable)
            try:
                logger.info("Docker environment detected - using Azure Data Lake operations directly")
                return self.azure_ops.get_all_directories()
            except Exception as azure_e:
                logger.error(f"Azure operations failed in Docker: {azure_e}")
                return []
        else:
            # In non-Docker environments, try Spark first then fallback to Azure
            try:
                logger.info("Non-Docker environment - using Spark-based operations")
                return self.data_ops.get_spark_directories()
            except Exception as e:
                logger.warning(f"Spark-based directory listing failed: {e}")
                logger.info("Falling back to Azure Data Lake direct access")
                try:
                    return self.azure_ops.get_all_directories()
                except Exception as fallback_e:
                    logger.error(f"Azure fallback also failed: {fallback_e}")
                    return []

    def get_subdirectories(self, site_id: str) -> List[Dict[str, str]]:
        """
        Get subdirectories (tables) for a site using Azure operations as primary method in Docker.
        Falls back to Spark only in non-Docker environments.
        """
        import os
        is_docker = os.getenv('DOCKER_CONTAINER') or os.path.exists('/.dockerenv')

        if is_docker:
            # In Docker containers, use Azure operations directly (more reliable)
            try:
                logger.info(f"Docker environment detected - getting subdirectories for {site_id} using Azure Data Lake operations")
                return self.azure_ops.get_subdirectories(site_id)
            except Exception as azure_e:
                logger.error(f"Azure operations failed for {site_id} in Docker: {azure_e}")
                return []
        else:
            # In non-Docker environments, try Spark first then fallback to Azure
            try:
                logger.info(f"Non-Docker environment - getting subdirectories for {site_id} using Spark-based operations")
                return self.data_ops.get_spark_subdirectories(site_id)
            except Exception as e:
                logger.warning(f"Spark-based subdirectory listing failed for {site_id}: {e}")
                logger.info("Falling back to Azure Data Lake direct access")
                try:
                    return self.azure_ops.get_subdirectories(site_id)
                except Exception as fallback_e:
                    logger.error(f"Azure fallback also failed for {site_id}: {fallback_e}")
                    return []

    # Data Operations - Enhanced with filtering
    def get_parquet_columns(
        self,
        table_id: str,
        site_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        date_column: Optional[str] = "Datetime",
        date_format: Optional[str] = None,
        # New filtering parameters
        include_samples: bool = True,
        exclude_calculated: bool = True,
        exclude_null: bool = True,
        include_performance: bool = False
    ) -> Dict:
        """
        Get parquet columns with enhanced filtering options.
        Now supports cleaning up the response to remove unnecessary data.
        Returns ALL data rows for live analysis (no sample size limitation).
        """
        return self.data_ops.get_parquet_columns(
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
        """
        Get column metadata for multiple tables in a single request.
        Uses optimized FastMetadataService (PyArrow) with SparkSQL fallback.
        
        Args:
            table_requests: List of dicts with 'siteName' and 'tableName' keys
            from_date: Start date for filtering (YYYY-MM-DD)
            to_date: End date for filtering (YYYY-MM-DD)
            date_column: Date column name for filtering
            include_samples: Include sample data in response
            exclude_calculated: Exclude calculated columns
            exclude_null: Exclude null columns
            include_performance: Include performance metrics
            
        Returns:
            Dict with bulk column metadata results
        """
        return self.data_ops.get_bulk_parquet_columns(
            table_requests=table_requests,
            from_date=from_date,
            to_date=to_date,
            date_column=date_column,
            include_samples=include_samples,
            exclude_calculated=exclude_calculated,
            exclude_null=exclude_null,
            include_performance=include_performance
        )

    def get_unique_racks(self, site_id: str, table_ids: List[str]) -> Dict:
        """
        Get unique racks from specified tables using ClickHouse as primary data source with Spark fallback.

        Args:
            site_id: Site identifier
            table_ids: List of table identifiers

        Returns:
            Dict with unique racks data
        """
        # Check for ClickHouse availability first
        if self._is_clickhouse_available():
            try:
                logger.info(f"Using ClickHouse as primary data source for racks in site {site_id}")
                from .clickhouse_rack_service import ClickHouseRackService
                clickhouse_service = ClickHouseRackService()
                return clickhouse_service.get_unique_racks_from_clickhouse(site_id, table_ids)
            except Exception as e:
                logger.warning(f"ClickHouse rack service failed: {str(e)}, falling back to Spark")
        else:
            logger.info(f"ClickHouse not available, using Spark fallback for racks in site {site_id}")

        # Fallback to existing Spark-based implementation
        from .smart_rack_service import SmartRackService
        rack_service = SmartRackService()
        return rack_service.get_unique_racks_smart(site_id, table_ids)

    def _is_clickhouse_available(self) -> bool:
        """
        Check if ClickHouse is available and responsive.

        Returns:
            bool: True if ClickHouse is available, False otherwise
        """
        try:
            from config.clickhouse_connector import check_clickhouse_health
            health = check_clickhouse_health()
            return health.get("status") == "healthy"
        except Exception as e:
            logger.debug(f"ClickHouse availability check failed: {e}")
            return False

    # Legacy methods for backward compatibility
    def get_parquet_files_by_date_range(self, *args, **kwargs):
        """Legacy method - delegates to data operations"""
        return self.data_ops.get_parquet_files_by_date_range(*args, **kwargs)