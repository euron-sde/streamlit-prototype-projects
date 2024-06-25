import os
import logging

from enum import Enum  # type: ignore
from pathlib import Path  # type: ignore

from typing import Any  # type: ignore
from pydantic import RedisDsn, model_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

PROJECT_ROOT = Path(__file__).parent.parent.parent
logger = logging.getLogger(__name__)


class Environment(str, Enum):
    DEV = "DEV"
    TESTING = "TESTING"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

    @property
    def is_debug(self):
        return self in (self.DEV, self.STAGING, self.TESTING)

    @property
    def is_testing(self):
        return self == self.TESTING

    @property
    def is_deployed(self) -> bool:
        return self in (self.STAGING, self.PRODUCTION)


class Config(BaseSettings):

    # REDIS_URL: str | RedisDsn = os.getenv("REDIS_URL")
    # DATABASE_URL: str = os.getenv("DATABASE_URL")

    CORS_ORIGINS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    CORS_ORIGINS_REGEX: str | None = None

    ENVIRONMENT: Environment = Environment.DEV
    DEBUG: bool = False

    SENTRY_DSN: str | None = None

    APP_VERSION: str = "0.1.0"
    PROJECT_NAME: str = "sales-support-chatBot"
    SITE_DOMAIN: str = "localhost"

    # database settings
    DB_USER: str = os.environ.get("DB_USER")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD")
    DB_NAME: str = os.environ.get("DB_NAME")
    DB_NAME_TEST: str | None = None
    DB_PORT: str = os.environ.get("DB_PORT")
    DB_HOST: str = os.environ.get("DB_HOST")
    # MIGRATIONS_DIR: Path = PROJECT_ROOT / "migrations" / "versions"

    @property
    def DB_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @model_validator(mode="after")
    def validate_sentry_non_local(self) -> "Config":
        if self.ENVIRONMENT.is_deployed and not self.SENTRY_DSN:
            raise ValueError("Sentry is not set")

        return self

    # redis settings
    REDIS_HOST: str | None = None
    REDIS_PORT: int | None = None
    REDIS_URL: str | None = None
    REDIS_DB: int | None = 0

    # chroma settings
    CHROMA_HOST: str | None = None
    CHROMA_PORT: int | None = None

    OPENAI_API_KEY: str | None = os.environ.get("OPENAI_API_KEY")
    # ANTHROPIC_API_KEY: str | None = os.environ.get("ANTHROPIC_API_KEY")

    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str | None = None

    SERPER_API_KEY: str | None = None
    MAX_IMAGE_UPLOAD_SIZE: int = 1024 * 1024 * 10  # 10MB


settings = Config()

app_configs: dict[str, Any] = {"title": "App API"}
if settings.ENVIRONMENT.is_deployed:
    app_configs["root_path"] = f"/v{settings.APP_VERSION}"

if not settings.ENVIRONMENT.is_debug:
    app_configs["openapi_url"] = None  # hide docs
