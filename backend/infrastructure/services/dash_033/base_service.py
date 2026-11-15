"""
Base Service for Dashboard-033 ClickHouse Operations
Provides shared functionality for all Dashboard-033 sub-services.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from infrastructure.orm.repositories.clickhouseRepository import ClickHouseRepository
from infrastructure.exceptions import ClickHouseServiceError, InvalidColumnNameError
from constants import Dash033Config

logger = logging.getLogger(__name__)


class Dash033BaseService:
    """
    Base service class providing shared functionality for Dashboard-033 operations.
    All sub-services should inherit from this class.
    """

    def __init__(self):
        """Initialize the base service with a ClickHouse repository instance."""
        self.repository = ClickHouseRepository()

    def _normalize_site_name(self, site_name: str) -> str:
        """
        Normalize site name to standard format for database lookup.
        Uses Dash033Config.SITE_NAME_MAPPINGS for consistent naming.

        Args:
            site_name: Raw site name from user input

        Returns:
            Normalized site name

        Example:
            >>> service = Dash033BaseService()
            >>> service._normalize_site_name("rabigh3")
            'Rabigh3'
        """
        return Dash033Config.SITE_NAME_MAPPINGS.get(site_name, site_name)

    def _validate_column_names(self, columns: List[str], table_context: str = "") -> None:
        """
        Validate column names against whitelist to prevent SQL injection.

        Args:
            columns: List of column names to validate
            table_context: Context for error message (e.g., "datetime filtering")

        Raises:
            InvalidColumnNameError: If any column name is not whitelisted

        Example:
            >>> service = Dash033BaseService()
            >>> service._validate_column_names(["Train", "Start_Time"], "CIP filtering")
            # No exception raised if valid
        """
        for col in columns:
            if col and not any(
                col.lower() == pattern.lower()
                for pattern in Dash033Config.COLUMN_NAME_WHITELIST
            ):
                raise InvalidColumnNameError(
                    f"Invalid column name '{col}' in {table_context}. "
                    f"Column must match whitelist patterns."
                )

    def site_table_suffix_mappings(self, site_name: str) -> Optional[str]:
        """
        Get table suffix mapping for a site.

        Args:
            site_name: Site name identifier

        Returns:
            Table suffix for the site, or None if not found

        Example:
            >>> service = Dash033BaseService()
            >>> service.site_table_suffix_mappings("Rabigh3")
            'r3'
        """
        mappings = {
            "Rabigh3": "r3",
            "UAQ": "UAQ",
            "STPC": "STPC",
            "Jubail-Jazlah": "Jubail-Jazlah"
        }
        return mappings.get(site_name)

    def get_defaults(self, user: dict) -> str:
        """
        Get default site name based on user context.

        Args:
            user: User context dictionary

        Returns:
            Default site name from user context or 'default_site'

        Example:
            >>> service = Dash033BaseService()
            >>> user = {"site_name": "Rabigh3"}
            >>> service.get_defaults(user)
            'Rabigh3'
        """
        try:
            if user and isinstance(user, dict):
                return user.get('site_name', user.get('default_site', 'default_site'))
            return 'default_site'
        except Exception as e:
            logger.warning(f"Error getting user defaults: {e}")
            return 'default_site'

    def _get_clickhouse_table(
        self, 
        site_name: str, 
        table_suffix: str, 
        user: Optional[dict] = None
    ) -> str:
        """
        Get ClickHouse table name for a site and suffix.
        Handles site name normalization and default site resolution.

        Args:
            site_name: Site identifier
            table_suffix: Table suffix to append
            user: Optional user context for default site

        Returns:
            Full ClickHouse table name

        Raises:
            ClickHouseServiceError: If table not found

        Example:
            >>> service = Dash033BaseService()
            >>> table = service._get_clickhouse_table("Rabigh3", "r3_mode_cip")
            >>> print(table)
            'Rabigh3_r3_mode_cip'
        """
        if not site_name:
            site_name = self.get_defaults(user)

        site_name = self._normalize_site_name(site_name)
        
        clickhouse_table = self.repository.get_clickhouse_table_name(site_name, table_suffix)
        if not clickhouse_table:
            raise ClickHouseServiceError(
                f"No ClickHouse table found for site {site_name} with suffix {table_suffix}",
                context={"site_name": site_name, "table_suffix": table_suffix}
            )
        
        return clickhouse_table

    def format_items_to_columnar(self, items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Convert row-based items (list of dicts) into column-based format
        with { column_name: { "name": column_name, "data": [...] } }.

        Args:
            items: List of row dictionaries from API format

        Returns:
            Column-based dictionary in old API format

        Example:
            >>> service = Dash033BaseService()
            >>> items = [
            ...     {"Train": 1, "Duration": 2.5},
            ...     {"Train": 2, "Duration": 3.0}
            ... ]
            >>> result = service.format_items_to_columnar(items)
            >>> result["Train"]["data"]
            [1, 2]
        """
        if not items:
            return {}

        # Collect all unique keys from the first row (assuming schema is consistent)
        keys = items[0].keys()
        columnar = {key: {"name": key, "data": []} for key in keys}

        for row in items:
            for key, value in row.items():
                # Format datetime values without timezone
                if isinstance(value, datetime):
                    from infrastructure.utils.datetime_utils import DateTimeParser
                    value = DateTimeParser.format_datetime_without_timezone(value)
                elif isinstance(value, str):
                    # Check if it's a datetime string (ISO format or contains time/date keywords)
                    key_lower = key.lower()
                    is_datetime_key = (
                        key_lower in ['datetime', 'timestamp', 'start_time', 'end_time', 'created_on', 'updated_on'] or
                        'time' in key_lower or 
                        'date' in key_lower
                    )
                    
                    if is_datetime_key:
                        # Try to parse and format datetime strings
                        try:
                            from infrastructure.utils.datetime_utils import DateTimeParser
                            parsed_dt = DateTimeParser.parse_datetime(value)
                            if parsed_dt:
                                value = DateTimeParser.format_datetime_without_timezone(parsed_dt)
                        except (ValueError, TypeError):
                            pass  # keep as is if parsing fails

                # Convert all non-null numerics to string to match old format
                if isinstance(value, (int, float)) and value is not None:
                    value = f"{value:.2f}".rstrip("0").rstrip(".") if "." in f"{value:.2f}" else str(value)

                columnar[key]["data"].append(value)

        return columnar


