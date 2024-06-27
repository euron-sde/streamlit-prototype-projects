import logging
from datetime import datetime, timezone  # type: ignore

from typing import Any  # type: ignore
from fastapi import Depends, Cookie
from datetime import datetime, timezone  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import service
from backend.auth.schemas import AuthUser
from backend.auth.exceptions import EmailTaken, RefreshTokenNotValid

logger = logging.getLogger(__name__)


async def valid_user_create(
    user: AuthUser,
) -> AuthUser:

    logger.info(user)
    if await service.get_user_by_email(user.email):
        raise EmailTaken()

    return user


async def valid_refresh_token(
    refresh_token: str = Cookie(..., alias="refreshToken"),
) -> dict[str, Any]:
    db_refresh_token = await service.get_refresh_token(refresh_token)

    if not db_refresh_token:
        raise RefreshTokenNotValid()

    if not _is_valid_refresh_token(db_refresh_token):
        raise RefreshTokenNotValid()

    return db_refresh_token


async def valid_refresh_token_user(
    refresh_token: dict[str, Any] = Depends(valid_refresh_token),
) -> dict[str, Any]:
    user = await service.get_user_by_id(refresh_token["user_id"])
    if not user:
        raise RefreshTokenNotValid()

    return user


def _is_valid_refresh_token(db_refresh_token: dict[str, Any]) -> bool:
    expires_at = datetime.fromisoformat(str(db_refresh_token.expires_at)).astimezone(timezone.utc)
    return datetime.now(timezone.utc) <= expires_at
