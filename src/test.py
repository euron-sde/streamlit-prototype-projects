from pydantic import BaseModel

from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()


class UserCreate(BaseModel):
    username: str
    password: str


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        "SELECT * FROM users WHERE username = :username", {"username": username}
    )
    return result.fetchone()


async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@app.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(async_session)):
    db_user = await get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    return await create_user(db, user)


class UserLogin(BaseModel):
    username: str
    password: str


@app.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(async_session)):
    db_user = await get_user_by_username(db, user.username)
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )
    return {"message": "Login successful"}
