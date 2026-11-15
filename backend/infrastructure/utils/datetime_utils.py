import logging
from datetime import datetime
from typing import Optional, Union
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)


class DateTimeParser:
    """
    Unified datetime parser that handles multiple datetime formats.
    Supports: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, ISO 8601 (YYYY-MM-DDTHH:MM:SS), and more.
    """
    
    # Common datetime formats to try in order of preference
    DATETIME_FORMATS = [
        '%Y-%m-%d',                    # 2025-10-14
        '%Y-%m-%d %H:%M:%S',          # 2025-10-14 20:16:22
        '%Y-%m-%dT%H:%M:%S',          # 2025-10-14T20:16:22
        '%Y-%m-%dT%H:%M:%SZ',         # 2025-10-14T20:16:22Z
        '%Y-%m-%dT%H:%M:%S.%f',       # 2025-10-14T20:16:22.123456
        '%Y-%m-%dT%H:%M:%S.%fZ',      # 2025-10-14T20:16:22.123456Z
        '%Y-%m-%d,%H:%M:%S',          # 2025-10-14,20:16:22
    ]

    @staticmethod
    def parse_datetime(
        date_string: Union[str, datetime, None],
        default: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Parse a datetime string into a datetime object.
        Handles multiple formats gracefully.
        
        Args:
            date_string: The date/datetime string to parse, or datetime object, or None
            default: Default value to return if parsing fails
            
        Returns:
            datetime object or default value if parsing fails
        """
        if date_string is None:
            return default
            
        # If already a datetime object, return as-is
        if isinstance(date_string, datetime):
            return date_string
            
        # Convert to string if not already
        date_str = str(date_string).strip()
        
        if not date_str:
            return default
        
        # Try each format explicitly first (faster for common formats)
        for fmt in DateTimeParser.DATETIME_FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Fall back to dateutil parser (more flexible but slower)
        try:
            # Remove 'Z' suffix if present for better compatibility
            date_str_clean = date_str.replace('Z', '+00:00') if date_str.endswith('Z') else date_str
            parsed_dt = dateutil_parser.parse(date_str_clean)
            logger.debug(f"Successfully parsed datetime using dateutil: {date_str} -> {parsed_dt}")
            return parsed_dt
        except (ValueError, TypeError, dateutil_parser.ParserError) as e:
            logger.warning(f"Failed to parse datetime string '{date_str}': {e}")
            return default
    
    @staticmethod
    def parse_datetime_safe(
        date_string: Union[str, datetime, None],
        fallback: Optional[datetime] = None,
        raise_on_error: bool = False
    ) -> Optional[datetime]:
        """
        Safe datetime parsing with optional error raising.
        
        Args:
            date_string: The date/datetime string to parse
            fallback: Fallback value if parsing fails
            raise_on_error: If True, raise ValueError on parsing failure
            
        Returns:
            datetime object or fallback value
            
        Raises:
            ValueError: If raise_on_error is True and parsing fails
        """
        result = DateTimeParser.parse_datetime(date_string, fallback)
        
        if result is None and raise_on_error and date_string is not None:
            raise ValueError(
                f"Unable to parse datetime from '{date_string}'. "
                f"Expected formats: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, "
                f"YYYY-MM-DDTHH:MM:SS, or ISO 8601 format"
            )
        
        return result
    
    @staticmethod
    def format_datetime(
        dt: Union[datetime, str, None],
        output_format: str = '%Y-%m-%d %H:%M:%S'
    ) -> Optional[str]:
        """
        Format a datetime object or string to a specific format.
        
        Args:
            dt: datetime object or string to format
            output_format: Target format string
            
        Returns:
            Formatted datetime string or None
        """
        if dt is None:
            return None
            
        # Parse if string
        if isinstance(dt, str):
            dt = DateTimeParser.parse_datetime(dt)
            if dt is None:
                return None
        
        try:
            return dt.strftime(output_format)
        except Exception as e:
            logger.warning(f"Error formatting datetime {dt}: {e}")
            return None
    
    @staticmethod
    def to_date_only(dt: Union[datetime, str, None]) -> Optional[str]:
        """Convert datetime to YYYY-MM-DD format."""
        return DateTimeParser.format_datetime(dt, '%Y-%m-%d')
    
    @staticmethod
    def to_iso_format(dt: Union[datetime, str, None]) -> Optional[str]:
        """Convert datetime to ISO 8601 format (YYYY-MM-DDTHH:MM:SS) without timezone."""
        if dt is None:
            return None
        
        # Parse if string
        if isinstance(dt, str):
            dt = DateTimeParser.parse_datetime(dt)
            if dt is None:
                return None
        
        # Remove timezone info if present
        if dt.tzinfo is not None:
            # Convert to naive datetime (local time)
            dt = dt.replace(tzinfo=None)
        
        try:
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
        except Exception as e:
            logger.warning(f"Error formatting datetime {dt}: {e}")
            return None
    
    @staticmethod
    def format_datetime_without_timezone(dt: Union[datetime, str, None]) -> Optional[str]:
        """
        Format datetime to YYYY-MM-DDTHH:MM:SS without timezone information.
        This is the preferred method for API responses.
        
        Args:
            dt: datetime object or string to format
            
        Returns:
            Formatted datetime string without timezone (e.g., '2025-11-10T12:01:36') or None
        """
        return DateTimeParser.to_iso_format(dt)


# Convenience function for backward compatibility
def parse_datetime_flexible(date_string: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Legacy wrapper for DateTimeParser.parse_datetime.
    Handles multiple datetime formats.
    """
    return DateTimeParser.parse_datetime(date_string)