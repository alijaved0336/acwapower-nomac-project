import re
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime, date
from infrastructure.applevel.responseBuilder import ResponseBuilder
from infrastructure.orm.repositories.chemicalRepository import ChemicalRepository
from infrastructure.orm.repositories.sparkRepository import SparkRepository
from infrastructure.services.dash_001 import Dash_001Service
from config.clickhouse_connector import execute_clickhouse_query

# Set up logging for debugging
logger = logging.getLogger(__name__)

class Dash_071Service:

    def __init__(self):
        self.chemical_repository = ChemicalRepository()

    def __del__(self):
        """Cleanup repository connection when service is destroyed"""
        if hasattr(self, 'chemical_repository'):
            self.chemical_repository.close()

    # Context manager support for the service
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.chemical_repository.close()

    def filter_latest_records_by_date(self, column_responses):
        """
        Filter column responses to keep only the latest record for each unique date.
        Each column has a dataSource array, and they're aligned by index.
        
        Args:
            column_responses: List of column response objects with dataSource containing arrays
            
        Returns:
            Filtered column responses with latest record per date
        """
        if not column_responses:
            return column_responses
            
        # Find the DateTime column to use for filtering
        datetime_column = None
        datetime_data = None
        
        for response in column_responses:
            if hasattr(response, 'columnName'):
                column_name = getattr(response, 'columnName', '').lower()
            elif isinstance(response, dict):
                column_name = response.get('columnName', '').lower()
            else:
                continue
                
            # Check if this is a datetime column
            if column_name in ['datetime', 'timestamp'] or 'datetime' in column_name:
                if hasattr(response, 'dataSource'):
                    datetime_data = getattr(response, 'dataSource', [])
                elif isinstance(response, dict):
                    datetime_data = response.get('dataSource', [])
                    
                if datetime_data:
                    datetime_column = response
                    break
        
        if not datetime_column or not datetime_data:
            # No datetime column found, return original data
            return column_responses
            
        # Group indices by date and find latest timestamp for each date
        date_groups = {}
        
        for index, timestamp_str in enumerate(datetime_data):
            if not timestamp_str:
                continue
                
            try:
                # Parse the timestamp string
                if isinstance(timestamp_str, str):
                    # Handle ISO format with Z suffix
                    timestamp_str = timestamp_str.replace('Z', '+00:00')
                    datetime_value = datetime.fromisoformat(timestamp_str)
                else:
                    continue
                    
                # Extract date part for grouping
                date_key = datetime_value.date()
                
                # Keep the index with the latest time for this date
                if date_key not in date_groups or datetime_value > date_groups[date_key]['datetime']:
                    date_groups[date_key] = {
                        'datetime': datetime_value,
                        'index': index
                    }
                    
            except Exception as e:
                logger.warning(f"Could not parse timestamp '{timestamp_str}': {e}")
                continue
        
        # Get the indices to keep (latest timestamp for each unique date)
        indices_to_keep = [group_info['index'] for group_info in date_groups.values()]
        
        # Sort indices to maintain chronological order
        indices_to_keep.sort(key=lambda idx: date_groups[datetime.fromisoformat(datetime_data[idx].replace('Z', '+00:00')).date()]['datetime'])
        
        # Filter all columns using the selected indices
        filtered_responses = []
        
        for response in column_responses:
            # Get dataSource - handle both object attributes and dict keys
            if hasattr(response, 'dataSource'):
                data_source = getattr(response, 'dataSource', [])
            elif isinstance(response, dict):
                data_source = response.get('dataSource', [])
            else:
                filtered_responses.append(response)
                continue
                
            if not data_source:
                filtered_responses.append(response)
                continue
            
            # Filter the dataSource to keep only selected indices
            filtered_data_source = [data_source[i] for i in indices_to_keep if i < len(data_source)]
            
            # Create filtered response
            if hasattr(response, 'dataSource'):
                # Handle ColumnResponse object - create new instance with required parameters
                try:
                    # Get the required attributes for ColumnResponse constructor
                    column_name = getattr(response, 'columnName', '')
                    column_type = getattr(response, 'columnType', '')
                    table_name = getattr(response, 'tableName', '')
                    site_name = getattr(response, 'siteName', '')

                    # Create new ColumnResponse with filtered data using keyword arguments
                    filtered_response = type(response)(
                        columnName=column_name,
                        columnType=column_type,
                        tableName=table_name,
                        siteName=site_name,
                        dataSource=filtered_data_source
                    )
                    filtered_responses.append(filtered_response)
                except Exception as e:
                    # Fallback: modify the existing object in place
                    logger.warning(f"Warning: Could not create new response object, modifying in place: {e}")
                    setattr(response, 'dataSource', filtered_data_source)
                    filtered_responses.append(response)
            else:
                # Handle dict format
                filtered_response = response.copy()
                filtered_response['dataSource'] = filtered_data_source
                filtered_responses.append(filtered_response)
                
        return filtered_responses
    
    def extract_metadata_from_response(self, column_responses):
        """
        Extract fallback metadata from column responses returned by ClickHouseADLSService.
        
        Args:
            column_responses: Response from get_column_data_sources (dict with 'column_data' and 'metadata')
            
        Returns:
            Dictionary with data_availability_for_given_date, from_date, to_date
        """
        try:
            # Check if response is a dict with metadata
            if isinstance(column_responses, dict):
                if 'metadata' in column_responses:
                    metadata = column_responses['metadata']
                    return {
                        "data_availability_for_given_date": metadata.get("data_availability_for_given_date", True),
                        "from_date": metadata.get("from_date"),
                        "to_date": metadata.get("to_date")
                    }
                
                # If it's a dict but no metadata key, check if column_data exists
                if 'column_data' in column_responses:
                    # This is the new format, but metadata might be missing
                    logger.warning("Response has column_data but no metadata key")
                    return {
                        "data_availability_for_given_date": True,
                        "from_date": None,
                        "to_date": None
                    }
            
            # Fallback for old format (list of column responses)
            logger.warning("Response is not in expected dict format, assuming old format")
            return {
                "data_availability_for_given_date": True,
                "from_date": None,
                "to_date": None
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata from response: {e}")
            return {
                "data_availability_for_given_date": True,
                "from_date": None,
                "to_date": None
            }
    
    def extract_column_data_from_response(self, response):
        """
        Extract column data list from service response.
        Handles both new dict format and legacy list format.
        
        Args:
            response: Response from get_column_data_sources
            
        Returns:
            List of column response objects
        """
        try:
            if isinstance(response, dict) and 'column_data' in response:
                return response['column_data']
            elif isinstance(response, list):
                # Legacy format - list of column responses
                return response
            else:
                logger.warning(f"Unexpected response format: {type(response)}")
                return []
        except Exception as e:
            logger.error(f"Error extracting column data from response: {e}")
            return []

    def get_sites_by_cluster(self, cluster: str):
        """Get site names filtered by cluster"""
        plant_mappings = {
            "hive_metastore.nomac_mpc_swro_gold_j3a.plant_landing": "Jubail Energy Plant",
            "hive_metastore.nomac_mpc_swro_gold_j3a.plant_rabigh_landing": "Rabigh Energy Plant",
            "hive_metastore.nomac_mpc_swro_gold_j3a.plant_stpc_landing": "STPC Energy Plant",
            "hive_metastore.nomac_mpc_swro_gold_j3a.plant_uaq_landing": "UAQ Energy Plant"
        }

        site_names = set()

        for table_name in plant_mappings.keys():
            where_params = {"Cluster_Name": cluster}
            service = Dash_001Service()
            cluster_count = service.plant_repository.get_cluster_count_by_table(table_name, where_params)

            if cluster_count > 0:
                plant_results = service.plant_repository.get_sites_by_cluster_and_table(table_name, where_params)
                for plant_row in plant_results:
                    site_name = plant_row['Site_Name']
                    site_names.add(site_name)

        return list(site_names)

    def get_defaults(self, user):
        cluster = user.get("role").get("clusters")[0]
        plants = self.get_sites_by_cluster(cluster)
        plant = plants[0]
        return plant

    # def get_site_mapping(self, site):
    #     site_table_mappings = {
    #         'Jubail-Jazlah': 'Jubail_Chemicals_ppm',
    #         'Rabigh3': 'Rabigh3_Chemicals_ppm',
    #         'STPC': '',
    #         'UAQ': '',
    #     }
    #     table_name = site_table_mappings.get(site, None)
    #     return table_name

    def _is_eav_table(self, clickhouse_table: str) -> bool:
        """
        Check if a ClickHouse table has EAV schema (has Area, Stream, Chemical, Metric, Value columns).

        Args:
            clickhouse_table: ClickHouse table name

        Returns:
            True if table has EAV schema, False otherwise
        """
        try:
            # Use parameterized query for safety
            query = """
            SELECT name
            FROM system.columns
            WHERE table = {table_name:String}
              AND database = currentDatabase()
              AND name IN ('Area', 'Stream', 'Chemical', 'Metric', 'Value')
            """
            result = execute_clickhouse_query(query, params={"table_name": clickhouse_table})

            # EAV tables should have all 5 columns
            eav_columns = {row[0] for row in result.result_rows}
            required_columns = {'Area', 'Stream', 'Chemical', 'Metric', 'Value'}

            is_eav = required_columns.issubset(eav_columns)
            logger.debug(f"Table {clickhouse_table} EAV check: {is_eav} (found: {eav_columns})")
            return is_eav

        except Exception as e:
            logger.error(f"Error checking table schema for {clickhouse_table}: {e}")
            return False

    def _get_clickhouse_table_name(self, site: str, table_suffix: str = "Chemicals_ppm") -> Optional[str]:
        """
        Get the ClickHouse table name from site_table_mapping.

        Args:
            site: Site name (e.g., 'Rabigh3')
            table_suffix: Table suffix (e.g., 'Chemicals_ppm' or 'Chemicals_stock')

        Returns:
            ClickHouse table name or None if not found
        """
        try:
            # Construct the logical table name pattern: {site}_{table_suffix}
            logical_table_name = f"{site}_{table_suffix}"

            # Use case-insensitive matching for table_name (some sites use Stock vs stock)
            query = """
            SELECT clickhouse_table_name
            FROM site_table_mapping
            WHERE site_name = {site_name:String}
              AND lower(table_name) = lower({table_name:String})
              AND migration_status IN ('migrated', 'pending')
            LIMIT 1
            """

            result = execute_clickhouse_query(query, params={
                "site_name": site,
                "table_name": logical_table_name
            })

            if result.result_rows:
                return result.result_rows[0][0]
            return None

        except Exception as e:
            logger.error(f"Error getting ClickHouse table name for {site}: {e}")
            return None

    def get_area_values(self, site: Optional[str]) -> List[Dict[str, str]]:
        """
        Get distinct area values from ClickHouse Chemicals_ppm table.

        Args:
            site: Site name (e.g., 'Rabigh3'). Required for ClickHouse query.

        Returns:
            List of area options with label and value
        """
        if not site:
            # If no site provided, return empty list or default areas
            logger.warning("No site provided for get_area_values, returning empty list")
            return []

        try:
            # Get the ClickHouse table name for this site
            clickhouse_table = self._get_clickhouse_table_name(site, "Chemicals_ppm")

            if not clickhouse_table:
                logger.warning(f"No ClickHouse table found for site: {site}")
                return []

            # Query distinct Area values from ClickHouse
            query = f"""
            SELECT DISTINCT Area
            FROM `{clickhouse_table}`
            WHERE Area IS NOT NULL AND Area != ''
            ORDER BY Area
            """

            result = execute_clickhouse_query(query)

            if not result.result_rows:
                logger.info(f"No areas found in {clickhouse_table}")
                return []

            # Build options list
            options = []
            for row in result.result_rows:
                area_name = row[0]
                if area_name:
                    options.append({"label": area_name.replace("_", " "), "value": area_name})

            # Sort with RO first
            options.sort(key=lambda d: (0, "") if d["value"].upper() == "RO" else (1, d["value"]))

            logger.info(f"Retrieved {len(options)} areas from {clickhouse_table}")
            return options

        except Exception as e:
            logger.error(f"Error fetching areas from ClickHouse for site {site}: {e}")
            return []

    # -----------------------------
    # UPDATED: get_chemical_list()
    # -----------------------------
    def get_chemical_list(self, site: Optional[str], area: str) -> List[Dict[str, str]]:
        """
        Get distinct chemical values from ClickHouse Chemicals_ppm table for a given site and area.

        Args:
            site: Site name (e.g., 'Rabigh3'). Required for ClickHouse query.
            area: Area name (e.g., 'RO', 'Pre_Treatment'). Required for filtering.

        Returns:
            List of chemical options with label and value
        """
        if not site:
            logger.warning("No site provided for get_chemical_list, returning empty list")
            return []

        if not area:
            logger.warning("No area provided for get_chemical_list, returning empty list")
            return []

        try:
            # Get the ClickHouse table name for this site
            clickhouse_table = self._get_clickhouse_table_name(site, "Chemicals_ppm")

            if not clickhouse_table:
                logger.warning(f"No ClickHouse table found for site: {site}")
                return []

            # Query distinct Chemical values from ClickHouse filtered by area
            query = f"""
            SELECT DISTINCT Chemical
            FROM `{clickhouse_table}`
            WHERE Area = {{area:String}}
              AND Chemical IS NOT NULL AND Chemical != ''
            ORDER BY Chemical
            """

            result = execute_clickhouse_query(query, params={"area": area})

            if not result.result_rows:
                logger.info(f"No chemicals found in {clickhouse_table} for area: {area}")
                return []

            # Build options list
            chemicals = []
            for row in result.result_rows:
                chemical_name = row[0]
                if chemical_name:
                    chemicals.append({"label": chemical_name, "value": chemical_name})

            logger.info(f"Retrieved {len(chemicals)} chemicals from {clickhouse_table} for area: {area}")
            return chemicals

        except Exception as e:
            logger.error(f"Error fetching chemicals from ClickHouse for site {site}, area {area}: {e}")
            return []

    # -----------------------------
    # NEW: get_chemical_data() - Fetch from EAV tables
    # -----------------------------
    def get_chemical_data(
        self,
        site: str,
        area: str,
        chemical: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Get chemical data from ClickHouse EAV table for graphing and table display.

        Args:
            site: Site name (e.g., 'Rabigh3')
            area: Area name (e.g., 'RO', 'Pre_Treatment')
            chemical: Chemical name (e.g., 'Sodium_Bisulphite')
            from_date: Start date for filtering
            to_date: End date for filtering

        Returns:
            Dictionary with 'graph', 'table', and metadata
        """
        if not site or not area or not chemical:
            logger.warning("Missing required parameters for get_chemical_data")
            return {
                "graph": [],
                "table": [],
                "data_availability_for_given_date": True,
                "from_date": from_date.isoformat() if from_date else None,
                "to_date": to_date.isoformat() if to_date else None,
            }

        try:
            # Get the ClickHouse table name for this site
            clickhouse_table = self._get_clickhouse_table_name(site, "Chemicals_ppm")

            if not clickhouse_table:
                logger.warning(f"No ClickHouse table found for site: {site}")
                return {
                    "graph": [],
                    "table": [],
                    "data_availability_for_given_date": True,
                    "from_date": from_date.isoformat() if from_date else None,
                    "to_date": to_date.isoformat() if to_date else None,
                }

            # Build date filter
            date_filter = ""
            params = {"area": area, "chemical": chemical}

            if from_date:
                date_filter += " AND DateTime >= {from_date:DateTime}"
                params["from_date"] = from_date
            if to_date:
                date_filter += " AND DateTime <= {to_date:DateTime}"
                params["to_date"] = to_date

            # Query raw EAV data
            query = f"""
            SELECT DateTime, Stream, Metric, Value
            FROM `{clickhouse_table}`
            WHERE Area = {{area:String}}
              AND Chemical = {{chemical:String}}
              {date_filter}
            ORDER BY DateTime ASC
            """

            result = execute_clickhouse_query(query, params=params)

            if not result.result_rows:
                # Try fallback to last 7 days of available data
                logger.info(f"No data found for date range, trying fallback for {site}/{area}/{chemical}")
                fallback_result = self._get_chemical_data_fallback(
                    clickhouse_table, area, chemical
                )
                if fallback_result:
                    return fallback_result

                return {
                    "graph": [],
                    "table": [],
                    "data_availability_for_given_date": True,
                    "from_date": from_date.isoformat() if from_date else None,
                    "to_date": to_date.isoformat() if to_date else None,
                }

            # Process and pivot the EAV data
            return self._process_eav_data(
                result.result_rows,
                site,
                clickhouse_table,
                from_date,
                to_date,
                data_available=True,
            )

        except Exception as e:
            logger.error(f"Error fetching chemical data for {site}/{area}/{chemical}: {e}")
            return {
                "graph": [],
                "table": [],
                "data_availability_for_given_date": True,
                "from_date": from_date.isoformat() if from_date else None,
                "to_date": to_date.isoformat() if to_date else None,
                "error": str(e),
            }

    def _get_chemical_data_fallback(
        self, clickhouse_table: str, area: str, chemical: str
    ) -> Optional[Dict]:
        """
        Fallback to get last 7 days of available data when no data found for requested range.
        """
        try:
            # Find the date range of available data
            range_query = f"""
            SELECT MIN(DateTime) as min_date, MAX(DateTime) as max_date
            FROM `{clickhouse_table}`
            WHERE Area = {{area:String}}
              AND Chemical = {{chemical:String}}
              AND Value IS NOT NULL
            """
            range_result = execute_clickhouse_query(
                range_query, params={"area": area, "chemical": chemical}
            )

            if not range_result.result_rows or not range_result.result_rows[0][1]:
                return None

            max_date = range_result.result_rows[0][1]
            # Get last 7 days from max_date
            from datetime import timedelta
            fallback_from = max_date - timedelta(days=7)

            # Query with fallback date range
            query = f"""
            SELECT DateTime, Stream, Metric, Value
            FROM `{clickhouse_table}`
            WHERE Area = {{area:String}}
              AND Chemical = {{chemical:String}}
              AND DateTime >= {{from_date:DateTime}}
              AND DateTime <= {{to_date:DateTime}}
            ORDER BY DateTime ASC
            """

            result = execute_clickhouse_query(
                query,
                params={
                    "area": area,
                    "chemical": chemical,
                    "from_date": fallback_from,
                    "to_date": max_date,
                },
            )

            if not result.result_rows:
                return None

            # Extract site from table name for response
            site = clickhouse_table.split("_")[0] if "_" in clickhouse_table else ""

            processed = self._process_eav_data(
                result.result_rows,
                site,
                clickhouse_table,
                fallback_from,
                max_date,
                data_available=False,
            )
            return processed

        except Exception as e:
            logger.error(f"Error in fallback query: {e}")
            return None

    def _process_eav_data(
        self,
        rows: List,
        site: str,
        table_name: str,
        from_date: Optional[datetime],
        to_date: Optional[datetime],
        data_available: bool = True,
    ) -> Dict:
        """
        Process EAV rows and pivot into column-oriented format for graph/table.

        Graph metrics: ppm, Flow
        Table metrics: Consumption_per_Day, Consumption_per_Month, Consumption_per_Year
        """
        # Organize data by DateTime -> Stream -> Metric -> Value
        data_by_time: Dict[datetime, Dict[str, Dict[str, float]]] = {}
        streams_seen = set()
        metrics_seen = set()

        for row in rows:
            dt, stream, metric, value = row
            if dt not in data_by_time:
                data_by_time[dt] = {}
            if stream not in data_by_time[dt]:
                data_by_time[dt][stream] = {}
            data_by_time[dt][stream][metric] = value
            streams_seen.add(stream)
            metrics_seen.add(metric)

        # Sort timestamps
        sorted_times = sorted(data_by_time.keys())
        
        # Debug: Log what metrics were found
        logger.info(f"[CHEMICAL DATA] Metrics found in data: {metrics_seen}")
        logger.info(f"[CHEMICAL DATA] Streams found: {streams_seen}")

        # Define which metrics go to graph vs table
        # PPM metrics from database: PPM, Dosification_PPM, Equivalent_FE3+_PPM, Amount_FeOH3_PPM
        graph_metrics = [
            "PPM",
            "Flow",
            "Dosification_PPM",
            "Equivalent_FE3+_PPM",
            "Amount_FeOH3_PPM",
        ]
        table_metrics = ["Flow_per_day", "Flow_per_month", "Flow_per_year"]

        # Sort streams for consistent ordering (Stream_01, Stream_02, Total)
        sorted_streams = sorted(streams_seen, key=lambda s: (0 if s == "Total" else 1, s))

        # Build graph columns
        graph_columns = []

        # DateTime column for graph
        datetime_data = [dt.isoformat() for dt in sorted_times]
        graph_columns.append({
            "columnName": "DateTime",
            "columnType": "timestamp[ns]",
            "tableName": table_name,
            "siteName": site,
            "dataSource": datetime_data,
        })

        # Add columns for each Stream + Metric combination (graph metrics only)
        for stream in sorted_streams:
            for metric in graph_metrics:
                if metric in metrics_seen:
                    col_name = f"{stream}_{metric}"
                    col_data = []
                    for dt in sorted_times:
                        val = data_by_time[dt].get(stream, {}).get(metric)
                        col_data.append(val)

                    graph_columns.append({
                        "columnName": col_name,
                        "columnType": "double",
                        "tableName": table_name,
                        "siteName": site,
                        "dataSource": col_data,
                    })

        # Build table columns - Always include DateTime and consumption metrics
        table_columns = []

        # DateTime column for table
        table_columns.append({
            "columnName": "DateTime",
            "columnType": "timestamp[ns]",
            "tableName": table_name,
            "siteName": site,
            "dataSource": datetime_data,
        })

        # Always add consumption columns (Daily, Monthly, Yearly)
        # Use Total stream if available, otherwise first stream
        stream = "Total" if "Total" in streams_seen else (sorted_streams[0] if sorted_streams else None)
        logger.info(f"[CHEMICAL DATA] Using stream for consumption: {stream}")

        # Map of consumption metrics to display names
        # Note: Database uses Flow_per_day, Flow_per_month, Flow_per_year
        consumption_columns = [
            ("Flow_per_day", "Daily_Consumption"),
            ("Flow_per_month", "Monthly_Consumption"),
            ("Flow_per_year", "Yearly_Consumption"),
        ]

        # Debug: Check sample data structure for first timestamp
        if sorted_times and stream:
            first_time = sorted_times[0]
            sample_data = data_by_time.get(first_time, {}).get(stream, {})
            logger.info(f"[CHEMICAL DATA] Sample data for {stream} at {first_time}: {sample_data}")
            # Also check what streams have consumption data
            for s in sorted_streams:
                sample_stream_data = data_by_time.get(first_time, {}).get(s, {})
                has_consumption = any(m in sample_stream_data for m in ["Consumption_per_Day", "Consumption_per_Month", "Consumption_per_Year"])
                if has_consumption:
                    logger.info(f"[CHEMICAL DATA] Stream {s} has consumption data: {sample_stream_data}")

        for metric_name, display_name in consumption_columns:
            col_data = []
            for dt in sorted_times:
                if stream and metric_name in metrics_seen:
                    val = data_by_time[dt].get(stream, {}).get(metric_name)
                else:
                    val = None
                col_data.append(val)

            # Debug: Log non-null count
            non_null = sum(1 for v in col_data if v is not None)
            logger.info(f"[CHEMICAL DATA] {display_name}: {non_null}/{len(col_data)} non-null values")

            table_columns.append({
                "columnName": display_name,
                "columnType": "double",
                "tableName": table_name,
                "siteName": site,
                "dataSource": col_data,
            })

        # Determine actual date range from data
        actual_from = sorted_times[0] if sorted_times else from_date
        actual_to = sorted_times[-1] if sorted_times else to_date

        return {
            "graph": graph_columns,
            "table": table_columns,
            "data_availability_for_given_date": data_available,
            "from_date": actual_from.isoformat() if actual_from else None,
            "to_date": actual_to.isoformat() if actual_to else None,
        }

    # -----------------------------
    # get_chemical_stock_data() - Fetch stock data from EAV tables (Backward Compatible)
    # -----------------------------
    def _round_value(self, value: float) -> float:
        """
        Round numeric values based on magnitude:
        - If value < 1: round to 4 decimal places
        - If value >= 1: round to 2 decimal places

        Args:
            value: Numeric value to round

        Returns:
            Rounded value
        """
        if value is None:
            return None

        try:
            num_value = float(value)
            if abs(num_value) < 1:
                return round(num_value, 4)
            else:
                return round(num_value, 2)
        except (ValueError, TypeError):
            return value

    def get_chemical_stock_data(
            self,
            site: str,
            target_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Get chemical stock data from ClickHouse EAV tables.
        BACKWARD COMPATIBLE: Returns the same structure as the old ChemicalMappingConstants-based implementation.

        Fetches from TWO tables:
        - Chemicals_ppm: for line1/line2 (measured/expected ppm, flow data)
        - Chemicals_stock: for level1/level2/stock (tank levels and storage)

        Args:
            site: Site name (e.g., 'Rabigh3')
            target_date: Optional specific date for filtering

        Returns:
            {
                "siteName": "Rabigh3",
                "chemicals": {
                    "Chemical Name": {
                        "line1": [ppm, flow] or [],
                        "line2": [ppm, flow] or [],
                        "level1": value or None,
                        "level2": value or None,
                        "stock": [storage_values] or [],
                        "totalStock": total_storage_value or None
                    }
                }
            }
        """
        if not site:
            logger.warning("No site provided for get_chemical_stock_data")
            return {
                "siteName": site,
                "data_availability_for_given_date": True,
                "from_date": None,
                "to_date": None,
                "dateFilter": "latest",
                "chemicals": {},
            }

        try:
            # Get ClickHouse table names for both tables
            stock_table = self._get_clickhouse_table_name(site, "Chemicals_stock")
            ppm_table = self._get_clickhouse_table_name(site, "Chemicals_ppm")

            if not stock_table:
                logger.warning(f"No ClickHouse stock table found for site: {site}")
                return {
                    "siteName": site,
                    "data_availability_for_given_date": True,
                    "from_date": None,
                    "to_date": None,
                    "dateFilter": target_date.isoformat() if target_date else "latest",
                    "chemicals": {},
                }

            # Check if stock table has EAV schema
            if not self._is_eav_table(stock_table):
                logger.info(f"Stock table {stock_table} is not EAV format, skipping")
                return {
                    "siteName": site,
                    "data_availability_for_given_date": True,
                    "from_date": None,
                    "to_date": None,
                    "dateFilter": target_date.isoformat() if target_date else "latest",
                    "chemicals": {},
                    "info": "Stock table is not in EAV format",
                }

            # Build date filter parameters
            date_filter = ""
            params = {}

            if target_date:
                date_filter = """
                    AND DateTime >= {start_date:DateTime}
                    AND DateTime <= {end_date:DateTime}
                """
                params["start_date"] = target_date.replace(hour=0, minute=0, second=0)
                params["end_date"] = target_date.replace(hour=23, minute=59, second=59)

            # 1. Fetch STOCK data (level1, level2, stock, totalStock)
            chemical_datetime_map, stock_data_organized = self._fetch_stock_table_data(
                stock_table, date_filter, params
            )

            # 2. Fetch PPM data (line1, line2 with ppm and flow)
            ppm_data_organized = {}
            if ppm_table and self._is_eav_table(ppm_table):
                ppm_data_organized = self._fetch_ppm_table_data(
                    ppm_table, chemical_datetime_map
                )



            # 3. Format the response
            chemicals_data = self._format_chemical_stock_response(
                site,
                chemical_datetime_map,
                stock_data_organized,
                ppm_data_organized,
            )

            return {
                "siteName": site,
                "data_availability_for_given_date": True,
                "from_date": None,
                "to_date": target_date.isoformat() if target_date else None,
                "dateFilter": target_date.isoformat() if target_date else "latest",
                "chemicals": chemicals_data,
            }

        except Exception as e:
            logger.error(f"Error fetching chemical stock data for {site}: {e}")
            return {
                "siteName": site,
                "data_availability_for_given_date": False,
                "from_date": None,
                "to_date": None,
                "dateFilter": target_date.isoformat() if target_date else "latest",
                "chemicals": {},
                "error": str(e),
            }

    def _fetch_stock_table_data(
            self,
            stock_table: str,
            date_filter: str,
            params: Dict,
    ) -> Dict[str, Dict[str, List]]:
        """
        Fetch data from the stock EAV table only.

        Returns:
            Dict organized by Chemical -> Stream -> Metric -> Value
        """
        query = f"""
        SELECT DateTime, Area, Stream, Chemical, Metric, Value
        FROM `{stock_table}`
        WHERE Chemical IS NOT NULL
        AND Chemical != 'Unknown'
        AND Metric IN ('Storage_Days_Total', 'Level')
        AND Value IS NOT NULL
          {date_filter}
        ORDER BY Chemical, Stream, Metric, DateTime DESC
        LIMIT 1 BY Chemical, Stream, Metric
        """

        result = execute_clickhouse_query(query, params=params if params else None)


        # Organize stock data by Chemical -> DateTime
        chemical_datetime_map = {}
        stock_data_organized = {}

        for row in result.result_rows:
            dt, area, stream, chemical, metric, value = row

            # Track datetime and area for ppm query
            if chemical not in chemical_datetime_map:
                chemical_datetime_map[chemical] = {
                    'datetime': dt,
                    'area': area
                }

            # Organize stock data with rounding
            if chemical not in stock_data_organized:
                stock_data_organized[chemical] = {}
            if stream not in stock_data_organized[chemical]:
                stock_data_organized[chemical][stream] = {}

            stock_data_organized[chemical][stream][metric] = self._round_value(value)


        return chemical_datetime_map, stock_data_organized

    def _fetch_ppm_table_data(
            self,
            ppm_table: str,
            chemical_datetime_map: Dict,
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Fetch ppm and Flow data for each chemical from the ppm EAV table.

        Args:
            ppm_table: Name of the ppm table
            chemical_datetime_map: Dict with datetime and area info for each chemical

        Returns:
            Dict organized by Chemical -> Stream -> Metric -> Value
        """
        ppm_data_organized = {}

        for chemical, info in chemical_datetime_map.items():
            dt = info['datetime']
            area = info['area']

            ppm_query = f"""
            SELECT Stream, Metric, Value
            FROM `{ppm_table}`
            WHERE Chemical = {{chemical:String}}
              AND Area = {{area:String}}
              AND DateTime = {{datetime:DateTime}}
              AND Metric IN ('PPM', 'Flow', 'PPM_Exp', 'Flow_Exp')
              AND Value IS NOT NULL
            ORDER BY Stream, Metric
            """


            ppm_params = {
                'chemical': chemical,
                'area': area,
                'datetime': dt
            }


            try:
                ppm_result = execute_clickhouse_query(ppm_query, params=ppm_params)


                # Organize ppm data with rounding
                if chemical not in ppm_data_organized:
                    ppm_data_organized[chemical] = {}

                for ppm_row in ppm_result.result_rows:
                    stream, metric, value = ppm_row

                    if stream not in ppm_data_organized[chemical]:
                        ppm_data_organized[chemical][stream] = {}

                    ppm_data_organized[chemical][stream][metric] = self._round_value(value)

            except Exception as e:
                logger.error(f"Error fetching ppm data for {chemical}: {e}")
                ppm_data_organized[chemical] = {}



        return ppm_data_organized

    def _format_chemical_stock_response(
            self,
            site: str,
            chemical_datetime_map: Dict,
            stock_data_organized: Dict,
            ppm_data_organized: Dict,
    ) -> Dict[str, Dict]:
        """
        Format the chemical stock data into the final response structure.
        Supports line1, line2 for all sites, and line3 for UAQ site.
        Includes nested ppm/flow objects with measured/expected values.

        Args:
            site: Site name to determine number of lines (UAQ = 3, others = 2)
            chemical_datetime_map: Dict with datetime and area info for each chemical
            stock_data_organized: Stock data organized by Chemical -> Stream -> Metric -> Value
            ppm_data_organized: PPM data organized by Chemical -> Stream -> Metric -> Value

        Returns:
            Dict organized by chemical name with all required keys
            {
                "Chemical Name": {
                    "line1": {"ppm": {"measured": ..., "expected": ...}, "flow": {...}},
                    "line2": {"ppm": {"measured": ..., "expected": ...}, "flow": {...}},
                    "line3": {...},  # Only for UAQ
                    "Total": {"ppm": {"measured": ..., "expected": ...}, "flow": {...}},
                    "level1": value or None,
                    "level2": value or None,
                    "level3": value or None,  # Only for UAQ
                    "stock": [Storage_Days_Total from Total stream]
                }
            }
        """
        final_data = {}

        # Determine max lines based on site
        max_lines = 3 if site.upper() == "UAQ" else 2

        for chemical in chemical_datetime_map.keys():
            chem_response = {}

            # Get ppm and stock data for this chemical
            ppm_chem = ppm_data_organized.get(chemical, {})
            stock_chem = stock_data_organized.get(chemical, {})

            # Sort streams to ensure consistent ordering (Stream_01, Stream_02, etc., excluding Total)
            ppm_streams = sorted(
                [s for s in ppm_chem.keys() if s != 'Total'],
                key=lambda x: x
            )

            stock_streams = sorted(
                [s for s in stock_chem.keys() if s != 'Total'],
                key=lambda x: x
            )

            # ============ LINE DATA (line1, line2, line3 for UAQ) ============
            # Always add line1, line2 (and line3 for UAQ), even if empty
            for line_num in range(1, max_lines + 1):
                line_key = f'line{line_num}'
                line_data = {
                    "ppm": {"measured": None, "expected": None},
                    "flow": {"measured": None, "expected": None}
                }

                # Check if we have a corresponding stream
                if line_num <= len(ppm_streams):
                    stream = ppm_streams[line_num - 1]
                    stream_data = ppm_chem.get(stream, {})

                    # Map PPM values
                    if 'PPM' in stream_data:
                        line_data["ppm"]["measured"] = stream_data['PPM']
                    if 'PPM_Exp' in stream_data:
                        line_data["ppm"]["expected"] = stream_data['PPM_Exp']

                    # Map Flow values
                    if 'Flow' in stream_data:
                        line_data["flow"]["measured"] = stream_data['Flow']
                    if 'Flow_Exp' in stream_data:
                        line_data["flow"]["expected"] = stream_data['Flow_Exp']

                chem_response[line_key] = line_data

            # ============ TOTAL SECTION ============
            # Extract Total stream data from ppm_data_organized
            total_data = {
                "ppm": {"measured": None, "expected": None},
                "flow": {"measured": None, "expected": None}
            }

            total_stream_ppm = ppm_chem.get('Total', {})
            if total_stream_ppm:
                # Map PPM values
                if 'PPM' in total_stream_ppm:
                    total_data["ppm"]["measured"] = total_stream_ppm['PPM']
                if 'PPM_Exp' in total_stream_ppm:
                    total_data["ppm"]["expected"] = total_stream_ppm['PPM_Exp']

                # Map Flow values
                if 'Flow' in total_stream_ppm:
                    total_data["flow"]["measured"] = total_stream_ppm['Flow']
                if 'Flow_Exp' in total_stream_ppm:
                    total_data["flow"]["expected"] = total_stream_ppm['Flow_Exp']

            chem_response['Total'] = total_data

            # ============ LEVEL DATA (level1, level2, level3 for UAQ) ============
            # Collect all Level values from stock data (excluding Total stream)
            level_values = []
            for stream in stock_streams:
                metrics = stock_chem.get(stream, {})
                if 'Level' in metrics:
                    level_values.append(metrics['Level'])  # Already rounded

            # Always add level1, level2 (and level3 for UAQ)
            chem_response['level1'] = level_values[0] if len(level_values) > 0 else None
            chem_response['level2'] = level_values[1] if len(level_values) > 1 else None
            if max_lines == 3:
                chem_response['level3'] = level_values[2] if len(level_values) > 2 else None

            # ============ STOCK DATA - FIXED ============
            # stock: Array containing Total stream's Storage_Days_Total
            # If Total stream doesn't have it, sum from individual streams
            stock_values = []
            total_stream_stock = stock_chem.get('Total', {})

            if total_stream_stock and 'Storage_Days_Total' in total_stream_stock:
                # Use Total stream's Storage_Days_Total
                stock_values.append(total_stream_stock['Storage_Days_Total'])
            else:
                # Fallback: Sum Storage_Days_Total from individual streams
                total_storage = 0
                has_storage = False
                for stream in stock_streams:
                    metrics = stock_chem.get(stream, {})
                    if 'Storage_Days_Total' in metrics:
                        total_storage += metrics['Storage_Days_Total']
                        has_storage = True

                if has_storage:
                    stock_values.append(self._round_value(total_storage))

            chem_response['stock'] = stock_values

            # Convert chemical name format (replace underscores with spaces)
            display_name = chemical.replace("_", " ")
            final_data[display_name] = chem_response

        return final_data


    # -----------------------------
    # NEW: get_chemical_data_by_metric()
    # -----------------------------
    def get_chemical_data_by_metric(
        self,
        site: str,
        area: str,
        chemical: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Fetch chemical data and segregate by Metric type for graph and table views.

        This method fetches all data for a specific chemical in one query,
        then post-processes to separate into:
        - Graph Data: Metric in ['ppm', 'Flow'] - for visual trends
        - Table Data: Metric in ['Consumption_per_Day', 'Consumption_per_Month', 'Consumption_per_Year']

        Args:
            site: Site identifier (e.g., 'Rabigh3')
            area: Area filter (e.g., 'RO', 'Pre-treatment')
            chemical: Chemical name (e.g., 'Ferric Chloride')
            from_date: Start date for filtering
            to_date: End date for filtering

        Returns:
            Dictionary with 'graph' and 'table' data separated by metric type
        """
        from infrastructure.services.clickhouse_adls_service import ClickHouseADLSService

        # Metric type definitions
        GRAPH_METRICS = ['ppm', 'Flow']
        TABLE_METRICS = ['Flow_per_day', 'Flow_per_month', 'Flow_per_year']

        # Build table name based on site
        table_name = f"{site}_Chemicals_ppm"

        # Define columns to fetch (EAV structure)
        columns_request = [
            {"siteName": site, "tableName": table_name, "columnName": "DateTime", "columnType": "timestamp[ns]"},
            {"siteName": site, "tableName": table_name, "columnName": "Area", "columnType": "string"},
            {"siteName": site, "tableName": table_name, "columnName": "Stream", "columnType": "string"},
            {"siteName": site, "tableName": table_name, "columnName": "Chemical", "columnType": "string"},
            {"siteName": site, "tableName": table_name, "columnName": "Metric", "columnType": "string"},
            {"siteName": site, "tableName": table_name, "columnName": "Value", "columnType": "double"},
        ]

        # Filters for Area and Chemical
        filters = {
            "Area": area,
            "Chemical": chemical
        }

        # Fetch data from ClickHouse
        clickhouse_service = ClickHouseADLSService()
        response = clickhouse_service.get_column_data_sources(
            columns_list=columns_request,
            from_date=from_date,
            to_date=to_date,
            filters=filters,
            enable_fallback=True
        )

        # Extract column data and metadata
        if isinstance(response, dict) and 'column_data' in response:
            column_data = response.get('column_data', [])
            metadata = response.get('metadata', {
                "data_availability_for_given_date": True,
                "from_date": from_date,
                "to_date": to_date
            })
        else:
            column_data = response if isinstance(response, list) else []
            metadata = {
                "data_availability_for_given_date": True,
                "from_date": from_date,
                "to_date": to_date
            }

        # Build data lookup by column name
        data_by_column = {}
        for col in column_data:
            col_name = col.get('columnName') if isinstance(col, dict) else getattr(col, 'columnName', None)
            data_source = col.get('dataSource', []) if isinstance(col, dict) else getattr(col, 'dataSource', [])
            if col_name:
                data_by_column[col_name] = data_source

        # Get data arrays
        datetimes = data_by_column.get('DateTime', [])
        areas = data_by_column.get('Area', [])
        streams = data_by_column.get('Stream', [])
        chemicals = data_by_column.get('Chemical', [])
        metrics = data_by_column.get('Metric', [])
        values = data_by_column.get('Value', [])

        # Segregate data by metric type
        graph_data = {
            "ppm": [],
            "flow": []
        }
        table_data = {
            "consumption_per_day": [],
            "consumption_per_month": [],
            "consumption_per_year": []
        }

        # Process each row
        data_length = len(datetimes)
        for i in range(data_length):
            dt = datetimes[i] if i < len(datetimes) else None
            stream = streams[i] if i < len(streams) else None
            metric = metrics[i] if i < len(metrics) else None
            value = values[i] if i < len(values) else None

            if not metric or value is None:
                continue

            record = {
                "dateTime": dt,
                "stream": stream,
                "value": value
            }

            metric_lower = metric.lower() if metric else ""

            # Segregate into graph or table data
            if metric_lower == 'ppm':
                record["unit"] = "ppm"
                graph_data["ppm"].append(record)
            elif metric_lower == 'flow':
                record["unit"] = "flow"
                graph_data["flow"].append(record)
            elif metric_lower == 'flow_per_day':
                table_data["consumption_per_day"].append(record)
            elif metric_lower == 'flow_per_month':
                table_data["consumption_per_month"].append(record)
            elif metric_lower == 'flow_per_year':
                table_data["consumption_per_year"].append(record)

        # Format table data date-wise for tabular view
        formatted_table_data = self._format_consumption_table(table_data)

        return {
            "graph": graph_data,
            "table": formatted_table_data,
            "metadata": metadata
        }

    def _format_consumption_table(self, table_data: Dict[str, list]) -> Dict[str, Any]:
        """
        Format consumption data date-wise for tabular view.

        Groups data by date and creates rows suitable for a table display.

        Args:
            table_data: Dictionary with consumption_per_day, consumption_per_month, consumption_per_year lists

        Returns:
            Formatted table data with rows organized by date
        """

        from collections import defaultdict

        # Group by date for daily consumption (primary table)
        daily_by_date = defaultdict(list)
        monthly_by_date = defaultdict(list)
        yearly_by_date = defaultdict(list)


        for record in table_data.get("consumption_per_day", []):
            dt = record.get("dateTime")
            if dt:
                # Extract date part
                date_key = dt[:10] if isinstance(dt, str) and len(dt) >= 10 else str(dt)[:10]
                daily_by_date[date_key].append(record)

        for record in table_data.get("consumption_per_month", []):
            dt = record.get("dateTime")
            if dt:
                date_key = dt[:10] if isinstance(dt, str) and len(dt) >= 10 else str(dt)[:10]
                monthly_by_date[date_key].append(record)

        for record in table_data.get("consumption_per_year", []):
            dt = record.get("dateTime")
            if dt:
                date_key = dt[:10] if isinstance(dt, str) and len(dt) >= 10 else str(dt)[:10]
                yearly_by_date[date_key].append(record)

        # Build formatted table rows
        all_dates = sorted(set(daily_by_date.keys()) | set(monthly_by_date.keys()) | set(yearly_by_date.keys()), reverse=True)

        rows = []
        for date_str in all_dates:
            row = {
                "date": date_str,
                "daily": [],
                "monthly": [],
                "yearly": []
            }

            # Add daily values (may have multiple streams)
            for rec in daily_by_date.get(date_str, []):
                row["daily"].append({
                    "stream": rec.get("stream"),
                    "value": rec.get("value")
                })

            # Add monthly values
            for rec in monthly_by_date.get(date_str, []):
                row["monthly"].append({
                    "stream": rec.get("stream"),
                    "value": rec.get("value")
                })

            # Add yearly values
            for rec in yearly_by_date.get(date_str, []):
                row["yearly"].append({
                    "stream": rec.get("stream"),
                    "value": rec.get("value")
                })

            rows.append(row)

        return {
            "rows": rows,
            "columns": ["date", "daily", "monthly", "yearly"],
            "total_rows": len(rows)

        }