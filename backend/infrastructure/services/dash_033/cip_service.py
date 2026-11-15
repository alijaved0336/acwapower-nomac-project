"""
CIP Service for Dashboard-033
Handles CIP (Clean-In-Place) operations and related data retrieval.
"""
import logging
import math
from http.client import responses
from typing import List, Optional, Dict, Any
from .base_service import Dash033BaseService
from infrastructure.exceptions import ClickHouseServiceError
from constants import Dash033Config

logger = logging.getLogger(__name__)


class CIPService(Dash033BaseService):
    """
    Service class for CIP operations.
    Handles validated CIP, flushing mode, and CIP summary data.
    """

    def _handle_duplicate_datetime_columns(
        self, 
        rows: List[tuple], 
        available_columns: List[str], 
        clickhouse_table: str
    ) -> List[tuple]:
        """
        Handle duplicate datetime columns in result rows from repository.
        
        The repository adds datetime column with timezone conversion at INDEX 0,
        then adds all requested columns. This creates a duplicate if datetime 
        column is in available_columns.
        
        Args:
            rows: List of result rows from repository
            available_columns: List of expected column names
            clickhouse_table: Table name for logging
        
        Returns:
            List of rows with duplicate column removed
        
        Example - CIP Summary:
            available_columns = ['Train', 'Count', 'Latest_Start_Time', 'Days']  (4 columns)
            actual row = (tz_datetime, train, count, raw_datetime, days)         (5 columns)
                        ↑ Index 0 - Added by repo with timezone conversion
            
            We remove index 0, resulting in:
            cleaned row = (train, count, raw_datetime, days)  (4 columns) ✅
        """
        if not rows:
            return rows
        
        # Get the datetime column from repository
        datetime_column = self.repository.get_datetime_column(clickhouse_table)
        
        # Check if we have a column count mismatch
        expected_count = len(available_columns)
        actual_count = len(rows[0]) if rows else 0
        
        if actual_count == expected_count:
            # No mismatch, return as-is
            logger.debug(f"[CIP] Column counts match: {actual_count} columns")
            return rows
        
        if actual_count != expected_count + 1:
            # Unexpected mismatch (not the duplicate datetime issue)
            logger.warning(
                f"[CIP] Unexpected column count mismatch in {clickhouse_table}: "
                f"expected {expected_count}, got {actual_count}"
            )
            return rows
        
        # We have exactly one extra column - the duplicate datetime at index 0
        logger.info(
            f"[CIP] Detected duplicate column in {clickhouse_table}: "
            f"expected {expected_count}, got {actual_count}. "
            f"Removing duplicate datetime column '{datetime_column}'"
        )
        
        try:
            # ✅ CRITICAL FIX: Always remove index 0 (the timezone-converted datetime added by repository)
            # The repository ALWAYS adds the datetime column at the BEGINNING with timezone conversion,
            # then adds all the requested columns (which may include the datetime column again)
            remove_index = 0
            
            logger.debug(
                f"[CIP] Removing duplicate datetime at index {remove_index} "
                f"('{datetime_column}' with timezone conversion added by repository)"
            )
            
            # Remove the duplicate column from each row
            cleaned_rows = []
            for row in rows:
                # Convert to list, remove index 0, convert back to tuple
                row_list = list(row)
                if len(row_list) > remove_index:
                    row_list.pop(remove_index)
                cleaned_rows.append(tuple(row_list))
            
            logger.info(
                f"[CIP] Successfully cleaned {len(cleaned_rows)} rows: "
                f"removed duplicate datetime column at index {remove_index}"
            )
            
            return cleaned_rows
            
        except (ValueError, IndexError) as e:
            logger.error(
                f"[CIP] Error removing duplicate column: {e}. "
                f"Returning original rows"
            )
            return rows
    
    def get_cip_validated_info(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        page: int = 1,
        limit: int = 25,
        racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get CIP validated info using ClickHouse with pagination and filtering.

        Args:
            site_name: Site identifier
            user: User context for default site
            start_time: Start datetime filter
            end_time: End datetime filter
            page: Page number for pagination
            limit: Items per page
            racks: Optional list of rack IDs to filter

        Returns:
            Paginated CIP validated data

        Raises:
            ClickHouseServiceError: If retrieval fails

        Example:
            >>> service = CIPService()
            >>> result = service.get_cip_validated_info(
            ...     site_name='Rabigh3',
            ...     page=1,
            ...     limit=25
            ... )
            >>> print(result["total"])
            150
        """
        return self._get_cip_info_by_mode(
            mode_value=Dash033Config.MODE_VALIDATED_CIP,
            mode_name="validated",
            site_name=site_name,
            user=user,
            start_time=start_time,
            end_time=end_time,
            page=page,
            limit=limit,
            racks=racks
        )

    def get_cip_flushing_info(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        page: int = 1,
        limit: int = 25,
        racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get CIP flushing info using ClickHouse with pagination and filtering.

        Args:
            site_name: Site identifier
            user: User context for default site
            start_time: Start datetime filter
            end_time: End datetime filter
            page: Page number for pagination
            limit: Items per page
            racks: Optional list of rack IDs to filter

        Returns:
            Paginated CIP flushing data

        Raises:
            ClickHouseServiceError: If retrieval fails
        """
        return self._get_cip_info_by_mode(
            mode_value=Dash033Config.MODE_FLUSHING,
            mode_name="flushing",
            site_name=site_name,
            user=user,
            start_time=start_time,
            end_time=end_time,
            page=page,
            limit=limit,
            racks=racks
        )

    def get_cip_summary(
        self,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get CIP summary using ClickHouse with database-level data retrieval.

        Args:
            site_name: Site identifier
            user: User context for default site
            start_time: Start datetime filter
            end_time: End datetime filter
            racks: Optional list of rack IDs to filter

        Returns:
            CIP summary data formatted for chart rendering

        Raises:
            ClickHouseServiceError: If retrieval fails
        """
        try:
            if not site_name:
                site_name = self.get_defaults(user)

            site_name = self._normalize_site_name(site_name)
            table_prefix = self.site_table_suffix_mappings(site_name)
            table_suffix = f"{table_prefix}_mode_cip_summary"
            
            clickhouse_table = self._get_clickhouse_table(site_name, table_suffix, user)

            # Get available columns
            columns = self.repository.get_table_columns(clickhouse_table)
            available_columns = [col["name"] for col in columns]
            logger.debug(f"[CIP_SUMMARY] Available columns in {clickhouse_table}: {available_columns}")

            # Flexible column matching - pass table name for Train column detection
            found_columns = self._find_cip_summary_columns(clickhouse_table, available_columns)

            if not found_columns:
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
                        "sample_data": [dict(zip(available_columns, r)) for r in sample_rows],
                        "message": "No required columns found for CIP summary"
                    }
                }

            # Build where conditions
            where_conditions, query_params = self._build_cip_where_conditions(
                clickhouse_table, available_columns, start_time, end_time, racks, found_columns
            )

            # Fetch data from ClickHouse
            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=clickhouse_table,
                column_names=available_columns,
                where_conditions=where_conditions,
                query_params=query_params,
                limit=Dash033Config.MAX_CHART_DATA_ROWS
            )
            # Extract result_rows from Dict response
            all_rows = result_dict.get("result_rows", [])
            
            cleaned_rows = self._handle_duplicate_datetime_columns(
                rows=all_rows,
                available_columns=available_columns,
                clickhouse_table=clickhouse_table
            )

            logger.info(f"Retrieved {len(cleaned_rows)} rows for CIP summary from {clickhouse_table}")
            
            if not cleaned_rows:
                logger.info(f"No CIP summary data found for site {site_name} with racks filter: {racks}")
                return self._empty_cip_summary_response()
                
            response_data = self._format_cip_summary_result_clickhouse(cleaned_rows, found_columns, available_columns)
            response_data["to_date"] = result_dict.get("to_date")
            response_data["from_date"] = result_dict.get("from_date")
            response_data["data_availability_for_given_date"] = result_dict.get("data_availability_for_given_date", True)
            
            return response_data

        except ClickHouseServiceError:
            raise
        except Exception as e:
            logger.error(f"Error in get_cip_summary (ClickHouse): {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to retrieve CIP summary: {str(e)}"
            ) from e

    def _empty_cip_summary_response(self) -> Dict[str, Any]:
        """Return empty CIP summary response structure."""
        return {
            "rackcipstatus": {
                "G1": {
                    "x": [{"name": "Days Since Last CIP", "data": []}],
                    "y": [{"name": "Train", "data": []}]
                }
            }
        }

    def _get_cip_info_by_mode(
        self,
        mode_value: str,
        mode_name: str,
        site_name: str = None,
        user: dict = None,
        start_time: str = None,
        end_time: str = None,
        page: int = 1,
        limit: int = 25,
        racks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Shared method to get CIP info filtered by mode value.

        Args:
            mode_value: The mode filter value (e.g., "Validated CIP", "Flushing")
            mode_name: Human-readable name for logging
            site_name: Site identifier
            user: User context
            start_time: Start datetime filter
            end_time: End datetime filter
            page: Page number
            limit: Items per page
            racks: Optional rack filter

        Returns:
            Dictionary with paginated CIP data

        Raises:
            ValueError: If pagination parameters are invalid
            ClickHouseServiceError: If database operation fails
        """
        try:
            if page < 1:
                raise ValueError("Page must be a positive integer")

            if not site_name:
                site_name = self.get_defaults(user)

            site_name = self._normalize_site_name(site_name)
            table_prefix = self.site_table_suffix_mappings(site_name)
            table_suffix = f"{table_prefix}_mode_cip"
            
            clickhouse_table = self._get_clickhouse_table(site_name, table_suffix, user)

            # Get available columns
            columns = self.repository.get_table_columns(clickhouse_table)
            available_columns = [col["name"] for col in columns]
            logger.debug(f"[CIP_{mode_name.upper()}] Available columns: {available_columns}")

            # Find mode column
            mode_column = self._find_mode_column(available_columns)

            if not mode_column:
                return self._diagnostic_response(available_columns, clickhouse_table, mode_name, page, limit)

            # Build where conditions
            self._validate_column_names([mode_column], f"CIP {mode_name} mode filtering")
            where_conditions = [f"`{mode_column}` = '{mode_value}'"]
            query_params = {}

            # Add date and rack filtering
            self._add_date_filter(where_conditions, query_params, available_columns, start_time, end_time, mode_name)
            self._add_rack_filter(where_conditions, query_params, clickhouse_table, racks, mode_name)

            # Get total count
            total_count = self.repository.get_count_for_table(
                clickhouse_table_name=clickhouse_table,
                where_conditions=where_conditions,
                query_params=query_params
            )

            total_pages = math.ceil(total_count / limit) if limit > 0 else 1

            if page > total_pages and total_count > 0:
                logger.warning(f"Requested page {page} exceeds total pages {total_pages}, returning last page")
                page = total_pages

            # Calculate offset
            offset = (page - 1) * limit

            # Fetch paginated rows
            result_dict = self.repository.get_column_data_for_table(
                clickhouse_table_name=clickhouse_table,
                column_names=available_columns,
                where_conditions=where_conditions,
                query_params=query_params,
                limit=limit,
                offset=offset
            )
            # Extract result_rows from Dict response
            paginated_rows = result_dict.get("result_rows", [])

            cleaned_rows = self._handle_duplicate_datetime_columns(
                rows=paginated_rows,
                available_columns=available_columns,
                clickhouse_table=clickhouse_table
            )
            
            logger.debug(
                f"[CIP_{mode_name.upper()}] Original row count: {len(paginated_rows)}, "
                f"Cleaned row count: {len(cleaned_rows)}, "
                f"Expected columns: {len(available_columns)}, "
                f"Actual columns in row: {len(cleaned_rows[0]) if cleaned_rows else 0}"
            )

            items = [dict(zip(available_columns, row)) for row in cleaned_rows]
            items_formatted = self.format_items_to_columnar(items)

            logger.info(f"Retrieved {len(items)} CIP {mode_name} items (page {page}/{total_pages}, total: {total_count})")

            return {
                "to_date": result_dict.get("to_date"),
                "from_date": result_dict.get("from_date"),
                "data_availability_for_given_date": result_dict.get("data_availability_for_given_date"),
                "items": items_formatted,
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }

        except ClickHouseServiceError:
            raise
        except Exception as e:
            logger.error(f"Error in _get_cip_info_by_mode (mode={mode_name}): {e}", exc_info=True)
            raise ClickHouseServiceError(
                f"Failed to retrieve CIP {mode_name} info: {str(e)}"
            ) from e

    def _find_mode_column(self, available_columns: List[str]) -> Optional[str]:
        """Find mode validation column using flexible matching."""
        mode_candidates = Dash033Config.COLUMN_MAPPINGS.get("Mode_Validated", [])
        for candidate in mode_candidates:
            if candidate in available_columns:
                logger.debug(f"[CIP] Found mode column: {candidate}")
                return candidate
        return None

    def _find_cip_summary_columns(self, clickhouse_table: str, available_columns: List[str]) -> Dict[str, str]:
        """Find required columns for CIP summary using repository method for Train column."""
        found_columns = {}
        
        # Use repository method to find Train column
        train_col = self.repository.get_rack_trailer_column(clickhouse_table)
        if train_col:
            found_columns["Train"] = train_col
            logger.debug(f"[CIP_SUMMARY] Found train column using repository: {train_col}")
        
        # Find Days_Since_Last_CIP column
        days_candidates = Dash033Config.COLUMN_MAPPINGS.get("Days_Since_Last_CIP", [])
        for candidate in days_candidates:
            if candidate in available_columns:
                found_columns["Days_Since_Last_CIP"] = candidate
                logger.debug(f"[CIP_SUMMARY] Found days column: {candidate}")
                break

        return found_columns

    def _build_cip_where_conditions(
        self, clickhouse_table: str, available_columns: List[str], start_time: str, end_time: str,
        racks: Optional[List[str]], found_columns: Dict[str, str]
    ) -> tuple:
        """Build WHERE conditions for CIP summary query."""
        where_conditions = []
        query_params = {}

        if "Start_Time" in available_columns and "End_Time" in available_columns:
            if start_time and end_time:
                self._validate_column_names(["Start_Time", "End_Time"], "CIP summary date filtering")
                where_conditions.append(
                    f"(`Start_Time` >= {{start_date:DateTime}} AND `End_Time` <= {{end_date:DateTime}})"
                )
                query_params["start_date"] = start_time
                query_params["end_date"] = end_time

        # Use found Train column from repository method
        if racks and found_columns.get("Train"):
            train_col = found_columns["Train"]
            self._validate_column_names([train_col], "CIP summary rack filtering")
            rack_params = []
            for i, rack in enumerate(racks):
                param_name = f"train_{i}"
                rack_params.append(f"{{{param_name}:String}}")
                query_params[param_name] = str(rack)
            where_conditions.append(f"`{train_col}` IN ({', '.join(rack_params)})")
            logger.debug(f"[CIP_SUMMARY] Applying rack filter on column '{train_col}' with values: {racks}")

        return where_conditions, query_params

    def _add_date_filter(
        self, where_conditions: List[str], query_params: Dict,
        available_columns: List[str], start_time: str, end_time: str, context: str
    ) -> None:
        """Add date filtering to WHERE conditions."""
        if "Start_Time" in available_columns and "End_Time" in available_columns:
            if start_time and end_time:
                self._validate_column_names(["Start_Time", "End_Time"], f"CIP {context} date filtering")
                where_conditions.append(
                    f"(`Start_Time` >= {{start_date:DateTime}} AND `End_Time` <= {{end_date:DateTime}})"
                )
                query_params["start_date"] = start_time
                query_params["end_date"] = end_time

    def _add_rack_filter(
        self, where_conditions: List[str], query_params: Dict,
        clickhouse_table: str, racks: Optional[List[str]], context: str
    ) -> None:
        """Add rack filtering to WHERE conditions using repository method."""
        if not racks:
            return
        
        # Use repository method to find the train column
        train_col = self.repository.get_rack_trailer_column(clickhouse_table)
        
        if train_col:
            self._validate_column_names([train_col], f"CIP {context} rack filtering")
            rack_params = []
            for i, rack in enumerate(racks):
                param_name = f"train_{i}"
                rack_params.append(f"{{{param_name}:String}}")
                query_params[param_name] = str(rack)
            where_conditions.append(f"`{train_col}` IN ({', '.join(rack_params)})")
            logger.debug(f"[CIP_{context.upper()}] Applying rack filter on column '{train_col}' with values: {racks}")
        else:
            logger.warning(f"[CIP_{context.upper()}] Could not apply rack filter - no train column found")

    def _diagnostic_response(
        self, available_columns: List[str], clickhouse_table: str,
        mode_name: str, page: int, limit: int
    ) -> Dict[str, Any]:
        """Return diagnostic response when mode column not found."""
        result_dict = self.repository.get_column_data_for_table(
            clickhouse_table_name=clickhouse_table,
            column_names=available_columns,
            where_conditions=[],
            query_params={},
            limit=2
        )
        # Extract result_rows from Dict response
        sample_rows = result_dict.get("result_rows", [])
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 0,
            "diagnostic_info": {
                "available_columns": available_columns,
                "sample_data": [dict(zip(available_columns, r)) for r in sample_rows],
                "message": f"No mode validation column found for {mode_name}"
            }
        }

    def _format_cip_summary_result_clickhouse(
        self, rows: List, found_columns: Dict, available_columns: List[str]
    ) -> Dict[str, Any]:
        """Format CIP summary results for ClickHouse query output."""
        try:
            if not rows:
                return self._empty_cip_summary_response()

            train_col = found_columns.get("Train", "Train")
            days_col = found_columns.get("Days_Since_Last_CIP", "days_since")

            # Convert rows into dicts
            dict_rows = [dict(zip(available_columns, row)) for row in rows]

            # Build parallel arrays FIRST (before sorting)
            train_data = []
            days_data = []

            for row in dict_rows:
                try:
                    train_data.append(row.get(train_col))
                    days_data.append(row.get(days_col))
                except Exception as row_error:
                    logger.warning(f"[CIP_SUMMARY] Row processing error: {row_error}")
                    continue

            # Safe sorting with proper type handling (copied from racks_runtime service)
            def sort_key(item):
                """
                Safe sorting key that handles both numeric and string train IDs.
                Returns a tuple (is_numeric, numeric_value or string_value) for proper sorting.
                
                How it works:
                - Numeric train IDs (e.g., "5", "10") get (0, numeric_value) and sort first
                - String train IDs (e.g., "R1", "R5") get (1, string_value) and sort after
                - This prevents TypeError when comparing mixed types
                
                Args:
                    item: Tuple from zip() where item[0] is the train_id
                
                Returns:
                    Tuple of (sort_priority, sort_value) for safe comparison
                """
                train_id = item[0]
                try:
                    # Try to convert to integer for numeric sorting
                    return (0, int(str(train_id).strip()))
                except (ValueError, TypeError):
                    # Fall back to string sorting for non-numeric IDs
                    return (1, str(train_id).strip().lower())

            # Sort all parallel arrays together using zip to maintain alignment
            try:
                sorted_data = sorted(
                    zip(train_data, days_data),
                    key=sort_key
                )

                if sorted_data:
                    # Unpack sorted data back into separate arrays
                    train_data, days_data = zip(*sorted_data)
                    train_data = list(train_data)
                    days_data = list(days_data)
                    
                    logger.info(
                        f"[CIP_SUMMARY] Successfully sorted {len(train_data)} train records"
                    )

            except Exception as sort_error:
                logger.warning(
                    f"[CIP_SUMMARY] Sorting failed: {sort_error}. Returning unsorted data."
                )
                # Data remains in original order if sorting fails

            return {
                "rackcipstatus": {
                    "G1": {
                        "x": [{"name": "Days Since Last CIP", "data": days_data}],
                        "y": [{"name": "Train", "data": train_data}]
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error formatting CIP summary result (ClickHouse): {e}")
            raise ClickHouseServiceError(
                f"Failed to format CIP summary result: {str(e)}"
            ) from e