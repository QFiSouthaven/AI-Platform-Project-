#Requires -Version 5.1
<#
.SYNOPSIS
    Run tests for AI Platform modules.

.DESCRIPTION
    Runs pytest for all or specific modules with optional coverage reporting.

.PARAMETER Module
    Run tests only for a specific module.

.PARAMETER Coverage
    Generate coverage report (default: true).

.PARAMETER Html
    Generate HTML coverage report.

.PARAMETER Verbose
    Show verbose test output.

.PARAMETER FailFast
    Stop on first failure.

.PARAMETER Parallel
    Run tests in parallel (requires pytest-xdist).

.EXAMPLE
    .\run-tests.ps1

.EXAMPLE
    .\run-tests.ps1 -Module user-gateway -Coverage -Html

.EXAMPLE
    .\run-tests.ps1 -FailFast -Verbose

.NOTES
    Author: AI Platform Development Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [string]$Module,
    [switch]$Coverage = $true,
    [switch]$Html,
    [switch]$Verbose,
    [switch]$FailFast,
    [switch]$Parallel,
    [string]$Marker,
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
$AllModules = @(
    "user-gateway",
    "workflow-orchestration",
    "core-processing",
    "data-integration",
    "model-management",
    "infrastructure"
)

# Filter modules
if ($Module) {
    if ($AllModules -contains $Module) {
        $Modules = @($Module)
    } else {
        Write-Error "Unknown module: $Module"
        Write-Info "Available modules: $($AllModules -join ', ')"
        exit 1
    }
} else {
    $Modules = $AllModules
}

Write-ColorOutput @"

AI Platform Test Runner
=======================

"@ "Cyan"

$totalPassed = 0
$totalFailed = 0
$totalSkipped = 0
$results = @()

foreach ($mod in $Modules) {
    $modulePath = Join-Path $ProjectRoot $mod
    $testsPath = Join-Path $modulePath "tests"
    $venvPython = Join-Path $modulePath "venv\Scripts\python.exe"
    $venvPytest = Join-Path $modulePath "venv\Scripts\pytest.exe"

    # Check if module has tests
    if (-not (Test-Path $testsPath)) {
        Write-Warning "No tests directory found for $mod"

        # Create test directory structure
        New-Item -ItemType Directory -Path $testsPath -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $testsPath "unit") -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $testsPath "integration") -Force | Out-Null

        # Create conftest.py
        $conftest = Join-Path $testsPath "conftest.py"
        $conftestContent = @"
"""
Pytest configuration for $mod tests.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_db():
    """Fixture for mocking database connections."""
    return MagicMock()


@pytest.fixture
def mock_kafka():
    """Fixture for mocking Kafka producer/consumer."""
    return MagicMock()


@pytest.fixture
def mock_redis():
    """Fixture for mocking Redis client."""
    return MagicMock()
"@
        Set-Content -Path $conftest -Value $conftestContent

        # Create sample test
        $sampleTest = Join-Path $testsPath "unit\test_sample.py"
        $sampleTestContent = @"
"""
Sample test file for $mod.
"""

import pytest


class TestSample:
    """Sample test class."""

    def test_example(self):
        """Example test that always passes."""
        assert True

    def test_addition(self):
        """Test basic addition."""
        assert 1 + 1 == 2

    @pytest.mark.skip(reason="Example of skipped test")
    def test_skipped(self):
        """This test will be skipped."""
        pass
"@
        Set-Content -Path $sampleTest -Value $sampleTestContent
        Write-Info "Created test structure for $mod"
    }

    # Check if pytest is available
    if (-not (Test-Path $venvPytest)) {
        Write-Warning "pytest not found for $mod, installing..."
        if (Test-Path $venvPython) {
            & $venvPython -m pip install pytest pytest-asyncio pytest-cov --quiet
        } else {
            Write-Warning "No virtual environment found for $mod, skipping"
            continue
        }
    }

    Write-Step "Running Tests for $mod"

    # Build pytest command
    $pytestArgs = @($testsPath)

    if ($Verbose) {
        $pytestArgs += "-v"
    }

    if ($FailFast) {
        $pytestArgs += "-x"
    }

    if ($Coverage) {
        $pytestArgs += "--cov=$modulePath\app"
        $pytestArgs += "--cov-report=term-missing"

        if ($Html) {
            $coverageDir = Join-Path $modulePath "htmlcov"
            $pytestArgs += "--cov-report=html:$coverageDir"
        }
    }

    if ($Parallel) {
        $pytestArgs += "-n"
        $pytestArgs += "auto"
    }

    if ($Marker) {
        $pytestArgs += "-m"
        $pytestArgs += $Marker
    }

    # Run tests
    Write-Info "Running: pytest $($pytestArgs -join ' ')"

    $testOutput = & $venvPytest $pytestArgs 2>&1
    $exitCode = $LASTEXITCODE

    # Display output
    $testOutput | ForEach-Object { Write-Host $_ }

    # Parse results (simplified)
    $passed = 0
    $failed = 0
    $skipped = 0

    foreach ($line in $testOutput) {
        if ($line -match "(\d+) passed") {
            $passed = [int]$Matches[1]
        }
        if ($line -match "(\d+) failed") {
            $failed = [int]$Matches[1]
        }
        if ($line -match "(\d+) skipped") {
            $skipped = [int]$Matches[1]
        }
    }

    $totalPassed += $passed
    $totalFailed += $failed
    $totalSkipped += $skipped

    $results += [PSCustomObject]@{
        Module = $mod
        Passed = $passed
        Failed = $failed
        Skipped = $skipped
        Status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
    }

    if ($exitCode -eq 0) {
        Write-Success "Tests passed for $mod"
    } else {
        Write-Error "Tests failed for $mod"
        if ($FailFast) {
            Write-Warning "Stopping due to -FailFast flag"
            break
        }
    }
}

Write-Step "Test Summary"

# Display results table
Write-Host ""
Write-Host "Module                    Passed  Failed  Skipped  Status"
Write-Host "=" * 60

foreach ($result in $results) {
    $statusColor = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    $line = "{0,-25} {1,6}  {2,6}  {3,7}  " -f $result.Module, $result.Passed, $result.Failed, $result.Skipped
    Write-Host $line -NoNewline
    Write-ColorOutput $result.Status $statusColor
}

Write-Host "=" * 60
Write-Host ("{0,-25} {1,6}  {2,6}  {3,7}" -f "TOTAL", $totalPassed, $totalFailed, $totalSkipped)
Write-Host ""

# Final status
if ($totalFailed -eq 0) {
    Write-Success "All tests passed! ($totalPassed passed, $totalSkipped skipped)"
    exit 0
} else {
    Write-Error "$totalFailed tests failed"
    exit 1
}
