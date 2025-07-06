import pytest
from django.contrib.auth.models import User

from mentor.assistant.models import ChatMessage, ChatSession

pytestmark = pytest.mark.django_db


def test_chat_session_creation():
    user = User.objects.create_user(username="testuser", password="secret")
    session = ChatSession.objects.create(
        user=user,
        title="Ciclos Biogeoquímicos",
    )

    assert session.user == user
    assert session.title == "Ciclos Biogeoquímicos"
    assert session.__str__() == "Ciclos Biogeoquímicos (User: testuser)"


def test_chat_message_creation():
    user = User.objects.create_user(username="testuser", password="secret")
    session = ChatSession.objects.create(
        user=user,
        title="Independência do Brasil",
    )
    message_content = {
        "type": "ai",
        "content": "Texto analisado com sucesso.",
    }
    message = ChatMessage.objects.create(
        session=session,
        message=message_content,
    )

    assert message.session == session
    assert message.message["type"] == "ai"
    assert message.message["content"] == "Texto analisado com sucesso."


def test_cascade_delete_chat_session_deletes_messages():
    user = User.objects.create_user(username="testuser", password="secret")
    session = ChatSession.objects.create(user=user, title="Teste")
    ChatMessage.objects.create(
        session=session,
        message={"type": "human", "content": "Olá!"},
    )
    assert ChatMessage.objects.count() == 1

    session.delete()

    assert ChatMessage.objects.count() == 0


def test_blank_title_allowed():
    user = User.objects.create_user(username="testuser", password="secret")
    session = ChatSession.objects.create(
        user=user,
        title="",
    )
    assert session.title == ""
