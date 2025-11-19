#Requires -Version 5.1
<#
.SYNOPSIS
    Comprehensive Windows 11 validation script for AI Platform development environment.

.DESCRIPTION
    Validates all prerequisites for running the AI Platform on Windows 11:
    - Python 3.9+
    - pip
    - Docker Desktop
    - Docker Compose
    - WSL2
    - System resources
    - Environment files
    - Database connections

.PARAMETER SkipDatabaseCheck
    Skip database connectivity tests

.PARAMETER Verbose
    Show detailed output

.EXAMPLE
    .\validate-windows.ps1
    .\validate-windows.ps1 -SkipDatabaseCheck
#>

[CmdletBinding()]
param(
    [switch]$SkipDatabaseCheck,
    [switch]$Detailed
)

$ErrorActionPreference = "Stop"

# Script configuration
$script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$script:ValidationResults = @()
$script:WarningCount = 0
$script:ErrorCount = 0

# Helper functions
function Write-Header {
    param([string]$Text)
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Write-SubHeader {
    param([string]$Text)
    Write-Host "`n$Text" -ForegroundColor Yellow
    Write-Host "-" * 40 -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Text)
    Write-Host "[PASS] " -ForegroundColor Green -NoNewline
    Write-Host $Text
}

function Write-Failure {
    param([string]$Text)
    Write-Host "[FAIL] " -ForegroundColor Red -NoNewline
    Write-Host $Text
    $script:ErrorCount++
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $Text
    $script:WarningCount++
}

function Write-Info {
    param([string]$Text)
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $Text
}

function Add-ValidationResult {
    param(
        [string]$Component,
        [string]$Status,
        [string]$Details
    )
    $script:ValidationResults += [PSCustomObject]@{
        Component = $Component
        Status = $Status
        Details = $Details
    }
}

function Test-CommandExists {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Validation functions
function Test-PythonInstallation {
    Write-SubHeader "Python Installation"

    try {
        if (Test-CommandExists "python") {
            $pythonVersion = python --version 2>&1
            $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)"

            if ($versionMatch) {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]

                if ($major -ge 3 -and $minor -ge 9) {
                    Write-Success "Python $($Matches[1]).$($Matches[2]).$($Matches[3]) installed"
                    Add-ValidationResult "Python" "PASS" "$pythonVersion"

                    # Check Python path
                    $pythonPath = (Get-Command python).Source
                    Write-Info "Python path: $pythonPath"

                    return $true
                } else {
                    Write-Failure "Python version $major.$minor is below required 3.9"
                    Add-ValidationResult "Python" "FAIL" "Version too low: $pythonVersion"
                    return $false
                }
            }
        } else {
            Write-Failure "Python not found in PATH"
            Add-ValidationResult "Python" "FAIL" "Not installed"
            return $false
        }
    } catch {
        Write-Failure "Error checking Python: $_"
        Add-ValidationResult "Python" "FAIL" $_.Exception.Message
        return $false
    }
}

function Test-PipInstallation {
    Write-SubHeader "Pip Installation"

    try {
        if (Test-CommandExists "pip") {
            $pipVersion = pip --version 2>&1
            Write-Success "pip installed: $pipVersion"
            Add-ValidationResult "pip" "PASS" $pipVersion
            return $true
        } else {
            Write-Failure "pip not found in PATH"
            Add-ValidationResult "pip" "FAIL" "Not installed"
            return $false
        }
    } catch {
        Write-Failure "Error checking pip: $_"
        Add-ValidationResult "pip" "FAIL" $_.Exception.Message
        return $false
    }
}

