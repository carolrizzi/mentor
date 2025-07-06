from assistant.models import ChatMessage, ChatSession
from rest_framework import serializers


class TextAnalysisRequestSerializer(serializers.Serializer):
    title = serializers.CharField(
        required=False,
        allow_null=True,
        max_length=255,
        default=None,
        help_text="Optional title for the text. If not provided, a title will "
        + "be generated automatically by the language model.",
    )
    text = serializers.CharField(
        help_text="The text to be analyzed.",
    )


class SessionResponseSerializer(serializers.ModelSerializer):
    session_id = serializers.UUIDField(
        source="id", help_text="The UUID of the session."
    )

    class Meta:
        model = ChatSession
        fields = ["session_id", "title", "created_at"]


class MessageResponseSerializer(serializers.ModelSerializer):
    message_id = serializers.UUIDField(
        source="id", help_text="The UUID of the message."
    )

    class Meta:
        model = ChatMessage
        fields = ["message_id", "created_at", "message"]


class SessionDetailsResponseSerializer(serializers.ModelSerializer):
    session_id = serializers.UUIDField(
        source="id", help_text="The UUID of the session."
    )
    messages = MessageResponseSerializer(
        many=True,
        read_only=True,
        help_text="List of messages belonging to this text analysis session.",
    )

    class Meta:
        model = ChatSession
        fields = ["session_id", "title", "created_at", "messages"]


class QuestionRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(
        required=True,
        help_text="The UUID of the chat session to which the question belongs.",
    )
    question = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="The follow-up question based on the session history.",
    )
