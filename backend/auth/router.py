import logging

from uuid import UUID  # type: ignore
from typing import Any  # type: ignore

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Response, status

from backend.auth import jwt, service, utils
from backend.auth.dependencies import (
    valid_refresh_token,
    valid_refresh_token_user,
    valid_user_create,
)
from backend.auth.schemas import AccessTokenResponse, AuthUser, UserResponse

router = APIRouter()

logger = logging.getLogger(__name__)


# Create user
@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    auth_data: AuthUser = Depends(valid_user_create),
) -> UserResponse:

    user = await service.create_user(auth_data)
    logger.info(f"User created: {user['_id']}")
    return UserResponse(email=user["email"])


# @router.get("/users/me", response_model=UserResponse)
# async def get_my_account(
#     jwt_data: JWTData = Depends(parse_jwt_user_data),
# ) -> dict[str, str]:
#     logger.info(f"User requested: {jwt_data.user_id}")

#     user = await service.get_user_by_id(jwt_data.user_id)

#     return {
#         "email": user["email"],
#     }


# create yuser token and refresh token
# @router.post("/users/tokens", response_model=AccessTokenResponse)
# async def auth_user(
#     auth_data: AuthUser,
#     response: Response,
#     db: AsyncSession = Depends(get_db),
# ) -> AccessTokenResponse:
#     user = await service.authenticate_user(db, auth_data)
#     refresh_token_value = await service.create_refresh_token(db, user_id=user.id)

#     response.set_cookie(**utils.get_refresh_token_settings(refresh_token_value))

#     return AccessTokenResponse(
#         access_token=jwt.create_access_token(user=user),
#         refresh_token=refresh_token_value,
#     )


@router.post("/users/tokens", response_model=AccessTokenResponse)
async def auth_user(
    auth_data: AuthUser,
    response: Response,
) -> AccessTokenResponse:
    user = await service.authenticate_user(auth_data)
    refresh_token_value = await service.create_refresh_token(user_id=user["_id"])

    response.set_cookie(**utils.get_refresh_token_settings(refresh_token_value))

    return AccessTokenResponse(
        access_token=jwt.create_access_token(user=user),
        refresh_token=refresh_token_value,
    )


# @router.delete("/users/tokens")
# async def logout_user(
#     response: Response,
#     refresh_token: dict[str, Any] = Depends(valid_refresh_token),
# ) -> None:
#     await service.expire_refresh_token(refresh_token["uuid"])

#     response.delete_cookie(
#         **utils.get_refresh_token_settings(refresh_token["refresh_token"], expired=True)
#     )
