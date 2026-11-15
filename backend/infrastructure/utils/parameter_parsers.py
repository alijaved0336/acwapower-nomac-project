"""
Parameter parsing utilities for common API parameter handling.
Provides reusable functions for parsing and validating API parameters.
"""
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ParameterParsers:
    """
    Utility class for parsing and validating common API parameters.
    """

    @staticmethod
    def parse_rack_parameter(rack_param: Optional[str]) -> List[str]:
        """
        Parse comma-separated rack parameter into a list of rack values.

        This utility handles the common pattern of supporting both single rack
        values and comma-separated multiple rack values in API endpoints.

        Args:
            rack_param: Single rack value or comma-separated rack values

        Returns:
            List of cleaned rack values, empty list if None or empty

        Examples:
            "rack_02" -> ["rack_02"]
            "rack_02,rack_03,rack_05" -> ["rack_02", "rack_03", "rack_05"]
            "rack_02, rack_03 , rack_05" -> ["rack_02", "rack_03", "rack_05"]
            None -> []
            "" -> []
            "  " -> []
        """
        if not rack_param or not rack_param.strip():
            return []

        # Split by comma and clean up whitespace, filter empty values
        rack_values = [
            rack.strip()
            for rack in rack_param.split(',')
            if rack.strip()
        ]

        logger.debug(f"[PARAMETER_PARSER] Parsed rack parameter '{rack_param}' into: {rack_values}")
        return rack_values

    @staticmethod
    def validate_rack_list(rack_list: List[str], max_racks: int = 50) -> List[str]:
        """
        Validate and clean a list of rack values.

        Args:
            rack_list: List of rack values to validate
            max_racks: Maximum number of racks allowed (default: 50)

        Returns:
            Validated and cleaned list of rack values

        Raises:
            ValueError: If validation fails
        """
        if not rack_list:
            return []

        # Remove duplicates while preserving order
        validated_racks = []
        seen = set()

        for rack in rack_list:
            if not rack or not rack.strip():
                continue

            cleaned_rack = rack.strip()

            # Check for reasonable rack name length
            if len(cleaned_rack) > 50:
                logger.warning(f"[PARAMETER_PARSER] Rack name too long, truncating: {cleaned_rack[:50]}...")
                cleaned_rack = cleaned_rack[:50]

            if cleaned_rack not in seen:
                validated_racks.append(cleaned_rack)
                seen.add(cleaned_rack)

        # Check maximum number of racks
        if len(validated_racks) > max_racks:
            raise ValueError(f"Too many rack filters specified. Maximum {max_racks} allowed, got {len(validated_racks)}")

        logger.debug(f"[PARAMETER_PARSER] Validated {len(validated_racks)} unique racks from {len(rack_list)} input values")
        return validated_racks