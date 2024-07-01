import os
import logging

from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient

from backend.auth import utils
from backend.auth.schemas import AuthUser
from backend.auth.exceptions import InvalidCredentials
from backend.auth.security import hash_password, check_password
from backend.db import get_db

db = get_db("virtual_assistant")


async def create_user(user_data: AuthUser) -> Dict[str, Any]:
    hashed_password = hash_password(user_data.password)
    created_user = {
        "email": user_data.email,
        "password": hashed_password,
    }
    result = await db["users"].insert_one(created_user)
    created_user["_id"] = result.inserted_id
    return created_user


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(user_id):
        return None
    return await db["users"].find_one({"_id": ObjectId(user_id)})


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return await db["users"].find_one({"email": email})


async def create_refresh_token(user_id: str, refresh_token: Optional[str] = None) -> str:
    if not refresh_token:
        refresh_token = utils.generate_random_alphanum(64)

    new_refresh_token = {
        "refresh_token": refresh_token,
        "expires_at": utils.calculate_refresh_token_expiry(),
        "user_id": user_id,
    }
    await db["refresh_tokens"].insert_one(new_refresh_token)
    return refresh_token


async def get_refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    return await db["refresh_tokens"].find_one({"refresh_token": refresh_token})


async def expire_refresh_token(refresh_token_uuid: str) -> None:
    if not ObjectId.is_valid(refresh_token_uuid):
        raise ValueError("Invalid refresh_token_uuid")

    await db["refresh_tokens"].update_one(
        {"_id": ObjectId(refresh_token_uuid)},
        {"$set": {"expires_at": datetime.now()}}
    )


async def authenticate_user(auth_data: AuthUser) -> Dict[str, Any]:
    user = await get_user_by_email(auth_data.email)
    if not user or not check_password(auth_data.password, user["password"]):
        raise InvalidCredentials("Invalid email or password")

    return user
