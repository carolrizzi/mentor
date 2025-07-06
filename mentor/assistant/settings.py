from pydantic import SecretStr
from pydantic_settings import BaseSettings


class MentorBaseSettings(BaseSettings):
    class Config:
        env_file = ".env"
        extra = "ignore"


class Settings(MentorBaseSettings):
    access_token_lifetime_minutes: int = 30
    refresh_token_lifetime_days: int = 2
    redis_url: str = "redis://localhost:6379/0"
    # redis: str = "redis://redis:6379/0"


class ModelSettings(MentorBaseSettings):
    model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    together_api_key: SecretStr
    temperature: float = 0.0


class PostgreSettings(MentorBaseSettings):
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_username: str = "mentor"
    pg_password: SecretStr
    pg_db_name: str = "mentor"
