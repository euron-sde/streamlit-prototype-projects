import uuid  # type: ignore
import datetime  # type: ignore

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
