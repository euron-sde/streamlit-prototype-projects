import sentry_sdk  # type: ignore
import redis.asyncio as aioredis

from typing import AsyncGenerator  # type: ignore
from contextlib import asynccontextmanager  # type: ignore

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.logger import logger
from backend.config import app_configs, settings
from backend.auth.router import router as auth_router
from backend.chat.router import router as chat_router
from backend.data.router import router as data_router

logger.info("Starting application")

# use redis as session backend
try:
    if settings.REDIS_URL:
        REDIS_URL = settings.REDIS_URL
    else:
        REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        logger.info(f"Using redis url: {REDIS_URL}")
except Exception as e:
    logger.error(f"Error setting redis url: {e}")
    REDIS_URL = "redis://localhost:6379/0"

redis = aioredis.from_url(REDIS_URL)


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
    # Startup
    pool = aioredis.ConnectionPool.from_url(
        str(REDIS_URL), max_connections=10, decode_responses=True
    )
    redis.redis_client = aioredis.Redis(connection_pool=pool)

    yield

    if settings.ENVIRONMENT.is_testing:
        return
    # Shutdown
    await pool.disconnect()


app = FastAPI(**app_configs, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=settings.CORS_HEADERS,
)

if settings.ENVIRONMENT.is_deployed:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
    )

# lifecycle events
# -------------------


def setup_langchain():
    import os

    if settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    if settings.LANGCHAIN_TRACING_V2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if settings.LANGCHAIN_ENDPOINT:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    if settings.LANGCHAIN_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT


@app.get("/healthcheck", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    logger.info("Healthcheck")
    return {"status": "ok"}

app.include_router(auth_router, tags=["auth"])
app.include_router(chat_router, tags=["chat"])
app.include_router(data_router, tags=["data"])
