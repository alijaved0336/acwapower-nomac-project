"""
Serializers for Column Schema API
Handles validation and serialization for column schema requests and responses.
"""
from rest_framework import serializers
from typing import List, Any


class TableRequestSerializer(serializers.Serializer):
    """
    Serializer for table request payload.
    Validates individual table requests within the array.
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
        help_text="Name of the table to get columns for",
        error_messages={
            'required': 'tableName is required',
            'max_length': 'tableName cannot exceed 100 characters',
            'blank': 'tableName cannot be blank'
        }
    )

    def validate(self, data):
        """
        Perform cross-field validation on the table request.
        """
        # Remove any leading/trailing whitespace
        for field in ['siteName', 'tableName']:
            if field in data:
                data[field] = data[field].strip()
        
        # Validate that none of the required fields are empty after stripping
        for field in ['siteName', 'tableName']:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} cannot be empty")
        
        # Additional validation for table name format
        table_name = data.get('tableName', '')
        if any(char in table_name for char in ['<', '>', '"', "'", '&', ';']):
            raise serializers.ValidationError(
                "tableName contains invalid characters. Avoid: < > \" ' & ;"
            )
        
        # Additional validation for site name format
        site_name = data.get('siteName', '')
        if any(char in site_name for char in ['<', '>', '"', "'", '&', ';']):
            raise serializers.ValidationError(
                "siteName contains invalid characters. Avoid: < > \" ' & ;"
            )
        
        return data


class ColumnSchemaResponseSerializer(serializers.Serializer):
    """
    Serializer for column schema response.
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


class ColumnSchemaRequestSerializer(serializers.Serializer):
    """
    Serializer for the complete request payload (array of table requests).
    Validates the entire request structure.
    """
    def to_internal_value(self, data):
        """
        Handle array input validation.
        Expects data to be a list of table request objects.
        """
        if not isinstance(data, list):
            raise serializers.ValidationError(
                "Request payload must be an array of table requests"
            )
        
        if len(data) == 0:
            raise serializers.ValidationError(
                "Request payload cannot be empty"
            )
        
        if len(data) > 50:  # Reasonable limit for performance
            raise serializers.ValidationError(
                "Request payload cannot contain more than 50 table requests"
            )
        
        # Validate each item in the array
        validated_data = []
        errors = {}
        
        for index, item in enumerate(data):
            item_serializer = TableRequestSerializer(data=item)
            if item_serializer.is_valid():
                validated_data.append(item_serializer.validated_data)
            else:
                errors[f"item_{index}"] = item_serializer.errors
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return validated_data


class ColumnSchemaResponseListSerializer(serializers.Serializer):
    """
    Serializer for the complete response (array of column schema responses).
    Documents the expected response structure.
    """
    def to_representation(self, instance):
        """
        Handle array output serialization.
        Expects instance to be a list of ColumnMetadata objects.
        """
        if not isinstance(instance, list):
            return []
        
        result = []
        for item in instance:
            if hasattr(item, 'to_dict'):
                # If it's a ColumnMetadata object
                result.append(item.to_dict())
            elif isinstance(item, dict):
                # If it's already a dictionary
                result.append(item)
            else:
                # Fallback serialization
                serializer = ColumnSchemaResponseSerializer(item)
                result.append(serializer.data)
        
        return result


# Example data for Swagger documentation
EXAMPLE_TABLE_REQUEST = {
    "siteName": "Jubail-Jazlah",
    "tableName": "Jubail_Chemicals_ppm"
}

EXAMPLE_COLUMN_SCHEMA_RESPONSE = {
    "columnName": "INL_FL_TO_DMPF_12_MES",
    "columnType": "double",
    "tableName": "Jubail_Chemicals_ppm",
    "siteName": "Jubail-Jazlah"
}

EXAMPLE_REQUEST_PAYLOAD = [
    {
        "siteName": "Jubail-Jazlah",
        "tableName": "Jubail_Chemicals_ppm"
    },
    {
        "siteName": "Jubail-Jazlah",
        "tableName": "Jubail-Jazlah_Normalization_pass_1"
    }
]

EXAMPLE_RESPONSE_PAYLOAD = [
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
    },
    {
        "columnName": "DateTime",
        "columnType": "timestamp[ns, tz=UTC]",
        "tableName": "Jubail-Jazlah_Normalization_pass_1",
        "siteName": "Jubail-Jazlah"
    }
]