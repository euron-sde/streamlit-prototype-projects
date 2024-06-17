from __future__ import annotations

import enum  # type: ignore
import uuid  # type: ignore
from datetime import datetime
from typing import TYPE_CHECKING  # type: ignore

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, CreatedUpdatedMixin


if TYPE_CHECKING:
    from src.auth import models as auth_models


class ProductData(Base, CreatedUpdatedMixin):
    __tablename__ = "product_data"

    # id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.uuid_generate_v4())
    product_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    product_category: Mapped[str] = mapped_column(sa.Text, nullable=False)
    product_images: Mapped[str] = mapped_column(sa.Text, nullable=False)
    price: Mapped[float] = mapped_column(sa.Float, nullable=False)
    discount_price: Mapped[float] = mapped_column(sa.Float, nullable=True)
    product_rating: Mapped[float] = mapped_column(sa.Float, nullable=True)
    product_description: Mapped[str] = mapped_column(sa.Text, nullable=True)
    product_specifications: Mapped[str] = mapped_column(sa.Text, nullable=True)


class UserProductData(Base, CreatedUpdatedMixin):
    __tablename__ = "user_product_data"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.uuid_generate_v4())
    user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID, ForeignKey("auth_user.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(sa.UUID, ForeignKey("product_data.product_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    purchase_price: Mapped[float] = mapped_column(sa.Float, nullable=False)
    status: Mapped[str] = mapped_column(sa.Text, nullable=False)

    user: Mapped[auth_models.User] = relationship("User")
    product: Mapped[ProductData] = relationship("ProductData")

    def __repr__(self) -> str:
        return f"<UserProductData {self.id}>"
