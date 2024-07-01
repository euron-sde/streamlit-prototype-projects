import logging

from typing import Any  # type: ignore
from fastapi import APIRouter, HTTPException, Depends, Body, Request

from backend.chat.chat import Chat
from backend.auth import dependencies as auth_deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat/start")
async def create_chat(
    user_id: dict[str, Any] = Depends(auth_deps.valid_refresh_token),
):
    try:
        chat = Chat(user_id=user_id["user_id"])
        return await chat.initialize_task_chat()

    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the chat.",
        ) from e


@router.post("/chat")
async def add_message_to_chat(
    request: Request,
    is_image: bool = False,
    streaming: bool = False,
    image_data: str = Body(None, embed=True),
    message: str = Body(..., embed=True),
    user_id: dict[str, Any] = Depends(auth_deps.valid_refresh_token),
):
    try:
        chat = Chat(user_id=user_id['user_id'])

        if is_image:
            return await chat.vision_chat(
                user_message=message,
                image_data=image_data,
            )

        if streaming:
            return await chat.task_chat(
                user_message=message,
                stream=streaming
            )

        return await chat.task_chat(
            user_message=message
        )

    except Exception as e:
        logger.error(f"Error adding message to chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding the message to the chat.",
        ) from e


@router.get("/allChat")
async def get_all_chat(
    user_id: dict[str, Any] = Depends(auth_deps.valid_refresh_token),
):
    try:
        chat = Chat(user_id=user_id['user_id'])
        return await chat.get_all_messages()

    except Exception as e:
        logger.error(f"Error fetching all chats: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching all chats.",
        ) from e
