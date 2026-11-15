"""
Main Dashboard-033 Service
Orchestrates all sub-services using composition pattern.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base_service import Dash033BaseService
from .runtime_service import RuntimeService
from .cip_service import CIPService
from .membrane_service import MembraneService
from .metadata_service import MetadataService
# Note: Membrane and Metadata services not yet split - keeping original implementation for now

from infrastructure.exceptions import ClickHouseServiceError

logger = logging.getLogger(__name__)


class Dash_033OptimizedService_CH(Dash033BaseService):
    """
    Main service for Dash-033 ClickHouse operations.
    Uses composition to delegate to specialized sub-services.
    
    This approach improves code organization and maintainability by:
    - Separating concerns into focused services
    - Making testing easier (can test services independently)
    - Improving code reusability
    - Following Single Responsibility Principle
    """

    def __init__(self):
        """Initialize main service with sub-service instances."""
        super().__init__()
        
        # Initialize specialized services
        self.runtime_service = RuntimeService()
        self.cip_service = CIPService()
        self.membrane_service = MembraneService()
        self.metadata_service = MetadataService()
        # TODO: Add MembraneService() when created
        # TODO: Add MetadataService() when created
        
        logger.info("Dash_033OptimizedService_CH initialized with sub-services")

    # ==================== Runtime Operations (Delegated) ====================

    def get_racks_runtime_only(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: datetime = None,
        end_time: datetime = None,
        racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get rack runtime percentages.
        Delegates to RuntimeService.
        """
        return self.runtime_service.get_racks_runtime_only(
            site_name=site_name,
            user=user,
            start_time=start_time,
            end_time=end_time,
            racks=racks
        )

    # ==================== CIP Operations (Delegated) ====================

    def get_cip_validated_info(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        page: int = 1,
        limit: int = 25,
        racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get CIP validated info.
        Delegates to CIPService.
        """
        return self.cip_service.get_cip_validated_info(
            site_name=site_name,
            user=user,
            start_time=start_time,
            end_time=end_time,
            page=page,
            limit=limit,
            racks=racks
        )

    def get_cip_flushing_info(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        page: int = 1,
        limit: int = 25,
        racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get CIP flushing info.
        Delegates to CIPService.
        """
        return self.cip_service.get_cip_flushing_info(
            site_name=site_name,
            user=user,
            start_time=start_time,
            end_time=end_time,
            page=page,
            limit=limit,
            racks=racks
        )

    def get_cip_summary(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get CIP summary.
        Delegates to CIPService.
        """
        return self.cip_service.get_cip_summary(
            site_name=site_name,
            user=user,
            start_time=start_time,
            end_time=end_time,
            racks=racks
        )
    
    def get_membrane_graph_averages(
        self,
        site_name: str = None,
        user: dict = None,
        col_pre: str = "AVG_Salt_Passage_Normalized_Pre",
        col_post: str = "AVG_Salt_Passage_Normalized_Post",
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        return self.membrane_service.get_membrane_graph_averages(
            site_name=site_name,
            user=user,
            col_pre=col_pre,
            col_post=col_post,
            start_time=start_time,
            end_time=end_time,
            racks=racks
        )
    
    def get_membrane_info(
        self,
        site_name: str = None,
        user: dict = None,
        page: int = 1,
        limit: int = 25,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None,
        modes: Optional[List[str]] = None
    ):
        return self.membrane_service.get_membrane_info(
            site_name=site_name,
            user=user,
            page=page,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            racks=racks,
            modes=modes
        )
    
    def get_membrane_graph_percentages(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        return self.membrane_service.get_membrane_graph_percentages(
            site_name=site_name,
            user=user,
            start_time=start_time,
            end_time=end_time,
            racks=racks
        )
    
    def get_columns_metadata(
        self,
        site_name: str = None,
        user: dict = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        include_samples: bool = True,
        exclude_calculated: bool = True,
        exclude_null: bool = True,
        include_performance: bool = False,
        racks: Optional[List[str]] = None
    ):
        return self.metadata_service.get_columns_metadata(
            site_name=site_name,
            user=user,
            from_date=from_date,
            to_date=to_date,
            include_samples=include_samples,
            exclude_calculated=exclude_calculated,
            exclude_null=exclude_null,
            include_performance=include_performance,
            racks=racks
        )
    
    def get_racks_data(
        self,
        site_name: str = None,
        user: dict = None
    ):
        return self.metadata_service.get_racks_data(
            site_name=site_name,
            user=user
        )    

    # ==================== Membrane Operations (TODO: Delegate to MembraneService) ====================
    
    # Note: The following methods are temporarily kept in the original file
    # until MembraneService is fully extracted.
    # These should be moved to a dedicated MembraneService class:
    # - get_membrane_graph_averages()
    # - get_membrane_info()
    # - get_membrane_graph_percentages()
    
    # ==================== Metadata Operations (TODO: Delegate to MetadataService) ====================
    
    # Note: The following methods are temporarily kept in the original file
    # until MetadataService is fully extracted.
    # These should be moved to a dedicated MetadataService class:
    # - get_columns_metadata()
    # - get_racks_data()
    
    # For now, import remaining methods from original service
    # This is a temporary bridge until full refactoring is complete


