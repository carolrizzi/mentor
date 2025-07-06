import uuid

import pytest

from mentor.assistant.serializers.task import (
    TaskCreatedResponseSerializer,
    TaskStatusResponseSerializer,
)

pytestmark = pytest.mark.django_db


# ---------------------------
# TaskCreatedResponseSerializer
# ---------------------------


def test_task_created_response_valid():
    data = {
        "session_id": str(uuid.uuid4()),
        "task_id": str(uuid.uuid4()),
    }
    serializer = TaskCreatedResponseSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    validated = serializer.validated_data
    assert "session_id" in validated
    assert "task_id" in validated


def test_task_created_response_missing_field_should_fail():
    data = {
        "task_id": str(uuid.uuid4()),
    }
    serializer = TaskCreatedResponseSerializer(data=data)
    assert not serializer.is_valid()
    assert "session_id" in serializer.errors


# ---------------------------
# TaskStatusResponseSerializer
# ---------------------------


def test_task_status_response_minimal_valid():
    data = {
        "task_id": str(uuid.uuid4()),
        "status": "PENDING",
    }
    serializer = TaskStatusResponseSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    validated = serializer.validated_data
    assert validated["status"] == "PENDING"
    assert validated.get("result") is None
    assert validated.get("error") is None


def test_task_status_response_with_result():
    data = {
        "task_id": str(uuid.uuid4()),
        "status": "SUCCESS",
        "result": {"answer": "Texto analisado com sucesso."},
    }
    serializer = TaskStatusResponseSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert (
        serializer.validated_data["result"]["answer"] == "Texto analisado com sucesso."
    )


def test_task_status_response_with_error():
    data = {
        "task_id": str(uuid.uuid4()),
        "status": "FAILURE",
        "error": "An unexpected error occurred.",
    }
    serializer = TaskStatusResponseSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["error"] == "An unexpected error occurred."


def test_task_status_response_missing_required_fields_should_fail():
    data = {"result": {"some": "data"}}
    serializer = TaskStatusResponseSerializer(data=data)
    assert not serializer.is_valid()
    assert "task_id" in serializer.errors
    assert "status" in serializer.errors
