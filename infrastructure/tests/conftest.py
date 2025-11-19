"""
Infrastructure Module - Test Configuration and Fixtures

This module provides pytest fixtures and configuration for testing
the infrastructure module components.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment before imports
import os
os.environ["APP_ENV"] = "testing"
os.environ["DEBUG"] = "True"
os.environ["RAY_ADDRESS"] = "auto"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app():
    """Create the FastAPI application for testing."""
    from app.main import app
    return app


@pytest.fixture
def client(app) -> Generator:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app) -> AsyncGenerator:
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_ray_service(mocker):
    """Mock the Ray service for testing."""
    mock = mocker.patch("app.services.ray_service.RayService")
    mock_instance = mock.return_value
    mock_instance.initialize = mocker.AsyncMock()
    mock_instance.shutdown = mocker.AsyncMock()
    mock_instance.is_healthy = mocker.AsyncMock(return_value=True)
    mock_instance.is_ready = mocker.AsyncMock(return_value=True)
    mock_instance.get_cluster_resources = mocker.AsyncMock(return_value={
        "total": {"cpus": 8, "gpus": 0, "memory_bytes": 8000000000},
        "available": {"cpus": 4, "gpus": 0, "memory_bytes": 4000000000},
        "used": {"cpus": 4, "gpus": 0, "memory_bytes": 4000000000}
    })
    mock_instance.list_tasks = mocker.AsyncMock(return_value=[])
    mock_instance.get_nodes = mocker.AsyncMock(return_value=[])
    return mock_instance


@pytest.fixture
def mock_resource_manager(mocker):
    """Mock the Resource Manager for testing."""
    mock = mocker.patch("app.services.resource_manager.ResourceManager")
    mock_instance = mock.return_value
    mock_instance.initialize = mocker.AsyncMock()
    mock_instance.cleanup = mocker.AsyncMock()
    mock_instance.get_resource_availability = mocker.AsyncMock(return_value={})
    mock_instance.get_all_workers = mocker.AsyncMock(return_value=[])
    mock_instance.get_resource_stats = mocker.AsyncMock(return_value={})
    return mock_instance


@pytest.fixture
def mock_health_monitor(mocker):
    """Mock the Health Monitor for testing."""
    mock = mocker.patch("app.services.health_monitor.HealthMonitor")
    mock_instance = mock.return_value
    mock_instance.start = mocker.AsyncMock()
    mock_instance.stop = mocker.AsyncMock()
    mock_instance.get_cluster_health = mocker.AsyncMock(return_value={
        "status": "healthy",
        "healthy_components": 1,
        "unhealthy_components": 0
    })
    mock_instance.get_uptime = mocker.Mock(return_value=100.0)
    return mock_instance


@pytest.fixture
def mock_autoscaler(mocker):
    """Mock the AutoScaler for testing."""
    mock = mocker.patch("app.services.autoscaler.AutoScaler")
    mock_instance = mock.return_value
    mock_instance.start = mocker.AsyncMock()
    mock_instance.stop = mocker.AsyncMock()
    mock_instance.get_config = mocker.AsyncMock(return_value={
        "enabled": True,
        "min_workers": 1,
        "max_workers": 10
    })
    mock_instance.get_current_state = mocker.AsyncMock(return_value={
        "enabled": True,
        "current_workers": 2,
        "in_cooldown": False
    })
    return mock_instance


@pytest.fixture
def sample_task_payload():
    """Sample task payload for testing."""
    return {
        "task_type": "compute",
        "payload": {"duration": 1, "value": "test"},
        "priority": 5,
        "timeout": 60,
        "max_retries": 3
    }


@pytest.fixture
def sample_worker():
    """Sample worker data for testing."""
    return {
        "worker_id": "worker-0001",
        "status": "running",
        "created_at": "2024-01-15T10:00:00",
        "cpu_allocated": 0.25,
        "memory_allocated_mb": 1024,
        "metrics": {"cpu_usage": 50.0, "memory_usage": 60.0}
    }


@pytest.fixture
def sample_scaling_config():
    """Sample scaling configuration for testing."""
    return {
        "min_workers": 2,
        "max_workers": 8,
        "cpu_threshold_high": 75.0,
        "cpu_threshold_low": 25.0,
        "memory_threshold_high": 80.0,
        "memory_threshold_low": 35.0,
        "queue_threshold": 50,
        "cooldown_period": 60
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
