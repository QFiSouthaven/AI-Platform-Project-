# AI Platform Project - Guide for AI Assistants

## Project Overview

This repository contains the design specifications and implementation guidelines for a comprehensive AI Platform that orchestrates AI-powered workflows, model management, and application assembly. The platform is designed with a microservices architecture consisting of 6 core modules.

### Current Repository State

**Status**: Pre-implementation / Design Phase
- Contains HTML specification documents for UI/UX design
- Contains backend implementation specifications with code examples
- No actual implemented code yet - ready for development
- All specifications are in `.txt` files (HTML and code snippets)

## Architecture Overview

The AI Platform consists of 6 interconnected modules:

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Platform Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐        ┌──────────────────┐         │
│  │  Module 1:       │───────▶│  Module 2:       │         │
│  │  User Gateway    │        │  Workflow        │         │
│  │  (OAuth2, API)   │        │  Orchestration   │         │
│  └──────────────────┘        └──────────────────┘         │
│           │                           │                     │
│           ▼                           ▼                     │
│  ┌──────────────────┐        ┌──────────────────┐         │
│  │  Module 3:       │◀───────│  Module 4:       │         │
│  │  Core Processing │        │  Data Integration│         │
│  │  (LLM/AI)        │        │  (Kafka, Redis)  │         │
│  └──────────────────┘        └──────────────────┘         │
│           │                           │                     │
│           ▼                           ▼                     │
│  ┌──────────────────┐        ┌──────────────────┐         │
│  │  Module 5:       │        │  Module 6:       │         │
│  │  Model Management│        │  Infrastructure  │         │
│  │  (Storage)       │        │  (Parallel Proc) │         │
│  └──────────────────┘        └──────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Module Specifications

### Module 1: User Gateway
**Purpose**: Entry point for all user interactions
**AI Buildability**: ⭐⭐⭐⭐⭐ (5/5)
**Technology Stack**:
- Backend: Node.js/Express or Python/FastAPI
- Authentication: OAuth2, JWT
- Message Queue: Kafka
- Database: PostgreSQL (for session management)

**Key Features**:
- OAuth2 authentication and authorization
- API gateway and request routing
- Rate limiting and request validation
- Kafka message publishing for async operations

**Files to Create**:
- `user-gateway/app/main.py` - FastAPI application entry point
- `user-gateway/app/auth/oauth2.py` - OAuth2 implementation
- `user-gateway/app/api/routes.py` - API routing logic
- `user-gateway/app/kafka/publisher.py` - Kafka integration

### Module 2: Workflow Orchestration
**Purpose**: Analyzes requirements, orchestrates workflows, schedules tasks
**AI Buildability**: ⭐⭐⭐⭐ (4/5)
**Technology Stack**:
- Backend: Python/FastAPI
- Database: PostgreSQL
- Message Queue: Kafka
- Orchestration: Custom scheduler + Kubernetes CronJobs

**Key Features**:
- DAG (Directed Acyclic Graph) workflow definition
- Task dependency management
- Retry policies and error handling
- Workflow versioning and templates

**Database Models**:
- `Workflow`: workflow definitions, status, versioning
- `WorkflowExecution`: execution history and metrics
- `Task`: individual task definitions
- `TaskExecution`: task execution logs

**Files Structure**:
```
workflow-orchestration/
├── app/
│   ├── main.py              # FastAPI app
│   ├── models/
│   │   ├── workflow.py      # Workflow & WorkflowExecution models
│   │   └── task.py          # Task & TaskExecution models
│   ├── services/
│   │   ├── workflow_service.py
│   │   ├── scheduler.py
│   │   ├── analyzer.py
│   │   └── orchestrator.py
│   └── api/v1/
│       └── workflows.py     # API endpoints
├── requirements.txt
└── Dockerfile
```

### Module 3: Core Processing
**Purpose**: AI-driven code generation, debugging, and optimization using LLMs
**AI Buildability**: ⭐⭐⭐ (3/5) - Complex LLM integration
**Technology Stack**:
- Backend: Python/FastAPI
- LLM Provider: Hugging Face Transformers
- GPU Support: CUDA, PyTorch
- Message Queue: Kafka