function Test-DockerDesktop {
    Write-SubHeader "Docker Desktop"

    try {
        # Check if Docker command exists
        if (-not (Test-CommandExists "docker")) {
            Write-Failure "Docker not found in PATH"
            Add-ValidationResult "Docker" "FAIL" "Not installed"
            return $false
        }

        # Check Docker daemon is running
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Failure "Docker Desktop is not running"
            Write-Info "Please start Docker Desktop from the Start menu"
            Add-ValidationResult "Docker" "FAIL" "Not running"
            return $false
        }

        # Get Docker version
        $dockerVersion = docker --version 2>&1
        Write-Success "Docker installed: $dockerVersion"

        # Check Docker server version
        $serverVersion = docker version --format '{{.Server.Version}}' 2>&1
        Write-Info "Docker Server: $serverVersion"

        Add-ValidationResult "Docker" "PASS" $dockerVersion
        return $true
    } catch {
        Write-Failure "Error checking Docker: $_"
        Add-ValidationResult "Docker" "FAIL" $_.Exception.Message
        return $false
    }
}

function Test-DockerCompose {
    Write-SubHeader "Docker Compose"

    try {
        # Try docker compose (v2) first
        $composeVersion = docker compose version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker Compose (v2): $composeVersion"
            Add-ValidationResult "Docker Compose" "PASS" $composeVersion
            return $true
        }

        # Fall back to docker-compose (v1)
        if (Test-CommandExists "docker-compose") {
            $composeVersion = docker-compose --version 2>&1
            Write-Success "Docker Compose (v1): $composeVersion"
            Add-ValidationResult "Docker Compose" "PASS" $composeVersion
            return $true
        }

        Write-Failure "Docker Compose not found"
        Add-ValidationResult "Docker Compose" "FAIL" "Not installed"
        return $false
    } catch {
        Write-Failure "Error checking Docker Compose: $_"
        Add-ValidationResult "Docker Compose" "FAIL" $_.Exception.Message
        return $false
    }
}

function Test-WSL2 {
    Write-SubHeader "WSL2 Configuration"

    try {
        # Check if WSL is installed
        $wslStatus = wsl --status 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning-Custom "WSL2 may not be properly configured"
            Write-Info "Run 'wsl --install' to install WSL2"
            Add-ValidationResult "WSL2" "WARN" "Not configured"
            return $false
        }

        # Check default version
        $wslList = wsl -l -v 2>&1
        if ($wslList -match "VERSION\s+2") {
            Write-Success "WSL2 is enabled and configured"
            Add-ValidationResult "WSL2" "PASS" "Enabled"

            # Show distributions
            if ($Detailed) {
                Write-Info "WSL Distributions:"
                $wslList | ForEach-Object { Write-Host "  $_" }
            }
            return $true
        } else {
            Write-Warning-Custom "WSL2 may not be the default version"
            Write-Info "Run 'wsl --set-default-version 2' to set WSL2 as default"
            Add-ValidationResult "WSL2" "WARN" "Check version"
            return $false
        }
    } catch {
        Write-Warning-Custom "Could not verify WSL2 status"
        Add-ValidationResult "WSL2" "WARN" "Unable to verify"
        return $false
    }
}

function Test-SystemMemory {
    Write-SubHeader "System Memory"

    try {
        $computerInfo = Get-CimInstance -ClassName Win32_ComputerSystem
        $totalMemoryGB = [math]::Round($computerInfo.TotalPhysicalMemory / 1GB, 2)

        $availableMemory = Get-CimInstance -ClassName Win32_OperatingSystem
        $freeMemoryGB = [math]::Round($availableMemory.FreePhysicalMemory / 1MB, 2)

        Write-Info "Total Memory: $totalMemoryGB GB"
        Write-Info "Available Memory: $freeMemoryGB GB"

        if ($totalMemoryGB -ge 16) {
            Write-Success "Excellent! 16GB+ RAM available"
            Add-ValidationResult "Memory" "PASS" "$totalMemoryGB GB"
        } elseif ($totalMemoryGB -ge 8) {
            Write-Success "8GB+ RAM available (recommended minimum)"
            Add-ValidationResult "Memory" "PASS" "$totalMemoryGB GB"
        } else {
            Write-Warning-Custom "Less than 8GB RAM detected. Performance may be limited."
            Add-ValidationResult "Memory" "WARN" "$totalMemoryGB GB"
        }

        return $totalMemoryGB -ge 8
    } catch {
        Write-Warning-Custom "Could not determine system memory: $_"
        Add-ValidationResult "Memory" "WARN" "Unable to check"
        return $false
    }
}

