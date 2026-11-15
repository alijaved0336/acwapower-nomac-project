import re
from datetime import datetime
from dateutil import parser
from rest_framework import serializers


class Dash028FilterSerializer(serializers.Serializer):
    """
    Serializer for Dash028 feature filter.
    Accepts a single date or datetime and computes start/end time automatically.
    Also normalizes RO identifier strings like 'RO Pass 1', 'Pass1', 'RO1', or '1' → 'pass1'.
    """

    site_id = serializers.CharField(required=True)
    date = serializers.CharField(required=True)
    ro_identifier = serializers.CharField(required=False, allow_blank=True)

    @staticmethod
    def extract_pass_number(text: str) -> str:
        """
        Extracts pass number from strings like 'RO Pass 1', 'Pass1', 'RO1', or '1'
        Returns normalized string like 'pass1'
        """
        if not text:
            return ""

        text = text.strip()

        # First, look for 'pass <num>' pattern
        match = re.search(r'pass\s*(\d+)', text, re.IGNORECASE)
        if match:
            return f"pass{match.group(1)}"

        # If no 'pass' word found, check for number alone (e.g. '1', 'RO1', 'RO 1')
        match = re.search(r'\b(\d+)\b', text)
        if match:
            return f"pass{match.group(1)}"

        return ""

    def validate_site_id(self, value):
        value = value.strip()
        if not re.match(r'^[a-zA-Z0-9_\-]+$', value):
            raise serializers.ValidationError("Invalid site_id format.")
        return value

    def validate_date(self, value):
        try:
            parsed_date = parser.parse(value)
            return parsed_date.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            raise serializers.ValidationError("Invalid date or datetime format.")

    def validate_ro_identifier(self, value):
        # Safely handle if key is missing or blank
        if not value:
            return None

        normalized = self.extract_pass_number(value)
        if not normalized:
            raise serializers.ValidationError(
                f"Invalid RO identifier '{value}'. Expected formats like 'RO Pass 1', 'Pass1', or '1'."
            )
        return normalized

    def to_internal_value(self, data):
        """
        Adds start_time and end_time after field-level validation.
        """
        validated = super().to_internal_value(data)

        parsed_date = validated.get("date")
        if parsed_date:
            date_str = data.get("date", "")
            has_time = any(ch in date_str for ch in ["T", ":"])
            if has_time:
                validated["start_time"] = parsed_date
                validated["end_time"] = parsed_date
            else:
                validated["start_time"] = parsed_date.replace(hour=0, minute=0, second=0)
                validated["end_time"] = parsed_date.replace(hour=23, minute=59, second=59)

        return validated


import re
from rest_framework import serializers
from dateutil import parser


class OperationalStatusFilterSerializer(serializers.Serializer):
    """
    Serializer for Operational Status feature filter.
    Accepts both start and end datetimes explicitly.
    Also normalizes RO identifier strings like 'RO Pass 1', 'Pass1', 'RO1', or '1' → 'pass1'.
    """

    site_id = serializers.CharField(required=True)
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)
    ro_identifier = serializers.CharField(required=False, allow_blank=True)

    @staticmethod
    def extract_pass_number(text: str) -> str:
        """
        Extracts pass number from strings like 'RO Pass 1', 'Pass1', 'RO1', or '1'
        Returns normalized string like 'pass1'
        """
        if not text:
            return ""

        text = text.strip()

        # First, look for 'pass <num>' pattern
        match = re.search(r'pass\s*(\d+)', text, re.IGNORECASE)
        if match:
            return f"pass{match.group(1)}"

        # If no 'pass' word found, check for number alone (e.g. '1', 'RO1', 'RO 1')
        match = re.search(r'\b(\d+)\b', text)
        if match:
            return f"pass{match.group(1)}"

        return ""

    def validate_site_id(self, value):
        value = value.strip()
        if not re.match(r'^[a-zA-Z0-9_\-]+$', value):
            raise serializers.ValidationError("Invalid site_id format.")
        return value

    def validate_start_datetime(self, value):
        try:
            parsed = parser.parse(value)
            return parsed
        except Exception:
            raise serializers.ValidationError("Invalid start_datetime format. Expected valid date or datetime string.")

    def validate_end_datetime(self, value):
        try:
            parsed = parser.parse(value)
            return parsed
        except Exception:
            raise serializers.ValidationError("Invalid end_datetime format. Expected valid date or datetime string.")

    def validate_ro_identifier(self, value):
        if not value:
            return None

        normalized = self.extract_pass_number(value)
        if not normalized:
            raise serializers.ValidationError(
                f"Invalid RO identifier '{value}'. Expected formats like 'RO Pass 1', 'Pass1', or '1'."
            )
        return normalized

    def validate(self, attrs):
        """
        Cross-field validation: ensure end_datetime >= start_datetime.
        """
        start = attrs.get("start_datetime")
        end = attrs.get("end_datetime")

        if start and end and end < start:
            raise serializers.ValidationError("end_datetime cannot be earlier than start_datetime.")

        return attrs


class YAxisOptionsSerializer(serializers.Serializer):
    reverse = serializers.BooleanField(required=False, default=False)
    min = serializers.FloatField(required=False, allow_null=True)
    max = serializers.FloatField(required=False, allow_null=True)
    colors = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    color = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    colorScheme = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        """
        Ensure that at least one of 'color' or 'colors' exists if colorScheme is provided.
        """
        color = data.get("color")
        colors = data.get("colors")

        # Optional rule: at least one color field should exist if colorScheme exists
        if data.get("colorScheme") and not (color or colors):
            raise serializers.ValidationError(
                "Either 'color' or 'colors' must be provided when 'colorScheme' is set."
            )

        return data

class ColumnSerializer(serializers.Serializer):
    columnName = serializers.CharField(required=True)
    yAxisOptions = YAxisOptionsSerializer(required=False, default=dict)



class WidgetSerializer(serializers.Serializer):
    site_id = serializers.CharField(required=True)
    pump_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    page = serializers.CharField(required=True)
    columns = ColumnSerializer(many=True, required=True)

    def validate(self, attrs):
        if not attrs.get("columns"):
            raise serializers.ValidationError("At least one column is required.")
        return attrs