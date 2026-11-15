import logging
from http.client import responses
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base_service import Dash033BaseService
from infrastructure.exceptions import ClickHouseServiceError
from constants import Dash033Config
import math

logger = logging.getLogger(__name__)

class MetadataService(Dash033BaseService):

    def _handle_duplicate_datetime_columns(
        self, 
        rows: List[tuple], 
        expected_columns: List[str], 
        clickhouse_table: str
    ) -> List[tuple]:
        """
        Handle duplicate datetime columns in result rows from repository.
        
        The repository may return duplicate datetime columns when timezone conversion
        is applied. This method detects and removes the duplicate raw datetime column.
        
        Args:
            rows: List of result rows from repository
            expected_columns: List of expected column names (e.g., existing_columns)
            clickhouse_table: Table name for logging
        
        Returns:
            List of rows with duplicate columns removed
        
        Example:
            Expected columns: ['Train', 'AVG_DP_Pre', 'AVG_DP_Post']  (3 columns)
            Actual row:       (datetime_tz, train, dp_pre, dp_post)   (4 columns)
            Cleaned row:      (train, dp_pre, dp_post)                (3 columns)
        """
        if not rows:
            return rows
        
        # Get the datetime column from repository
        datetime_column = self.repository.get_datetime_column(clickhouse_table)
        
        # Check if we have a column count mismatch
        expected_count = len(expected_columns)
        actual_count = len(rows[0]) if rows else 0
        
        if actual_count == expected_count:
            # No mismatch, return as-is
            logger.debug(f"[METADATA] Column counts match: {actual_count} columns")
            return rows
        
        if actual_count != expected_count + 1:
            # Unexpected mismatch (not the duplicate datetime issue)
            logger.warning(
                f"[METADATA] Unexpected column count mismatch in {clickhouse_table}: "
                f"expected {expected_count}, got {actual_count}"
            )
            return rows
        
        # We have exactly one extra column - likely the duplicate datetime
        logger.info(
            f"[METADATA] Detected duplicate datetime column in {clickhouse_table}: "
            f"expected {expected_count}, got {actual_count}. "
            f"Datetime column '{datetime_column}' appears to be duplicated"
        )
        
        try:
            # The datetime column is added FIRST by the repository (index 0)
            # Then the regular columns follow
            # So we need to remove the first column (index 0)
            remove_index = 0
            
            logger.debug(
                f"[METADATA] Removing datetime column at index {remove_index} "
                f"('{datetime_column}' with timezone conversion)"
            )
            
            # Remove the datetime column from each row
            cleaned_rows = []
            for row in rows:
                # Convert to list, remove the datetime, convert back to tuple
                row_list = list(row)
                if remove_index < len(row_list):
                    row_list.pop(remove_index)
                cleaned_rows.append(tuple(row_list))
            
            logger.info(
                f"[METADATA] Successfully cleaned {len(cleaned_rows)} rows: "
                f"removed duplicate datetime column at index {remove_index}"
            )
            
            return cleaned_rows
            
        except (ValueError, IndexError) as e:
            logger.error(
                f"[METADATA] Error removing duplicate column: {e}. "
                f"Returning original rows"
            )
            return rows
    
    def get_columns_metadata(
            self,
            site_name: str = None,
            user: dict = None,
            from_date: Optional[str] = None,
            to_date: Optional[str] = None,
            include_samples: bool = True,
            exclude_calculated: bool = True,
            exclude_null: bool = True,
            include_performance: bool = False,
            racks: Optional[List[str]] = None  # Added racks parameter
        ):
            """
            Get column metadata for membrane maintenance data with chart groupings using ClickHouse.
            Returns data structured for G1, G2, G3 charts with specific column sets.
            Now supports rack filtering.
            """
            try:
                if not site_name:
                    site_name = self.get_defaults(user)

                site_name = self._normalize_site_name(site_name)

                table_prefix = self.site_table_suffix_mappings(site_name)

                # Map site name to table identifier (similar to original logic)
                table_suffix = f"{table_prefix}_mode_cip"
                clickhouse_table = self.repository.get_clickhouse_table_name(site_name, table_suffix)
                if not clickhouse_table:
                    logger.error(f"No ClickHouse table found for site {site_name} with suffix r3_mode_cip")
                    return self._empty_metadata_response(from_date, to_date)

                logger.debug(f"Getting columns metadata for {clickhouse_table} with racks filter: {racks}")
                start_time = datetime.now()

                # Define column groups for different charts
                chart_columns = {
                    "G1": [  # Perm Flow Norm Chart
                        "Train",
                        "AVG_Perm_Flow_Normalized_Pre",
                        "AVG_Perm_Flow_Normalized_Post",
                        "Diff_Norm_Perm_Flow_%"
                    ],
                    "G2": [  # Dp Flow Norm Chart
                        "Train",
                        "AVG_DP_Normalized_BAR_Pre",
                        "AVG_DP_Normalized_BAR_Post",
                        "Diff_DP_%"
                    ],
                    "G3": [  # Salt Passage Norm Chart
                        "Train",
                        "AVG_Salt_Passage_Normalized_Pre",
                        "AVG_Salt_Passage_Normalized_Post",
                        "Diff_Norm_Salt_Passage_%"
                    ]
                }

                # Get all available columns
                columns = self.repository.get_table_columns(clickhouse_table)
                available_columns = [c["name"] for c in columns]

                # Get all unique columns needed
                all_columns = set()
                for group_cols in chart_columns.values():
                    all_columns.update(group_cols)

                # Check which columns exist
                existing_columns = [col for col in all_columns if col in available_columns]
                
                if not existing_columns:
                    logger.warning(f"No required columns found in table {clickhouse_table}")
                    return self._empty_metadata_response(from_date, to_date)

                # Get sample data if requested
                sample_data = []
                total_rows = 0
                response_data = {}

                if include_samples:
                    # Build where conditions for date and rack filtering
                    where_conditions = []
                    query_params = {}

                    # Date filtering
                    if from_date and to_date:
                        if "Start_Time" in available_columns and "End_Time" in available_columns:
                            self._validate_column_names(["Start_Time", "End_Time"], "columns metadata date filtering")
                            where_conditions.append(
                                f"(`Start_Time` >= {{start_date:DateTime}} AND `End_Time` <= {{end_date:DateTime}})"
                            )
                            query_params["start_date"] = from_date
                            query_params["end_date"] = to_date

                    # Rack filtering - use repository method
                    if racks:
                        rack_column = self.repository.get_rack_trailer_column(clickhouse_table)
                        if rack_column:
                            self._validate_column_names([rack_column], "columns metadata rack filtering")
                            rack_params = []
                            for i, rack in enumerate(racks):
                                param_name = f"rack_{i}"
                                rack_params.append(f"{{{param_name}:String}}")
                                query_params[param_name] = str(rack)
                            where_conditions.append(f"`{rack_column}` IN ({', '.join(rack_params)})")
                            logger.debug(f"[METADATA] Applying rack filter on column '{rack_column}' with values: {racks}")
                        else:
                            logger.warning(f"[METADATA] No rack column found for filtering in table {clickhouse_table}")

                    # Get sample data from ClickHouse
                    result_dict = self.repository.get_column_data_for_table(
                        clickhouse_table_name=clickhouse_table,
                        column_names=existing_columns,
                        where_conditions=where_conditions,
                        query_params=query_params,
                        limit=Dash033Config.MAX_METADATA_SAMPLES
                    )
                    
                    # Extract result_rows from Dict response
                    sample_rows = result_dict.get("result_rows", [])
                    
                    cleaned_rows = self._handle_duplicate_datetime_columns(
                        rows=sample_rows,
                        expected_columns=existing_columns,
                        clickhouse_table=clickhouse_table
                    )
                    
                    logger.debug(
                        f"[METADATA] Original row count: {len(sample_rows)}, "
                        f"Cleaned row count: {len(cleaned_rows)}, "
                        f"Expected columns: {len(existing_columns)}, "
                        f"Actual columns in row: {len(cleaned_rows[0]) if cleaned_rows else 0}"
                    )
                    
                    to_date = result_dict.get("to_date")
                    from_date = result_dict.get("from_date")
                    data_availability_for_given_date = result_dict.get("data_availability_for_given_date", False)
                    response_data["to_date"] = to_date
                    response_data["from_date"] = from_date
                    response_data["data_availability_for_given_date"] = data_availability_for_given_date

                    # Convert to dictionaries with cleaned rows
                    sample_data = [dict(zip(existing_columns, row)) for row in cleaned_rows]
                    total_rows = len(sample_data)

                # Build response structure for each chart group
                charts_data = {}
                
                for chart_id, columns_list in chart_columns.items():
                    chart_data = self._build_chart_metadata_ch(
                        sample_data, columns_list, available_columns, exclude_null, include_samples
                    )
                    if chart_data:
                        charts_data[chart_id] = chart_data

                processing_time = (datetime.now() - start_time).total_seconds()
                response = {
                        "charts": charts_data,
                        "date_filter": {
                            "from_date": from_date,
                            "to_date": to_date,
                            "rows_in_range": total_rows,
                            "sample_size": total_rows,
                            "processing_time_seconds": processing_time,
                            "racks_filter": racks if racks else []
                        },
                        "method_used": "clickhouse_repository",
                        "performance": {
                            "processing_time_seconds": processing_time,
                            "rows_processed": total_rows,
                            "columns_found": len(existing_columns)
                        }
                    }
                response_data.update(response)
                return response_data

            except ClickHouseServiceError:
                raise  # Re-raise our custom exceptions
            except Exception as e:
                logger.error(f"Error in get_columns_metadata (ClickHouse): {e}", exc_info=True)
                raise ClickHouseServiceError(
                    f"Failed to retrieve columns metadata: {str(e)}"
                ) from e
            
    def _empty_metadata_response(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
        """
        Return empty metadata response structure for error cases.
        """
        return {
            "charts": {},
            "date_filter": {
                "from_date": from_date,
                "to_date": to_date,
                "rows_in_range": 0,
                "sample_size": 0,
                "processing_time_seconds": 0
            },
            "method_used": "error",
            "performance": {
                "processing_time_seconds": 0,
                "rows_processed": 0,
                "columns_found": 0
            }
        }

    def _build_chart_metadata_ch(
        self, 
        sample_data: List[Dict], 
        columns: List[str], 
        available_columns: List[str],
        exclude_null: bool = True, 
        include_samples: bool = True
    ):
        """
        Build chart metadata structure from ClickHouse data for specific columns.
        """
        try:
            # Check which columns actually exist
            existing_columns = [col for col in columns if col in available_columns]
            
            if not existing_columns:
                return None

            chart_structure = {
                "x": [],
                "y": []
            }

            # Find Train column (x-axis) - use base service helper
            train_columns = ["Train", "train", "Train_ID", "Unit", "Rack"]
            train_col = None
            for col in train_columns:
                if col in existing_columns:
                    train_col = col
                    break

            # Build x-axis data (Train column)
            if train_col and include_samples:
                train_values = []
                for row in sample_data:
                    val = row.get(train_col)
                    if val is not None:
                        # Normalize to string
                        if isinstance(val, (int, float)):
                            train_values.append(str(int(val)))
                        else:
                            train_values.append(str(val))
                    elif not exclude_null:
                        train_values.append(None)

                # Get unique sorted train values
                unique_trains = []
                if train_values:
                    unique_set = set([t for t in train_values if t is not None])
                    unique_trains = sorted(list(unique_set), 
                                        key=lambda x: int(x) if x and x.isdigit() else 999)

                chart_structure["x"].append({
                    "name": train_col,
                    "type": "int64",
                    "nullable": True,
                    "dataSource": unique_trains
                })

            # Build y-axis data (other columns)
            for col in existing_columns:
                if col == train_col:
                    continue  # Skip train column as it's in x-axis

                if include_samples:
                    col_values = []
                    for row in sample_data:
                        val = row.get(col)
                        if val is not None:
                            if isinstance(val, (int, float)):
                                col_values.append(f"{float(val):.2f}")
                            elif isinstance(val, datetime):
                                col_values.append(val.strftime("%Y-%m-%d %H:%M:%S"))
                            else:
                                col_values.append(str(val))
                        elif not exclude_null:
                            col_values.append(None)

                    # Determine column type based on sample data
                    col_type = self._determine_column_type(col_values)

                    chart_structure["y"].append({
                        "name": col,
                        "type": col_type,
                        "nullable": True,
                        "dataSource": col_values[:20] if len(col_values) > 20 else col_values  # Limit sample size
                    })
                else:
                    # Just metadata without samples
                    chart_structure["y"].append({
                        "name": col,
                        "type": "unknown",
                        "nullable": True,
                        "dataSource": []
                    })

            return chart_structure

        except Exception as e:
            logger.error(f"Error building chart metadata: {e}")
            return None

    def _determine_column_type(self, values: List) -> str:
        """
        Determine the data type of a column based on sample values.
        """
        try:
            if not values:
                return "unknown"
            
            # Get first non-null value for type determination
            sample_val = next((v for v in values if v is not None), None)
            
            if sample_val is None:
                return "unknown"
            
            # Check if it's a numeric value (allowing for decimal points)
            if isinstance(sample_val, str):
                # Remove minus sign and decimal point for digit check
                cleaned = sample_val.replace('.', '').replace('-', '')
                if cleaned.isdigit():
                    if '.' in sample_val:
                        return "double"
                    else:
                        return "int64"
            
            # Check for percentage columns
            if any(keyword in str(sample_val).lower() for keyword in ['%', 'percent', 'pct']):
                return "double"
                
            # Default to string for other cases
            return "string"
            
        except Exception as e:
            logger.error(f"Error determining column type: {e}")
            return "unknown"
        
    def get_racks_data(
        self,
        site_name: str = None,
        user: dict = None
    ):
        """
        Get unique rack/train data for a site using ClickHouse.
        Returns unique Train column values.
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)

            site_name = self._normalize_site_name(site_name)

            table_prefix = self.site_table_suffix_mappings(site_name)

            # Map site name to table identifier (similar to original logic)
            table_suffix = f"{table_prefix}_mode_racks_operation"

            clickhouse_table = self.repository.get_clickhouse_table_name(site_name, table_suffix)
            if not clickhouse_table:
                logger.error(f"No ClickHouse table found for site {site_name} with suffix {table_suffix}")
                return {
                    "racks": [],
                    "count": 0
                }

            # Use repository method to find train column
            train_column = self.repository.get_rack_trailer_column(clickhouse_table)

            if not train_column:
                logger.warning(f"No train column found in table {clickhouse_table}")
                return {
                    "racks": [],
                    "count": 0
                }

            # Validate train column before using in query
            self._validate_column_names([train_column], "racks data filtering")

            try:
                # Execute the query using repository's connection
                result_dict = self.repository.get_column_data_for_table(
                    clickhouse_table_name=clickhouse_table,
                    column_names=[train_column],
                    where_conditions=[f"`{train_column}` IS NOT NULL"],
                    query_params={},
                    limit=Dash033Config.MAX_DISTINCT_RACKS
                )
                # Extract result_rows from Dict response
                unique_trains_rows = result_dict.get("result_rows", [])

                cleaned_rows = self._handle_duplicate_datetime_columns(
                    rows=unique_trains_rows,
                    expected_columns=[train_column],
                    clickhouse_table=clickhouse_table
                )
                
                logger.debug(
                    f"[RACKS_DATA] Original row count: {len(unique_trains_rows)}, "
                    f"Cleaned row count: {len(cleaned_rows)}, "
                    f"Expected columns: 1, "
                    f"Actual columns in row: {len(cleaned_rows[0]) if cleaned_rows else 0}"
                )

                # Extract unique train values
                seen = set()
                racks_list = []

                for row in cleaned_rows:
                    train_val = row[0] if row else None
                    
                    if train_val is not None and train_val not in seen:
                        seen.add(train_val)
                        try:
                            # Convert to integer for proper sorting
                            racks_list.append(int(float(train_val)))
                        except (ValueError, TypeError):
                            # If conversion fails, use string representation
                            racks_list.append(str(train_val))

                # Sort the list (integers will sort numerically, strings alphabetically)
                racks_list.sort(key=lambda x: (isinstance(x, str), x))

                return {
                    "racks": racks_list,
                    "count": len(racks_list)
                }

            except Exception as query_error:
                logger.error(f"Error querying racks data: {query_error}")
                return {
                    "racks": [],
                    "count": 0
                }

        except ClickHouseServiceError:
            raise  # Re-raise our custom exceptions
        except Exception as e:
            logger.error(f"Error in get_racks_data (ClickHouse): {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to retrieve racks data: {str(e)}"
            ) from e