"""
Optimized ClickHouse Connector with Connection Pooling and Performance Enhancements

This module provides an optimized ClickHouse connection management system
specifically designed to improve performance when connecting to Azure Container Apps
deployed ClickHouse instances.

Key optimizations:
- Connection pooling to reuse connections
- Reduced timeout values
- Async query support
- Connection health monitoring
- Query result caching
- Batch query execution
"""

import logging
import os
import asyncio
import threading
import time
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json

import clickhouse_connect
from clickhouse_connect.driver import Client
from clickhouse_connect.driver.query import QueryResult

from constants import ClickHouseConfig, ErrorMessages

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Track connection statistics for monitoring"""
    created_at: datetime
    last_used: datetime
    query_count: int = 0
    total_query_time: float = 0.0
    error_count: int = 0


class ConnectionPool:
    """Thread-safe connection pool for ClickHouse connections"""
    
    def __init__(self, max_connections: int = 10, max_idle_time: int = 300):
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time  # 5 minutes
        self._pool = []
        self._stats = {}
        self._lock = threading.RLock()
        self._created_connections = 0
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_idle_connections, daemon=True)
        self._cleanup_thread.start()
    
    def get_connection(self) -> Client:
        """Get a connection from the pool or create a new one"""
        with self._lock:
            # Try to reuse existing connection
            while self._pool:
                client = self._pool.pop()
                try:
                    # Test connection health
                    client.ping()
                    stats = self._stats.get(id(client))
                    if stats:
                        stats.last_used = datetime.now()
                    return client
                except Exception as e:
                    logger.warning(f"Removing unhealthy connection from pool: {e}")
                    self._close_connection_safely(client)
            
            # Create new connection if pool is empty
            if self._created_connections < self.max_connections:
                return self._create_new_connection()
            else:
                raise Exception("Connection pool exhausted. Consider increasing max_connections.")
    
    def return_connection(self, client: Client):
        """Return a connection to the pool"""
        with self._lock:
            if len(self._pool) < self.max_connections:
                self._pool.append(client)
                stats = self._stats.get(id(client))
                if stats:
                    stats.last_used = datetime.now()
            else:
                self._close_connection_safely(client)
    
    def _create_new_connection(self) -> Client:
        """Create a new ClickHouse connection with optimized settings"""
        try:
            # Optimized connection parameters
            host = os.getenv("CLICKHOUSE_HOST", "localhost")
            port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
            username = os.getenv("CLICKHOUSE_USERNAME")
            password = os.getenv("CLICKHOUSE_PASSWORD")
            database = os.getenv("CLICKHOUSE_DATABASE", "default")
            secure = os.getenv("CLICKHOUSE_SECURE", "0") in ("1", "true", "True")
            
            # Optimized timeout values for Azure Container Apps
            connect_timeout = int(os.getenv("CLICKHOUSE_CONNECT_TIMEOUT", "15"))  # Reduced from 60
            send_receive_timeout = int(os.getenv("CLICKHOUSE_SEND_RECEIVE_TIMEOUT", "45"))  # Reduced from 120
            
            client = clickhouse_connect.get_client(
                host=host,
                port=port,
                username=username,
                password=password,
                database=database,
                secure=secure,
                connect_timeout=connect_timeout,
                send_receive_timeout=send_receive_timeout,
                # Optimizations for Azure Container Apps
                compress=True,  # Enable compression to reduce network traffic
                query_retries=2,  # Retry failed queries
                # Connection pool settings
                session_id=f"swro_pool_{threading.current_thread().ident}_{int(time.time())}"
            )
            
            # Test the connection
            client.ping()
            
            # Track connection stats
            self._stats[id(client)] = ConnectionStats(
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            self._created_connections += 1
            logger.info(f"Created new ClickHouse connection ({self._created_connections}/{self.max_connections})")
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to create ClickHouse connection: {e}")
            raise Exception(f"Failed to connect to ClickHouse: {str(e)}")
    
    def _cleanup_idle_connections(self):
        """Background thread to cleanup idle connections"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                with self._lock:
                    current_time = datetime.now()
                    active_connections = []
                    
                    for client in self._pool:
                        stats = self._stats.get(id(client))
                        if stats and (current_time - stats.last_used).seconds < self.max_idle_time:
                            active_connections.append(client)
                        else:
                            logger.info("Cleaning up idle ClickHouse connection")
                            self._close_connection_safely(client)
                    
                    self._pool = active_connections
                    
            except Exception as e:
                logger.error(f"Error in connection cleanup: {e}")
    
    def _close_connection_safely(self, client: Client):
        """Safely close a connection and update stats"""
        try:
            client.close()
            stats = self._stats.pop(id(client), None)
            if stats:
                self._created_connections -= 1
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "created_connections": self._created_connections,
                "max_connections": self.max_connections,
                "total_queries": sum(stats.query_count for stats in self._stats.values()),
                "total_errors": sum(stats.error_count for stats in self._stats.values()),
                "average_query_time": sum(stats.total_query_time for stats in self._stats.values()) / max(1, sum(stats.query_count for stats in self._stats.values()))
            }


