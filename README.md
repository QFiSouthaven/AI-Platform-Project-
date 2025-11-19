# AI Platform

A comprehensive AI Platform that orchestrates AI-powered workflows, model management, and application assembly using a microservices architecture.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Platform Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  Module 1:       │───────▶│  Module 2:       │          │
│  │  User Gateway    │        │  Workflow        │          │
│  │  Port: 8001      │        │  Orchestration   │          │
│  │  (OAuth2, API)   │        │  Port: 8002      │          │
│  └──────────────────┘        └──────────────────┘          │
│           │                           │                     │
│           ▼                           ▼                     │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  Module 3:       │◀───────│  Module 4:       │          │
│  │  Core Processing │        │  Data Integration│          │
│  │  Port: 8003      │        │  Port: 8004      │          │
│  │  (LLM/AI)        │        │  (Kafka, Redis)  │          │
│  └──────────────────┘        └──────────────────┘          │
│           │                           │                     │
│           ▼                           ▼                     │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  Module 5:       │        │  Module 6:       │          │
│  │  Model Management│        │  Infrastructure  │          │
│  │  Port: 8005      │        │  Port: 8006      │          │
│  │  (Storage)       │        │  (Parallel Proc) │          │
│  └──────────────────┘        └──────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### For All Platforms
- Python 3.9 or higher
- Docker and Docker Compose
- Git
- Make (for running Makefile commands)

### Windows 11 Specific Requirements
- **Docker Desktop for Windows** with WSL 2 backend
- **Windows Subsystem for Linux 2 (WSL 2)**
- Git Bash or WSL terminal for running Make commands
- PowerShell 5.1+ or PowerShell Core 7+

### Linux/macOS Requirements
- Docker Engine and Docker Compose
- GNU Make

## Quick Start Guide

### Windows 11 Setup

#### 1. Install WSL 2 and Docker Desktop

```powershell
# Open PowerShell as Administrator
wsl --install

# Restart your computer after installation
```

Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) and enable WSL 2 backend:
1. Open Docker Desktop Settings
2. Go to General > Use the WSL 2 based engine
3. Go to Resources > WSL Integration > Enable for your distro

#### 2. Configure Docker Memory (Recommended)

Create or edit `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
```

Restart WSL:
```powershell
wsl --shutdown
```

#### 3. Clone and Setup

Using Git Bash or WSL terminal:

```bash
# Clone the repository
git clone <repository-url>
cd AI-Platform-Project-

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Git Bash
# OR
source venv/bin/activate  # WSL

# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install

# Start all services
make setup
make start
```

#### 4. PowerShell Execution Policy (if needed)

If you encounter script execution issues:

```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux/macOS Setup

```bash
# Clone the repository
git clone <repository-url>
cd AI-Platform-Project-

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install

# Start all services
make setup
make start
```

## Module Descriptions

| Module | Name | Port | Description |
|--------|------|------|-------------|
| 1 | User Gateway | 8001 | OAuth2 authentication, API gateway, request routing |
| 2 | Workflow Orchestration | 8002 | DAG workflows, task scheduling, orchestration |
| 3 | Core Processing | 8003 | LLM integration, code generation, AI processing |
| 4 | Data Integration | 8004 | Kafka messaging, Redis caching, event handling |
| 5 | Model Management | 8005 | Model storage, versioning, plugin system |
| 6 | Infrastructure | 8006 | Ray parallel processing, load balancing |

### Infrastructure Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Relational database for structured data |
| MongoDB | 27017 | Document database for model metadata |
| Redis | 6379 | Caching and session storage |
| Kafka | 9092 | Message broker for event-driven architecture |
| Zookeeper | 2181 | Kafka cluster coordination |

## API Documentation

Once the services are running, access the API documentation:

- **User Gateway**: http://localhost:8001/docs
- **Workflow Orchestration**: http://localhost:8002/docs
- **Core Processing**: http://localhost:8003/docs
- **Data Integration**: http://localhost:8004/docs
- **Model Management**: http://localhost:8005/docs
- **Infrastructure**: http://localhost:8006/docs

All APIs follow OpenAPI 3.0 specification with interactive Swagger UI.

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run tests for specific module
pytest user-gateway/tests -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Run linting
make lint

# Format code
black .
isort .

# Type checking
mypy app/
```

### Working with Services

```bash
# Start all services
make start

# Stop all services
make stop

# View logs
docker-compose logs -f

# Rebuild services
docker-compose build --no-cache

# Clean up
make clean
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

## Troubleshooting

### Windows-Specific Issues

#### Docker Desktop Not Starting

1. Ensure virtualization is enabled in BIOS
2. Check WSL 2 is properly installed: `wsl --status`
3. Update WSL: `wsl --update`
4. Restart Docker Desktop service

#### Port Conflicts

```powershell
# Find process using port (e.g., 8001)
netstat -ano | findstr :8001

# Kill process by PID
taskkill /PID <PID> /F
```

#### WSL Memory Issues

If Docker/WSL consumes too much memory:
1. Create/edit `%USERPROFILE%\.wslconfig` with memory limits
2. Run `wsl --shutdown`
3. Restart Docker Desktop

#### File Permission Issues in WSL

```bash
# Fix line endings
git config --global core.autocrlf input

# Fix file permissions
chmod +x scripts/*.sh
```

#### Slow File System Performance

For better performance, clone the repository inside WSL:
```bash
# In WSL terminal
cd ~
git clone <repository-url>
```

### General Issues

#### Kafka Connection Refused

```bash
# Check if Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka

# Restart Kafka
docker-compose restart kafka zookeeper
```

#### Database Connection Issues

```bash
# Check database status
docker-compose ps postgres mongodb

# Reset database
docker-compose down -v
docker-compose up -d postgres mongodb
```

#### Redis Connection Issues

```bash
# Check Redis
docker-compose exec redis redis-cli ping
# Should return PONG
```

#### Module Health Checks

```bash
# Check all module health endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
curl http://localhost:8006/health
```

## Project Structure

```
AI-Platform-Project-/
├── user-gateway/           # Module 1: Authentication & API Gateway
├── workflow-orchestration/ # Module 2: Workflow Management
├── core-processing/        # Module 3: AI/LLM Processing
├── data-integration/       # Module 4: Event & Cache Management
├── model-management/       # Module 5: Model Storage & Versioning
├── infrastructure/         # Module 6: Scaling & Load Balancing
├── shared/                 # Shared utilities and configurations
│   ├── logging_config.py
│   ├── constants.py
│   └── exceptions.py
├── docker-compose.yml      # Main Docker Compose file
├── Makefile               # Development commands
├── pyproject.toml         # Python project configuration
├── .pre-commit-config.yaml # Pre-commit hooks
├── .gitignore
├── .dockerignore
└── README.md
```

## Contributing

### Git Workflow

1. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following code conventions

3. Run tests and linting:
   ```bash
   make test
   make lint
   ```

4. Commit with conventional commit messages:
   ```bash
   git commit -m "feat(module): add new feature"
   ```

5. Push and create a Pull Request:
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for public functions
- Maintain 80% minimum test coverage
- Use async/await for I/O operations

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code is formatted with Black
- [ ] Imports are sorted with isort
- [ ] Type hints are complete
- [ ] Documentation is updated
- [ ] No secrets committed

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `MONGODB_URI`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `JWT_SECRET`: Secret key for JWT tokens
- `HF_API_TOKEN`: Hugging Face API token (for Module 3)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review module-specific READMEs
- Open a GitHub issue with detailed information

---

**Version**: 1.0.0
**Last Updated**: 2024-01-15
