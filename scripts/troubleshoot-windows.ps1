#Requires -Version 5.1
<#
.SYNOPSIS
    Troubleshooting script for common AI Platform issues on Windows.

.DESCRIPTION
    Provides fixes for common issues:
    - Reset Docker Desktop
    - Clear Docker cache
    - Fix WSL2 issues
    - Reset virtual environments
    - Clear Python cache
    - Repair permissions

.PARAMETER Action
    Specific action to perform

.EXAMPLE
    .\troubleshoot-windows.ps1
    .\troubleshoot-windows.ps1 -Action ResetDocker
    .\troubleshoot-windows.ps1 -Action ClearCache
#>

[CmdletBinding()]
param(
    [ValidateSet("Menu", "ResetDocker", "ClearDockerCache", "FixWSL",
                 "ResetVenv", "ClearPythonCache", "FixPermissions",
                 "ResetAll", "DiagnoseNetwork")]
    [string]$Action = "Menu"
)

$ErrorActionPreference = "Stop"

# Configuration
$script:ProjectRoot = Split-Path -Parent $PSScriptRoot

# Helper functions
function Write-Header {
    param([string]$Text)
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Text)
    Write-Host "`n>> $Text" -ForegroundColor Yellow
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

function Confirm-Action {
    param([string]$Message)
    $response = Read-Host "$Message (y/n)"
    return $response -eq "y" -or $response -eq "Y"
}

# Action functions
function Reset-DockerDesktop {
    Write-Step "Resetting Docker Desktop..."

    try {
        # Stop all containers
        Write-Info "Stopping all containers..."
        docker stop $(docker ps -aq) 2>$null

        # Remove all containers
        Write-Info "Removing all containers..."
        docker rm $(docker ps -aq) 2>$null

        # Restart Docker Desktop
        Write-Info "Restarting Docker Desktop..."

        # Try to stop Docker Desktop
        $dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
        if ($dockerProcess) {
            Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
        }

        # Start Docker Desktop
        $dockerPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerPath) {
            Start-Process $dockerPath
            Write-Info "Waiting for Docker to start..."

            # Wait for Docker to be ready
            $timeout = 60
            $elapsed = 0
            while ($elapsed -lt $timeout) {
                $dockerInfo = docker info 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Docker Desktop restarted successfully"
                    return
                }
                Start-Sleep -Seconds 2
                $elapsed += 2
                Write-Host "." -NoNewline
            }
            Write-Host ""
            Write-Failure "Docker Desktop did not start within $timeout seconds"
        } else {
            Write-Warning-Custom "Docker Desktop not found at expected path"
            Write-Info "Please restart Docker Desktop manually"
        }
    } catch {
        Write-Failure "Failed to reset Docker Desktop: $_"
    }
}

function Clear-DockerCache {
    Write-Step "Clearing Docker cache..."

    if (-not (Confirm-Action "This will remove unused Docker data. Continue?")) {
        Write-Info "Cancelled"
        return
    }

    try {
        # Docker system prune
        Write-Info "Running docker system prune..."
        docker system prune -af --volumes

        # Show disk usage
        Write-Info "Current Docker disk usage:"
        docker system df

        Write-Success "Docker cache cleared"
    } catch {
        Write-Failure "Failed to clear Docker cache: $_"
    }
}

function Fix-WSL2 {
    Write-Step "Fixing WSL2 issues..."

    try {
        # Check WSL status
        Write-Info "Checking WSL status..."
        $wslStatus = wsl --status 2>&1
        Write-Host $wslStatus

        # Shutdown WSL
        Write-Info "Shutting down WSL..."
        wsl --shutdown
        Start-Sleep -Seconds 3

        # Set default version to WSL2
        Write-Info "Setting WSL default version to 2..."
        wsl --set-default-version 2 2>&1

        # Update WSL
        Write-Info "Updating WSL..."
        wsl --update 2>&1

        Write-Success "WSL2 fixes applied"

        # Suggest .wslconfig optimization
        Write-Info "Consider adding .wslconfig for better performance"
        Write-Host @"

Create or edit %USERPROFILE%\.wslconfig with:

[wsl2]
memory=4GB
processors=2
swap=2GB
localhostForwarding=true

"@ -ForegroundColor Gray

    } catch {
        Write-Failure "Failed to fix WSL2: $_"
    }
}

