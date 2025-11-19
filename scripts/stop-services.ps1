#Requires -Version 5.1
<#
.SYNOPSIS
    Stop all AI Platform services.

.DESCRIPTION
    Stops Docker Compose services with optional volume removal.

.PARAMETER RemoveVolumes
    Remove volumes when stopping (WARNING: deletes all data).

.PARAMETER RemoveOrphans
    Remove orphan containers.

.PARAMETER Force
    Force stop without confirmation for volume removal.

.EXAMPLE
    .\stop-services.ps1

.EXAMPLE
    .\stop-services.ps1 -RemoveVolumes -Force

.NOTES
    Author: AI Platform Development Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [switch]$RemoveVolumes,
    [switch]$RemoveOrphans,
    [switch]$Force,
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

Stopping AI Platform Services
=============================

"@ "Cyan"

# Check docker-compose.yml exists
if (-not (Test-Path $DockerComposePath)) {
    Write-Error "docker-compose.yml not found at $DockerComposePath"
    exit 1
}

# Confirm volume removal
if ($RemoveVolumes -and (-not $Force)) {
    Write-Warning "This will delete all data in volumes!"
    $confirm = Read-Host "Are you sure you want to remove volumes? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Info "Volume removal cancelled"
        $RemoveVolumes = $false
    }
}

Write-Step "Stopping Docker Services"

# Build stop command
$composeCmd = "docker compose -f `"$DockerComposePath`" down"

if ($RemoveVolumes) {
    $composeCmd += " -v"
    Write-Warning "Volumes will be removed"
}

if ($RemoveOrphans) {
    $composeCmd += " --remove-orphans"
}

# Execute
Write-Info "Running: $composeCmd"
Invoke-Expression $composeCmd

if ($LASTEXITCODE -eq 0) {
    Write-Success "Docker services stopped"
} else {
    Write-Warning "Some services may not have stopped cleanly"
}

# Show remaining containers
$remainingContainers = docker ps --filter "name=ai-platform" --format "{{.Names}}" 2>$null
if ($remainingContainers) {
    Write-Warning "Some containers are still running:"
    $remainingContainers | ForEach-Object { Write-Info "  - $_" }
}

Write-Step "Services Stopped"

Write-ColorOutput @"

All AI Platform services have been stopped.

To restart services:
  .\scripts\start-services.ps1

To remove all Docker resources:
  docker system prune -a

"@ "Green"
