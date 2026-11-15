"""
OpenAPI/Swagger schemas for scheduler monitoring endpoint.
Defines response structure for comprehensive scheduler monitoring data.
"""
from drf_yasg import openapi

# Scheduler Status Schema
scheduler_status_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "is_enabled": openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description="Whether the scheduler is enabled"
        ),
        "is_running": openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description="Whether the scheduler is currently running"
        ),
        "job_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="APScheduler job ID",
            nullable=True
        ),
        "job_name": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Human-readable job name",
            nullable=True
        ),
        "next_run_time": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Next scheduled run time (ISO format)",
            nullable=True
        ),
        "trigger_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Type of trigger (e.g., IntervalTrigger)",
            nullable=True
        ),
        "trigger_interval": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Human-readable trigger interval (e.g., '1 hour')",
            nullable=True
        ),
        "timezone": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Timezone for scheduler (e.g., 'Asia/Dubai')",
            nullable=True
        ),
    },
)

# Current Execution Schema
current_execution_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "is_running": openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description="Whether a migration is currently running"
        ),
        "migration_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Unique identifier for current migration",
            nullable=True
        ),
        "started_at": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="When the current migration started (ISO format)",
            nullable=True
        ),
        "elapsed_time_seconds": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Elapsed time in seconds since migration started"
        ),
        "current_phase": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Current migration phase (discovering, schema_creation, data_migration, completed)",
            nullable=True
        ),
        "progress_percentage": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description="Estimated progress percentage (0-100)"
        ),
        "current_site": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Site currently being processed",
            nullable=True
        ),
        "current_table": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Table currently being processed",
            nullable=True
        ),
        "sites_processed": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of sites processed so far"
        ),
        "tables_processed": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of tables processed so far"
        ),
        "total_sites_discovered": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Total number of sites discovered"
        ),
        "total_tables_discovered": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Total number of tables discovered"
        ),
    },
)

# Statistics Schema
statistics_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "total_executions_24h": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Total number of executions in last 24 hours"
        ),
        "successful_executions": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of successful executions"
        ),
        "failed_executions": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of failed executions"
        ),
        "success_rate_percentage": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description="Success rate as percentage (0-100)"
        ),
        "average_duration_seconds": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Average duration of successful executions in seconds"
        ),
        "last_successful_run": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Timestamp of last successful run",
            nullable=True
        ),
        "last_failed_run": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Timestamp of last failed run",
            nullable=True
        ),
    },
)

# Latest Migration Schema
latest_migration_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "migration_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Unique identifier for migration"
        ),
        "status": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Migration status (started, completed, failed)"
        ),
        "command_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Type of migration command (incremental, full, etc.)"
        ),
        "base_paths": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Base paths scanned during migration"
        ),
        "started_at": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="When migration started"
        ),
        "completed_at": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="When migration completed",
            nullable=True
        ),
        "duration_seconds": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Duration in seconds",
            nullable=True
        ),
        "sites_processed": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of sites processed"
        ),
        "tables_processed": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of tables processed"
        ),
        "rows_migrated": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Total rows migrated"
        ),
        "error_message": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Error message if migration failed",
            nullable=True
        ),
    },
    nullable=True
)

# Recent Error Schema
error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "migration_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Migration identifier"
        ),
        "timestamp": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="When the error occurred"
        ),
        "error_message": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Error message"
        ),
        "command_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Type of migration command that failed"
        ),
    },
)

# File Statistics Schema
file_statistics_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "total_files_tracked": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Total number of files being tracked"
        ),
        "files_imported_successfully": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of files imported successfully"
        ),
        "files_failed": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of files that failed to import"
        ),
        "files_pending": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description="Number of files pending import"
        ),
        "last_file_update": openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Timestamp of last file update",
            nullable=True
        ),
    },
)

# Complete Monitoring Response Schema
scheduler_monitoring_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "success": openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description="Whether the request was successful"
        ),
        "message": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Response message"
        ),
        "data": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "scheduler_status": scheduler_status_schema,
                "current_execution": current_execution_schema,
                "statistics": statistics_schema,
                "latest_migration": latest_migration_schema,
                "recent_errors": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=error_schema,
                    description="List of recent errors (up to 10)"
                ),
                "file_statistics": file_statistics_schema,
            },
        ),
    },
)
