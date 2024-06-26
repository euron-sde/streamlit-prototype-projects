import random  # type: ignore
import string  # type: ignore

from typing import Any  # type: ignore
from datetime import datetime, timedelta  # type: ignore

from backend.config import settings
from backend.auth.config import auth_config


ALPHA_NUM = string.ascii_letters + string.digits


def get_refresh_token_settings(
    refresh_token: str,
    expired: bool = False,
) -> dict[str, Any]:
    base_cookie = {
        "key": auth_config.REFRESH_TOKEN_KEY,
        "httponly": True,
        "samesite": "none",
        "secure": auth_config.SECURE_COOKIES,
        "domain": settings.SITE_DOMAIN,
    }
    if expired:
        return base_cookie

    return {
        **base_cookie,
        "value": refresh_token,
        "max_age": auth_config.REFRESH_TOKEN_EXP,
    }


def generate_random_alphanum(length: int = 20) -> str:
    return "".join(random.choices(ALPHA_NUM, k=length))

def calculate_refresh_token_expiry() -> datetime:
    return datetime.utcnow() + timedelta(seconds=auth_config.REFRESH_TOKEN_EXP)