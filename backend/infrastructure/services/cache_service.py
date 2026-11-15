import json
import logging
import hashlib
import threading
import os
import pickle
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta

from config.redis_cache_config import (
    get_redis_cache_instance, 
    get_redis_cache_config, 
    validate_cache_connection,
    CacheConfig
)

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis caching service for SWRO Backend.
    Provides a clean, reusable interface for caching operations.
    Follows the same pattern as other services in the project.
    """
    
    def __init__(self):
        """Initialize cache service with Redis connection and persistent fallback"""
        self.fallback_cache = {}  # In-memory fallback cache
        self.fallback_expiry = {}  # Expiry times for fallback cache
        self.fallback_lock = threading.RLock()  # Thread safety for fallback
        
        # File-based cache for persistence
        self.cache_dir = "/tmp/swro_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        try:
            # self.cache = get_redis_cache_instance()
            self.cache = None
            self.config = get_redis_cache_config()
            self.is_available = False
            self.use_fallback = False
            
            if self.config.get("enable_logging", True):
                logger.info("CacheService initialized successfully with Redis")
                
        except Exception as e:
            logger.warning(f"CacheService Redis initialization failed: {e}. Using persistent file-based fallback.")
            self.cache = None
            self.config = {"enable_logging": True, "key_prefix": CacheConfig.DEFAULT_PREFIX}
            self.is_available = True  # Still available, just using fallback
            self.use_fallback = True
            # Load existing cache from disk
            # self._load_fallback_cache()

    def _generate_key(self, key: str, prefix: Optional[str] = None) -> str:
        """
        Generate a properly formatted cache key with optional prefix.
        
        Args:
            key (str): Base cache key
            prefix (str, optional): Key prefix for namespacing
            
        Returns:
            str: Formatted cache key
        """
        if prefix:
            return f"{self.config.get('key_prefix', CacheConfig.DEFAULT_PREFIX)}:{prefix}:{key}"
        return f"{self.config.get('key_prefix', CacheConfig.DEFAULT_PREFIX)}:{key}"

    def _serialize_value(self, value: Any) -> str:
        """
        Serialize value for cache storage with error handling.
        
        Args:
            value (Any): Value to serialize
            
        Returns:
            str: Serialized value
        """
        try:
            if isinstance(value, (str, int, float, bool)):
                return str(value)
            return json.dumps(value, default=str, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to serialize cache value: {e}")
            return str(value)

    def _deserialize_value(self, value: str) -> Any:
        """
        Deserialize value from cache with error handling.
        
        Args:
            value (str): Serialized value from cache
            
        Returns:
            Any: Deserialized value
        """
        if value is None:
            return None
            
        try:
            # Try to parse as JSON first
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return as string if JSON parsing fails
            return value

    def is_cache_available(self) -> bool:
        """
        Check if cache is available and operational.
        
        Returns:
            bool: True if cache is available, False otherwise
        """
        if not self.is_available:
            return False
        
        # If using fallback, it's always available
        if self.use_fallback:
            return True
            
        # For Redis, check if cache instance exists
        if not self.cache:
            return False
            
        try:
            # Simple test instead of validate_cache_connection
            self.cache.get("__cache_test__")
            return True
        except Exception as e:
            logger.warning(f"Redis cache not available, switching to fallback: {e}")
            self.use_fallback = True
            return True

    def get(self, key: str, prefix: Optional[str] = None, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key (str): Cache key
            prefix (str, optional): Key prefix for namespacing
            default (Any): Default value if key not found
            
        Returns:
            Any: Cached value or default
        """
        if not self.is_available:
            return default
        
        cache_key = self._generate_key(key, prefix)
        
        # Try Redis first if available
        if not self.use_fallback and self.cache:
            try:
                cached_value = self.cache.get(cache_key)
                
                if cached_value is not None:
                    if self.config.get("enable_logging", True):
                        logger.debug(f"Redis cache hit for key '{cache_key}'")
                    return self._deserialize_value(cached_value)
                    
            except Exception as e:
                if self.config.get("enable_logging", True):
                    logger.warning(f"Redis cache get failed for key '{key}': {e}, switching to fallback")
                self.use_fallback = True
        
        # Use fallback cache
        return self._get_from_fallback(cache_key, default)

    def set(self, key: str, value: Any, ttl: Optional[int] = None, prefix: Optional[str] = None) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (int, optional): Time to live in seconds
            prefix (str, optional): Key prefix for namespacing
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        cache_key = self._generate_key(key, prefix)
        timeout = ttl or self.config.get("default_ttl", CacheConfig.DEFAULT_TTL)
        
        # Try Redis first if available
        if not self.use_fallback and self.cache:
            try:
                serialized_value = self._serialize_value(value)
                self.cache.set(cache_key, serialized_value, timeout=timeout)
                
                if self.config.get("enable_logging", True):
                    logger.debug(f"Redis cache set successful for key '{cache_key}' with TTL {timeout}s")
                    
                return True
                
            except Exception as e:
                if self.config.get("enable_logging", True):
                    logger.warning(f"Redis cache set failed for key '{key}': {e}, switching to fallback")
                self.use_fallback = True
        
        # Use fallback cache
        return self._set_to_fallback(cache_key, value, timeout)

    def delete(self, key: str, prefix: Optional[str] = None) -> bool:
        """
        Delete value from cache.
        
        Args:
            key (str): Cache key
            prefix (str, optional): Key prefix for namespacing
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_cache_available():
            return False
            
        try:
            cache_key = self._generate_key(key, prefix)
            result = self.cache.delete(cache_key)
            
            if self.config.get("enable_logging", True):
                logger.debug(f"Cache delete operation for key '{cache_key}': {'success' if result else 'key not found'}")
                
            return bool(result)
            
        except Exception as e:
            if self.config.get("enable_logging", True):
                logger.warning(f"Cache delete operation failed for key '{key}': {e}")
            return False

    def get_or_set(self, key: str, fetch_func: Callable[[], Any], ttl: Optional[int] = None, 
                   prefix: Optional[str] = None) -> Any:
        """
        Get value from cache or set it using fetch function if not exists.
        
        Args:
            key (str): Cache key
            fetch_func (Callable): Function to fetch value if not in cache
            ttl (int, optional): Time to live in seconds
            prefix (str, optional): Key prefix for namespacing
            
        Returns:
            Any: Cached or fetched value
        """
        # Try to get from cache first
        cached_value = self.get(key, prefix)
        if cached_value is not None:
            return cached_value
            
        try:
            # Fetch new value
            fresh_value = fetch_func()
            
            # Cache the fresh value
            self.set(key, fresh_value, ttl, prefix)
            
            return fresh_value
            
        except Exception as e:
            if self.config.get("enable_logging", True):
                logger.error(f"Failed to fetch value for cache key '{key}': {e}")
            return None

    def get_many(self, keys: List[str], prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys (List[str]): List of cache keys
            prefix (str, optional): Key prefix for namespacing
            
        Returns:
            Dict[str, Any]: Dictionary of key-value pairs found in cache
        """
        if not self.is_cache_available() or not keys:
            return {}
            
        try:
            cache_keys = [self._generate_key(key, prefix) for key in keys]
            cached_values = self.cache.get_many(cache_keys)
            
            # Map back to original keys and deserialize values
            result = {}
            for original_key, cache_key in zip(keys, cache_keys):
                if cache_key in cached_values:
                    result[original_key] = self._deserialize_value(cached_values[cache_key])
                    
            return result
            
        except Exception as e:
            if self.config.get("enable_logging", True):
                logger.warning(f"Cache get_many operation failed: {e}")
            return {}

    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None, prefix: Optional[str] = None) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            data (Dict[str, Any]): Dictionary of key-value pairs to cache
            ttl (int, optional): Time to live in seconds
            prefix (str, optional): Key prefix for namespacing
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_cache_available() or not data:
            return False
            
        try:
            timeout = ttl or self.config.get("default_ttl", CacheConfig.DEFAULT_TTL)
            
            # Prepare data for caching
            cache_data = {}
            for key, value in data.items():
                cache_key = self._generate_key(key, prefix)
                cache_data[cache_key] = self._serialize_value(value)
                
            self.cache.set_many(cache_data, timeout=timeout)
            
            if self.config.get("enable_logging", True):
                logger.debug(f"Cache set_many successful for {len(data)} keys with TTL {timeout}s")
                
            return True
            
        except Exception as e:
            if self.config.get("enable_logging", True):
                logger.warning(f"Cache set_many operation failed: {e}")
            return False

    def delete_many(self, keys: List[str], prefix: Optional[str] = None) -> int:
        """
        Delete multiple values from cache.
        
        Args:
            keys (List[str]): List of cache keys to delete
            prefix (str, optional): Key prefix for namespacing
            
        Returns:
            int: Number of keys successfully deleted
        """
        if not self.is_cache_available() or not keys:
            return 0
            
        try:
            cache_keys = [self._generate_key(key, prefix) for key in keys]
            deleted_count = self.cache.delete_many(cache_keys)
            
            if self.config.get("enable_logging", True):
                logger.debug(f"Cache delete_many operation: {deleted_count}/{len(keys)} keys deleted")
                
            return deleted_count
            
        except Exception as e:
            if self.config.get("enable_logging", True):
                logger.warning(f"Cache delete_many operation failed: {e}")
            return 0

    def clear_prefix(self, prefix: str) -> bool:
        """
        Clear all cache entries with a specific prefix.
        
        Args:
            prefix (str): Prefix to clear
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_cache_available():
            return False
            
        try:
            pattern = f"{self.config.get('key_prefix', CacheConfig.DEFAULT_PREFIX)}:{prefix}:*"
            
            # Note: This is a simplified implementation
            # In production, you might want to use Redis SCAN for large datasets
            if hasattr(self.cache, 'delete_pattern'):
                deleted_count = self.cache.delete_pattern(pattern)
            else:
                # Fallback for cache backends that don't support pattern deletion
                logger.warning("Cache backend doesn't support pattern deletion")
                return False
                
            if self.config.get("enable_logging", True):
                logger.info(f"Cleared cache entries with prefix '{prefix}': {deleted_count} keys deleted")
                
            return True
            
        except Exception as e:
            if self.config.get("enable_logging", True):
                logger.warning(f"Cache clear_prefix operation failed for prefix '{prefix}': {e}")
            return False

    def generate_key_from_params(self, base_key: str, **params) -> str:
        """
        Generate a cache key from base key and parameters.
        
        Args:
            base_key (str): Base key name
            **params: Parameters to include in key generation
            
        Returns:
            str: Generated cache key
        """
        if not params:
            return base_key
            
        # Sort parameters for consistent key generation
        sorted_params = sorted(params.items())
        params_str = "_".join(f"{k}:{v}" for k, v in sorted_params)
        
        # Create hash if the key would be too long
        if len(params_str) > 100:
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:16]
            return f"{base_key}_{params_hash}"
        
        return f"{base_key}_{params_str}"

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache service information and statistics.
        
        Returns:
            Dict[str, Any]: Cache service information
        """
        try:
            from config.redis_cache_config import get_cache_stats
            stats = get_cache_stats()
            
            stats.update({
                "service_available": self.is_available,
                "connection_healthy": self.is_cache_available(),
                "default_ttl": self.config.get("default_ttl", CacheConfig.DEFAULT_TTL),
                "key_prefix": self.config.get("key_prefix", CacheConfig.DEFAULT_PREFIX)
            })
            
            return stats
            
        except Exception as e:
            return {
                "service_available": self.is_available,
                "connection_healthy": False,
                "error": str(e)
            }
    
    def _get_from_fallback(self, cache_key: str, default: Any = None) -> Any:
        """Get value from in-memory fallback cache"""
        with self.fallback_lock:
            # Clean expired entries
            self._cleanup_expired_fallback()
            
            if cache_key in self.fallback_cache:
                if self.config.get("enable_logging", True):
                    logger.debug(f"Fallback cache hit for key '{cache_key}'")
                return self.fallback_cache[cache_key]
            
            if self.config.get("enable_logging", True):
                logger.debug(f"Fallback cache miss for key '{cache_key}'")
            return default
    
    def _set_to_fallback(self, cache_key: str, value: Any, ttl: int) -> bool:
        """Set value to in-memory fallback cache"""
        try:
            with self.fallback_lock:
                # Clean expired entries first
                self._cleanup_expired_fallback()
                
                # Set value and expiry
                self.fallback_cache[cache_key] = value
                self.fallback_expiry[cache_key] = datetime.now() + timedelta(seconds=ttl)
                
                if self.config.get("enable_logging", True):
                    logger.debug(f"Fallback cache set successful for key '{cache_key}' with TTL {ttl}s")
                
                # Save to disk for persistence
                self._save_fallback_cache()
                
                return True
                
        except Exception as e:
            if self.config.get("enable_logging", True):
                logger.error(f"Fallback cache set failed for key '{cache_key}': {e}")
            return False
    
    def _cleanup_expired_fallback(self):
        """Clean up expired entries from fallback cache"""
        try:
            current_time = datetime.now()
            expired_keys = [
                key for key, expiry_time in self.fallback_expiry.items()
                if current_time > expiry_time
            ]
            
            for key in expired_keys:
                self.fallback_cache.pop(key, None)
                self.fallback_expiry.pop(key, None)
                
            if expired_keys and self.config.get("enable_logging", True):
                logger.debug(f"Cleaned up {len(expired_keys)} expired fallback cache entries")
                
        except Exception as e:
            logger.warning(f"Error cleaning up fallback cache: {e}")
    
    def _load_fallback_cache(self):
        """Load fallback cache from disk"""
        try:
            cache_file = os.path.join(self.cache_dir, "fallback_cache.pkl")
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.fallback_cache = cache_data.get('cache', {})
                    self.fallback_expiry = cache_data.get('expiry', {})
                logger.info(f"Loaded {len(self.fallback_cache)} items from file-based cache")
        except Exception as e:
            logger.warning(f"Error loading fallback cache from disk: {e}")
    
    def _save_fallback_cache(self):
        """Save fallback cache to disk"""
        try:
            cache_file = os.path.join(self.cache_dir, "fallback_cache.pkl")
            cache_data = {
                'cache': self.fallback_cache,
                'expiry': self.fallback_expiry
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.warning(f"Error saving fallback cache to disk: {e}")