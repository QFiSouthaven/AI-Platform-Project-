# User Gateway Module

Entry point for all user interactions with the AI Platform. Provides authentication, API gateway, rate limiting, and event publishing functionality.

## Features

- OAuth2 authentication with JWT tokens
- User registration and management
- Password hashing with bcrypt
- API versioning (/api/v1/)
- Kafka event publishing
- PostgreSQL database with async support
- Structured JSON logging
- CORS middleware
- Input validation and sanitization

## Technology Stack

- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy async
- **Authentication**: JWT with OAuth2
- **Message Queue**: Apache Kafka (aiokafka)
- **Validation**: Pydantic v2
- **Password Hashing**: Passlib with bcrypt
- **Logging**: structlog

## Project Structure

```
user-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and settings
│   ├── database.py          # Database connection
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # User model and schemas
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── oauth2.py        # OAuth2 authentication
│   │   └── jwt_handler.py   # JWT token handling
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py      # Authentication endpoints
│   │       └── routes.py    # User CRUD endpoints
│   ├── kafka/
│   │   ├── __init__.py
│   │   └── publisher.py     # Kafka event publisher
│   └── utils/
│       ├── __init__.py
│       └── validators.py    # Input validators
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Apache Kafka (optional, for event publishing)
- Docker (optional)

### Local Development

1. **Clone the repository and navigate to the module:**
   ```bash
   cd user-gateway
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start PostgreSQL and Kafka (using Docker):**
   ```bash
   docker run -d --name postgres \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=ai_platform \
     -p 5432:5432 \
     postgres:15

   docker run -d --name kafka \
     -p 9092:9092 \
     -e KAFKA_CFG_NODE_ID=0 \
     -e KAFKA_CFG_PROCESS_ROLES=controller,broker \
     -e KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
     -e KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
     -e KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=0@localhost:9093 \
     -e KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER \
     bitnami/kafka:latest
   ```

6. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t user-gateway:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name user-gateway \
     -p 8000:8000 \
     --env-file .env \
     user-gateway:latest
   ```

## API Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API info |
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout user |
| GET | `/api/v1/auth/me` | Get current user |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/` | List all users (admin) |
| GET | `/api/v1/users/{id}` | Get user by ID |
| PATCH | `/api/v1/users/{id}` | Update user |
| PATCH | `/api/v1/users/{id}/password` | Update password |
| DELETE | `/api/v1/users/{id}` | Delete user (admin) |
| POST | `/api/v1/users/{id}/activate` | Activate user (admin) |
| POST | `/api/v1/users/{id}/deactivate` | Deactivate user (admin) |

## Authentication

The API uses JWT tokens for authentication. To authenticate:

1. **Register a new user:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "username": "testuser",
       "password": "SecurePass123!",
       "full_name": "Test User"
     }'
   ```

2. **Login to get tokens:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=SecurePass123!"
   ```

3. **Use the access token:**
   ```bash
   curl -X GET http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer <access_token>"
   ```

## Kafka Events

The module publishes the following events to Kafka:

| Topic | Event Type | Description |
|-------|------------|-------------|
| `gateway.user.created` | user.created | User registered |
| `gateway.user.logged_in` | user.logged_in | User logged in |
| `gateway.user.logged_out` | user.logged_out | User logged out |
| `gateway.user.updated` | user.updated | User profile updated |
| `gateway.user.password_changed` | user.password_changed | Password changed |
| `gateway.user.activated` | user.activated | User activated |
| `gateway.user.deactivated` | user.deactivated | User deactivated |
| `gateway.user.deleted` | user.deleted | User deleted |

Event format:
```json
{
  "schema_version": "1.0",
  "event_type": "user.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com"
  },
  "metadata": {
    "correlation_id": "uuid",
    "source": "user-gateway"
  }
}
```

## Configuration

All configuration is done via environment variables. See `.env.example` for all available options.

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `JWT_SECRET` | Secret key for JWT tokens | Required |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 30 |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | localhost:9092 |
| `LOG_LEVEL` | Logging level | INFO |

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Code Quality

```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
pylint app/

# Type checking
mypy app/

# Security scanning
bandit -r app/
```

## Database Migrations

Using Alembic for database migrations:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Common Issues

1. **Database connection errors:**
   - Verify PostgreSQL is running
   - Check DATABASE_URL format
   - Ensure database exists

2. **Kafka connection errors:**
   - Verify Kafka is running
   - Check KAFKA_BOOTSTRAP_SERVERS
   - Ensure topics exist or auto-create is enabled

3. **JWT errors:**
   - Ensure JWT_SECRET is set
   - Check token expiration
   - Verify token format in Authorization header

## License

This project is part of the AI Platform and is proprietary software.

## Support

For issues or questions, please refer to the main project documentation or contact the development team.
