from rest_framework import serializers


class TaskCreatedResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(
        help_text="The UUID of the text analysis session.",
    )
    task_id = serializers.UUIDField(
        help_text="The UUID of the async task created to process the request.",
    )


class TaskStatusResponseSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(
        help_text="The UUID of the async task.",
    )
    status = serializers.CharField(
        help_text="The current status of the task (e.g., PENDING, STARTED, "
        + "SUCCESS, FAILURE, etc)."
    )
    result = serializers.JSONField(
        required=False,
        allow_null=True,
        default=None,
        help_text="The result of the task if it has completed successfully.",
    )
    error = serializers.CharField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Error message if the task failed.",
    )
