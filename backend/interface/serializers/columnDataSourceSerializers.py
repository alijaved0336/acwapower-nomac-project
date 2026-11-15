"""
Serializers for Column Data Source API
Handles validation and serialization for column data requests and responses.
"""
from rest_framework import serializers
from typing import List, Any


class ColumnRequestSerializer(serializers.Serializer):
    """
    Serializer for column data request payload.
    Validates individual column requests within the array.
    """
    columnName = serializers.CharField(
        max_length=200,
        help_text="Name of the column to retrieve data for",
        error_messages={
            'required': 'columnName is required',
            'max_length': 'columnName cannot exceed 200 characters',
            'blank': 'columnName cannot be blank'
        }
    )
    
    columnType = serializers.CharField(
        max_length=50,
        help_text="Data type of the column (e.g., 'double', 'string', 'timestamp')",
        error_messages={
            'required': 'columnType is required',
            'max_length': 'columnType cannot exceed 50 characters',
            'blank': 'columnType cannot be blank'
        }
    )
    
    tableName = serializers.CharField(
        max_length=100,
        help_text="Name of the table containing the column",
        error_messages={
            'required': 'tableName is required',
            'max_length': 'tableName cannot exceed 100 characters',
            'blank': 'tableName cannot be blank'
        }
    )
    
    siteName = serializers.CharField(
        max_length=100,
        help_text="Name of the site containing the table",
        error_messages={
            'required': 'siteName is required',
            'max_length': 'siteName cannot exceed 100 characters',
            'blank': 'siteName cannot be blank'
        }
    )

    def validate(self, data):
        """
        Perform cross-field validation on the column request.
        """
        # Remove any leading/trailing whitespace
        for field in ['columnName', 'columnType', 'tableName', 'siteName']:
            if field in data:
                data[field] = data[field].strip()
        
        # Validate that none of the required fields are empty after stripping
        for field in ['columnName', 'columnType', 'tableName', 'siteName']:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} cannot be empty")
        
        # Additional validation for column name format
        column_name = data.get('columnName', '')
        if any(char in column_name for char in ['<', '>', '"', "'", '&', ';']):
            raise serializers.ValidationError(
                "columnName contains invalid characters. Avoid: < > \" ' & ;"
            )
        
        return data


class ColumnResponseSerializer(serializers.Serializer):
    """
    Serializer for column data response.
    Documents the expected response structure.
    """
    columnName = serializers.CharField(
        help_text="Name of the column"
    )
    
    columnType = serializers.CharField(
        help_text="Data type of the column"
    )
    
    tableName = serializers.CharField(
        help_text="Name of the table containing the column"
    )
    
    siteName = serializers.CharField(
        help_text="Name of the site containing the table"
    )
    
    dataSource = serializers.ListField(
        child=serializers.CharField(allow_null=True, allow_blank=True),
        help_text="Array containing the actual column data values",
        allow_empty=True
    )


class ColumnDataSourceRequestSerializer(serializers.Serializer):
    """
    Serializer for the complete request payload (array of column requests).
    Validates the entire request structure.
    """
    def to_internal_value(self, data):
        """
        Handle array input validation.
        Expects data to be a list of column request objects.
        """
        if not isinstance(data, list):
            raise serializers.ValidationError(
                "Request payload must be an array of column requests"
            )
        
        if len(data) == 0:
            raise serializers.ValidationError(
                "Request payload cannot be empty"
            )
        
        if len(data) > 100:  # Reasonable limit for performance
            raise serializers.ValidationError(
                "Request payload cannot contain more than 100 column requests"
            )
        
        # Validate each item in the array
        validated_data = []
        errors = {}
        
        for index, item in enumerate(data):
            item_serializer = ColumnRequestSerializer(data=item)
            if item_serializer.is_valid():
                validated_data.append(item_serializer.validated_data)
            else:
                errors[f"item_{index}"] = item_serializer.errors
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return validated_data


