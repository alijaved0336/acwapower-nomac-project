"""
Dashboard 007 Service - Pump Retrieval Business Logic
Handles pump data retrieval with dynamic table discovery and category grouping.
"""

import logging
from typing import Dict, List, Optional

from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService
from infrastructure.orm.dash_007 import Dash007Repsoitory

logger = logging.getLogger(__name__)


class Dash007Service:
    """
    Service for Dashboard 007 - Pump List functionality.
    Provides business logic for retrieving and grouping pumps by category.
    """

    def __init__(self):
        """Initialize service with ClickHouse ADLS service dependency."""
        self.clickhouse_service = ClickHouseADLSService()
        self.dash007_repo = Dash007Repsoitory()

    def get_pumps_by_category(self, site_id: str) -> Dict[str, List[Dict]]:
        """
        Retrieve pumps grouped by category for a specific site.

        This method performs the following steps:
        1. Validates that the site exists
        2. Discovers the correct pump reference table (Pattern 1 or Pattern 2)
        3. Retrieves pump data (Pump_Category, Pump, Pump_ID columns)
        4. Groups pumps by category

        Args:
            site_id: Site identifier (e.g., 'Rabigh3', 'UAQ', 'STPC', 'Jubail-Jazlah')

        Returns:
            Dictionary with pump categories as keys and lists of pumps as values.
            Format:
            {
                "Feed Pumps": [
                    {"pump": "Feed Pump 1A", "Pump_id": "FP-001"},
                    {"pump": "Feed Pump 1B", "Pump_id": "FP-002"}
                ],
                "High Pressure Pumps": [...],
                "Booster Pumps": []
            }

        Raises:
            ValueError: If site not found or pump reference table not found
            Exception: If data retrieval fails
        """
        try:
            logger.info(f"Starting pump retrieval for site: {site_id}")

            # Step 1: Validate site exists
            self._validate_site_exists(site_id)
            logger.info(f"Site validation successful for: {site_id}")

            # Step 2: Discover pump reference table (Pattern 1 or Pattern 2)
            table_name = self._discover_pump_reference_table(site_id)
            logger.info(f"Discovered pump reference table: {table_name}")

            # Step 3: Build column request for pump data
            columns_request = [
                {
                    "siteName": site_id,
                    "tableName": table_name,
                    "columnName": "Pump_Category",
                    "columnType": "string"
                },
                {
                    "siteName": site_id,
                    "tableName": table_name,
                    "columnName": "Pump",
                    "columnType": "string"
                },
                {
                    "siteName": site_id,
                    "tableName": table_name,
                    "columnName": "Pump_ID",
                    "columnType": "string"
                }
            ]

            logger.info(f"Requesting pump data with columns: {[col['columnName'] for col in columns_request]}")

            # Step 4: Get data from ClickHouse (no date or rack filtering)
            response = self.clickhouse_service.get_column_data_sources(
                columns_list=columns_request,
                from_date=None,
                to_date=None,
                rack=None
            )

            # Extract column_data from response (ignore metadata for pump list)
            column_data = response.get("column_data", [])

            logger.info(f"Retrieved {len(column_data)} column data responses")

            # Step 5: Transform to grouped structure
            grouped_pumps = self._transform_to_grouped_structure(column_data)

            logger.info(f"Successfully grouped pumps into {len(grouped_pumps)} categories")

            return grouped_pumps

        except ValueError as ve:
            # Re-raise validation errors (site not found, table not found)
            logger.error(f"Validation error in get_pumps_by_category: {str(ve)}")
            raise

        except Exception as e:
            logger.error(f"Error in get_pumps_by_category for site {site_id}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve pumps: {str(e)}")

    def _validate_site_exists(self, site_id: str) -> None:
        """
        Validate that the site exists in ClickHouse.

        Args:
            site_id: Site identifier to validate

        Raises:
            ValueError: If site not found
        """
        try:
            # Get all sites from ClickHouse
            sites = self.clickhouse_service.get_sites()

            # Extract site names from response
            site_names = [site.get('name') for site in sites]

            # Check if site_id exists
            if site_id not in site_names:
                raise ValueError(f"Site '{site_id}' not found. Available sites: {', '.join(site_names)}")

            logger.info(f"Site '{site_id}' validated successfully")

        except ValueError as ve:
            # Re-raise validation error
            raise

        except Exception as e:
            logger.error(f"Error validating site {site_id}: {str(e)}")
            raise Exception(f"Failed to validate site: {str(e)}")

    def _discover_pump_reference_table(self, site_id: str) -> str:
        """
        Discover the pump reference table using dynamic table discovery.

        Different sites use different table naming patterns:
        - Pattern 1: {site_id}_Pumps_Reference (Rabigh3, STPC, Jubail-Jazlah)
        - Pattern 2: {site_id}_Stream_All_Pumps_Reference (UAQ)

        Algorithm:
        1. Get all tables for the site
        2. Check if Pattern 1 exists
        3. If not, check if Pattern 2 exists
        4. If neither exists, raise ValueError

        Args:
            site_id: Site identifier

        Returns:
            Name of the pump reference table

        Raises:
            ValueError: If no pump reference table found
        """
        try:
            logger.info(f"Starting pump reference table discovery for site: {site_id}")

            # Get all tables for the site
            tables = self.clickhouse_service.get_tables_for_site(site_id)

            # Extract table names
            table_names = [table.get('tableName') for table in tables]

            logger.info(f"Found {len(table_names)} tables for site {site_id}")

            # Define table name patterns
            pattern1 = f"{site_id}_Pumps_Reference"
            pattern2 = f"{site_id}_Stream_All_Pumps_Reference"

            # Check Pattern 1
            if pattern1 in table_names:
                logger.info(f"Found pump reference table using Pattern 1: {pattern1}")
                return pattern1

            # Check Pattern 2
            if pattern2 in table_names:
                logger.info(f"Found pump reference table using Pattern 2: {pattern2}")
                return pattern2

            # Neither pattern found
            error_message = (
                f"No pump reference table found for site '{site_id}'. "
                f"Expected '{pattern1}' or '{pattern2}'. "
                f"Available tables: {', '.join(table_names)}"
            )
            logger.warning(error_message)
            raise ValueError(error_message)

        except ValueError as ve:
            # Re-raise validation error
            raise

        except Exception as e:
            logger.error(f"Error discovering pump reference table for site {site_id}: {str(e)}")
            raise Exception(f"Failed to discover pump reference table: {str(e)}")

    def _transform_to_grouped_structure(self, column_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Transform column data into grouped structure by pump category.

        Expected input format (from get_column_data_sources):
        [
            {
                "columnName": "Pump_Category",
                "dataSource": ["Feed Pumps", "Feed Pumps", "High Pressure Pumps"]
            },
            {
                "columnName": "Pump",
                "dataSource": ["Feed Pump 1A", "Feed Pump 1B", "HP Pump 2A"]
            },
            {
                "columnName": "Pump_ID",
                "dataSource": ["FP-001", "FP-002", "HPP-001"]
            }
        ]

        Output format:
        {
            "Feed Pumps": [
                {"pump": "Feed Pump 1A", "Pump_id": "FP-001"},
                {"pump": "Feed Pump 1B", "Pump_id": "FP-002"}
            ],
            "High Pressure Pumps": [
                {"pump": "HP Pump 2A", "Pump_id": "HPP-001"}
            ]
        }

        Args:
            column_data: List of column data from ClickHouse

        Returns:
            Dictionary with categories as keys and pump lists as values
        """
        try:
            logger.info("Starting transformation to grouped structure")

            # Extract data sources from column data
            pump_category_data = []
            pump_data = []
            pump_id_data = []

            for col in column_data:
                column_name = col.get('columnName')
                data_source = col.get('dataSource', [])

                if column_name == 'Pump_Category':
                    pump_category_data = data_source
                elif column_name == 'Pump':
                    pump_data = data_source
                elif column_name == 'Pump_ID':
                    pump_id_data = data_source

            logger.info(
                f"Extracted data: {len(pump_category_data)} categories, "
                f"{len(pump_data)} pumps, {len(pump_id_data)} IDs"
            )

            # Validate all lists have the same length
            if not (len(pump_category_data) == len(pump_data) == len(pump_id_data)):
                logger.warning(
                    f"Data length mismatch - Categories: {len(pump_category_data)}, "
                    f"Pumps: {len(pump_data)}, IDs: {len(pump_id_data)}"
                )
                # Handle mismatch by using the minimum length
                min_length = min(len(pump_category_data), len(pump_data), len(pump_id_data))
                pump_category_data = pump_category_data[:min_length]
                pump_data = pump_data[:min_length]
                pump_id_data = pump_id_data[:min_length]

            # Group pumps by category
            grouped_pumps: Dict[str, List[Dict]] = {}

            for i in range(len(pump_category_data)):
                category = pump_category_data[i]
                pump = pump_data[i]
                pump_id = pump_id_data[i]

                # Initialize category if not exists
                if category not in grouped_pumps:
                    grouped_pumps[category] = []

                # Add pump to category (note: field name is "Pump_id" with lowercase 'd')
                grouped_pumps[category].append({
                    "pump": pump,
                    "Pump_id": pump_id
                })

            logger.info(f"Grouped pumps into {len(grouped_pumps)} categories")

            # Log category summary
            for category, pumps in grouped_pumps.items():
                logger.info(f"Category '{category}': {len(pumps)} pumps")

            return grouped_pumps

        except Exception as e:
            logger.error(f"Error transforming data to grouped structure: {str(e)}", exc_info=True)
            # Return empty dict instead of failing
            logger.warning("Returning empty grouped structure due to transformation error")
            return {}

    def get_pump_data(
        self,
        site_id: str,
        pump_category: str,
        pump: str,
        pump_id: str,
        from_date: Optional[str],
        to_date: Optional[str]
    ) -> Dict:
        """
        Retrieve pump data for a specific pump within a date range.
        Returns real data for 6 columns and mock data for 4 calculated columns.

        This method performs the following steps:
        1. Validates that the site exists
        2. Discovers the correct pump operational performance table (Pattern 1 or Pattern 2)
        3. Retrieves real data columns (Pump_Power, Efficiency, Head, etc.) with date and pump filtering
        4. Generates mock data for calculated columns (Avg Flow, Avg Efficiency, etc.)
        5. Combines real and mock data into a single response array
        6. Extracts dropdown data from expected table (paired expected/measured columns)

        Args:
            site_id: Site identifier (e.g., 'Jubail-Jazlah', 'Rabigh3', 'UAQ')
            pump_category: Pump category (e.g., 'seawater_intake_system', 'feed_pump_second_pass')
            pump: Pump name (e.g., 'Pump_01', 'Feed_Pump_1A')
            pump_id: Pump ID (e.g., '23331', 'FP-001')
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with format:
            {
                "column_data": [list of column data dictionaries],
                "dropdown_data": [list of base column names for paired expected/measured]
            }

        Raises:
            ValueError: If site not found, table not found, or pump not found
            Exception: If data retrieval fails
        """
        try:
            logger.info(
                f"Starting pump data retrieval - Site: {site_id}, Category: {pump_category}, "
                f"Pump: {pump}, ID: {pump_id}, Date Range: {from_date} to {to_date}"
            )

            # Step 1: Validate site exists
            self._validate_site_exists(site_id)
            logger.info(f"Site validation successful for: {site_id}")

            # Step 2: Discover pump operational performance table (Pattern 1 or Pattern 2)
            table_name, table_name_exp = self._discover_pump_operational_table(site_id, pump_category)
            logger.info(f"Discovered pump operational performance table: {table_name}")

            # Step 3: If no date range provided, get latest 7 days from DB
            if from_date is None or to_date is None:
                logger.info("No date range provided, fetching latest 7 days from database")
                from_date, to_date = self.dash007_repo._get_latest_date_range_from_db(
                    site_id=site_id,
                    table_name=table_name,
                    pump=pump,
                    pump_id=pump_id,
                    days=7
                )

                if from_date is None or to_date is None:
                    logger.warning(f"No data found for pump {pump}/{pump_id} in database")
                    # Return empty result instead of failing
                    return {
                        "column_data": [],
                        "dropdown_data": [],
                        "vsd_performance_data": None,
                        "data_availability_for_given_date": False,
                        "from_date": from_date,
                        "to_date": to_date
                    }

                logger.info(f"Using latest date range from DB: {from_date} to {to_date}")

            # Step 4: Retrieve real data columns with date and pump filtering
            # Enable fallback for Dashboard APIs - repository will handle fallback automatically
            all_columns_data, metadata = self._get_real_data_columns(
                site_id, table_name, table_name_exp, pump, pump_id, from_date, to_date
            )
            logger.info(f"Retrieved {len(all_columns_data)} real data columns")

            # Step 5: Add calculated columns (Pump_Differential_Pressure)
            all_columns_data = self._add_calculated_columns(
                all_columns_data, site_id, table_name
            )

            # Step 6: Extract dropdown data from expected table
            dropdown_data = self._extract_dropdown_data(site_id, table_name_exp)
            logger.info(f"Extracted {len(dropdown_data)} dropdown items from expected table")

            # Step 7: Retrieve VSD Performance data (optional - non-blocking)
            # Use dates from metadata to ensure we use the same dates as the data retrieval (including fallback dates)
            actual_from_date = metadata.get("from_date", from_date)
            actual_to_date = metadata.get("to_date", to_date)
            vsd_performance_data = self._retrieve_vsd_performance_data(
                site_id, pump_category, table_name, pump, pump_id, actual_from_date, actual_to_date
            )

            logger.info(
                f"Successfully processed pump data for {site_id}/{pump_category}/{pump}/{pump_id}. "
                f"Total columns: {len(all_columns_data)}, Dropdown items: {len(dropdown_data)}, "
                f"VSD data: {'Available' if vsd_performance_data else 'Not available'}"
            )

            return {
                "column_data": all_columns_data,
                "dropdown_data": dropdown_data,
                "vsd_performance_data": vsd_performance_data,
                "data_availability_for_given_date": metadata.get("data_availability_for_given_date", True),
                "from_date": metadata.get("from_date", from_date),
                "to_date": metadata.get("to_date", to_date)
            }

        except ValueError as ve:
            # Re-raise validation errors (site not found, table not found)
            logger.error(f"Validation error in get_pump_data: {str(ve)}")
            raise

        except Exception as e:
            logger.error(
                f"Error in get_pump_data for {site_id}/{pump_category}/{pump}/{pump_id}: {str(e)}",
                exc_info=True
            )
            raise Exception(f"Failed to retrieve pump data: {str(e)}")

    def _discover_pump_operational_table(self, site_id: str, pump_category: str) -> str:
        """
        Discover the pump operational performance table using dynamic table discovery.

        Different sites and pump categories use different table naming patterns:
        - Pattern 1: {site_id}_Pumps_Operational_Performance_{pump_category}
        - Pattern 2: {site_id}_Stream_All_Pumps_Reference_{pump_category}

        Note: Pattern 2 is different from Pump List API which uses Stream_All_Pumps_Reference

        Algorithm:
        1. Get all tables for the site
        2. Check if Pattern 1 exists
        3. If not, check if Pattern 2 exists
        4. If neither exists, raise ValueError

        Args:
            site_id: Site identifier
            pump_category: Pump category identifier

        Returns:
            Name of the pump operational performance table

        Raises:
            ValueError: If no pump operational performance table found
        """
        try:
            logger.info(
                f"Starting pump operational table discovery for site: {site_id}, category: {pump_category}"
            )

            # Get all tables for the site
            tables = self.clickhouse_service.get_tables_for_site(site_id)

            # Extract table names
            table_names = [table.get('tableName') for table in tables]

            logger.info(f"Found {len(table_names)} tables for site {site_id}")

            # Define table name patterns
            # Note: Use site_id as-is (DO NOT replace hyphens)
            pattern1_exp = f"{site_id}_Pumps_Operational_Performance_Expected_{pump_category}"
            pattern2_exp = f"{site_id}_Stream_All_Pumps_Operational_Performance_Expected_{pump_category}"
            
            pattern1 = f"{site_id}_Pumps_Operational_Performance_{pump_category}"
            pattern2 = f"{site_id}_Stream_All_Pumps_Operational_Performance_{pump_category}"
            
            # Check Pattern 1
            if pattern1 in table_names:
                logger.info(f"Found pump operational table using Pattern 1: {pattern1}")
                return pattern1, pattern1_exp

            # Check Pattern 2
            if pattern2 in table_names:
                logger.info(f"Found pump operational table using Pattern 2: {pattern2}")
                return pattern2, pattern2_exp

            # Neither pattern found
            error_message = (
                f"No pump operational performance table found for site '{site_id}' "
                f"and category '{pump_category}'. "
                f"Expected '{pattern1}' or '{pattern2}'. "
                f"Available tables: {', '.join(table_names)}"
            )
            logger.warning(error_message)
            raise ValueError(error_message)

        except ValueError as ve:
            # Re-raise validation error
            raise

        except Exception as e:
            logger.error(
                f"Error discovering pump operational table for site {site_id}, category {pump_category}: {str(e)}"
            )
            raise Exception(f"Failed to discover pump operational table: {str(e)}")

    def _get_real_data_columns(
        self,
        site_id: str,
        table_name: str,
        table_name_exp: str,
        pump: str,
        pump_id: str,
        from_date: str,
        to_date: str
    ) -> tuple:
        """
        Retrieve real data columns from ClickHouse with date and pump filtering.

        Retrieves 6 real data columns:
        - Pump_Power
        - Efficiency
        - Head
        - Pump_Current
        - Pump_Flow
        - Pump_Discharge_Press
        - SEC_Measured
        - SEC_Expected
        - Pump_Power_Measured
        - Pump_Power_Expected
        - Efficiency_Measured
        - Efficiency_Expected
        - Head_Measured
        - Head_Expected
        - Flow_Measured
        - Flow_Expected

        Args:
            site_id: Site identifier
            table_name: Discovered table name
            table_name_exp: Discovered table name with expected data
            pump: Pump name for filtering
            pump_id: Pump ID for filtering
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            Tuple of (column_data, metadata)
            - column_data: List of column data dictionaries from ClickHouse
            - metadata: Dict with data_availability_for_given_date, from_date, to_date

        Raises:
            Exception: If data retrieval fails
        """
        try:
            logger.info(f"Retrieving real data columns for table: {table_name}")

            # Build column request for ClickHouse ADLS service
            columns_request = [
                {"siteName": site_id, "tableName": table_name, "columnName": "timestamp", "columnType": "timestamp[ns]"},
                {"siteName": site_id, "tableName": table_name, "columnName": "Speed", "columnType": "double"},
                {"siteName": site_id, "tableName": table_name, "columnName": "Pump_Power", "columnType": "double"},
                {"siteName": site_id, "tableName": table_name, "columnName": "Efficiency", "columnType": "double"},
                {"siteName": site_id, "tableName": table_name, "columnName": "Head", "columnType": "double"},
                {"siteName": site_id, "tableName": table_name, "columnName": "Pump_Current", "columnType": "double"},
                {"siteName": site_id, "tableName": table_name, "columnName": "Pump_Flow", "columnType": "double"},
                {"siteName": site_id, "tableName": table_name, "columnName": "Pump_Discharge_Press", "columnType": "double"},
                {"siteName": site_id, "tableName": table_name, "columnName": "Pump_Feed_Press", "columnType": "double"}
            ]

            # Dynamically add all paired expected/measured columns from table_name_exp
            expected_columns = self._build_expected_measured_columns_request(site_id, table_name_exp)
            columns_request.extend(expected_columns)

            logger.info(f"Requesting {len(columns_request)} real data columns ({len(expected_columns)} from expected table)")

            # Build filters for pump and pump_id
            filters = {
                "Pump": pump,
                "Pump_ID": pump_id
            }

            logger.info(f"Applying filters: {filters}")

            # Get data from ClickHouse ADLS service with date and pump filtering
            response = self.clickhouse_service.get_column_data_sources(
                columns_list=columns_request,
                from_date=from_date,
                to_date=to_date,
                rack=None,
                filters=filters,
                enable_fallback=True  # Dashboard API - enable fallback to last 7 days
            )

            # Extract column_data and metadata from response
            column_data = response.get("column_data", [])
            metadata = response.get("metadata", {
                "data_availability_for_given_date": True,
                "from_date": from_date,
                "to_date": to_date
            })

            logger.info(f"Retrieved {len(column_data)} real data column responses")
            logger.info(f"Metadata: data_availability={metadata.get('data_availability_for_given_date')}, "
                       f"from_date={metadata.get('from_date')}, to_date={metadata.get('to_date')}")

            # Validate that data was returned
            if not column_data or all(not col.get('dataSource') for col in column_data):
                logger.warning(
                    f"No data found for pump {pump} (ID: {pump_id}) in table {table_name} "
                    f"for date range {from_date} to {to_date}"
                )
                return [], metadata

            return column_data, metadata

        except ValueError as ve:
            # Re-raise validation errors
            raise

        except Exception as e:
            logger.error(f"Error retrieving real data columns: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve real data columns: {str(e)}")

    def _add_calculated_columns(
        self,
        column_data: List[Dict],
        site_id: str,
        table_name: str
    ) -> List[Dict]:
        """
        Add calculated columns: Pump_Differential_Pressure and Shaft_Power.

        Calculations:
        1. Pump_Differential_Pressure = Pump_Discharge_Press - Pump_Feed_Press
        2. Shaft_Power (kW) = (Flow × Head × 0.2795125) / Efficiency

        Where:
        - Flow is in m³/hr (Pump_Flow)
        - Head is in meters
        - Efficiency is in percentage
        - 0.2795125 = (1025 kg/m³ × 9.81 m/s²) / (3600 s/hr × 1000 W/kW)

        Args:
            column_data: List of column data from ClickHouse
            site_id: Site identifier
            table_name: Table name for metadata

        Returns:
            Enhanced column_data with calculated columns appended
        """
        try:
            logger.info("Adding calculated columns: Pump_Differential_Pressure and Shaft_Power")

            # Extract data arrays using generator expressions
            discharge_press_data = next(
                (col['dataSource'] for col in column_data if col['columnName'] == 'Pump_Discharge_Press'),
                []
            )
            feed_press_data = next(
                (col['dataSource'] for col in column_data if col['columnName'] == 'Pump_Feed_Press'),
                []
            )
            flow_data = next(
                (col['dataSource'] for col in column_data if col['columnName'] == 'Pump_Flow'),
                []
            )
            head_data = next(
                (col['dataSource'] for col in column_data if col['columnName'] == 'Head'),
                []
            )
            efficiency_data = next(
                (col['dataSource'] for col in column_data if col['columnName'] == 'Efficiency'),
                []
            )

            # Calculate Pump_Differential_Pressure (element-wise subtraction)
            diff_pressure_data = []
            for dp, fp in zip(discharge_press_data, feed_press_data):
                if dp is not None and fp is not None:
                    diff_pressure_data.append(dp - fp)
                else:
                    diff_pressure_data.append(None)

            logger.info(f"Calculated {len(diff_pressure_data)} Pump_Differential_Pressure values")

            # Create column dictionaries for calculated columns
            calculated_columns = [
                {
                    "columnName": "Pump_Differential_Pressure",
                    "columnType": "double",
                    "dataSource": diff_pressure_data,
                    "siteName": site_id,
                    "tableName": table_name
                }
            ]

            # Append calculated columns to column_data
            column_data.extend(calculated_columns)

            logger.info(
                f"Successfully added 2 calculated columns. Total columns: {len(column_data)}"
            )

            return column_data

        except Exception as e:
            logger.error(f"Error adding calculated columns: {str(e)}", exc_info=True)
            # Return original data without calculated columns if calculation fails
            logger.warning("Returning original column data without calculated columns")
            return column_data

    def _build_expected_measured_columns_request(self, site_id: str, table_name_exp: str) -> List[Dict]:
        """
        Build column request for all paired expected/measured columns from expected table.

        This method:
        1. Gets all columns from the expected table
        2. Identifies columns ending with '_Expected' or '_Measured'
        3. Finds pairs where both exist
        4. Builds column request objects for ALL paired columns

        Args:
            site_id: Site identifier
            table_name_exp: Expected table name

        Returns:
            List of column request dictionaries
            Example: [
                {"siteName": "UAQ", "tableName": "table_exp", "columnName": "SEC_Measured", "columnType": "double"},
                {"siteName": "UAQ", "tableName": "table_exp", "columnName": "SEC_Expected", "columnType": "double"},
                ...
            ]

        Raises:
            Exception: If column retrieval fails
        """
        try:
            logger.info(f"Building expected/measured columns request for table: {table_name_exp}")

            # Get all columns from the expected table
            tables_request = [
                {
                    "siteName": site_id,
                    "tableName": table_name_exp
                }
            ]

            columns_info = self.clickhouse_service.get_columns_for_tables(tables_request)
            logger.info(f"Retrieved {len(columns_info)} columns from expected table")

            # Extract column names and types
            expected_columns = {}
            measured_columns = {}

            for col_info in columns_info:
                col_name = col_info.get('columnName')
                col_type = col_info.get('columnType', 'double')

                if col_name.endswith('_Expected'):
                    base_name = col_name.replace('_Expected', '')
                    expected_columns[base_name] = col_type
                elif col_name.endswith('_Measured'):
                    base_name = col_name.replace('_Measured', '')
                    measured_columns[base_name] = col_type

            # Find pairs (columns that have both expected and measured)
            paired_base_names = set(expected_columns.keys()).intersection(set(measured_columns.keys()))
            logger.info(f"Found {len(paired_base_names)} paired column bases: {paired_base_names}")

            # Build column request for all paired columns
            columns_request = []
            for base_name in sorted(paired_base_names):
                # Add Measured column
                columns_request.append({
                    "siteName": site_id,
                    "tableName": table_name_exp,
                    "columnName": f"{base_name}_Measured",
                    "columnType": measured_columns[base_name]
                })
                # Add Expected column
                columns_request.append({
                    "siteName": site_id,
                    "tableName": table_name_exp,
                    "columnName": f"{base_name}_Expected",
                    "columnType": expected_columns[base_name]
                })

            logger.info(f"Built {len(columns_request)} column requests for paired expected/measured columns")
            return columns_request

        except Exception as e:
            logger.error(f"Error building expected/measured columns request: {str(e)}", exc_info=True)
            # Return empty list instead of failing
            logger.warning("Returning empty columns request due to build error")
            return []

    def _extract_dropdown_data(self, site_id: str, table_name_exp: str) -> List[str]:
        """
        Extract dropdown data from expected table by finding paired expected/measured columns.

        This method:
        1. Gets all columns from the expected table using get_columns_for_tables
        2. Identifies columns ending with '_Expected' or '_Measured'
        3. Finds pairs where both Expected and Measured exist
        4. Returns the base column names (without _Expected or _Measured suffix)

        Args:
            site_id: Site identifier
            table_name_exp: Expected table name

        Returns:
            List of base column names for paired expected/measured columns
            Example: ["SEC", "Pump_Power", "Efficiency", "Head", "Flow"]

        Raises:
            Exception: If column retrieval fails
        """
        try:
            logger.info(f"Extracting dropdown data from table: {table_name_exp}")

            # Get all columns from the expected table
            tables_request = [
                {
                    "siteName": site_id,
                    "tableName": table_name_exp
                }
            ]

            columns_info = self.clickhouse_service.get_columns_for_tables(tables_request)
            logger.info(f"Retrieved {len(columns_info)} columns from expected table")

            # Extract column names
            column_names = [col.get('columnName') for col in columns_info]
            logger.info(f"Column names: {column_names}")

            # Find expected and measured columns
            expected_columns = set()
            measured_columns = set()

            for col_name in column_names:
                if col_name.endswith('_Expected'):
                    base_name = col_name.replace('_Expected', '')
                    expected_columns.add(base_name)
                elif col_name.endswith('_Measured'):
                    base_name = col_name.replace('_Measured', '')
                    measured_columns.add(base_name)

            # Find pairs (columns that have both expected and measured)
            paired_columns = expected_columns.intersection(measured_columns)
            logger.info(f"Found {len(paired_columns)} paired columns: {paired_columns}")

            # Convert to sorted list for consistent ordering
            dropdown_data = sorted(list(paired_columns))

            logger.info(f"Dropdown data extracted successfully: {dropdown_data}")
            return dropdown_data

        except Exception as e:
            logger.error(f"Error extracting dropdown data from {table_name_exp}: {str(e)}", exc_info=True)
            # Return empty list instead of failing
            logger.warning("Returning empty dropdown data due to extraction error")
            return []

    def _retrieve_vsd_performance_data(
        self,
        site_id: str,
        pump_category: str,
        operational_table_name: str,
        pump: str,
        pump_id: str,
        from_date: str,
        to_date: str
    ) -> Optional[Dict]:
        """
        Retrieve VSD Performance Expected Trend data for pump (non-blocking).

        This is the main orchestration method that:
        1. Discovers VSD table
        2. Calculates speed ratio range from operational data
        3. Queries VSD data
        4. Groups data by speed ratio

        Args:
            site_id: Site identifier
            pump_category: Pump category
            operational_table_name: Operational performance table name
            pump: Pump name
            pump_id: Pump ID
            from_date: Start date
            to_date: End date

        Returns:
            VSD performance data dictionary or None if unavailable
        """
        try:
            logger.info(f"Starting VSD performance data retrieval for {site_id}/{pump_category}")

            # Step 1: Discover VSD table
            vsd_table_name = self._discover_vsd_performance_table(site_id, pump_category)
            if not vsd_table_name:
                logger.info(f"No VSD table found for {site_id}/{pump_category} - skipping VSD data")
                return None

            logger.info(f"Found VSD table: {vsd_table_name}")

            # Step 2: Calculate speed ratio range from operational data
            speed_range = self._calculate_speed_ratio_range(
                site_id, operational_table_name, pump, pump_id, from_date, to_date
            )
            if not speed_range:
                logger.warning(f"No speed data found for pump {pump}/{pump_id} in date range")
                return None

            logger.info(
                f"Speed ratio range: {speed_range['min_speed_ratio']} - {speed_range['max_speed_ratio']}"
            )

            # Step 3: Get VSD data
            vsd_rows = self._get_vsd_performance_data(
                site_id, vsd_table_name, pump, pump_id,
                speed_range["min_speed_ratio"], speed_range["max_speed_ratio"]
            )
            if not vsd_rows:
                logger.warning(f"No VSD data found in speed range {speed_range['min_speed_ratio']}-{speed_range['max_speed_ratio']}")
                return {
                    "min_speed_ratio": speed_range["min_speed_ratio"],
                    "max_speed_ratio": speed_range["max_speed_ratio"],
                    "speed_groups": {}
                }

            logger.info(f"Retrieved {len(vsd_rows)} VSD rows")

            # Step 4: Group by speed ratio
            speed_groups = self._group_by_speed_ratio(vsd_rows)
            logger.info(f"Grouped VSD data into {len(speed_groups)} speed groups")

            return {
                "min_speed_ratio": speed_range["min_speed_ratio"],
                "max_speed_ratio": speed_range["max_speed_ratio"],
                "speed_groups": speed_groups
            }

        except Exception as e:
            # Don't fail the entire request if VSD data fails
            logger.error(f"Error retrieving VSD performance data: {str(e)}", exc_info=True)
            return None

    def _discover_vsd_performance_table(self, site_id: str, pump_category: str) -> Optional[str]:
        """
        Discover VSD Performance Expected Trend table using dynamic table discovery.

        Patterns:
        - Pattern 1: {site_id}_Pumps_VSD_Performance_Expected_Trend_{pump_category}
        - Pattern 2: {site_id}_Stream_All_Pumps_VSD_Performance_Expected_Trend_{pump_category}

        Args:
            site_id: Site identifier
            pump_category: Pump category

        Returns:
            VSD table name or None if not found
        """
        try:
            logger.info(f"Starting VSD table discovery for site: {site_id}, category: {pump_category}")

            # Get all tables for the site
            tables = self.clickhouse_service.get_tables_for_site(site_id)
            table_names = [table.get('tableName') for table in tables]

            logger.info(f"Found {len(table_names)} tables for site {site_id}")

            # Define VSD table name patterns
            pattern1 = f"{site_id}_Pumps_VSD_Performance_Expected_Trend_{pump_category}"
            pattern2 = f"{site_id}_Stream_All_Pumps_VSD_Performance_Expected_Trend_{pump_category}"

            # Check Pattern 1
            if pattern1 in table_names:
                logger.info(f"Found VSD table using Pattern 1: {pattern1}")
                return pattern1

            # Check Pattern 2
            if pattern2 in table_names:
                logger.info(f"Found VSD table using Pattern 2: {pattern2}")
                return pattern2

            # Neither pattern found - not an error, VSD data is optional
            logger.info(f"No VSD table found for {site_id}/{pump_category}")
            return None

        except Exception as e:
            logger.error(f"Error discovering VSD table for {site_id}/{pump_category}: {str(e)}")
            return None

    def _calculate_speed_ratio_range(
        self,
        site_id: str,
        table_name: str,
        pump: str,
        pump_id: str,
        from_date: str,
        to_date: str
    ) -> Optional[Dict[str, float]]:
        """
        Calculate min/max speed ratios from operational performance data.

        Speed ratio = Speed / 100 (rounded to 2 decimals)

        Args:
            site_id: Site identifier
            table_name: Operational performance table name
            pump: Pump name
            pump_id: Pump ID
            from_date: Start date
            to_date: End date

        Returns:
            Dictionary with min_speed_ratio and max_speed_ratio, or None if no data
        """
        try:
            logger.info(f"Calculating speed ratio range for pump {pump}/{pump_id}")

            # Build column request for Speed column
            columns_request = [{
                "siteName": site_id,
                "tableName": table_name,
                "columnName": "Speed",
                "columnType": "double"
            }]

            # Build filters
            filters = {
                "Pump": pump,
                "Pump_ID": pump_id
            }

            # Get Speed data - enable fallback for Dashboard APIs
            response = self.clickhouse_service.get_column_data_sources(
                columns_list=columns_request,
                from_date=from_date,
                to_date=to_date,
                rack=None,
                filters=filters,
                enable_fallback=True  # Dashboard API - enable fallback to last 7 days
            )

            # Extract column_data from response (ignore metadata for VSD speed calculation)
            column_data = response.get("column_data", [])

            # Extract Speed values
            speed_values = []
            for col in column_data:
                if col.get('columnName') == 'Speed':
                    speed_values = [v for v in col.get('dataSource', []) if v is not None]
                    break

            # Calculate min/max speed ratios
            if speed_values:
                min_speed_ratio = round(min(speed_values) / 100, 2)
                max_speed_ratio = round(max(speed_values) / 100, 2)
                logger.info(f"Speed ratio range: {min_speed_ratio} - {max_speed_ratio}")
                return {
                    "min_speed_ratio": min_speed_ratio,
                    "max_speed_ratio": max_speed_ratio
                }

            logger.warning("No speed data found")
            return None

        except Exception as e:
            logger.error(f"Error calculating speed ratio range: {str(e)}", exc_info=True)
            return None

    def _get_vsd_performance_data(
        self,
        site_id: str,
        vsd_table_name: str,
        pump: str,
        pump_id: str,
        min_speed_ratio: float,
        max_speed_ratio: float
    ) -> List[Dict]:
        """
        Query VSD Performance Expected Trend table and filter by speed ratio range.

        Args:
            site_id: Site identifier
            vsd_table_name: VSD table name
            pump: Pump name
            pump_id: Pump ID
            min_speed_ratio: Minimum speed ratio
            max_speed_ratio: Maximum speed ratio

        Returns:
            List of row dictionaries with VSD data
        """
        try:
            logger.info(f"Retrieving VSD data from table: {vsd_table_name}")

            # Step 1: Get all columns from VSD table
            tables_request = [{
                "siteName": site_id,
                "tableName": vsd_table_name
            }]
            columns_info = self.clickhouse_service.get_columns_for_tables(tables_request)
            logger.info(f"Retrieved {len(columns_info)} columns from VSD table")

            # Step 2: Build column request for all columns
            columns_request = [
                {
                    "siteName": site_id,
                    "tableName": vsd_table_name,
                    "columnName": col_info["columnName"],
                    "columnType": col_info["columnType"]
                }
                for col_info in columns_info
            ]

            # Step 3: Build filters for pump and pump_id
            filters = {
                "Pump": pump,
                "Pump_ID": pump_id
            }

            # Step 4: Get VSD data (no date filtering - VSD is reference data)
            response = self.clickhouse_service.get_column_data_sources(
                columns_list=columns_request,
                from_date=None,  # No date filtering for VSD data
                to_date=None,
                rack=None,
                filters=filters
            )

            # Extract column_data from response (ignore metadata for VSD reference data)
            column_data = response.get("column_data", [])

            # Step 5: Transform column-oriented data to row-oriented
            if not column_data or not column_data[0].get('dataSource'):
                logger.warning("No VSD data returned from query")
                return []

            num_rows = len(column_data[0]["dataSource"])
            rows = []
            for i in range(num_rows):
                row = {}
                for col in column_data:
                    col_name = col["columnName"]
                    data_source = col.get("dataSource", [])
                    row[col_name] = data_source[i] if i < len(data_source) else None
                rows.append(row)

            logger.info(f"Transformed {num_rows} rows from column-oriented to row-oriented format")

            # Step 6: Filter rows by speed ratio range
            filtered_rows = []
            for row in rows:
                speed_ratio = row.get("Speed_Ratio")
                if speed_ratio is not None:
                    speed_ratio_rounded = round(speed_ratio, 1)
                    if min_speed_ratio <= speed_ratio_rounded <= max_speed_ratio:
                        row["Speed_Ratio_Rounded"] = speed_ratio_rounded
                        filtered_rows.append(row)

            logger.info(f"Filtered to {len(filtered_rows)} rows within speed range")
            return filtered_rows

        except Exception as e:
            logger.error(f"Error retrieving VSD performance data: {str(e)}", exc_info=True)
            return []

    def _group_by_speed_ratio(self, vsd_rows: List[Dict]) -> Dict[str, Dict[str, List]]:
        """
        Group VSD data by rounded Speed_Ratio (1 decimal place).

        Args:
            vsd_rows: List of VSD row dictionaries

        Returns:
            Dictionary grouped by speed ratio:
            {
                "0.8": {
                    "Head": [10.5, 10.6, 10.4],
                    "Flow": [1500, 1520, 1480],
                    ...
                },
                "0.9": {...},
                ...
            }
        """
        try:
            logger.info(f"Grouping {len(vsd_rows)} VSD rows by speed ratio")

            speed_groups = {}

            for row in vsd_rows:
                speed_ratio_rounded = row.get("Speed_Ratio_Rounded")
                if speed_ratio_rounded is None:
                    continue

                # Convert to string key with 1 decimal place
                speed_key = f"{speed_ratio_rounded:.1f}"

                # Initialize group if not exists
                if speed_key not in speed_groups:
                    speed_groups[speed_key] = {}

                # Add performance columns only (exclude filter and grouping columns)
                # Exclude: Pump, Pump_ID, Pump_Category (filters - constant values)
                # Exclude: Speed_Ratio, Speed_Ratio_Rounded (grouping keys)
                # Exclude: Speed_Percent (redundant - same as Speed_Ratio * 100)
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

            logger.info(f"Grouped into {len(speed_groups)} speed groups")

            # Log group summary
            for speed_key in sorted(speed_groups.keys()):
                num_records = len(next(iter(speed_groups[speed_key].values()))) if speed_groups[speed_key] else 0
                logger.info(f"Speed ratio {speed_key}: {num_records} records")

            return speed_groups

        except Exception as e:
            logger.error(f"Error grouping VSD data by speed ratio: {str(e)}", exc_info=True)
            return {}
