"""
Date utility functions for ClickHouse services.
Provides common date parsing, validation, and filtering functionality.
"""

import logging
import os
from datetime import datetime, timedelta, date
from typing import Optional, Tuple, Union
import pytz
import re

logger = logging.getLogger(__name__)

def validate_date_range(from_date: str, to_date: str, apply_timezone: bool = False) -> None:
    """
    Validate that date range is reasonable.

    Args:
        from_date: Start date string
        to_date: End date string
        apply_timezone: If True, applies timezone conversion for validation (default: False)

    Raises:
        Exception: If date range is invalid
    """
    try:
        from_dt_str = parse_datetime(from_date)
        to_dt_str = parse_datetime(to_date)

        if from_dt_str and to_dt_str:
            from_dt = datetime.strptime(from_dt_str, '%Y-%m-%d %H:%M:%S')
            to_dt = datetime.strptime(to_dt_str, '%Y-%m-%d %H:%M:%S')

            if to_dt < from_dt:
                raise Exception("End date cannot be before start date")

            # Allow up to 90 days range
            if (to_dt - from_dt).days > 90:
                logger.warning("Date range exceeds 90 days, performance may be affected")

    except Exception as e:
        logger.warning(f"Date validation warning: {e}")
        # Don't fail the request on validation warnings
        pass


def parse_datetime(datetime_str: str, return_datetime_object: bool = False) -> Union[str, datetime, None]:
    """
    Parse various datetime formats to standard format.

    Args:
        datetime_str: Input datetime string

    Returns:
        Standardized datetime string in format 'YYYY-MM-DD HH:MM:SS'

    Raises:
        Exception: If datetime format is invalid
    """
    if not datetime_str:
        return None

    datetime_str = datetime_str.strip()

    try:
        if 'T' in datetime_str:
            # Remove 'Z' suffix and replace with '+00:00' for ISO format parsing
            if datetime_str.endswith('Z'):
                datetime_str_cleaned = datetime_str[:-1] + '+00:00'
            else:
                datetime_str_cleaned = datetime_str

            try:
                # Try parsing as ISO format with timezone
                dt = datetime.fromisoformat(datetime_str_cleaned)
                
                # Remove timezone info to work with naive datetime (as ClickHouse expects)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                
                # DEFAULT behavior: return string (backward compatible)
                if return_datetime_object:
                    return dt
                else:
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                    
            except (ValueError, AttributeError):
                # If fromisoformat fails, try manual parsing
                # Handle format like "2024-10-30T08:58:20" without timezone
                if datetime_str.count('T') == 1:
                    date_time_parts = datetime_str.split('T')
                    date_part = date_time_parts[0]
                    time_part = date_time_parts[1].rstrip('Z')  # Remove Z if present
                    
                    # Remove microseconds if present
                    if '.' in time_part:
                        time_part = time_part.split('.')[0]
                    
                    # Validate and create datetime
                    dt = datetime.strptime(f"{date_part} {time_part}", '%Y-%m-%d %H:%M:%S')
                    
                    # DEFAULT behavior: return string (backward compatible)
                    if return_datetime_object:
                        return dt
                    else:
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
        elif ',' in datetime_str:
            date_part, time_part = datetime_str.split(',', 1)
            date_part = date_part.strip()
            time_part = time_part.strip()

            # Validate date format
            datetime.strptime(date_part, '%Y-%m-%d')

            # Add seconds if not present in time
            if len(time_part.split(':')) == 2:
                time_part += ':00'

            if return_datetime_object:
                return datetime.strptime(f"{date_part} {time_part}", '%Y-%m-%d %H:%M:%S')
            else:
                return f"{date_part} {time_part}"

        # Handle space-separated format: "2025-06-01 10:00:00"
        elif ' ' in datetime_str:
            parts = datetime_str.split(' ', 1)
            date_part = parts[0]
            time_part = parts[1]

            # Validate date format
            datetime.strptime(date_part, '%Y-%m-%d')

            # Add seconds if not present
            if len(time_part.split(':')) == 2:
                time_part += ':00'

            if return_datetime_object:
                return datetime.strptime(f"{date_part} {time_part}", '%Y-%m-%d %H:%M:%S')
            else:
                return f"{date_part} {time_part}"

        # Handle date-only format: "2025-06-01"
        else:
            # Validate date format
            datetime.strptime(datetime_str, '%Y-%m-%d')

            if return_datetime_object:
                return datetime.strptime(datetime_str, '%Y-%m-%d')
            else:
                return f"{datetime_str} 00:00:00"

    except ValueError as e:
        logger.error(f"Invalid date format: {datetime_str} - {e}")
        raise Exception(
            f"Invalid date format: {datetime_str}. "
            f"Expected formats: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, "
            f"YYYY-MM-DD,HH:MM:SS, or ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)"
        )


