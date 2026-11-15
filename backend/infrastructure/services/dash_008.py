"""
Dashboard 008 Service - Pump Analysis Business Logic
Handles operational trend and performance trend data retrieval.
"""

import logging
from typing import Dict, List, Optional

from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService
from infrastructure.orm.dash_008 import Dash008Repository
from config.clickhouse_connector import execute_clickhouse_query

logger = logging.getLogger(__name__)


class Dash008Service:
    """
    Service for Dashboard 008 - Pump Analysis functionality.
    Provides business logic for operational and performance trend data.
    """

    def __init__(self):
        """Initialize service with ClickHouse ADLS service dependency."""
        self.clickhouse_service = ClickHouseADLSService()
        self.dash008_repo = Dash008Repository()

    def _validate_site_exists(self, site_id: str) -> None:
        """Validate that the site exists in ClickHouse."""
        try:
            sites = self.clickhouse_service.get_sites()
            site_names = [site.get('name') for site in sites]
            if site_id not in site_names:
                raise ValueError(f"Site '{site_id}' not found. Available sites: {', '.join(site_names)}")
            logger.info(f"Site '{site_id}' validated successfully")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error validating site {site_id}: {str(e)}")
            raise Exception(f"Failed to validate site: {str(e)}")

    def _discover_operational_table(self, site_id: str, pump_type: str) -> tuple:
        """
        Discover the operational performance table.
        Returns tuple of (measured_table, expected_table)
        """
        try:
            logger.info(f"Starting table discovery for site: {site_id}, type: {pump_type}")
            tables = self.clickhouse_service.get_tables_for_site(site_id)
            table_names = [table.get('tableName') for table in tables]
            logger.info(f"Found {len(table_names)} tables for site {site_id}")

            # Try exact patterns (with Expected)
            pattern1_exp = f"{site_id}_Pumps_Operational_Performance_Expected_{pump_type}"
            pattern2_exp = f"{site_id}_Stream_All_Pumps_Operational_Performance_Expected_{pump_type}"
            
            # Try patterns without Expected (measured data)
            pattern1 = f"{site_id}_Pumps_Operational_Performance_{pump_type}"
            pattern2 = f"{site_id}_Stream_All_Pumps_Operational_Performance_{pump_type}"
            
            measured_table = None
            expected_table = None
            
            # Find measured table
            if pattern1 in table_names:
                measured_table = pattern1
            elif pattern2 in table_names:
                measured_table = pattern2

            # Find expected table
            if pattern1_exp in table_names:
                expected_table = pattern1_exp
            elif pattern2_exp in table_names:
                expected_table = pattern2_exp

            # Try lowercase if not found
            if not measured_table or not expected_table:
                pump_type_lower = pump_type.lower()
                pattern1_lower = f"{site_id}_Pumps_Operational_Performance_{pump_type_lower}"
                pattern2_lower = f"{site_id}_Stream_All_Pumps_Operational_Performance_{pump_type_lower}"
                pattern1_exp_lower = f"{site_id}_Pumps_Operational_Performance_Expected_{pump_type_lower}"
                pattern2_exp_lower = f"{site_id}_Stream_All_Pumps_Operational_Performance_Expected_{pump_type_lower}"
                
                if not measured_table:
                    if pattern1_lower in table_names:
                        measured_table = pattern1_lower
                    elif pattern2_lower in table_names:
                        measured_table = pattern2_lower
                
                if not expected_table:
                    if pattern1_exp_lower in table_names:
                        expected_table = pattern1_exp_lower
                    elif pattern2_exp_lower in table_names:
                        expected_table = pattern2_exp_lower

            # Fuzzy search as last resort
            if not measured_table or not expected_table:
                pump_type_search = pump_type.lower().replace('_', '').replace('-', '').replace("'", '')
                for table_name in table_names:
                    table_normalized = table_name.lower().replace('_', '').replace('-', '')
                    if pump_type_search in table_normalized and 'operationalperformance' in table_normalized:
                        if not measured_table and 'expected' not in table_normalized:
                            measured_table = table_name
                        if not expected_table and 'expected' in table_normalized:
                            expected_table = table_name

            # Use measured table for both if expected not found
            if not measured_table:
                error_msg = f"No operational table found for {site_id}/{pump_type}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not expected_table:
                logger.warning(f"No expected table found, using measured table: {measured_table}")
                expected_table = measured_table

            return measured_table, expected_table

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error discovering table: {str(e)}")
            raise Exception(f"Failed to discover table: {str(e)}")
    
    def _extract_dropdown_data(self, site_id: str, table_name_exp: str) -> List[str]:
        """Extract dropdown data from expected table."""
        try:
            logger.info(f"Extracting dropdown data from table: {table_name_exp}")
            tables_request = [{"siteName": site_id, "tableName": table_name_exp}]
            columns_info = self.clickhouse_service.get_columns_for_tables(tables_request)
            
            column_names = [col.get('columnName') for col in columns_info]
            expected_columns = set()
            measured_columns = set()

            for col_name in column_names:
                if col_name.endswith('_Expected'):
                    base_name = col_name.replace('_Expected', '')
                    expected_columns.add(base_name)
                elif col_name.endswith('_Measured'):
                    base_name = col_name.replace('_Measured', '')
                    measured_columns.add(base_name)

            paired_columns = expected_columns.intersection(measured_columns)
            dropdown_data = sorted(list(paired_columns))
            
            logger.info(f"Dropdown data: {dropdown_data}")
            return dropdown_data

        except Exception as e:
            logger.error(f"Error extracting dropdown data: {str(e)}")
            return []

    def _get_measured_table_column_mapping(self, site_id: str, measured_table: str) -> Dict[str, str]:
        """Get column name mapping for measured table."""
        try:
            clickhouse_table_name = self.clickhouse_service.repository.get_clickhouse_table_name(
                site_id, measured_table
            )
            
            if not clickhouse_table_name:
                return {}
            
            columns_query = f"DESCRIBE TABLE `{clickhouse_table_name}`"
            columns_result = execute_clickhouse_query(query=columns_query)
            column_names = [row[0] for row in columns_result.result_rows]
            
            mapping = {}
            base_names = ["Flow", "Efficiency", "Head", "Pump_Power", "SEC"]
            
            for base_name in base_names:
                patterns = [
                    f"{base_name}_Measured",
                    f"{base_name}_measured",
                    f"Pump_{base_name}",
                    base_name,
                ]
                
                for pattern in patterns:
                    if pattern in column_names:
                        mapping[base_name] = pattern
                        break
            
            logger.info(f"Column mapping: {mapping}")
            return mapping
            
        except Exception as e:
            logger.error(f"Error getting column mapping: {str(e)}")
            return {}

    def _format_column_data_with_labels(
        self, column_data: List[Dict], measured_columns_map: Dict[str, str]
    ) -> List[Dict]:
        """
        Format column data with consistent naming labels.
        Converts actual column names to standard format (e.g., Pump_Flow -> Flow_Measured).
        """
        try:
            # Create reverse mapping
            reverse_map = {v: k for k, v in measured_columns_map.items()}
            
            formatted_data = []
            
            for col in column_data:
                col_name = col.get('columnName')
                
                # Determine the display name
                if col_name in reverse_map:
                    # It's a measured column - use standard format
                    base_name = reverse_map[col_name]
                    display_name = f"{base_name}_Measured"
                elif col_name.endswith('_Expected'):
                    # Already in correct format
                    display_name = col_name
                else:
                    # Keep as-is (timestamp, Pump, Pump_ID, Speed, etc.)
                    display_name = col_name
                
                formatted_data.append({
                    "columnName": display_name,
                    "columnType": col.get('columnType'),
                    "tableName": col.get('tableName'),
                    "siteName": col.get('siteName'),
                    "dataSource": col.get('dataSource', [])
                })
            
            logger.info(f"Formatted {len(formatted_data)} columns with labels")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error formatting column data: {str(e)}")
            return column_data  # Return original on error

    def get_operational_trend_data(
        self, site_id: str, pump_type: str, pump_id: str,
        from_date: Optional[str], to_date: Optional[str]
    ) -> Dict:
        """
        Retrieve operational trend data in columnar format for a specific pump.
        Returns column_data in ClickHouse format with dropdown options.
        
        Args:
            site_id: Site identifier
            pump_type: Pump category/type
            pump_id: Specific pump ID (REQUIRED)
            from_date: Start date (optional)
            to_date: End date (optional)
        """
        try:
            logger.info(f"Getting operational trend: {site_id}/{pump_type}/{pump_id}")
            
            self._validate_site_exists(site_id)
            measured_table, expected_table = self._discover_operational_table(site_id, pump_type)
            
            if not from_date or not to_date:
                from_date, to_date = self.dash008_repo.get_latest_date_range_from_db(
                    site_id=site_id, table_name=measured_table, days=7
                )
                if not from_date or not to_date:
                    logger.warning(f"No date range found for {site_id}/{measured_table}")
                    return {
                        "column_data": [],
                        "dropdown_data": [],
                        "metadata": {
                            "data_availability_for_given_date": False,
                            "from_date": from_date,
                            "to_date": to_date
                        }
                    }
            
            # Get column mapping for measured table
            measured_columns_map = self._get_measured_table_column_mapping(site_id, measured_table)
            logger.info(f"Measured table column mapping: {measured_columns_map}")
            
            # Get dropdown data
            dropdown_data = self._extract_dropdown_data(site_id, expected_table)
            logger.info(f"Dropdown data: {dropdown_data}")
            
            # Build column request
            columns_request = [
                {"siteName": site_id, "tableName": measured_table, "columnName": "timestamp", "columnType": "timestamp[ns]"}
            ]
            
            # Add all paired columns (measured + expected)
            for base_column in dropdown_data:
                # Add Measured column from measured_table
                measured_col_name = measured_columns_map.get(base_column)
                if measured_col_name:
                    columns_request.append({
                        "siteName": site_id,
                        "tableName": measured_table,
                        "columnName": measured_col_name,
                        "columnType": "double"
                    })
                    logger.info(f"Added measured column: {measured_col_name} for {base_column}")
                
                # Add Expected column from expected_table
                columns_request.append({
                    "siteName": site_id,
                    "tableName": expected_table,
                    "columnName": f"{base_column}_Expected",
                    "columnType": "double"
                })
            
            logger.info(f"Requesting {len(columns_request)} columns for operational trend")
            
            # Apply pump_id filter
            filters = {"Pump_ID": pump_id}
            
            # Get data from ClickHouse - already in columnar format
            response = self.clickhouse_service.get_column_data_sources(
                columns_list=columns_request,
                from_date=from_date,
                to_date=to_date,
                rack=None,
                filters=filters,
                enable_fallback=True  # Dashboard API - enable fallback to last 7 days
            )
            
            # CRITICAL FIX: Handle nested response structure
            column_data = None
            metadata = {}
            
            if isinstance(response, dict):
                # Response is a dict with 'column_data' and 'metadata' keys
                column_data = response.get('column_data')
                metadata = response.get('metadata', {})
                logger.info(f"Extracted column_data from nested response structure")
            elif isinstance(response, list):
                # Direct list response (old format)
                column_data = response
                logger.info(f"Using direct list response")
            else:
                logger.error(f"Unexpected response type: {type(response).__name__}")
                return {
                    "column_data": [],
                    "dropdown_data": dropdown_data,
                    "metadata": {
                        "data_availability_for_given_date": False,
                        "from_date": from_date,
                        "to_date": to_date
                    }
                }
            
            if not column_data or not isinstance(column_data, list):
                logger.warning(f"No valid column data returned. Type: {type(column_data)}")
                return {
                    "column_data": [],
                    "dropdown_data": dropdown_data,
                    "metadata": {
                        "data_availability_for_given_date": metadata.get("data_availability_for_given_date", False),
                        "from_date": metadata.get("from_date", from_date),
                        "to_date": metadata.get("to_date", to_date)
                    }
                }
            
            logger.info(f"Retrieved {len(column_data)} columns for operational trend")
            
            # Convert to proper format with consistent naming
            formatted_column_data = self._format_column_data_with_labels(
                column_data, measured_columns_map
            )
            
            # Ensure metadata has all required fields
            if not metadata:
                metadata = {
                    "data_availability_for_given_date": True,
                    "from_date": from_date,
                    "to_date": to_date
                }
            
            return {
                "column_data": formatted_column_data,
                "dropdown_data": dropdown_data,
                "metadata": metadata
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error in get_operational_trend_data: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve operational trend data: {str(e)}")

    def get_performance_trend_data(
        self, site_id: str, pump_type: str, pump_id: str, 
        from_date: Optional[str], to_date: Optional[str]
    ) -> Dict:
        """
        Retrieve performance trend data in columnar format with VSD performance data.
        
        Args:
            site_id: Site identifier
            pump_type: Pump category/type
            pump_id: Specific pump ID (REQUIRED)
            from_date: Start date (optional)
            to_date: End date (optional)
        """
        try:
            logger.info(f"Getting performance trend: {site_id}/{pump_type}/{pump_id}")
            
            self._validate_site_exists(site_id)
            measured_table, expected_table = self._discover_operational_table(site_id, pump_type)
            
            if not from_date or not to_date:
                from_date, to_date = self.dash008_repo.get_latest_date_range_from_db(
                    site_id=site_id, table_name=measured_table, days=7
                )
                if not from_date or not to_date:
                    return {
                        "column_data": [],
                        "dropdown_data": [],
                        "vsd_performance_data": None,
                        "metadata": {
                            "data_availability_for_given_date": False,
                            "from_date": from_date,
                            "to_date": to_date
                        }
                    }
            
            # Get column mapping
            measured_columns_map = self._get_measured_table_column_mapping(site_id, measured_table)
            
            # Build column request
            columns_request = [
                {"siteName": site_id, "tableName": measured_table, "columnName": "timestamp", "columnType": "timestamp[ns]"},
                {"siteName": site_id, "tableName": measured_table, "columnName": "Pump", "columnType": "string"},
                {"siteName": site_id, "tableName": measured_table, "columnName": "Pump_ID", "columnType": "string"},
                {"siteName": site_id, "tableName": measured_table, "columnName": "Speed", "columnType": "double"},
            ]
            
            # Get dropdown data
            dropdown_data = self._extract_dropdown_data(site_id, expected_table)
            
            # Add paired columns
            for base_column in dropdown_data:
                measured_col_name = measured_columns_map.get(base_column)
                if measured_col_name:
                    columns_request.append({
                        "siteName": site_id,
                        "tableName": measured_table,
                        "columnName": measured_col_name,
                        "columnType": "double"
                    })
                columns_request.append({
                    "siteName": site_id,
                    "tableName": expected_table,
                    "columnName": f"{base_column}_Expected",
                    "columnType": "double"
                })
            
            # Apply pump_id filter
            filters = {"Pump_ID": pump_id}
            
            # Get data from ClickHouse - enable fallback for Dashboard APIs
            response = self.clickhouse_service.get_column_data_sources(
                columns_list=columns_request,
                from_date=from_date,
                to_date=to_date,
                rack=None,
                filters=filters,
                enable_fallback=True  # Dashboard API - enable fallback to last 7 days
            )
            
            # CRITICAL FIX: Handle nested response structure
            column_data = None
            metadata = {}
            
            if isinstance(response, dict):
                column_data = response.get('column_data')
                metadata = response.get('metadata', {})
                logger.info(f"Extracted column_data from nested response structure")
            elif isinstance(response, list):
                column_data = response
                logger.info(f"Using direct list response")
            else:
                logger.error(f"Unexpected response type: {type(response).__name__}")
                return {
                    "column_data": [],
                    "dropdown_data": dropdown_data,
                    "vsd_performance_data": None,
                    "metadata": {
                        "data_availability_for_given_date": False,
                        "from_date": from_date,
                        "to_date": to_date
                    }
                }
            
            if not column_data or not isinstance(column_data, list):
                logger.warning(f"No valid column data returned. Type: {type(column_data)}")
                return {
                    "column_data": [],
                    "dropdown_data": dropdown_data,
                    "vsd_performance_data": None,
                    "metadata": {
                        "data_availability_for_given_date": metadata.get("data_availability_for_given_date", False),
                        "from_date": metadata.get("from_date", from_date),
                        "to_date": metadata.get("to_date", to_date)
                    }
                }
            
            logger.info(f"Retrieved {len(column_data)} columns for performance trend")
            
            # Convert to proper format with consistent naming
            # This returns a LIST of formatted columns
            formatted_column_data = self._format_column_data_with_labels(
                column_data, measured_columns_map
            )
            
            # Ensure metadata has all required fields
            if not metadata:
                metadata = {
                    "data_availability_for_given_date": True,
                    "from_date": from_date,
                    "to_date": to_date
                }
            
            # Get VSD performance data
            # Use dates from metadata to ensure we use the same dates as the data retrieval (including fallback dates)
            actual_from_date = metadata.get("from_date", from_date)
            actual_to_date = metadata.get("to_date", to_date)
            vsd_performance_data = self._retrieve_vsd_performance_data(
                site_id, pump_type, measured_table, pump_id, actual_from_date, actual_to_date
            )

            # Return the properly structured response
            return {
                "column_data": formatted_column_data,  # This is already a list
                "dropdown_data": dropdown_data,
                "metadata": metadata,
                "vsd_performance_data": vsd_performance_data
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error in get_performance_trend_data: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve performance trend data: {str(e)}")

    def _retrieve_vsd_performance_data(
        self, site_id: str, pump_type: str, operational_table_name: str,
        pump_id: str, from_date: str, to_date: str
    ) -> Optional[Dict]:
        """Retrieve VSD Performance Expected Trend data."""
        try:
            # Discover VSD table
            vsd_table_name = self._discover_vsd_performance_table(site_id, pump_type)
            if not vsd_table_name:
                logger.info("No VSD table found")
                return None

            # Calculate speed ratio range
            speed_range = self._calculate_speed_ratio_range(
                site_id, operational_table_name, pump_id, from_date, to_date
            )
            if not speed_range:
                return None

            # Get VSD data
            vsd_rows = self._get_vsd_performance_data(
                site_id, vsd_table_name, pump_id,
                speed_range["min_speed_ratio"], speed_range["max_speed_ratio"]
            )
            
            if not vsd_rows:
                return {
                    "min_speed_ratio": speed_range["min_speed_ratio"],
                    "max_speed_ratio": speed_range["max_speed_ratio"],
                    "speed_groups": {}
                }

            # Group by speed ratio
            speed_groups = self._group_by_speed_ratio(vsd_rows)
            
            return {
                "min_speed_ratio": speed_range["min_speed_ratio"],
                "max_speed_ratio": speed_range["max_speed_ratio"],
                "speed_groups": speed_groups
            }

        except Exception as e:
            logger.error(f"Error retrieving VSD data: {str(e)}")
            return None

    def _discover_vsd_performance_table(self, site_id: str, pump_type: str) -> Optional[str]:
        """Discover VSD Performance Expected Trend table."""
        try:
            tables = self.clickhouse_service.get_tables_for_site(site_id)
            table_names = [table.get('tableName') for table in tables]

            pattern1 = f"{site_id}_Pumps_VSD_Performance_Expected_Trend_{pump_type}"
            pattern2 = f"{site_id}_Stream_All_Pumps_VSD_Performance_Expected_Trend_{pump_type}"
            
            if pattern1 in table_names:
                return pattern1
            if pattern2 in table_names:
                return pattern2
            
            # Try lowercase
            pump_type_lower = pump_type.lower()
            pattern1_lower = f"{site_id}_Pumps_VSD_Performance_Expected_Trend_{pump_type_lower}"
            pattern2_lower = f"{site_id}_Stream_All_Pumps_VSD_Performance_Expected_Trend_{pump_type_lower}"
            
            if pattern1_lower in table_names:
                return pattern1_lower
            if pattern2_lower in table_names:
                return pattern2_lower

            return None

        except Exception as e:
            logger.error(f"Error discovering VSD table: {str(e)}")
            return None

    def _calculate_speed_ratio_range(
        self, site_id: str, table_name: str, pump_id: str, 
        from_date: str, to_date: str
    ) -> Optional[Dict[str, float]]:
        """Calculate min/max speed ratios from operational data."""
        try:
            columns_request = [{
                "siteName": site_id,
                "tableName": table_name,
                "columnName": "Speed",
                "columnType": "double"
            }]

            filters = {"Pump_ID": pump_id}

            # Enable fallback for Dashboard APIs - use same dates as main data retrieval
            response = self.clickhouse_service.get_column_data_sources(
                columns_list=columns_request,
                from_date=from_date,
                to_date=to_date,
                rack=None,
                filters=filters,
                enable_fallback=True  # Dashboard API - enable fallback to last 7 days
            )

            # CRITICAL FIX: Handle nested response structure
            column_data = None
            
            if isinstance(response, dict):
                # Response is a dict with 'column_data' and 'metadata' keys
                column_data = response.get('column_data')
                logger.info(f"Extracted column_data from nested response structure")
            elif isinstance(response, list):
                # Direct list response (old format)
                column_data = response
                logger.info(f"Using direct list response")
            else:
                logger.error(f"Unexpected response type: {type(response).__name__}")
                return None
            
            if not column_data or not isinstance(column_data, list):
                logger.warning(f"No valid column data returned. Type: {type(column_data)}")
                return None

            speed_values = []
            for col in column_data:
                if not isinstance(col, dict):
                    logger.error(f"Expected dict for column data, got {type(col).__name__}")
                    continue
                    
                if col.get('columnName') == 'Speed':
                    data_source = col.get('dataSource', [])
                    if isinstance(data_source, list):
                        speed_values = [v for v in data_source if v is not None]
                        logger.info(f"Found {len(speed_values)} speed values")
                    else:
                        logger.error(f"Expected list for dataSource, got {type(data_source).__name__}")
                    break

            if speed_values:
                min_speed_ratio = round(min(speed_values) / 100, 2)
                max_speed_ratio = round(max(speed_values) / 100, 2)
                return {
                    "min_speed_ratio": min_speed_ratio,
                    "max_speed_ratio": max_speed_ratio
                }

            return None

        except Exception as e:
            logger.error(f"Error calculating speed ratio range: {str(e)}")
            return None

    def _get_vsd_performance_data(
        self, site_id: str, vsd_table_name: str, pump_id: str,
        min_speed_ratio: float, max_speed_ratio: float
    ) -> List[Dict]:
        """Query VSD Performance table."""
        try:
            tables_request = [{"siteName": site_id, "tableName": vsd_table_name}]
            columns_info = self.clickhouse_service.get_columns_for_tables(tables_request)

            # Validate columns_info
            if not isinstance(columns_info, list):
                logger.error(f"Expected list from get_columns_for_tables, got {type(columns_info).__name__}")
                return []

            columns_request = [
                {"siteName": site_id, "tableName": vsd_table_name,
                 "columnName": col_info["columnName"], "columnType": col_info["columnType"]}
                for col_info in columns_info
                if isinstance(col_info, dict) and "columnName" in col_info and "columnType" in col_info
            ]

            filters = {"Pump_ID": pump_id}

            response = self.clickhouse_service.get_column_data_sources(
                columns_list=columns_request,
                from_date=None,
                to_date=None,
                rack=None,
                filters=filters
            )

            # CRITICAL FIX: Handle nested response structure
            column_data = None
            
            if isinstance(response, dict):
                # Response is a dict with 'column_data' and 'metadata' keys
                column_data = response.get('column_data')
                logger.info(f"Extracted column_data from nested response structure")
            elif isinstance(response, list):
                # Direct list response (old format)
                column_data = response
                logger.info(f"Using direct list response")
            else:
                logger.error(f"Unexpected response type: {type(response).__name__}")
                return []
            
            if not column_data or not isinstance(column_data, list):
                logger.warning(f"No valid column data. Type: {type(column_data)}")
                return []
            
            # Validate first element has dataSource
            if not column_data:
                logger.warning("Empty column data list")
                return []
            
            first_col = column_data[0]
            if not isinstance(first_col, dict):
                logger.error(f"Expected dict for column data element, got {type(first_col).__name__}")
                return []
            
            if not first_col.get('dataSource'):
                logger.warning("No dataSource in first column")
                return []

            num_rows = len(first_col["dataSource"])
            logger.info(f"Processing {num_rows} rows from VSD data")
            
            rows = []
            for i in range(num_rows):
                row = {}
                for col in column_data:
                    if not isinstance(col, dict):
                        continue
                    
                    col_name = col.get("columnName")
                    if not col_name:
                        continue
                        
                    data_source = col.get("dataSource", [])
                    if isinstance(data_source, list) and i < len(data_source):
                        row[col_name] = data_source[i]
                    else:
                        row[col_name] = None
                rows.append(row)

            # Filter by speed ratio range
            filtered_rows = []
            for row in rows:
                speed_ratio = row.get("Speed_Ratio")
                if speed_ratio is not None:
                    try:
                        speed_ratio_rounded = round(float(speed_ratio), 1)
                        if min_speed_ratio <= speed_ratio_rounded <= max_speed_ratio:
                            row["Speed_Ratio_Rounded"] = speed_ratio_rounded
                            filtered_rows.append(row)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid speed_ratio value: {speed_ratio}, error: {e}")
                        continue

            logger.info(f"Found {len(filtered_rows)} VSD rows after filtering (from {num_rows} total)")
            return filtered_rows

        except Exception as e:
            logger.error(f"Error getting VSD data: {str(e)}")
            return []

    def _group_by_speed_ratio(self, vsd_rows: List[Dict]) -> Dict[str, Dict[str, List]]:
        """Group VSD data by speed ratio."""
        try:
            speed_groups = {}

            for row in vsd_rows:
                speed_ratio_rounded = row.get("Speed_Ratio_Rounded")
                if speed_ratio_rounded is None:
                    continue

                # Convert to percentage string (0.8 -> "80%")
                speed_key = f"{int(speed_ratio_rounded * 100)}%"

                if speed_key not in speed_groups:
                    speed_groups[speed_key] = {}

                excluded_columns = [
                    "Speed_Ratio", "Speed_Ratio_Rounded", "Speed_Percent",
                    "Pump", "Pump_ID", "Pump_Category"
                ]

                for col_name, col_value in row.items():
                    if col_name in excluded_columns:
                        continue

                    if col_name not in speed_groups[speed_key]:
                        speed_groups[speed_key][col_name] = []

                    speed_groups[speed_key][col_name].append(col_value)

            logger.info(f"Grouped into {len(speed_groups)} speed groups: {list(speed_groups.keys())}")
            return speed_groups

        except Exception as e:
            logger.error(f"Error grouping VSD data: {str(e)}")
            return {}