function Reset-VirtualEnvironment {
    Write-Step "Resetting virtual environment..."

    $venvPath = Join-Path $script:ProjectRoot "venv"

    if (Test-Path $venvPath) {
        if (-not (Confirm-Action "Delete existing virtual environment?")) {
            Write-Info "Cancelled"
            return
        }

        try {
            # Deactivate if active
            if ($env:VIRTUAL_ENV) {
                deactivate 2>$null
            }

            # Remove venv directory
            Write-Info "Removing virtual environment..."
            Remove-Item -Path $venvPath -Recurse -Force

            Write-Success "Virtual environment removed"
        } catch {
            Write-Failure "Failed to remove virtual environment: $_"
            return
        }
    }

    try {
        # Create new virtual environment
        Write-Info "Creating new virtual environment..."
        python -m venv $venvPath

        # Activate and upgrade pip
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        . $activateScript

        python -m pip install --upgrade pip

        Write-Success "Virtual environment reset complete"
        Write-Info "Run '.\scripts\quick-start-windows.ps1 -SkipValidation' to reinstall dependencies"
    } catch {
        Write-Failure "Failed to create virtual environment: $_"
    }
}

function Clear-PythonCache {
    Write-Step "Clearing Python cache..."

    try {
        # Find and remove __pycache__ directories
        Write-Info "Removing __pycache__ directories..."
        Get-ChildItem -Path $script:ProjectRoot -Directory -Recurse -Filter "__pycache__" |
            ForEach-Object {
                Remove-Item $_.FullName -Recurse -Force
                Write-Host "  Removed: $($_.FullName)" -ForegroundColor Gray
            }

        # Find and remove .pyc files
        Write-Info "Removing .pyc files..."
        Get-ChildItem -Path $script:ProjectRoot -File -Recurse -Filter "*.pyc" |
            ForEach-Object {
                Remove-Item $_.FullName -Force
            }

        # Remove .pytest_cache
        $pytestCache = Join-Path $script:ProjectRoot ".pytest_cache"
        if (Test-Path $pytestCache) {
            Remove-Item $pytestCache -Recurse -Force
            Write-Info "Removed .pytest_cache"
        }

        # Remove .mypy_cache
        $mypyCache = Join-Path $script:ProjectRoot ".mypy_cache"
        if (Test-Path $mypyCache) {
            Remove-Item $mypyCache -Recurse -Force
            Write-Info "Removed .mypy_cache"
        }

        # Remove egg-info directories
        Get-ChildItem -Path $script:ProjectRoot -Directory -Recurse -Filter "*.egg-info" |
            ForEach-Object {
                Remove-Item $_.FullName -Recurse -Force
                Write-Info "Removed $($_.Name)"
            }

        Write-Success "Python cache cleared"
    } catch {
        Write-Failure "Failed to clear Python cache: $_"
    }
}

function Fix-Permissions {
    Write-Step "Fixing file permissions..."

    try {
        # Reset permissions on project directory
        Write-Info "Resetting permissions on project directory..."

        $acl = Get-Acl $script:ProjectRoot
        $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $currentUser,
            "FullControl",
            "ContainerInherit,ObjectInherit",
            "None",
            "Allow"
        )

        $acl.SetAccessRule($accessRule)
        Set-Acl $script:ProjectRoot $acl

        # Fix Docker socket permissions (Windows-specific)
        Write-Info "Checking Docker permissions..."

        # Check if user is in docker-users group
        $dockerGroup = Get-LocalGroupMember -Group "docker-users" -ErrorAction SilentlyContinue
        if ($dockerGroup) {
            if ($dockerGroup.Name -contains $currentUser) {
                Write-Success "User is in docker-users group"
            } else {
                Write-Warning-Custom "User is not in docker-users group"
                Write-Info "Run this as Administrator to add user to docker-users group:"
                Write-Host "  Add-LocalGroupMember -Group 'docker-users' -Member '$currentUser'" -ForegroundColor Cyan
            }
        }

        Write-Success "Permission fixes applied"
    } catch {
        Write-Failure "Failed to fix permissions: $_"
        Write-Info "You may need to run this script as Administrator"
    }
}