def is_date_only(datetime_str: Union[str, datetime, date]) -> bool:
    """
    Check if the date string contains only date (no time component).
    
    Args:
        datetime_str: Input datetime string
        
    Returns:
        True if date only, False if contains time
    """
    if not datetime_str:
        return False
    
    # Handle datetime/date objects
    if isinstance(datetime_str, datetime):
        return datetime_str.hour == 0 and datetime_str.minute == 0 and datetime_str.second == 0
    elif isinstance(datetime_str, date):
        return True
    
    # Handle string
    if not isinstance(datetime_str, str):
        return False
        
    datetime_str = datetime_str.strip()
    
    # Check if it matches date-only pattern (YYYY-MM-DD)
    # Updated to also check for ISO format with 'T'
    if 'T' in datetime_str:
        return False  # Has time component
    
    return ',' not in datetime_str and ' ' not in datetime_str


def build_date_filter(datetime_column: str, from_date: Optional[Union[str, datetime, date]], 
                     to_date: Optional[Union[str, datetime, date]]) -> Tuple[str, list]:
    """
    Build date filter conditions for ClickHouse query.

    Args:
        datetime_column: Name of the datetime column
        from_date: Start date (optional)
        to_date: End date (optional)

    Returns:
        Tuple of (condition_string, parameters_list)
    """
    conditions = []
    params = []

    if not from_date and not to_date:
        # Default: last 7 days
        conditions.append(f"`{datetime_column}` >= now() - INTERVAL 7 DAY")
        return " AND ".join(conditions), params

    try:
        # Handle from_date - convert to string format for ClickHouse
        from_datetime = None
        from_is_date_only = False
        
        if isinstance(from_date, datetime):
            from_datetime = from_date.strftime('%Y-%m-%d %H:%M:%S')
            from_is_date_only = (from_date.hour == 0 and from_date.minute == 0 and from_date.second == 0)
        elif isinstance(from_date, date):
            from_datetime = from_date.strftime('%Y-%m-%d 00:00:00')
            from_is_date_only = True
        elif from_date and isinstance(from_date, str):
            from_datetime = parse_datetime(from_date)
            from_is_date_only = is_date_only(from_date)

        # Handle to_date - convert to string format for ClickHouse
        to_datetime = None
        to_is_date_only = False
        
        if isinstance(to_date, datetime):
            to_datetime = to_date.strftime('%Y-%m-%d %H:%M:%S')
            to_is_date_only = (to_date.hour == 0 and to_date.minute == 0 and to_date.second == 0)
        elif isinstance(to_date, date):
            to_datetime = to_date.strftime('%Y-%m-%d 23:59:59')
            to_is_date_only = True
        elif to_date and isinstance(to_date, str):
            to_datetime = parse_datetime(to_date)
            to_is_date_only = is_date_only(to_date)

        if from_datetime and to_datetime:
            # Range filtering
            conditions.append(f"`{datetime_column}` >= '{from_datetime}'")
            conditions.append(f"`{datetime_column}` <= '{to_datetime}'")
        elif from_datetime:
            # From date only - check if it's a date-only or datetime
            if from_is_date_only:
                # Date only - from start of day to end of day
                end_of_day = from_datetime.replace(' 00:00:00', ' 23:59:59')
                conditions.append(f"`{datetime_column}` >= '{from_datetime}'")
                conditions.append(f"`{datetime_column}` <= '{end_of_day}'")
            else:
                # Has time component - from this time onwards
                conditions.append(f"`{datetime_column}` >= '{from_datetime}'")
        elif to_datetime:
            # To date only - check if it's a date-only or datetime
            if to_is_date_only:
                # Date only - up to end of day
                end_of_day = to_datetime.replace(' 00:00:00', ' 23:59:59')
                conditions.append(f"`{datetime_column}` <= '{end_of_day}'")
            else:
                # Has time component - up to this exact time
                conditions.append(f"`{datetime_column}` <= '{to_datetime}'")

    except Exception as e:
        logger.error(f"Error building date filter: {e}", exc_info=True)  # Added exc_info for full traceback
        # Fallback to default range if date parsing fails
        conditions.append(f"`{datetime_column}` >= now() - INTERVAL 7 DAY")
        logger.info("Applied fallback 7-day filter due to date parsing error")

    return " AND ".join(conditions), params


