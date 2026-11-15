from rest_framework import serializers

class Dash009RequestSchema(serializers.Serializer):
    site_id = serializers.CharField(required=False, allow_blank=True, max_length=255)

class Dash009ResponseSchema(serializers.Serializer):
    data = serializers.DictField()
    message = serializers.CharField()