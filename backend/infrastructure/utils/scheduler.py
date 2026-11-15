"""
APScheduler configuration for scheduled tasks.
Runs migration command every 1 hour (Asia/Dubai timezone).

Features:
- Exponential backoff retry for failed migrations
- Failed table priority retry mechanism
- Comprehensive error tracking and recovery
- Pipeline resilience - never stops under any circumstances
"""
import logging
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from django.core.management import call_command
from django.conf import settings

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 5
INITIAL_RETRY_DELAY_SECONDS = 60  # 1 minute
MAX_RETRY_DELAY_SECONDS = 1800  # 30 minutes
BACKOFF_MULTIPLIER = 2

# Track migration state
_migration_state: Dict[str, Any] = {
    'consecutive_failures': 0,
    'last_success': None,
    'last_failure': None,
    'retry_scheduled': False,
    'total_runs': 0,
    'successful_runs': 0,
    'failed_runs': 0,
}
_state_lock = threading.Lock()


def get_migration_state() -> Dict[str, Any]:
    """Get current migration state for monitoring."""
    with _state_lock:
        return _migration_state.copy()


def _calculate_backoff_delay(attempt: int) -> int:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: Current retry attempt (0-indexed)

    Returns:
        Delay in seconds
    """
    delay = min(
        INITIAL_RETRY_DELAY_SECONDS * (BACKOFF_MULTIPLIER ** attempt),
        MAX_RETRY_DELAY_SECONDS
    )
    # Add 10% jitter to prevent thundering herd
    jitter = delay * 0.1 * random.random()
    return int(delay + jitter)


def run_adls_migration(is_retry: bool = False, retry_attempt: int = 0):
    """
    Execute the ADLS to ClickHouse migration command with retry support.

    Runs with optimized settings for incremental migration with schema evolution,
    partitioning, and file validation.

    Args:
        is_retry: Whether this is a retry attempt
        retry_attempt: Current retry attempt number (0-indexed)
    """
    global _migration_state

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    with _state_lock:
        _migration_state['total_runs'] += 1
        _migration_state['retry_scheduled'] = False

    try:
        if is_retry:
            logger.info(f"[{run_id}] Starting RETRY attempt {retry_attempt + 1}/{MAX_RETRIES} "
                       f"for ADLS to ClickHouse migration")
        else:
            logger.info(f"[{run_id}] Starting scheduled ADLS to ClickHouse migration")

        # Run the migration command with optimized settings
        call_command(
            'migrate_adls_to_clickhouse',
            '--incremental',              # Incremental migration with file-level tracking
            '--skip-hash-check',          # Use size+date for performance (faster)
            '--enable-partitioning',      # Enable time-based partitioning for efficiency
            '--validate-parquet-magic',   # Validate parquet files to prevent errors
            '--force',                    # Auto-rebuild tables when schema changes detected
        )

        # Success - reset failure counter
        with _state_lock:
            _migration_state['consecutive_failures'] = 0
            _migration_state['last_success'] = datetime.now()
            _migration_state['successful_runs'] += 1

        logger.info(f"[{run_id}] Scheduled ADLS to ClickHouse migration completed successfully")

    except Exception as e:
        with _state_lock:
            _migration_state['consecutive_failures'] += 1
            _migration_state['last_failure'] = datetime.now()
            _migration_state['failed_runs'] += 1
            failures = _migration_state['consecutive_failures']

        logger.error(f"[{run_id}] Error in scheduled ADLS migration (failure #{failures}): {e}",
                    exc_info=True)

        # Schedule retry with exponential backoff if under retry limit
        if retry_attempt < MAX_RETRIES - 1:
            _schedule_retry(retry_attempt + 1)
        else:
            logger.error(f"[{run_id}] Max retries ({MAX_RETRIES}) exhausted. "
                        "Migration will retry on next scheduled run.")
            # Even after max retries, the hourly schedule will continue
            # This ensures pipeline never stops permanently


def _schedule_retry(retry_attempt: int):
    """
    Schedule a retry with exponential backoff.

    Args:
        retry_attempt: The retry attempt number to schedule
    """
    global _migration_state

    with _state_lock:
        if _migration_state['retry_scheduled']:
            logger.debug("Retry already scheduled, skipping")
            return
        _migration_state['retry_scheduled'] = True

    delay_seconds = _calculate_backoff_delay(retry_attempt)
    retry_time = datetime.now() + timedelta(seconds=delay_seconds)

    logger.info(f"Scheduling retry attempt {retry_attempt + 1}/{MAX_RETRIES} "
               f"in {delay_seconds} seconds (at {retry_time.strftime('%H:%M:%S')})")

    # Get the scheduler instance
    from infrastructure.utils.scheduler import _scheduler_instance
    if _scheduler_instance and _scheduler_instance.running:
        try:
            _scheduler_instance.add_job(
                run_adls_migration,
                trigger=DateTrigger(run_date=retry_time, timezone='Asia/Dubai'),
                id=f'adls_migration_retry_{retry_attempt}',
                name=f'ADLS Migration Retry {retry_attempt + 1}',
                replace_existing=True,
                kwargs={'is_retry': True, 'retry_attempt': retry_attempt}
            )
            logger.info(f"Retry job scheduled successfully for {retry_time}")
        except Exception as e:
            logger.error(f"Failed to schedule retry job: {e}")
            with _state_lock:
                _migration_state['retry_scheduled'] = False
    else:
        logger.warning("Scheduler not available for retry scheduling")
        with _state_lock:
            _migration_state['retry_scheduled'] = False


def run_failed_tables_migration():
    """
    Priority retry for failed tables.

    This function specifically targets tables that failed in previous migrations,
    attempting to recover them without waiting for the next full migration cycle.
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        logger.info(f"[{run_id}] Starting failed tables priority migration")

        # Run migration with retry-failed flag to prioritize failed tables
        call_command(
            'migrate_adls_to_clickhouse',
            '--incremental',
            '--skip-hash-check',
            '--enable-partitioning',
            '--validate-parquet-magic',
            '--force',                    # Auto-rebuild tables when schema changes detected
            '--retry-failed',             # Priority flag for failed tables
        )

        logger.info(f"[{run_id}] Failed tables priority migration completed")

    except Exception as e:
        logger.error(f"[{run_id}] Error in failed tables migration: {e}", exc_info=True)
        # Don't retry here - the main hourly job will pick up any remaining failures


