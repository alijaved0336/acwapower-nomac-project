import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import re
import os

from config.clickhouse_connector import execute_clickhouse_query, validate_table_name

logger = logging.getLogger(__name__)

class Dash002Repository:
    """Repository for handling ClickHouse-related database queries"""

    def __init__(self):
        """Initialize repository"""
        pass

    def _get_timezone(self) -> str:
        """
        Get the configured timezone for the application.
        
        Returns:
            str: Timezone string (e.g., 'Asia/Dubai')            import os

        """
        import os
        return os.getenv('CLICKHOUSE_TIMEZONE', 'Asia/Dubai')
    
    def get_max_timestamp(self, clickhouse_table_name: str, datetime_column: str) -> Optional[datetime]:
        """
        Get the maximum (most recent) timestamp from a table.
        
        Args:
            clickhouse_table_name: ClickHouse table name
            datetime_column: DateTime column to query
            
        Returns:
            Maximum datetime or None if no data
        """
        if not datetime_column:
            logger.warning(f"No datetime column provided for table {clickhouse_table_name}")
            return None
        
        try:
            import os
            database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
            timezone = self._get_timezone()
            
            query = f"""
            SELECT MAX(if(toTypeName(`{datetime_column}`) LIKE '%String%',
                toTimeZone(parseDateTime64BestEffort(`{datetime_column}`), '{timezone}'),
                toTimeZone(`{datetime_column}`, '{timezone}'))) as max_timestamp
            FROM `{database}`.`{clickhouse_table_name}`
            """
            
            result = execute_clickhouse_query(query)
            
            if result.result_rows and result.result_rows[0][0]:
                max_timestamp = result.result_rows[0][0]
                logger.info(f"Max timestamp from {clickhouse_table_name}: {max_timestamp}")
                return max_timestamp
            
            logger.warning(f"No timestamp found in table {clickhouse_table_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting max timestamp from {clickhouse_table_name}: {e}")
            return None