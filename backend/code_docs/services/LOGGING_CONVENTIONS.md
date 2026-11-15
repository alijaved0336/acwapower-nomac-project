# Logging Conventions Documentation

## Overview

This document provides comprehensive documentation for the logging conventions used in the SWRO Backend project. All logs are automatically prefixed with their service name, making it easy to filter and identify logs from different services when streaming to a unified terminal or log aggregator.

## Architecture Overview

The logging system follows a custom formatter approach:

1. **Configuration Layer** (`nomac/settings.py`) - Django LOGGING configuration
2. **Utility Layer** (`infrastructure/utils/logging_config.py`) - Custom formatters and service prefix mapping
3. **Service Layer** - Individual services using standard Python logging

## File Structure

```
├── nomac/
│   └── settings.py                          # Django LOGGING configuration
├── infrastructure/
│   └── utils/
│       └── logging_config.py                # Custom formatters and prefix mapping
└── logs/
    └── django.log                           # Application log file (JSON format)
```

---

## Service Prefixes

All logs are automatically prefixed based on the module they originate from:

| Prefix | Description | Example Modules |
|--------|-------------|-----------------|
| `[CLICKHOUSE]` | ClickHouse database operations | `clickhouse.py`, `clickhouseRepository.py`, `clickhouse_connector.py` |
| `[SPARK]` | Apache Spark processing | `spark_singleton.py`, `sparkRepository.py`, `sparkSqlRepository.py` |
| `[REDIS]` | Redis cache operations | `cache_service.py`, `cache_decorators.py`, `redis_cache_config.py` |
| `[ADLS]` | Azure Data Lake Storage | `clickhouse_adls_service.py`, `azureConfig.py`, `databricks_connector.py` |
| `[API]` | REST API endpoints | `controllers/*`, `views.py` |
| `[AUTH]` | Authentication/Authorization | `jwt_middleware.py`, `jwtService.py`, `roles.py` |
| `[SCHEDULER]` | Background task scheduling | `scheduler.py`, APScheduler-related modules |
| `[DJANGO]` | Django framework logs | `django.*` modules |
| `[MIDDLEWARE]` | Request/response middleware | `middleware/*` |
| `[SERVICE]` | Generic service logs | Other service modules |
| `[APP]` | General application logs | Default for unmatched modules |

---

## Log Output Format

### JSON Format (Default)

All logs are output in JSON format for easy parsing and log aggregation:

```json
{
  "asctime": "2025-12-10 10:30:00,123",
  "levelname": "INFO",
  "message": "[CLICKHOUSE] Successfully connected to database",
  "service": "CLICKHOUSE",
  "logger": "config.clickhouse_connector"
}
```

**Fields:**
- `asctime` - Timestamp of the log entry
- `levelname` - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message` - Log message with service prefix
- `service` - Service identifier for filtering
- `logger` - Full module path of the logger

### Standard Format (Alternative)

For development, a human-readable format is also available:

```
2025-12-10 10:30:00,123 INFO [CLICKHOUSE] Successfully connected to database
```

---

## Usage Guidelines

### Basic Logging

Use standard Python logging - prefixes are added automatically:

```python
import logging

logger = logging.getLogger(__name__)

