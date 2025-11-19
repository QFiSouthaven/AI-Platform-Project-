"""
Pytest configuration and fixtures for Model Management tests.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import Settings
from app.database import Database
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        APP_ENV="test",
        DEBUG=True,
        MONGODB_URI=os.getenv("TEST_MONGODB_URI", "mongodb://localhost:27017"),
        MONGODB_DB_NAME="model_management_test",
        MODEL_STORAGE_PATH="/tmp/test-models",
        PLUGIN_STORAGE_PATH="/tmp/test-plugins",
        TEMP_STORAGE_PATH="/tmp/test-temp",
        ENABLE_ENCRYPTION=False,
    )


@pytest_asyncio.fixture
async def test_db(test_settings: Settings) -> AsyncGenerator:
    """Create test database connection."""
    client = AsyncIOMotorClient(test_settings.MONGODB_URI)
    db = client[test_settings.MONGODB_DB_NAME]

    # Set up Database class
    Database.client = client
    Database.db = db

    yield db

    # Clean up
    await client.drop_database(test_settings.MONGODB_DB_NAME)
    client.close()


@pytest_asyncio.fixture
async def client(test_db) -> AsyncGenerator:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_model_data() -> dict:
    """Sample model data for testing."""
    return {
        "name": "test-model",
        "version": "1.0.0",
        "model_type": "classification",
        "framework": "pytorch",
        "description": "Test model for unit tests",
        "tags": "test,unit",
        "metadata": "{}",
        "encrypted": "false",
        "created_by": "test@example.com",
    }


@pytest.fixture
def sample_plugin_data() -> dict:
    """Sample plugin data for testing."""
    return {
        "name": "test-plugin",
        "plugin_type": "preprocessor",
        "entry_point": "plugin:TestPlugin",
        "description": "Test plugin for unit tests",
        "version": "1.0.0",
        "author": "Test Author",
        "dependencies": "",
        "config": "{}",
        "config_schema": "{}",
        "metadata": "{}",
        "created_by": "test@example.com",
    }


@pytest.fixture
def sample_version_data() -> dict:
    """Sample version data for testing."""
    return {
        "version": "1.0.0",
        "change_type": "major",
        "description": "Initial version",
        "changelog": "Initial release",
        "metadata": "{}",
        "performance_metrics": '{"accuracy": 0.95}',
        "created_by": "test@example.com",
    }


@pytest.fixture
def model_file_content() -> bytes:
    """Sample model file content for testing."""
    # Simple binary content to simulate a model file
    return b"fake model content for testing" * 100
