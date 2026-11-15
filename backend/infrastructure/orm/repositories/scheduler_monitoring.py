"""
Repository for scheduler monitoring data from ClickHouse.
Queries migration_log, parquet_file_tracking, and site_table_mapping tables.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import os

from config.clickhouse_connector import execute_clickhouse_query
from constants import ErrorMessages

logger = logging.getLogger(__name__)


class SchedulerMonitoringRepository:
    """
    Repository for retrieving scheduler and migration monitoring data from ClickHouse.
    """

    def __init__(self):
        """Initialize repository with database name."""
        self.database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')

    def get_migrations_by_timeframe(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get all migrations within the specified timeframe.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of migration records
        """
        try:
            query = f"""
            SELECT
                migration_id,
                command_type,
                base_paths,
                sites_processed,
                tables_processed,
                rows_migrated,
                status,
                error_message,
                started_at,
                completed_at
            FROM `{self.database}`.migration_log
            WHERE started_at >= now() - INTERVAL {{hours:UInt32}} HOUR
            ORDER BY started_at DESC
            """

            result = execute_clickhouse_query(query, params={"hours": hours})

            migrations = []
            for row in result.result_rows:
                migrations.append({
                    "migration_id": row[0],
                    "command_type": row[1],
                    "base_paths": row[2],
                    "sites_processed": row[3],
                    "tables_processed": row[4],
                    "rows_migrated": row[5],
                    "status": row[6],
                    "error_message": row[7],
                    "started_at": row[8],
                    "completed_at": row[9] if row[9] and row[9].year > 1970 else None
                })

            logger.info(f"Retrieved {len(migrations)} migrations from last {hours} hours")
            return migrations

        except Exception as e:
            logger.error(f"Failed to retrieve migrations by timeframe: {e}")
            return []

    def get_latest_migration(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent migration record.

        Returns:
            Latest migration record or None
        """
        try:
            query = f"""
            SELECT
                migration_id,
                command_type,
                base_paths,
                sites_processed,
                tables_processed,
                rows_migrated,
                status,
                error_message,
                started_at,
                completed_at
            FROM `{self.database}`.migration_log
            ORDER BY started_at DESC
            LIMIT 1
            """

            result = execute_clickhouse_query(query)

            if not result.result_rows:
                return None

            row = result.result_rows[0]

            # Calculate duration if both timestamps exist
            duration_seconds = None
            if row[9] and row[9].year > 1970 and row[8]:
                duration = row[9] - row[8]
                duration_seconds = int(duration.total_seconds())

            migration = {
                "migration_id": row[0],
                "command_type": row[1],
                "base_paths": row[2],
                "sites_processed": row[3],
                "tables_processed": row[4],
                "rows_migrated": row[5],
                "status": row[6],
                "error_message": row[7],
                "started_at": row[8],
                "completed_at": row[9] if row[9] and row[9].year > 1970 else None,
                "duration_seconds": duration_seconds
            }

            logger.info(f"Retrieved latest migration: {migration['migration_id']}")
            return migration

        except Exception as e:
            logger.error(f"Failed to retrieve latest migration: {e}")
            return None

    def get_migration_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Calculate aggregated statistics for migrations in timeframe.

        Args:
            hours: Number of hours to analyze (default: 24)

        Returns:
            Dict with statistics (total_executions, successful, failed, etc.)
        """
        try:
            query = f"""
            SELECT
                COUNT(*) as total_executions,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
                AVG(CASE
                    WHEN status = 'completed' AND completed_at > '1970-01-01 00:00:00'
                    THEN toUnixTimestamp(completed_at) - toUnixTimestamp(started_at)
                    ELSE NULL
                END) as avg_duration_seconds,
                MAX(CASE
                    WHEN status = 'completed' THEN started_at
                    ELSE NULL
                END) as last_successful_run,
                MAX(CASE
                    WHEN status = 'failed' THEN started_at
                    ELSE NULL
                END) as last_failed_run
            FROM `{self.database}`.migration_log
            WHERE started_at >= now() - INTERVAL {{hours:UInt32}} HOUR
            """

            result = execute_clickhouse_query(query, params={"hours": hours})

            if not result.result_rows:
                return self._get_empty_statistics()

            row = result.result_rows[0]
            total = row[0] or 0
            successful = row[1] or 0
            failed = row[2] or 0
            avg_duration = row[3]
            last_success = row[4]
            last_failure = row[5]

            # Calculate success rate
            success_rate = (successful / total * 100) if total > 0 else 0.0

            statistics = {
                "total_executions_24h": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate_percentage": round(success_rate, 2),
                "average_duration_seconds": int(avg_duration) if avg_duration else 0,
                "last_successful_run": last_success,
                "last_failed_run": last_failure
            }

            logger.info(f"Calculated migration statistics: {total} total, {successful} successful, {failed} failed")
            return statistics

        except Exception as e:
            logger.error(f"Failed to calculate migration statistics: {e}")
            return self._get_empty_statistics()

    def get_failed_migrations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent failed migrations for error reporting.

        Args:
            limit: Maximum number of errors to return (default: 10)

        Returns:
            List of failed migration records with error details
        """
        try:
            query = f"""
            SELECT
                migration_id,
                command_type,
                started_at,
                error_message
            FROM `{self.database}`.migration_log
            WHERE status = 'failed' AND error_message != ''
            ORDER BY started_at DESC
            LIMIT {{limit:UInt32}}
            """

            result = execute_clickhouse_query(query, params={"limit": limit})

            errors = []
            for row in result.result_rows:
                errors.append({
                    "migration_id": row[0],
                    "command_type": row[1],
                    "timestamp": row[2],
                    "error_message": row[3]
                })

            logger.info(f"Retrieved {len(errors)} recent failed migrations")
            return errors

        except Exception as e:
            logger.error(f"Failed to retrieve failed migrations: {e}")
            return []

    def get_file_tracking_stats(self) -> Dict[str, Any]:
        """
        Get statistics from parquet_file_tracking table.

        Returns:
            Dict with file tracking statistics
        """
        try:
            query = f"""
            SELECT
                COUNT(*) as total_files_tracked,
                COUNT(CASE WHEN import_status = 'imported' THEN 1 END) as files_imported_successfully,
                COUNT(CASE WHEN import_status = 'failed' THEN 1 END) as files_failed,
                COUNT(CASE WHEN import_status = 'pending' THEN 1 END) as files_pending,
                MAX(import_date) as last_file_update
            FROM `{self.database}`.parquet_file_tracking
            """

            result = execute_clickhouse_query(query)

            if not result.result_rows:
                return self._get_empty_file_stats()

            row = result.result_rows[0]

            stats = {
                "total_files_tracked": row[0] or 0,
                "files_imported_successfully": row[1] or 0,
                "files_failed": row[2] or 0,
                "files_pending": row[3] or 0,
                "last_file_update": row[4]
            }

            logger.info(f"Retrieved file tracking stats: {stats['total_files_tracked']} total files")
            return stats

        except Exception as e:
            logger.error(f"Failed to retrieve file tracking stats: {e}")
            return self._get_empty_file_stats()

    def _get_empty_statistics(self) -> Dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "total_executions_24h": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "success_rate_percentage": 0.0,
            "average_duration_seconds": 0,
            "last_successful_run": None,
            "last_failed_run": None
        }

    def _get_empty_file_stats(self) -> Dict[str, Any]:
        """Return empty file statistics structure."""
        return {
            "total_files_tracked": 0,
            "files_imported_successfully": 0,
            "files_failed": 0,
            "files_pending": 0,
            "last_file_update": None
        }
