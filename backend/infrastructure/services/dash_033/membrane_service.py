"""
Membrane Service for Dashboard-033
Handles membrane-related operations with improved rack filtering.
FIXED: Column ordering issue resolved with auto-detection and logging.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base_service import Dash033BaseService
from infrastructure.exceptions import ClickHouseServiceError
from constants import Dash033Config
import math

logger = logging.getLogger(__name__)


class MembraneService(Dash033BaseService):
    
    def _safe_zip_with_column_check(
        self, 
        columns: List[str], 
        row: tuple, 
        context: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Safely zip columns with row data, auto-detecting and handling column mismatches.
        
        Args:
            columns: Expected column names
            row: Row data tuple
            context: Context string for logging (e.g., "membrane_avg", "membrane_info")
            
        Returns:
            Dictionary with columns mapped to row values
            
        Raises:
            ClickHouseServiceError: If column mismatch cannot be auto-resolved
        """
        actual_count = len(row)
        expected_count = len(columns)
        
        # Perfect match - no issues
        if actual_count == expected_count:
            return dict(zip(columns, row))
        
        # Mismatch detected - try to auto-fix
        logger.warning(
            f"[MEMBRANE][{context.upper()}] Column mismatch detected! "
            f"Actual: {actual_count}, Expected: {expected_count}"
        )
        
        # Check if there's exactly one extra column and it's a datetime at position 0
        if actual_count == expected_count + 1:
            if isinstance(row[0], datetime):
                logger.warning(
                    f"[MEMBRANE][{context.upper()}] Auto-fix: Detected extra datetime at position 0, "
                    f"adding 'datetime_index' column"
                )
                adjusted_columns = ['datetime_index'] + columns
                return dict(zip(adjusted_columns, row))
        
        # Cannot auto-fix - raise error with details
        logger.error(
            f"[MEMBRANE][{context.upper()}] COLUMN MISMATCH - cannot auto-fix!"
        )
        logger.error(f"[MEMBRANE][{context.upper()}] Expected columns ({expected_count}): {columns}")
        logger.error(f"[MEMBRANE][{context.upper()}] Got row values ({actual_count}): {row}")
        
        raise ClickHouseServiceError(
            f"Column count mismatch in {context}: expected {expected_count}, got {actual_count}"
        )
    
    def _build_membrane_where_conditions(
        self,
        clickhouse_table: str,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None,
        modes: Optional[List[str]] = None
    ) -> tuple:
        """
        Build where conditions and query params for membrane table queries.
        Returns tuple of (where_conditions, query_params).
        """
        where_conditions = []
        query_params = {}

        # Get available columns
        columns = self.repository.get_table_columns(clickhouse_table)
        available_columns = [col["name"] for col in columns]

        # Date filtering
        if "Start_Time" in available_columns and "End_Time" in available_columns:
            if start_time and end_time:
                self._validate_column_names(["Start_Time", "End_Time"], "membrane info date filtering")
                where_conditions.append(
                    f"(`Start_Time` >= {{start_date:DateTime}} AND `End_Time` <= {{end_date:DateTime}})"
                )
                query_params["start_date"] = start_time
                query_params["end_date"] = end_time

        # Rack filtering using repository method
        if racks:
            rack_column = self.repository.get_rack_trailer_column(clickhouse_table)
            if rack_column:
                self._validate_column_names([rack_column], "membrane info rack filtering")
                rack_params = []
                for i, rack in enumerate(racks):
                    param_name = f"rack_{i}"
                    rack_params.append(f"{{{param_name}:String}}")
                    query_params[param_name] = str(rack)
                where_conditions.append(f"`{rack_column}` IN ({', '.join(rack_params)})")
                logger.debug(f"[MEMBRANE] Applying rack filter on column '{rack_column}' with values: {racks}")
            else:
                logger.warning("[MEMBRANE] Could not apply rack filter - no train column found")

        # Mode filtering
        if modes:
            mode_column = None
            mode_candidates = Dash033Config.COLUMN_MAPPINGS.get("Mode_Validated", [])
            for candidate in mode_candidates:
                if candidate in available_columns:
                    mode_column = candidate
                    break

            if mode_column:
                self._validate_column_names([mode_column], "membrane info mode filtering")
                mode_params = []
                for i, mode in enumerate(modes):
                    param_name = f"mode_{i}"
                    mode_params.append(f"{{{param_name}:String}}")
                    query_params[param_name] = str(mode)
                where_conditions.append(f"`{mode_column}` IN ({', '.join(mode_params)})")
                logger.debug(f"[MEMBRANE] Applying mode filter on column '{mode_column}' with values: {modes}")

        return where_conditions, query_params

    def get_membrane_graph_averages(
        self,
        site_name: str = None,
        user: dict = None,
        col_pre: str = "AVG_Salt_Passage_Normalized_Pre",
        col_post: str = "AVG_Salt_Passage_Normalized_Post",
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        """
        Get membrane graph averages using ClickHouse.
        Replicates the Spark logic: averages + percentages + rack/date filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)

            site_name = self._normalize_site_name(site_name)
            table_prefix = self.site_table_suffix_mappings(site_name)
            table_suffix = f"{table_prefix}_mode_maintenance"
            clickhouse_table = self.repository.get_clickhouse_table_name(site_name, table_suffix)
            
            if not clickhouse_table:
                logger.error(f"No ClickHouse table found for site {site_name} with suffix {table_suffix}")
                raise ClickHouseServiceError(
                    f"No ClickHouse table found for site {site_name} with suffix {table_suffix}",
                    context={"site_name": site_name, "table_suffix": table_suffix}
                )

            # Get available columns
            columns = self.repository.get_table_columns(clickhouse_table)
            available_columns = [c["name"] for c in columns]
            logger.debug(f"[MEMBRANE_AVG] Available columns in {clickhouse_table}: {available_columns}")

            # Find Train column using repository method
            train_column = self.repository.get_rack_trailer_column(clickhouse_table)

            if not train_column:
                result_dict = self.repository.get_column_data_for_table(
                    clickhouse_table_name=clickhouse_table,
                    column_names=available_columns,
                    where_conditions=[],
                    query_params={},
                    limit=3
                )
                # Extract result_rows from Dict response
                sample_rows = result_dict.get("result_rows", [])
                return {
                    "diagnostic_info": {
                        "available_columns": available_columns,
                        "sample_data": [self._safe_zip_with_column_check(available_columns, r, "diagnostic") for r in sample_rows],
                        "message": "No Train column found"
                    }
                }

            # Check if required metric columns exist
            if col_pre not in available_columns or col_post not in available_columns:
                return {
                    "diagnostic_info": {
                        "available_columns": available_columns,
                        "message": f"Required columns {col_pre} or {col_post} not found"
                    }
                }

            # Run calculation
            result = self._calculate_train_metric_ch(
                clickhouse_table, train_column, col_pre, col_post,
                available_columns, start_time=start_time, end_time=end_time, racks=racks
            )

            if not result:
                logger.info(f"No membrane graph averages data found for site {site_name} with racks filter: {racks}")
                return self._empty_membrane_graph_response()

            return self._format_membrane_result_ch(result, col_pre, col_post)

        except ClickHouseServiceError:
            raise
        except Exception as e:
            logger.error(f"Error in get_membrane_graph_averages (ClickHouse): {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to retrieve membrane graph averages: {str(e)}"
            ) from e

    def _empty_membrane_graph_response(self) -> Dict[str, Any]:
        """Return empty membrane graph response structure."""
        return {
            "rackmembrance": {
                "G1": {
                    "x": [{"name": "Train", "data": []}],
                    "y": []
                }
            }
        }

    def _calculate_train_metric_ch(
        self,
        table_name: str,
        train_col: str,
        col_pre: str,
        col_post: str,
        available_columns: List[str],
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        """
        Calculate train metrics using ClickHouse repository methods.
        Returns aggregated data with averages and percentages per Train.
        """
        try:
            # Build where conditions
            where_conditions = []
            query_params = {}

            # Date filter
            if "Start_Time" in available_columns and "End_Time" in available_columns:
                if start_time and end_time:
                    self._validate_column_names(["Start_Time", "End_Time"], "membrane averages date filtering")
                    where_conditions.append(
                        f"(`Start_Time` >= {{start_date:DateTime}} AND `End_Time` <= {{end_date:DateTime}})"
                    )
                    query_params["start_date"] = start_time
                    query_params["end_date"] = end_time

            # Rack filter
            if racks:
                self._validate_column_names([train_col], "membrane averages rack filtering")
                rack_params = []
                for i, rack in enumerate(racks):
                    param_name = f"rack_{i}"
                    rack_params.append(f"{{{param_name}:String}}")
                    query_params[param_name] = str(rack)
                where_conditions.append(f"`{train_col}` IN ({', '.join(rack_params)})")
                logger.debug(f"[MEMBRANE_AVG] Applying rack filter on column '{train_col}' with values: {racks}")

            # Get all raw data first
            required_columns = [train_col, col_pre, col_post]
            self._validate_column_names(required_columns, "membrane averages metric columns")

            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=table_name,
                column_names=required_columns,
                where_conditions=where_conditions,
                query_params=query_params,
                limit=Dash033Config.MAX_AGGREGATION_ROWS
            )
            # Extract result_rows from Dict response
            all_rows = result_dict.get("result_rows", [])

            if not all_rows:
                logger.warning("[MEMBRANE_AVG] No data returned from ClickHouse")
                return []

            # Check first row for column count mismatch
            if all_rows:
                first_row = all_rows[0]
                logger.debug(
                    f"[MEMBRANE][AVG][CALC] First row length: {len(first_row)}, "
                    f"Expected columns: {len(required_columns)}"
                )
                logger.debug(f"[MEMBRANE][AVG][CALC] First row sample: {first_row[:min(3, len(first_row))]}")
                logger.debug(f"[MEMBRANE][AVG][CALC] Expected columns: {required_columns}")

            # Convert to dict format with safe zipping
            dict_rows = []
            for idx, row in enumerate(all_rows):
                try:
                    row_dict = self._safe_zip_with_column_check(required_columns, row, "membrane_avg_calc")
                    dict_rows.append(row_dict)
                    
                    if idx < 3:
                        logger.debug(
                            f"[MEMBRANE][AVG][CALC] Row {idx} mapped successfully - "
                            f"Keys: {list(row_dict.keys())}"
                        )
                except Exception as e:
                    logger.error(
                        f"[MEMBRANE][AVG][CALC] Error mapping row {idx}: {e}. "
                        f"Row length: {len(row)}, Columns length: {len(required_columns)}"
                    )
                    raise
            
            logger.info(f"[MEMBRANE][AVG][CALC] Successfully mapped {len(dict_rows)} rows")
            
            # Group by train and calculate averages
            train_groups = {}
            for row in dict_rows:
                train = row.get(train_col)
                if train is None:
                    continue
                    
                # Normalize train to string
                train = str(int(train)) if isinstance(train, (int, float)) else str(train)
                
                if train not in train_groups:
                    train_groups[train] = {
                        "pre_values": [],
                        "post_values": []
                    }
                
                pre_val = row.get(col_pre)
                post_val = row.get(col_post)
                
                # Only add numeric values
                if isinstance(pre_val, (int, float)) and pre_val is not None:
                    train_groups[train]["pre_values"].append(float(pre_val))
                if isinstance(post_val, (int, float)) and post_val is not None:
                    train_groups[train]["post_values"].append(float(post_val))

            # Calculate averages and percentages
            result = []
            for train in sorted(train_groups.keys()):
                data = train_groups[train]
                
                # Calculate averages
                avg_pre = sum(data["pre_values"]) / len(data["pre_values"]) if data["pre_values"] else 0
                avg_post = sum(data["post_values"]) / len(data["post_values"]) if data["post_values"] else 0
                
                # Calculate percentages
                total = avg_pre + avg_post
                if total > 0:
                    percentage_pre = (avg_pre / total) * 100
                    percentage_post = (avg_post / total) * 100
                else:
                    percentage_pre = 0
                    percentage_post = 0
                
                result.append({
                    "Train": train,
                    f"Avg_{col_pre}": avg_pre,
                    f"Avg_{col_post}": avg_post,
                    "Percentage_Pre": percentage_pre,
                    "Percentage_Post": percentage_post
                })

            logger.debug(f"[MEMBRANE_AVG] Processed {len(result)} trains with averages")
            return result

        except Exception as e:
            logger.error(f"Error in _calculate_train_metric_ch: {e}")
            return []

    def get_membrane_info(
            self,
            site_name: str = None,
            user: dict = None,
            page: int = 1,
            limit: int = 25,
            start_time: str = None,
            end_time: str = None,
            racks: Optional[List[str]] = None,
            modes: Optional[List[str]] = None
    ):
        """
        Get membrane info using ClickHouse with database-level pagination.
        Combines data from multiple tables (_mode_maintenance and _mode_cip).
        Uses database COUNT and LIMIT/OFFSET for memory efficiency.
        Supports fallback to last 7 days when no data found for specified date range.
        """
        try:
            # Validate pagination parameters
            if limit <= 0:
                raise ValueError("Limit must be a positive integer")
            if page <= 0:
                raise ValueError("Page must be a positive integer")

            if not site_name:
                site_name = self.get_defaults(user)

            site_name = self._normalize_site_name(site_name)
            table_prefix = self.site_table_suffix_mappings(site_name)

            # Validate that we have a valid table prefix
            if not table_prefix:
                logger.error(f"No table prefix found for site {site_name}")
                raise ClickHouseServiceError(
                    f"No table configuration found for site {site_name}",
                    context={"site_name": site_name}
                )

            table_suffixes = [f"{table_prefix}_mode_maintenance", f"{table_prefix}_mode_cip"]

            logger.debug(f"Getting membrane info for {site_name} with racks filter: {racks}, modes filter: {modes}")

            # Collect total counts from all tables
            total_count = 0
            table_counts = []

            for table_suffix in table_suffixes:
                clickhouse_table = self.repository.get_clickhouse_table_name(site_name, table_suffix)
                if not clickhouse_table:
                    logger.warning(f"No ClickHouse table found for site {site_name} with suffix {table_suffix}")
                    # Don't skip - add to table_counts with count 0 so fallback can work
                    table_counts.append({
                        "table": None,
                        "suffix": table_suffix,
                        "count": 0,
                        "skipped": True  # Mark as skipped so we don't try to query it later
                    })
                    continue

                # Build where conditions for this table
                where_conditions, query_params = self._build_membrane_where_conditions(
                    clickhouse_table, start_time, end_time, racks, modes
                )

                # Get count from database
                count = self.repository.get_count_for_table(
                    clickhouse_table_name=clickhouse_table,
                    where_conditions=where_conditions,
                    query_params=query_params
                )

                table_counts.append({"table": clickhouse_table, "suffix": table_suffix, "count": count})
                total_count += count

            # Calculate pagination even if count is 0 (to allow fallback mechanism)
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

            # Adjust page if it exceeds available pages
            if page > total_pages and total_count > 0:
                logger.warning(f"Requested page {page} exceeds total pages {total_pages}, returning last page")
                page = total_pages

            offset = (page - 1) * limit

            # Fetch paginated data from tables
            # Note: Even if total_count is 0, we still proceed to allow fallback mechanism
            all_data = []
            remaining_offset = offset
            remaining_limit = limit
            all_metadata = []  # Store metadata from all tables to determine overall status

            for table_info in table_counts:
                if remaining_limit <= 0:
                    break

                # Skip tables that were marked as not found
                if table_info.get("skipped"):
                    logger.debug(f"Skipping table {table_info['suffix']} - not found in database")
                    continue

                # Build where conditions for this table
                clickhouse_table = table_info["table"]
                where_conditions, query_params = self._build_membrane_where_conditions(
                    clickhouse_table, start_time, end_time, racks, modes
                )

                columns = self.repository.get_table_columns(clickhouse_table)
                available_columns = [col["name"] for col in columns]

                # If count was 0, we still call get_column_data_for_table
                # This allows the fallback mechanism to trigger and fetch last 7 days of data
                if table_info["count"] == 0:
                    logger.info(
                        f"[MEMBRANE][INFO] Count is 0 for {clickhouse_table}, "
                        f"calling get_column_data_for_table to trigger fallback"
                    )
                    
                result_dict = self.repository.get_column_data_for_table(
                    clickhouse_table_name=clickhouse_table,
                    column_names=available_columns,
                    where_conditions=where_conditions,
                    query_params=query_params,
                    limit=remaining_limit if table_info["count"] > 0 else remaining_limit,
                    offset=remaining_offset if table_info["count"] > 0 else 0
                )

                # Capture metadata
                if result_dict.get('data_availability_for_given_date') is not None:
                    all_metadata.append({
                        'table': table_info['suffix'],
                        'data_availability_for_given_date': result_dict.get('data_availability_for_given_date'),
                        'from_date': result_dict.get('from_date'),
                        'to_date': result_dict.get('to_date'),
                        'row_count': len(result_dict.get("result_rows", []))
                    })

                # Extract result_rows from Dict response
                result_rows = result_dict.get("result_rows", [])
                logger.info(
                    f"[MEMBRANE][INFO] Retrieved {len(result_rows)} rows from {table_info['suffix']}"
                )

                if result_rows:
                    first_row = result_rows[0]
                    logger.debug(
                        f"[MEMBRANE][INFO] First row length: {len(first_row)}, "
                        f"Expected columns: {len(available_columns)}"
                    )
                    logger.debug(
                        f"[MEMBRANE][INFO] First row sample: {first_row[:min(3, len(first_row))]}"
                    )

                # Convert to dicts and add source table info
                for idx, row in enumerate(result_rows):
                    try:
                        row_dict = self._safe_zip_with_column_check(
                            available_columns, row, f"membrane_info_{table_info['suffix']}"
                        )
                        row_dict["source_table"] = table_info["suffix"]
                        all_data.append(row_dict)
                        
                        if idx < 3:
                            logger.debug(
                                f"[MEMBRANE][INFO] Row {idx} from {table_info['suffix']} mapped successfully"
                            )
                    except Exception as e:
                        logger.error(
                            f"[MEMBRANE][INFO] Error mapping row {idx} from {table_info['suffix']}: {e}"
                        )
                        raise

                # Update counters
                fetched_count = len(result_rows)
                remaining_limit -= fetched_count

                if table_info["count"] > 0:
                    if remaining_offset < table_info["count"]:
                        remaining_offset = 0
                    else:
                        remaining_offset -= table_info["count"]

            logger.info(f"[MEMBRANE][INFO] Total data retrieved: {len(all_data)} rows")

            # If we got data through fallback, recalculate pagination based on actual data
            if total_count == 0 and len(all_data) > 0:
                logger.info(f"Fallback mechanism retrieved {len(all_data)} records")
                # Update pagination info based on actual fetched data
                total_count = len(all_data)
                total_pages = 1  # Since we fetched with fallback, it's effectively one page

            # Format result with all available columns
            formatted_data = self._format_membrane_data_ch(all_data)

            logger.info(
                f"Retrieved {len(all_data)} membrane info items (page {page}/{total_pages}, total: {total_count})")

            # Determine overall metadata based on all tables
            fallback_metadata = self._determine_overall_metadata(all_metadata)

            # Build response
            response = {
                "items": formatted_data,
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "source_tables": table_suffixes,
                "merged_from": len(table_suffixes),
                "fallback_used": total_count == 0 and len(all_data) > 0  # Indicate if fallback was triggered
            }

            # Add fallback metadata if available
            if fallback_metadata:
                response.update(fallback_metadata)
                logger.info(f"Including overall metadata in response: {fallback_metadata}")

            return response

        except ClickHouseServiceError:
            raise
        except Exception as e:
            logger.error(f"Error in get_membrane_info (ClickHouse): {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to retrieve membrane info: {str(e)}"
            ) from e

    def _determine_overall_metadata(self, all_metadata: List[Dict]) -> Dict[str, Any]:
        """
        Determine overall metadata from multiple tables.

        Logic:
        - If ANY table has data_availability_for_given_date=True, overall is True
        - Use the widest date range (earliest from_date, latest to_date)
        - Include details about each table's contribution
        """
        if not all_metadata:
            return {}

        # Check if any table has data available for given date
        any_data_available = any(m.get('data_availability_for_given_date') for m in all_metadata)

        # Find the widest date range
        from_dates = [m.get('from_date') for m in all_metadata if m.get('from_date')]
        to_dates = [m.get('to_date') for m in all_metadata if m.get('to_date')]

        overall_from_date = min(from_dates) if from_dates else None
        overall_to_date = max(to_dates) if to_dates else None

        metadata = {
            'data_availability_for_given_date': any_data_available,
            'from_date': overall_from_date,
            'to_date': overall_to_date,
        }

        logger.debug(f"Overall metadata determined: {metadata}")
        return metadata

    def _format_membrane_data_ch(self, data: List[Dict]) -> Dict:
        """
        Format membrane data into columnar structure.
        Works with any data structure and detects numeric vs text columns.
        """
        try:
            if not data:
                return {}
            
            formatted = {}
            
            # Get all unique columns from the data
            all_columns = set()
            for row in data:
                all_columns.update(row.keys())
            
            # Exclude Mode and source_table columns from the response (case-insensitive)
            excluded_columns_lower = {'mode', 'source_table'}
            filtered_columns = [
                col for col in sorted(all_columns) 
                if col.lower() not in excluded_columns_lower
            ]
            
            # Process each column
            for col in filtered_columns:
                col_data = []
                
                for row in data:
                    value = row.get(col)
                    
                    # Handle different data types
                    if value is None:
                        col_data.append(None)
                    elif col.lower() in ['train', 'train_id', 'unit', 'rack']:
                        # Train identifiers should be integers
                        if isinstance(value, (int, float)):
                            col_data.append(int(float(value)))
                        else:
                            # Try to convert to int, fallback to string
                            try:
                                col_data.append(int(float(str(value))))
                            except (ValueError, TypeError):
                                col_data.append(str(value))
                    elif isinstance(value, datetime):
                        # Format datetime as string
                        col_data.append(value.strftime("%Y-%m-%d %H:%M:%S"))
                    elif isinstance(value, (int, float)):
                        # Numeric data - format to 2 decimal places as string
                        formatted_value = f"{float(value):.2f}"
                        # Strip trailing zeros and decimal point if whole number
                        col_data.append(formatted_value.rstrip('0').rstrip('.') if '.' in formatted_value else str(int(value)))
                    else:
                        # Other data - convert to string
                        col_data.append(str(value))
                
                # Standardize train column name
                if col.lower() in ['train', 'train_id', 'unit', 'rack']:
                    formatted["Train"] = {
                        "name": "Train",
                        "data": col_data
                    }
                else:
                    formatted[col] = {
                        "name": col,
                        "data": col_data
                    }
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error in membrane data formatting: {e}")
            raise ClickHouseServiceError(
                f"Failed to format membrane data: {str(e)}"
            ) from e

    def get_membrane_percentages_graph(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ):
        """
        Get membrane graph percentages using ClickHouse with proper calculation logic and rack filtering.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)

            site_name = self._normalize_site_name(site_name)
            table_prefix = self.site_table_suffix_mappings(site_name)
            table_suffix = f"{table_prefix}_mode_maintenance"
            clickhouse_table = self.repository.get_clickhouse_table_name(site_name, table_suffix)
            
            if not clickhouse_table:
                logger.error(
                    f"[MEMBRANE][PCT] No ClickHouse table found for "
                    f"site {site_name} with suffix {table_suffix}"
                )
                raise ClickHouseServiceError(
                    f"No ClickHouse table found for site {site_name} with suffix {table_suffix}"
                )

            logger.info(f"[MEMBRANE][PCT] Using ClickHouse table: {clickhouse_table}")

            # Get result
            result_data = self._get_membrane_percentage_data_ch(
                clickhouse_table, start_time, end_time, racks
            )

            if not result_data:
                logger.info(
                    f"[MEMBRANE][PCT] No percentage data found for site {site_name} with racks filter: {racks}"
                )
                return self._empty_membrane_percentage_response()

            # Get column mappings
            columns = self.repository.get_table_columns(clickhouse_table)
            available_columns = [col["name"] for col in columns]
            found_columns = self._find_membrane_columns(available_columns)

            logger.info(f"[MEMBRANE][PCT] Formatting data for {len(result_data)} trains")
            return self._format_membrane_percentage_result_ch(result_data, found_columns)

        except ClickHouseServiceError:
            raise
        except Exception as e:
            logger.error(f"Error in get_membrane_graph_percentages (ClickHouse): {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to retrieve membrane graph percentages: {str(e)}"
            ) from e

    def _empty_membrane_percentage_response(self) -> Dict[str, Any]:
        """Return empty membrane percentage response structure."""
        return {
            "rackmembrance": {
                "G1": {
                    "x": [{"name": "Train", "data": []}],
                    "y": []
                }
            }
        }

    def _find_membrane_columns(self, available_columns: List[str]) -> Dict[str, str]:
        """
        Find required membrane columns using flexible matching.
        """
        logger.debug(f"[MEMBRANE] Finding columns from: {available_columns}")
        
        column_mappings = Dash033Config.COLUMN_MAPPINGS
        found_columns = {}

        for standard_name in ["Train", "Diff_Salt_Passage_%", "Diff_Norm_DP_%", "Diff_Norm_Perm_Flow_%"]:
            possible_names = column_mappings.get(standard_name, [])
            for possible_name in possible_names:
                if possible_name in available_columns:
                    found_columns[standard_name] = possible_name
                    logger.debug(f"[MEMBRANE] Mapped {standard_name} -> {possible_name}")
                    break

        logger.info(f"[MEMBRANE] Found {len(found_columns)} column mappings")
        return found_columns

    def _get_membrane_percentage_data_ch(
        self,
        clickhouse_table: str,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get membrane percentage data from ClickHouse and calculate train metrics.
        """
        try:
            logger.info(f"[MEMBRANE][PCT][DATA] Fetching percentage data from {clickhouse_table}")
            
            # Get available columns
            columns = self.repository.get_table_columns(clickhouse_table)
            available_columns = [col["name"] for col in columns]
            logger.info(f"[MEMBRANE][PCT][DATA] Available columns: {available_columns}")

            # Find required columns
            found_columns = self._find_membrane_columns(available_columns)

            if not found_columns.get("Train"):
                logger.warning("[MEMBRANE][PCT][DATA] No Train column found")
                return []

            # Build where conditions
            where_conditions = []
            query_params = {}

            # Date filtering
            if "Start_Time" in available_columns and "End_Time" in available_columns:
                if start_time and end_time:
                    self._validate_column_names(["Start_Time", "End_Time"], "membrane percentages date filtering")
                    where_conditions.append(
                        f"(`Start_Time` >= {{start_date:DateTime}} AND `End_Time` <= {{end_date:DateTime}})"
                    )
                    query_params["start_date"] = start_time
                    query_params["end_date"] = end_time
                    logger.debug(
                        f"[MEMBRANE][PCT][DATA] Applied date filter: {start_time} to {end_time}"
                    )

            # Rack filtering
            if racks and found_columns.get("Train"):
                train_col = found_columns["Train"]
                self._validate_column_names([train_col], "membrane percentages rack filtering")
                rack_params = []
                for i, rack in enumerate(racks):
                    param_name = f"rack_{i}"
                    rack_params.append(f"{{{param_name}:String}}")
                    query_params[param_name] = str(rack)
                where_conditions.append(f"`{train_col}` IN ({', '.join(rack_params)})")
                logger.debug(f"[MEMBRANE_PCT] Applying rack filter on column '{train_col}' with values: {racks}")

            # Get required columns for calculation
            required_columns = [found_columns["Train"]]
            percentage_columns = []

            for col_name in ["Diff_Salt_Passage_%", "Diff_Norm_DP_%", "Diff_Norm_Perm_Flow_%"]:
                if found_columns.get(col_name):
                    required_columns.append(found_columns[col_name])
                    percentage_columns.append(col_name)

            if not percentage_columns:
                logger.warning("[MEMBRANE_PCT] No percentage columns found")
                return []

            self._validate_column_names(required_columns, "membrane percentages metric columns")

            # Get raw data from ClickHouse
            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=clickhouse_table,
                column_names=required_columns,
                where_conditions=where_conditions,
                query_params=query_params,
                limit=Dash033Config.MAX_AGGREGATION_ROWS
            )
            # Extract result_rows from Dict response
            all_rows = result_dict.get("result_rows", [])

            if not all_rows:
                logger.warning("[MEMBRANE_PCT] No data returned from ClickHouse")
                return []

            logger.info(f"[MEMBRANE][PCT][DATA] Retrieved {len(all_rows)} rows")

            if all_rows:
                first_row = all_rows[0]
                logger.debug(
                    f"[MEMBRANE][PCT][DATA] First row length: {len(first_row)}, "
                    f"Expected columns: {len(required_columns)}"
                )
                logger.debug(f"[MEMBRANE][PCT][DATA] First row sample: {first_row[:min(3, len(first_row))]}")

            # Convert to dictionaries with safe zipping
            dict_rows = []
            for idx, row in enumerate(all_rows):
                try:
                    row_dict = self._safe_zip_with_column_check(
                        required_columns, row, "membrane_pct_data"
                    )
                    dict_rows.append(row_dict)
                    
                    if idx < 3:
                        logger.debug(
                            f"[MEMBRANE][PCT][DATA] Row {idx} mapped successfully - "
                            f"Keys: {list(row_dict.keys())}"
                        )
                except Exception as e:
                    logger.error(
                        f"[MEMBRANE][PCT][DATA] Error mapping row {idx}: {e}. "
                        f"Row length: {len(row)}, Columns length: {len(required_columns)}"
                    )
                    raise

            logger.info(f"[MEMBRANE][PCT][DATA] Successfully mapped {len(dict_rows)} rows")

            # Group by train and calculate averages
            train_groups = {}
            train_col = found_columns["Train"]

            for row in dict_rows:
                train = row.get(train_col)
                if train is None:
                    continue

                # Normalize train to string
                train = str(int(train)) if isinstance(train, (int, float)) else str(train)

                if train not in train_groups:
                    train_groups[train] = {}
                    for pct_col in percentage_columns:
                        train_groups[train][pct_col] = []

                # Collect values for each percentage column
                for pct_col in percentage_columns:
                    actual_col = found_columns[pct_col]
                    value = row.get(actual_col)
                    if isinstance(value, (int, float)) and value is not None:
                        train_groups[train][pct_col].append(float(value))

            # Calculate averages for each train
            result = []
            for train in sorted(train_groups.keys(), key=lambda x: int(x) if x.isdigit() else x):
                train_data = {"Train": train}
                
                for pct_col in percentage_columns:
                    values = train_groups[train][pct_col]
                    if values:
                        avg_value = sum(values) / len(values)
                        train_data[f"Avg_{pct_col}"] = avg_value
                    else:
                        train_data[f"Avg_{pct_col}"] = None

                result.append(train_data)

            logger.debug(f"[MEMBRANE_PCT] Calculated averages for {len(result)} trains")
            return result

        except Exception as e:
            logger.error(f"Error getting membrane percentage data: {e}")
            return []

    def _format_membrane_percentage_result_ch(self, result_data: List[Dict], found_columns: Dict[str, str]) -> dict:
        """
        Format membrane percentage results matching the original format.
        """
        try:
            if not result_data:
                return self._empty_membrane_percentage_response()

            trains = [row["Train"] for row in result_data]
            y_data = []

            # Create y-axis data for each percentage column found
            percentage_columns = ["Diff_Salt_Passage_%", "Diff_Norm_DP_%", "Diff_Norm_Perm_Flow_%"]
            
            for col_name in percentage_columns:
                if found_columns.get(col_name):
                    values = []
                    avg_col = f"Avg_{col_name}"
                    
                    for row in result_data:
                        val = row.get(avg_col)
                        values.append(f"{val:.2f}" if val is not None else None)

                    y_data.append({
                        "name": col_name,
                        "data": values
                    })

            return {
                "rackmembrance": {
                    "G1": {
                        "x": [{"name": "Train", "data": trains}],
                        "y": y_data
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error formatting membrane percentage result: {e}")
            raise ClickHouseServiceError(
                f"Failed to format membrane percentage result: {str(e)}"
            ) from e

    def _format_membrane_result_ch(self, rows: List[dict], col_pre: str, col_post: str) -> dict:
        """
        Format membrane results to match original Spark output.
        """
        try:
            if not rows:
                return self._empty_membrane_graph_response()

            trains = [row["Train"] for row in rows]
            pre_values = []
            post_values = []
            pre_percentages = []
            post_percentages = []

            for row in rows:
                pre_val = row.get(f"Avg_{col_pre}")
                post_val = row.get(f"Avg_{col_post}")
                pre_pct = row.get("Percentage_Pre")
                post_pct = row.get("Percentage_Post")

                pre_values.append(f"{pre_val:.2f}" if pre_val is not None else "0.00")
                post_values.append(f"{post_val:.2f}" if post_val is not None else "0.00")
                pre_percentages.append(f"{pre_pct:.2f}" if pre_pct is not None else "0.00")
                post_percentages.append(f"{post_pct:.2f}" if post_pct is not None else "0.00")

            logger.debug(f"[MEMBRANE_AVG] Formatted result for {len(trains)} trains")
            
            return {
                "rackmembrance": {
                    "G1": {
                        "x": [{"name": "Train", "data": trains}],
                        "y": [
                            {
                                "name": col_pre,
                                "data": {
                                    "value": pre_values,
                                    "percentage": pre_percentages
                                }
                            },
                            {
                                "name": col_post,
                                "data": {
                                    "value": post_values,
                                    "percentage": post_percentages
                                }
                            }
                        ]
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error in _format_membrane_result_ch: {e}")
            raise ClickHouseServiceError(
                f"Failed to format membrane result: {str(e)}"
            ) from e