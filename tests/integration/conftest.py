"""
Shared test fixtures for AI Platform integration tests.
"""
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# ===========================================
# Event Loop Configuration
# ===========================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ===========================================
# Environment Configuration
# ===========================================

@pytest.fixture(scope="session")
def test_config() -> dict:
    """Test configuration settings."""
    return {
        "API_GATEWAY_URL": os.getenv("API_GATEWAY_URL", "http://localhost:8080"),
        "USER_GATEWAY_URL": os.getenv("USER_GATEWAY_URL", "http://localhost:8001"),
        "WORKFLOW_URL": os.getenv("WORKFLOW_URL", "http://localhost:8002"),
        "CORE_PROCESSING_URL": os.getenv("CORE_PROCESSING_URL", "http://localhost:8003"),
        "DATA_INTEGRATION_URL": os.getenv("DATA_INTEGRATION_URL", "http://localhost:8004"),
        "MODEL_MANAGEMENT_URL": os.getenv("MODEL_MANAGEMENT_URL", "http://localhost:8005"),
        "INFRASTRUCTURE_URL": os.getenv("INFRASTRUCTURE_URL", "http://localhost:8006"),
        "KAFKA_BOOTSTRAP_SERVERS": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/test_db"),
        "MONGODB_URI": os.getenv("MONGODB_URI", "mongodb://localhost:27017/test_db"),
        "JWT_SECRET": os.getenv("JWT_SECRET", "test-secret-key"),
        "JWT_ALGORITHM": "HS256",
        "TEST_TIMEOUT": int(os.getenv("TEST_TIMEOUT", "30")),
    }


# ===========================================
# HTTP Client Fixtures
# ===========================================

@pytest_asyncio.fixture
async def api_client(test_config: dict) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for API Gateway tests."""
    async with AsyncClient(
        base_url=test_config["API_GATEWAY_URL"],
        timeout=test_config["TEST_TIMEOUT"],
        headers={"Content-Type": "application/json"}
    ) as client:
        yield client


@pytest_asyncio.fixture
async def user_gateway_client(test_config: dict) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for User Gateway direct tests."""
    async with AsyncClient(
        base_url=test_config["USER_GATEWAY_URL"],
        timeout=test_config["TEST_TIMEOUT"],
        headers={"Content-Type": "application/json"}
    ) as client:
        yield client


@pytest_asyncio.fixture
async def workflow_client(test_config: dict) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for Workflow Orchestration tests."""
    async with AsyncClient(
        base_url=test_config["WORKFLOW_URL"],
        timeout=test_config["TEST_TIMEOUT"],
        headers={"Content-Type": "application/json"}
    ) as client:
        yield client


# ===========================================
# Authentication Fixtures
# ===========================================

@pytest.fixture
def test_user() -> dict:
    """Test user data."""
    return {
        "id": "test-user-001",
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "roles": ["user"],
    }


@pytest.fixture
def admin_user() -> dict:
    """Admin user data."""
    return {
        "id": "admin-user-001",
        "email": "admin@example.com",
        "username": "adminuser",
        "password": "AdminPassword123!",
        "roles": ["admin", "user"],
    }


@pytest.fixture
def valid_token(test_config: dict, test_user: dict) -> str:
    """Generate a valid JWT token for testing."""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": test_user["id"],
        "email": test_user["email"],
        "roles": test_user["roles"],
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }

    return jwt.encode(
        payload,
        test_config["JWT_SECRET"],
        algorithm=test_config["JWT_ALGORITHM"]
    )


@pytest.fixture
def expired_token(test_config: dict, test_user: dict) -> str:
    """Generate an expired JWT token for testing."""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": test_user["id"],
        "email": test_user["email"],
        "roles": test_user["roles"],
        "exp": datetime.utcnow() - timedelta(hours=1),
        "iat": datetime.utcnow() - timedelta(hours=2),
    }

    return jwt.encode(
        payload,
        test_config["JWT_SECRET"],
        algorithm=test_config["JWT_ALGORITHM"]
    )


@pytest.fixture
def auth_headers(valid_token: str) -> dict:
    """Authorization headers with valid token."""
    return {"Authorization": f"Bearer {valid_token}"}


# ===========================================
# Workflow Fixtures
# ===========================================

@pytest.fixture
def sample_workflow() -> dict:
    """Sample workflow definition."""
    return {
        "name": "test-workflow",
        "description": "Test workflow for integration tests",
        "version": "1.0.0",
        "tasks": [
            {
                "id": "task-1",
                "name": "Initialize",
                "type": "initialization",
                "config": {"timeout": 30},
                "dependencies": [],
            },
            {
                "id": "task-2",
                "name": "Process",
                "type": "processing",
                "config": {"batch_size": 100},
                "dependencies": ["task-1"],
            },
            {
                "id": "task-3",
                "name": "Finalize",
                "type": "finalization",
                "config": {},
                "dependencies": ["task-2"],
            },
        ],
        "metadata": {
            "owner": "test@example.com",
            "tags": ["test", "integration"],
        },
    }


@pytest.fixture
def sample_task() -> dict:
    """Sample task definition."""
    return {
        "id": "standalone-task-1",
        "name": "Standalone Task",
        "type": "computation",
        "config": {
            "priority": "high",
            "retries": 3,
            "timeout": 60,
        },
        "input": {"data": "test-input"},
    }


# ===========================================
# Model Management Fixtures
# ===========================================

@pytest.fixture
def sample_model_metadata() -> dict:
    """Sample model metadata."""
    return {
        "name": "test-model",
        "version": "1.0.0",
        "description": "Test model for integration tests",
        "model_type": "classification",
        "framework": "pytorch",
        "tags": ["test", "classification"],
        "metadata": {
            "accuracy": 0.95,
            "parameters": 1000000,
        },
    }


# ===========================================
# Kafka Fixtures
# ===========================================

@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer for testing."""
    producer = MagicMock()
    producer.send = MagicMock(return_value=MagicMock())
    producer.flush = MagicMock()
    return producer