function Reset-All {
    Write-Step "Performing complete reset..."

    if (-not (Confirm-Action "This will reset Docker, WSL, and Python environment. Continue?")) {
        Write-Info "Cancelled"
        return
    }

    Clear-PythonCache
    Reset-VirtualEnvironment
    Clear-DockerCache
    Fix-WSL2
    Reset-DockerDesktop

    Write-Success "Complete reset finished"
    Write-Info "Run '.\scripts\quick-start-windows.ps1' to set up the environment again"
}

function Diagnose-Network {
    Write-Step "Diagnosing network issues..."

    try {
        # Check Docker network
        Write-Info "Docker networks:"
        docker network ls

        # Check if ports are in use
        Write-Info "`nChecking port availability..."

        $ports = @(5432, 27017, 6379, 9092, 8001, 8002, 8003, 8004, 8005, 8006)

        foreach ($port in $ports) {
            $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
            if ($connection) {
                $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
                Write-Warning-Custom "Port $port is in use by $($process.ProcessName) (PID: $($connection.OwningProcess))"
            } else {
                Write-Success "Port $port is available"
            }
        }

        # Check DNS resolution
        Write-Info "`nChecking DNS resolution..."
        try {
            $dns = Resolve-DnsName "localhost" -ErrorAction Stop
            Write-Success "localhost resolves correctly"
        } catch {
            Write-Failure "localhost DNS resolution failed"
        }

        # Check Docker host networking
        Write-Info "`nDocker host information:"
        docker info --format '{{.Name}}: {{.NCPU}} CPUs, {{.MemTotal}} memory'

        # Check WSL networking
        Write-Info "`nWSL network interfaces:"
        wsl hostname -I 2>&1

    } catch {
        Write-Failure "Network diagnosis failed: $_"
    }
}

function Show-Menu {
    Write-Header "AI Platform - Troubleshooting Menu"

    Write-Host "`nSelect an action:" -ForegroundColor White
    Write-Host "-" * 40
    Write-Host "1. Reset Docker Desktop" -ForegroundColor Cyan
    Write-Host "2. Clear Docker Cache" -ForegroundColor Cyan
    Write-Host "3. Fix WSL2 Issues" -ForegroundColor Cyan
    Write-Host "4. Reset Virtual Environment" -ForegroundColor Cyan
    Write-Host "5. Clear Python Cache" -ForegroundColor Cyan
    Write-Host "6. Fix Permissions" -ForegroundColor Cyan
    Write-Host "7. Diagnose Network" -ForegroundColor Cyan
    Write-Host "8. Reset All (Full Reset)" -ForegroundColor Yellow
    Write-Host "9. Exit" -ForegroundColor Gray
    Write-Host "-" * 40

    $choice = Read-Host "`nEnter your choice (1-9)"

    switch ($choice) {
        "1" { Reset-DockerDesktop }
        "2" { Clear-DockerCache }
        "3" { Fix-WSL2 }
        "4" { Reset-VirtualEnvironment }
        "5" { Clear-PythonCache }
        "6" { Fix-Permissions }
        "7" { Diagnose-Network }
        "8" { Reset-All }
        "9" {
            Write-Info "Exiting..."
            return
        }
        default {
            Write-Warning-Custom "Invalid choice"
        }
    }

    # Show menu again unless exit was chosen
    if ($choice -ne "9") {
        Write-Host "`nPress Enter to return to menu..."
        Read-Host
        Show-Menu
    }
}

# Main execution
function Main {
    Write-Header "AI Platform - Windows Troubleshooting"
    Write-Host "Project: $script:ProjectRoot" -ForegroundColor Gray

    switch ($Action) {
        "Menu" { Show-Menu }
        "ResetDocker" { Reset-DockerDesktop }
        "ClearDockerCache" { Clear-DockerCache }
        "FixWSL" { Fix-WSL2 }
        "ResetVenv" { Reset-VirtualEnvironment }
        "ClearPythonCache" { Clear-PythonCache }
        "FixPermissions" { Fix-Permissions }
        "ResetAll" { Reset-All }
        "DiagnoseNetwork" { Diagnose-Network }
    }
}

Main
