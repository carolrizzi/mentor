import pytest
from django.contrib.auth.models import User

from mentor.assistant.serializers.manage import (
    ErrorResponseSerializer,
    UserRegistrationSerializer,
)

pytestmark = pytest.mark.django_db


# ---------------------------
# UserRegistrationSerializer
# ---------------------------


def test_user_registration_valid_data():
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepassword123",
    }
    serializer = UserRegistrationSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()

    assert isinstance(user, User)
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.check_password("securepassword123")


def test_user_registration_missing_password_should_fail():
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
    }
    serializer = UserRegistrationSerializer(data=data)
    assert not serializer.is_valid()
    assert "password" in serializer.errors


def test_user_registration_blank_username_should_fail():
    data = {
        "username": "",
        "email": "test@example.com",
        "password": "password123",
    }
    serializer = UserRegistrationSerializer(data=data)
    assert not serializer.is_valid()
    assert "username" in serializer.errors


# ---------------------------
# ErrorResponseSerializer
# ---------------------------


def test_error_response_serializer_with_required_fields():
    data = {
        "error": "Invalid request.",
        "code": 400,
    }
    serializer = ErrorResponseSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    validated = serializer.validated_data
    assert validated["error"] == "Invalid request."
    assert validated["code"] == 400
    assert "detail" not in validated or validated["detail"] == ""


def test_error_response_serializer_with_detail():
    data = {
        "error": "Validation failed.",
        "detail": "Username already exists.",
        "code": 409,
    }
    serializer = ErrorResponseSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    validated = serializer.validated_data
    assert validated["error"] == "Validation failed."
    assert validated["detail"] == "Username already exists."
    assert validated["code"] == 409


def test_error_response_serializer_missing_error_should_fail():
    data = {
        "code": 400,
    }
    serializer = ErrorResponseSerializer(data=data)
    assert not serializer.is_valid()
    assert "error" in serializer.errors
