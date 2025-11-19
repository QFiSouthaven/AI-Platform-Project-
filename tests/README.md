# AI Platform Test Suite

This directory contains the test suite for the AI Platform, including integration tests and end-to-end tests.

## Test Structure

```
tests/
├── integration/           # Integration tests for individual modules
│   ├── conftest.py       # Shared fixtures and configuration
│   ├── test_api_gateway.py    # API Gateway tests
│   ├── test_auth_flow.py      # Authentication flow tests
│   └── test_workflow_execution.py  # Workflow execution tests
├── e2e/                  # End-to-end pipeline tests
│   └── test_full_pipeline.py  # Complete workflow tests
└── README.md             # This file
```

## Prerequisites

### Python Dependencies

Install test dependencies:

```bash
pip install pytest pytest-asyncio httpx pyjwt
```

Or create a requirements file:

```bash
# tests/requirements.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
PyJWT>=2.8.0
pytest-cov>=4.0.0
pytest-xdist>=3.0.0
```

Install with:

```bash
pip install -r tests/requirements.txt
```

### Services

For full test coverage, the following services should be running:

- **API Gateway** (NGINX) - Port 8080
- **User Gateway** - Port 8001
- **Workflow Orchestration** - Port 8002
- **Core Processing** - Port 8003
- **Data Integration** - Port 8004
- **Model Management** - Port 8005
- **Infrastructure** - Port 8006
- **Kafka** - Port 9092
- **Redis** - Port 6379
- **PostgreSQL** - Port 5432
- **MongoDB** - Port 27017

## Running Tests

### All Tests

```bash
# From project root
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
```

### Integration Tests Only

```bash
pytest tests/integration/ -v
```

### End-to-End Tests Only

```bash
pytest tests/e2e/ -v -m e2e
```

### Specific Test Files

```bash
# API Gateway tests
pytest tests/integration/test_api_gateway.py -v

# Authentication tests
pytest tests/integration/test_auth_flow.py -v

# Workflow tests
pytest tests/integration/test_workflow_execution.py -v

# Full pipeline tests
pytest tests/e2e/test_full_pipeline.py -v
```

### Specific Test Classes or Functions

```bash
# Specific class
pytest tests/integration/test_api_gateway.py::TestHealthEndpoints -v

# Specific test
pytest tests/integration/test_api_gateway.py::TestHealthEndpoints::test_health_endpoint_returns_healthy -v
```

## Windows-Specific Instructions

### Running on Windows

1. **Install Python 3.9+** from [python.org](https://www.python.org/downloads/)

2. **Create virtual environment**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```cmd
   pip install pytest pytest-asyncio httpx pyjwt
   ```

4. **Run tests**:
   ```cmd
   pytest tests\ -v
   ```

### Windows Event Loop Policy

The test suite automatically handles Windows event loop policy for async tests. If you encounter event loop errors, ensure Python 3.9+ is installed.

### Path Separators

All test files use forward slashes which work on both Windows and Unix systems.

## Test Markers

The test suite uses pytest markers to categorize tests:

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.requires_kafka` - Tests requiring Kafka
- `@pytest.mark.requires_redis` - Tests requiring Redis
- `@pytest.mark.requires_db` - Tests requiring database

### Running Tests by Marker

```bash
# Skip slow tests
pytest tests/ -m "not slow"

# Run only e2e tests
pytest tests/ -m "e2e"

# Run tests not requiring Kafka
pytest tests/ -m "not requires_kafka"
```

## Environment Variables

Configure test environment with these variables:

```bash
# Service URLs
export API_GATEWAY_URL=http://localhost:8080
export USER_GATEWAY_URL=http://localhost:8001
export WORKFLOW_URL=http://localhost:8002
export CORE_PROCESSING_URL=http://localhost:8003
export DATA_INTEGRATION_URL=http://localhost:8004
export MODEL_MANAGEMENT_URL=http://localhost:8005
export INFRASTRUCTURE_URL=http://localhost:8006

# Infrastructure
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql://user:pass@localhost:5432/test_db
export MONGODB_URI=mongodb://localhost:27017/test_db

# Security
export JWT_SECRET=test-secret-key

# Timeouts
export TEST_TIMEOUT=30
```

On Windows (Command Prompt):
```cmd
set API_GATEWAY_URL=http://localhost:8080
set JWT_SECRET=test-secret-key
```

On Windows (PowerShell):
```powershell
$env:API_GATEWAY_URL="http://localhost:8080"
$env:JWT_SECRET="test-secret-key"
```

## Running with Docker

### Start Services

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### Run Tests Against Docker Services

```bash
# Set environment to Docker network
export API_GATEWAY_URL=http://localhost:8080

# Run tests
pytest tests/ -v
```

## Test Configuration

### pytest.ini

Create a `pytest.ini` file in the project root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    e2e: marks tests as end-to-end
    integration: marks tests as integration
    requires_kafka: tests requiring Kafka
    requires_redis: tests requiring Redis
    requires_db: tests requiring database
```

### pyproject.toml

Alternatively, configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = "-v --tb=short"
```

## Coverage Reports

Generate test coverage reports:

```bash
# HTML report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=app --cov-report=term-missing

# XML report (for CI)
pytest tests/ --cov=app --cov-report=xml
```

## Parallel Test Execution

Run tests in parallel for faster execution:

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest tests/ -n 4

# Auto-detect CPU count
pytest tests/ -n auto
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379

      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: test-secret
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

1. **Event loop errors on Windows**
   - Ensure Python 3.9+ is installed
   - The conftest.py handles Windows event loop policy automatically

2. **Connection refused errors**
   - Check that all required services are running
   - Verify port numbers match environment variables

3. **Authentication failures**
   - Ensure JWT_SECRET matches across services
   - Check token expiration times

4. **Timeout errors**
   - Increase TEST_TIMEOUT environment variable
   - Check service health and performance

5. **Import errors**
   - Ensure test dependencies are installed
   - Check Python path includes project root

### Debug Mode

Run tests with verbose output and no capture:

```bash
pytest tests/ -v -s --tb=long
```

### Test Isolation

If tests are affecting each other, run them in separate processes:

```bash
pytest tests/ --forked
```

## Writing New Tests

### Test File Template

```python
"""
Module description.
"""
import pytest
from httpx import AsyncClient


class TestFeatureName:
    """Tests for specific feature."""

    @pytest.mark.asyncio
    async def test_feature_works(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that feature works correctly."""
        response = await api_client.get(
            "/api/v1/feature/",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
```

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Use fixtures** for common setup and teardown
3. **Handle service unavailability** gracefully with `pytest.skip()`
4. **Clean up test data** after tests complete
5. **Use markers** to categorize tests appropriately
6. **Test both success and failure cases**
7. **Validate response structure**, not just status codes

## Contributing

When adding new tests:

1. Follow existing naming conventions
2. Add appropriate markers
3. Update this README if adding new test categories
4. Ensure tests pass in isolation and when run together
5. Add fixtures for reusable test data
6. Document any new environment variables required