# These will be automatically prefixed based on module location
logger.info("Connected to database")      # → "[CLICKHOUSE] Connected to database"
logger.warning("Cache miss")              # → "[REDIS] Cache miss"
logger.error("Query failed", exc_info=True)
```

### Log Levels

Use appropriate log levels:

| Level | Use Case |
|-------|----------|
| `DEBUG` | Detailed debugging info (connection attempts, date conversions) |
| `INFO` | General informational messages (initialization, successful operations) |
| `WARNING` | Non-critical issues, fallbacks, missing optional data |
| `ERROR` | Failures, exceptions (use `exc_info=True` for stack traces) |
| `CRITICAL` | System-level failures requiring immediate attention |

### Best Practices

1. **Always use `__name__` for logger creation:**
   ```python
   logger = logging.getLogger(__name__)
   ```

2. **Include context in error logs:**
   ```python
   logger.error(f"Failed to process site {site_id}: {e}", exc_info=True)
   ```

3. **Use parameterized logging for performance:**
   ```python
   logger.debug("Processing %s records for site %s", count, site_id)
   ```

4. **Don't add manual prefixes** - the formatter handles this automatically:
   ```python
   # Good
   logger.info("Connected to database")

   # Unnecessary (prefix will be duplicated)
   logger.info("[CLICKHOUSE] Connected to database")
   ```

5. **Redact sensitive information:**
   ```python
   # Good - redact auth headers
   sanitized_headers = {k: ("<redacted>" if k.lower() == "authorization" else v)
                        for k, v in headers.items()}
   logger.debug("Request headers: %s", sanitized_headers)
   ```

---

## Configuration

### Django Settings (`nomac/settings.py`)

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "service_json": {
            "()": "infrastructure.utils.logging_config.ServicePrefixJsonFormatter",
            "format": "%(asctime)s %(levelname)s %(message)s",
        },
        "service_standard": {
            "()": "infrastructure.utils.logging_config.ServicePrefixFormatter",
            "format": "%(asctime)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "service_json",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs/django.log",
            "formatter": "service_json",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        # Service-specific loggers are configured here
        # See settings.py for full configuration
    },
}
```

### Switching to Standard Format

To use human-readable logs during development, change the formatter in handlers:

```python
"handlers": {
    "console": {
        "class": "logging.StreamHandler",
        "stream": sys.stdout,
        "formatter": "service_standard",  # Changed from "service_json"
    },
}
```

---

## Adding New Service Prefixes

To add a new service prefix, update `infrastructure/utils/logging_config.py`:

### 1. Add to `SERVICE_PREFIX_MAP`

```python
SERVICE_PREFIX_MAP = {
    # ... existing mappings
    "my_new_service": "NEWSERVICE",
    "my_new_repository": "NEWSERVICE",
}
```

### 2. Add to `PARENT_PREFIX_MAP` (for hierarchical matching)

```python
PARENT_PREFIX_MAP = {
    # ... existing mappings
    "infrastructure.services.my_new_service": "NEWSERVICE",
}
```

### 3. Add logger to Django settings (optional)

```python
"loggers": {
    # ... existing loggers
    "infrastructure.services.my_new_service": {
        "handlers": ["console", "file"],
        "level": "INFO",
        "propagate": False,
    },
}
```

---

## Filtering Logs

### By Service Prefix

Filter logs by service using grep or log aggregator queries:

```bash
# Filter ClickHouse logs
grep '"service": "CLICKHOUSE"' logs/django.log

# Filter API logs
grep '\[API\]' logs/django.log

# Multiple services
grep -E '"service": "(CLICKHOUSE|SPARK)"' logs/django.log
```

### By Log Level

```bash
# Errors only
grep '"levelname": "ERROR"' logs/django.log

# Warnings and above
grep -E '"levelname": "(WARNING|ERROR|CRITICAL)"' logs/django.log
```

### In Docker

```bash
# Filter Django container logs by service
make logs-django | grep '\[CLICKHOUSE\]'

# Real-time filtering
docker-compose logs -f django | grep '\[SPARK\]'
```

---

## Troubleshooting

### Logs Not Showing Prefix

1. Ensure the module is using `logging.getLogger(__name__)`
2. Check if the module path is mapped in `SERVICE_PREFIX_MAP` or `PARENT_PREFIX_MAP`
3. Verify the formatter is correctly configured in `settings.py`

### Duplicate Prefixes

The formatter automatically detects existing bracket prefixes (e.g., `[CUSTOM]`) and won't add another. If you see duplicates:
- Remove manual prefixes from log messages
- Let the formatter handle prefixing automatically

### Missing Logs

1. Check the log level configuration (default is INFO)
2. Verify the logger has `propagate: False` if it has its own handlers
3. Ensure the logs directory exists: `mkdir -p logs/`

---

## Related Documentation

- [Cache Service Documentation](./CACHE_SERVICE_DOCUMENTATION.md) - Redis caching details
- [ClickHouse Documentation](./CLICKHOUSE_DOCUMENTATION.md) - Database operations
- [Developer Session Guide](../development/DEVELOPER_SESSION_GUIDE.md) - General development practices
