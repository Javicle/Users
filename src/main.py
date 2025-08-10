import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import APIRouter, FastAPI
from openverse_applaunch import ApplicationManager, JaegerService
from tools_openverse.common.config import get_redis, settings

from tools_openverse import setup_logger

from src.delivery.route.user import UserRoute
from src.infra.repository.db.base import init_db


logger = setup_logger()


@asynccontextmanager
async def lifespan(fast_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting application lifespan for %s", settings.PROJECT_NAME)
    logger.info("Initializing database, redis connection")
    db_task = asyncio.create_task(init_db())
    redis_client = asyncio.create_task(get_redis())
    await asyncio.gather(db_task, redis_client)
    logger.info("Database, redis initialized successfully")

    router = APIRouter(tags=["Users"])
    UserRoute(router)
    fast_app.include_router(router)
    logger.info("User routes registered successfully")
    # heath_check = HealthCheck()
    # db_health_task = asyncio.create_task(
    #     heath_check.add_service(DatabaseHealthService("database", session))
    # )
    # redis_health_task = asyncio.create_task(
    #     heath_check.add_service(RedisHealthCheck("redis", await redis_client))
    # )
    # await asyncio.gather(db_health_task, redis_health_task)
    # # await heath_check.display_start_message()
    yield


app = ApplicationManager.create(
    service_name=settings.PROJECT_NAME,
    lifespan=lifespan
)


async def _run_application() -> None:
    jaeger_service = JaegerService()
    await jaeger_service.init(service_name=settings.PROJECT_NAME)
    app.add_service(jaeger_service)
    await app.initialize_application(config=settings.to_dict(), with_tracers=True,
                                     with_metrics=False, health_check=True)

if __name__ == "__main__":
    asyncio.run(_run_application())
    uvicorn.run(app=app.get_app,
                host=settings.BASE_URL,
                port=int(settings.PORT_SERVICE_USERS
                         if settings.PORT_SERVICE_USERS else 8000))
