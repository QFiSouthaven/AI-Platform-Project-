"""
Database configuration and session management.

Uses SQLAlchemy async with PostgreSQL for database operations.
Windows 11 compatible with proper connection handling.
"""

import sys
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings, IS_WINDOWS

def get_engine_kwargs():
    """
    Get engine configuration kwargs.

    Handles Windows-specific configurations for better compatibility.
    """
    kwargs = {
        "echo": settings.DEBUG,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        "pool_pre_ping": True,
    }

    # Windows-specific: Use shorter pool recycle time to handle connection drops
    if IS_WINDOWS:
        kwargs["pool_recycle"] = 1800  # 30 minutes
        kwargs["pool_use_lifo"] = True  # Use LIFO to reduce stale connections

    return kwargs


# Create async engine with platform-specific settings
engine = create_async_engine(
    settings.DATABASE_URL,
    **get_engine_kwargs()
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
