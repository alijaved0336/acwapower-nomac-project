"""
Number formatting utilities for consistent decimal handling across the application.

This module provides centralized functions for formatting numeric values,
particularly for handling decimal precision based on the magnitude of values.
"""

import logging
import math
from typing import Optional, Union

logger = logging.getLogger(__name__)


def format_decimal_value(
    value: Union[float, int, str],
    large_value_decimals: int = 2,
    small_value_decimals: int = 4,
    threshold: float = 1.0
) -> Optional[float]:
    """
    Format a numeric value with conditional decimal precision based on magnitude.

    For values with absolute value >= threshold (default 1.0):
        Returns value rounded to large_value_decimals (default 2)
    For values with absolute value < threshold (close to zero):
        Returns value rounded to small_value_decimals (default 4)

    This provides better precision for small measurements while keeping
    larger values readable.

    Args:
        value: The numeric value to format (float, int, or string representation)
        large_value_decimals: Number of decimal places for |value| >= threshold (default: 2)
        small_value_decimals: Number of decimal places for |value| < threshold (default: 4)
        threshold: The boundary value for determining precision (default: 1.0)

    Returns:
        Formatted float value with appropriate decimal precision, or None if invalid

    Examples:
        >>> format_decimal_value(123.456789)
        123.46
        >>> format_decimal_value(0.00123456)
        0.0012
        >>> format_decimal_value(-0.5678)
        -0.5678
        >>> format_decimal_value(1.0)
        1.0
        >>> format_decimal_value(-1.5)
        -1.5
    """
    if value is None:
        return None

    try:
        # Convert to float if necessary
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            numeric_value = float(value)
        else:
            numeric_value = float(value)

        # Check for invalid float values (NaN, Inf)
        if math.isnan(numeric_value) or math.isinf(numeric_value):
            logger.warning(f"Invalid numeric value detected: {value}")
            return None

        # Determine decimal precision based on magnitude
        abs_value = abs(numeric_value)

        if abs_value >= threshold:
            # Large values: use fewer decimals for readability
            return round(numeric_value, large_value_decimals)
        else:
            # Small values (close to zero): use more decimals for precision
            return round(numeric_value, small_value_decimals)

    except (ValueError, TypeError) as e:
        logger.warning(f"Cannot convert value '{value}' to float: {e}")
        return None


def format_decimal_value_safe(
    value: Union[float, int, str, None],
    column_name: str = "unknown"
) -> Optional[float]:
    """
    Safe wrapper for format_decimal_value with additional logging context.

    Uses the application defaults:
    - 2 decimal places for values >= 1.0 or <= -1.0
    - 4 decimal places for values between -1.0 and 1.0

    Args:
        value: The numeric value to format
        column_name: Name of the column (for logging purposes)

    Returns:
        Formatted float value or None if invalid
    """
    if value is None:
        return None

    try:
        result = format_decimal_value(value)
        if result is None and value is not None:
            logger.debug(
                f"Value formatting returned None for column '{column_name}': {value}"
            )
        return result
    except Exception as e:
        logger.warning(
            f"Error formatting value for column '{column_name}': {value}, error: {e}"
        )
        return None
