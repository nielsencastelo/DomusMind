from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.settings import settings

# FastAPI engine — connection pool for high-throughput request handling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Celery worker engine — NullPool avoids "Event loop is closed" errors.
# asyncio.run() closes the event loop when it exits; a pooled engine has
# background keep-alive tasks that fail on a closed loop. NullPool opens
# and closes each connection immediately, leaving nothing for the pool to clean up.
_worker_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
)

WorkerSessionLocal = async_sessionmaker(
    _worker_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables() -> None:
    """Create all tables (used in tests / first-run fallback)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
