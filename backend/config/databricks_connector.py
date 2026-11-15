import os
import logging
import threading
from databricks import sql

from constants import DatabaseConfig, ErrorMessages

logger = logging.getLogger(__name__)

# Global connection instance with thread safety
_connection = None
_connection_lock = threading.Lock()

def get_databricks_connector():
    """
    Get a Databricks connection with connection reuse and automatic reconnection.
    Implements singleton pattern - creates connection once and reuses it.
    """
    global _connection
    
    # Thread-safe connection creation/reuse
    with _connection_lock:
        if _connection is None:
            _create_connection()
        
        # Test connection and recreate if needed
        if not _test_connection(_connection):
            logger.warning("Connection test failed, recreating connection")
            _create_connection()
            
        return _connection

def _test_connection(connection):
    """Test if the connection is still valid."""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return True
    except Exception as e:
        logger.debug(f"Connection test failed: {e}")
        return False

def _create_connection():
    """Create a new Databricks connection (called once or on reconnection)."""
    global _connection
    
    # Close existing connection if any
    if _connection:
        try:
            _connection.close()
            logger.debug("Closed existing Databricks connection")
        except:
            pass
    
    # Get environment variables
    server_hostname = os.getenv(DatabaseConfig.SERVER_HOSTNAME)
    http_path = os.getenv(DatabaseConfig.HTTP_PATH)
    access_token = os.getenv(DatabaseConfig.ACCESS_TOKEN)

    # Validate that all required environment variables are present
    if not server_hostname:
        raise ValueError(ErrorMessages.SERVER_HOSTNAME_NOT_SET)
    if not http_path:
        raise ValueError(ErrorMessages.HTTP_PATH_NOT_SET)
    if not access_token:
        raise ValueError(ErrorMessages.ACCESS_TOKEN_NOT_SET)

    try:
        _connection = sql.connect(
            server_hostname=server_hostname,
            http_path=http_path,
            access_token=access_token,
        )
        logger.info("Created singleton Databricks connection (will be reused)")
    except Exception as e:
        logger.error(f"Failed to create Databricks connection: {e}")
        raise Exception(ErrorMessages.DATABRICKS_CONNECTION_FAILED.format(error=str(e)))

def close_databricks_connection():
    """Close the Databricks connection (for cleanup)."""
    global _connection
    
    with _connection_lock:
        if _connection:
            try:
                _connection.close()
                logger.info("Closed singleton Databricks connection")
            except Exception as e:
                logger.warning(f"Error closing Databricks connection: {e}")
            finally:
                _connection = None
