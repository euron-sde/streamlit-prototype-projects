from typing import Any  # type: ignore
from jose import JWTError, jwt
from datetime import datetime, timedelta  # type: ignore

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer


from backend.auth.schemas import JWTData
from backend.auth.config import auth_config
from backend.auth.exceptions import AuthorizationFailed, AuthRequired, InvalidToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/tokens", auto_error=False)


def create_access_token(
    *,
    user: dict,
) -> str:
    # if user.is_admin:
    #     jwt_data = {
    #         "sub": str(user.id),
    #         "exp": datetime.utcnow() + expires_delta,
    #         "is_admin": user.is_admin,
    #     }
    # else:
    jwt_data = {
        "email": str(user["email"]),
        # "exp": datetime.utcnow() + expires_delta,
        "password": str(user["password"]),
    }

    return jwt.encode(jwt_data, auth_config.SECRET_KEY, algorithm=auth_config.JWT_ALGORITHM)


async def parse_jwt_user_data_optional(
    token: str = Depends(oauth2_scheme),
) -> JWTData | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, auth_config.SECRET_KEY, algorithms=[auth_config.JWT_ALGORITHM]
        )
    except JWTError as e:
        raise InvalidToken() from e

    return JWTData(**payload)


async def parse_jwt_user_data(
    token: JWTData | None = Depends(parse_jwt_user_data_optional),
) -> JWTData:
    if not token:
        raise AuthRequired()

    return token


async def parse_jwt_admin_data(
    token: JWTData = Depends(parse_jwt_user_data),
) -> JWTData:
    if not token.is_admin:
        raise AuthorizationFailed()

    return token


async def validate_admin_access(
    token: JWTData | None = Depends(parse_jwt_user_data_optional),
) -> None:
    if token and token.is_admin:
        return

    raise AuthorizationFailed()


class TokenVerificationError(HTTPException):
    """Custom exception class for token verification errors."""

    def __init__(self, detail: str = "Token verification failed"):
        super().__init__(status_code=401, detail=detail)


async def verify_token(api_key: str) -> None:
    """
    Verify the JWT token.
    """
    try:
        jwt.decode(
            api_key, auth_config.SECRET_KEY, algorithms=[auth_config.JWT_ALGORITHM]
        )
    except JWTError as e:
        raise TokenVerificationError("Unauthorized user") from e


async def authenticate_jwt(request: Request) -> None:
    """
    Middleware function to authenticate API keys.
    """
    # Extract headers
    api_key = request.headers.get("Api-Key")
    if api_key is None:
        raise HTTPException(status_code=401, detail="API Key is missing")

    # Verify JWT token
    await verify_token(api_key)
