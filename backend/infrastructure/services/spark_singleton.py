"""
Spark Singleton Service - Pre-initialized Spark session for optimal performance.
Eliminates Spark initialization overhead by keeping a single session alive.
"""
import logging
import threading
from typing import Optional
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)


class SparkSingleton:
    """
    Singleton pattern for Spark session to eliminate initialization overhead.
    Initializes Spark once and reuses the session across all requests.
    """
    
    _instance = None
    _lock = threading.Lock()
    _spark_session = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SparkSingleton, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._initialize_spark()
                    self._initialized = True
    
    def _initialize_spark(self):
        """
        Initialize Spark session with optimized configuration.
        This runs only once when the singleton is first created.
        """
        try:
            logger.info("Initializing Spark session for optimal performance...")
            
            # Import here to avoid circular imports
            from config.spark_connection_optimized import get_spark_connection
            
            # Get the pre-configured Spark session
            self._spark_session = get_spark_connection()
            
            # Set additional runtime optimizations
            try:
                self._spark_session.conf.set("spark.sql.adaptive.enabled", "true")
                self._spark_session.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
                self._spark_session.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
                logger.info("Applied runtime performance optimizations")
            except Exception as e:
                logger.warning(f"Could not set some performance configs: {e}")
            
            logger.info("Spark session initialized successfully and ready for use")
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            # Don't raise the exception, just log it and set to None
            self._spark_session = None
            logger.warning("Spark will be unavailable. Services will use fallback methods.")
    
    @property
    def spark(self) -> SparkSession:
        """
        Get the pre-initialized Spark session.
        Returns the same session instance across all calls.
        """
        if self._spark_session is None:
            logger.warning("Spark session not available. Returning None.")
            return None
        return self._spark_session
    
    def get_spark_session(self) -> SparkSession:
        """
        Get the pre-initialized Spark session.
        Alias for the spark property for backward compatibility.
        """
        return self.spark
    
    def is_initialized(self) -> bool:
        """
        Check if Spark session is initialized and ready.
        """
        return self._spark_session is not None
    
    def get_spark_info(self) -> dict:
        """
        Get information about the Spark session.
        """
        if not self.is_initialized():
            return {"status": "not_initialized"}
        
        try:
            return {
                "status": "initialized",
                "app_name": self._spark_session.conf.get("spark.app.name"),
                "master": self._spark_session.conf.get("spark.master"),
                "timestamp_type": self._spark_session.conf.get("spark.sql.parquet.timestampType"),
                "output_timestamp_type": self._spark_session.conf.get("spark.sql.parquet.outputTimestampType"),
                "adaptive_enabled": self._spark_session.conf.get("spark.sql.adaptive.enabled"),
                "version": self._spark_session.version
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def stop(self):
        """
        Stop the Spark session. Use with caution - this will affect all users.
        """
        if self._spark_session is not None:
            logger.info("Stopping Spark session...")
            self._spark_session.stop()
            self._spark_session = None
            self._initialized = False
            logger.info("Spark session stopped")


# Global instance - initialized when first imported
_spark_singleton = None

def get_spark_singleton() -> SparkSingleton:
    """
    Get the global Spark singleton instance.
    Initializes Spark on first call.
    """
    global _spark_singleton
    if _spark_singleton is None:
        _spark_singleton = SparkSingleton()
    return _spark_singleton

def get_spark_session() -> SparkSession:
    """
    Get the pre-initialized Spark session.
    Convenience function for easy access.
    """
    return get_spark_singleton().spark

def initialize_spark():
    """
    Explicitly initialize Spark singleton.
    Can be called at application startup for early initialization.
    """
    return get_spark_singleton()

def get_spark_info() -> dict:
    """
    Get Spark session information.
    """
    return get_spark_singleton().get_spark_info()
