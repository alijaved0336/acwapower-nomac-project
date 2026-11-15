import functools
import hashlib
import logging
from typing import Any, Callable, Optional, Union, Dict, List
from datetime import datetime

from infrastructure.services.cache_service import CacheService
from config.redis_cache_config import CacheConfig

logger = logging.getLogger(__name__)


def cache_result(ttl: Optional[int] = None, key_prefix: Optional[str] = None, 
                 include_args: bool = True, include_kwargs: bool = True,
                 key_func: Optional[Callable] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl (int, optional): Time to live in seconds
        key_prefix (str, optional): Prefix for cache key
        include_args (bool): Include function args in cache key generation
        include_kwargs (bool): Include function kwargs in cache key generation
        key_func (Callable, optional): Custom function to generate cache key
        
    Usage:
        @cache_result(ttl=600, key_prefix="dashboard")
        def get_dashboard_data(user_id: str):
            return expensive_calculation()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache_service = CacheService()
                
                # Skip caching if cache is not available
                if not cache_service.is_cache_available():
                    return func(*args, **kwargs)
                
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = _generate_function_cache_key(
                        func, args, kwargs, include_args, include_kwargs
                    )
                
                # Try to get from cache
                cached_result = cache_service.get(cache_key, prefix=key_prefix)
                if cached_result is not None:
                    logger.debug(f"Cache hit for function '{func.__name__}' with key '{cache_key}'")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache_ttl = ttl or CacheConfig.DEFAULT_TTL
                
                success = cache_service.set(cache_key, result, ttl=cache_ttl, prefix=key_prefix)
                if success:
                    logger.debug(f"Cache set for function '{func.__name__}' with key '{cache_key}' and TTL {cache_ttl}s")
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache decorator error for function '{func.__name__}': {e}")
                # Always return function result even if caching fails
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


def cache_method_result(ttl: Optional[int] = None, key_prefix: Optional[str] = None,
                       include_self: bool = False, include_args: bool = True, 
                       include_kwargs: bool = True):
    """
    Decorator to cache method results (for class methods).
    
    Args:
        ttl (int, optional): Time to live in seconds
        key_prefix (str, optional): Prefix for cache key
        include_self (bool): Include self object in cache key generation
        include_args (bool): Include method args in cache key generation
        include_kwargs (bool): Include method kwargs in cache key generation
        
    Usage:
        class DataService:
            @cache_method_result(ttl=300, key_prefix="data")
            def get_expensive_data(self, param1: str):
                return expensive_operation(param1)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                cache_service = CacheService()
                
                # Skip caching if cache is not available
                if not cache_service.is_cache_available():
                    return func(self, *args, **kwargs)
                
                # Generate cache key for method
                method_args = (self,) + args if include_self else args
                cache_key = _generate_function_cache_key(
                    func, method_args, kwargs, include_args or include_self, include_kwargs
                )
                
                # Try to get from cache
                cached_result = cache_service.get(cache_key, prefix=key_prefix)
                if cached_result is not None:
                    logger.debug(f"Cache hit for method '{func.__name__}' with key '{cache_key}'")
                    return cached_result
                
                # Execute method and cache result
                result = func(self, *args, **kwargs)
                cache_ttl = ttl or CacheConfig.DEFAULT_TTL
                
                success = cache_service.set(cache_key, result, ttl=cache_ttl, prefix=key_prefix)
                if success:
                    logger.debug(f"Cache set for method '{func.__name__}' with key '{cache_key}' and TTL {cache_ttl}s")
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache method decorator error for '{func.__name__}': {e}")
                # Always return method result even if caching fails
                return func(self, *args, **kwargs)
                
        return wrapper
    return decorator


def invalidate_cache(key_pattern: str, prefix: Optional[str] = None):
    """
    Decorator to invalidate cache entries after function execution.
    
    Args:
        key_pattern (str): Cache key pattern to invalidate
        prefix (str, optional): Cache key prefix
        
    Usage:
        @invalidate_cache(key_pattern="user_*", prefix="dashboard")
        def update_user_data(user_id: str):
            # Update user data
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Execute function first
                result = func(*args, **kwargs)
                
                # Invalidate cache after successful execution
                cache_service = CacheService()
                if cache_service.is_cache_available():
                    # For now, we'll use a simple approach
                    # In production, you might want to implement pattern-based deletion
                    logger.debug(f"Cache invalidation triggered for pattern '{key_pattern}' with prefix '{prefix}'")
                    
                    # If key_pattern contains wildcards, use clear_prefix
                    if "*" in key_pattern:
                        pattern_prefix = key_pattern.replace("*", "").rstrip("_")
                        cache_service.clear_prefix(f"{prefix}:{pattern_prefix}" if prefix else pattern_prefix)
                    else:
                        cache_service.delete(key_pattern, prefix=prefix)
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache invalidation decorator error for '{func.__name__}': {e}")
                # Return function result even if cache invalidation fails
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


def cache_lock(lock_key: str, timeout: int = 300, prefix: Optional[str] = None):
    """
    Decorator to implement distributed locking using cache.
    Prevents multiple instances of the same function from running simultaneously.
    
    Args:
        lock_key (str): Unique key for the lock
        timeout (int): Lock timeout in seconds
        prefix (str, optional): Lock key prefix
        
    Usage:
        @cache_lock(lock_key="expensive_report_generation", timeout=600)
        def generate_expensive_report():
            # Only one instance can run at a time
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache_service = CacheService()
                
                # Skip locking if cache is not available
                if not cache_service.is_cache_available():
                    return func(*args, **kwargs)
                
                lock_cache_key = f"lock_{lock_key}"
                lock_value = f"{func.__name__}_{datetime.now().isoformat()}"
                
                # Try to acquire lock
                existing_lock = cache_service.get(lock_cache_key, prefix=prefix)
                if existing_lock is not None:
                    logger.warning(f"Function '{func.__name__}' is locked by another process")
                    raise RuntimeError(f"Function '{func.__name__}' is currently locked")
                
                # Set lock
                cache_service.set(lock_cache_key, lock_value, ttl=timeout, prefix=prefix)
                logger.debug(f"Lock acquired for function '{func.__name__}' with timeout {timeout}s")
                
                try:
                    # Execute function
                    result = func(*args, **kwargs)
                    return result
                finally:
                    # Always release lock
                    cache_service.delete(lock_cache_key, prefix=prefix)
                    logger.debug(f"Lock released for function '{func.__name__}'")
                
            except Exception as e:
                logger.error(f"Cache lock decorator error for '{func.__name__}': {e}")
                raise
                
        return wrapper
    return decorator


def _generate_function_cache_key(func: Callable, args: tuple, kwargs: dict, 
                                include_args: bool = True, include_kwargs: bool = True) -> str:
    """
    Generate a cache key for a function based on its name and parameters.
    
    Args:
        func (Callable): Function object
        args (tuple): Function arguments
        kwargs (dict): Function keyword arguments
        include_args (bool): Include args in key generation
        include_kwargs (bool): Include kwargs in key generation
        
    Returns:
        str: Generated cache key
    """
    key_parts = [func.__name__]
    
    if include_args and args:
        # Convert args to string representation
        args_str = "_".join(str(arg) for arg in args)
        key_parts.append(f"args:{args_str}")
    
    if include_kwargs and kwargs:
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = "_".join(f"{k}:{v}" for k, v in sorted_kwargs)
        key_parts.append(f"kwargs:{kwargs_str}")
    
    base_key = "_".join(key_parts)
    
    # Create hash if key is too long
    if len(base_key) > 200:
        key_hash = hashlib.md5(base_key.encode()).hexdigest()[:16]
        return f"{func.__name__}_{key_hash}"
    
    return base_key


class CacheUtils:
    """
    Utility class for common caching operations.
    """
    
    @staticmethod
    def warm_cache(cache_configs: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Warm cache with predefined data.
        
        Args:
            cache_configs (List[Dict]): List of cache configuration dictionaries
                Each dict should contain: key, value, ttl, prefix (optional)
        
        Returns:
            Dict[str, bool]: Results of cache warming operations
        """
        cache_service = CacheService()
        results = {}
        
        for config in cache_configs:
            try:
                key = config.get("key")
                value = config.get("value")
                ttl = config.get("ttl", CacheConfig.DEFAULT_TTL)
                prefix = config.get("prefix")
                
                if not key or value is None:
                    continue
                
                success = cache_service.set(key, value, ttl=ttl, prefix=prefix)
                results[key] = success
                
                if success:
                    logger.debug(f"Cache warmed for key '{key}' with TTL {ttl}s")
                else:
                    logger.warning(f"Failed to warm cache for key '{key}'")
                    
            except Exception as e:
                logger.error(f"Error warming cache for config {config}: {e}")
                results[config.get("key", "unknown")] = False
        
        return results
    
    @staticmethod
    def clear_cache_by_pattern(pattern: str, prefix: Optional[str] = None) -> bool:
        """
        Clear cache entries matching a pattern.
        
        Args:
            pattern (str): Pattern to match (supports wildcards)
            prefix (str, optional): Cache key prefix
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cache_service = CacheService()
            
            if "*" in pattern:
                pattern_prefix = pattern.replace("*", "").rstrip("_")
                return cache_service.clear_prefix(f"{prefix}:{pattern_prefix}" if prefix else pattern_prefix)
            else:
                return cache_service.delete(pattern, prefix=prefix)
                
        except Exception as e:
            logger.error(f"Error clearing cache pattern '{pattern}': {e}")
            return False
    
    @staticmethod
    def get_cache_health() -> Dict[str, Any]:
        """
        Get cache health information.
        
        Returns:
            Dict[str, Any]: Cache health status and metrics
        """
        try:
            cache_service = CacheService()
            return cache_service.get_cache_info()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connection_healthy": False
            }
    
    @staticmethod
    def create_time_based_key(base_key: str, time_window_minutes: int = 5) -> str:
        """
        Create a time-based cache key that changes every N minutes.
        Useful for time-sensitive data that should be refreshed periodically.
        
        Args:
            base_key (str): Base cache key
            time_window_minutes (int): Time window in minutes
            
        Returns:
            str: Time-based cache key
        """
        now = datetime.now()
        time_slot = (now.hour * 60 + now.minute) // time_window_minutes
        return f"{base_key}_time_{now.strftime('%Y%m%d')}_{time_slot}"