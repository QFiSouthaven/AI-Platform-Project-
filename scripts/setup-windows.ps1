#Requires -Version 5.1
<#
.SYNOPSIS
    Setup script for AI Platform on Windows 11.

.DESCRIPTION
    This script sets up the AI Platform development environment on Windows.
    It checks for required tools, creates virtual environments, installs
    dependencies, and initializes databases.

.PARAMETER SkipDocker
    Skip Docker Desktop check and setup.

.PARAMETER SkipVenv
    Skip virtual environment creation.

.PARAMETER Force
    Force reinstall of dependencies even if already installed.

.EXAMPLE
    .\setup-windows.ps1

.EXAMPLE
    .\setup-windows.ps1 -SkipDocker -Force

.NOTES
    Author: AI Platform Development Team
    Version: 1.0.0
    Requires: PowerShell 5.1+, Docker Desktop, Python 3.9+, Git
#>

[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [switch]$SkipVenv,
    [switch]$Force,
    [switch]$Help
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Color output functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    $prevColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Output $Message
    $Host.UI.RawUI.ForegroundColor = $prevColor
}

function Write-Success { Write-ColorOutput "[SUCCESS] $args" "Green" }
function Write-Info { Write-ColorOutput "[INFO] $args" "Cyan" }
function Write-Warning { Write-ColorOutput "[WARNING] $args" "Yellow" }
function Write-Error { Write-ColorOutput "[ERROR] $args" "Red" }
function Write-Step { Write-ColorOutput "`n=== $args ===" "Magenta" }

# Display help
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

# Project configuration
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Modules = @(
    "user-gateway",
    "workflow-orchestration",
    "core-processing",
    "data-integration",
    "model-management",
    "infrastructure"
)

# Minimum version requirements
$MinPythonVersion = [version]"3.9.0"
$MinDockerVersion = [version]"20.0.0"
$MinGitVersion = [version]"2.30.0"

Write-ColorOutput @"

    _    ___   ____  _       _    _    __
   / \  |_ _| |  _ \| | __ _| |_ | |_ / _| ___  _ __ _ __ ___
  / _ \  | |  | |_) | |/ _` | __|| |_| |_ / _ \| '__| '_ ` _ \
 / ___ \ | |  |  __/| | (_| | |_ |  _|  _| (_) | |  | | | | | |
/_/   \_\___| |_|   |_|\__,_|\__||_| |_|  \___/|_|  |_| |_| |_|

            Windows Setup Script v1.0.0

"@ "Cyan"

Write-Step "Checking System Requirements"

# Check for Administrator privileges (recommended but not required)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "Running without Administrator privileges. Some features may be limited."
}

# Check Python
Write-Info "Checking Python installation..."
try {
    $pythonCmd = Get-Command python -ErrorAction Stop
    $pythonVersionOutput = & python --version 2>&1
    if ($pythonVersionOutput -match "Python (\d+\.\d+\.\d+)") {
        $pythonVersion = [version]$Matches[1]
        if ($pythonVersion -ge $MinPythonVersion) {
            Write-Success "Python $pythonVersion found at $($pythonCmd.Source)"
        } else {
            throw "Python version $pythonVersion is below minimum required version $MinPythonVersion"
        }
    }
} catch {
    Write-Error "Python 3.9+ is required but not found."
    Write-Info "Please install Python from https://www.python.org/downloads/"
    Write-Info "Make sure to check 'Add Python to PATH' during installation."
    exit 1
}

# Check pip
Write-Info "Checking pip installation..."
try {
    $pipVersion = & python -m pip --version 2>&1
    Write-Success "pip is available: $pipVersion"
} catch {
    Write-Error "pip is not available. Please reinstall Python with pip."
    exit 1
}

# Check Git
Write-Info "Checking Git installation..."
try {
    $gitCmd = Get-Command git -ErrorAction Stop
    $gitVersionOutput = & git --version 2>&1
    if ($gitVersionOutput -match "git version (\d+\.\d+\.\d+)") {
        $gitVersion = [version]$Matches[1]
        if ($gitVersion -ge $MinGitVersion) {
            Write-Success "Git $gitVersion found at $($gitCmd.Source)"
        } else {
            Write-Warning "Git version $gitVersion is below recommended version $MinGitVersion"
        }
    }
} catch {
    Write-Error "Git is required but not found."
    Write-Info "Please install Git from https://git-scm.com/download/win"
    exit 1
}

# Check Docker Desktop
if (-not $SkipDocker) {
    Write-Info "Checking Docker Desktop installation..."
    try {
        $dockerCmd = Get-Command docker -ErrorAction Stop
        $dockerVersionOutput = & docker --version 2>&1
        if ($dockerVersionOutput -match "Docker version (\d+\.\d+\.\d+)") {
            $dockerVersion = [version]$Matches[1]
            Write-Success "Docker $dockerVersion found"
        }

        # Check if Docker daemon is running
        $dockerInfo = & docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Docker Desktop is installed but not running."
            Write-Info "Please start Docker Desktop and run this script again."
            exit 1
        }
        Write-Success "Docker daemon is running"

        # Check Docker Compose
        $composeVersion = & docker compose version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker Compose is available: $composeVersion"
        } else {
            Write-Warning "Docker Compose V2 not found, trying docker-compose..."
            $composeVersion = & docker-compose --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Docker Compose V1 is available: $composeVersion"
            } else {
                Write-Error "Docker Compose is required but not found."
                exit 1
            }
        }
    } catch {
        Write-Error "Docker Desktop is required but not found."
        Write-Info "Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
        exit 1
    }
} else {
    Write-Warning "Skipping Docker check as requested"
}

Write-Step "Setting Up Project Structure"