@pytest.fixture
def mock_kafka_consumer():
    """Mock Kafka consumer for testing."""
    consumer = MagicMock()
    consumer.__iter__ = MagicMock(return_value=iter([]))
    consumer.subscribe = MagicMock()
    consumer.close = MagicMock()
    return consumer


@pytest.fixture
def sample_kafka_message() -> dict:
    """Sample Kafka message."""
    from datetime import datetime
    import uuid

    return {
        "schema_version": "1.0",
        "event_type": "workflow.task.completed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "task_id": "task-123",
            "status": "completed",
            "result": {"output": "success"},
        },
        "metadata": {
            "correlation_id": str(uuid.uuid4()),
            "source": "workflow-orchestration",
        },
    }


# ===========================================
# Redis Fixtures
# ===========================================

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    redis.expire = AsyncMock(return_value=True)
    return redis


# ===========================================
# Database Fixtures
# ===========================================

@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


# ===========================================
# Response Validation Helpers
# ===========================================

@pytest.fixture
def validate_response():
    """Helper to validate API response format."""
    def _validate(response_data: dict, expected_status: str = "success"):
        assert "status" in response_data
        assert response_data["status"] == expected_status

        if expected_status == "success":
            assert "data" in response_data
        else:
            assert "error" in response_data
            assert "code" in response_data["error"]
            assert "message" in response_data["error"]

        return True

    return _validate


@pytest.fixture
def validate_error_response():
    """Helper to validate error response format."""
    def _validate(response_data: dict, expected_code: str = None):
        assert response_data["status"] == "error"
        assert "error" in response_data
        assert "code" in response_data["error"]
        assert "message" in response_data["error"]

        if expected_code:
            assert response_data["error"]["code"] == expected_code

        return True

    return _validate


# ===========================================
# Cleanup Fixtures
# ===========================================

@pytest_asyncio.fixture
async def cleanup_workflows(workflow_client: AsyncClient, auth_headers: dict):
    """Cleanup created workflows after tests."""
    created_ids = []

    yield created_ids

    # Cleanup
    for workflow_id in created_ids:
        try:
            await workflow_client.delete(
                f"/api/v1/workflows/{workflow_id}",
                headers=auth_headers
            )
        except Exception:
            pass  # Ignore cleanup errors


# ===========================================
# Test Markers
# ===========================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "requires_kafka: marks tests that require Kafka")
    config.addinivalue_line("markers", "requires_redis: marks tests that require Redis")
    config.addinivalue_line("markers", "requires_db: marks tests that require database")
