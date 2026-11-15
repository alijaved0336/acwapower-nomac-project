"""
Serializers for Rack API
Handles validation and serialization for rack requests and responses.
"""
from rest_framework import serializers
from typing import List, Any, Optional


class RackRequestSerializer(serializers.Serializer):
    """
    Serializer for individual rack request payload.
    Validates individual rack requests within the array.
    """
    siteName = serializers.CharField(
        max_length=100,
        help_text="Name of the site containing the table",
        error_messages={
            'required': 'siteName is required',
            'max_length': 'siteName cannot exceed 100 characters',
            'blank': 'siteName cannot be blank'
        }
    )
    
    tableName = serializers.CharField(
        max_length=100,
        help_text="Name of the table to get racks for",
        error_messages={
            'required': 'tableName is required',
            'max_length': 'tableName cannot exceed 100 characters',
            'blank': 'tableName cannot be blank'
        }
    )

    def validate(self, data):
        """
        Perform cross-field validation on the rack request.
        """
        # Remove any leading/trailing whitespace
        for field in ['siteName', 'tableName']:
            if field in data:
                data[field] = data[field].strip()
        
        # Validate that none of the required fields are empty after stripping
        for field in ['siteName', 'tableName']:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} cannot be empty")
        
        # Additional validation for site and table name format
        site_name = data.get('siteName', '')
        table_name = data.get('tableName', '')
        
        if any(char in site_name for char in ['<', '>', '"', "'", '&', ';']):
            raise serializers.ValidationError(
                "siteName contains invalid characters. Avoid: < > \" ' & ;"
            )
        
        if any(char in table_name for char in ['<', '>', '"', "'", '&', ';']):
            raise serializers.ValidationError(
                "tableName contains invalid characters. Avoid: < > \" ' & ;"
            )
        
        return data


class RackResponseSerializer(serializers.Serializer):
    """
    Serializer for individual rack response.
    """
    rackLabel = serializers.CharField(
        help_text="Label of the rack"
    )
    siteName = serializers.CharField(
        help_text="Name of the site containing the rack"
    )
    tableName = serializers.CharField(
        help_text="Name of the table containing the rack"
    )
    rackValue = serializers.CharField(
        help_text="Value of the rack"
    )


class RackRequestListSerializer(serializers.Serializer):
    """
    Serializer for the complete request payload (array of rack requests).
    Validates the entire request structure.
    """
    def to_internal_value(self, data):
        """
        Handle array input validation.
        Expects data to be a list of rack request objects.
        """
        if not isinstance(data, list):
            raise serializers.ValidationError(
                "Request payload must be an array of rack requests"
            )
        
        if len(data) == 0:
            raise serializers.ValidationError(
                "Request payload cannot be empty"
            )
        
        if len(data) > 10:  # Reasonable limit for performance
            raise serializers.ValidationError(
                "Request payload cannot contain more than 10 rack requests"
            )
        
        # Validate each item in the array
        validated_data = []
        errors = {}
        
        for index, item in enumerate(data):
            item_serializer = RackRequestSerializer(data=item)
            if item_serializer.is_valid():
                validated_data.append(item_serializer.validated_data)
            else:
                errors[f"item_{index}"] = item_serializer.errors
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return validated_data


class RackResponseListSerializer(serializers.Serializer):
    """
    Serializer for the complete response payload.
    """
    success = serializers.BooleanField(
        help_text="Indicates if the request was successful"
    )
    message = serializers.CharField(
        help_text="Response message"
    )
    data = RackResponseSerializer(
        many=True,
        help_text="Array of rack data",
        allow_empty=True
    )

class RackFilterSerializer(serializers.Serializer):
    """
    Serializer for handling rack filtering parameters.
    Converts comma-separated rack string to list for processing.
    """
    racks = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Comma-separated rack IDs (e.g., '1,2,3')"
    )
    modes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Comma-separated mode values (e.g., 'Production,Maintenance,CIP')"
    )
    site_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Site name identifier"
    )
    start_date = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Start date and time"
    )
    end_date = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="End date and time"
    )
    page = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text="Page number (default: 1)"
    )
    limit = serializers.IntegerField(
        required=False,
        default=25,
        min_value=1,
        max_value=1000,
        help_text="Items per page (default: 25, max: 1000)"
    )
    col_pre = serializers.CharField(
        required=False,
        default="AVG_Salt_Passage_Normalized_Pre",
        help_text="Column Pre (First Column)"
    )
    col_post = serializers.CharField(
        required=False,
        default="AVG_Salt_Passage_Normalized_Post",
        help_text="Column Post (Second Column)"
    )

    def validate_racks(self, value: str) -> Optional[List[str]]:
        """
        Convert comma-separated racks string to list.
        Returns None if empty or invalid.
        """
        if not value or not value.strip():
            return None
        
        try:
            # Split by comma and clean each rack ID
            racks_list = [rack.strip() for rack in value.split(',') if rack.strip()]
            
            if not racks_list:
                return None
            
            # Validate that all rack IDs are non-empty
            for rack in racks_list:
                if not rack:
                    raise serializers.ValidationError("Rack IDs cannot be empty")
            
            return racks_list
            
        except Exception as e:
            raise serializers.ValidationError(f"Invalid racks format: {str(e)}")

    def validate_modes(self, value: str) -> Optional[List[str]]:
        """
        Convert comma-separated modes string to list.
        Returns None if empty or invalid.
        """
        if not value or not value.strip():
            return None
        
        try:
            # Split by comma and clean each mode
            modes_list = [mode.strip() for mode in value.split(',') if mode.strip()]
            
            if not modes_list:
                return None
            
            # Validate that all modes are non-empty
            for mode in modes_list:
                if not mode:
                    raise serializers.ValidationError("Mode values cannot be empty")
            
            return modes_list
            
        except Exception as e:
            raise serializers.ValidationError(f"Invalid modes format: {str(e)}")

    def to_internal_value(self, data):
        """Override to ensure proper data processing"""
        validated_data = super().to_internal_value(data)
        
        return validated_data