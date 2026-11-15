"""
Cache utility for tracking scheduler migration progress in real-time.
Uses Django's Redis cache to store current execution state and progress.
"""
import logging
from django.core.cache import cache
from typing import Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SchedulerCache:
    """
    Manages Redis cache for scheduler monitoring.
    Tracks current migration execution and progress in real-time.
    """

    # Cache key constants
    CURRENT_EXECUTION_KEY = "scheduler:migration:current_execution"
    PROGRESS_KEY = "scheduler:migration:progress"

    # Cache TTL (2 hours - longer than migration interval)
    TTL = 7200

    @staticmethod
    def set_current_execution(migration_id: str, started_at: datetime, command_type: str = "incremental"):
        """
        Mark migration as currently running.

        Args:
            migration_id: Unique identifier for this migration run
            started_at: When the migration started
            command_type: Type of migration (incremental, full, etc.)
        """
        try:
            execution_data = {
                "is_running": True,
                "migration_id": migration_id,
                "started_at": started_at.isoformat(),
                "command_type": command_type,
                "sites_processed": 0,
                "tables_processed": 0,
                "total_sites_discovered": 0,
                "total_tables_discovered": 0,
            }
            cache.set(
                SchedulerCache.CURRENT_EXECUTION_KEY,
                json.dumps(execution_data),
                timeout=SchedulerCache.TTL
            )

            # Initialize progress
            progress_data = {
                "phase": "initializing",
                "percentage": 0,
                "current_site": None,
                "current_table": None,
            }
            cache.set(
                SchedulerCache.PROGRESS_KEY,
                json.dumps(progress_data),
                timeout=SchedulerCache.TTL
            )

            logger.info(f"[SCHEDULER_CACHE] Set current execution: {migration_id}")

        except Exception as e:
            logger.error(f"[SCHEDULER_CACHE] Failed to set current execution: {e}")

    @staticmethod
    def get_current_execution() -> Optional[Dict]:
        """
        Get current running migration information.

        Returns:
            Dict with execution info, or None if no migration is running
        """
        try:
            execution_json = cache.get(SchedulerCache.CURRENT_EXECUTION_KEY)
            if execution_json:
                return json.loads(execution_json)
            return None

        except Exception as e:
            logger.error(f"[SCHEDULER_CACHE] Failed to get current execution: {e}")
            return None

    @staticmethod
    def update_progress(
        phase: str,
        percentage: float,
        details: Optional[Dict] = None
    ):
        """
        Update migration progress.

        Args:
            phase: Current phase (discovering, schema_creation, data_migration, completed)
            percentage: Estimated progress percentage (0-100)
            details: Optional dict with additional details (current_site, current_table, etc.)
        """
        try:
            progress_data = {
                "phase": phase,
                "percentage": min(100, max(0, percentage)),  # Clamp between 0-100
            }

            # Add optional details
            if details:
                progress_data.update(details)

            cache.set(
                SchedulerCache.PROGRESS_KEY,
                json.dumps(progress_data),
                timeout=SchedulerCache.TTL
            )

            # Also update execution data if provided
            if details:
                execution_data = SchedulerCache.get_current_execution()
                if execution_data:
                    # Update sites/tables processed
                    if "sites_processed" in details:
                        execution_data["sites_processed"] = details["sites_processed"]
                    if "tables_processed" in details:
                        execution_data["tables_processed"] = details["tables_processed"]
                    if "total_sites_discovered" in details:
                        execution_data["total_sites_discovered"] = details["total_sites_discovered"]
                    if "total_tables_discovered" in details:
                        execution_data["total_tables_discovered"] = details["total_tables_discovered"]

                    cache.set(
                        SchedulerCache.CURRENT_EXECUTION_KEY,
                        json.dumps(execution_data),
                        timeout=SchedulerCache.TTL
                    )

            logger.debug(f"[SCHEDULER_CACHE] Updated progress: {phase} - {percentage}%")

        except Exception as e:
            logger.error(f"[SCHEDULER_CACHE] Failed to update progress: {e}")

    @staticmethod
    def get_progress() -> Optional[Dict]:
        """
        Get current migration progress.

        Returns:
            Dict with progress info, or None if not available
        """
        try:
            progress_json = cache.get(SchedulerCache.PROGRESS_KEY)
            if progress_json:
                return json.loads(progress_json)
            return None

        except Exception as e:
            logger.error(f"[SCHEDULER_CACHE] Failed to get progress: {e}")
            return None

    @staticmethod
    def clear_execution():
        """
        Clear current execution on completion or error.
        Marks migration as not running.
        """
        try:
            execution_data = SchedulerCache.get_current_execution()
            if execution_data:
                execution_data["is_running"] = False
                cache.set(
                    SchedulerCache.CURRENT_EXECUTION_KEY,
                    json.dumps(execution_data),
                    timeout=300  # Keep for 5 minutes after completion
                )

                logger.info(f"[SCHEDULER_CACHE] Cleared execution: {execution_data.get('migration_id')}")

        except Exception as e:
            logger.error(f"[SCHEDULER_CACHE] Failed to clear execution: {e}")

    @staticmethod
    def get_elapsed_time_seconds() -> int:
        """
        Calculate elapsed time of current execution.

        Returns:
            Elapsed seconds, or 0 if no execution is running
        """
        try:
            execution = SchedulerCache.get_current_execution()
            if execution and execution.get("is_running") and execution.get("started_at"):
                started_at = datetime.fromisoformat(execution["started_at"])
                elapsed = (datetime.now() - started_at).total_seconds()
                return int(elapsed)
            return 0

        except Exception as e:
            logger.error(f"[SCHEDULER_CACHE] Failed to calculate elapsed time: {e}")
            return 0
