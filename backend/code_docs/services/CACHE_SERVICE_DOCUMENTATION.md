# Redis Caching Service Documentation

## Overview

This document provides comprehensive documentation for the Redis caching service implemented in the SWRO Backend project. The caching service is designed to be standalone, reusable, and production-ready without affecting existing code until actively used.

## Architecture Overview

The caching service follows a three-layer architecture:

1. **Configuration Layer** (`config/`) - Redis connection and configuration management
2. **Service Layer** (`infrastructure/services/`) - Core caching operations and business logic
3. **Utility Layer** (`infrastructure/utils/`) - Decorators, helpers, and common utilities

## File Structure

```
├── config/
│   └── redis_cache_config.py          # Redis configuration and connection management
├── infrastructure/
│   ├── services/
│   │   └── cache_service.py            # Core caching service
│   └── utils/
│       └── cache_decorators.py         # Decorators and utility functions
└── code_docs/
        └── CACHE_SERVICE_DOCUMENTATION.md     # This documentation file
```

---

## Component Documentation

### 1. Configuration Layer

#### `config/redis_cache_config.py`

**Purpose**: Centralized Redis configuration management following the project's config pattern.

**Key Components**:

##### `CacheConfig` Class
Configuration constants and environment variable mappings.

```python
class CacheConfig:
    # TTL Constants
    DEFAULT_TTL = 300      # 5 minutes
    SHORT_TTL = 60         # 1 minute  
    MEDIUM_TTL = 900       # 15 minutes
    LONG_TTL = 3600        # 1 hour
    EXTRA_LONG_TTL = 86400 # 24 hours
    
    # Key Prefixes
    DEFAULT_PREFIX = "swro_cache"
    USER_PREFIX = "user"
    SESSION_PREFIX = "session"
    QUERY_PREFIX = "query"
    METADATA_PREFIX = "metadata"
```

**Environment Variables**:
- `REDIS_HOST` (default: "localhost")
- `REDIS_PORT` (default: "6379")
- `REDIS_DB` (default: "1")
- `REDIS_PASSWORD` (optional)
- `REDIS_MAX_CONNECTIONS` (default: "50")
- `REDIS_ENABLE_COMPRESSION` (default: "true")
- `REDIS_ENABLE_LOGGING` (default: "true")

##### Core Functions

**`get_redis_cache_config() -> Dict[str, Any]`**
- Returns Redis configuration dictionary
- Validates environment variables
- Raises `ValueError` if configuration is invalid

**`get_redis_cache_instance()`**
- Returns Django's configured cache instance
- Tests connection health
- Provides graceful degradation on connection failures

**`validate_cache_connection() -> bool`**
- Performs health check on Redis connection
- Tests basic operations (get/set/delete)
- Returns connection status

**`get_cache_stats() -> Dict[str, Any]`**
- Returns cache statistics and configuration info
- Includes connection health status
- Used for monitoring and debugging

---

### 2. Service Layer

#### `infrastructure/services/cache_service.py`

**Purpose**: Main caching service providing comprehensive Redis operations with error handling and type safety.

##### `CacheService` Class

**Initialization**:
```python
def __init__(self):
    """Initialize cache service with Redis connection"""
    # Attempts to connect to Redis
    # Falls back to disabled mode if connection fails
    # Logs initialization status
```

**Core Methods**:

##### Basic Operations

**`get(key: str, prefix: Optional[str] = None, default: Any = None) -> Any`**
- Retrieves value from cache
- Supports namespacing with prefixes
- Returns default value if key not found
- Automatic JSON deserialization

**`set(key: str, value: Any, ttl: Optional[int] = None, prefix: Optional[str] = None) -> bool`**
- Stores value in cache with optional TTL
- Automatic JSON serialization
- Returns success status
- Uses default TTL if not specified

**`delete(key: str, prefix: Optional[str] = None) -> bool`**
- Removes key from cache
- Supports prefixed keys
- Returns deletion status

