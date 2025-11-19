# =============================================================================
# AI Platform - Windows 11 Docker Operations Script
# =============================================================================
# PowerShell script for managing Docker containers on Windows 11.
#
# Usage:
#   .\docker-windows.ps1                    # Start all services
#   .\docker-windows.ps1 -Action start      # Start all services
#   .\docker-windows.ps1 -Action stop       # Stop all services
#   .\docker-windows.ps1 -Action restart    # Restart all services
#   .\docker-windows.ps1 -Action status     # Show service status
#   .\docker-windows.ps1 -Action logs       # Show logs
#   .\docker-windows.ps1 -Action build      # Build images
#   .\docker-windows.ps1 -Action clean      # Remove containers and volumes
#
# Prerequisites:
#   - Docker Desktop for Windows with WSL2 backend
#   - PowerShell 5.1+ (Windows PowerShell) or PowerShell 7+ (PowerShell Core)
#
# =============================================================================

param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'build', 'clean', 'help')]
    [string]$Action = 'start',

    [Parameter()]
    [string]$Service = '',

    [Parameter()]
    [switch]$Force,

    [Parameter()]
    [switch]$NoBuild,

    [Parameter()]
    [int]$Timeout = 300  # 5 minutes default timeout
)

# =============================================================================
# Configuration
# =============================================================================
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $ProjectRoot 'docker-compose.yml'
$WindowsOverride = Join-Path $ProjectRoot 'docker-compose.windows.yml'
$EnvFile = Join-Path $ProjectRoot '.env.docker.windows'

# Service URLs for display
$ServiceUrls = @{
    'user-gateway'           = 'http://localhost:8001'
    'workflow-orchestration' = 'http://localhost:8002'
    'core-processing'        = 'http://localhost:8003'
    'data-integration'       = 'http://localhost:8004'
    'model-management'       = 'http://localhost:8005'
    'infrastructure'         = 'http://localhost:8006'
    'postgres'               = 'localhost:5432'
    'mongodb'                = 'localhost:27017'
    'redis'                  = 'localhost:6379'
    'kafka'                  = 'localhost:9092'
    'zookeeper'              = 'localhost:2181'
}

# =============================================================================
# Helper Functions
# =============================================================================

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'White'
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-ColorOutput "  $Title" 'Cyan'
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "[*] $Message" 'Yellow'
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[+] $Message" 'Green'
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[!] $Message" 'Red'
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "    $Message" 'Gray'
}

# =============================================================================
# Docker Desktop Check
# =============================================================================

function Test-DockerDesktop {
    Write-Step "Checking Docker Desktop..."

    # Check if Docker is installed
    $dockerPath = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerPath) {
        Write-Error "Docker is not installed or not in PATH"
        Write-Info "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        return $false
    }

    # Check if Docker daemon is running
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker Desktop is not running"
            Write-Info "Please start Docker Desktop and wait for it to be ready"
            return $false
        }
    }
    catch {
        Write-Error "Failed to connect to Docker daemon"
        Write-Info "Please ensure Docker Desktop is running"
        return $false
    }

    # Check for WSL2 backend (recommended for Windows 11)
    if ($dockerInfo -match "Operating System:.*WSL") {
        Write-Success "Docker Desktop is running with WSL2 backend"
    }
    elseif ($dockerInfo -match "Operating System:.*Windows") {
        Write-ColorOutput "[!] Docker Desktop is using Hyper-V backend" 'Yellow'
        Write-Info "WSL2 backend is recommended for better performance"
    }
    else {
        Write-Success "Docker Desktop is running"
    }

    return $true
}

# =============================================================================
# Environment Setup
# =============================================================================

function Set-WindowsEnvironment {
    Write-Step "Setting Windows environment variables..."

    # Set COMPOSE_CONVERT_WINDOWS_PATHS for path conversion
    $env:COMPOSE_CONVERT_WINDOWS_PATHS = "1"
    Write-Info "COMPOSE_CONVERT_WINDOWS_PATHS=1"

    # Set project name
    $env:COMPOSE_PROJECT_NAME = "ai-platform"
    Write-Info "COMPOSE_PROJECT_NAME=ai-platform"

    Write-Success "Environment variables configured"
}

# =============================================================================
# Docker Compose Commands
# =============================================================================

