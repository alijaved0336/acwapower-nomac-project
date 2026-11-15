from rest_framework import serializers


# class RoleSerializer(serializers.Serializer):
#     name = serializers.CharField(max_length=100)
#     type = serializers.CharField(max_length=50)
#     description = serializers.CharField(allow_blank=True, required=False)
#     clusters = serializers.ListField(
#         child=serializers.CharField(), required=False, allow_empty=True
#     )
#     is_active = serializers.BooleanField(required=False)

class ClusterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    sites = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        allow_empty=False
    )

class RoleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=50)
    description = serializers.CharField(allow_blank=True, required=False)
    clusters = serializers.ListField(
        child=ClusterSerializer(),
        required=True,
        allow_empty=False
    )
    is_active = serializers.BooleanField(required=False)


class RoleUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    type = serializers.CharField(max_length=50, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    clusters = serializers.ListField(
        child=ClusterSerializer(),
        required=False,
        allow_empty=True
    )
    is_active = serializers.BooleanField(required=False)
