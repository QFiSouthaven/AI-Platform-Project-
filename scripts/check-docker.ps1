# =============================================================================
# AI Platform - Docker Desktop Installation Check
# =============================================================================
# PowerShell script to check Docker Desktop installation and WSL2 backend.
#
# Usage:
#   .\check-docker.ps1
#
# This script verifies:
#   - Docker Desktop is installed
#   - Docker daemon is running
#   - WSL2 backend is configured (recommended for Windows 11)
#   - Docker Compose is available
#   - Minimum system requirements
#
# =============================================================================

$ErrorActionPreference = 'Continue'

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

function Write-Check {
    param([string]$Message)
    Write-Host "[?] $Message" -ForegroundColor Yellow -NoNewline
}

function Write-Pass {
    param([string]$Message)
    Write-Host "`r[PASS] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "`r[FAIL] $Message" -ForegroundColor Red
}

function Write-Warn {
    param([string]$Message)
    Write-Host "`r[WARN] $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "       $Message" -ForegroundColor Gray
}

# =============================================================================
# Check Functions
# =============================================================================

function Test-WindowsVersion {
    Write-Check "Checking Windows version..."

    $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem
    $version = [System.Environment]::OSVersion.Version
    $buildNumber = $osInfo.BuildNumber

    if ($version.Major -ge 10) {
        if ([int]$buildNumber -ge 22000) {
            Write-Pass "Windows 11 detected (Build $buildNumber)"
            return $true
        }
        elseif ([int]$buildNumber -ge 19041) {
            Write-Pass "Windows 10 20H1+ detected (Build $buildNumber)"
            Write-Info "Windows 11 is recommended for best performance"
            return $true
        }
        else {
            Write-Warn "Windows 10 Build $buildNumber detected"
            Write-Info "Update to Windows 10 20H2+ or Windows 11 for WSL2 support"
            return $true
        }
    }
    else {
        Write-Fail "Windows $($version.Major) detected"
        Write-Info "Windows 10 20H2+ or Windows 11 is required"
        return $false
    }
}

function Test-SystemResources {
    Write-Check "Checking system resources..."

    $computerInfo = Get-CimInstance -ClassName Win32_ComputerSystem
    $totalRamGB = [math]::Round($computerInfo.TotalPhysicalMemory / 1GB, 2)

    if ($totalRamGB -ge 16) {
        Write-Pass "System RAM: $totalRamGB GB (Recommended: 16GB+)"
        return $true
    }
    elseif ($totalRamGB -ge 8) {
        Write-Warn "System RAM: $totalRamGB GB (Minimum met, 16GB recommended)"
        Write-Info "Some services may be slow with limited memory"
        return $true
    }
    else {
        Write-Fail "System RAM: $totalRamGB GB (Minimum: 8GB required)"
        Write-Info "Docker may not run properly with insufficient memory"
        return $false
    }
}

function Test-DockerInstallation {
    Write-Check "Checking Docker installation..."

    $dockerPath = Get-Command docker -ErrorAction SilentlyContinue

    if ($dockerPath) {
        $dockerVersion = docker --version 2>&1
        Write-Pass "Docker installed: $dockerVersion"
        return $true
    }
    else {
        Write-Fail "Docker is not installed"
        Write-Info "Download Docker Desktop from: https://www.docker.com/products/docker-desktop"
        return $false
    }
}

function Test-DockerDaemon {
    Write-Check "Checking Docker daemon..."

    try {
        $result = docker info 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Pass "Docker daemon is running"
            return $true
        }
        else {
            Write-Fail "Docker daemon is not running"
            Write-Info "Start Docker Desktop application"
            return $false
        }
    }
    catch {
        Write-Fail "Cannot connect to Docker daemon"
        Write-Info "Ensure Docker Desktop is running"
        return $false
    }
}

function Test-WSL2Backend {
    Write-Check "Checking Docker backend..."

    try {
        $dockerInfo = docker info 2>&1

        # Check for WSL2
        if ($dockerInfo -match "Operating System:.*Microsoft.*WSL") {
            Write-Pass "WSL2 backend is enabled (Recommended)"
            return $true
        }
        # Check for Linux (which means WSL2)
        elseif ($dockerInfo -match "Kernel Version:.*microsoft") {
            Write-Pass "WSL2 backend is enabled (Recommended)"
            return $true
        }
        # Hyper-V backend
        elseif ($dockerInfo -match "Operating System:.*Windows") {
            Write-Warn "Hyper-V backend detected"
            Write-Info "Switch to WSL2 backend for better performance:"
            Write-Info "  1. Open Docker Desktop Settings"
            Write-Info "  2. Go to General settings"
            Write-Info "  3. Enable 'Use the WSL 2 based engine'"
            return $true
        }
        else {
            Write-Warn "Could not determine Docker backend"
            return $true
        }
    }
    catch {
        Write-Warn "Could not check Docker backend"
        return $true
    }
}

function Test-DockerCompose {
    Write-Check "Checking Docker Compose..."

    try {
        # Try docker compose (v2)
        $composeVersion = docker compose version 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Pass "Docker Compose V2: $composeVersion"
            return $true
        }
    }
    catch {
        # Ignore and try docker-compose
    }

    # Try docker-compose (v1)
    $composePath = Get-Command docker-compose -ErrorAction SilentlyContinue

    if ($composePath) {
        $composeVersion = docker-compose --version 2>&1
        Write-Pass "Docker Compose: $composeVersion"
        return $true
    }
    else {
        Write-Fail "Docker Compose is not installed"
        Write-Info "Docker Compose should be included with Docker Desktop"
        Write-Info "Reinstall Docker Desktop or install Compose separately"
        return $false
    }
}

