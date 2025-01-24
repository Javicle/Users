from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import APIRouter, FastAPI
from tools_openverse.common.config import get_redis, settings
from tools_openverse.common.heath import HealthCheck

from src.delivery.route.user import UserRoute
from src.infra.repository.db.base import get_db, init_db
from src.usecases.heatlh import DatabaseHealthService, RedisHealthCheck


@asynccontextmanager
async def lifespan(fast_app: FastAPI) -> AsyncIterator[None]:
    # Инициализация базы данных

    await init_db()
    router = APIRouter(tags=["Users"])
    UserRoute(router)
    fast_app.include_router(router)

    redis_client = await get_redis()

    async for session in get_db():

        heath_check = HealthCheck()
        await heath_check.add_service(DatabaseHealthService("database", session))
        await heath_check.add_service(RedisHealthCheck("redis", redis_client))
        await heath_check.display_start_message()

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    description="Users Services",
    version="0.1",
    # root_path="/openverse/api",
    # docs_url="/docs",
    # openapi_url="/openapi.json",
)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
