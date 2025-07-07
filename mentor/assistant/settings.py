from enum import StrEnum

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class AiPlatform(StrEnum):
    TOGETHER_AI = "together.ai"
    OPENAI = "openai"
    AWS_BEDROCK = "aws_bedrock"
    AZURE_OPENAI = "azure_openai"


class MentorBaseSettings(BaseSettings):
    class Config:
        env_file = ".env"
        extra = "ignore"


class Settings(MentorBaseSettings):
    access_token_lifetime_minutes: int = 30
    refresh_token_lifetime_days: int = 2
    redis_url: str = "redis://localhost:6379/0"
    ai_platform: AiPlatform = AiPlatform.TOGETHER_AI


class ModelSettings(MentorBaseSettings):
    model: str
    api_key: SecretStr
    temperature: float = 0.0
    # ...
    # Any other global model configs


class TogetherAiModelSettings(ModelSettings):
    model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    # ...
    # any other configs that are specific to Together AI


class AzureOpenAiModelSettings(ModelSettings):
    deployment_name: str
    # ...
    # any other configs that are specific to Azure OpenAI


class OpenAiModelSettings(ModelSettings): ...


class AwsBedrockModelSettings(ModelSettings):
    region: str = "us-east-1"
    # ...
    # any other configs that are specific to AWS Bedrock


class PostgreSettings(MentorBaseSettings):
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_username: str = "mentor"
    pg_password: SecretStr
    pg_db_name: str = "mentor"
