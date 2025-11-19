.PHONY: setup start stop test lint clean help install dev-install build logs shell migrate

# Default target
help:
	@echo "AI Platform - Available Commands"
	@echo "================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup        - Complete project setup (install deps, build containers)"
	@echo "  make install      - Install Python dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make start        - Start all services"
	@echo "  make stop         - Stop all services"
	@echo "  make build        - Build Docker images"
	@echo "  make logs         - View service logs"
	@echo "  make shell        - Open shell in specified service (SERVICE=name)"
	@echo ""
	@echo "Development:"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linting and formatting checks"
	@echo "  make format       - Format code with Black and isort"
	@echo "  make typecheck    - Run mypy type checking"
	@echo "  make migrate      - Run database migrations"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove containers, volumes, and cache files"
	@echo "  make clean-pyc    - Remove Python cache files"
	@echo "  make clean-docker - Remove Docker containers and volumes"
	@echo ""
	@echo "Examples:"
	@echo "  make shell SERVICE=user-gateway"
	@echo "  make test MODULE=user-gateway"

# ============================================================================
# Setup & Installation
# ============================================================================

setup: install dev-install build
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo ""
	@echo "Setup complete! Run 'make start' to start all services."

install:
	@echo "Installing Python dependencies..."
	pip install --upgrade pip
	@if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

dev-install:
	@echo "Installing development dependencies..."
	pip install black isort mypy pytest pytest-cov pytest-asyncio pre-commit
	pip install httpx fakeredis mongomock

# ============================================================================
# Docker Operations
# ============================================================================

build:
	@echo "Building Docker images..."
	docker-compose build

start:
	@echo "Starting all services..."
	docker-compose up -d
	@echo ""
	@echo "Services started. Access points:"
	@echo "  - User Gateway:          http://localhost:8001/docs"
	@echo "  - Workflow Orchestration: http://localhost:8002/docs"
	@echo "  - Core Processing:        http://localhost:8003/docs"
	@echo "  - Data Integration:       http://localhost:8004/docs"
	@echo "  - Model Management:       http://localhost:8005/docs"
	@echo "  - Infrastructure:         http://localhost:8006/docs"

stop:
	@echo "Stopping all services..."
	docker-compose down

restart: stop start

logs:
	docker-compose logs -f

shell:
ifndef SERVICE
	@echo "Please specify a service: make shell SERVICE=<service-name>"
	@echo "Available services:"
	@docker-compose config --services
else
	docker-compose exec $(SERVICE) /bin/sh
endif

# ============================================================================
# Development
# ============================================================================

test:
ifdef MODULE
	@echo "Running tests for $(MODULE)..."
	pytest $(MODULE)/tests -v --cov=$(MODULE)/app --cov-report=term-missing
else
	@echo "Running all tests..."
	pytest --cov --cov-report=term-missing -v
endif

lint:
	@echo "Running linting checks..."
	@echo ""
	@echo "Checking code formatting with Black..."
	black --check --diff .
	@echo ""
	@echo "Checking import sorting with isort..."
	isort --check-only --diff .
	@echo ""
	@echo "Running flake8..."
	@if command -v flake8 > /dev/null; then flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; fi
	@echo ""
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	black .
	isort .
	@echo "Formatting complete!"

typecheck:
	@echo "Running type checks with mypy..."
	mypy . --ignore-missing-imports

migrate:
	@echo "Running database migrations..."
	alembic upgrade head

# ============================================================================
# Cleanup
# ============================================================================

clean: clean-pyc clean-docker
	@echo "Cleanup complete!"

clean-pyc:
	@echo "Removing Python cache files..."
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type f -name '.coverage' -delete
	find . -type d -name 'htmlcov' -exec rm -rf {} +
	find . -type d -name '.eggs' -exec rm -rf {} +

clean-docker:
	@echo "Removing Docker containers and volumes..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# ============================================================================
# Database Operations
# ============================================================================

db-reset:
	@echo "Resetting databases..."
	docker-compose down -v
	docker-compose up -d postgres mongodb redis
	@echo "Waiting for databases to start..."
	sleep 10
	make migrate

db-shell-postgres:
	docker-compose exec postgres psql -U postgres

db-shell-mongo:
	docker-compose exec mongodb mongosh

db-shell-redis:
	docker-compose exec redis redis-cli

# ============================================================================
# Kafka Operations
# ============================================================================

kafka-topics:
	docker-compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092

kafka-create-topic:
ifndef TOPIC
	@echo "Please specify a topic: make kafka-create-topic TOPIC=<topic-name>"
else
	docker-compose exec kafka kafka-topics.sh --create --topic $(TOPIC) --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
endif

# ============================================================================
# Health Checks
# ============================================================================

health:
	@echo "Checking service health..."
	@echo ""
	@echo "User Gateway:"
	@curl -s http://localhost:8001/health || echo "Not responding"
	@echo ""
	@echo "Workflow Orchestration:"
	@curl -s http://localhost:8002/health || echo "Not responding"
	@echo ""
	@echo "Core Processing:"
	@curl -s http://localhost:8003/health || echo "Not responding"
	@echo ""
	@echo "Data Integration:"
	@curl -s http://localhost:8004/health || echo "Not responding"
	@echo ""
	@echo "Model Management:"
	@curl -s http://localhost:8005/health || echo "Not responding"
	@echo ""
	@echo "Infrastructure:"
	@curl -s http://localhost:8006/health || echo "Not responding"

# ============================================================================
# Documentation
# ============================================================================

docs:
	@echo "Opening API documentation..."
	@echo "Make sure services are running (make start)"
	@if command -v xdg-open > /dev/null; then xdg-open http://localhost:8001/docs; \
	elif command -v open > /dev/null; then open http://localhost:8001/docs; \
	elif command -v start > /dev/null; then start http://localhost:8001/docs; \
	else echo "Please open http://localhost:8001/docs in your browser"; fi