def get_default_date_range() -> Tuple[str, str]:
    """
    Get default date range (last 7 days).
    
    Returns:
        Tuple of (from_date, to_date) as strings
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    return (
        start_date.strftime('%Y-%m-%d %H:%M:%S'),
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    )

def parse_datetime_to_object(datetime_str: str, set_end_of_day: bool = False) -> Optional[datetime]:
    """
    Parse datetime string and return datetime object.
    NEW FUNCTION - For use in new/updated endpoints only.

    Args:
        datetime_str: Input datetime string
        set_end_of_day: If True and only date provided, set time to 23:59:59

    Returns:
        datetime object or None

    Raises:
        ValueError: If datetime format is invalid

    Examples:
        >>> parse_datetime_to_object("2024-10-30T08:58:20Z")
        datetime.datetime(2024, 10, 30, 8, 58, 20)
        
        >>> parse_datetime_to_object("2024-10-30")
        datetime.datetime(2024, 10, 30, 0, 0, 0)
        
        >>> parse_datetime_to_object("2024-10-30", set_end_of_day=True)
        datetime.datetime(2024, 10, 30, 23, 59, 59, 999999)
    """
    if not datetime_str:
        return None
    
    try:
        # Use enhanced parse_datetime with return_datetime_object=True
        dt = parse_datetime(datetime_str, return_datetime_object=True)
        
        # If only date was provided and set_end_of_day is True
        if set_end_of_day and is_date_only(datetime_str):
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return dt
    except Exception as e:
        logger.error(f"Failed to parse datetime: {datetime_str} - {e}")
        raise ValueError(
            f"Invalid datetime format: '{datetime_str}'. "
            f"Supported formats: ISO 8601 (2024-10-30T08:58:20Z), "
            f"date only (2024-10-30), or standard formats"
        )


def parse_date_range(
    from_date: Optional[str],
    to_date: Optional[str],
    default_days: int = 7
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse a date range from string parameters and return datetime objects.
    NEW FUNCTION - For use in new/updated endpoints only.

    Args:
        from_date: Start date/datetime string
        to_date: End date/datetime string
        default_days: Default number of days to use if dates not provided

    Returns:
        Tuple of (start_datetime, end_datetime) as datetime objects

    Examples:
        >>> parse_date_range("2024-10-30T08:00:00Z", "2024-10-30T18:00:00Z")
        (datetime(2024, 10, 30, 8, 0, 0), datetime(2024, 10, 30, 18, 0, 0))

        >>> parse_date_range("2024-10-30", "2024-10-31")
        (datetime(2024, 10, 30, 0, 0, 0), datetime(2024, 10, 31, 23, 59, 59, 999999))
    """
    # Parse start date
    start_dt = parse_datetime_to_object(from_date, set_end_of_day=False) if from_date else None

    # Parse end date - if only date provided (no time), set to end of day
    end_dt = parse_datetime_to_object(to_date, set_end_of_day=True) if to_date else None

    # If neither date provided, use default range
    if start_dt is None and end_dt is None:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=default_days)
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    # If only start date provided, set end to now
    elif end_dt is None and start_dt is not None:
        end_dt = datetime.now()

    # If only end date provided, set start to default_days before
    elif start_dt is None and end_dt is not None:
        start_dt = end_dt - timedelta(days=default_days)
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    return start_dt, end_dt


def validate_date_range_extended(
    from_date: Union[str, datetime, None],
    to_date: Union[str, datetime, None],
    max_days: int = 90
) -> Tuple[bool, Optional[str]]:
    """
    Validate that date range is reasonable with extended functionality.
    NEW FUNCTION - For use in new/updated endpoints only.
    
    This version accepts both strings and datetime objects and returns validation result.

    Args:
        from_date: Start date string or datetime object
        to_date: End date string or datetime object
        max_days: Maximum allowed days in range (default: 90)

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_date_range_extended("2024-10-30", "2024-10-31")
        (True, None)

        >>> validate_date_range_extended("2024-10-31", "2024-10-30")
        (False, "End date cannot be before start date")
    """
    try:
        # Convert to datetime objects if strings
        if isinstance(from_date, str):
            from_dt = parse_datetime_to_object(from_date)
        else:
            from_dt = from_date

        if isinstance(to_date, str):
            to_dt = parse_datetime_to_object(to_date)
        else:
            to_dt = to_date

        if from_dt is None or to_dt is None:
            return True, None

        # Check if end date is before start date
        if to_dt < from_dt:
            return False, "End date cannot be before start date"

        return True, None

    except Exception as e:
        logger.warning(f"Date validation error: {e}")
        return False, str(e)


def get_default_date_range_objects(days: int = 7) -> Tuple[datetime, datetime]:
    """
    Get default date range as datetime objects (last N days).
    NEW FUNCTION - For use in new/updated endpoints only.
    
    Args:
        days: Number of days to look back (default: 7)
    
    Returns:
        Tuple of (from_datetime, to_datetime) as datetime objects
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return start_date, end_date