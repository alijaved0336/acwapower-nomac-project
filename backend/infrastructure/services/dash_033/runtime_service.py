"""
Runtime Service for Dashboard-033
Handles rack runtime calculations and related operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base_service import Dash033BaseService
from infrastructure.exceptions import ClickHouseServiceError
from constants import Dash033Config

logger = logging.getLogger(__name__)

"""
Runtime Service for Dashboard-033
Handles rack runtime calculations and related operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base_service import Dash033BaseService
from infrastructure.exceptions import ClickHouseServiceError
from constants import Dash033Config

logger = logging.getLogger(__name__)


class RuntimeService(Dash033BaseService):
    """
    Service class for rack runtime operations.
    Handles runtime percentage calculations and data formatting.
    """

    def get_racks_runtime_only(
            self,
            site_name: str = None,
            user: dict = None,
            start_time: datetime = None,
            end_time: datetime = None,
            racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get rack runtime percentages with proper calculation logic and rack filtering.

        Args:
            site_name: Site identifier
            user: User context for default site resolution
            start_time: Start datetime for filtering
            end_time: End datetime for filtering
            racks: Optional list of rack IDs to filter

        Returns:
            Dictionary with runtime and stoptime percentages by rack, including date metadata

        Raises:
            ClickHouseServiceError: If data retrieval or calculation fails
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)

            site_name = self._normalize_site_name(site_name)
            table_prefix = self.site_table_suffix_mappings(site_name)
            table_suffix = f"{table_prefix}_mode_racks_operation"

            logger.debug(f"Getting runtime data for {site_name}/{table_suffix} with racks filter: {racks}")

            # Initialize runtime_result to avoid UnboundLocalError
            runtime_result = None
            date_metadata = {}

            # Use ClickHouse repository to get data
            result = self._get_data_using_clickhouse(
                site_name=site_name,
                table_suffix=table_suffix,
                start_time=start_time,
                end_time=end_time,
                racks=racks
            )

            # Extract date metadata from result
            date_metadata = {
                "to_date": result.get("to_date"),
                "from_date": result.get("from_date"),
                "data_availability_for_given_date": result.get("data_availability_for_given_date", True)
            }

            if result["success"] and result["data"]:
                clickhouse_data = result["data"]

                # Get available columns from first row
                available_columns = list(clickhouse_data[0].keys()) if clickhouse_data else []
                logger.debug(f"[RUNTIME] Available columns: {available_columns}")

                # Enhanced flexible column matching
                found_columns, duration_unit = self._find_runtime_columns(available_columns)

                if not found_columns.get("Train"):
                    logger.warning(f"[RUNTIME] No Train column found. Available: {available_columns}")
                    # Return safe empty response with date metadata
                    return self._empty_runtime_response(date_metadata)

                # Process runtime calculations
                runtime_result = self._calculate_runtime_percentage_clickhouse(
                    clickhouse_data, found_columns, duration_unit
                )
                
                if runtime_result:
                    logger.info(
                        f"[RUNTIME] Calculation complete - "
                        f"Processed {len(runtime_result)} trains/racks"
                    )
                else:
                    logger.warning("[RUNTIME] Runtime calculation returned None")

            if runtime_result:
                return self._format_runtime_result_clickhouse(
                    runtime_result, clickhouse_data, found_columns, date_metadata
                )

            # Return safe empty response with date metadata
            logger.info(f"No runtime data found for site {site_name} with racks filter: {racks}")
            return self._empty_runtime_response(date_metadata)

        except ClickHouseServiceError:
            raise  # Re-raise our custom exceptions
        except Exception as e:
            logger.error(f"Error in get_racks_runtime_only: {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to retrieve rack runtime data: {str(e)}"
            ) from e

    def _empty_runtime_response(self, date_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Return a safe empty response structure for runtime data.

        Args:
            date_metadata: Optional dictionary with date metadata (to_date, from_date, data_availability)

        Returns:
            Dictionary with empty runtime structure and date metadata
        """
        response = {
            "rackruntimestoptime": {
                "G1": {
                    "x": [{"name": "Racks", "data": []}],
                    "y": [
                        {"name": "Runtime %", "data": []},
                        {"name": "Stoptime %", "data": []}
                    ]
                }
            }
        }

        # Add date metadata if provided
        if date_metadata:
            response.update(date_metadata)

        return response

    def _get_data_using_clickhouse(
            self,
            site_name: str,
            table_suffix: str,
            start_time: datetime = None,
            end_time: datetime = None,
            racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve data from ClickHouse with filtering.

        Args:
            site_name: Site identifier
            table_suffix: Table suffix to query
            start_time: Start datetime filter
            end_time: End datetime filter
            racks: Optional rack filter list

        Returns:
            Dictionary with success flag, data, and date metadata

        Raises:
            ClickHouseServiceError: If query fails
        """
        try:
            clickhouse_table_name = self.repository.get_clickhouse_table_name(site_name, table_suffix)
            if not clickhouse_table_name:
                logger.error(f"No ClickHouse table found for site {site_name} with suffix {table_suffix}")
                return {"success": False, "data": []}

            columns = self.repository.get_table_columns(clickhouse_table_name)
            available_columns = [col["name"] for col in columns]

            datetime_column = self.repository.get_datetime_column(clickhouse_table_name)

            # Use repository method to find rack column
            rack_column = self.repository.get_rack_trailer_column(clickhouse_table_name)
            logger.info(f"[RUNTIME][DATA] Detected rack column: {rack_column}")

            final_columns = available_columns.copy()
            
            logger.info(
                f"[RUNTIME][DATA] COLUMN ORDER ENFORCED - "
                f"Final column order: {final_columns}"
            )

            where_conditions, query_params = [], {}
            # Date filtering
            if datetime_column and start_time and end_time:
                self._validate_column_names([datetime_column], "runtime date filtering")
                # Filter by Start_Time within the requested range
                where_conditions.append(
                    f"`{datetime_column}` >= {{start_date:DateTime}} AND `{datetime_column}` <= {{end_date:DateTime}}"
                )
                query_params["start_date"] = start_time
                query_params["end_date"] = end_time
                
                # Also filter by End_Time to ensure it doesn't extend beyond requested end_date
                # This prevents showing operations that start within range but end after the requested end_date
                if "End_Time" in available_columns:
                    self._validate_column_names(["End_Time"], "runtime end time filtering")
                    where_conditions.append(
                        f"`End_Time` <= {{end_date:DateTime}}"
                    )
                    logger.debug(
                        f"[RUNTIME] Applying End_Time filter to ensure operations don't extend beyond requested end_date"
                    )

            # Rack filtering using repository-detected column
            if rack_column and racks:
                validated_racks = [rack for rack in racks if rack and isinstance(rack, str)]
                if validated_racks:
                    self._validate_column_names([rack_column], "runtime rack filtering")
                    rack_params = []
                    for i, rack in enumerate(validated_racks):
                        param_name = f"rack_{i}"
                        rack_params.append(f"{{{param_name}:String}}")
                        query_params[param_name] = str(rack)
                    where_conditions.append(f"`{rack_column}` IN ({', '.join(rack_params)})")
                    logger.debug(
                        f"[RUNTIME] Applying rack filter on column '{rack_column}' with values: {validated_racks}")

            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=clickhouse_table_name,
                column_names=final_columns,
                where_conditions=where_conditions,
                query_params=query_params,
                limit=Dash033Config.MAX_RUNTIME_DATA_ROWS
            )

            # Extract result_rows and metadata from Dict response
            result_rows = result_dict.get("result_rows", [])
            to_date = result_dict.get("to_date")
            from_date = result_dict.get("from_date")
            data_availability_for_given_date = result_dict.get("data_availability_for_given_date", True)

            logger.info(
                f"[RUNTIME][DATA] Retrieved {len(result_rows)} rows from ClickHouse table "
                f"{clickhouse_table_name} (from_date: {from_date}, to_date: {to_date}, "
                f"data_available: {data_availability_for_given_date})"
            )

            # ============================================================
            # FIX: Detect actual columns from first row if mismatch
            # ============================================================
            if result_rows:
                first_row = result_rows[0]
                actual_column_count = len(first_row)
                expected_column_count = len(final_columns)
                
                logger.debug(
                    f"[RUNTIME][DATA] First row data sample (length={actual_column_count}): "
                    f"{first_row[:min(3, actual_column_count)]}"
                )
                logger.debug(
                    f"[RUNTIME][DATA] Expected columns (length={expected_column_count}): "
                    f"{final_columns[:min(3, expected_column_count)]}"
                )
                
                if actual_column_count != expected_column_count:
                    logger.warning(
                        f"[RUNTIME][DATA] Column count mismatch detected! "
                        f"Actual: {actual_column_count}, Expected: {expected_column_count}"
                    )
                    
                    # WORKAROUND: Check if there's an extra datetime column at the start
                    if actual_column_count == expected_column_count + 1:
                        # Check if first value is datetime
                        if isinstance(first_row[0], datetime):
                            logger.warning(
                                f"[RUNTIME][DATA] Detected extra datetime column at position 0. "
                                f"Adding to column list."
                            )
                            # Add a generic datetime column name at the start
                            final_columns = ['datetime_index'] + final_columns
                            logger.info(
                                f"[RUNTIME][DATA] ADJUSTED column order: {final_columns}"
                            )
                        else:
                            logger.error(
                                f"[RUNTIME][DATA] COLUMN MISMATCH - cannot auto-fix. "
                                f"Expected columns: {final_columns}"
                            )
                            logger.error(f"[RUNTIME][DATA] Got row values: {first_row}")
                            raise ClickHouseServiceError(
                                "Column count mismatch between query result and expected columns"
                            )
                    else:
                        logger.error(
                            f"[RUNTIME][DATA] COLUMN MISMATCH DETECTED! "
                            f"Result row length ({actual_column_count}) != "
                            f"Column list length ({expected_column_count})"
                        )
                        logger.error(f"[RUNTIME][DATA] Expected columns: {final_columns}")
                        logger.error(f"[RUNTIME][DATA] Got row values: {first_row}")
                        raise ClickHouseServiceError(
                            "Column count mismatch between query result and expected columns"
                        )

            # Create dictionaries by zipping columns with rows
            data = []
            for idx, row in enumerate(result_rows):
                try:
                    row_dict = dict(zip(final_columns, row))
                    data.append(row_dict)
                    
                    if idx < 3:
                        logger.debug(
                            f"[RUNTIME][DATA] Row {idx} mapped successfully - "
                            f"Sample keys: {list(row_dict.keys())[:3]}"
                        )
                except Exception as zip_error:
                    logger.error(
                        f"[RUNTIME][DATA] Error zipping row {idx}: {zip_error}. "
                        f"Row length: {len(row)}, Columns length: {len(final_columns)}"
                    )
                    raise

            logger.info(
                f"[RUNTIME][DATA] Successfully created {len(data)} data dictionaries "
                f"with column order preserved"
            )

            return {
                "success": True,
                "data": data,
                "to_date": to_date,
                "from_date": from_date,
                "data_availability_for_given_date": data_availability_for_given_date
            }

        except ClickHouseServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting data from ClickHouse: {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to retrieve data from ClickHouse table: {str(e)}"
            ) from e

    def _find_runtime_columns(self, available_columns: List[str]) -> tuple:
        """
        Find required columns for runtime calculation using flexible matching.

        Args:
            available_columns: List of available column names

        Returns:
            Tuple of (found_columns dict, duration_unit string)
        """
        column_mappings = Dash033Config.COLUMN_MAPPINGS

        found_columns = {}
        duration_unit = None

        # Use config-based mappings for consistency
        for standard_name in ["Train", "Start_Time", "End_Time", "Duration_Hours", "Duration_Days"]:
            possible_names = column_mappings.get(standard_name, [])
            for possible_name in possible_names:
                if possible_name in available_columns:
                    found_columns[standard_name] = possible_name
                    logger.debug(f"[RUNTIME] Mapped {standard_name} -> {possible_name}")

                    # Track duration unit type
                    if standard_name == "Duration_Hours":
                        duration_unit = "hours"
                    elif standard_name == "Duration_Days":
                        duration_unit = "days"
                    break

        return found_columns, duration_unit

    def _calculate_runtime_percentage_clickhouse(
            self, data: List[Dict], found_columns: Dict, duration_unit: str
    ) -> Optional[Dict]:
        """
        Calculate runtime percentages from ClickHouse data.

        Args:
            data: List of data rows
            found_columns: Mapping of standard column names to actual columns
            duration_unit: Unit of duration ("hours" or "days")

        Returns:
            Dictionary mapping train IDs to duration lists, or None if calculation fails
        """
        try:
            if not data or not found_columns.get("Train"):
                return None

            rack_durations = {}
            train_col = found_columns["Train"]
            duration_col = found_columns.get("Duration_Hours") or found_columns.get("Duration_Days")

            if not duration_col:
                logger.warning("No duration column found for runtime calculation")
                return None

            processed_count = 0
            skipped_count = 0

            for idx, record in enumerate(data):
                train = record.get(train_col)
                if train is None:
                    skipped_count += 1
                    if idx < 5:  # Log first few skips
                        logger.debug(f"[RUNTIME][CALC] Row {idx}: Skipping - Train is None")
                    continue

                # Normalize train to string
                train = str(int(train)) if isinstance(train, (int, float)) else str(train)

                duration = record.get(duration_col, 0)

                # Fix: if duration is datetime, compute from End_Time - Start_Time
                if isinstance(duration, datetime):
                    start_time = record.get(found_columns.get("Start_Time"))
                    end_time = record.get(found_columns.get("End_Time"))
                    if start_time and end_time and isinstance(start_time, datetime) and isinstance(end_time, datetime):
                        duration = (end_time - start_time).total_seconds() / 3600.0
                        if idx < 3:  # Log first few calculations
                            logger.debug(
                                f"[RUNTIME][CALC] Row {idx}: Calculated duration from timestamps: "
                                f"{duration:.2f} hours"
                            )
                    else:
                        duration = 0
                        logger.debug(f"[RUNTIME][CALC] Row {idx}: Invalid timestamps, duration set to 0")

                # Normalize to float hours
                duration_hours = float(duration) if duration else 0
                if duration_unit == "days":
                    duration_hours *= 24
                    if idx < 3:  # Log first few conversions
                        logger.debug(
                            f"[RUNTIME][CALC] Row {idx}: Converted days to hours: "
                            f"{duration} days -> {duration_hours:.2f} hours"
                        )

                if train not in rack_durations:
                    rack_durations[train] = []
                    logger.debug(f"[RUNTIME][CALC] Created new entry for train: {train}")

                rack_durations[train].append(duration_hours)
                processed_count += 1

            logger.info(
                f"[RUNTIME][CALC] Calculation complete - "
                f"Processed: {processed_count}, Skipped: {skipped_count}, "
                f"Unique trains: {len(rack_durations)}"
            )
            
            # Log summary statistics
            for train, durations in list(rack_durations.items())[:3]:  # First 3 trains
                total_hours = sum(durations)
                logger.debug(
                    f"[RUNTIME][CALC] Train {train}: {len(durations)} records, "
                    f"Total runtime: {total_hours:.2f} hours"
                )

            return rack_durations

        except Exception as e:
            logger.error(f"Error calculating runtime percentages: {e}")
            return None

    def _format_runtime_result_clickhouse(
            self, rack_durations: Dict, data: List[Dict], found_columns: Dict, date_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Format runtime result into chart-compatible structure.
        Now includes Duration_Hours, End_Time, and date metadata in the response.

        Args:
            rack_durations: Dictionary of train IDs to duration lists
            data: Original data rows
            found_columns: Mapping of column names
            date_metadata: Dictionary with to_date, from_date, and data_availability_for_given_date

        Returns:
            Formatted dictionary for chart rendering with additional data and metadata

        Raises:
            ClickHouseServiceError: If formatting fails
        """
        try:
            if not rack_durations:
                return self._empty_runtime_response(date_metadata)

            # Calculate total observation period
            start_times = [r.get(found_columns.get("Start_Time")) for r in data if
                           r.get(found_columns.get("Start_Time"))]
            end_times = [r.get(found_columns.get("End_Time")) for r in data if r.get(found_columns.get("End_Time"))]

            total_period_hours = 24
            if start_times and end_times:
                overall_start = min(start_times)
                overall_end = max(end_times)
                if isinstance(overall_start, datetime) and isinstance(overall_end, datetime):
                    total_period_hours = (overall_end - overall_start).total_seconds() / 3600.0

            rack_data = []
            runtime_percentages = []
            stoptime_percentages = []
            duration_hours_data = []
            end_times_data = []

            # Get column names
            duration_col = found_columns.get("Duration_Hours") or found_columns.get("Duration_Days")
            end_time_col = found_columns.get("End_Time")
            train_col = found_columns.get("Train")

            # Debug logging
            logger.debug(
                f"[RUNTIME][FORMAT] Column mapping - "
                f"Duration: {duration_col}, End_Time: {end_time_col}, Train: {train_col}"
            )
            logger.info(f"[RUNTIME][FORMAT] Processing {len(rack_durations)} trains for formatting")

            for train, durations in rack_durations.items():
                total_runtime_hours = sum(durations)
                runtime_percentage = (total_runtime_hours / total_period_hours) * 100 if total_period_hours > 0 else 0
                runtime_percentage = min(runtime_percentage, 100.0)
                stoptime_percentage = 100.0 - runtime_percentage

                rack_data.append(str(train))
                runtime_percentages.append(f"{runtime_percentage:.2f}")
                stoptime_percentages.append(f"{stoptime_percentage:.2f}")
                duration_hours_data.append(f"{total_runtime_hours:.2f}")

                # Get the latest End_Time for this train
                train_end_times = []
                if end_time_col and train_col:
                    for r in data:
                        row_train = r.get(train_col)
                        if row_train is not None:
                            row_train_normalized = str(int(row_train)) if isinstance(row_train, (int, float)) else str(
                                row_train)
                            if row_train_normalized == train:
                                row_end_time = r.get(end_time_col)
                                if row_end_time:
                                    train_end_times.append(row_end_time)

                    logger.debug(f"[RUNTIME] Train {train}: found {len(train_end_times)} end times")
                else:
                    logger.warning(f"[RUNTIME] Missing columns - end_time_col: {end_time_col}, train_col: {train_col}")

                if train_end_times:
                    latest_end_time = max(train_end_times)
                    if isinstance(latest_end_time, datetime):
                        end_times_data.append(latest_end_time.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        end_times_data.append(str(latest_end_time))
                else:
                    end_times_data.append(None)

            # Safe sorting with proper type handling
            def sort_key(item):
                """
                Safe sorting key that handles both numeric and string train IDs.
                Returns a tuple (is_numeric, numeric_value or string_value) for proper sorting.
                """
                train_id = item[0]
                try:
                    return (0, int(str(train_id).strip()))
                except (ValueError, TypeError):
                    return (1, str(train_id).strip().lower())

            # Sort results by rack number with safe comparison
            try:
                sorted_data = sorted(
                    zip(
                        rack_data,
                        runtime_percentages,
                        stoptime_percentages,
                        duration_hours_data,
                        end_times_data
                    ),
                    key=sort_key
                )

                if sorted_data:
                    rack_data, runtime_percentages, stoptime_percentages, duration_hours_data, end_times_data = zip(
                        *sorted_data)
                    rack_data = list(rack_data)
                    runtime_percentages = list(runtime_percentages)
                    stoptime_percentages = list(stoptime_percentages)
                    duration_hours_data = list(duration_hours_data)
                    end_times_data = list(end_times_data)

            except Exception as sort_error:
                logger.warning(f"[RUNTIME] Sorting failed: {sort_error}. Returning unsorted data.")

            # Build response with runtime data
            response = {
                "rackruntimestoptime": {
                    "G1": {
                        "x": [{"name": "Racks", "data": rack_data}],
                        "y": [
                            {"name": "Runtime %", "data": runtime_percentages},
                            {"name": "Stoptime %", "data": stoptime_percentages},
                            {"name": "Duration Hours", "data": duration_hours_data},
                            {"name": "End_Time", "data": end_times_data}
                        ]
                    }
                }
            }

            # Add date metadata if provided
            if date_metadata:
                response["to_date"] = date_metadata.get("to_date")
                response["from_date"] = date_metadata.get("from_date")
                response["data_availability_for_given_date"] = date_metadata.get("data_availability_for_given_date", True)

            return response

        except Exception as e:
            logger.error(f"Error formatting runtime result: {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to format runtime result: {str(e)}"
            ) from e