**Key Features**:
- Code generation using LLMs (StarCoder, CodeLlama, etc.)
- Automated debugging and error analysis
- Code optimization and refactoring
- Multi-agent coordination

**Critical Dependencies**:
- `transformers` - Hugging Face transformers library
- `torch` - PyTorch for model inference
- `kafka-python` - Kafka integration
- `fastapi[all]` - FastAPI with all extras

**Environment Variables**:
```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
HF_API_TOKEN=your_huggingface_token
MODEL_NAME=bigcode/starcoder
USE_GPU=True
MAX_SEQUENCE_LENGTH=2048
TEMPERATURE=0.7
```

### Module 4: Data Integration
**Purpose**: Event-driven communication, caching, application assembly
**AI Buildability**: ⭐⭐⭐⭐⭐ (5/5)
**Technology Stack**:
- Backend: Python/FastAPI
- Message Bus: Apache Kafka
- Cache: Redis
- Containerization: Docker, Kubernetes

**Key Features**:
- Event-driven architecture with Kafka topics
- In-memory caching with Redis for performance
- Data transformation and assembly pipelines
- Stream processing

### Module 5: Model Management
**Purpose**: Store, load, and extend AI models with plugin support
**AI Buildability**: ⭐⭐⭐⭐ (4/5)
**Technology Stack**:
- Backend: Python/FastAPI
- Database: MongoDB (model metadata)
- Storage: File system + encryption
- Security: Python cryptography library

**Key Features**:
- Model versioning and lifecycle management
- Encrypted model storage
- Dynamic model loading
- Plugin system for model extensions

**Database Schema (MongoDB)**:
```javascript
{
  _id: ObjectId,
  name: String,
  version: String,
  description: String,
  model_type: String,  // classification, generation, etc.
  framework: String,   // pytorch, tensorflow, etc.
  file_path: String,
  encrypted: Boolean,
  metadata: Object,
  tags: [String],
  created_at: Date,
  updated_at: Date,
  created_by: String
}
```

### Module 6: Infrastructure
**Purpose**: Parallel processing and load balancing
**AI Buildability**: ⭐⭐⭐⭐ (4/5)
**Technology Stack**:
- Parallel Processing: Ray
- Load Balancing: NGINX
- Message Queue: Kafka
- Container Orchestration: Kubernetes

**Key Features**:
- Distributed task execution with Ray
- Dynamic resource allocation
- Auto-scaling based on load
- Health monitoring and recovery

## Development Workflow

### Phase 1: Setup and Infrastructure
1. Create project structure for each module
2. Set up Docker and docker-compose for local development
3. Configure Kafka, Redis, PostgreSQL, MongoDB
4. Implement basic health check endpoints

### Phase 2: Core Module Implementation
1. **Start with Module 1 (User Gateway)** - Foundation for authentication
2. **Then Module 2 (Workflow Orchestration)** - Core orchestration logic
3. **Then Module 4 (Data Integration)** - Event handling infrastructure
4. **Then Module 3 (Core Processing)** - AI processing capabilities
5. **Then Module 5 (Model Management)** - Model storage and loading
6. **Finally Module 6 (Infrastructure)** - Scaling and optimization

### Phase 3: Integration and Testing
1. Integration testing between modules
2. End-to-end workflow testing
3. Performance testing and optimization
4. Security audit

## Key Conventions for AI Assistants

### Code Style
- **Language**: Python 3.9+ for all backend services
- **Framework**: FastAPI for all REST APIs
- **Async**: Use async/await for I/O operations
- **Type Hints**: Always use type hints (PEP 484)
- **Formatting**: Follow PEP 8, use `black` for formatting
- **Imports**: Use absolute imports, organize by stdlib → third-party → local