function Get-ComposeCommand {
    # Build the docker-compose command with Windows override
    $cmd = "docker-compose"
    $cmd += " -f `"$ComposeFile`""
    $cmd += " -f `"$WindowsOverride`""

    # Use Windows env file if it exists
    if (Test-Path $EnvFile) {
        $cmd += " --env-file `"$EnvFile`""
    }

    return $cmd
}

function Invoke-DockerCompose {
    param([string]$Arguments)

    $cmd = "$(Get-ComposeCommand) $Arguments"
    Write-Info "Running: $cmd"

    Invoke-Expression $cmd
    return $LASTEXITCODE
}

# =============================================================================
# Service Operations
# =============================================================================

function Start-Services {
    Write-Header "Starting AI Platform Services"

    Set-WindowsEnvironment

    # Build if needed
    if (-not $NoBuild) {
        Write-Step "Building Docker images..."
        $result = Invoke-DockerCompose "build"
        if ($result -ne 0) {
            Write-Error "Failed to build images"
            return $false
        }
        Write-Success "Images built successfully"
    }

    # Start services
    Write-Step "Starting services..."
    if ($Service) {
        $result = Invoke-DockerCompose "up -d $Service"
    }
    else {
        $result = Invoke-DockerCompose "up -d"
    }

    if ($result -ne 0) {
        Write-Error "Failed to start services"
        return $false
    }

    Write-Success "Services started"

    # Wait for services to be healthy
    Wait-ForServices

    # Display service URLs
    Show-ServiceUrls

    return $true
}

function Stop-Services {
    Write-Header "Stopping AI Platform Services"

    Set-WindowsEnvironment

    if ($Service) {
        $result = Invoke-DockerCompose "stop $Service"
    }
    else {
        $result = Invoke-DockerCompose "stop"
    }

    if ($result -eq 0) {
        Write-Success "Services stopped"
    }
    else {
        Write-Error "Failed to stop services"
    }

    return $result -eq 0
}

function Restart-Services {
    Write-Header "Restarting AI Platform Services"

    Stop-Services
    Start-Services
}

function Remove-Services {
    Write-Header "Cleaning Up AI Platform"

    Set-WindowsEnvironment

    if ($Force) {
        Write-Step "Removing containers, networks, and volumes..."
        Invoke-DockerCompose "down -v --remove-orphans"
    }
    else {
        Write-Step "Removing containers and networks..."
        Invoke-DockerCompose "down --remove-orphans"
    }

    Write-Success "Cleanup completed"

    if (-not $Force) {
        Write-Info "Note: Volumes were preserved. Use -Force to remove volumes too."
    }
}

function Build-Images {
    Write-Header "Building AI Platform Docker Images"

    Set-WindowsEnvironment

    Write-Step "Building images..."

    if ($Service) {
        $result = Invoke-DockerCompose "build --no-cache $Service"
    }
    else {
        $result = Invoke-DockerCompose "build --no-cache"
    }

    if ($result -eq 0) {
        Write-Success "Images built successfully"
    }
    else {
        Write-Error "Failed to build images"
    }

    return $result -eq 0
}

# =============================================================================
# Status and Monitoring
# =============================================================================

function Show-Status {
    Write-Header "AI Platform Service Status"

    Set-WindowsEnvironment

    Invoke-DockerCompose "ps"
}

function Show-Logs {
    Write-Header "AI Platform Logs"

    Set-WindowsEnvironment

    if ($Service) {
        Invoke-DockerCompose "logs -f --tail=100 $Service"
    }
    else {
        Invoke-DockerCompose "logs -f --tail=50"
    }
}

function Wait-ForServices {
    Write-Step "Waiting for services to be healthy..."

    $startTime = Get-Date
    $allHealthy = $false

    while (-not $allHealthy -and ((Get-Date) - $startTime).TotalSeconds -lt $Timeout) {
        $services = docker-compose -f $ComposeFile -f $WindowsOverride ps --format json 2>&1 | ConvertFrom-Json

        if (-not $services) {
            Start-Sleep -Seconds 5
            continue
        }

        $healthyCount = 0
        $totalCount = 0

        foreach ($svc in $services) {
            $totalCount++
            if ($svc.Health -eq 'healthy' -or $svc.State -eq 'running') {
                $healthyCount++
            }
        }

        $percent = if ($totalCount -gt 0) { [math]::Round(($healthyCount / $totalCount) * 100) } else { 0 }
        Write-Host "`r    Services ready: $healthyCount/$totalCount ($percent%)" -NoNewline

        if ($healthyCount -eq $totalCount -and $totalCount -gt 0) {
            $allHealthy = $true
        }
        else {
            Start-Sleep -Seconds 5
        }
    }

    Write-Host ""

    if ($allHealthy) {
        Write-Success "All services are healthy!"
    }
    else {
        Write-ColorOutput "[!] Some services may still be starting up" 'Yellow'
        Write-Info "Check status with: .\docker-windows.ps1 -Action status"
    }
}

