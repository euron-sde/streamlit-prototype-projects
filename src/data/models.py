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

# Create models for data here