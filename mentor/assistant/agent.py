from enum import StrEnum
from functools import cache
from uuid import UUID

from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_postgres import PostgresChatMessageHistory
from langchain_together import ChatTogether
from psycopg_pool import ConnectionPool

from mentor.assistant.settings import ModelSettings, PostgreSettings


class PromptType(StrEnum):
    SYSTEM = "system"
    HUMAN = "human"


class PromptName(StrEnum):
    TEXT_ANALYSIS = "text_analysis"
    FOLLOW_UP_QUESTIONS = "follow_up"
    GENERATE_TITLE = "generate_title"


def get_prompt_file_path(prompt_name: PromptName, prompt_type: PromptType) -> str:
    return (
        settings.BASE_DIR
        / "assistant"
        / "prompts"
        / f"{prompt_name.value}_{prompt_type.value}.txt"
    )


def read_text_file(file_path: str) -> str:
    with open(file_path, encoding="utf-8") as file:
        return file.read()


@cache
def get_prompt(prompt_name: PromptName, prompt_type: PromptType) -> str:
    return read_text_file(
        get_prompt_file_path(prompt_name=prompt_name, prompt_type=prompt_type)
    )


@cache
def get_connection_pool() -> ConnectionPool:
    settings = PostgreSettings()
    return ConnectionPool(
        conninfo=f"dbname={settings.pg_db_name} user={settings.pg_username} "
        f"password={settings.pg_password.get_secret_value()} host={settings.pg_host} "
        f"port={settings.pg_port}",
        # TODO: What is a good max size for the connection pool?
        # max_size=10,
    )


@cache
def get_model() -> ChatTogether:
    settings = ModelSettings()
    return ChatTogether(
        model=settings.model,
        temperature=settings.temperature,
        api_key=settings.together_api_key.get_secret_value(),
    )


def get_session_history(table_name: str):
    def _get_session_history(session_id):
        with get_connection_pool().connection() as conn:
            return PostgresChatMessageHistory(
                table_name,
                session_id,
                sync_connection=conn,
            )

    return _get_session_history


def get_prompt_template(prompt_name: PromptName) -> ChatPromptTemplate:
    system_prompt = get_prompt(prompt_name, PromptType.SYSTEM)
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )


def get_chain_with_history(prompt_name: PromptName):
    prompt = get_prompt_template(prompt_name)
    chain = prompt | get_model()
    return RunnableWithMessageHistory(
        chain,
        # TODO: move this table name to a settings file??
        get_session_history(table_name="chat_message"),
        input_messages_key="question",
        history_messages_key="history",
    )


def chain_with_history_invoke(
    chain: RunnableWithMessageHistory, session_id: UUID, question: str
):
    return chain.invoke(
        {"question": question},
        config={"configurable": {"session_id": str(session_id)}},
    )


def analyze_text(session_id: UUID, text: str):
    chain_with_history = get_chain_with_history(PromptName.TEXT_ANALYSIS)
    question = get_prompt(PromptName.TEXT_ANALYSIS, PromptType.HUMAN)
    return chain_with_history_invoke(
        chain=chain_with_history, session_id=session_id, question=question + text
    )


def follow_up_question(session_id: UUID, question: str):
    chain_with_history = get_chain_with_history(PromptName.FOLLOW_UP_QUESTIONS)
    return chain_with_history_invoke(
        chain=chain_with_history, session_id=session_id, question=question
    )


def generate_title(text: str):
    system_prompt = get_prompt(PromptName.GENERATE_TITLE, PromptType.SYSTEM)
    human_prompt = get_prompt(PromptName.GENERATE_TITLE, PromptType.HUMAN)
    human_prompt += text

    return get_model().invoke(
        [
            ("system", system_prompt),
            ("human", human_prompt),
        ]
    )
