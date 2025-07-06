from uuid import UUID

from celery.result import AsyncResult
from django.contrib.auth.models import User

from mentor.celery import app

from .agent import analyze_text as agent_analyze_text
from .agent import follow_up_question as agent_follow_up_question
from .agent import generate_title
from .models import ChatSession


@app.task
def analyze_text(
    user_id: int, session_id: UUID, text: str, title: str | None = None
) -> str | None:
    """
    Generate a title for the text if not provided, then analyze the text.
    """

    if not title:
        response = generate_title(text)
        if not response:
            return None
        title = response.content

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

    ChatSession.objects.create(
        id=session_id,
        user=user,
        title=title,
    )

    response = agent_analyze_text(session_id=session_id, text=text)
    return response.content if response else None


def get_task_status(task_id):
    res = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": res.status,  # e.g. PENDING, STARTED, SUCCESS, FAILURE
        "result": res.result if res.successful() else None,
        "error": str(res.result) if res.failed() else None,
    }


@app.task
def follow_up_question(session_id: UUID, question: str):
    """
    Ask a follow-up question based on the session history.
    """
    response = agent_follow_up_question(session_id=session_id, question=question)
    return response.content if response else None
