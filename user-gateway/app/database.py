"""
Database module for User Gateway.

Provides async PostgreSQL connection using SQLAlchemy.
Windows 11 compatible with proper connection handling.
"""

import logging
import sys
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings, IS_WINDOWS

logger = logging.getLogger(__name__)


def get_engine_kwargs():
    """
    Get engine configuration kwargs.

    Handles Windows-specific configurations for better compatibility.
    """
    kwargs = {
        "echo": settings.DEBUG,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
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

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Yields:
        AsyncSession: Database session for use in request handlers.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db() -> None:
    """
    Close database connections.

    This should be called on application shutdown.
    """
    await engine.dispose()
    logger.info("Database connections closed")
