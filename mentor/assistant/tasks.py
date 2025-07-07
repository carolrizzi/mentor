from uuid import UUID

from celery.result import AsyncResult
from django.contrib.auth.models import User

from mentor.assistant.agent import get_agent
from mentor.assistant.models import ChatSession
from mentor.core.celery import app


@app.task
def analyze_text(
    user_id: int, session_id: UUID, text: str, title: str | None = None
) -> str | None:
    """
    Generate a title for the text if not provided, then analyze the text.
    """
    agent = get_agent()
    if not title:
        response = agent.generate_title(text)
        if not response:
            return None
        final_title = response.content
    else:
        final_title = title

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

    ChatSession.objects.create(
        id=session_id,
        user=user,
        title=final_title,
    )

    response = agent.analyze_text(session_id=session_id, text=text)
    return response.content if response else None


def get_task_status(task_id):
    res = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": res.status,
        "result": res.result if res.successful() else None,
        "error": str(res.result) if res.failed() else None,
    }


@app.task
def follow_up_question(session_id: UUID, question: str):
    """
    Ask a follow-up question based on the session history.
    """
    response = get_agent().follow_up_question(session_id=session_id, question=question)
    return response.content if response else None
