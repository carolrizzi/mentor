from contextlib import contextmanager
from functools import cache
from logging import getLogger
from os import makedirs, path
from pathlib import Path
from shutil import rmtree
from uuid import UUID

from celery.result import AsyncResult
from django.contrib.auth.models import User

from mentor.assistant.agent import (
    get_assistant_agent,
    get_system_agent,
)
from mentor.assistant.models import ChatSession
from mentor.assistant.settings import Settings
from mentor.core import settings as django_settings
from mentor.core.celery import app

LOG_BASE_NAME = __name__


@cache
def get_language_dir(language: str) -> Path:
    return django_settings.BASE_DIR / "assistant" / "prompts" / "assistant" / language


def prompt_language_exists(language: str) -> bool:
    lang_path = get_language_dir(language)
    return path.isdir(lang_path)


@contextmanager
def create_language(language: str):
    lang_dir = get_language_dir(language)
    makedirs(lang_dir, exist_ok=True)
    try:
        yield lang_dir
    except Exception:
        rmtree(lang_dir, ignore_errors=True)
        raise


def process_language(text: str) -> str:
    logger = getLogger(LOG_BASE_NAME + ".process_language")
    def_lang = Settings().default_language

    language = None
    try:
        system_agent = get_system_agent()
        language = system_agent.detect_language(text)
        if prompt_language_exists(language):
            logger.info(f"Detected text language '{language}' already exists.")
            return language

        with create_language(language) as new_lang_dir:
            logger.info(
                f"Creating new language prompts '{language}' under '{new_lang_dir}'"
            )
            def_lang_dir = get_language_dir(language=def_lang)

            for file in def_lang_dir.iterdir():
                if not file.is_file():
                    continue
                prompt = file.read_text(encoding="utf-8")
                translated_prompt = system_agent.translate_prompt(
                    prompt=prompt, language=language
                )
                new_prompt_path = new_lang_dir / file.name
                logger.info(f"Writing prompt to '{new_prompt_path}'")
                new_prompt_path.write_text(translated_prompt, encoding="utf-8")
            logger.info(f"All prompts for language '{language}' created!")
        return language
    except Exception as e:
        msg = "Failed processing "
        msg += f"new languange '{language}'." if language else "new unknown language."
        logger.error(
            f"{msg} Falling back to default language '{def_lang}'. Reason: {e}"
        )
        return def_lang


@app.task
def analyze_text(
    user_id: int,
    session_id: UUID,
    text: str,
    title: str | None = None,
) -> str | None:
    """
    Generate a title for the text if not provided, then analyze the text.
    """

    language = process_language(text=text)
    assistant_agent = get_assistant_agent(language)

    if not title:
        response = assistant_agent.generate_title(text)
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
        language=language,
    )

    response = assistant_agent.analyze_text(session_id=session_id, text=text)
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
    session = ChatSession.objects.get(id=session_id)
    assistant_agent = get_assistant_agent(session.language)
    response = assistant_agent.follow_up_question(
        session_id=session_id, question=question
    )
    return response.content if response else None
