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
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseORM):
    id: uuid.UUID
    user_id: uuid.UUID
    role: ChatRole
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
