#Requires -Version 5.1
<#
.SYNOPSIS
    Start all AI Platform services.

.DESCRIPTION
    Starts Docker Compose services and waits for health checks.
    Optionally starts individual module services.

.PARAMETER Module
    Start a specific module service (e.g., user-gateway).

.PARAMETER Detached
    Run services in detached mode (default: true).

.PARAMETER Build
    Rebuild images before starting.

.PARAMETER NoWait
    Don't wait for health checks.

.EXAMPLE
    .\start-services.ps1

.EXAMPLE
    .\start-services.ps1 -Module user-gateway -Build

.NOTES
    Author: AI Platform Development Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [string]$Module,
    [switch]$Detached = $true,
    [switch]$Build,
    [switch]$NoWait,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Color output functions
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
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

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DockerComposePath = Join-Path $ProjectRoot "docker-compose.yml"

Write-ColorOutput @"

Starting AI Platform Services
=============================

"@ "Cyan"

# Check Docker is running
Write-Info "Checking Docker status..."
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}
Write-Success "Docker is running"

# Check docker-compose.yml exists
if (-not (Test-Path $DockerComposePath)) {
    Write-Error "docker-compose.yml not found at $DockerComposePath"
    Write-Info "Please run setup-windows.ps1 first"
    exit 1
}

Write-Step "Starting Docker Services"

# Build command
$composeCmd = "docker compose -f `"$DockerComposePath`""

if ($Build) {
    $composeCmd += " up --build"
} else {
    $composeCmd += " up"
}

if ($Detached) {
    $composeCmd += " -d"
}

# Execute
Write-Info "Running: $composeCmd"
Invoke-Expression $composeCmd

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Docker services"
    exit 1
}

Write-Success "Docker Compose services started"

# Wait for health checks
if (-not $NoWait) {
    Write-Step "Waiting for Services to be Healthy"

    $services = @(
        @{Name = "PostgreSQL"; Container = "ai-platform-postgres"; MaxWait = 30},
        @{Name = "MongoDB"; Container = "ai-platform-mongodb"; MaxWait = 30},
        @{Name = "Redis"; Container = "ai-platform-redis"; MaxWait = 30},
        @{Name = "Kafka"; Container = "ai-platform-kafka"; MaxWait = 60}
    )

    foreach ($service in $services) {
        Write-Info "Waiting for $($service.Name)..."
        $waited = 0
        $healthy = $false

        while ($waited -lt $service.MaxWait) {
            $health = docker inspect --format='{{.State.Health.Status}}' $service.Container 2>$null

            if ($health -eq "healthy") {
                Write-Success "$($service.Name) is healthy"
                $healthy = $true
                break
            }

            # For containers without health checks, just check if running
            if (-not $health) {
                $running = docker inspect --format='{{.State.Running}}' $service.Container 2>$null
                if ($running -eq "true") {
                    Write-Success "$($service.Name) is running"
                    $healthy = $true
                    break
                }
            }

            Start-Sleep -Seconds 2
            $waited += 2
            Write-Host "." -NoNewline
        }

        if (-not $healthy) {
            Write-Warning "$($service.Name) did not become healthy within $($service.MaxWait) seconds"
        }
    }
}

# Start specific module if requested
if ($Module) {
    Write-Step "Starting Module: $Module"

    $modulePath = Join-Path $ProjectRoot $Module
    if (-not (Test-Path $modulePath)) {
        Write-Error "Module not found: $Module"
        exit 1
    }

    $venvActivate = Join-Path $modulePath "venv\Scripts\Activate.ps1"
    $mainApp = Join-Path $modulePath "app\main.py"

    if (Test-Path $mainApp) {
        Write-Info "Starting $Module with uvicorn..."
        & $venvActivate
        Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0" -WorkingDirectory $modulePath
        Write-Success "Started $Module"
    } else {
        Write-Warning "No main.py found for $Module"
    }
}

Write-Step "Services Started Successfully!"

Write-ColorOutput @"

Service URLs:
-------------
- PostgreSQL:  postgresql://postgres:postgres@localhost:5432
- MongoDB:     mongodb://localhost:27017
- Redis:       redis://localhost:6379
- Kafka:       localhost:9092

Commands:
---------
- View logs:      docker compose logs -f
- Stop services:  .\scripts\stop-services.ps1
- Service status: docker compose ps

Module Development:
-------------------
cd <module-name>
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

"@ "Green"
