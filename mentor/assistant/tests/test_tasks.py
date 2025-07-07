# tests/test_tasks.py

import uuid

import pytest
from django.contrib.auth.models import User

from mentor.assistant import tasks

pytestmark = pytest.mark.django_db


@pytest.fixture
def fake_agent(mocker):
    """
    Fixture that returns a fake Assistant instance
    with all its methods mocked.
    """
    agent_mock = mocker.Mock()
    agent_mock.generate_title.return_value = mocker.Mock(content="Generated Title")
    agent_mock.analyze_text.return_value = mocker.Mock(content="Analysis Result")
    agent_mock.follow_up_question.return_value = mocker.Mock(
        content="The follow-up answer"
    )
    return agent_mock


def test_analyze_text_with_provided_title(mocker, fake_agent):
    mock_user = User.objects.create_user(username="tester", password="pw")

    mock_get_agent = mocker.patch(
        "mentor.assistant.tasks.get_agent", return_value=fake_agent
    )
    mock_create_session = mocker.patch(
        "mentor.assistant.tasks.ChatSession.objects.create"
    )

    session_id = uuid.uuid4()
    text = "Some educational text"
    title = "My Title"

    result = tasks.analyze_text.run(
        user_id=mock_user.id,
        session_id=session_id,
        text=text,
        title=title,
    )

    mock_get_agent.assert_called_once()
    mock_create_session.assert_called_once_with(
        id=session_id,
        user=mock_user,
        title=title,
    )
    fake_agent.analyze_text.assert_called_once_with(session_id=session_id, text=text)
    assert result == "Analysis Result"


def test_analyze_text_without_title_generates_title(mocker, fake_agent):
    mock_user = User.objects.create_user(username="tester", password="pw")

    fake_agent.generate_title.return_value = mocker.Mock(content="Generated Title")
    fake_agent.analyze_text.return_value = mocker.Mock(content="Analysis Result")

    mocker.patch("mentor.assistant.tasks.get_agent", return_value=fake_agent)
    mock_create_session = mocker.patch(
        "mentor.assistant.tasks.ChatSession.objects.create"
    )

    session_id = uuid.uuid4()
    text = "Some educational text"

    result = tasks.analyze_text.run(
        user_id=mock_user.id,
        session_id=session_id,
        text=text,
        title=None,
    )

    fake_agent.generate_title.assert_called_once_with(text)
    mock_create_session.assert_called_once_with(
        id=session_id,
        user=mock_user,
        title="Generated Title",
    )
    fake_agent.analyze_text.assert_called_once_with(session_id=session_id, text=text)
    assert result == "Analysis Result"


def test_analyze_text_returns_none_if_title_generation_fails(mocker, fake_agent):
    fake_agent.generate_title.return_value = None
    mocker.patch("mentor.assistant.tasks.get_agent", return_value=fake_agent)

    result = tasks.analyze_text.run(
        user_id=123,
        session_id=uuid.uuid4(),
        text="Some text",
        title=None,
    )

    assert result is None


def test_analyze_text_returns_none_if_user_does_not_exist(mocker, fake_agent):
    mock_user_get = mocker.patch("mentor.assistant.tasks.User.objects.get")
    mock_user_get.side_effect = User.DoesNotExist

    mocker.patch("mentor.assistant.tasks.get_agent", return_value=fake_agent)

    result = tasks.analyze_text.run(
        user_id=999,
        session_id=uuid.uuid4(),
        text="Some text",
        title="Title",
    )

    assert result is None


def test_follow_up_question_returns_content(mocker, fake_agent):
    mocker.patch("mentor.assistant.tasks.get_agent", return_value=fake_agent)

    session_id = uuid.uuid4()
    question = "What is photosynthesis?"

    result = tasks.follow_up_question.run(
        session_id=session_id,
        question=question,
    )

    fake_agent.follow_up_question.assert_called_once_with(
        session_id=session_id,
        question=question,
    )
    assert result == "The follow-up answer"


def test_follow_up_question_returns_none_if_response_is_none(mocker, fake_agent):
    fake_agent.follow_up_question.return_value = None

    mocker.patch("mentor.assistant.tasks.get_agent", return_value=fake_agent)

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
