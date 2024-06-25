import uuid  # type: ignore
from typing import List  # type: ignore

from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db

router = APIRouter()

# Create Routes for data here