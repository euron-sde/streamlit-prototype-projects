import uuid  # type: ignore
import datetime  # type: ignore
from enum import Enum  # type: ignore

from pydantic import BaseModel, ConfigDict


class BaseORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ChatNotFound(Exception):
    pass


class ChatAlreadyExists(Exception):
    pass


class ChatMessageOut(BaseORM):
    id: str
    role: str
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class AllChatMessage(BaseORM):
    id: str
    role: str
    message: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseORM):
    id: str
    user_id: str
    role: ChatRole
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
