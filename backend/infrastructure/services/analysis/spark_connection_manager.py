"""
Spark Connection Manager - Advanced connection pooling and optimization
Provides centralized Spark session management with connection pooling and health monitoring.
"""
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from threading import Lock, RLock
import threading

from infrastructure.services.spark_singleton import get_spark_session
from infrastructure.utils.datetime_utils import DateTimeParser

logger = logging.getLogger(__name__)


class SparkConnectionManager:
    """
    Advanced Spark connection manager with pooling, health monitoring, and optimization.
    Ensures optimal Spark session reuse across all analysis services.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern for connection manager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._session_lock = RLock()
        self._spark_session = None
        self._session_created_at = None
        self._session_last_used = None
        self._session_use_count = 0
        self._connection_healthy = True
        
        # Configuration
        self.max_session_age = timedelta(hours=2)  # Recreate session after 2 hours
        self.max_idle_time = timedelta(minutes=30)  # Check health after 30 min idle
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = None
        
        # Statistics
        self.stats = {
            'total_sessions_created': 0,
            'total_operations': 0,
            'cache_hits': 0,
            'health_checks': 0,
            'session_recreations': 0
        }
        
        self._initialized = True
        logger.info("SparkConnectionManager initialized with advanced pooling")
    
    def get_spark_session(self, force_new: bool = False) -> Any:
        """
        Get optimized Spark session with health monitoring and automatic recreation.
        
        Args:
            force_new: Force creation of new session
            
        Returns:
            Spark session instance
        """
        with self._session_lock:
            current_time = datetime.now()
            
            # Check if we need a new session
            needs_new_session = (
                force_new or 
                self._spark_session is None or
                not self._connection_healthy or
                self._session_needs_recreation(current_time)
            )
            
            if needs_new_session:
                self._create_new_session()
            else:
                # Health check if needed
                if self._should_perform_health_check(current_time):
                    self._perform_health_check()
                
                self.stats['cache_hits'] += 1
            
            # Update usage statistics
            self._session_last_used = current_time
            self._session_use_count += 1
            self.stats['total_operations'] += 1
            
            logger.debug(f"Spark session provided (age: {self._get_session_age()}, uses: {self._session_use_count})")
            return self._spark_session
    
    def _session_needs_recreation(self, current_time: datetime) -> bool:
        """Check if session needs recreation based on age and idle time"""
        if not self._session_created_at or not self._session_last_used:
            return True
            
        # Check age limit
        session_age = current_time - self._session_created_at
        if session_age > self.max_session_age:
            logger.info(f"Session recreation needed: age {session_age} exceeds limit {self.max_session_age}")
            return True
        
        # Check idle time (for health concerns)
        idle_time = current_time - self._session_last_used
        if idle_time > self.max_idle_time:
            logger.info(f"Session health check needed: idle for {idle_time}")
            return False  # Just need health check, not recreation
            
        return False
    
    def _should_perform_health_check(self, current_time: datetime) -> bool:
        """Determine if health check is needed"""
        if not self.last_health_check:
            return True
            
        time_since_check = current_time - self.last_health_check
        return time_since_check.total_seconds() > self.health_check_interval
    
    def _create_new_session(self):
        """Create a new Spark session with optimized configuration"""
        try:
            logger.info("Creating new optimized Spark session")
            start_time = time.time()
            
            # Close existing session if any
            if self._spark_session:
                try:
                    self._spark_session.stop()
                except Exception as e:
                    logger.warning(f"Error stopping old Spark session: {e}")
            
            # Create new session using singleton (which has optimized config)
            self._spark_session = get_spark_session()
            
            # Update tracking
            current_time = datetime.now()
            self._session_created_at = current_time
            self._session_last_used = current_time
            self._session_use_count = 0
            self._connection_healthy = True
            
            # Update statistics
            self.stats['total_sessions_created'] += 1
            if self.stats['total_sessions_created'] > 1:
                self.stats['session_recreations'] += 1
            
            creation_time = time.time() - start_time
            logger.info(f"New Spark session created in {creation_time:.2f}s (total created: {self.stats['total_sessions_created']})")
            
        except Exception as e:
            logger.error(f"Failed to create Spark session: {e}")
            self._connection_healthy = False
            raise
    
    def _perform_health_check(self):
        """Perform health check on current Spark session"""
        try:
            logger.debug("Performing Spark session health check")
            start_time = time.time()
            
            # Simple health check - try to get Spark context info
            if self._spark_session:
                app_name = self._spark_session.sparkContext.appName
                logger.debug(f"Health check passed - app: {app_name}")
                self._connection_healthy = True
            else:
                self._connection_healthy = False
                
            self.last_health_check = datetime.now()
            self.stats['health_checks'] += 1
            
            health_check_time = time.time() - start_time
            logger.debug(f"Health check completed in {health_check_time:.3f}s")
            
        except Exception as e:
            logger.warning(f"Spark session health check failed: {e}")
            self._connection_healthy = False
    
    def _get_session_age(self) -> Optional[timedelta]:
        """Get current session age"""
        if self._session_created_at:
            return datetime.now() - self._session_created_at
        return None
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics and health information"""
        with self._session_lock:
            current_time = datetime.now()
            session_age = self._get_session_age()
            
            return {
                'healthy': self._connection_healthy,
                'session_created_at': DateTimeParser.format_datetime_without_timezone(self._session_created_at) if self._session_created_at else None,
                'session_age_seconds': session_age.total_seconds() if session_age else None,
                'session_use_count': self._session_use_count,
                'last_used_ago_seconds': (current_time - self._session_last_used).total_seconds() if self._session_last_used else None,
                'last_health_check': DateTimeParser.format_datetime_without_timezone(self.last_health_check) if self.last_health_check else None,
                'statistics': self.stats.copy()
            }
    
    def force_session_recreation(self):
        """Force recreation of Spark session (for administrative purposes)"""
        logger.info("Forcing Spark session recreation")
        with self._session_lock:
            self._create_new_session()
    
    def cleanup(self):
        """Clean up resources"""
        with self._session_lock:
            if self._spark_session:
                try:
                    logger.info("Cleaning up Spark session")
                    self._spark_session.stop()
                    self._spark_session = None
                except Exception as e:
                    logger.error(f"Error during Spark session cleanup: {e}")


# Global connection manager instance
_connection_manager = None
_manager_lock = Lock()

def get_spark_connection_manager() -> SparkConnectionManager:
    """Get the global Spark connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        with _manager_lock:
            if _connection_manager is None:
                _connection_manager = SparkConnectionManager()
    return _connection_manager

def get_optimized_spark_session(force_new: bool = False) -> Any:
    """
    Get optimized Spark session through connection manager.
    This is the recommended way to get Spark sessions in analysis services.
    
    Args:
        force_new: Force creation of new session
        
    Returns:
        Optimized Spark session
    """
    manager = get_spark_connection_manager()
    return manager.get_spark_session(force_new=force_new)
