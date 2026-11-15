"""
Controller for scheduler monitoring endpoint.
Provides comprehensive monitoring data for the APScheduler migration job.
"""
import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.services.scheduler_monitoring import SchedulerMonitoringService
from interface.schemas.scheduler_monitoring_schemas import scheduler_monitoring_response_schema

logger = logging.getLogger(__name__)


class SchedulerMonitoringController(APIView):
    """
    Controller for scheduler monitoring.
    Returns comprehensive data about scheduler status, current execution,
    historical statistics, and recent errors.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_id="get_scheduler_monitoring",
        operation_summary="Get comprehensive scheduler monitoring data",
        operation_description="""
        Retrieve detailed monitoring information about the APScheduler migration job.

        This endpoint provides real-time and historical data including:

        **Scheduler Status:**
        - Whether the scheduler is enabled and running
        - Next scheduled run time
        - Trigger configuration (interval, timezone)

        **Current Execution:**
        - Real-time progress of ongoing migration (if any)
        - Current phase (discovering, schema_creation, data_migration)
        - Progress percentage (0-100)
        - Sites and tables processed so far
        - Elapsed time since start

        **Historical Statistics (Last 24 Hours):**
        - Total executions
        - Success/failure counts and rates
        - Average execution duration
        - Timestamps of last successful and failed runs

        **Latest Migration Details:**
        - Complete information about the most recent migration
        - Duration, rows migrated, status

        **Recent Errors:**
        - Last 10 failed migrations with error messages
        - Useful for debugging and monitoring issues

        **File Statistics:**
        - Total files tracked
        - Files imported successfully/failed/pending
        - Last file update timestamp

        **Use Cases:**
        - Dashboard monitoring displays
        - Health check integrations
        - Alerting systems
        - Performance analysis
        - Debugging migration issues

        **Notes:**
        - Public endpoint (no authentication required)
        - Data is aggregated from APScheduler, Redis cache, and ClickHouse
        - Real-time progress tracking via Redis for minimal latency
        - Historical data provides trends and patterns
        """,
        responses={
            200: scheduler_monitoring_response_schema,
            500: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True)
                }
            )
        },
        tags=["Scheduler Monitoring"]
    )
    def get(self, request):
        """
        GET endpoint to retrieve scheduler monitoring data.

        Returns:
            Response: JSON response with comprehensive monitoring data
        """
        try:
            logger.info("Fetching scheduler monitoring data")

            # Initialize service and get monitoring data
            service = SchedulerMonitoringService()
            monitoring_data = service.get_complete_monitoring_data()

            logger.info("Successfully retrieved scheduler monitoring data")

            return ResponseBuilder.success(
                data=monitoring_data,
                message="Scheduler monitoring data retrieved successfully"
            )

        except Exception as e:
            logger.error(f"Failed to retrieve scheduler monitoring data: {e}", exc_info=True)
            return ResponseBuilder.error(
                message=f"Failed to retrieve monitoring data: {str(e)}",
                status_code=500
            )
