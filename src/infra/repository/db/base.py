from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from tools_openverse.common.config import settings

engine = None
SessionLocal = None

if settings.database_url:
    print("-" * 100)
    print(f"Initializing database engine with URL: {settings.database_url}")
    print("-" * 100)
    engine = create_async_engine(settings.database_url)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
else:
    raise ValueError(f"Database URL not specified {settings.database_url}")


class Base(DeclarativeBase):
    __abstract__ = True


async def init_db() -> None:
    if engine is None:
        raise ValueError("Engine is not initialized.")
    async with engine.begin() as conn:
        # Атрибут для чистки базы данных
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        raise ValueError("SessionLocal is not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
