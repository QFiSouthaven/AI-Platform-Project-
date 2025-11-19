#Requires -Version 5.1
<#
.SYNOPSIS
    Health check script for AI Platform services.

.DESCRIPTION
    Checks the health status of all AI Platform services:
    - Pings health endpoints
    - Checks Docker container status
    - Verifies database connectivity
    - Displays comprehensive status table

.PARAMETER Timeout
    HTTP request timeout in seconds (default: 5)

.PARAMETER Continuous
    Run continuously with specified interval in seconds

.EXAMPLE
    .\health-check.ps1
    .\health-check.ps1 -Timeout 10
    .\health-check.ps1 -Continuous 30
#>

[CmdletBinding()]
param(
    [int]$Timeout = 5,
    [int]$Continuous = 0
)

$ErrorActionPreference = "Stop"

# Configuration
$script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$script:Services = @(
    @{Name = "User Gateway"; Port = 8001; Endpoint = "/health"; Container = "ai-platform-gateway"}
    @{Name = "Workflow Orchestration"; Port = 8002; Endpoint = "/health"; Container = "ai-platform-workflow"}
    @{Name = "Core Processing"; Port = 8003; Endpoint = "/health"; Container = "ai-platform-processing"}
    @{Name = "Data Integration"; Port = 8004; Endpoint = "/health"; Container = "ai-platform-integration"}
    @{Name = "Model Management"; Port = 8005; Endpoint = "/health"; Container = "ai-platform-models"}
    @{Name = "Infrastructure"; Port = 8006; Endpoint = "/health"; Container = "ai-platform-infra"}
)

$script:Infrastructure = @(
    @{Name = "PostgreSQL"; Container = "ai-platform-postgres"; CheckCmd = "pg_isready"}
    @{Name = "MongoDB"; Container = "ai-platform-mongodb"; CheckCmd = "mongosh --eval 'db.runCommand(""ping"")'"}
    @{Name = "Redis"; Container = "ai-platform-redis"; CheckCmd = "redis-cli ping"}
    @{Name = "Kafka"; Container = "ai-platform-kafka"; CheckCmd = "kafka-broker-api-versions --bootstrap-server localhost:9092"}
)

# Helper functions
function Write-Header {
    param([string]$Text)
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Get-StatusColor {
    param([string]$Status)
    switch ($Status) {
        "Healthy" { return "Green" }
        "Unhealthy" { return "Red" }
        "Degraded" { return "Yellow" }
        "Unknown" { return "Gray" }
        "Running" { return "Green" }
        "Stopped" { return "Red" }
        default { return "White" }
    }
}

function Test-ServiceHealth {
    param(
        [string]$Name,
        [int]$Port,
        [string]$Endpoint
    )

    $url = "http://localhost:$Port$Endpoint"

    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec $Timeout -UseBasicParsing -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            return @{
                Status = "Healthy"
                ResponseTime = "OK"
                Details = "HTTP 200"
            }
        } else {
            return @{
                Status = "Degraded"
                ResponseTime = "N/A"
                Details = "HTTP $($response.StatusCode)"
            }
        }
    } catch [System.Net.WebException] {
        return @{
            Status = "Unhealthy"
            ResponseTime = "N/A"
            Details = "Connection refused"
        }
    } catch {
        return @{
            Status = "Unknown"
            ResponseTime = "N/A"
            Details = $_.Exception.Message
        }
    }
}

function Test-ContainerStatus {
    param([string]$ContainerName)

    try {
        $status = docker inspect --format '{{.State.Status}}' $ContainerName 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($status -eq "running") {
                return @{
                    Status = "Running"
                    Details = "Container is running"
                }
            } else {
                return @{
                    Status = "Stopped"
                    Details = "Status: $status"
                }
            }
        } else {
            return @{
                Status = "Unknown"
                Details = "Container not found"
            }
        }
    } catch {
        return @{
            Status = "Unknown"
            Details = $_.Exception.Message
        }
    }
}

function Test-InfrastructureHealth {
    param(
        [string]$Container,
        [string]$CheckCmd
    )

    try {
        $result = docker exec $Container sh -c $CheckCmd 2>&1
        if ($LASTEXITCODE -eq 0) {
            return @{
                Status = "Healthy"
                Details = "Service responding"
            }
        } else {
            return @{
                Status = "Unhealthy"
                Details = "Service not responding"
            }
        }
    } catch {
        return @{
            Status = "Unknown"
            Details = $_.Exception.Message
        }
    }
}

