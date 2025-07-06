from uuid import uuid4

import pytest
from django.contrib.auth.models import User

from mentor.assistant.models import ChatMessage, ChatSession
from mentor.assistant.serializers.chat import (
    MessageResponseSerializer,
    QuestionRequestSerializer,
    SessionDetailsResponseSerializer,
    SessionResponseSerializer,
    TextAnalysisRequestSerializer,
)

pytestmark = pytest.mark.django_db


# ---------------------------
# TextAnalysisRequestSerializer
# ---------------------------


def test_text_analysis_valid_with_all_fields():
    data = {"title": "Título personalizado", "text": "Texto educacional de exemplo."}
    serializer = TextAnalysisRequestSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["title"] == "Título personalizado"


def test_text_analysis_valid_without_title():
    data = {"text": "Texto educacional sem título."}
    serializer = TextAnalysisRequestSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["title"] is None


def test_text_analysis_missing_text_should_fail():
    data = {"title": "Título"}
    serializer = TextAnalysisRequestSerializer(data=data)
    assert not serializer.is_valid()
    assert "text" in serializer.errors


# ---------------------------
# QuestionRequestSerializer
# ---------------------------


def test_question_request_valid():
    data = {"session_id": str(uuid4()), "question": "O que é fotossíntese?"}
    serializer = QuestionRequestSerializer(data=data)
    assert serializer.is_valid(), serializer.errors


def test_question_request_blank_question_should_fail():
    data = {"session_id": str(uuid4()), "question": ""}
    serializer = QuestionRequestSerializer(data=data)
    assert not serializer.is_valid()
    assert "question" in serializer.errors


def test_question_request_missing_fields_should_fail():
    serializer = QuestionRequestSerializer(data={})
    assert not serializer.is_valid()
    assert "session_id" in serializer.errors
    assert "question" in serializer.errors


# ---------------------------
# SessionResponseSerializer
# ---------------------------


def test_session_response_serialization():
    user = User.objects.create_user(username="test", password="pass")
    session = ChatSession.objects.create(user=user, title="Teste de sessão")
    serializer = SessionResponseSerializer(instance=session)
    data = serializer.data

    assert "session_id" in data
    assert data["session_id"] == str(session.id)
    assert data["title"] == "Teste de sessão"
    assert "created_at" in data


# ---------------------------
# MessageResponseSerializer
# ---------------------------


def test_message_response_serialization():
    user = User.objects.create_user(username="test", password="pass")
    session = ChatSession.objects.create(user=user)
    message = ChatMessage.objects.create(
        session=session, message={"type": "user", "content": "Olá!"}
    )
    serializer = MessageResponseSerializer(instance=message)
    data = serializer.data

    assert "message_id" in data
    assert data["message_id"] == str(message.id)
    assert data["message"] == message.message
    assert "created_at" in data


# ---------------------------
# SessionDetailsResponseSerializer
# ---------------------------


def test_session_details_response_serialization_with_messages():
    user = User.objects.create_user(username="test", password="pass")
    session = ChatSession.objects.create(user=user, title="Sessão de Teste")
    ChatMessage.objects.create(
        session=session, message={"type": "user", "content": "Pergunta 1"}
    )
    ChatMessage.objects.create(
        session=session, message={"type": "assistant", "content": "Resposta 1"}
    )

    serializer = SessionDetailsResponseSerializer(instance=session)
    data = serializer.data

    assert data["session_id"] == str(session.id)
    assert data["title"] == "Sessão de Teste"
    assert isinstance(data["messages"], list)
    assert len(data["messages"]) == 2
    assert "message" in data["messages"][0]
