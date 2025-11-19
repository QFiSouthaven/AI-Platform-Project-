#Requires -Version 5.1
<#
.SYNOPSIS
    One-click setup and start script for AI Platform on Windows.

.DESCRIPTION
    Performs complete setup and startup:
    - Runs environment validation
    - Installs Python dependencies
    - Copies .env files from examples
    - Starts Docker services
    - Displays access URLs

.PARAMETER SkipValidation
    Skip environment validation

.PARAMETER SkipDependencies
    Skip dependency installation

.PARAMETER Force
    Overwrite existing .env files

.EXAMPLE
    .\quick-start-windows.ps1
    .\quick-start-windows.ps1 -SkipValidation
    .\quick-start-windows.ps1 -Force
#>

[CmdletBinding()]
param(
    [switch]$SkipValidation,
    [switch]$SkipDependencies,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Configuration
$script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$script:Modules = @(
    "user-gateway",
    "workflow-orchestration",
    "core-processing",
    "data-integration",
    "model-management",
    "infrastructure"
)

# Service URLs
$script:ServiceUrls = @(
    @{Name = "User Gateway"; Url = "http://localhost:8001"; Docs = "http://localhost:8001/docs"}
    @{Name = "Workflow Orchestration"; Url = "http://localhost:8002"; Docs = "http://localhost:8002/docs"}
    @{Name = "Core Processing"; Url = "http://localhost:8003"; Docs = "http://localhost:8003/docs"}
    @{Name = "Data Integration"; Url = "http://localhost:8004"; Docs = "http://localhost:8004/docs"}
    @{Name = "Model Management"; Url = "http://localhost:8005"; Docs = "http://localhost:8005/docs"}
    @{Name = "Infrastructure"; Url = "http://localhost:8006"; Docs = "http://localhost:8006/docs"}
)

# Helper functions
function Write-Header {
    param([string]$Text)
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Write-Step {
    param([int]$Number, [string]$Text)
    Write-Host "`n[$Number] $Text" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Text)
    Write-Host "[FAIL] $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "[INFO] $Text" -ForegroundColor Blue
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "[WARN] $Text" -ForegroundColor Yellow
}

function Run-Validation {
    Write-Step 1 "Running environment validation..."

    if ($SkipValidation) {
        Write-Info "Skipping validation (use -SkipValidation to enable)"
        return $true
    }

    try {
        $validateScript = Join-Path $PSScriptRoot "validate-windows.ps1"
        if (Test-Path $validateScript) {
            & $validateScript -SkipDatabaseCheck
            if ($LASTEXITCODE -ne 0) {
                Write-Warning-Custom "Validation completed with warnings"
                $continue = Read-Host "Do you want to continue anyway? (y/n)"
                return $continue -eq "y"
            }
            return $true
        } else {
            Write-Warning-Custom "Validation script not found, skipping..."
            return $true
        }
    } catch {
        Write-Warning-Custom "Validation failed: $_"
        return $false
    }
}

function Install-Dependencies {
    Write-Step 2 "Installing Python dependencies..."

    if ($SkipDependencies) {
        Write-Info "Skipping dependency installation"
        return $true
    }

    try {
        # Create virtual environment
        $venvPath = Join-Path $script:ProjectRoot "venv"
        if (-not (Test-Path $venvPath)) {
            Write-Info "Creating virtual environment..."
            python -m venv $venvPath
        }

        # Activate virtual environment
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            . $activateScript
        }

        # Install common dependencies
        Write-Info "Installing common dependencies..."
        pip install --upgrade pip --quiet
        pip install fastapi uvicorn sqlalchemy alembic pydantic python-dotenv --quiet
        pip install kafka-python redis motor pymongo --quiet
        pip install pytest pytest-asyncio httpx --quiet

        # Install module-specific dependencies
        foreach ($module in $script:Modules) {
            $requirementsPath = Join-Path $script:ProjectRoot "$module/requirements.txt"
            if (Test-Path $requirementsPath) {
                Write-Info "Installing dependencies for $module..."
                pip install -r $requirementsPath --quiet
            }
        }

        Write-Success "Dependencies installed"
        return $true
    } catch {
        Write-Failure "Failed to install dependencies: $_"
        return $false
    }
}

function Copy-EnvFiles {
    Write-Step 3 "Setting up environment files..."

    $copiedCount = 0
    $skippedCount = 0

    foreach ($module in $script:Modules) {
        $envExample = Join-Path $script:ProjectRoot "$module/.env.example"
        $envFile = Join-Path $script:ProjectRoot "$module/.env"

        if (Test-Path $envExample) {
            if ((Test-Path $envFile) -and -not $Force) {
                Write-Info "$module/.env already exists (use -Force to overwrite)"
                $skippedCount++
            } else {
                Copy-Item $envExample $envFile -Force
                Write-Success "Created $module/.env"
                $copiedCount++
            }
        }
    }

    # Copy root .env if example exists
    $rootEnvExample = Join-Path $script:ProjectRoot ".env.example"
    $rootEnvFile = Join-Path $script:ProjectRoot ".env"

    if (Test-Path $rootEnvExample) {
        if ((Test-Path $rootEnvFile) -and -not $Force) {
            Write-Info "Root .env already exists"
            $skippedCount++
        } else {
            Copy-Item $rootEnvExample $rootEnvFile -Force
            Write-Success "Created root .env"
            $copiedCount++
        }
    }

    if ($copiedCount -gt 0) {
        Write-Success "Created $copiedCount environment file(s)"
    }
    if ($skippedCount -gt 0) {
        Write-Info "Skipped $skippedCount existing file(s)"
    }

    return $true
}