function Test-DiskSpace {
    Write-SubHeader "Disk Space"

    try {
        $drive = Get-PSDrive -Name (Split-Path $script:ProjectRoot -Qualifier).TrimEnd(':')
        $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
        $totalSpaceGB = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)

        Write-Info "Drive $($drive.Name): $freeSpaceGB GB free of $totalSpaceGB GB"

        if ($freeSpaceGB -ge 50) {
            Write-Success "Plenty of disk space available"
            Add-ValidationResult "Disk Space" "PASS" "$freeSpaceGB GB free"
        } elseif ($freeSpaceGB -ge 20) {
            Write-Success "Adequate disk space available"
            Add-ValidationResult "Disk Space" "PASS" "$freeSpaceGB GB free"
        } else {
            Write-Warning-Custom "Low disk space. At least 20GB recommended."
            Add-ValidationResult "Disk Space" "WARN" "$freeSpaceGB GB free"
        }

        return $freeSpaceGB -ge 20
    } catch {
        Write-Warning-Custom "Could not check disk space: $_"
        Add-ValidationResult "Disk Space" "WARN" "Unable to check"
        return $false
    }
}

function Test-EnvironmentFiles {
    Write-SubHeader "Environment Files"

    $modules = @(
        "user-gateway",
        "workflow-orchestration",
        "core-processing",
        "data-integration",
        "model-management",
        "infrastructure"
    )

    $allFound = $true
    $foundCount = 0
    $exampleCount = 0

    foreach ($module in $modules) {
        $envPath = Join-Path $script:ProjectRoot "$module/.env"
        $envExamplePath = Join-Path $script:ProjectRoot "$module/.env.example"

        if (Test-Path $envPath) {
            Write-Success "$module/.env exists"
            $foundCount++
        } elseif (Test-Path $envExamplePath) {
            Write-Warning-Custom "$module/.env missing (example exists)"
            $exampleCount++
            $allFound = $false
        } else {
            Write-Info "$module/.env not found (module may not be implemented)"
        }
    }

    # Check root .env
    $rootEnv = Join-Path $script:ProjectRoot ".env"
    if (Test-Path $rootEnv) {
        Write-Success "Root .env exists"
        $foundCount++
    }

    if ($allFound -and $foundCount -gt 0) {
        Add-ValidationResult "Env Files" "PASS" "$foundCount files found"
    } elseif ($exampleCount -gt 0) {
        Add-ValidationResult "Env Files" "WARN" "$exampleCount need to be created from examples"
    } else {
        Add-ValidationResult "Env Files" "INFO" "No env files found yet"
    }

    return $allFound
}

function Test-DatabaseConnections {
    Write-SubHeader "Database Connections"

    if ($SkipDatabaseCheck) {
        Write-Info "Skipping database checks (use -SkipDatabaseCheck to enable)"
        Add-ValidationResult "Databases" "SKIP" "Skipped by user"
        return $true
    }

    $allConnected = $true

    # Test PostgreSQL
    try {
        $pgResult = docker exec -i ai-platform-postgres pg_isready 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "PostgreSQL is ready"
        } else {
            Write-Warning-Custom "PostgreSQL not responding (container may not be running)"
            $allConnected = $false
        }
    } catch {
        Write-Warning-Custom "Could not check PostgreSQL"
        $allConnected = $false
    }

    # Test MongoDB
    try {
        $mongoResult = docker exec -i ai-platform-mongodb mongosh --eval "db.runCommand('ping')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "MongoDB is ready"
        } else {
            Write-Warning-Custom "MongoDB not responding (container may not be running)"
            $allConnected = $false
        }
    } catch {
        Write-Warning-Custom "Could not check MongoDB"
        $allConnected = $false
    }

    # Test Redis
    try {
        $redisResult = docker exec -i ai-platform-redis redis-cli ping 2>&1
        if ($redisResult -match "PONG") {
            Write-Success "Redis is ready"
        } else {
            Write-Warning-Custom "Redis not responding (container may not be running)"
            $allConnected = $false
        }
    } catch {
        Write-Warning-Custom "Could not check Redis"
        $allConnected = $false
    }

    if ($allConnected) {
        Add-ValidationResult "Databases" "PASS" "All connected"
    } else {
        Add-ValidationResult "Databases" "WARN" "Some databases not available"
    }

    return $allConnected
}

