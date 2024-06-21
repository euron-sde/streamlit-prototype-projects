# add course data to course
import uuid  # type: ignore
import logging

from fastapi import HTTPException

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.product_data.models import CourseData
from src.product_data.schema import CourseDataInput

logger = logging.getLogger(__name__)

dummy_data = [
    {
        "course_name": "Introduction to Python",
        "description": "Learn the basics of Python programming.",
        "instructor": "Jane Doe",
        "course_price": 100,
        "course_timing": "Mon-Wed-Fri 10:00-11:30 AM",
        "course_rating": 4.5,
        "course_duration": "6 weeks",
        "course_status": "active"
    },
    {
        "course_name": "Data Science with R",
        "description": "An in-depth course on Data Science using R.",
        "instructor": "John Smith",
        "course_price": 200,
        "course_timing": "Tue-Thu 2:00-4:00 PM",
        "course_rating": 4.7,
        "course_duration": "8 weeks",
        "course_status": "active"
    },
    {
        "course_name": "Web Development Bootcamp",
        "description": "Become a full-stack web developer.",
        "instructor": "Alice Johnson",
        "course_price": 300,
        "course_timing": "Mon-Fri 9:00 AM-12:00 PM",
        "course_rating": 4.8,
        "course_duration": "12 weeks",
        "course_status": "active"
    },
    {
        "course_name": "Machine Learning with Python",
        "description": "Learn the fundamentals of Machine Learning.",
        "instructor": "Bob Brown",
        "course_price": 250,
        "course_timing": "Mon-Wed-Fri 1:00-3:00 PM",
        "course_rating": 4.6,
        "course_duration": "10 weeks",
        "course_status": "completed"
    },
    {
        "course_name": "Advanced JavaScript",
        "description": "Master advanced JavaScript concepts.",
        "instructor": "Carol Davis",
        "course_price": 150,
        "course_timing": "Tue-Thu 10:00-11:30 AM",
        "course_rating": 4.4,
        "course_duration": "5 weeks",
        "course_status": "inactive"
    }
]


async def add_course_data_to_db(db: AsyncSession, data: CourseDataInput):
    """
    Add course data to the database.
    """
    course_obj = CourseData(
        course_name=data.course_name,
        description=data.description,
        instructor=data.instructor,
        course_price=data.course_price,
        course_timing=data.course_timing,
        course_rating=data.course_rating,
        course_duration=data.course_duration,
        course_status=data.course_status,
    )
    db.add(course_obj)
    await db.commit()
    await db.refresh(course_obj)


async def get_course_data_from_db(
    db: AsyncSession,
    course_id: uuid.UUID
) -> CourseData:
    """
    Get course data from the database.
    """
    stmt = select(CourseData).where(CourseData.id == course_id)
    course_obj = await db.execute(stmt)
    result = course_obj.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return result[0]


async def get_all_course_data_from_db(db: AsyncSession) -> dict:
    """
    Get all course data from the database.
    """
    stmt = select(CourseData)
    course_obj = await db.execute(stmt)
    course_data = course_obj.scalars().all()
    return [{
        "course_name": course_data.course_name,
        "description": course_data.description,
        "instructor": course_data.instructor,
        "course_price": course_data.course_price,
        "course_timing": course_data.course_timing,
        "course_rating": course_data.course_rating,
        "course_duration": course_data.course_duration,
        "course_status": course_data.course_status,
    } for course_data in course_data]


async def delete_course_data_from_db(db: AsyncSession, course_id: uuid.UUID):
    """
    Delete course data from the database.
    """
    stmt = delete(CourseData).where(CourseData.id == course_id)
    await db.execute(stmt)
    await db.commit()


async def update_course_data_in_db(db: AsyncSession, course_id: uuid.UUID, data: CourseDataInput):
    """
    Update course data in the database.
    """
    stmt = update(CourseData).where(CourseData.id == course_id).values(data.dict())
    await db.execute(stmt)
    await db.commit()
