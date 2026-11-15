"""
Repository for Dash-029 (RO Power Consumption) ClickHouse queries.

This repository handles direct ClickHouse queries that bypass the standard
datetime handling to avoid AMBIGUOUS_COLUMN_NAME errors when the DateTime
column is stored as String type.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from config.clickhouse_connector import execute_clickhouse_query
from constants import CLICKHOUSE_FALLBACK_DAYS

logger = logging.getLogger(__name__)


class Dash029Repository:
    """Repository for Dash-029 RO Power Consumption queries."""
    
    def __init__(self):
        self.database = os.getenv('CLICKHOUSE_DATABASE', 'swro_db')
    
    def get_power_consumption_data(
        self,
        clickhouse_table_name: str,
        columns_to_fetch: List[str],
        datetime_column: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        rack_column: str = "Rack",
        limit: int = 10000
    ) -> Dict[str, Any]:
        """
        Fetch power consumption data grouped by Rack with AVG aggregation.
        
        This method uses direct SQL queries to avoid the AMBIGUOUS_COLUMN_NAME
        error that occurs when the DateTime column is stored as String type
        and the standard repository applies automatic datetime conversions.
        
        Args:
            clickhouse_table_name: Name of the ClickHouse table
            columns_to_fetch: List of column names to fetch
            datetime_column: Name of the datetime column for filtering
            start_time: Start datetime for filtering
            end_time: End datetime for filtering
            rack_column: Name of the column to group by (default: "Rack")
            limit: Maximum number of rows to return
            
        Returns:
            Dict containing:
                - result_rows: List of tuples with query results
                - data_availability_for_given_date: Boolean indicating if data was found
                - from_date: Start date string
                - to_date: End date string
        """
        # Build SELECT with GROUP BY and AVG for numeric columns
        numeric_columns = [col for col in columns_to_fetch if col != rack_column]
        
        select_parts = [f"`{rack_column}`"]
        for col in numeric_columns:
            select_parts.append(f"AVG(`{col}`) as `{col}`")
        
        select_cols = ", ".join(select_parts)
        base_query = f"SELECT {select_cols} FROM `{self.database}`.`{clickhouse_table_name}`"
        
        query_params = {}
        from_date_str = None
        to_date_str = None
        
        if datetime_column and start_time and end_time:
            # Convert datetime to string format for consistent handling
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(start_time, 'strftime') else str(start_time)
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(end_time, 'strftime') else str(end_time)
            from_date_str = start_time.strftime('%Y-%m-%d') if hasattr(start_time, 'strftime') else str(start_time)[:10]
            to_date_str = end_time.strftime('%Y-%m-%d') if hasattr(end_time, 'strftime') else str(end_time)[:10]
            
            # Use simple string comparison since the column is stored as String type
            query = base_query + f" WHERE `{datetime_column}` >= {{start_date:String}} AND `{datetime_column}` <= {{end_date:String}}"
            query_params["start_date"] = start_time_str
            query_params["end_date"] = end_time_str
        else:
            query = base_query
        
        # Add GROUP BY and ORDER BY (extract numeric part for proper sorting)
        query += f" GROUP BY `{rack_column}` ORDER BY toUInt32OrZero(replaceRegexpAll(`{rack_column}`, '\\\\D', '')) ASC LIMIT {limit}"
        
        # Execute the query
        try:
            query_result = execute_clickhouse_query(query, params=query_params)
            result_rows = query_result.result_rows if query_result else []
        except Exception as e:
            logger.error(f"Failed to retrieve power consumption data: {str(e)}")
            raise Exception(f"Failed to retrieve column data: {str(e)}")
        
        data_availability_for_given_date = len(result_rows) > 0
        
        # Apply fallback mechanism if no data found
        if len(result_rows) == 0 and datetime_column and from_date_str:
            fallback_result = self._apply_fallback(
                clickhouse_table_name=clickhouse_table_name,
                base_query=base_query,
                datetime_column=datetime_column,
                rack_column=rack_column,
                from_date_str=from_date_str,
                limit=limit
            )
            
            if fallback_result:
                result_rows = fallback_result["result_rows"]
                from_date_str = fallback_result["from_date_str"]
                to_date_str = fallback_result["to_date_str"]
                data_availability_for_given_date = False  # Flag that we used fallback
        
        return {
            "result_rows": result_rows,
            "data_availability_for_given_date": data_availability_for_given_date,
            "from_date": from_date_str,
            "to_date": to_date_str
        }
    
    def get_weighted_heatmap_data(
        self,
        clickhouse_table_name: str,
        columns_to_fetch: List[str],
        datetime_column: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10000
    ) -> Dict[str, Any]:
        """
        Fetch weighted heatmap data without aggregation.
        
        This method uses direct SQL queries to avoid the AMBIGUOUS_COLUMN_NAME
        error that occurs when the DateTime column is stored as String type
        and the standard repository applies automatic datetime conversions.
        
        Args:
            clickhouse_table_name: Name of the ClickHouse table
            columns_to_fetch: List of column names to fetch
            datetime_column: Name of the datetime column for filtering
            start_time: Start datetime for filtering
            end_time: End datetime for filtering
            limit: Maximum number of rows to return
            
        Returns:
            Dict containing:
                - result_rows: List of tuples with query results
                - data_availability_for_given_date: Boolean indicating if data was found
                - from_date: Start date string
                - to_date: End date string
        """
        # Build SELECT - include datetime column for later filtering
        all_columns = [datetime_column] + columns_to_fetch if datetime_column else columns_to_fetch
        select_parts = [f"`{col}`" for col in all_columns]
        select_cols = ", ".join(select_parts)
        base_query = f"SELECT {select_cols} FROM `{self.database}`.`{clickhouse_table_name}`"
        
        query_params = {}
        from_date_str = None
        to_date_str = None
        
        if datetime_column and start_time and end_time:
            # Convert datetime to string format for consistent handling
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(start_time, 'strftime') else str(start_time)
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(end_time, 'strftime') else str(end_time)
            from_date_str = start_time.strftime('%Y-%m-%d') if hasattr(start_time, 'strftime') else str(start_time)[:10]
            to_date_str = end_time.strftime('%Y-%m-%d') if hasattr(end_time, 'strftime') else str(end_time)[:10]
            
            # Use simple string comparison since the column may be stored as String type
            query = base_query + f" WHERE `{datetime_column}` >= {{start_date:String}} AND `{datetime_column}` <= {{end_date:String}}"
            query_params["start_date"] = start_time_str
            query_params["end_date"] = end_time_str
        else:
            query = base_query
        
        # Add ORDER BY datetime and LIMIT
        if datetime_column:
            query += f" ORDER BY `{datetime_column}` DESC"
        query += f" LIMIT {limit}"
        
        # Execute the query
        try:
            query_result = execute_clickhouse_query(query, params=query_params)
            result_rows = query_result.result_rows if query_result else []
        except Exception as e:
            logger.error(f"Failed to retrieve weighted heatmap data: {str(e)}")
            raise Exception(f"Failed to retrieve column data: {str(e)}")
        
        data_availability_for_given_date = len(result_rows) > 0
        
        # Apply fallback mechanism if no data found
        if len(result_rows) == 0 and datetime_column and from_date_str:
            fallback_result = self._apply_heatmap_fallback(
                clickhouse_table_name=clickhouse_table_name,
                base_query=base_query,
                datetime_column=datetime_column,
                from_date_str=from_date_str,
                limit=limit
            )
            
            if fallback_result:
                result_rows = fallback_result["result_rows"]
                from_date_str = fallback_result["from_date_str"]
                to_date_str = fallback_result["to_date_str"]
                data_availability_for_given_date = False  # Flag that we used fallback
        
        return {
            "result_rows": result_rows,
            "data_availability_for_given_date": data_availability_for_given_date,
            "from_date": from_date_str,
            "to_date": to_date_str
        }
    
    def _apply_heatmap_fallback(
        self,
        clickhouse_table_name: str,
        base_query: str,
        datetime_column: str,
        from_date_str: str,
        limit: int
    ) -> Optional[Dict[str, Any]]:
        """
        Apply fallback mechanism to find the most recent available data for heatmap queries.
        
        Args:
            clickhouse_table_name: Name of the ClickHouse table
            base_query: Base SELECT query
            datetime_column: Name of the datetime column
            from_date_str: Original requested start date
            limit: Maximum number of rows
            
        Returns:
            Dict with fallback results or None if no data found
        """
        # Find the last available date in the table
        last_date_query = f"""
            SELECT MAX(`{datetime_column}`) 
            FROM `{self.database}`.`{clickhouse_table_name}`
            WHERE `{datetime_column}` < {{requested_start:String}}
        """
        
        try:
            last_date_result = execute_clickhouse_query(
                last_date_query, 
                params={"requested_start": from_date_str + ' 00:00:00'}
            )
            last_available = last_date_result.result_rows[0][0] if last_date_result.result_rows and last_date_result.result_rows[0][0] else None
            
            if not last_available:
                logger.warning(f"No fallback data available before {from_date_str}")
                return None
            
            # Parse the last available date
            if hasattr(last_available, 'strftime'):
                last_available_str = last_available.strftime('%Y-%m-%d')
            else:
                last_available_str = str(last_available)[:10]
            
            # Calculate fallback range: 7 days ending at last_available_date
            last_date_obj = datetime.strptime(last_available_str, '%Y-%m-%d')
            fallback_start = (last_date_obj - timedelta(days=CLICKHOUSE_FALLBACK_DAYS - 1)).strftime('%Y-%m-%d')
            fallback_end = last_available_str
            
            logger.info(f"Applying heatmap fallback: {fallback_start} to {fallback_end} (original: {from_date_str})")
            
            # Re-query with fallback date range
            fallback_query = base_query + f" WHERE `{datetime_column}` >= {{start_date:String}} AND `{datetime_column}` <= {{end_date:String}} ORDER BY `{datetime_column}` DESC LIMIT {limit}"
            fallback_params = {
                "start_date": fallback_start + ' 00:00:00',
                "end_date": fallback_end + ' 23:59:59'
            }
            
            fallback_result = execute_clickhouse_query(fallback_query, params=fallback_params)
            result_rows = fallback_result.result_rows if fallback_result else []
            
            return {
                "result_rows": result_rows,
                "from_date_str": fallback_start,
                "to_date_str": fallback_end
            }
            
        except Exception as fallback_error:
            logger.error(f"Heatmap fallback query failed: {str(fallback_error)}")
            return None

    def _apply_fallback(
        self,
        clickhouse_table_name: str,
        base_query: str,
        datetime_column: str,
        rack_column: str,
        from_date_str: str,
        limit: int
    ) -> Optional[Dict[str, Any]]:
        """
        Apply fallback mechanism to find the most recent available data.
        
        Args:
            clickhouse_table_name: Name of the ClickHouse table
            base_query: Base SELECT query
            datetime_column: Name of the datetime column
            rack_column: Name of the rack column for ordering
            from_date_str: Original requested start date
            limit: Maximum number of rows
            
        Returns:
            Dict with fallback results or None if no data found
        """
        # Find the last available date in the table
        last_date_query = f"""
            SELECT MAX(`{datetime_column}`) 
            FROM `{self.database}`.`{clickhouse_table_name}`
            WHERE `{datetime_column}` < {{requested_start:String}}
        """
        
        try:
            last_date_result = execute_clickhouse_query(
                last_date_query, 
                params={"requested_start": from_date_str + ' 00:00:00'}
            )
            last_available = last_date_result.result_rows[0][0] if last_date_result.result_rows and last_date_result.result_rows[0][0] else None
            
            if not last_available:
                logger.warning(f"No fallback data available before {from_date_str}")
                return None
            
            # Parse the last available date
            if hasattr(last_available, 'strftime'):
                last_available_str = last_available.strftime('%Y-%m-%d')
            else:
                last_available_str = str(last_available)[:10]
            
            # Calculate fallback range: 7 days ending at last_available_date
            last_date_obj = datetime.strptime(last_available_str, '%Y-%m-%d')
            fallback_start = (last_date_obj - timedelta(days=CLICKHOUSE_FALLBACK_DAYS - 1)).strftime('%Y-%m-%d')
            fallback_end = last_available_str
            
            logger.info(f"Applying fallback: {fallback_start} to {fallback_end} (original: {from_date_str})")
            
            # Re-query with fallback date range
            fallback_query = base_query + f" WHERE `{datetime_column}` >= {{start_date:String}} AND `{datetime_column}` <= {{end_date:String}} GROUP BY `{rack_column}` ORDER BY toUInt32OrZero(replaceRegexpAll(`{rack_column}`, '\\\\D', '')) ASC LIMIT {limit}"
            fallback_params = {
                "start_date": fallback_start + ' 00:00:00',
                "end_date": fallback_end + ' 23:59:59'
            }
            
            fallback_result = execute_clickhouse_query(fallback_query, params=fallback_params)
            result_rows = fallback_result.result_rows if fallback_result else []
            
            return {
                "result_rows": result_rows,
                "from_date_str": fallback_start,
                "to_date_str": fallback_end
            }
            
        except Exception as fallback_error:
            logger.error(f"Fallback query failed: {str(fallback_error)}")
            return None