##### Advanced Operations

**`get_or_set(key: str, fetch_func: Callable[[], Any], ttl: Optional[int] = None, prefix: Optional[str] = None) -> Any`**
- Cache-aside pattern implementation
- Gets from cache or executes fetch function
- Automatically caches result from fetch function
- Ideal for expensive operations

Example:
```python
cache = CacheService()
result = cache.get_or_set(
    "dashboard_kpis", 
    lambda: expensive_kpi_calculation(), 
    ttl=300
)
```

**`get_many(keys: List[str], prefix: Optional[str] = None) -> Dict[str, Any]`**
- Bulk get operation for multiple keys
- More efficient than multiple single gets
- Returns dictionary of found key-value pairs

**`set_many(data: Dict[str, Any], ttl: Optional[int] = None, prefix: Optional[str] = None) -> bool`**
- Bulk set operation for multiple key-value pairs
- Atomic operation where possible
- All keys get same TTL

**`delete_many(keys: List[str], prefix: Optional[str] = None) -> int`**
- Bulk delete operation
- Returns number of successfully deleted keys

##### Utility Methods

**`clear_prefix(prefix: str) -> bool`**
- Clears all cache entries with specific prefix
- Useful for invalidating related data
- Uses pattern matching where supported

**`generate_key_from_params(base_key: str, **params) -> str`**
- Generates consistent cache keys from parameters
- Handles long parameter lists with hashing
- Ensures key uniqueness based on parameters

**`get_cache_info() -> Dict[str, Any]`**
- Returns comprehensive cache service information
- Includes health status, configuration, and statistics
- Used for monitoring and debugging

##### Internal Methods

**`_generate_key(key: str, prefix: Optional[str] = None) -> str`**
- Internal key formatting with project prefix
- Ensures consistent key naming across application

**`_serialize_value(value: Any) -> str`**
- Handles JSON serialization with fallbacks
- Supports complex Python objects
- Graceful handling of non-serializable objects

**`_deserialize_value(value: str) -> Any`**
- Handles JSON deserialization with fallbacks
- Returns original types where possible
- Safe handling of corrupted cache data

---

### 3. Utility Layer

#### `infrastructure/utils/cache_decorators.py`

**Purpose**: Provides decorators and utility functions for common caching patterns.

##### Decorators

**`@cache_result`**
Function-level caching decorator.

```python
@cache_result(ttl=600, key_prefix="dashboard", include_args=True, include_kwargs=True)
def get_dashboard_data(user_id: str, filters: dict = None):
    return expensive_dashboard_calculation(user_id, filters)
```

**Parameters**:
- `ttl`: Time to live in seconds
- `key_prefix`: Namespace for cache keys  
- `include_args`: Include function arguments in key generation
- `include_kwargs`: Include keyword arguments in key generation
- `key_func`: Custom key generation function

**`@cache_method_result`**
Method-level caching decorator for class methods.

```python
class DataService:
    @cache_method_result(ttl=300, key_prefix="data", include_self=False)
    def get_expensive_data(self, param1: str):
        return expensive_operation(param1)
```

**Parameters**:
- All parameters from `@cache_result`
- `include_self`: Whether to include `self` object in key generation

**`@invalidate_cache`**
Cache invalidation decorator that clears cache after function execution.

```python
@invalidate_cache(key_pattern="user_*", prefix="dashboard")
def update_user_data(user_id: str):
    # Update user data in database
    pass
```

**Parameters**:
- `key_pattern`: Pattern of keys to invalidate (supports wildcards)
- `prefix`: Cache key prefix to target

**`@cache_lock`**
Distributed locking decorator to prevent concurrent execution.

```python
@cache_lock(lock_key="expensive_report_generation", timeout=600)
def generate_expensive_report():
    # Only one instance can run at a time
    return generate_report()
```

**Parameters**:
- `lock_key`: Unique identifier for the lock
- `timeout`: Lock timeout in seconds
- `prefix`: Optional prefix for lock key

