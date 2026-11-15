# interface/serializers/auth.py
from rest_framework import serializers


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(trim_whitespace=True)