class ColumnDataSourceResponseSerializer(serializers.Serializer):
    """
    Serializer for the complete response (array of column responses).
    Documents the expected response structure.
    """
    def to_representation(self, instance):
        """
        Handle array output serialization.
        Expects instance to be a list of ColumnResponse objects.
        """
        if not isinstance(instance, list):
            return []
        
        result = []
        for item in instance:
            if hasattr(item, 'to_dict'):
                # If it's a ColumnResponse object
                result.append(item.to_dict())
            elif isinstance(item, dict):
                # If it's already a dictionary
                result.append(item)
            else:
                # Fallback serialization
                serializer = ColumnResponseSerializer(item)
                result.append(serializer.data)
        
        return result


class DateTimeParameterSerializer(serializers.Serializer):
    """
    Serializer for DateTime and rack filter query parameters validation.
    Handles the comma-separated format and validation.
    """
    from_date = serializers.CharField(
        required=False,
        help_text="Start date/time in format 'YYYY-MM-DD,HH:MM:SS' or 'YYYY-MM-DD'. "
                  "If only from_date is provided, performs exact match filtering.",
        error_messages={
            'invalid': 'from_date must be in format YYYY-MM-DD,HH:MM:SS or YYYY-MM-DD'
        }
    )
    
    to_date = serializers.CharField(
        required=False,
        help_text="End date/time in format 'YYYY-MM-DD,HH:MM:SS' or 'YYYY-MM-DD'. "
                  "If only to_date is provided, performs exact match filtering.",
        error_messages={
            'invalid': 'to_date must be in format YYYY-MM-DD,HH:MM:SS or YYYY-MM-DD'
        }
    )
    
    rack = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,  # Increased to support multiple comma-separated racks
        help_text="Filter records by rack/trailer value. Supports single rack (e.g., 'rack_02') or "
                  "comma-separated multiple racks (e.g., 'rack_02,rack_03,rack_05'). "
                  "Will filter on 'rack' column if available, otherwise on 'trailer' column if available. "
                  "Multiple racks use OR logic (matches ANY specified rack).",
        error_messages={
            'max_length': 'rack parameter cannot exceed 500 characters'
        }
    )

    def validate_from_date(self, value):
        """Validate from_date format."""
        if value:
            return self._validate_datetime_format(value, 'from_date')
        return value

    def validate_to_date(self, value):
        """Validate to_date format."""
        if value:
            return self._validate_datetime_format(value, 'to_date')
        return value

    def _validate_datetime_format(self, value, field_name):
        """
        Validate datetime format supports comma-separated format.
        """
        import re
        from datetime import datetime
        
        # Clean the input
        cleaned_value = value.strip()
        
        # Check for comma-separated format
        if ',' in cleaned_value:
            parts = cleaned_value.split(',')
            if len(parts) != 2:
                raise serializers.ValidationError(
                    f"{field_name} with comma must have exactly one comma separating date and time"
                )
            
            date_part = parts[0].strip()
            time_part = parts[1].strip()
            
            # Validate date part (YYYY-MM-DD)
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_part):
                raise serializers.ValidationError(
                    f"{field_name} date part must be in YYYY-MM-DD format"
                )
            
            # Validate time part (HH:MM:SS)
            if not re.match(r'^\d{2}:\d{2}:\d{2}$', time_part):
                raise serializers.ValidationError(
                    f"{field_name} time part must be in HH:MM:SS format"
                )
            
            # Validate actual date values
            try:
                datetime.strptime(date_part, '%Y-%m-%d')
                datetime.strptime(time_part, '%H:%M:%S')
            except ValueError as e:
                raise serializers.ValidationError(
                    f"{field_name} contains invalid date/time values: {str(e)}"
                )
        
        else:
            # Check for date-only format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', cleaned_value):
                try:
                    datetime.strptime(cleaned_value, '%Y-%m-%d')
                except ValueError as e:
                    raise serializers.ValidationError(
                        f"{field_name} contains invalid date: {str(e)}"
                    )
            
            # Check for standard datetime format
            elif re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', cleaned_value):
                try:
                    datetime.strptime(cleaned_value, '%Y-%m-%d %H:%M:%S')
                except ValueError as e:
                    raise serializers.ValidationError(
                        f"{field_name} contains invalid datetime: {str(e)}"
                    )
            
            else:
                raise serializers.ValidationError(
                    f"{field_name} must be in format 'YYYY-MM-DD,HH:MM:SS', 'YYYY-MM-DD HH:MM:SS', or 'YYYY-MM-DD'"
                )
        
        return cleaned_value

    def validate_rack(self, value):
        """
        Validate rack parameter format.
        Supports single rack or comma-separated multiple racks.
        """
        if value:
            # Clean the input
            cleaned_value = value.strip()

            # Split by comma and validate each rack value
            rack_values = [rack.strip() for rack in cleaned_value.split(',') if rack.strip()]

            # Validate the list is not empty
            if not rack_values:
                raise serializers.ValidationError(
                    "rack parameter cannot be empty after parsing"
                )

            # Validate each rack value individually
            for rack in rack_values:
                # Check for potentially dangerous characters in each rack
                if any(char in rack for char in ['<', '>', '"', "'", '&', ';', '\\', '/']):
                    raise serializers.ValidationError(
                        f"rack value '{rack}' contains invalid characters. Avoid: < > \" ' & ; \\ /"
                    )

                # Check rack value length
                if len(rack) > 50:
                    raise serializers.ValidationError(
                        f"rack value '{rack}' cannot exceed 50 characters"
                    )

            # Validate total number of racks
            if len(rack_values) > 20:
                raise serializers.ValidationError(
                    "Cannot specify more than 20 rack values"
                )

            return cleaned_value
        return value

    def validate(self, data):
        """
        Cross-field validation for datetime and rack parameters.
        """
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        rack = data.get('rack')
        
        # Both dates provided - range filtering
        if from_date and to_date:
            # Additional validation can be added here for range logic
            pass
        
        # Only one date provided - exact match filtering
        elif from_date or to_date:
            # This is valid for exact match scenarios
            pass
        
        # No dates provided - will use default 7-day range
        else:
            # This is also valid
            pass
        
        # Rack filtering is optional and can be combined with any date filtering mode
        if rack:
            # Additional rack validation can be added here if needed
            pass
        
        return data