##### Utility Classes

**`CacheUtils`**
Static utility class for advanced caching operations.

**`CacheUtils.warm_cache(cache_configs: List[Dict[str, Any]]) -> Dict[str, bool]`**
Pre-populate cache with predefined data.

```python
configs = [
    {"key": "config_data", "value": config_dict, "ttl": 3600},
    {"key": "user_roles", "value": roles_list, "ttl": 1800, "prefix": "auth"}
]
results = CacheUtils.warm_cache(configs)
```

**`CacheUtils.clear_cache_by_pattern(pattern: str, prefix: Optional[str] = None) -> bool`**
Clear cache entries matching a pattern.

```python
# Clear all user-related cache entries
CacheUtils.clear_cache_by_pattern("user_*", prefix="dashboard")
```

**`CacheUtils.get_cache_health() -> Dict[str, Any]`**
Get comprehensive cache health information.

**`CacheUtils.create_time_based_key(base_key: str, time_window_minutes: int = 5) -> str`**
Create time-based cache keys that automatically expire.

```python
# Key changes every 5 minutes
key = CacheUtils.create_time_based_key("real_time_data", 5)
```

---

## Usage Examples

### Basic Usage

```python
from infrastructure.services.cache_service import CacheService

# Initialize service
cache = CacheService()

# Basic operations
cache.set("user_123", user_data, ttl=3600)
user_data = cache.get("user_123")
cache.delete("user_123")

# Bulk operations
users = cache.get_many(["user_123", "user_456"])
cache.set_many({"user_789": data1, "user_101": data2}, ttl=1800)
```

### Decorator Usage

```python
from infrastructure.utils.cache_decorators import cache_result, cache_method_result

# Function caching
@cache_result(ttl=600, key_prefix="analytics")
def calculate_plant_efficiency(plant_id: str, date_range: str):
    return expensive_calculation(plant_id, date_range)

# Method caching
class AnalysisService:
    @cache_method_result(ttl=300, key_prefix="analysis")
    def get_kpi_data(self, site_id: str):
        return self.repository.get_kpis(site_id)

# Cache invalidation
@invalidate_cache(key_pattern="plant_*", prefix="analytics")
def update_plant_data(plant_id: str):
    # Update plant data
    pass
```

### Advanced Patterns

```python
# Cache-aside pattern
def get_dashboard_data(user_id: str):
    cache = CacheService()
    return cache.get_or_set(
        f"dashboard_{user_id}",
        lambda: fetch_dashboard_from_db(user_id),
        ttl=900  # 15 minutes
    )

# Distributed locking
@cache_lock(lock_key="daily_report_generation", timeout=1800)
def generate_daily_report():
    # Ensures only one instance generates the report
    return create_comprehensive_report()

# Time-based caching
from infrastructure.utils.cache_decorators import CacheUtils

def get_real_time_metrics():
    cache = CacheService()
    # Key changes every 5 minutes
    time_key = CacheUtils.create_time_based_key("metrics", 5)
    return cache.get_or_set(time_key, fetch_live_metrics, ttl=300)
```

---

## Integration Guidelines

### When to Use Caching

**Recommended Use Cases**:
- Database query results that don't change frequently
- Expensive calculations (KPIs, analytics)
- External API responses
- User session data
- Configuration data
- Metadata operations

**Not Recommended For**:
- Frequently changing data
- Large binary data (>1MB)
- Sensitive information requiring encryption
- Data requiring ACID transactions

### Performance Considerations

**Cache Key Design**:
- Keep keys short but descriptive
- Use consistent naming conventions
- Include version numbers for schema changes
- Avoid special characters

**TTL Strategy**:
- Short TTL (1-5 min): Real-time data, user sessions
- Medium TTL (15-60 min): Dashboard data, calculations
- Long TTL (1-24 hours): Configuration, metadata
- Very Long TTL (days): Static reference data