# Navigate to project root
Set-Location $ProjectRoot
Write-Info "Working in: $ProjectRoot"

# Create module directories if they don't exist
foreach ($module in $Modules) {
    $modulePath = Join-Path $ProjectRoot $module
    if (-not (Test-Path $modulePath)) {
        New-Item -ItemType Directory -Path $modulePath -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $modulePath "app") -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $modulePath "tests") -Force | Out-Null
        Write-Info "Created module directory: $module"
    }
}

Write-Step "Creating Virtual Environments"

if (-not $SkipVenv) {
    foreach ($module in $Modules) {
        $modulePath = Join-Path $ProjectRoot $module
        $venvPath = Join-Path $modulePath "venv"

        if ((Test-Path $venvPath) -and (-not $Force)) {
            Write-Info "Virtual environment already exists for $module (use -Force to recreate)"
            continue
        }

        if (Test-Path $venvPath) {
            Write-Info "Removing existing virtual environment for $module..."
            Remove-Item -Recurse -Force $venvPath
        }

        Write-Info "Creating virtual environment for $module..."
        & python -m venv "$venvPath"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Created virtual environment for $module"
        } else {
            Write-Error "Failed to create virtual environment for $module"
        }
    }
} else {
    Write-Warning "Skipping virtual environment creation as requested"
}

Write-Step "Installing Dependencies"

foreach ($module in $Modules) {
    $modulePath = Join-Path $ProjectRoot $module
    $requirementsPath = Join-Path $modulePath "requirements.txt"
    $venvPip = Join-Path $modulePath "venv\Scripts\pip.exe"

    if (Test-Path $requirementsPath) {
        if (Test-Path $venvPip) {
            Write-Info "Installing dependencies for $module..."
            & $venvPip install -r "$requirementsPath" --quiet
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Installed dependencies for $module"
            } else {
                Write-Warning "Some dependencies failed to install for $module"
            }
        } else {
            Write-Warning "No virtual environment found for $module, skipping dependency installation"
        }
    } else {
        Write-Info "No requirements.txt found for $module, creating template..."
        $templateRequirements = @"
# $module dependencies
fastapi[all]>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
python-dotenv>=1.0.0
structlog>=23.1.0
"@
        Set-Content -Path $requirementsPath -Value $templateRequirements
        Write-Info "Created template requirements.txt for $module"
    }
}

Write-Step "Configuring Environment Files"

foreach ($module in $Modules) {
    $modulePath = Join-Path $ProjectRoot $module
    $envExample = Join-Path $modulePath ".env.example"
    $envFile = Join-Path $modulePath ".env"

    if (Test-Path $envExample) {
        if ((-not (Test-Path $envFile)) -or $Force) {
            Copy-Item $envExample $envFile -Force
            Write-Success "Created .env file for $module from .env.example"
        } else {
            Write-Info ".env file already exists for $module (use -Force to overwrite)"
        }
    } else {
        # Create a default .env.example
        $defaultEnv = @"
# $module Environment Configuration

# Application
APP_NAME=$module
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/$($module -replace '-','_')
MONGODB_URI=mongodb://localhost:27017/$($module -replace '-','_')

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Security
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
"@
        Set-Content -Path $envExample -Value $defaultEnv
        Copy-Item $envExample $envFile -Force
        Write-Info "Created default .env.example and .env for $module"
    }
}

Write-Step "Setting Up Docker Services"

if (-not $SkipDocker) {
    $dockerComposePath = Join-Path $ProjectRoot "docker-compose.yml"

    if (-not (Test-Path $dockerComposePath)) {
        Write-Info "Creating docker-compose.yml for development services..."
        $dockerComposeContent = @"
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: ai-platform-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
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

  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    container_name: ai-platform-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    container_name: ai-platform-kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "29092:29092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
"@
        Set-Content -Path $dockerComposePath -Value $dockerComposeContent
        Write-Success "Created docker-compose.yml"
    }

    Write-Info "Starting Docker services..."
    & docker compose -f "$dockerComposePath" up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker services started"
    } else {
        Write-Warning "Failed to start some Docker services"
    }
}

Write-Step "Initializing Databases"

if (-not $SkipDocker) {
    Write-Info "Waiting for databases to be ready..."
    Start-Sleep -Seconds 10

    # Create databases for each module
    Write-Info "Creating PostgreSQL databases..."
    foreach ($module in $Modules) {
        $dbName = $module -replace '-','_'
        $createDbCmd = "docker exec ai-platform-postgres psql -U postgres -tc `"SELECT 1 FROM pg_database WHERE datname = '$dbName'`" | findstr 1"
        $result = Invoke-Expression $createDbCmd 2>$null
        if (-not $result) {
            & docker exec ai-platform-postgres psql -U postgres -c "CREATE DATABASE $dbName;" 2>$null
            Write-Info "Created database: $dbName"
        }
    }
    Write-Success "Database initialization complete"
}

Write-Step "Setup Complete!"

Write-ColorOutput @"

AI Platform Windows Setup Complete!

Next Steps:
-----------
1. Review and update .env files in each module directory
2. Start the development services:
   .\scripts\start-services.ps1

3. Run tests:
   .\scripts\run-tests.ps1

4. Begin development on Module 1 (User Gateway):
   cd user-gateway
   .\venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload

Service URLs (when running):
----------------------------
- PostgreSQL:  localhost:5432
- MongoDB:     localhost:27017
- Redis:       localhost:6379
- Kafka:       localhost:9092

Documentation:
--------------
- Project Guide: CLAUDE.md
- Scripts Help:  scripts\README.md

"@ "Green"

Write-Info "For help with any script, use the -Help parameter"