function Show-ServiceStatus {
    Write-Host "`nService Health Status:" -ForegroundColor White
    Write-Host "-" * 70
    Write-Host ("{0,-25} {1,-12} {2,-12} {3}" -f "Service", "Health", "Container", "Details") -ForegroundColor Gray
    Write-Host "-" * 70

    foreach ($service in $script:Services) {
        # Check HTTP health
        $health = Test-ServiceHealth -Name $service.Name -Port $service.Port -Endpoint $service.Endpoint

        # Check container status
        $container = Test-ContainerStatus -ContainerName $service.Container

        $healthColor = Get-StatusColor $health.Status
        $containerColor = Get-StatusColor $container.Status

        Write-Host ("{0,-25} " -f $service.Name) -NoNewline
        Write-Host ("{0,-12} " -f $health.Status) -ForegroundColor $healthColor -NoNewline
        Write-Host ("{0,-12} " -f $container.Status) -ForegroundColor $containerColor -NoNewline
        Write-Host $health.Details
    }

    Write-Host "-" * 70
}

function Show-InfrastructureStatus {
    Write-Host "`nInfrastructure Status:" -ForegroundColor White
    Write-Host "-" * 70
    Write-Host ("{0,-25} {1,-12} {2,-12} {3}" -f "Service", "Health", "Container", "Details") -ForegroundColor Gray
    Write-Host "-" * 70

    foreach ($infra in $script:Infrastructure) {
        # Check container status
        $container = Test-ContainerStatus -ContainerName $infra.Container

        # Check service health if container is running
        if ($container.Status -eq "Running") {
            $health = Test-InfrastructureHealth -Container $infra.Container -CheckCmd $infra.CheckCmd
        } else {
            $health = @{
                Status = "Unhealthy"
                Details = "Container not running"
            }
        }

        $healthColor = Get-StatusColor $health.Status
        $containerColor = Get-StatusColor $container.Status

        Write-Host ("{0,-25} " -f $infra.Name) -NoNewline
        Write-Host ("{0,-12} " -f $health.Status) -ForegroundColor $healthColor -NoNewline
        Write-Host ("{0,-12} " -f $container.Status) -ForegroundColor $containerColor -NoNewline
        Write-Host $health.Details
    }

    Write-Host "-" * 70
}

function Show-DockerStatus {
    Write-Host "`nDocker Overview:" -ForegroundColor White
    Write-Host "-" * 70

    try {
        # Get running containers
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $containers | ForEach-Object { Write-Host $_ }
        } else {
            Write-Host "Could not retrieve Docker container status" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Docker may not be running" -ForegroundColor Red
    }

    Write-Host "-" * 70
}

function Show-Summary {
    $healthyServices = 0
    $totalServices = $script:Services.Count + $script:Infrastructure.Count

    # Count healthy services
    foreach ($service in $script:Services) {
        $health = Test-ServiceHealth -Name $service.Name -Port $service.Port -Endpoint $service.Endpoint
        if ($health.Status -eq "Healthy") { $healthyServices++ }
    }

    foreach ($infra in $script:Infrastructure) {
        $container = Test-ContainerStatus -ContainerName $infra.Container
        if ($container.Status -eq "Running") {
            $health = Test-InfrastructureHealth -Container $infra.Container -CheckCmd $infra.CheckCmd
            if ($health.Status -eq "Healthy") { $healthyServices++ }
        }
    }

    Write-Host "`nOverall Status: " -NoNewline

    $percentage = [math]::Round(($healthyServices / $totalServices) * 100)

    if ($percentage -eq 100) {
        Write-Host "All systems operational ($healthyServices/$totalServices)" -ForegroundColor Green
    } elseif ($percentage -ge 75) {
        Write-Host "Mostly operational ($healthyServices/$totalServices)" -ForegroundColor Yellow
    } elseif ($percentage -ge 50) {
        Write-Host "Partially operational ($healthyServices/$totalServices)" -ForegroundColor Yellow
    } else {
        Write-Host "System degraded ($healthyServices/$totalServices)" -ForegroundColor Red
    }
}

function Run-HealthCheck {
    Clear-Host
    Write-Header "AI Platform - Health Check"
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host "Timeout: ${Timeout}s" -ForegroundColor Gray

    Show-ServiceStatus
    Show-InfrastructureStatus
    Show-DockerStatus
    Show-Summary
}

# Main execution
function Main {
    if ($Continuous -gt 0) {
        Write-Host "Running continuous health check every $Continuous seconds..."
        Write-Host "Press Ctrl+C to stop`n"

        while ($true) {
            Run-HealthCheck
            Write-Host "`nNext check in $Continuous seconds... (Ctrl+C to stop)" -ForegroundColor Gray
            Start-Sleep -Seconds $Continuous
        }
    } else {
        Run-HealthCheck
    }
}

Main