function Start-Services {
    Write-Step 4 "Starting Docker services..."

    try {
        # Check Docker is running
        $dockerCheck = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Failure "Docker is not running"
            Write-Info "Please start Docker Desktop and try again"
            return $false
        }

        # Check for docker-compose.yml
        $composePath = Join-Path $script:ProjectRoot "docker-compose.yml"
        if (-not (Test-Path $composePath)) {
            Write-Warning-Custom "docker-compose.yml not found"
            Write-Info "Creating basic docker-compose.yml..."

            # Create a basic docker-compose.yml
            $composeContent = @"
version: '3.8'

services:
  postgres:
    image: postgres:14
    container_name: ai-platform-postgres
    environment:
      POSTGRES_USER: aiplatform
      POSTGRES_PASSWORD: aiplatform
      POSTGRES_DB: aiplatform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aiplatform"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:6
    container_name: ai-platform-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: ai-platform-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    container_name: ai-platform-kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    healthcheck:
      test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 5

  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    container_name: ai-platform-zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
"@
            $composeContent | Out-File -FilePath $composePath -Encoding UTF8
            Write-Success "Created docker-compose.yml"
        }

        # Start services
        Push-Location $script:ProjectRoot
        try {
            Write-Info "Starting Docker containers..."
            $result = docker compose up -d 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Failure "Failed to start Docker services"
                Write-Host $result -ForegroundColor Red
                return $false
            }

            Write-Success "Docker services started"

            # Wait for services to be healthy
            Write-Info "Waiting for services to be ready..."
            Start-Sleep -Seconds 5

            # Show container status
            docker compose ps

            return $true
        } finally {
            Pop-Location
        }
    } catch {
        Write-Failure "Failed to start services: $_"
        return $false
    }
}

function Show-AccessUrls {
    Write-Step 5 "Access URLs"

    Write-Host "`nService Endpoints:" -ForegroundColor White
    Write-Host "-" * 60

    foreach ($service in $script:ServiceUrls) {
        Write-Host ("{0,-25}" -f $service.Name) -NoNewline
        Write-Host $service.Url -ForegroundColor Cyan
    }

    Write-Host "-" * 60

    Write-Host "`nInfrastructure:" -ForegroundColor White
    Write-Host "-" * 60
    Write-Host "PostgreSQL:              " -NoNewline
    Write-Host "localhost:5432" -ForegroundColor Cyan
    Write-Host "MongoDB:                 " -NoNewline
    Write-Host "localhost:27017" -ForegroundColor Cyan
    Write-Host "Redis:                   " -NoNewline
    Write-Host "localhost:6379" -ForegroundColor Cyan
    Write-Host "Kafka:                   " -NoNewline
    Write-Host "localhost:9092" -ForegroundColor Cyan
    Write-Host "-" * 60

    Write-Host "`nAPI Documentation:" -ForegroundColor White
    Write-Host "Each service has Swagger docs at /docs endpoint" -ForegroundColor Gray
    Write-Host "Example: http://localhost:8001/docs" -ForegroundColor Cyan
}

function Show-NextSteps {
    Write-Header "Quick Start Complete!"

    Write-Host "`nNext Steps:" -ForegroundColor White
    Write-Host "1. Check service health:" -ForegroundColor Gray
    Write-Host "   .\scripts\health-check.ps1" -ForegroundColor Cyan

    Write-Host "`n2. Run integration tests:" -ForegroundColor Gray
    Write-Host "   .\scripts\run-integration-tests.ps1" -ForegroundColor Cyan

    Write-Host "`n3. View logs:" -ForegroundColor Gray
    Write-Host "   docker compose logs -f" -ForegroundColor Cyan

    Write-Host "`n4. Stop services:" -ForegroundColor Gray
    Write-Host "   docker compose down" -ForegroundColor Cyan

    Write-Host "`nFor troubleshooting:" -ForegroundColor Gray
    Write-Host "   .\scripts\troubleshoot-windows.ps1" -ForegroundColor Cyan

    Write-Host "`nDocumentation:" -ForegroundColor Gray
    Write-Host "   See WINDOWS-SETUP.md for detailed instructions" -ForegroundColor Cyan
}

# Main execution
function Main {
    Write-Header "AI Platform - Quick Start for Windows"
    Write-Host "Project: $script:ProjectRoot" -ForegroundColor Gray
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

    $success = $true

    # Step 1: Validation
    if (-not (Run-Validation)) {
        Write-Failure "Validation failed"
        $success = $false
    }

    # Step 2: Dependencies
    if ($success -and -not (Install-Dependencies)) {
        Write-Failure "Dependency installation failed"
        $success = $false
    }

    # Step 3: Environment files
    if ($success -and -not (Copy-EnvFiles)) {
        Write-Failure "Environment file setup failed"
        $success = $false
    }

    # Step 4: Start services
    if ($success -and -not (Start-Services)) {
        Write-Failure "Service startup failed"
        $success = $false
    }

    # Step 5: Show URLs
    if ($success) {
        Show-AccessUrls
        Show-NextSteps
        exit 0
    } else {
        Write-Host "`nQuick start failed. Please check the errors above." -ForegroundColor Red
        Write-Host "For troubleshooting, run: .\scripts\troubleshoot-windows.ps1" -ForegroundColor Yellow
        exit 1
    }
}

Main