function Test-GitInstallation {
    Write-SubHeader "Git Installation"

    try {
        if (Test-CommandExists "git") {
            $gitVersion = git --version 2>&1
            Write-Success "Git installed: $gitVersion"
            Add-ValidationResult "Git" "PASS" $gitVersion
            return $true
        } else {
            Write-Warning-Custom "Git not found in PATH"
            Add-ValidationResult "Git" "WARN" "Not installed"
            return $false
        }
    } catch {
        Write-Warning-Custom "Error checking Git: $_"
        Add-ValidationResult "Git" "WARN" $_.Exception.Message
        return $false
    }
}

function Show-SystemInfo {
    Write-SubHeader "System Information"

    try {
        $os = Get-CimInstance -ClassName Win32_OperatingSystem
        $cpu = Get-CimInstance -ClassName Win32_Processor

        Write-Info "OS: $($os.Caption) $($os.Version)"
        Write-Info "CPU: $($cpu.Name)"
        Write-Info "Cores: $($cpu.NumberOfCores) / Threads: $($cpu.NumberOfLogicalProcessors)"
        Write-Info "Project Root: $script:ProjectRoot"
    } catch {
        Write-Warning-Custom "Could not retrieve system information"
    }
}

function Show-Summary {
    Write-Header "Validation Summary"

    # Display results table
    Write-Host "`nComponent Status:" -ForegroundColor White
    Write-Host "-" * 50

    foreach ($result in $script:ValidationResults) {
        $statusColor = switch ($result.Status) {
            "PASS" { "Green" }
            "FAIL" { "Red" }
            "WARN" { "Yellow" }
            "SKIP" { "Gray" }
            default { "White" }
        }

        $status = $result.Status.PadRight(6)
        $component = $result.Component.PadRight(20)

        Write-Host "$component " -NoNewline
        Write-Host "[$status]" -ForegroundColor $statusColor -NoNewline
        Write-Host " $($result.Details)"
    }

    Write-Host "-" * 50

    # Final status
    Write-Host "`n"
    if ($script:ErrorCount -eq 0 -and $script:WarningCount -eq 0) {
        Write-Host "All validations passed! Your environment is ready." -ForegroundColor Green
        return 0
    } elseif ($script:ErrorCount -eq 0) {
        Write-Host "Validation completed with $($script:WarningCount) warning(s)." -ForegroundColor Yellow
        Write-Host "Your environment should work but may need attention." -ForegroundColor Yellow
        return 0
    } else {
        Write-Host "Validation completed with $($script:ErrorCount) error(s) and $($script:WarningCount) warning(s)." -ForegroundColor Red
        Write-Host "Please fix the errors before proceeding." -ForegroundColor Red
        return 1
    }
}

# Main execution
function Main {
    Write-Header "AI Platform - Windows 11 Environment Validation"
    Write-Host "Project: $script:ProjectRoot" -ForegroundColor Gray
    Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

    # Run all validations
    Show-SystemInfo
    Test-GitInstallation
    Test-PythonInstallation
    Test-PipInstallation
    Test-DockerDesktop
    Test-DockerCompose
    Test-WSL2
    Test-SystemMemory
    Test-DiskSpace
    Test-EnvironmentFiles
    Test-DatabaseConnections

    # Show summary
    $exitCode = Show-Summary

    Write-Host "`nFor detailed setup instructions, see WINDOWS-SETUP.md" -ForegroundColor Cyan
    Write-Host "For troubleshooting, run: .\scripts\troubleshoot-windows.ps1" -ForegroundColor Cyan

    exit $exitCode
}

# Run main function
Main
