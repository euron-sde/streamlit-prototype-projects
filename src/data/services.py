# add course data to course
import uuid  # type: ignore
import logging

from fastapi import HTTPException

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)

# Create services for data here
