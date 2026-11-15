"""
Custom logging configuration with service-specific prefixes.

This module provides a custom JSON formatter that automatically adds service
prefixes to log messages based on the module name, making it easier to identify
which service generated each log entry.

Service Prefixes:
- [CLICKHOUSE] - ClickHouse database operations
- [SPARK] - Apache Spark processing
- [REDIS] - Redis cache operations
- [ADLS] - Azure Data Lake Storage operations
- [API] - REST API endpoints and controllers
- [AUTH] - Authentication and authorization
- [SCHEDULER] - Background task scheduling
- [DJANGO] - Django framework logs
- [APP] - General application logs
"""

import logging
from pythonjsonlogger import jsonlogger


# Service prefix mapping based on module paths
SERVICE_PREFIX_MAP = {
    # ClickHouse related
    "clickhouse": "CLICKHOUSE",
    "clickhouse_connector": "CLICKHOUSE",
    "optimized_clickhouse_connector": "CLICKHOUSE",
    "clickhouseRepository": "CLICKHOUSE",
    "clickhouse_adls_service": "CLICKHOUSE",
    # Spark related
    "spark": "SPARK",
    "sparkRepository": "SPARK",
    "sparkSqlRepository": "SPARK",
    "spark_singleton": "SPARK",
    "spark_connection_manager": "SPARK",
    "pyarrowParallelProcessor": "SPARK",
    # Redis/Cache related
    "redis": "REDIS",
    "cache_service": "REDIS",
    "cache_decorators": "REDIS",
    "cache_helpers": "REDIS",
    "redis_cache_config": "REDIS",
    "scheduler_cache": "REDIS",
    # Azure/ADLS related
    "azure": "ADLS",
    "adls": "ADLS",
    "databricks": "ADLS",
    "databricks_connector": "ADLS",
    "azureConfig": "ADLS",
    # API/Controllers related
    "controllers": "API",
    "controller": "API",
    "views": "API",
    # Authentication related
    "auth": "AUTH",
    "jwt": "AUTH",
    "jwtService": "AUTH",
    "jwt_middleware": "AUTH",
    "roles": "AUTH",
    "permissions": "AUTH",
    # Scheduler related
    "scheduler": "SCHEDULER",
    "apscheduler": "SCHEDULER",
    # Django framework
    "django": "DJANGO",
    # Infrastructure app
    "infrastructure.apps": "APP",
    # Services (default for other services)
    "services": "SERVICE",
    # Middleware
    "middleware": "MIDDLEWARE",
}

# Parent module prefixes (for hierarchical matching)
PARENT_PREFIX_MAP = {
    "infrastructure.services.clickhouse": "CLICKHOUSE",
    "infrastructure.services.cache": "REDIS",
    "infrastructure.services.spark": "SPARK",
    "infrastructure.services.analysis": "SPARK",
    "infrastructure.controllers": "API",
    "infrastructure.middleware": "MIDDLEWARE",
    "infrastructure.applevel": "AUTH",
    "config.clickhouse": "CLICKHOUSE",
    "config.redis": "REDIS",
    "config.azure": "ADLS",
    "config.databricks": "ADLS",
    "config.spark": "SPARK",
}


def get_service_prefix(logger_name: str) -> str:
    """
    Determine the service prefix based on the logger name (module path).

    Args:
        logger_name: The name of the logger (usually __name__ of the module)

    Returns:
        Service prefix string (e.g., "CLICKHOUSE", "SPARK", "API")
    """
    if not logger_name:
        return "APP"

    # Check for exact parent path matches first
    for parent_path, prefix in PARENT_PREFIX_MAP.items():
        if logger_name.startswith(parent_path):
            return prefix

    # Extract the module name from the full path
    parts = logger_name.split(".")
    module_name = parts[-1] if parts else logger_name

    # Check for exact module name matches
    if module_name in SERVICE_PREFIX_MAP:
        return SERVICE_PREFIX_MAP[module_name]

    # Check if any part of the path matches
    for part in reversed(parts):
        if part in SERVICE_PREFIX_MAP:
            return SERVICE_PREFIX_MAP[part]

    # Default prefix
    return "APP"


class ServicePrefixJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds a service prefix to all log messages.

    This formatter extends pythonjsonlogger's JsonFormatter to automatically
    prepend a service identifier to each log message, making it easier to
    filter and identify logs from different services in a unified log stream.

    Example output:
    {
        "asctime": "2025-12-10 10:30:00,123",
        "levelname": "INFO",
        "message": "[CLICKHOUSE] Successfully connected to database",
        "service": "CLICKHOUSE",
        "logger": "infrastructure.services.clickhouse"
    }
    """

    def add_fields(self, log_record, record, message_dict):
        """Add service prefix and additional fields to the log record."""
        super().add_fields(log_record, record, message_dict)

        # Get the service prefix based on the logger name
        service_prefix = get_service_prefix(record.name)

        # Add service field for filtering
        log_record["service"] = service_prefix
        log_record["logger"] = record.name

        # Prepend service prefix to message if not already present
        message = log_record.get("message", "")
        if message and not message.startswith(f"[{service_prefix}]"):
            # Check if message already has any bracket prefix
            if not (message.startswith("[") and "]" in message[:30]):
                log_record["message"] = f"[{service_prefix}] {message}"


class ServicePrefixFormatter(logging.Formatter):
    """
    Standard (non-JSON) formatter with service prefixes.

    Use this formatter for development when you prefer human-readable logs
    instead of JSON format.

    Example output:
    2025-12-10 10:30:00,123 INFO [CLICKHOUSE] Successfully connected to database
    """

    def format(self, record):
        # Get the service prefix
        service_prefix = get_service_prefix(record.name)

        # Prepend prefix to message if not already present
        original_msg = record.msg
        if isinstance(original_msg, str) and not original_msg.startswith(f"[{service_prefix}]"):
            if not (original_msg.startswith("[") and "]" in original_msg[:30]):
                record.msg = f"[{service_prefix}] {original_msg}"

        result = super().format(record)

        # Restore original message to avoid mutation
        record.msg = original_msg
        return result


# Pre-configured formatters for easy use in settings.py
LOGGING_FORMATTERS = {
    "service_json": {
        "()": "infrastructure.utils.logging_config.ServicePrefixJsonFormatter",
        "format": "%(asctime)s %(levelname)s %(message)s",
    },
    "service_standard": {
        "()": "infrastructure.utils.logging_config.ServicePrefixFormatter",
        "format": "%(asctime)s %(levelname)s %(message)s",
    },
}


def get_logging_config(
    use_json: bool = True,
    log_level: str = "INFO",
    log_file: str = None,
) -> dict:
    """
    Get a complete logging configuration dictionary with service prefixes.

    Args:
        use_json: If True, use JSON formatter; otherwise use standard formatter
        log_level: The root logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file (optional)

    Returns:
        Dictionary suitable for Django's LOGGING setting
    """
    formatter_name = "service_json" if use_json else "service_standard"

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": formatter_name,
        },
    }

    if log_file:
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": log_file,
            "formatter": formatter_name,
        }

    handler_list = list(handlers.keys())

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": LOGGING_FORMATTERS,
        "handlers": handlers,
        "root": {
            "handlers": handler_list,
            "level": log_level,
        },
        "loggers": {
            # Django framework
            "django": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            "django.request": {
                "handlers": handler_list,
                "level": "ERROR",
                "propagate": False,
            },
            # ClickHouse
            "infrastructure.services.clickhouse": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            "infrastructure.orm.repositories.clickhouseRepository": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            "config.clickhouse_connector": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            # Spark
            "infrastructure.services.spark_singleton": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            "infrastructure.orm.repositories.sparkRepository": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            "infrastructure.orm.repositories.sparkSqlRepository": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            # Redis/Cache
            "infrastructure.services.cache_service": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            "infrastructure.utils.cache_decorators": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            # API/Controllers
            "infrastructure.controllers": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            # Authentication
            "infrastructure.middleware.jwt_middleware": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            "infrastructure.applevel.jwtService": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
            # Scheduler
            "infrastructure.utils.scheduler": {
                "handlers": handler_list,
                "level": log_level,
                "propagate": False,
            },
        },
    }