**Memory Management**:
- Monitor cache size and memory usage
- Use appropriate TTL values
- Implement cache warming for critical data
- Clean up expired keys regularly

### Error Handling

The caching service is designed with graceful degradation:
- Functions work normally if Redis is unavailable
- Errors are logged but don't break application flow
- Cache misses fall back to original data sources
- Connection issues are handled transparently

### Monitoring and Debugging

```python
# Check cache health
cache = CacheService()
health_info = cache.get_cache_info()
print(f"Cache Status: {health_info['status']}")

# Get detailed statistics
from infrastructure.utils.cache_decorators import CacheUtils
stats = CacheUtils.get_cache_health()
```

---

## Environment Configuration

### Development Environment

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
REDIS_ENABLE_LOGGING=true
REDIS_MAX_CONNECTIONS=10
```

### Production Environment

```bash
# Production .env
REDIS_HOST=your-redis-server.com
REDIS_PORT=6379
REDIS_PASSWORD=your-secure-password
REDIS_DB=0
REDIS_ENABLE_COMPRESSION=true
REDIS_ENABLE_LOGGING=false
REDIS_MAX_CONNECTIONS=50
```

---

## Best Practices

### 1. Key Naming Conventions
```python
# Good
cache.set("user_profile_123", data, prefix="auth")
cache.set("dashboard_kpis_site_456", data, prefix="analytics")

# Avoid
cache.set("123", data)  # Too generic
cache.set("user:profile:123:data:2024", data)  # Too complex
```

### 2. TTL Management
```python
from config.redis_cache_config import CacheConfig

# Use predefined TTL constants
cache.set("user_session", data, ttl=CacheConfig.MEDIUM_TTL)
cache.set("daily_report", data, ttl=CacheConfig.EXTRA_LONG_TTL)
```

### 3. Error Handling
```python
def get_cached_data(key: str):
    cache = CacheService()
    try:
        return cache.get_or_set(key, fetch_from_db, ttl=300)
    except Exception as e:
        logger.error(f"Cache operation failed: {e}")
        # Always provide fallback
        return fetch_from_db()
```

### 4. Testing with Cache

```python
# Disable cache for testing
import os
os.environ['REDIS_HOST'] = 'invalid'  # Forces fallback mode

# Or use mock
from unittest.mock import patch
with patch('infrastructure.services.cache_service.CacheService.is_cache_available', return_value=False):
    # Test without cache
    pass
```

---

## Troubleshooting

### Common Issues

**Cache Not Working**:
1. Check Redis server status
2. Verify environment variables
3. Check network connectivity
4. Review cache service logs

**Performance Issues**:
1. Monitor cache hit/miss ratios
2. Optimize TTL values
3. Check key distribution
4. Review serialization overhead

**Memory Issues**:
1. Implement proper TTL values
2. Clean up unused cache entries
3. Monitor Redis memory usage
4. Consider cache size limits

### Debugging Commands

```python
# Check cache configuration
from config.redis_cache_config import get_cache_stats
print(get_cache_stats())

# Test cache operations
cache = CacheService()
print(f"Cache available: {cache.is_cache_available()}")

# Monitor cache health
health = CacheUtils.get_cache_health()
print(f"Health: {health}")
```

---

## Future Enhancements

### Planned Features
- Cache clustering support
- Advanced pattern matching
- Cache analytics dashboard  
- Automatic cache warming
- Cache compression optimization
- Multi-level cache hierarchies

### Extension Points
- Custom serialization backends
- Cache event listeners
- Metrics collection integration
- Custom key generation strategies

---

## Conclusion

This Redis caching service provides a comprehensive, production-ready caching solution for the SWRO Backend. It's designed to be:

- **Standalone**: No integration required until needed
- **Robust**: Comprehensive error handling and fallback
- **Flexible**: Supports various caching patterns and use cases
- **Maintainable**: Clear APIs and extensive documentation
- **Scalable**: Ready for production deployment

The service follows Django and project conventions, making it easy for developers to understand and use effectively.