class QueryCache:
    """Simple in-memory cache for query results"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = {}
        self._lock = threading.RLock()
    
    def get(self, query: str, params: Optional[Dict] = None) -> Optional[QueryResult]:
        """Get cached query result if available and not expired"""
        cache_key = self._generate_cache_key(query, params)
        
        with self._lock:
            if cache_key in self._cache:
                result, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self.ttl_seconds:
                    logger.debug(f"Cache HIT for query: {query[:50]}...")
                    return result
                else:
                    del self._cache[cache_key]
        
        return None
    
    def set(self, query: str, result: QueryResult, params: Optional[Dict] = None):
        """Cache query result"""
        cache_key = self._generate_cache_key(query, params)
        
        with self._lock:
            # Implement LRU eviction if cache is full
            if len(self._cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            
            self._cache[cache_key] = (result, time.time())
            logger.debug(f"Cached query result: {query[:50]}...")
    
    def _generate_cache_key(self, query: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from query and parameters"""
        key_data = query
        if params:
            key_data += json.dumps(params, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def clear(self):
        """Clear all cached results"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds
            }


class OptimizedClickHouseConnector:
    """Optimized ClickHouse connector with connection pooling and caching"""
    
    def __init__(self, pool_size: int = 10, cache_size: int = 1000, cache_ttl: int = 300):
        self.connection_pool = ConnectionPool(max_connections=pool_size)
        self.query_cache = QueryCache(max_size=cache_size, ttl_seconds=cache_ttl)
        self._stats = defaultdict(int)
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, 
                     use_cache: bool = True, cache_ttl: Optional[int] = None) -> QueryResult:
        """
        Execute a query with connection pooling and optional caching
        
        Args:
            query: SQL query to execute
            params: Optional parameters for parameterized queries
            use_cache: Whether to use query result caching
            cache_ttl: Override default cache TTL for this query
            
        Returns:
            QueryResult: Query results from ClickHouse
        """
        # Check cache first
        if use_cache:
            cached_result = self.query_cache.get(query, params)
            if cached_result:
                self._stats["cache_hits"] += 1
                return cached_result
            self._stats["cache_misses"] += 1
        
        # Execute query with connection pooling
        client = None
        start_time = time.time()
        
        try:
            client = self.connection_pool.get_connection()
            
            if params:
                result = client.query(query, parameters=params)
            else:
                result = client.query(query)
            
            execution_time = time.time() - start_time
            
            # Update stats
            self._stats["total_queries"] += 1
            self._stats["total_query_time"] += execution_time
            
            # Cache result if enabled
            if use_cache:
                if cache_ttl:
                    # Temporarily override cache TTL
                    original_ttl = self.query_cache.ttl_seconds
                    self.query_cache.ttl_seconds = cache_ttl
                    self.query_cache.set(query, result, params)
                    self.query_cache.ttl_seconds = original_ttl
                else:
                    self.query_cache.set(query, result, params)
            
            logger.debug(f"Query executed in {execution_time:.3f}s: {query[:100]}...")
            return result
            
        except Exception as e:
            self._stats["query_errors"] += 1
            error_message = str(e)
            logger.error(f"ClickHouse query failed: {error_message}")
            
            # Enhanced error handling for Azure Container Apps
            if "connection" in error_message.lower() or "timeout" in error_message.lower():
                logger.warning("Connection/timeout error detected - this may be due to Azure Container Apps networking")
            
            raise Exception(f"ClickHouse query failed: {error_message}")
            
        finally:
            if client:
                self.connection_pool.return_connection(client)
    
    def execute_batch_queries(self, queries: List[Dict[str, Any]], 
                            use_cache: bool = True) -> List[QueryResult]:
        """
        Execute multiple queries efficiently using a single connection
        
        Args:
            queries: List of query dictionaries with 'query' and optional 'params' keys
            use_cache: Whether to use query result caching
            
        Returns:
            List[QueryResult]: List of query results
        """
        results = []
        client = None
        
        try:
            client = self.connection_pool.get_connection()
            
            for query_info in queries:
                query = query_info["query"]
                params = query_info.get("params")
                
                # Check cache first
                if use_cache:
                    cached_result = self.query_cache.get(query, params)
                    if cached_result:
                        results.append(cached_result)
                        self._stats["cache_hits"] += 1
                        continue
                    self._stats["cache_misses"] += 1
                
                # Execute query
                start_time = time.time()
                if params:
                    result = client.query(query, parameters=params)
                else:
                    result = client.query(query)
                
                execution_time = time.time() - start_time
                self._stats["total_queries"] += 1
                self._stats["total_query_time"] += execution_time
                
                # Cache result
                if use_cache:
                    self.query_cache.set(query, result, params)
                
                results.append(result)
            
            logger.info(f"Executed batch of {len(queries)} queries")
            return results
            
        except Exception as e:
            self._stats["query_errors"] += 1
            logger.error(f"Batch query execution failed: {e}")
            raise Exception(f"Batch query execution failed: {str(e)}")
            
        finally:
            if client:
                self.connection_pool.return_connection(client)
    
    async def execute_query_async(self, query: str, params: Optional[Dict[str, Any]] = None,
                                 use_cache: bool = True) -> QueryResult:
        """
        Execute query asynchronously (non-blocking)
        
        Args:
            query: SQL query to execute
            params: Optional parameters for parameterized queries
            use_cache: Whether to use query result caching
            
        Returns:
            QueryResult: Query results from ClickHouse
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.execute_query, 
            query, 
            params, 
            use_cache
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get connector health status and performance metrics"""
        try:
            start_time = time.time()
            result = self.execute_query("SELECT 1 as health_check", use_cache=False)
            response_time = (time.time() - start_time) * 1000
            
            pool_stats = self.connection_pool.get_stats()
            cache_stats = self.query_cache.get_stats()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "connection_pool": pool_stats,
                "query_cache": cache_stats,
                "query_stats": dict(self._stats),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def clear_cache(self):
        """Clear query result cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")


# Global optimized connector instance
_optimized_connector = None
_connector_lock = threading.Lock()


def get_optimized_clickhouse_connector() -> OptimizedClickHouseConnector:
    """
    Get the global optimized ClickHouse connector instance (singleton pattern)
    
    Returns:
        OptimizedClickHouseConnector: The global connector instance
    """
    global _optimized_connector
    
    if _optimized_connector is None:
        with _connector_lock:
            if _optimized_connector is None:
                # Configure based on environment
                pool_size = int(os.getenv("CLICKHOUSE_POOL_SIZE", "10"))
                cache_size = int(os.getenv("CLICKHOUSE_CACHE_SIZE", "1000"))
                cache_ttl = int(os.getenv("CLICKHOUSE_CACHE_TTL", "300"))
                
                _optimized_connector = OptimizedClickHouseConnector(
                    pool_size=pool_size,
                    cache_size=cache_size,
                    cache_ttl=cache_ttl
                )
                
                logger.info(f"Initialized optimized ClickHouse connector (pool: {pool_size}, cache: {cache_size})")
    
    return _optimized_connector


def execute_optimized_clickhouse_query(query: str, params: Optional[Dict[str, Any]] = None,
                                     use_cache: bool = True, cache_ttl: Optional[int] = None) -> QueryResult:
    """
    Execute a ClickHouse query using the optimized connector
    
    Args:
        query: SQL query to execute
        params: Optional parameters for parameterized queries
        use_cache: Whether to use query result caching
        cache_ttl: Override default cache TTL for this query
        
    Returns:
        QueryResult: Query results from ClickHouse
    """
    connector = get_optimized_clickhouse_connector()
    return connector.execute_query(query, params, use_cache, cache_ttl)


# Convenience functions for backward compatibility
def get_clickhouse_connector_optimized() -> Client:
    """
    Get a single ClickHouse connection from the optimized pool
    
    Note: This is for backward compatibility. Use execute_optimized_clickhouse_query() instead.
    """
    connector = get_optimized_clickhouse_connector()
    return connector.connection_pool.get_connection()


def check_optimized_clickhouse_health() -> Dict[str, Any]:
    """
    Check ClickHouse connection health using optimized connector
    
    Returns:
        Dict containing health status and performance metrics
    """
    connector = get_optimized_clickhouse_connector()
    return connector.get_health_status()
