from abc import ABC, abstractmethod
from enum import StrEnum
from functools import cache, cached_property
from pathlib import Path
from uuid import UUID

from django.conf import settings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_postgres import PostgresChatMessageHistory
from langchain_together import ChatTogether
from psycopg_pool import ConnectionPool

from mentor.assistant.models import ChatMessage
from mentor.assistant.settings import (
    AiPlatform,
    OpenAiModelSettings,
    PostgreSettings,
    Settings,
    TogetherAiModelSettings,
)


class PromptType(StrEnum):
    SYSTEM = "system"
    HUMAN = "human"


class PromptName(StrEnum):
    TEXT_ANALYSIS = "text_analysis"
    FOLLOW_UP_QUESTIONS = "follow_up"
    GENERATE_TITLE = "generate_title"


def get_prompt_file_path(
    prompt_name: PromptName, prompt_type: PromptType, language: str
) -> Path:
    return (
        settings.BASE_DIR
        / "assistant"
        / "prompts"
        / "assistant"
        / language
        / f"{prompt_name.value}_{prompt_type.value}.txt"
    )


def read_text_file(file_path: str | Path) -> str:
    with open(file_path, encoding="utf-8") as file:
        return file.read()


@cache
def get_prompt(prompt_name: PromptName, prompt_type: PromptType, language: str) -> str:
    return read_text_file(
        get_prompt_file_path(
            prompt_name=prompt_name, prompt_type=prompt_type, language=language
        )
    )


@cache
def get_connection_pool() -> ConnectionPool:
    settings = PostgreSettings()
    return ConnectionPool(
        conninfo=f"dbname={settings.pg_db_name} user={settings.pg_username} "
        f"password={settings.pg_password.get_secret_value()} host={settings.pg_host} "
        f"port={settings.pg_port}",
        max_size=10,
    )


def get_session_history(session_id):
    with get_connection_pool().connection() as conn:
        return PostgresChatMessageHistory(
            ChatMessage._meta.db_table,
            session_id,
            sync_connection=conn,
        )


def get_prompt_template(prompt_name: PromptName, language: str) -> ChatPromptTemplate:
    system_prompt = get_prompt(prompt_name, PromptType.SYSTEM, language=language)
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )


def get_chain_with_history(
    prompt_name: PromptName, model: BaseChatModel, language: str
):
    prompt = get_prompt_template(prompt_name=prompt_name, language=language)
    chain = prompt | model
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
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


class Assistant(ABC):
    """
    Base class for the AI assistant.
    It provides methods to analyze text, ask follow-up questions, and generate titles.
    """

    def __init__(self, language: str = "pt"):
        self.language = language

    @property
    @abstractmethod
    def model(self) -> BaseChatModel:
        """
        Returns the model used by the assistant.
        Should be implemented by subclasses to return the specific model instance.
        """
        raise NotImplementedError

    def analyze_text(self, session_id: UUID, text: str):
        chain_with_history = get_chain_with_history(
            prompt_name=PromptName.TEXT_ANALYSIS,
            model=self.model,
            language=self.language,
        )
        question = get_prompt(
            PromptName.TEXT_ANALYSIS, PromptType.HUMAN, language=self.language
        )
        return chain_with_history_invoke(
            chain=chain_with_history, session_id=session_id, question=question + text
        )

    def follow_up_question(self, session_id: UUID, question: str):
        chain_with_history = get_chain_with_history(
            prompt_name=PromptName.FOLLOW_UP_QUESTIONS,
            model=self.model,
            language=self.language,
        )
        return chain_with_history_invoke(
            chain=chain_with_history, session_id=session_id, question=question
        )

    def generate_title(self, text: str):
        system_prompt = get_prompt(
            prompt_name=PromptName.GENERATE_TITLE,
            prompt_type=PromptType.SYSTEM,
            language=self.language,
        )
        human_prompt = get_prompt(
            prompt_name=PromptName.GENERATE_TITLE,
            prompt_type=PromptType.HUMAN,
            language=self.language,
        )
        human_prompt += text

        return self.model.invoke(
            [
                ("system", system_prompt),
                ("human", human_prompt),
            ]
        )


class TogetherAiAssistant(Assistant):
    """
    AI assistant that uses Together AI platform for text analysis.
    """

    @cached_property
    def model(self) -> ChatTogether:
        settings = TogetherAiModelSettings()
        return ChatTogether(
            model=settings.model,
            temperature=settings.temperature,
            api_key=settings.api_key.get_secret_value(),
        )


class OpenAiAssistant(Assistant):
    """
    AI assistant that uses OpenAI platform for text analysis.
    This is a placeholder for future implementation.
    """

    @cached_property
    def model(
        self,
    ) -> ChatOpenAI:
        settings = OpenAiModelSettings()
        return ChatOpenAI(
            model=settings.model,
            temperature=settings.temperature,
            api_key=settings.api_key.get_secret_value(),
        )


class AzureOpenAiAssistant(Assistant):
    """
    AI assistant that uses Azure OpenAI platform for text analysis.
    This is a placeholder for future implementation.
    """

    @cached_property
    def model(
        self,
    ) -> BaseChatModel:  # return langchain_openai.chat_models.azure.AzureChatOpenAI
        # settings = mentor.assistant.settings.AwsBedrockModelSettings()
        raise NotImplementedError("Azure OpenAI Assistant is not implemented yet.")


class AwsBedrockAssistant(Assistant):
    """
    AI assistant that uses AWS Bedrock platform for text analysis.
    This is a placeholder for future implementation.
    """

    @cached_property
    def model(
        self,
    ) -> BaseChatModel:  # should return langchain_aws.chat_models.bedrock.ChatBedrock
        # settings = mentor.assistant.settings.AzureOpenAiModelSettings()
        raise NotImplementedError("AWS Bedrock Assistant is not implemented yet.")


def get_agent() -> Assistant:
    """
    Returns an instance of the AI assistant.
    This function can be used to get the specific implementation of the assistant.
    """
    ai_platform = Settings().ai_platform
    match ai_platform:
        case AiPlatform.TOGETHER_AI:
            return TogetherAiAssistant()
        case AiPlatform.OPENAI:
            return OpenAiAssistant()
        case AiPlatform.AZURE_OPENAI:
            return AzureOpenAiAssistant()
        case AiPlatform.AWS_BEDROCK:
            return AwsBedrockAssistant()
    raise ValueError(f"Unsupported AI platform: {ai_platform.value}")
