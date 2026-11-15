"""
Serializers for ClickHouse API endpoints.
Handles validation and serialization for ClickHouse requests and responses.
"""
from rest_framework import serializers
from datetime import datetime, timedelta, timezone
from typing import List, Any
import re


class ClickHouseQueryParamsSerializer(serializers.Serializer):
    """
    Serializer for query parameters in ClickHouse column data requests.
    Handles flexible start_date, end_date, and racks filtering parameters with multiple datetime formats.
    
    DateTime Filtering Modes:
    - Range Filtering: When both start_date and end_date are provided
    - Exact Match: When only one date parameter is provided
    - Default Range: When no dates are provided (last 7 days)
    
    DateTime Formats Supported:
    - Comma-separated: 2025-06-01,10:00:00
    - Standard: 2025-06-01 10:00:00
    - Date-only: 2025-06-01
    - ISO format: 2025-04-03T00:59:00Z
    """
    start_date = serializers.CharField(
        required=False,
        help_text="Start date for filtering data (supports multiple formats: '2025-06-01,10:00:00', '2025-06-01 10:00:00', '2025-06-01', '2025-04-03T00:59:00Z')",
        error_messages={
            'invalid': 'Invalid date format. Supported formats: comma-separated, standard, date-only, or ISO format'
        }
    )

    end_date = serializers.CharField(
        required=False,
        help_text="End date for filtering data (supports multiple formats: '2025-06-01,10:00:00', '2025-06-01 10:00:00', '2025-06-01', '2025-04-03T00:59:00Z')",
        error_messages={
            'invalid': 'Invalid date format. Supported formats: comma-separated, standard, date-only, or ISO format'
        }
    )

    racks = serializers.CharField(
        required=False,
        max_length=1000,
        help_text="Comma-separated list of rack names for filtering",
        error_messages={
            'max_length': 'Racks parameter cannot exceed 1000 characters'
        }
    )

    def validate_start_date(self, value):
        """
        Parse and validate start_date with flexible format support.
        """
        if not value:
            return None
        
        try:
            return self._parse_flexible_datetime(value.strip())
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid start_date format: {str(e)}")

    def validate_end_date(self, value):
        """
        Parse and validate end_date with flexible format support.
        """
        if not value:
            return None
        
        try:
            return self._parse_flexible_datetime(value.strip())
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid end_date format: {str(e)}")

    def validate_racks(self, value):
        """
        Convert comma-separated racks string to list and validate.
        """
        if not value:
            return []
        
        # Split by comma and clean up whitespace
        racks_list = [rack.strip() for rack in value.split(',') if rack.strip()]
        
        if not racks_list:
            return []
            
        # Validate each rack name
        for rack in racks_list:
            # Basic validation for rack name format
            if not re.match(r'^[a-zA-Z0-9_-]+$', rack):
                raise serializers.ValidationError(
                    f"Invalid rack name '{rack}'. Rack names must contain only alphanumeric characters, underscores, and hyphens"
                )
        
        # Limit number of racks
        if len(racks_list) > 100:
            raise serializers.ValidationError(
                "Maximum 100 racks allowed per request"
            )
            
        return racks_list

    def validate(self, data):
        """
        Cross-field validation and datetime filtering mode determination.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Determine filtering mode and apply defaults
        filtering_mode, processed_start_date, processed_end_date = self._determine_filtering_mode(start_date, end_date)
        
        # Update data with processed dates and mode
        data['start_date'] = processed_start_date
        data['end_date'] = processed_end_date
        data['filtering_mode'] = filtering_mode
        
        # Validate date range if both dates are provided
        if processed_start_date and processed_end_date:
            if processed_start_date >= processed_end_date:
                raise serializers.ValidationError(
                    "start_date must be earlier than end_date"
                )
                
            # Check for reasonable date range (e.g., not more than 5 years)
            date_diff = processed_end_date - processed_start_date
            if date_diff.days > 1825:  # 5 years
                raise serializers.ValidationError(
                    "Date range cannot exceed 5 years"
                )
        
        return data

    def _parse_flexible_datetime(self, date_string: str) -> datetime:
        """
        Parse datetime string with support for multiple formats.
        
        Supported formats:
        - Comma-separated: 2025-06-01,10:00:00
        - Standard: 2025-06-01 10:00:00
        - Date-only: 2025-06-01
        - ISO format: 2025-04-03T00:59:00Z
        
        Args:
            date_string: The date string to parse
            
        Returns:
            datetime: Parsed datetime object (UTC timezone)
            
        Raises:
            ValueError: If the date string cannot be parsed
        """
        if not date_string:
            raise ValueError("Empty date string")
        
        # Remove any extra whitespace
        date_string = date_string.strip()
        
        # Handle comma-separated format (2025-06-01,10:00:00)
        if ',' in date_string and ' ' not in date_string:
            date_string = date_string.replace(',', ' ')
        
        # List of format patterns to try
        format_patterns = [
            # ISO format with timezone
            ('%Y-%m-%dT%H:%M:%SZ', lambda dt: dt.replace(tzinfo=timezone.utc)),
            ('%Y-%m-%dT%H:%M:%S.%fZ', lambda dt: dt.replace(tzinfo=timezone.utc)),
            ('%Y-%m-%dT%H:%M:%S%z', lambda dt: dt),
            
            # ISO format without timezone
            ('%Y-%m-%dT%H:%M:%S', lambda dt: dt.replace(tzinfo=timezone.utc)),
            ('%Y-%m-%dT%H:%M', lambda dt: dt.replace(tzinfo=timezone.utc)),
            
            # Standard format
            ('%Y-%m-%d %H:%M:%S', lambda dt: dt.replace(tzinfo=timezone.utc)),
            ('%Y-%m-%d %H:%M', lambda dt: dt.replace(tzinfo=timezone.utc)),
            
            # Date only (assume midnight UTC)
            ('%Y-%m-%d', lambda dt: dt.replace(tzinfo=timezone.utc)),
        ]
        
        # Try each format pattern
        for pattern, timezone_handler in format_patterns:
            try:
                parsed_dt = datetime.strptime(date_string, pattern)
                return timezone_handler(parsed_dt)
            except ValueError:
                continue
        
        # Try fromisoformat as fallback
        try:
            parsed_dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            return parsed_dt
        except:
            pass
        
        # If all parsing attempts fail
        raise ValueError(
            f"Unable to parse date '{date_string}'. "
            f"Supported formats: '2025-06-01,10:00:00', '2025-06-01 10:00:00', "
            f"'2025-06-01', '2025-04-03T00:59:00Z'"
        )

    def _determine_filtering_mode(self, start_date, end_date):
        """
        Determine the filtering mode and apply appropriate defaults.
        
        Args:
            start_date: Parsed start date or None
            end_date: Parsed end date or None
            
        Returns:
            tuple: (filtering_mode, processed_start_date, processed_end_date)
        """
        current_utc = datetime.now(timezone.utc)
        
        if start_date is not None and end_date is not None:
            # Range Filtering: Both dates provided
            return 'range', start_date, end_date
            
        elif start_date is not None and end_date is None:
            # Exact Match: Only start_date provided
            # For exact match, we'll use the entire day of the start_date
            start_of_day = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return 'exact', start_of_day, end_of_day
            
        elif start_date is None and end_date is not None:
            # Exact Match: Only end_date provided
            # For exact match, we'll use the entire day of the end_date
            start_of_day = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return 'exact', start_of_day, end_of_day
            
        else:
            # Default Range: No dates provided (last 7 days)
            end_date = current_utc
            start_date = current_utc - timedelta(days=7)
            return 'default', start_date, end_date


class ColumnSpecSerializer(serializers.Serializer):
    """
    Serializer for individual column specification.
    Validates columnName, columnType, tableName, and siteName for data retrieval.
    """
    columnName = serializers.CharField(
        max_length=255,
        help_text="Name of the column to retrieve data from",
        error_messages={
            'required': 'columnName is required',
            'max_length': 'columnName cannot exceed 255 characters',
            'blank': 'columnName cannot be blank'
        }
    )

    columnType = serializers.CharField(
        max_length=100,
        help_text="Data type of the column (e.g., double, string, int)",
        error_messages={
            'required': 'columnType is required',
            'max_length': 'columnType cannot exceed 100 characters',
            'blank': 'columnType cannot be blank'
        }
    )

    tableName = serializers.CharField(
        max_length=255,
        help_text="Name of the table containing the column",
        error_messages={
            'required': 'tableName is required',
            'max_length': 'tableName cannot exceed 255 characters',
            'blank': 'tableName cannot be blank'
        }
    )

    siteName = serializers.CharField(
        max_length=255,
        help_text="Name of the site (currently for future use)",
        error_messages={
            'required': 'siteName is required',
            'max_length': 'siteName cannot exceed 255 characters',
            'blank': 'siteName cannot be blank'
        }
    )

    def validate_tableName(self, value):
        """
        Validate table name format to prevent SQL injection.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError("tableName cannot be empty")

        # Basic validation for table name format
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "tableName must contain only alphanumeric characters, underscores, and hyphens"
            )

        return value

    def validate_columnName(self, value):
        """
        Validate column name format to prevent SQL injection.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError("columnName cannot be empty")

        # Basic validation for column name format
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "columnName must contain only alphanumeric characters and underscores"
            )

        return value

    def validate_columnType(self, value):
        """
        Validate column type format.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError("columnType cannot be empty")

        # List of common ClickHouse data types (can be extended)
        valid_types = [
            'int8', 'int16', 'int32', 'int64', 'int',
            'uint8', 'uint16', 'uint32', 'uint64', 'uint',
            'float32', 'float64', 'float', 'double',
            'string', 'fixedstring', 'uuid',
            'date', 'datetime', 'datetime64',
            'boolean', 'bool',
            'array', 'tuple', 'nullable'
        ]

        # Allow for basic type validation (case insensitive)
        value_lower = value.lower()
        is_valid_type = any(valid_type in value_lower for valid_type in valid_types)

        if not is_valid_type:
            # For now, just warn but don't reject - allow any string
            pass

        return value

    def validate_siteName(self, value):
        """
        Validate site name format.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError("siteName cannot be empty")

        # Basic validation for site name format
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "siteName must contain only alphanumeric characters, underscores, and hyphens"
            )

        return value

    def validate(self, data):
        """
        Perform cross-field validation on the column specification.
        """
        # Remove any leading/trailing whitespace
        for field in ['columnName', 'columnType', 'tableName', 'siteName']:
            if field in data:
                data[field] = data[field].strip()

        # Additional validation for SQL injection prevention
        table_name = data.get('tableName', '')
        column_name = data.get('columnName', '')

        # Check for potentially dangerous SQL characters
        dangerous_chars = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
        for char in dangerous_chars:
            if char.upper() in table_name.upper() or char.upper() in column_name.upper():
                raise serializers.ValidationError(
                    f"Invalid characters detected in table or column name: {char}"
                )

        return data


class ColumnDataRequestSerializer(serializers.ListSerializer):
    """
    Serializer for the complete column data request payload as a direct array.
    Validates the array of column specifications.
    """
    child = ColumnSpecSerializer()
    min_length = 1
    max_length = 50

    def validate(self, value):
        """
        Additional validation for the columns array.
        """
        if not value:
            raise serializers.ValidationError("Request array cannot be empty")

        if len(value) > 50:
            raise serializers.ValidationError(
                "Maximum 50 column specifications allowed per request"
            )

        # Check for duplicate table-column combinations
        seen_combinations = set()
        for i, column_spec in enumerate(value):
            table_name = column_spec.get('tableName', '')
            column_name = column_spec.get('columnName', '')
            combination = f"{table_name}.{column_name}"

            if combination in seen_combinations:
                raise serializers.ValidationError(
                    f"Duplicate column specification found: {table_name}.{column_name}"
                )
            seen_combinations.add(combination)

        return value


class ColumnDataResultSerializer(serializers.Serializer):
    """
    Serializer for individual column data result.
    Used for response documentation and validation.
    """
    columnName = serializers.CharField(
        help_text="Name of the column"
    )
    columnType = serializers.CharField(
        help_text="Data type of the column"
    )
    tableName = serializers.CharField(
        help_text="Name of the table"
    )
    siteName = serializers.CharField(
        help_text="Name of the site"
    )
    dataSource = serializers.ListField(
        help_text="Array of actual column data values"
    )


class ColumnDataResponseSerializer(serializers.Serializer):
    """
    Serializer for the complete column data response payload.
    """
    success = serializers.BooleanField(
        help_text="Whether the request was successful"
    )
    message = serializers.CharField(
        help_text="Success or error message"
    )
    data = ColumnDataResultSerializer(
        many=True,
        help_text="Array of column data results"
    )


class ClickHouseValidationErrorSerializer(serializers.Serializer):
    """
    Serializer for detailed validation error responses.
    """
    field = serializers.CharField(
        help_text="Name of the field that failed validation"
    )
    message = serializers.CharField(
        help_text="Validation error message"
    )
    index = serializers.IntegerField(
        required=False,
        help_text="Index of the item in array that failed validation"
    )