import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.http import Http404

from config.databricks_connector import get_databricks_connector
from config.databricks_sql_queries import CHECK_ANALYSIS_EXISTS
from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.orm.repositories.widgets import WidgetsRepository
from infrastructure.orm.repositories.dash_009_widgetRepository import HeatmapWidgetsRepository
from infrastructure.orm.repositories.analysis import AnalysisRepo
from infrastructure.services.analysis.analysis_crud_operations import (
    AnalysisCrudOperations,
)
from infrastructure.services.multiSiteColumnService import MultiSiteColumnDataService, ColumnRequest
from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService
from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig

logger = logging.getLogger(__name__)


class Dash009WidgetsService:

    def __init__(self):
        # Repository instances are now lightweight since they use connection-per-operation
        self.cache_service = CacheService()
        self.clickhouse_service = ClickHouseADLSService()
        logger.info("WidgetsService initialized with Redis caching support")

    def _get_repository(self) -> HeatmapWidgetsRepository:
        """Get a fresh repository instance for each operation"""
        return HeatmapWidgetsRepository()

    def _get_analysis_repository(self) -> AnalysisRepo:
        """Get a fresh repository instance for each operation"""
        return AnalysisRepo()

    def _get_analysis_service(self) -> AnalysisCrudOperations:
        """Get analysis service instance for operations"""
        return AnalysisCrudOperations()

    def get_widget(self, site_id: str, pump_id: str ,user_id: str, page):
        """
        Retrieve a widget by ID for a specific analysis
        Returns: dict with widget data or None if not found
        """
        try:
            repository = self._get_repository()
            widget = repository.get_heatmap_widget(site_id, pump_id, user_id, page)

            return widget

        except Exception as e:
            logger.error(f"Error in get_widget service: {str(e)}")
            raise

    def create_widget(self, widget_data: Dict, user_id: str):
        """
        Create a new widget for a specific analysis
        Returns: dict with created widget data
        """
        try:
            if not widget_data.get("id"):
                widget_data["id"] = str(uuid.uuid4())

            site_id = widget_data.get("site_id")
            pump_id = widget_data.get("pump_id")  # Optional field
            page = widget_data.get("page")

            # Normalize empty string to None for pump_id
            if pump_id and not pump_id.strip():
                pump_id = None
                widget_data["pump_id"] = None
            elif pump_id is None:
                widget_data["pump_id"] = None

            repository = self._get_repository()
            created_widget = repository.create_or_update_heatmap_widget(widget_data, user_id)

            return created_widget

        except Exception as e:
            logger.error(f"Error in create_widget service: {str(e)}")
            raise