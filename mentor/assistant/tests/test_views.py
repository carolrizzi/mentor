import uuid
from unittest import mock

import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from mentor.assistant.models import ChatSession

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="password")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def session(user):
    return ChatSession.objects.create(user=user, title="Sample Session")


# ---------------------------
# User Registration
# ---------------------------


def test_user_registration_success(client):
    url = "/api/register/"  # replace with actual route
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "testpass123",
    }
    response = client.post(url, data=data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="newuser").exists()


def test_user_registration_missing_fields(client):
    url = "/api/register/"
    response = client.post(url, data={}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------
# TextAnalysisView
# ---------------------------


@mock.patch("mentor.assistant.views.analyze_text.delay")
def test_text_analysis_post_success(mock_delay, auth_client):
    mock_task = mock.Mock()
    mock_task.id = str(uuid.uuid4())
    mock_delay.return_value = mock_task

    url = "/api/analysis/"
    data = {"title": "New Text", "text": "Some educational content."}
    response = auth_client.post(url, data=data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert "session_id" in response.data
    assert "task_id" in response.data
    mock_delay.assert_called_once()


def test_text_analysis_post_invalid(auth_client):
    url = "/api/analysis/"
    data = {"title": "Only title"}
    response = auth_client.post(url, data=data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_text_analysis_get_sessions(auth_client, session):
    url = "/api/analysis/"
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert any(s["session_id"] == str(session.id) for s in response.data)


# ---------------------------
# SessionManagementView
# ---------------------------


def test_session_management_get_found(auth_client, session):
    url = f"/api/analysis/{session.id}/"
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["session_id"] == str(session.id)


def test_session_management_get_not_found(auth_client):
    url = f"/api/analysis/{uuid.uuid4()}/"
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_session_management_delete_success(auth_client, session):
    url = f"/api/analysis/{session.id}/"
    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not ChatSession.objects.filter(id=session.id).exists()


def test_session_management_delete_not_found(auth_client):
    url = f"/api/analysis/{uuid.uuid4()}/"
    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------
# FollowUpQuestionView
# ---------------------------


@mock.patch("mentor.assistant.views.follow_up_question.delay")
def test_follow_up_question_success(mock_delay, auth_client, session):
    mock_task = mock.Mock()
    mock_task.id = str(uuid.uuid4())
    mock_delay.return_value = mock_task

    url = "/api/question/"
    data = {"session_id": str(session.id), "question": "What is photosynthesis?"}
    response = auth_client.post(url, data=data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "task_id" in response.data
    mock_delay.assert_called_once()


def test_follow_up_question_invalid_session(auth_client):
    url = "/api/question/"
    data = {"session_id": str(uuid.uuid4()), "question": "Invalid question."}
    response = auth_client.post(url, data=data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------
# TaskStatusView
# ---------------------------


@mock.patch("mentor.assistant.views.AsyncResult")
def test_task_status_pending(mock_async, auth_client):
    mock_async.return_value.status = "PENDING"
    mock_async.return_value.result = None

    url = f"/api/task/{uuid.uuid4()}/"
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data["status"] == "PENDING"


@mock.patch("mentor.assistant.views.AsyncResult")
def test_task_status_success(mock_async, auth_client):
    mock_async.return_value.status = "SUCCESS"
    mock_async.return_value.result = {"answer": "Some result"}

    url = f"/api/task/{uuid.uuid4()}/"
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "SUCCESS"
    assert response.data["result"] == {"answer": "Some result"}


@mock.patch("mentor.assistant.views.AsyncResult")
def test_task_status_failure(mock_async, auth_client):
    mock_async.return_value.status = "FAILURE"
    mock_async.return_value.result = "Something went wrong"

    url = f"/api/task/{uuid.uuid4()}/"
    response = auth_client.get(url)
    assert response.status_code == 500
    assert response.data["status"] == "FAILURE"
    assert response.data["error"] == "Something went wrong"
