# from django.contrib.auth.models import User
# from drf_spectacular.utils import extend_schema_field
# from rest_framework import serializers

# from .models import ChatMessage, ChatSession


# class UserRegistrationSerializer(serializers.ModelSerializer):
#     password = extend_schema_field({"type": "string", "format": "password"})(
#         serializers.CharField(write_only=True, style={"input_type": "password"})
#     )

#     class Meta:
#         model = User
#         fields = ["username", "email", "password"]

#     def create(self, validated_data):
#         user = User.objects.create_user(
#             username=validated_data["username"],
#             email=validated_data.get("email"),
#             password=validated_data["password"],
#         )
#         return user


# class TextAnalysisRequestSerializer(serializers.Serializer):
#     title = serializers.CharField(
#         required=False,
#         allow_null=True,
#         max_length=255,
#         default=None,
#         help_text="Optional title for the text. If not provided, a title will "
#         + "be generated automatically by the language model.",
#     )
#     text = serializers.CharField(
#         help_text="The text to be analyzed.",
#     )


# class SessionResponseSerializer(serializers.ModelSerializer):
#     session_id = serializers.UUIDField(
#         source="id", help_text="The UUID of the session."
#     )

#     class Meta:
#         model = ChatSession
#         fields = ["session_id", "title", "created_at"]


# class MessageResponseSerializer(serializers.ModelSerializer):
#     message_id = serializers.UUIDField(
#         source="id", help_text="The UUID of the message."
#     )

#     class Meta:
#         model = ChatMessage
#         fields = ["message_id", "created_at", "message"]


# class SessionDetailsResponseSerializer(serializers.ModelSerializer):
#     session_id = serializers.UUIDField(
#         source="id", help_text="The UUID of the session."
#     )
#     messages = MessageResponseSerializer(
#         many=True,
#         read_only=True,
#         help_text="List of messages belonging to this text analysis session.",
#     )

#     class Meta:
#         model = ChatSession
#         fields = ["session_id", "title", "created_at", "messages"]


# class QuestionRequestSerializer(serializers.Serializer):
#     session_id = serializers.UUIDField(
#         required=True,
#         help_text="The UUID of the chat session to which the question belongs.",
#     )
#     question = serializers.CharField(
#         required=True,
#         allow_blank=False,
#         help_text="The follow-up question based on the session history.",
#     )


# class TaskCreatedResponseSerializer(serializers.Serializer):
#     session_id = serializers.UUIDField(
#         help_text="The UUID of the text analysis session.",
#     )
#     task_id = serializers.UUIDField(
#         help_text="The UUID of the async task created to process the request.",
#     )


# class TaskStatusResponseSerializer(serializers.Serializer):
#     task_id = serializers.UUIDField(
#         help_text="The UUID of the async task.",
#     )
#     status = serializers.CharField(
#         help_text="The current status of the task (e.g., PENDING, STARTED, "
#         + "SUCCESS, FAILURE, etc)."
#     )
#     result = serializers.JSONField(
#         required=False,
#         allow_null=True,
#         default=None,
#         help_text="The result of the task if it has completed successfully.",
#     )
#     error = serializers.CharField(
#         required=False,
#         allow_null=True,
#         default=None,
#         help_text="Error message if the task failed.",
#     )


# class ErrorResponseSerializer(serializers.Serializer):
#     error = serializers.CharField(
#         help_text="Error message describing what went wrong.",
#     )
#     detail = serializers.CharField(
#         required=False,
#         allow_blank=True,
#         help_text="Optional detailed error message.",
#     )
#     code = serializers.IntegerField(
#         help_text="HTTP status code associated with the error.",
#     )
