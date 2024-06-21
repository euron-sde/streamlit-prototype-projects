import uuid  # type: ignore
from typing import List  # type: ignore

from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.product_data.models import CourseData
from src.product_data.schema import CourseDataInput
from src.product_data.services import add_course_data_to_db, get_course_data_from_db, get_all_course_data_from_db, delete_course_data_from_db, update_course_data_in_db

router = APIRouter()


@router.post("/course")
async def add_course_data(
    data: CourseDataInput,
    db: AsyncSession = Depends(get_db)
):
    return await add_course_data_to_db(db, data)


@router.get("/course/{course_id}")
async def get_course_data(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await get_course_data_from_db(db, course_id)


@router.get("/course")
async def get_all_course_data(
    db: AsyncSession = Depends(get_db)
):
    return await get_all_course_data_from_db(db)

@router.delete("/course/{course_id}")
async def delete_course_data(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await delete_course_data_from_db(db, course_id)

@router.put("/course/{course_id}")
async def update_course_data(
    course_id: uuid.UUID,
    data: CourseDataInput,
    db: AsyncSession = Depends(get_db)
):
    return await update_course_data_in_db(db, course_id, data)