# AI Platform Windows Scripts

This directory contains PowerShell and batch scripts for setting up and managing the AI Platform development environment on Windows 11.

## Prerequisites

Before running these scripts, ensure you have the following installed:

- **Windows 11** (or Windows 10 with PowerShell 5.1+)
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
  - Make sure to check "Add Python to PATH" during installation
- **Git** - [Download](https://git-scm.com/download/win)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
  - Enable WSL 2 backend for better performance

## Quick Start

1. Open PowerShell as Administrator (recommended)
2. Navigate to the project root directory
3. Run the setup script:

```powershell
.\scripts\setup-windows.ps1
```

Or using the batch file wrapper:

```cmd
scripts\setup-windows.bat
```

## Available Scripts

### setup-windows.ps1

Main setup script that prepares the entire development environment.

**Features:**
- Checks for required tools (Python, Git, Docker)
- Creates virtual environments for all modules
- Installs dependencies
- Creates `.env` files from templates
- Sets up Docker services (PostgreSQL, MongoDB, Redis, Kafka)
- Initializes databases

**Usage:**
```powershell
# Full setup
.\scripts\setup-windows.ps1

# Skip Docker setup
.\scripts\setup-windows.ps1 -SkipDocker

# Skip virtual environment creation
.\scripts\setup-windows.ps1 -SkipVenv

# Force reinstall dependencies
.\scripts\setup-windows.ps1 -Force

# Show help
.\scripts\setup-windows.ps1 -Help
```

### start-services.ps1

Starts all Docker Compose services and waits for health checks.

**Features:**
- Starts PostgreSQL, MongoDB, Redis, Kafka, Zookeeper
- Waits for services to be healthy
- Displays service URLs
- Optionally starts a specific module

**Usage:**
```powershell
# Start all services
.\scripts\start-services.ps1

# Rebuild images before starting
.\scripts\start-services.ps1 -Build

# Start a specific module
.\scripts\start-services.ps1 -Module user-gateway

# Don't wait for health checks
.\scripts\start-services.ps1 -NoWait
```

### stop-services.ps1

Stops all Docker Compose services.

**Features:**
- Gracefully stops all containers
- Optionally removes volumes (data)
- Removes orphan containers

**Usage:**
```powershell
# Stop services
.\scripts\stop-services.ps1

# Stop and remove volumes (WARNING: deletes data)
.\scripts\stop-services.ps1 -RemoveVolumes

# Force without confirmation
.\scripts\stop-services.ps1 -RemoveVolumes -Force

# Remove orphan containers
.\scripts\stop-services.ps1 -RemoveOrphans
```

### dev-setup.ps1

Sets up the development environment with additional tooling.

**Features:**
- Creates virtual environments
- Installs development dependencies (pytest, black, mypy, etc.)
- Sets up pre-commit hooks
- Creates VS Code configuration
- Creates pytest.ini

**Usage:**
```powershell
# Full dev setup
.\scripts\dev-setup.ps1

# Setup specific module only
.\scripts\dev-setup.ps1 -Module user-gateway

# Skip pre-commit hooks
.\scripts\dev-setup.ps1 -SkipPreCommit
```

### run-tests.ps1

Runs tests for all or specific modules with coverage reporting.

**Features:**
- Runs pytest for all modules
- Generates coverage reports
- Supports parallel test execution
- Creates test structure if missing

**Usage:**
```powershell
# Run all tests
.\scripts\run-tests.ps1

# Run tests for specific module
.\scripts\run-tests.ps1 -Module user-gateway

# Generate HTML coverage report
.\scripts\run-tests.ps1 -Coverage -Html

# Stop on first failure
.\scripts\run-tests.ps1 -FailFast

# Verbose output
.\scripts\run-tests.ps1 -Verbose

# Run tests in parallel
.\scripts\run-tests.ps1 -Parallel

# Run tests with specific marker
.\scripts\run-tests.ps1 -Marker "unit"
```

### Batch File Wrappers

For users who prefer Command Prompt:

- **setup-windows.bat** - Wrapper for setup-windows.ps1
- **start-services.bat** - Wrapper for start-services.ps1

These automatically detect and use PowerShell Core (pwsh) if available, otherwise fall back to Windows PowerShell.

## Execution Policy

If you encounter execution policy errors, run PowerShell as Administrator and execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or run scripts with bypass:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1
```

## Service URLs

After starting services, the following URLs are available:

| Service    | URL                                          |
|------------|----------------------------------------------|
| PostgreSQL | `postgresql://postgres:postgres@localhost:5432` |
| MongoDB    | `mongodb://localhost:27017`                  |
| Redis      | `redis://localhost:6379`                     |
| Kafka      | `localhost:9092`                             |
| Zookeeper  | `localhost:2181`                             |

## Module Development

After setup, start developing on a module:

```powershell
# Navigate to module
cd user-gateway

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run module tests
pytest tests/ -v

# Format code
black .
isort .

# Type check
mypy app/
```

## Troubleshooting

### Docker Desktop not starting

1. Ensure virtualization is enabled in BIOS
2. Enable Hyper-V in Windows Features
3. Update WSL 2: `wsl --update`
4. Restart Docker Desktop

### PowerShell script won't run

1. Check execution policy: `Get-ExecutionPolicy`
2. Set to RemoteSigned: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Use -ExecutionPolicy Bypass when running

### Python not found

1. Reinstall Python with "Add to PATH" checked
2. Manually add to PATH: `$env:Path += ";C:\Python39;C:\Python39\Scripts"`
3. Use full path: `C:\Python39\python.exe`

### Virtual environment activation fails

1. Ensure you're in the correct directory
2. Check venv exists: `Test-Path .\venv`
3. Recreate: `python -m venv venv`

### Docker services not starting

1. Check Docker is running: `docker info`
2. Check ports aren't in use: `netstat -ano | findstr :5432`
3. View logs: `docker compose logs`
4. Restart Docker Desktop

### Database connection errors

1. Wait for services to be healthy
2. Check container status: `docker ps`
3. Test connection: `docker exec ai-platform-postgres pg_isready`
4. Verify credentials in `.env` files

### Tests failing

1. Ensure dependencies installed: `pip install -r requirements-dev.txt`
2. Check database is running
3. Run single test: `pytest tests/unit/test_sample.py -v`
4. Check for import errors in test files

## Environment Variables

Each module uses a `.env` file. Key variables:

```env
# Application
APP_NAME=module-name
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Security
JWT_SECRET=your-secret-key
```

## Common Commands

```powershell
# View Docker logs
docker compose logs -f

# Check service status
docker compose ps

# Restart specific service
docker compose restart postgres

# Enter container shell
docker exec -it ai-platform-postgres bash

# Clean Docker resources
docker system prune -a

# View Python packages
pip list

# Update dependencies
pip install -r requirements.txt --upgrade
```

## Contributing

When adding new scripts:

1. Use PowerShell 5.1+ compatible syntax
2. Include comment-based help (`.SYNOPSIS`, `.DESCRIPTION`, etc.)
3. Add colored output using the provided functions
4. Include proper error handling
5. Update this README

## Support

For issues with these scripts:

1. Check the troubleshooting section above
2. Review the script with `-Help` parameter
3. Check Docker and service logs
4. Refer to CLAUDE.md for project-specific guidance
