from __future__ import annotations

import enum  # type: ignore
import uuid  # type: ignore

from typing import TYPE_CHECKING  # type: ignore

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, CreatedUpdatedMixin


if TYPE_CHECKING:
    from src.auth import models as auth_models


class CourseStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"


class CourseData(Base, CreatedUpdatedMixin):
    __tablename__ = "course_data"

    course_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.uuid_generate_v4())
    course_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=True)
    instructor: Mapped[str] = mapped_column(sa.Text, nullable=False)
    course_price: Mapped[int] = mapped_column(sa.INTEGER, nullable=False)
    course_timing: Mapped[str] = mapped_column(sa.Text, nullable=False)
    course_rating: Mapped[float] = mapped_column(sa.FLOAT, nullable=True)
    course_duration: Mapped[str] = mapped_column(sa.Text, nullable=False)
    course_status: Mapped[CourseStatus] = mapped_column(sa.Enum(CourseStatus), nullable=False)
