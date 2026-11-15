"""
DateTime processing component for the Multi-Site Column Data Service.
Handles parsing, validation, and filtering logic for DateTime parameters.
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from infrastructure.utils.datetime_utils import DateTimeParser
from .models import FilterMode

logger = logging.getLogger(__name__)


class DateTimeProcessor:
    """
    Handles all DateTime parsing, validation, and filtering logic.
    Supports the endpoint's comma-separated format and flexible filtering modes.
    """

    def __init__(self):
        # Read max_range_days from environment variable, None if not set or 0
        env_value = os.getenv('MAX_DATE_RANGE_DAYS', '')
        if env_value:
            try:
                days = int(env_value)
                self.max_range_days = days if days > 0 else None
            except ValueError:
                self.max_range_days = None
                logger.warning(f"[DATETIME_PROCESSOR] Invalid MAX_DATE_RANGE_DAYS value: {env_value}, date range validation disabled")
        else:
            self.max_range_days = None

        if self.max_range_days is None:
            logger.info("[DATETIME_PROCESSOR] Date range validation is disabled (MAX_DATE_RANGE_DAYS not configured)")
        else:
            logger.info(f"[DATETIME_PROCESSOR] Date range validation enabled with max {self.max_range_days} days")

        self.default_range_days = 7  # Default range when no dates provided
    
    def parse_filter_params(
        self, 
        from_date: Optional[str], 
        to_date: Optional[str]
    ) -> Tuple[FilterMode, Optional[datetime], Optional[datetime]]:
        """
        Parse DateTime parameters and determine filtering strategy.
        If no dates provided, defaults to last 7 days range.
        
        Returns:
            Tuple of (FilterMode, from_datetime, to_datetime)
        """
        try:
            if from_date and to_date:
                # Range filtering: both dates provided
                from_dt = self._parse_datetime_string(from_date)
                to_dt = self._parse_datetime_string(to_date)
                self._validate_datetime_range(from_dt, to_dt)
                
                logger.info(f"[DATETIME_PROCESSOR] Range filtering: {from_dt} to {to_dt}")
                return FilterMode.RANGE, from_dt, to_dt
                
            elif from_date and not to_date:
                # Exact match: only from_date provided
                exact_dt = self._parse_datetime_string(from_date)
                
                logger.info(f"[DATETIME_PROCESSOR] Exact match filtering: {exact_dt}")
                return FilterMode.EXACT, exact_dt, exact_dt
                
            elif to_date and not from_date:
                # Exact match: only to_date provided
                exact_dt = self._parse_datetime_string(to_date)
                
                logger.info(f"[DATETIME_PROCESSOR] Exact match filtering: {exact_dt}")
                return FilterMode.EXACT, exact_dt, exact_dt
                
            else:
                # No dates provided: default to last 7 days range
                now = datetime.now(timezone.utc)
                from_dt = now - timedelta(days=self.default_range_days)
                to_dt = now
                
                logger.info(f"[DATETIME_PROCESSOR] No dates provided, using default last {self.default_range_days} days: {from_dt} to {to_dt}")
                return FilterMode.RANGE, from_dt, to_dt
                
        except Exception as e:
            logger.error(f"[DATETIME_PROCESSOR] Error parsing DateTime parameters: {e}")
            raise ValueError(f"DateTime parsing error: {str(e)}")
    
    def _parse_datetime_string(self, datetime_str: str) -> datetime:
        """
        Parse DateTime string supporting multiple formats:
        - "2025-06-01,10:00:00" (endpoint format with comma)
        - "2025-06-01 10:00:00" (standard format)
        - "2025-06-01" (date-only format)
        """
        if not datetime_str or not datetime_str.strip():
            raise ValueError("DateTime string cannot be empty")
        
        try:
            cleaned_str = datetime_str.strip()
            
            # Handle comma-separated format from endpoint
            if ',' in cleaned_str:
                date_part, time_part = cleaned_str.split(',', 1)
                normalized_str = f"{date_part.strip()} {time_part.strip()}"
            else:
                normalized_str = cleaned_str
            
            # Try full datetime format first
            try:
                parsed_dt = datetime.strptime(normalized_str, '%Y-%m-%d %H:%M:%S')
                # Ensure timezone awareness for consistency
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                return parsed_dt
                
            except ValueError:
                # Try date-only format (assume start of day)
                try:
                    date_only = datetime.strptime(normalized_str.split()[0], '%Y-%m-%d')
                    # Set to start of day with UTC timezone
                    return date_only.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            # Try ISO format as fallback
            try:
                parsed_dt = datetime.fromisoformat(normalized_str.replace('Z', '+00:00'))
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                return parsed_dt
            except ValueError:
                pass
            
            raise ValueError(f"Unrecognized datetime format")
                
        except Exception as e:
            raise ValueError(
                f"Invalid datetime format: '{datetime_str}'. "
                f"Expected formats: 'YYYY-MM-DD,HH:MM:SS', 'YYYY-MM-DD HH:MM:SS', or 'YYYY-MM-DD'. "
                f"Error: {str(e)}"
            )
    
    def _validate_datetime_range(self, from_dt: datetime, to_dt: datetime) -> None:
        """Validate DateTime range for performance and logical consistency."""
        # Always check logical consistency
        if from_dt >= to_dt:
            raise ValueError("from_date must be before to_date")

        # Only apply date range limit if max_range_days is configured
        if self.max_range_days is not None:
            range_days = (to_dt - from_dt).days
            if range_days > self.max_range_days:
                raise ValueError(
                    f"DateTime range of {range_days} days exceeds maximum allowed {self.max_range_days} days"
                )
            logger.debug(f"[DATETIME_PROCESSOR] Date range of {range_days} days is within limit of {self.max_range_days} days")
        else:
            # Log when no limit is applied for debugging purposes
            range_days = (to_dt - from_dt).days
            logger.debug(f"[DATETIME_PROCESSOR] Date range of {range_days} days accepted (no limit configured)")

        # Check if dates are too far in the future (basic sanity check)
        now = datetime.now(timezone.utc)
        if from_dt > now:
            # Allow small buffer for timezone differences
            if (from_dt - now).days > 1:
                raise ValueError("from_date cannot be more than 1 day in the future")

        if to_dt > now:
            if (to_dt - now).days > 1:
                raise ValueError("to_date cannot be more than 1 day in the future")
    
    def create_datetime_filters_for_pyarrow(
        self,
        filter_mode: FilterMode,
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        datetime_column: str = "DateTime"
    ) -> Optional[list]:
        """
        Create PyArrow-compatible filters for datetime filtering.
        
        Returns:
            List of filter tuples for PyArrow, or None if no filtering needed
        """
        if filter_mode == FilterMode.NONE:
            return None
        
        filters = []
        
        if filter_mode == FilterMode.EXACT:
            # For exact match, we need to handle potential timestamp precision issues
            # Create a small range around the exact timestamp
            exact_start = from_dt.replace(microsecond=0)
            exact_end = from_dt.replace(second=59, microsecond=999999)
            
            filters = [
                (datetime_column, '>=', exact_start),
                (datetime_column, '<=', exact_end)
            ]
            
        elif filter_mode == FilterMode.RANGE:
            filters = [
                (datetime_column, '>=', from_dt),
                (datetime_column, '<=', to_dt)
            ]
        
        logger.debug(f"[DATETIME_PROCESSOR] Created PyArrow filters: {filters}")
        return filters
    
    def create_datetime_filters_for_spark(
        self,
        filter_mode: FilterMode,
        from_dt: Optional[datetime],
        to_dt: Optional[datetime],
        datetime_column: str = "DateTime"
    ) -> str:
        """
        Create Spark SQL WHERE clause for datetime filtering.
        
        Returns:
            SQL WHERE clause string, or empty string if no filtering needed
        """
        if filter_mode == FilterMode.NONE:
            return ""
        
        conditions = []
        
        if filter_mode == FilterMode.EXACT:
            # For exact match in Spark, use string casting for safety
            exact_dt_str = from_dt.strftime('%Y-%m-%d %H:%M:%S')
            conditions.append(f"CAST(`{datetime_column}` AS STRING) LIKE '{exact_dt_str}%'")
            
        elif filter_mode == FilterMode.RANGE:
            from_dt_str = from_dt.strftime('%Y-%m-%d %H:%M:%S')
            to_dt_str = to_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            conditions.extend([
                f"CAST(`{datetime_column}` AS STRING) >= '{from_dt_str}'",
                f"CAST(`{datetime_column}` AS STRING) <= '{to_dt_str}'"
            ])
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        logger.debug(f"[DATETIME_PROCESSOR] Created Spark WHERE clause: {where_clause}")
        
        return where_clause
    
    def is_file_relevant_for_filter(
        self,
        file_path: str,
        filter_mode: FilterMode,
        from_dt: Optional[datetime],
        to_dt: Optional[datetime]
    ) -> bool:
        """
        Check if a file is relevant based on DateTime filtering and path structure.
        Uses the YYYY/MM/DD directory structure for quick filtering.
        """
        if filter_mode == FilterMode.NONE:
            return True
        
        # Extract date from path structure: tables/gold/{site}/{table}/YYYY/MM/DD/file.parquet
        try:
            path_parts = file_path.split('/')
            if len(path_parts) < 7:
                return True  # Include file if path structure is unclear
            
            year = int(path_parts[-4])
            month = int(path_parts[-3])
            day = int(path_parts[-2])
            
            file_date = datetime(year, month, day, tzinfo=timezone.utc)
            
            if filter_mode == FilterMode.EXACT:
                # For exact match, check if file date matches target date
                target_date = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                return file_date.date() == target_date.date()
            
            elif filter_mode == FilterMode.RANGE:
                # For range, check if file date overlaps with range
                range_start = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                range_end = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                return range_start.date() <= file_date.date() <= range_end.date()
                
        except (ValueError, IndexError) as e:
            logger.warning(f"[DATETIME_PROCESSOR] Could not parse date from file path {file_path}: {e}")
            return True  # Include file if we can't parse the date
        
        return False
    
    def get_filter_summary(
        self,
        filter_mode: FilterMode,
        from_dt: Optional[datetime],
        to_dt: Optional[datetime]
    ) -> dict:
        """Get summary information about the current filter configuration."""
        summary = {
            "filter_mode": filter_mode.value,
            "from_date": DateTimeParser.format_datetime_without_timezone(from_dt) if from_dt else None,
            "to_date": DateTimeParser.format_datetime_without_timezone(to_dt) if to_dt else None,
            "range_days": None,
            "default_applied": False
        }
        
        if filter_mode == FilterMode.RANGE and from_dt and to_dt:
            summary["range_days"] = (to_dt - from_dt).days
            
            # Check if this was a default range (last 7 days)
            now = datetime.now(timezone.utc)
            expected_from = now - timedelta(days=self.default_range_days)
            if abs((from_dt - expected_from).total_seconds()) < 60:  # Within 1 minute
                summary["default_applied"] = True
        
        return summary