import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends, Body, Request


from src.db import get_db
from src.chat.chat import Chat
from src.auth import models as auth_models
from src.auth import dependencies as auth_deps

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat/start")
async def create_chat(
    db: AsyncSession = Depends(get_db),
    user: auth_models.RefreshToken = Depends(auth_deps.valid_refresh_token),
):
    try:
        chat = Chat(db=db, user_id=user.user_id)
        return await chat.initialize_task_chat(db=db)

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
    db: AsyncSession = Depends(get_db),
    user: auth_models.RefreshToken = Depends(auth_deps.valid_refresh_token),
):
    try:
        chat = Chat(db=db, user_id=user.user_id)

        # TODO: need to discuss need to add image in the chat
        if is_image:
            return await chat.vision_chat(
                db=db,
                user_message=message,
                image_data=image_data,
            )
        if streaming:
            return await chat.task_chat(db=db, request=request, user_message=message, stream=streaming)

        return await chat.task_chat(db=db, request=request, user_message=message)

    except Exception as e:
        logger.error(f"Error adding message to whiteboard chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding the message to the whiteboard chat.",
        ) from e


@router.get("/allChat")
async def get_all_chat(
    db: AsyncSession = Depends(get_db),
    user: auth_models.RefreshToken = Depends(auth_deps.valid_refresh_token),
):
    chat = Chat(db=db, user_id=user.user_id)
    return await chat.get_all_messages()