function Show-ServiceUrls {
    Write-Header "Service URLs"

    Write-ColorOutput "Application Modules:" 'White'
    Write-Info "User Gateway:           $($ServiceUrls['user-gateway'])/docs"
    Write-Info "Workflow Orchestration: $($ServiceUrls['workflow-orchestration'])/docs"
    Write-Info "Core Processing:        $($ServiceUrls['core-processing'])/docs"
    Write-Info "Data Integration:       $($ServiceUrls['data-integration'])/docs"
    Write-Info "Model Management:       $($ServiceUrls['model-management'])/docs"
    Write-Info "Infrastructure:         $($ServiceUrls['infrastructure'])/docs"

    Write-Host ""
    Write-ColorOutput "Infrastructure Services:" 'White'
    Write-Info "PostgreSQL:             $($ServiceUrls['postgres'])"
    Write-Info "MongoDB:                $($ServiceUrls['mongodb'])"
    Write-Info "Redis:                  $($ServiceUrls['redis'])"
    Write-Info "Kafka:                  $($ServiceUrls['kafka'])"
    Write-Info "Zookeeper:              $($ServiceUrls['zookeeper'])"

    Write-Host ""
    Write-ColorOutput "Health Check Endpoints:" 'White'
    Write-Info "curl http://localhost:8001/health"
    Write-Info "curl http://localhost:8002/health"
    Write-Info "curl http://localhost:8003/health"
    Write-Info "curl http://localhost:8004/health"
    Write-Info "curl http://localhost:8005/health"
    Write-Info "curl http://localhost:8006/health"
}

function Show-Help {
    Write-Header "AI Platform Docker Windows Script"

    Write-ColorOutput "Usage:" 'White'
    Write-Info ".\docker-windows.ps1 [Action] [Options]"

    Write-Host ""
    Write-ColorOutput "Actions:" 'White'
    Write-Info "start     - Start all services (default)"
    Write-Info "stop      - Stop all services"
    Write-Info "restart   - Restart all services"
    Write-Info "status    - Show service status"
    Write-Info "logs      - Show service logs"
    Write-Info "build     - Build Docker images"
    Write-Info "clean     - Remove containers and networks"
    Write-Info "help      - Show this help message"

    Write-Host ""
    Write-ColorOutput "Options:" 'White'
    Write-Info "-Service <name>  - Target specific service"
    Write-Info "-Force           - Force remove volumes (with clean)"
    Write-Info "-NoBuild         - Skip image build (with start)"
    Write-Info "-Timeout <sec>   - Health check timeout (default: 300)"

    Write-Host ""
    Write-ColorOutput "Examples:" 'White'
    Write-Info ".\docker-windows.ps1"
    Write-Info ".\docker-windows.ps1 -Action start -NoBuild"
    Write-Info ".\docker-windows.ps1 -Action logs -Service kafka"
    Write-Info ".\docker-windows.ps1 -Action clean -Force"
}

# =============================================================================
# Main Entry Point
# =============================================================================

function Main {
    # Check Docker Desktop first
    if ($Action -ne 'help') {
        if (-not (Test-DockerDesktop)) {
            exit 1
        }
    }

    # Execute requested action
    switch ($Action) {
        'start' {
            if (-not (Start-Services)) { exit 1 }
        }
        'stop' {
            if (-not (Stop-Services)) { exit 1 }
        }
        'restart' {
            Restart-Services
        }
        'status' {
            Show-Status
        }
        'logs' {
            Show-Logs
        }
        'build' {
            if (-not (Build-Images)) { exit 1 }
        }
        'clean' {
            Remove-Services
        }
        'help' {
            Show-Help
        }
    }
}

# Run main function
Main
