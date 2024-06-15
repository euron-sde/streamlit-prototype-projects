from uuid import UUID  # type: ignore
from typing import Optional  # type: ignore
from datetime import datetime  # type: ignore

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, CreatedUpdatedMixin


class User(Base, CreatedUpdatedMixin):
    __tablename__ = "auth_user"

    id: Mapped[UUID] = mapped_column(sa.UUID, primary_key=True, server_default=func.uuid_generate_v4())
    email: Mapped[str] = mapped_column(sa.String, index=True, nullable=False)
    password: Mapped[str]
    is_admin: Mapped[Optional[bool]] = mapped_column(
        sa.Boolean, server_default="false", nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class RefreshToken(Base, CreatedUpdatedMixin):
    __tablename__ = "auth_refresh_token"

    id: Mapped[UUID] = mapped_column(sa.UUID, primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[UUID] = mapped_column(sa.UUID, ForeignKey(
        "auth_user.id", ondelete="CASCADE"), nullable=False)
    user: Mapped[User] = relationship("User")
    refresh_token: Mapped[str] = mapped_column(sa.String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)

    # def __repr__(self) -> str:
    #     return f"<RefreshToken {self.uuid}>"
