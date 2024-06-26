from __future__ import annotations

import enum  # type: ignore
import uuid  # type: ignore
from typing import TYPE_CHECKING  # type: ignore

import sqlalchemy as sa
from sqlalchemy_file.file import File
from sqlalchemy_file.types import ImageField
from sqlalchemy_file.validators import SizeValidator
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config import settings


if TYPE_CHECKING:
    from backend.auth import models as auth_models


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(Base, CreatedUpdatedMixin):
    __tablename__ = "chat_message"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID, ForeignKey("auth_user.id"), nullable=False)
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    role: Mapped[ChatRole] = mapped_column(sa.Enum(ChatRole, name="chat_role"), nullable=False)

    user: Mapped[auth_models.User] = relationship("User")  # Define the relationship to the User model

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id} from user {self.user_id}>"


class ChatImage(Base, CreatedUpdatedMixin):
    __tablename__ = "chat_images"

    id: Mapped[int] = mapped_column(primary_key=True)

    file: Mapped[File] = mapped_column(
        ImageField(
            thumbnail_size=(512, 512),
            validators=[SizeValidator(
                max_size=settings.MAX_IMAGE_UPLOAD_SIZE)],
        ),
        nullable=False,
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chat_message.id"), nullable=True)
