import os

from bson import ObjectId
from typing import Optional  # type: ignore
from datetime import datetime  # type: ignore
from motor.motor_asyncio import AsyncIOMotorClient


from backend.auth import utils
from backend.auth.schemas import AuthUser
from backend.auth.exceptions import InvalidCredentials
from backend.auth.security import hash_password, check_password

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))


async def create_user(user_data: AuthUser) -> dict:
    hashed_password = hash_password(user_data.password)
    created_user = {
        "email": user_data.email,
        "password": hashed_password
    }
    await client["users"].insert_one(created_user)
    return created_user


async def get_user_by_id(user_id: str) -> Optional[dict]:
    return await client["users"].find_one({"_id": ObjectId(user_id)})


async def get_user_by_email(email: str) -> Optional[dict]:
    return await client["users"].find_one({"email": email})


async def create_refresh_token(user_id: str, refresh_token: Optional[str] = None) -> str:
    if not refresh_token:
        refresh_token = utils.generate_random_alphanum(64)

    new_refresh_token = {
        "refresh_token": refresh_token,
        "expires_at": utils.calculate_refresh_token_expiry(),
        "user_id": user_id
    }
    await client["refresh_tokens"].insert_one(new_refresh_token)
    return refresh_token


async def get_refresh_token(refresh_token: str) -> Optional[dict]:
    return await client["refresh_tokens"].find_one(
        {"refresh_token": refresh_token}
    )


async def expire_refresh_token(refresh_token_uuid: str) -> None:
    await client["refresh_tokens"].update_one(
        {"_id": ObjectId(refresh_token_uuid)},
        {"$set": {"expires_at": datetime.now()}}
    )


async def authenticate_user(auth_data: AuthUser) -> dict:
    user = await get_user_by_email(auth_data.email)
    if not user or not check_password(auth_data.password, user["password"]):
        raise InvalidCredentials()

    return user