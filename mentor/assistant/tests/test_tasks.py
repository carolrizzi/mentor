# tests/test_tasks.py

import uuid

import pytest
from django.contrib.auth.models import User

from mentor.assistant import tasks

pytestmark = pytest.mark.django_db


def test_analyze_text_with_provided_title(mocker):
    mock_user = User.objects.create_user(username="tester", password="pw")
    mock_analyze = mocker.patch("mentor.assistant.tasks.agent_analyze_text")
    mock_create_session = mocker.patch(
        "mentor.assistant.tasks.ChatSession.objects.create"
    )

    mock_response = mocker.Mock()
    mock_response.content = "Analysis result here"
    mock_analyze.return_value = mock_response

    session_id = uuid.uuid4()
    text = "Some educational text"
    title = "My Title"

    result = tasks.analyze_text.run(
        user_id=mock_user.id,
        session_id=session_id,
        text=text,
        title=title,
    )

    mock_create_session.assert_called_once_with(
        id=session_id,
        user=mock_user,
        title=title,
    )
    mock_analyze.assert_called_once_with(session_id=session_id, text=text)
    assert result == "Analysis result here"


def test_analyze_text_without_title_generates_title(mocker):
    mock_user = User.objects.create_user(username="tester", password="pw")
    mock_generate_title = mocker.patch("mentor.assistant.tasks.generate_title")
    mock_analyze = mocker.patch("mentor.assistant.tasks.agent_analyze_text")
    mock_create_session = mocker.patch(
        "mentor.assistant.tasks.ChatSession.objects.create"
    )

    mock_title_response = mocker.Mock()
    mock_title_response.content = "Generated Title"
    mock_generate_title.return_value = mock_title_response

    mock_analysis_response = mocker.Mock()
    mock_analysis_response.content = "Analysis Result"
    mock_analyze.return_value = mock_analysis_response

    session_id = uuid.uuid4()
    text = "Some educational text"

    result = tasks.analyze_text.run(
        user_id=mock_user.id,
        session_id=session_id,
        text=text,
        title=None,
    )

    mock_generate_title.assert_called_once_with(text)
    mock_create_session.assert_called_once_with(
        id=session_id,
        user=mock_user,
        title="Generated Title",
    )
    mock_analyze.assert_called_once_with(session_id=session_id, text=text)
    assert result == "Analysis Result"


def test_analyze_text_returns_none_if_title_generation_fails(mocker):
    mock_generate_title = mocker.patch("mentor.assistant.tasks.generate_title")
    mock_generate_title.return_value = None

    result = tasks.analyze_text.run(
        user_id=123,
        session_id=uuid.uuid4(),
        text="Some text",
        title=None,
    )

    assert result is None


def test_analyze_text_returns_none_if_user_does_not_exist(mocker):
    mock_user_get = mocker.patch("mentor.assistant.tasks.User.objects.get")
    mock_user_get.side_effect = User.DoesNotExist

    result = tasks.analyze_text.run(
        user_id=999,
        session_id=uuid.uuid4(),
        text="Some text",
        title="Title",
    )

    assert result is None


def test_follow_up_question_returns_content(mocker):
    mock_follow_up = mocker.patch("mentor.assistant.tasks.agent_follow_up_question")
    mock_response = mocker.Mock()
    mock_response.content = "The follow-up answer"
    mock_follow_up.return_value = mock_response

    session_id = uuid.uuid4()
    question = "What is photosynthesis?"

    result = tasks.follow_up_question.run(
        session_id=session_id,
        question=question,
    )

    mock_follow_up.assert_called_once_with(session_id=session_id, question=question)
    assert result == "The follow-up answer"


def test_follow_up_question_returns_none_if_response_is_none(mocker):
    mock_follow_up = mocker.patch("mentor.assistant.tasks.agent_follow_up_question")
    mock_follow_up.return_value = None

    session_id = uuid.uuid4()
    question = "Another question"

    result = tasks.follow_up_question.run(
        session_id=session_id,
        question=question,
    )

    assert result is None


def test_get_task_status_success(mocker):
    task_id = str(uuid.uuid4())
    mock_async = mocker.patch("mentor.assistant.tasks.AsyncResult")
    mock_async.return_value.status = "SUCCESS"
    mock_async.return_value.successful.return_value = True
    mock_async.return_value.failed.return_value = False
    mock_async.return_value.result = {"foo": "bar"}

    result = tasks.get_task_status(task_id)

    assert result == {
        "task_id": task_id,
        "status": "SUCCESS",
        "result": {"foo": "bar"},
        "error": None,
    }


def test_get_task_status_failure(mocker):
    task_id = str(uuid.uuid4())
    mock_async = mocker.patch("mentor.assistant.tasks.AsyncResult")
    mock_async.return_value.status = "FAILURE"
    mock_async.return_value.successful.return_value = False
    mock_async.return_value.failed.return_value = True
    mock_async.return_value.result = "Something went wrong"

    result = tasks.get_task_status(task_id)

    assert result == {
        "task_id": task_id,
        "status": "FAILURE",
        "result": None,
        "error": "Something went wrong",
    }
