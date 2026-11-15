from rest_framework import serializers

class ProcessOverviewRequestSchema(serializers.Serializer):
    site_id = serializers.CharField(required=False, allow_blank=True, max_length=255)

class ProcessOverviewResponseSchema(serializers.Serializer):
    data = serializers.DictField()
    message = serializers.CharField()
