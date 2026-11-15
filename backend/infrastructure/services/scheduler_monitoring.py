"""
Service layer for scheduler monitoring.
Orchestrates data from APScheduler, Redis cache, and ClickHouse.
"""
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from infrastructure.utils.scheduler_cache import SchedulerCache
from infrastructure.orm.repositories.scheduler_monitoring import SchedulerMonitoringRepository

logger = logging.getLogger(__name__)


class SchedulerMonitoringService:
    """
    Service for aggregating scheduler monitoring data from multiple sources:
    - APScheduler (scheduler status)
    - Redis cache (current execution progress)
    - ClickHouse (historical statistics)
    """

    def __init__(self):
        """Initialize service with repository and cache."""
        self.repository = SchedulerMonitoringRepository()
        self.cache = SchedulerCache()

    def get_complete_monitoring_data(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring data from all sources.

        Returns:
            Dict with scheduler_status, current_execution, statistics,
            latest_migration, recent_errors, and file_statistics
        """
        try:
            monitoring_data = {
                "scheduler_status": self.get_scheduler_status(),
                "current_execution": self.get_current_execution(),
                "statistics": self.repository.get_migration_statistics(hours=24),
                "latest_migration": self.repository.get_latest_migration(),
                "recent_errors": self.repository.get_failed_migrations(limit=10),
                "file_statistics": self.repository.get_file_tracking_stats()
            }

            logger.info("Successfully aggregated complete monitoring data")
            return monitoring_data

        except Exception as e:
            logger.error(f"Failed to get complete monitoring data: {e}")
            raise

    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get APScheduler status.

        Returns:
            Dict with scheduler status information
        """
        try:
            # Import here to avoid circular imports
            from infrastructure.apps import InfrastructureConfig

            scheduler = InfrastructureConfig._scheduler

            if not scheduler:
                return {
                    "is_enabled": False,
                    "is_running": False,
                    "job_id": None,
                    "job_name": None,
                    "next_run_time": None,
                    "trigger_type": None,
                    "trigger_interval": None,
                    "timezone": None
                }

            # Get job information
            job = scheduler.get_job('adls_migration_hourly')

            if not job:
                return {
                    "is_enabled": True,
                    "is_running": scheduler.running,
                    "job_id": None,
                    "job_name": None,
                    "next_run_time": None,
                    "trigger_type": None,
                    "trigger_interval": None,
                    "timezone": str(scheduler.timezone) if hasattr(scheduler, 'timezone') else None
                }

            # Extract trigger information
            trigger_type = str(type(job.trigger).__name__)
            trigger_interval = None

            if hasattr(job.trigger, 'interval'):
                interval = job.trigger.interval
                # Convert timedelta to human-readable format
                hours = interval.total_seconds() / 3600
                if hours == 1:
                    trigger_interval = "1 hour"
                elif hours < 1:
                    minutes = interval.total_seconds() / 60
                    trigger_interval = f"{int(minutes)} minutes"
                else:
                    trigger_interval = f"{int(hours)} hours"

            status = {
                "is_enabled": True,
                "is_running": scheduler.running,
                "job_id": job.id,
                "job_name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger_type": trigger_type,
                "trigger_interval": trigger_interval,
                "timezone": str(scheduler.timezone) if hasattr(scheduler, 'timezone') else None
            }

            logger.info(f"Retrieved scheduler status: {status['job_id']} - next run: {status['next_run_time']}")
            return status

        except Exception as e:
            logger.error(f"Failed to get scheduler status: {e}")
            return {
                "is_enabled": False,
                "is_running": False,
                "job_id": None,
                "job_name": None,
                "next_run_time": None,
                "trigger_type": None,
                "trigger_interval": None,
                "timezone": None,
                "error": str(e)
            }

    def get_current_execution(self) -> Dict[str, Any]:
        """
        Get current migration execution status from Redis cache.

        Returns:
            Dict with current execution information
        """
        try:
            execution = self.cache.get_current_execution()
            progress = self.cache.get_progress()

            if not execution:
                return {
                    "is_running": False,
                    "migration_id": None,
                    "started_at": None,
                    "elapsed_time_seconds": 0,
                    "current_phase": None,
                    "progress_percentage": 0,
                    "current_site": None,
                    "current_table": None,
                    "sites_processed": 0,
                    "tables_processed": 0,
                    "total_sites_discovered": 0,
                    "total_tables_discovered": 0
                }

            # Calculate elapsed time
            elapsed_seconds = self.cache.get_elapsed_time_seconds()

            # Merge execution and progress data
            current_execution = {
                "is_running": execution.get("is_running", False),
                "migration_id": execution.get("migration_id"),
                "started_at": execution.get("started_at"),
                "elapsed_time_seconds": elapsed_seconds,
                "current_phase": progress.get("phase") if progress else None,
                "progress_percentage": progress.get("percentage", 0) if progress else 0,
                "current_site": progress.get("current_site") if progress else None,
                "current_table": progress.get("current_table") if progress else None,
                "sites_processed": execution.get("sites_processed", 0),
                "tables_processed": execution.get("tables_processed", 0),
                "total_sites_discovered": execution.get("total_sites_discovered", 0),
                "total_tables_discovered": execution.get("total_tables_discovered", 0)
            }

            logger.info(f"Retrieved current execution: {current_execution['migration_id']} - {current_execution['current_phase']} - {current_execution['progress_percentage']}%")
            return current_execution

        except Exception as e:
            logger.error(f"Failed to get current execution: {e}")
            return {
                "is_running": False,
                "migration_id": None,
                "started_at": None,
                "elapsed_time_seconds": 0,
                "current_phase": None,
                "progress_percentage": 0,
                "current_site": None,
                "current_table": None,
                "sites_processed": 0,
                "tables_processed": 0,
                "total_sites_discovered": 0,
                "total_tables_discovered": 0,
                "error": str(e)
            }