### Project Structure Pattern
Each module follows this structure:
```
module-name/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration and environment variables
│   ├── database.py          # Database connections
│   ├── models/              # Data models (SQLAlchemy/Pydantic)
│   ├── services/            # Business logic
│   ├── api/                 # API endpoints
│   │   └── v1/              # Versioned APIs
│   ├── utils/               # Utility functions
│   └── kafka/               # Kafka consumers/producers
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Database Conventions
- **PostgreSQL**: For structured data (workflows, tasks, users)
  - Use SQLAlchemy ORM
  - Alembic for migrations
  - Use indexes on frequently queried columns

- **MongoDB**: For semi-structured data (model metadata, logs)
  - Use Motor (async MongoDB driver)
  - Create indexes on query fields

- **Redis**: For caching and session storage
  - Use `redis-py` with async support
  - Set appropriate TTLs for cached data

### API Design Conventions
- RESTful endpoints following best practices
- Versioning: `/api/v1/`, `/api/v2/`
- Use proper HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Response format:
  ```json
  {
    "status": "success|error",
    "data": {...},
    "message": "Optional message",
    "timestamp": "ISO 8601 timestamp"
  }
  ```
- Error responses:
  ```json
  {
    "status": "error",
    "error": {
      "code": "ERROR_CODE",
      "message": "Human readable message",
      "details": {...}
    },
    "timestamp": "ISO 8601 timestamp"
  }
  ```

### Kafka Integration
- **Topic Naming**: `{module}.{entity}.{action}`
  - Examples: `gateway.user.created`, `workflow.task.completed`
- **Message Format**: JSON with schema versioning
  ```json
  {
    "schema_version": "1.0",
    "event_type": "user.created",
    "timestamp": "ISO 8601",
    "data": {...},
    "metadata": {
      "correlation_id": "uuid",
      "source": "module_name"
    }
  }
  ```

### Authentication & Security
- **JWT tokens** for API authentication
- **OAuth2** for user authentication
- **API keys** for service-to-service communication
- **Secrets**: Use environment variables, never commit secrets
- **Encryption**: Use `cryptography` library for sensitive data
- **Validation**: Always validate and sanitize inputs

### Error Handling
- Use FastAPI's HTTPException for API errors
- Log all errors with context (correlation IDs, user info)
- Implement retry logic with exponential backoff for transient failures
- Use circuit breakers for external service calls

### Testing Strategy
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test module interactions
- **E2E Tests**: Test complete workflows
- **Coverage Target**: Minimum 80% code coverage
- Use `pytest` as the testing framework
- Use fixtures for common test data
- Mock external dependencies (Kafka, databases, APIs)

### Docker & Deployment
- Each module has its own Dockerfile
- Use multi-stage builds to minimize image size
- Base image: `python:3.9-slim` or `python:3.9-alpine`
- Include health check endpoints
- Use docker-compose for local development
- Kubernetes manifests for production deployment

### Logging & Monitoring
- Use structured logging (JSON format)
- Include correlation IDs in all logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Use `structlog` or `python-json-logger`
- Example log entry:
  ```json
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "module": "workflow-orchestration",
    "message": "Workflow started",
    "correlation_id": "uuid",
    "workflow_id": 123,
    "user_id": "user@example.com"
  }
  ```

### Environment Variables
Each module should have a `.env.example` file:
```env
# Application
APP_NAME=module-name
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
MONGODB_URI=mongodb://localhost:27017/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Security
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# External Services
HF_API_TOKEN=your-huggingface-token
```

## Implementation Priorities

### Critical Path (Must implement first)
1. **Module 1 (User Gateway)** - Authentication foundation
2. **Module 4 (Data Integration)** - Event infrastructure
3. **Module 2 (Workflow Orchestration)** - Core orchestration

### Secondary (Can be implemented in parallel)
4. **Module 3 (Core Processing)** - AI processing
5. **Module 5 (Model Management)** - Model storage

### Optimization (Implement last)
6. **Module 6 (Infrastructure)** - Scaling and optimization

## Common Tasks for AI Assistants

### When creating a new module:
1. Create the directory structure following the pattern above
2. Set up virtual environment: `python -m venv venv`
3. Create `requirements.txt` with dependencies
4. Create `.env.example` with required environment variables
5. Implement `main.py` with FastAPI app and health check
6. Create database models and migrations (if applicable)
7. Implement core service logic
8. Create API endpoints
9. Write unit tests
10. Create Dockerfile and docker-compose.yml
11. Document API endpoints in README.md

### When adding a new API endpoint:
1. Define Pydantic models for request/response
2. Create route in `api/v1/` directory
3. Implement business logic in `services/`
4. Add authentication/authorization checks
5. Add input validation
6. Add error handling
7. Write unit tests
8. Update OpenAPI documentation
9. Test with different scenarios

### When integrating Kafka:
1. Define topic naming convention
2. Create message schema
3. Implement producer in sending module
4. Implement consumer in receiving module
5. Add error handling and retry logic
6. Add monitoring and alerting
7. Test message flow end-to-end

### When working with databases:
1. Create models in `models/` directory
2. Create migration with Alembic: `alembic revision --autogenerate -m "description"`
3. Review and test migration
4. Apply migration: `alembic upgrade head`
5. Add indexes for performance
6. Write CRUD operations in services
7. Add database connection pooling
8. Implement proper transaction management

## Reference Documentation

### Specification Files
- `ai platform archihtectura modules.txt` - Module 4 & 5 UI specifications
- `AI platformDashboard.txt` - Dashboard UI for Module 5 & 6
- `backend module 1 user gate way.html.txt` - Module 1 UI specifications
- `backend moduele 2 workflow orchestration.txt` - Module 2 backend specs
- `backend core processingb.txt` - Module 3 backend specs
- `moduel5 model management backend.txt` - Module 5 backend specs
- `Workflow Orchestration Module Implementation Files.txt` - Module 2 implementation code
- `data_integrationmodule.txt` - Module 4 UI specifications

### External Resources
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Apache Kafka Documentation: https://kafka.apache.org/documentation/
- Hugging Face Transformers: https://huggingface.co/docs/transformers/
- Ray Documentation: https://docs.ray.io/

## Git Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `release/*` - Release preparation branches

### Commit Messages
Follow conventional commits:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(workflow): add task retry mechanism`
- `fix(gateway): resolve OAuth2 token expiration issue`
- `docs(readme): update installation instructions`

### Pull Request Process
1. Create feature branch from `develop`
2. Implement changes with tests
3. Ensure all tests pass
4. Update documentation
5. Create PR with clear description
6. Request review from team members
7. Address review comments
8. Merge after approval

## Troubleshooting Guide

### Common Issues

**Kafka Connection Issues**
- Check `KAFKA_BOOTSTRAP_SERVERS` in .env
- Verify Kafka is running: `docker ps | grep kafka`
- Check network connectivity
- Review Kafka logs

**Database Connection Issues**
- Verify DATABASE_URL format
- Check database is running
- Verify credentials
- Check network/firewall rules

**LLM Integration Issues**
- Verify HF_API_TOKEN is valid
- Check model name is correct
- Ensure sufficient GPU memory
- Review model loading logs

**Authentication Issues**
- Verify JWT_SECRET is set
- Check token expiration time
- Validate OAuth2 configuration
- Review authentication logs

## Performance Optimization

### Database
- Use connection pooling
- Add indexes on frequently queried columns
- Use database query optimization
- Implement read replicas for scaling

### Caching
- Cache frequently accessed data in Redis
- Set appropriate TTLs
- Use cache-aside pattern
- Implement cache invalidation strategy

### API
- Implement pagination for list endpoints
- Use async/await for I/O operations
- Add rate limiting
- Compress responses

### Kafka
- Batch message production
- Use appropriate partition keys
- Configure consumer groups properly
- Monitor consumer lag

## Security Checklist

- [ ] All secrets in environment variables
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize inputs)
- [ ] CSRF protection
- [ ] Rate limiting implemented
- [ ] Authentication on all protected endpoints
- [ ] Authorization checks
- [ ] Encrypted sensitive data at rest
- [ ] TLS/HTTPS for all communications
- [ ] Security headers configured
- [ ] Dependencies regularly updated
- [ ] Security audit conducted

## Next Steps

To start implementing this platform:

1. **Set up development environment**
   - Install Python 3.9+, Docker, docker-compose
   - Set up IDE with Python extensions
   - Install git and configure

2. **Start with Module 1 (User Gateway)**
   - Create project structure
   - Implement basic authentication
   - Set up Kafka integration
   - Create health check endpoint

3. **Implement remaining modules** following the priority order

4. **Integration testing** once all modules are implemented

5. **Deploy to staging environment** for testing

6. **Production deployment** after thorough testing

---

**Last Updated**: 2024-01-15
**Maintained By**: AI Platform Development Team
**For Questions**: Refer to individual module READMEs or specification files
