from rest_framework import serializers

class ChemicalAnalysisRequestSchema(serializers.Serializer):
    site_id = serializers.CharField(required=False, allow_blank=True, max_length=255)

class ChemicalAnalysisResponseSchema(serializers.Serializer):
    data = serializers.DictField()
    message = serializers.CharField()
