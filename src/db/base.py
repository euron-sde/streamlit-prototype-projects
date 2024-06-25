from datetime import datetime  # type: ignore

from sqlalchemy import MetaData
from sqlalchemy.sql import expression
from sqlalchemy.types import DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models

    Update the naming convention for all models to produce an explicit name for
    all constraints.
    """

    metadata = MetaData(
        naming_convention={
            "ix": "%(column_0_label)s_idx",
            "uq": "%(table_name)s_%(column_0_name)s_key",
            "ck": "%(table_name)s_%(constraint_name)s_check",
            "fk": "%(table_name)s_%(column_0_name)s_fkey",
            "pk": "%(table_name)s_pkey",
        }
    )


class utcnow(expression.FunctionElement):
    """A function that returns the current time in UTC

    See:
    https://docs.sqlalchemy.org/en/20/core/compiler.html#utc-timestamp-function
    """

    type = DateTime()
    name = "utcnow"


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


class CreatedUpdatedMixin:
    """Adds created_at, updated_at columns to a model"""

    created_at: Mapped[datetime] = mapped_column(server_default=utcnow(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=utcnow(), onupdate=utcnow(), nullable=False)
