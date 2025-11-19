# Workflow Orchestration Module

## Overview

The Workflow Orchestration module is responsible for analyzing requirements, defining workflows, scheduling tasks, and managing execution for the AI Platform. It provides a robust system for creating DAG-based workflows with dependency management, retry policies, and parallel execution support.

## Features

- **Workflow Management**: Create, update, clone, and manage workflow definitions
- **Task Scheduling**: Schedule tasks with dependency resolution using DAG structures
- **Execution Orchestration**: Execute workflows with parallel task processing
- **Retry Policies**: Configurable retry logic with exponential backoff
- **Event-Driven Architecture**: Kafka integration for event publishing and consumption
- **Requirement Analysis**: AI-assisted workflow suggestion based on requirements
- **Real-time Monitoring**: Track execution status, metrics, and logs

## Architecture

```
workflow-orchestration/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   │   ├── workflow.py      # Workflow & WorkflowExecution
│   │   ├── task.py          # Task & TaskExecution
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── workflow_service.py
│   │   ├── task_service.py
│   │   ├── scheduler.py
│   │   ├── orchestrator.py
│   │   └── analyzer.py
│   ├── api/v1/              # API endpoints
│   │   ├── workflows.py
│   │   ├── tasks.py
│   │   └── executions.py
│   ├── kafka/               # Kafka integration
│   │   ├── producer.py
│   │   └── consumer.py
│   └── utils/               # Utilities
│       └── dag.py
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Apache Kafka 2.8+
- Docker and Docker Compose (optional)

### Installation

1. Clone the repository and navigate to the module:
```bash
cd workflow-orchestration
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file and configure:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the application:
```bash
uvicorn app.main:app --reload --port 8002
```

### Using Docker Compose

```bash
docker-compose up -d
```

This starts:
- Workflow Orchestration API (port 8002)
- PostgreSQL (port 5432)
- Redis (port 6379)
- Kafka (port 9092)
- Zookeeper (port 2181)

## API Endpoints

### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/workflows` | Create a new workflow |
| GET | `/api/v1/workflows` | List workflows |
| GET | `/api/v1/workflows/{id}` | Get workflow details |
| PUT | `/api/v1/workflows/{id}` | Update workflow |
| DELETE | `/api/v1/workflows/{id}` | Delete workflow |
| POST | `/api/v1/workflows/{id}/activate` | Activate workflow |
| POST | `/api/v1/workflows/{id}/clone` | Clone workflow |
| POST | `/api/v1/workflows/{id}/execute` | Execute workflow |
| GET | `/api/v1/workflows/{id}/executions` | List workflow executions |
| POST | `/api/v1/workflows/analyze` | Analyze requirements |
| GET | `/api/v1/workflows/statistics` | Get workflow statistics |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tasks` | Create a new task |
| GET | `/api/v1/tasks` | List tasks |
| GET | `/api/v1/tasks/{id}` | Get task details |
| PUT | `/api/v1/tasks/{id}` | Update task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |
| GET | `/api/v1/tasks/statistics` | Get task statistics |

### Executions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/executions` | List all executions |
| GET | `/api/v1/executions/{id}` | Get execution details |
| POST | `/api/v1/executions/{id}/cancel` | Cancel execution |
| POST | `/api/v1/executions/{id}/retry` | Retry failed execution |
| GET | `/api/v1/executions/{id}/tasks` | List task executions |
| GET | `/api/v1/executions/{id}/logs` | Get execution logs |
| GET | `/api/v1/executions/{id}/metrics` | Get execution metrics |

## Usage Examples

### Create a Workflow

```python
import httpx

workflow = {
    "name": "data-pipeline",
    "description": "ETL data pipeline",
    "version": "1.0.0",
    "tasks": [
        {
            "name": "extract",
            "task_type": "data_processing",
            "config": {"source": "s3://bucket/data"},
            "depends_on": []
        },
        {
            "name": "transform",
            "task_type": "transform",
            "config": {"operations": ["clean", "normalize"]},
            "depends_on": [0]  # Depends on extract
        },
        {
            "name": "load",
            "task_type": "data_processing",
            "config": {"destination": "postgres://db/table"},
            "depends_on": [1]  # Depends on transform
        }
    ]
}

response = httpx.post(
    "http://localhost:8002/api/v1/workflows",
    json=workflow,
    params={"created_by": "user@example.com"}
)
print(response.json())
```

### Execute a Workflow

```python
execution = {
    "input_data": {"date": "2024-01-15"},
    "triggered_by": "user@example.com"
}

response = httpx.post(
    "http://localhost:8002/api/v1/workflows/1/execute",
    json=execution
)
print(response.json())
```

### Analyze Requirements

```python
analysis = {
    "requirements": "1. Extract data from S3\n2. Clean and transform\n3. Load into PostgreSQL\n4. Send notification on completion"
}

response = httpx.post(
    "http://localhost:8002/api/v1/workflows/analyze",
    json=analysis
)
print(response.json())
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap servers | `localhost:9092` |
| `DEFAULT_WORKFLOW_TIMEOUT` | Default workflow timeout (seconds) | `3600` |
| `DEFAULT_TASK_TIMEOUT` | Default task timeout (seconds) | `300` |
| `DEFAULT_RETRY_COUNT` | Default retry count | `3` |
| `SCHEDULER_MAX_WORKERS` | Maximum scheduler workers | `10` |

## Kafka Topics

- `workflow.events` - Workflow lifecycle events
- `workflow.task.events` - Task execution events
- `workflow.task.results` - Task execution results

## Database Schema

### Workflows Table
- `id` - Primary key
- `name` - Workflow name
- `description` - Description
- `status` - draft, active, paused, archived
- `version` - Semantic version
- `definition` - JSON workflow definition
- `timeout_seconds` - Execution timeout
- `is_template` - Template flag
- `tags` - JSON array of tags
- `metadata` - JSON metadata
- `created_by` - Creator
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

### Tasks Table
- `id` - Primary key
- `workflow_id` - Foreign key to workflow
- `name` - Task name
- `task_type` - Task type enum
- `config` - JSON configuration
- `depends_on` - JSON array of task IDs
- `retry_policy` - JSON retry configuration
- `timeout_seconds` - Task timeout
- `priority` - Execution priority

### WorkflowExecutions Table
- `id` - Primary key
- `workflow_id` - Foreign key to workflow
- `status` - pending, running, completed, failed, cancelled
- `input_data` - JSON input
- `output_data` - JSON output
- `error_message` - Error details
- `metrics` - JSON execution metrics
- `correlation_id` - Tracing ID
- `triggered_by` - Trigger source
- `started_at` - Start timestamp
- `completed_at` - Completion timestamp

### TaskExecutions Table
- `id` - Primary key
- `task_id` - Foreign key to task
- `workflow_execution_id` - Foreign key to workflow execution
- `status` - Task execution status
- `output_data` - JSON output
- `error_message` - Error details
- `retry_count` - Retry attempts
- `worker_id` - Worker identifier
- `logs` - JSON execution logs
- `metrics` - JSON task metrics
- `started_at` - Start timestamp
- `completed_at` - Completion timestamp

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_workflow_service.py
```

## Development

### Code Style

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Lint
flake8 app tests

# Type checking
mypy app
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Monitoring

The module exposes Prometheus metrics and provides health check endpoints:

- `/health` - Service health status
- `/ready` - Readiness check for load balancers

## License

This project is part of the AI Platform and is subject to its licensing terms.

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Run linting and tests
4. Submit pull request

## Support

For issues and questions, please refer to the AI Platform documentation or contact the development team.
