from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(required=True)
    picture = serializers.URLField(required=False, allow_null=True)
    sub = serializers.CharField(
        max_length=255, required=False, allow_null=True, allow_blank=True
    )
    # role_id = serializers.CharField(max_length=255)


class UserResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    picture = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sub = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_at = serializers.CharField()