# Global scheduler instance for retry scheduling
_scheduler_instance: BackgroundScheduler = None


def start_scheduler():
    """
    Initialize and start the APScheduler background scheduler.

    Features:
    - Hourly migration job
    - 15-minute failed tables retry job
    - Global instance for retry scheduling

    Returns:
        scheduler: The BackgroundScheduler instance, or None if disabled
    """
    global _scheduler_instance

    # Only run scheduler if explicitly enabled
    if not getattr(settings, 'ENABLE_SCHEDULER', False):
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=False or not set)")
        return None

    try:
        # Create scheduler with Dubai timezone (GST/UTC+4)
        scheduler = BackgroundScheduler(
            timezone='Asia/Dubai',
            job_defaults={
                'coalesce': True,  # Combine multiple pending executions of same job
                'max_instances': 1,  # Only one instance of job can run at a time
                'misfire_grace_time': 3600  # If missed, still run if within 1 hour
            }
        )

        # Store global instance for retry scheduling
        _scheduler_instance = scheduler

        # Schedule main migration every 1 hour
        scheduler.add_job(
            run_adls_migration,
            trigger=IntervalTrigger(
                hours=1,
                timezone='Asia/Dubai'
            ),
            id='adls_migration_hourly',
            name='ADLS to ClickHouse Hourly Migration',
            replace_existing=True
        )

        # Schedule failed tables retry every 15 minutes
        # This runs more frequently to quickly recover failed tables
        scheduler.add_job(
            run_failed_tables_migration,
            trigger=IntervalTrigger(
                minutes=15,
                timezone='Asia/Dubai'
            ),
            id='adls_failed_tables_retry',
            name='ADLS Failed Tables Priority Retry',
            replace_existing=True
        )

        # Start the scheduler
        scheduler.start()

        logger.info("APScheduler started successfully with enhanced retry support")
        logger.info("- Main migration: every 1 hour")
        logger.info("- Failed tables retry: every 15 minutes")
        logger.info("- Exponential backoff: up to 5 retries per failure")

        main_job = scheduler.get_job('adls_migration_hourly')
        retry_job = scheduler.get_job('adls_failed_tables_retry')

        if main_job:
            logger.info(f"Next main migration: {main_job.next_run_time}")
        if retry_job:
            logger.info(f"Next failed tables check: {retry_job.next_run_time}")

        return scheduler

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        return None


def stop_scheduler(scheduler=None):
    """
    Gracefully shutdown the scheduler.

    Args:
        scheduler: The BackgroundScheduler instance to stop (optional, uses global if not provided)
    """
    global _scheduler_instance

    target_scheduler = scheduler or _scheduler_instance

    if target_scheduler and target_scheduler.running:
        try:
            target_scheduler.shutdown(wait=True)
            _scheduler_instance = None
            logger.info("Scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")