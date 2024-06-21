from pydantic import BaseModel


class CourseDataInput(BaseModel):
    course_name: str
    description: str
    instructor: str
    course_price: int
    course_timing: str
    course_rating: float
    course_duration: str
    course_status: str
