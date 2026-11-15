import logging
import os
from typing import Any, Dict, Optional

import clickhouse_connect
from clickhouse_connect.driver import Client
from clickhouse_connect.driver.query import QueryResult

from constants import ClickHouseConfig, ErrorMessages

logger = logging.getLogger(__name__)


def get_clickhouse_connector(auto_create_database: bool = False) -> Client:
    """
    Creates and returns a ClickHouse client connection.

    Example:
        >>> client = get_clickhouse_connector()
        >>> result = client.query("SELECT 1")
        >>> client.close()

    Args:
        auto_create_database: If True, automatically creates the database if it doesn't exist

    Returns:
        Client: ClickHouse client instance configured from environment variables

    Raises:
        ValueError: If CLICKHOUSE_USERNAME or CLICKHOUSE_PASSWORD not set
        Exception: If connection to ClickHouse fails
    """
    # Get environment variables
    host = os.getenv(ClickHouseConfig.CLICKHOUSE_HOST, ClickHouseConfig.DEFAULT_HOST)
    port = int(os.getenv(ClickHouseConfig.CLICKHOUSE_PORT, ClickHouseConfig.DEFAULT_PORT))
    username = os.getenv(ClickHouseConfig.CLICKHOUSE_USERNAME)
    password = os.getenv(ClickHouseConfig.CLICKHOUSE_PASSWORD)
    database = os.getenv(ClickHouseConfig.CLICKHOUSE_DATABASE, ClickHouseConfig.DEFAULT_DATABASE)
    timezone = os.getenv('CLICKHOUSE_TIMEZONE', 'Asia/Dubai')
    secure = os.getenv(ClickHouseConfig.CLICKHOUSE_SECURE, "0") in ("1", "true", "True")
    connect_timeout = int(os.getenv(
        ClickHouseConfig.CLICKHOUSE_CONNECT_TIMEOUT,
        ClickHouseConfig.DEFAULT_CONNECT_TIMEOUT
    ))
    send_receive_timeout = int(os.getenv(
        ClickHouseConfig.CLICKHOUSE_SEND_RECEIVE_TIMEOUT,
        ClickHouseConfig.DEFAULT_SEND_RECEIVE_TIMEOUT
    ))

    logger.debug("Attempting to connect to ClickHouse at %s:%s with timezone %s", host, port, timezone)

    # Validate required environment variables
    if not username:
        raise ValueError(ErrorMessages.CLICKHOUSE_USERNAME_NOT_SET)
    if password is None:  # Allow empty string for no password, but not None
        raise ValueError(ErrorMessages.CLICKHOUSE_PASSWORD_NOT_SET)

    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            secure=secure,
            connect_timeout=connect_timeout,
            send_receive_timeout=send_receive_timeout,
            session_id=None,  # Don't reuse sessions
            pool_mgr=None,  # No connection pooling to avoid session conflicts
            settings={
                'session_timezone': timezone,  # Set session timezone
                'use_client_time_zone': 1      # Use client timezone for DateTime
            }
        )

        # Test the connection
        client.ping()

        logger.info("Successfully connected to ClickHouse database: %s with timezone: %s", database, timezone)
        return client

    except Exception as e:
        error_msg = str(e)

        # If auto_create_database is True and database doesn't exist, create it
        if auto_create_database and ("Database" in error_msg and "does not exist" in error_msg):
            logger.info(f"Database {database} does not exist. Creating it automatically...")

            try:
                # Connect to default database to create the new database
                temp_client = clickhouse_connect.get_client(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    database='default',
                    secure=secure,
                    connect_timeout=connect_timeout,
                    send_receive_timeout=send_receive_timeout,
                )

                # Create the database
                temp_client.command(f"CREATE DATABASE IF NOT EXISTS {database}")
                temp_client.close()
                logger.info(f"Successfully created database: {database}")

                # Now try connecting to the newly created database
                client = clickhouse_connect.get_client(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    database=database,
                    secure=secure,
                    connect_timeout=connect_timeout,
                    send_receive_timeout=send_receive_timeout,
                    session_id=None,
                    pool_mgr=None,
                    settings={
                        'session_timezone': timezone,
                        'use_client_time_zone': 1
                    }
                )

                client.ping()
                logger.info("Successfully connected to newly created database: %s", database)
                return client

            except Exception as create_error:
                logger.error(f"Failed to auto-create database {database}: {create_error}")
                raise Exception(f"Failed to connect to ClickHouse and could not auto-create database: {create_error}")

        logger.error("Failed to connect to ClickHouse: %s", error_msg)
        raise Exception(ErrorMessages.CLICKHOUSE_CONNECTION_FAILED.format(error=error_msg))


def execute_clickhouse_query(query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
    """
    Execute a query on ClickHouse and return results.

    Example:
        >>> result = execute_clickhouse_query("SELECT * FROM users WHERE id = {id:Int32}", {"id": 1})
        >>> print(result.result_rows)

    Args:
        query: SQL query to execute
        params: Optional parameters for parameterized queries

    Returns:
        QueryResult: Query results from ClickHouse

    Raises:
        Exception: If query execution fails
    """
    client = None
    try:
        client = get_clickhouse_connector()

        if params:
            result = client.query(query, parameters=params)
        else:
            result = client.query(query)

        return result

    except Exception as e:
        error_message = str(e)
        logger.error("ClickHouse query failed: %s", error_message)
        
        # Check for specific JSON parse errors
        if "JSON parse error" in error_message:
            logger.error("JSON parse error detected - this might be due to malformed data in ClickHouse")
            logger.error("Query that failed: %s", query)
            logger.error("Parameters used: %s", params)
        
        raise Exception(ErrorMessages.CLICKHOUSE_QUERY_FAILED.format(error=error_message))
    finally:
        if client:
            client.close()
            logger.debug("ClickHouse connection closed")


def validate_table_name(table_name: str) -> str:
    """
    Validate table name to prevent SQL injection.

    Args:
        table_name: Table name to validate

    Returns:
        str: Validated table name

    Raises:
        ValueError: If table name contains invalid characters
    """
    import re
    if not re.match(r'^[a-zA-Z0-9_\.]+$', table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name


def check_clickhouse_health() -> Dict[str, Any]:
    """
    Check ClickHouse connection health.

    Returns:
        Dict containing health status and response time or error
    """
    try:
        import time
        start_time = time.time()
        client = get_clickhouse_connector()
        result = client.query("SELECT 1 as health_check")
        client.close()
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return {
            "status": "healthy",
            "response_time_ms": elapsed_time
        }
    except Exception as e:
        logger.error(f"ClickHouse health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }