from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = extend_schema_field({"type": "string", "format": "password"})(
        serializers.CharField(write_only=True, style={"input_type": "password"})
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )
        return user


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(
        help_text="Error message describing what went wrong.",
    )
    detail = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional detailed error message.",
    )
    code = serializers.IntegerField(
        help_text="HTTP status code associated with the error.",
    )
