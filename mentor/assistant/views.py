from uuid import UUID, uuid4

from celery.result import AsyncResult
from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from mentor.assistant.models import ChatSession
from mentor.assistant.serializers.chat import (
    QuestionRequestSerializer,
    SessionDetailsResponseSerializer,
    SessionResponseSerializer,
    TextAnalysisRequestSerializer,
)
from mentor.assistant.serializers.manage import (
    ErrorResponseSerializer,
    UserRegistrationSerializer,
)
from mentor.assistant.serializers.task import (
    TaskCreatedResponseSerializer,
    TaskStatusResponseSerializer,
)
from mentor.assistant.tasks import analyze_text, follow_up_question


def get_invalid_session_response(user: User) -> Response:
    data = ErrorResponseSerializer().to_representation(
        {
            "error": f"Invalid session for user {user.username} (user id: {user.id}).",
            "code": status.HTTP_400_BAD_REQUEST,
        }
    )
    return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


def get_task_created_response(session_id: UUID | str, task_id: UUID | str) -> Response:
    return Response(
        data=TaskCreatedResponseSerializer().to_representation(
            {
                "session_id": session_id,
                "task_id": task_id,
            }
        ),
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    summary="Register a new user",
    description="Register a new user with a username, email (optional), and password.",
)
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class TextAnalysisView(APIView):
    @extend_schema(
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SessionResponseSerializer(many=True),
                description="List of text analysis sessions.",
            ),
        },
        summary="List all text analyses",
        description="List all sessions of text analysis created by the user.",
        operation_id="analysis_list",
    )
    def get(self, request):
        user_sessions = ChatSession.objects.filter(user=request.user)
        serializer = SessionResponseSerializer(user_sessions, many=True)

        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=TextAnalysisRequestSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=TaskCreatedResponseSerializer,
                description="Task created successfully.",
            ),
        },
        summary="Analyze a text",
        description="Analyze the provided text using a language model. "
        + "Optionally, you can provide a title for the text. If no title is provided, "
        + "one will be automatically generated by the language model."
        + "An async task will be created to process the text, and the task ID "
        + "will be returned. To consult on the task status, use the task route.",
    )
    def post(self, request):
        serializer = TextAnalysisRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Text analysis is always the start of a conversation,
        # so we generate a new session ID here
        session_id = uuid4()
        title = serializer.validated_data.get("title")
        result = analyze_text.delay(
            user_id=request.user.id,
            session_id=session_id,
            text=serializer.validated_data.get("text"),
            title=title,
        )
        return get_task_created_response(session_id=session_id, task_id=result.id)


class SessionManagementView(APIView):
    """
    View to manage chat sessions for the user.
    """

    @extend_schema(
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SessionDetailsResponseSerializer,
                description="Details of the text analysis session.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid session ID or session does not belong to user.",
            ),
        },
        summary="Retrieve a text analysis",
        description="Retrieve the details of a specific text analysis session, "
        + "including the messages exchanged between the user and the AI assistant.",
        operation_id="analysis_get_by_id",
    )
    def get(self, request, session_id):
        try:
            chat_session = ChatSession.objects.get(user=request.user, id=session_id)
            serializer = SessionDetailsResponseSerializer(chat_session)
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except ChatSession.DoesNotExist:
            return get_invalid_session_response(user=request.user)

    @extend_schema(
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Text analysis session deleted successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid session ID or session does not belong to user.",
            ),
        },
        summary="Delete a text analysis",
        description="Delete a specific text analysis session.",
    )
    def delete(self, request, session_id):
        try:
            chat_session = ChatSession.objects.get(user=request.user, id=session_id)
            chat_session.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ChatSession.DoesNotExist:
            return get_invalid_session_response(user=request.user)


class FollowUpQuestionView(APIView):
    @extend_schema(
        request=QuestionRequestSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=TaskCreatedResponseSerializer,
                description="Task created successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid session ID or session does not belong to user.",
            ),
        },
        summary="Ask a follow-up question",
        description="Ask a follow-up question based on the session history. "
        + "An async task will be created to process the question, and the task ID "
        + "will be returned. To consult on the task status, use the task route.",
    )
    def post(self, request):
        serializer = QuestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data.get("session_id")
        try:
            # Validate that the session belongs to the user
            ChatSession.objects.get(user=request.user, id=session_id)
        except ChatSession.DoesNotExist:
            return get_invalid_session_response(user=request.user)

        result = follow_up_question.delay(
            session_id=session_id, question=serializer.validated_data.get("question")
        )
        return get_task_created_response(session_id=session_id, task_id=result.id)


class TaskStatusView(APIView):
    @extend_schema(
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=TaskStatusResponseSerializer,
                description="Task finished successfully. Error will be empty.",
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response=TaskStatusResponseSerializer,
                description="Task still pending or running. "
                + "Both result and error will be empty.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                response=TaskStatusResponseSerializer,
                description="Task failed with an error. Result will be empty.",
            ),
        },
        summary="Check task status",
        description="Check the status of an initialized task.",
    )
    def get(self, request, task_id):
        res = AsyncResult(task_id)
        if res.status == "PENDING":
            return Response(
                data=TaskStatusResponseSerializer().to_representation(
                    {
                        "task_id": task_id,
                        "status": res.status,
                        "result": None,
                    }
                ),
                status=status.HTTP_202_ACCEPTED,
            )
        elif res.status == "SUCCESS":
            return Response(
                data=TaskStatusResponseSerializer().to_representation(
                    {
                        "task_id": task_id,
                        "status": res.status,
                        "result": res.result,
                    }
                ),
                status=status.HTTP_200_OK,
            )
        elif res.status == "FAILURE":
            return Response(
                data=TaskStatusResponseSerializer().to_representation(
                    {
                        "task_id": task_id,
                        "status": res.status,
                        "error": str(res.result),
                    }
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        else:
            return Response(
                data=TaskStatusResponseSerializer().to_representation(
                    {
                        "task_id": task_id,
                        "status": res.status,
                    }
                ),
                status=status.HTTP_202_ACCEPTED,
            )
