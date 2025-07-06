from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models


class ChatSession(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        help_text="The UUID of the text analysis session.",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        help_text="ID of the user who created the chat session.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the text analysis session was created.",
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Title of the text analysed, also used as a title for the session.",
    )

    def __str__(self):
        return f"{self.title} (User: {self.user.username})"

    class Meta:
        db_table = "chat_session"


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        to_field="id",
        related_name="messages",
        help_text="The chat session to which this message belongs.",
    )
    message = models.JSONField(
        help_text="Json representation of the chat message, including its content. "
        + "To access the content, use the 'content' key. To acces the author of the "
        + "message, use the 'type' key."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp when the message was created."
    )

    class Meta:
        db_table = "chat_message"