function Test-WSLInstallation {
    Write-Check "Checking WSL installation..."

    $wslPath = Get-Command wsl -ErrorAction SilentlyContinue

    if ($wslPath) {
        try {
            $wslStatus = wsl --status 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Pass "WSL is installed and configured"
                return $true
            }
            else {
                Write-Warn "WSL is installed but may not be configured"
                Write-Info "Run 'wsl --install' in an admin terminal"
                return $true
            }
        }
        catch {
            Write-Warn "Could not check WSL status"
            return $true
        }
    }
    else {
        Write-Warn "WSL is not installed"
        Write-Info "Install WSL2 for best Docker performance:"
        Write-Info "  1. Open PowerShell as Administrator"
        Write-Info "  2. Run: wsl --install"
        Write-Info "  3. Restart your computer"
        return $true
    }
}

function Test-DockerResources {
    Write-Check "Checking Docker Desktop resources..."

    try {
        $dockerInfo = docker info 2>&1

        # Extract memory limit
        if ($dockerInfo -match "Total Memory:\s+([\d.]+)\s*([GMKT]i?B)") {
            $memValue = [double]$matches[1]
            $memUnit = $matches[2]

            $memGB = switch ($memUnit) {
                'GiB' { $memValue }
                'GB' { $memValue }
                'TiB' { $memValue * 1024 }
                'TB' { $memValue * 1024 }
                'MiB' { $memValue / 1024 }
                'MB' { $memValue / 1024 }
                default { $memValue }
            }

            if ($memGB -ge 8) {
                Write-Pass "Docker memory limit: $($memValue) $memUnit (Good)"
            }
            elseif ($memGB -ge 4) {
                Write-Warn "Docker memory limit: $($memValue) $memUnit"
                Write-Info "Increase memory in Docker Desktop Settings > Resources"
                Write-Info "Recommended: 8GB+ for all AI Platform services"
            }
            else {
                Write-Fail "Docker memory limit: $($memValue) $memUnit (Too low)"
                Write-Info "Increase memory in Docker Desktop Settings > Resources"
            }
        }
        else {
            Write-Pass "Docker resources configured"
        }

        # Extract CPU count
        if ($dockerInfo -match "CPUs:\s+(\d+)") {
            $cpus = [int]$matches[1]
            if ($cpus -ge 4) {
                Write-Info "Docker CPUs: $cpus (Good)"
            }
            else {
                Write-Info "Docker CPUs: $cpus (Consider increasing for better performance)"
            }
        }

        return $true
    }
    catch {
        Write-Warn "Could not check Docker resources"
        return $true
    }
}

function Test-NetworkPorts {
    Write-Check "Checking required ports..."

    $requiredPorts = @(
        @{ Port = 5432; Service = 'PostgreSQL' },
        @{ Port = 27017; Service = 'MongoDB' },
        @{ Port = 6379; Service = 'Redis' },
        @{ Port = 9092; Service = 'Kafka' },
        @{ Port = 2181; Service = 'Zookeeper' },
        @{ Port = 8001; Service = 'User Gateway' },
        @{ Port = 8002; Service = 'Workflow Orchestration' },
        @{ Port = 8003; Service = 'Core Processing' },
        @{ Port = 8004; Service = 'Data Integration' },
        @{ Port = 8005; Service = 'Model Management' },
        @{ Port = 8006; Service = 'Infrastructure' }
    )

    $portsInUse = @()

    foreach ($portInfo in $requiredPorts) {
        $connection = Get-NetTCPConnection -LocalPort $portInfo.Port -ErrorAction SilentlyContinue

        if ($connection) {
            $portsInUse += $portInfo
        }
    }

    if ($portsInUse.Count -eq 0) {
        Write-Pass "All required ports are available"
        return $true
    }
    else {
        Write-Warn "Some ports are already in use:"
        foreach ($port in $portsInUse) {
            Write-Info "  Port $($port.Port) ($($port.Service)) is in use"
        }
        Write-Info "Stop conflicting services or change port mappings"
        return $true
    }
}

# =============================================================================
# Main Check Function
# =============================================================================

function Invoke-AllChecks {
    Write-Header "Docker Desktop Installation Check"

    $results = @{
        Windows       = Test-WindowsVersion
        Resources     = Test-SystemResources
        Docker        = Test-DockerInstallation
        Daemon        = Test-DockerDaemon
        Compose       = Test-DockerCompose
        WSL           = Test-WSLInstallation
        Backend       = Test-WSL2Backend
        DockerConfig  = Test-DockerResources
        Ports         = Test-NetworkPorts
    }

    # Summary
    Write-Header "Summary"

    $passed = ($results.Values | Where-Object { $_ -eq $true }).Count
    $total = $results.Count

    if ($passed -eq $total) {
        Write-ColorOutput "All checks passed! ($passed/$total)" 'Green'
        Write-Host ""
        Write-ColorOutput "You're ready to run the AI Platform!" 'Green'
        Write-Info "Start services with: .\scripts\docker-windows.ps1"
    }
    else {
        Write-ColorOutput "Checks completed: $passed/$total passed" 'Yellow'
        Write-Host ""
        Write-Info "Address the issues above before running the AI Platform"
    }

    Write-Host ""

    return $passed -eq $total
}

# =============================================================================
# Main Entry Point
# =============================================================================

$success = Invoke-AllChecks

if ($success) {
    exit 0
}
else {
    exit 1
}