# Example data for Swagger documentation
EXAMPLE_COLUMN_REQUEST = {
    "columnName": "INL_FL_TO_DMPF_12_MES",
    "columnType": "double",
    "tableName": "Jubail_Chemicals_ppm", 
    "siteName": "Jubail-Jazlah"
}

EXAMPLE_COLUMN_RESPONSE = {
    "columnName": "INL_FL_TO_DMPF_12_MES",
    "columnType": "double",
    "tableName": "Jubail_Chemicals_ppm",
    "siteName": "Jubail-Jazlah",
    "dataSource": ["1.25", "1.87", "2.34", "1.92"]
}

EXAMPLE_REQUEST_PAYLOAD = [
    {
        "columnName": "INL_FL_TO_DMPF_12_MES",
        "columnType": "double",
        "tableName": "Jubail_Chemicals_ppm",
        "siteName": "Jubail-Jazlah"
    },
    {
        "columnName": "INL_FL_TO_DMPF_13_MES", 
        "columnType": "double",
        "tableName": "Jubail_Chemicals_ppm",
        "siteName": "Jubail-Jazlah"
    }
]

EXAMPLE_RESPONSE_PAYLOAD = [
    {
        "columnName": "INL_FL_TO_DMPF_12_MES",
        "columnType": "double", 
        "tableName": "Jubail_Chemicals_ppm",
        "siteName": "Jubail-Jazlah",
        "dataSource": ["1.25", "1.87", "2.34", "1.92"]
    },
    {
        "columnName": "INL_FL_TO_DMPF_13_MES",
        "columnType": "double",
        "tableName": "Jubail_Chemicals_ppm", 
        "siteName": "Jubail-Jazlah",
        "dataSource": ["2.45", "3.21", "2.78", "3.15"]
    }
]