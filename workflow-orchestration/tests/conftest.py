"""
Pytest configuration and fixtures for tests.
"""

import asyncio
import pytest
from typing import AsyncGenerator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings


# Test database URL
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "/workflow_db", "/workflow_db_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing."""
    return {
        "name": "test-workflow",
        "description": "Test workflow",
        "version": "1.0.0",
        "is_template": False,
        "timeout_seconds": 3600,
        "tags": ["test"],
        "definition": {},
        "metadata": {},
        "tasks": [
            {
                "name": "task-1",
                "description": "First task",
                "task_type": "custom",
                "config": {},
                "depends_on": [],
                "retry_policy": {
                    "max_retries": 3,
                    "retry_delay": 60,
                    "exponential_backoff": True,
                    "retry_on_timeout": True
                },
                "timeout_seconds": 300,
                "priority": 0,
                "metadata": {}
            },
            {
                "name": "task-2",
                "description": "Second task",
                "task_type": "custom",
                "config": {},
                "depends_on": [0],
                "retry_policy": {
                    "max_retries": 3,
                    "retry_delay": 60,
                    "exponential_backoff": True,
                    "retry_on_timeout": True
                },
                "timeout_seconds": 300,
                "priority": 0,
                "metadata": {}
            }
        ]
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "name": "test-task",
        "description": "Test task",
        "task_type": "custom",
        "config": {},
        "depends_on": [],
        "retry_policy": {
            "max_retries": 3,
            "retry_delay": 60,
            "exponential_backoff": True,
            "retry_on_timeout": True
        },
        "timeout_seconds": 300,
        "priority": 0,
        "metadata": {}
    }


@pytest.fixture
def sample_execution_data():
    """Sample execution data for testing."""
    return {
        "input_data": {"key": "value"},
        "triggered_by": "test@example.com"
    }
