import os
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.core.cache.backends.redis import RedisCache

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration constants"""
    
    # Default TTL values (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    SHORT_TTL = 60     # 1 minute
    MEDIUM_TTL = 900   # 15 minutes
    LONG_TTL = 3600    # 1 hour
    EXTRA_LONG_TTL = 86400  # 24 hours
    
    # Cache key prefixes
    DEFAULT_PREFIX = "swro_cache"
    USER_PREFIX = "user"
    SESSION_PREFIX = "session"
    QUERY_PREFIX = "query"
    METADATA_PREFIX = "metadata"
    
    # Redis connection settings
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    
    # Connection pool settings
    MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    
    # Cache behavior settings
    ENABLE_COMPRESSION = os.getenv("REDIS_ENABLE_COMPRESSION", "true").lower() == "true"
    ENABLE_LOGGING = os.getenv("REDIS_ENABLE_LOGGING", "true").lower() == "true"


def get_redis_cache_config() -> Dict[str, Any]:
    """
    Get Redis cache configuration following the project's config pattern.
    Returns configuration dictionary for Redis cache settings.
    
    Returns:
        Dict[str, Any]: Redis cache configuration
        
    Raises:
        ValueError: If Redis configuration is invalid
    """
    try:
        # Validate Redis connection settings
        if not CacheConfig.REDIS_HOST:
            raise ValueError("Redis host is not configured")
            
        if CacheConfig.REDIS_PORT <= 0 or CacheConfig.REDIS_PORT > 65535:
            raise ValueError("Invalid Redis port configuration")
            
        config = {
            "host": CacheConfig.REDIS_HOST,
            "port": CacheConfig.REDIS_PORT,
            "db": CacheConfig.REDIS_DB,
            "password": CacheConfig.REDIS_PASSWORD,
            "max_connections": CacheConfig.MAX_CONNECTIONS,
            "enable_compression": CacheConfig.ENABLE_COMPRESSION,
            "enable_logging": CacheConfig.ENABLE_LOGGING,
            "default_ttl": CacheConfig.DEFAULT_TTL,
            "key_prefix": CacheConfig.DEFAULT_PREFIX
        }
        
        if CacheConfig.ENABLE_LOGGING:
            logger.info(f"Redis cache configuration loaded successfully for {CacheConfig.REDIS_HOST}:{CacheConfig.REDIS_PORT}")
            
        return config
        
    except Exception as e:
        error_msg = f"Failed to configure Redis cache: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def get_redis_cache_instance():
    """
    Get Redis cache instance using Django's cache framework.
    This function follows the same pattern as databricks_connector.py
    
    Returns:
        RedisCache: Configured Redis cache instance
        
    Raises:
        ValueError: If cache configuration fails
    """
    try:
        # Use Django's configured cache (from settings.py)
        cache_instance = cache
        
        # Verify cache is available
        if not hasattr(cache_instance, '_cache'):
            raise ValueError("Cache backend is not properly configured")
            
        # Test connection (optional)
        try:
            cache_instance.get('__connection_test__')
        except Exception as connection_error:
            logger.warning(f"Cache connection test failed: {connection_error}")
            # Don't raise here - allow graceful degradation
            
        if CacheConfig.ENABLE_LOGGING:
            logger.info("Redis cache instance initialized successfully")
            
        return cache_instance
        
    except Exception as e:
        error_msg = f"Failed to initialize Redis cache instance: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def validate_cache_connection() -> bool:
    """
    Validate Redis cache connection health.
    
    Returns:
        bool: True if cache is available, False otherwise
    """
    try:
        cache_instance = get_redis_cache_instance()
        
        # Test basic operations
        test_key = "__health_check__"
        test_value = "test"
        
        cache_instance.set(test_key, test_value, timeout=60)
        retrieved_value = cache_instance.get(test_key)
        cache_instance.delete(test_key)
        
        is_healthy = retrieved_value == test_value
        
        if CacheConfig.ENABLE_LOGGING:
            status = "healthy" if is_healthy else "unhealthy"
            logger.info(f"Cache health check completed: {status}")
            
        return is_healthy
        
    except Exception as e:
        if CacheConfig.ENABLE_LOGGING:
            logger.warning(f"Cache health check failed: {str(e)}")
        return False


def get_cache_stats() -> Dict[str, Any]:
    """
    Get basic cache statistics and configuration info.
    
    Returns:
        Dict[str, Any]: Cache statistics and configuration
    """
    try:
        config = get_redis_cache_config()
        is_healthy = validate_cache_connection()
        
        stats = {
            "status": "healthy" if is_healthy else "unhealthy",
            "host": config["host"],
            "port": config["port"],
            "db": config["db"],
            "max_connections": config["max_connections"],
            "default_ttl": config["default_ttl"],
            "compression_enabled": config["enable_compression"],
            "logging_enabled": config["enable_logging"]
        }
        
        return stats
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "host": CacheConfig.REDIS_HOST,
            "port": CacheConfig.REDIS_PORT
        }