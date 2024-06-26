import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())  # load environment variables from .env file


class AuthConfig(BaseSettings):
    JWT_ALGORITHM: str = os.environ.get("JWT_ALG")
    SECRET_KEY: str = os.environ.get("JWT_SECRET")
    JWT_EXPIRATION: int = 100  # minutes

    REFRESH_TOKEN_KEY: str = "refreshToken"
    REFRESH_TOKEN_EXP: int = 60 * 60 * 24 * 21  # 21 days

    SECURE_COOKIES: bool = True


auth_config = AuthConfig()
