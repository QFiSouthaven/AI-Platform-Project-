# Data Integration Module

Event-driven communication, caching, and application assembly for the AI Platform.

## Overview

The Data Integration module (Module 4) provides:

- **Event-Driven Architecture**: Kafka-based event consumption and publishing
- **In-Memory Caching**: Redis-based caching for high-performance data access
- **Data Transformation**: Utilities for data mapping, validation, and conversion
- **Application Assembly**: Services for assembling data from multiple sources

## Architecture

```
                    +------------------+
                    |   Kafka Topics   |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Kafka Consumer  |
                    +--------+---------+
                             |
                    +--------v---------+
                    | Event Processor  |
                    +--------+---------+
                             |
              +--------------+---------------+
              |                              |
    +---------v---------+         +----------v----------+
    |  Cache Manager    |         |  Kafka Producer     |
    +---------+---------+         +----------+----------+
              |                              |
    +---------v---------+         +----------v----------+
    |     Redis         |         |   Kafka Topics      |
    +-------------------+         +---------------------+
```

## Features

### Event Processing

- Consumes events from multiple Kafka topics
- Routes events to registered handlers
- Supports custom event transformations
- Publishes processed event notifications

### Caching

- Redis-based caching with connection pooling
- Automatic JSON serialization/deserialization
- TTL management and expiration
- Pattern-based key operations

### API Endpoints

- Event publishing and querying
- Cache management (get, set, delete)
- Statistics and monitoring

## Installation

### Prerequisites

- Python 3.9+
- Redis 6.0+
- Apache Kafka 2.8+

### Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `data-integration` |
| `APP_ENV` | Environment (development/production) | `development` |
| `DEBUG` | Enable debug mode | `True` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8004` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka servers | `localhost:9092` |
| `KAFKA_GROUP_ID` | Consumer group ID | `data-integration-group` |

## API Documentation

Once running, access the API documentation at:

- Swagger UI: http://localhost:8004/docs
- ReDoc: http://localhost:8004/redoc

### Key Endpoints

#### Events

- `POST /api/v1/events/publish` - Publish an event
- `POST /api/v1/events/publish/batch` - Publish multiple events
- `GET /api/v1/events/{event_id}` - Get processed event
- `GET /api/v1/events/stats` - Get processing statistics

#### Cache

- `GET /api/v1/cache/get/{key}` - Get cache entry
- `POST /api/v1/cache/set` - Set cache entry
- `DELETE /api/v1/cache/delete/{key}` - Delete cache entry
- `GET /api/v1/cache/stats` - Get cache statistics

#### Health

- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /metrics` - Application metrics

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint
flake8 app/ tests/

# Type check
mypy app/
```

## Docker

### Build Image

```bash
docker build -t data-integration:latest .
```

### Run Container

```bash
docker run -p 8004:8004 \
  -e REDIS_URL=redis://redis:6379/0 \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  data-integration:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  data-integration:
    build: .
    ports:
      - "8004:8004"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - redis
      - kafka

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      # Additional Kafka configuration...
```

## Event Schema

Events follow this standard schema:

```json
{
  "schema_version": "1.0",
  "event_id": "uuid",
  "event_type": "module.entity.action",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "key": "value"
  },
  "metadata": {
    "correlation_id": "uuid",
    "source": "module-name",
    "user_id": "optional-user-id"
  }
}
```

### Supported Event Types

- `gateway.user.created` - User creation
- `gateway.user.updated` - User update
- `workflow.task.created` - Task creation
- `workflow.task.completed` - Task completion
- `workflow.task.failed` - Task failure
- `processing.code.generated` - Code generation
- `model.loaded` - Model loaded
- `model.unloaded` - Model unloaded

## Kafka Topics

Topic naming convention: `{module}.{entity}.{action}`

### Consumed Topics

- `gateway.user.created`
- `gateway.user.updated`
- `workflow.task.created`
- `workflow.task.completed`
- `workflow.task.failed`
- `processing.code.generated`
- `processing.code.optimized`
- `model.loaded`
- `model.unloaded`

### Published Topics

- `integration.event.processed`
- `integration.data.transformed`
- `integration.cache.invalidated`

## Monitoring

### Metrics

The `/metrics` endpoint provides:

- Event processing statistics
- Cache hit/miss rates
- Kafka consumer lag
- Memory usage

### Health Checks

- `/health` - Overall health status
- `/ready` - Kubernetes readiness probe

### Logging

Structured JSON logging with:

- Timestamp
- Log level
- Module name
- Correlation ID
- Event details

## Troubleshooting

### Common Issues

#### Redis Connection Failed

```
Error: Cannot connect to Redis
```

Solution: Verify Redis is running and `REDIS_URL` is correct.

#### Kafka Consumer Not Receiving Messages

```
Warning: No messages received
```

Solutions:
- Verify Kafka is running
- Check `KAFKA_BOOTSTRAP_SERVERS`
- Ensure topics exist
- Check consumer group offsets

#### Cache Miss Rate High

Solutions:
- Increase TTL values
- Check cache key patterns
- Monitor memory usage

## Contributing

1. Create feature branch from `develop`
2. Write tests for new functionality
3. Follow code style guidelines
4. Update documentation
5. Submit pull request

## License

This project is part of the AI Platform and follows the project's licensing terms.

## Support

For questions and support:
- Check the troubleshooting section
- Review API documentation
- Open an issue in the repository
