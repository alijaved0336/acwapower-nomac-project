from rest_framework import serializers

from interface.serializers.users import UserResponseSerializer


class AuthSuccessSerializer(serializers.Serializer):
    message = serializers.CharField()
    user = UserResponseSerializer()
    token = serializers.CharField()
    refresh_token = serializers.CharField()


class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    details = serializers.DictField(required=False)
