#Requires -Version 5.1
<#
.SYNOPSIS
    Development environment setup for AI Platform.

.DESCRIPTION
    Sets up the development environment including virtual environments,
    dev dependencies, pre-commit hooks, and IDE configurations.

.PARAMETER Module
    Setup only a specific module.

.PARAMETER SkipPreCommit
    Skip pre-commit hook installation.

.PARAMETER SkipVenv
    Skip virtual environment creation.

.EXAMPLE
    .\dev-setup.ps1

.EXAMPLE
    .\dev-setup.ps1 -Module user-gateway

.NOTES
    Author: AI Platform Development Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [string]$Module,
    [switch]$SkipPreCommit,
    [switch]$SkipVenv,
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

# Filter modules if specific one requested
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

AI Platform Development Setup
=============================

"@ "Cyan"

Write-Step "Creating Virtual Environments"

if (-not $SkipVenv) {
    foreach ($mod in $Modules) {
        $modulePath = Join-Path $ProjectRoot $mod

        if (-not (Test-Path $modulePath)) {
            New-Item -ItemType Directory -Path $modulePath -Force | Out-Null
        }

        $venvPath = Join-Path $modulePath "venv"

        if (Test-Path $venvPath) {
            Write-Info "Virtual environment already exists for $mod"
            continue
        }

        Write-Info "Creating virtual environment for $mod..."
        python -m venv "$venvPath"

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Created virtual environment for $mod"
        } else {
            Write-Error "Failed to create virtual environment for $mod"
        }
    }
}

Write-Step "Installing Development Dependencies"

foreach ($mod in $Modules) {
    $modulePath = Join-Path $ProjectRoot $mod
    $venvPip = Join-Path $modulePath "venv\Scripts\pip.exe"
    $requirementsDev = Join-Path $modulePath "requirements-dev.txt"

    if (-not (Test-Path $venvPip)) {
        Write-Warning "No virtual environment found for $mod"
        continue
    }

    # Create requirements-dev.txt if it doesn't exist
    if (-not (Test-Path $requirementsDev)) {
        $devRequirements = @"
# Development dependencies for $mod

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
httpx>=0.24.0
factory-boy>=3.3.0

# Code quality
black>=23.7.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.5.0
pylint>=2.17.0

# Documentation
sphinx>=7.1.0
sphinx-rtd-theme>=1.3.0

# Pre-commit
pre-commit>=3.3.0

# Debugging
ipdb>=0.13.0
rich>=13.5.0
"@
        Set-Content -Path $requirementsDev -Value $devRequirements
        Write-Info "Created requirements-dev.txt for $mod"
    }

    # Install base requirements first
    $requirements = Join-Path $modulePath "requirements.txt"
    if (Test-Path $requirements) {
        Write-Info "Installing base dependencies for $mod..."
        & $venvPip install -r "$requirements" --quiet
    }

    # Install dev requirements
    Write-Info "Installing dev dependencies for $mod..."
    & $venvPip install -r "$requirementsDev" --quiet

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Installed dev dependencies for $mod"
    } else {
        Write-Warning "Some dev dependencies failed to install for $mod"
    }
}

Write-Step "Setting Up Pre-commit Hooks"

if (-not $SkipPreCommit) {
    $preCommitConfig = Join-Path $ProjectRoot ".pre-commit-config.yaml"

    if (-not (Test-Path $preCommitConfig)) {
        $preCommitContent = @"
# Pre-commit hooks for AI Platform
# See https://pre-commit.com for more information

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ['--ignore-missing-imports']
"@
        Set-Content -Path $preCommitConfig -Value $preCommitContent
        Write-Success "Created .pre-commit-config.yaml"
    }

    # Install pre-commit hooks
    Write-Info "Installing pre-commit hooks..."

    # Use pre-commit from first module's venv
    $firstModule = $Modules[0]
    $preCommitExe = Join-Path $ProjectRoot "$firstModule\venv\Scripts\pre-commit.exe"

    if (Test-Path $preCommitExe) {
        Set-Location $ProjectRoot
        & $preCommitExe install

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Pre-commit hooks installed"
        } else {
            Write-Warning "Failed to install pre-commit hooks"
        }
    } else {
        Write-Warning "pre-commit not found, skipping hook installation"
    }
}

Write-Step "Creating IDE Configurations"

# VS Code settings
$vscodeDir = Join-Path $ProjectRoot ".vscode"
if (-not (Test-Path $vscodeDir)) {
    New-Item -ItemType Directory -Path $vscodeDir -Force | Out-Null
}

$vscodeSettings = Join-Path $vscodeDir "settings.json"
if (-not (Test-Path $vscodeSettings)) {
    $settings = @"
{
    "python.defaultInterpreterPath": "./user-gateway/venv/Scripts/python.exe",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": "explicit"
    },
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.tabSize": 4
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true,
        "**/.pytest_cache": true,
        "**/.mypy_cache": true
    }
}
"@
    Set-Content -Path $vscodeSettings -Value $settings
    Write-Success "Created VS Code settings"
}

# VS Code extensions recommendations
$vscodeExtensions = Join-Path $vscodeDir "extensions.json"
if (-not (Test-Path $vscodeExtensions)) {
    $extensions = @"
{
    "recommendations": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-python.mypy-type-checker",
        "ms-azuretools.vscode-docker",
        "redhat.vscode-yaml",
        "eamodio.gitlens"
    ]
}
"@
    Set-Content -Path $vscodeExtensions -Value $extensions
    Write-Success "Created VS Code extension recommendations"
}

# Create pytest.ini
$pytestIni = Join-Path $ProjectRoot "pytest.ini"
if (-not (Test-Path $pytestIni)) {
    $pytestContent = @"
[pytest]
testpaths =
    user-gateway/tests
    workflow-orchestration/tests
    core-processing/tests
    data-integration/tests
    model-management/tests
    infrastructure/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --cov-report=term-missing
    --cov-report=html
asyncio_mode = auto
"@
    Set-Content -Path $pytestIni -Value $pytestContent
    Write-Success "Created pytest.ini"
}

# Create .gitignore additions for dev
$gitignore = Join-Path $ProjectRoot ".gitignore"
$gitignoreContent = @"

# Development
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.eggs/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/

# Build
dist/
build/

# Environment
.env
*.env.local
"@

if (-not (Test-Path $gitignore)) {
    Set-Content -Path $gitignore -Value $gitignoreContent
    Write-Success "Created .gitignore"
} else {
    # Check if already has Python ignores
    $existingContent = Get-Content $gitignore -Raw
    if ($existingContent -notmatch "__pycache__") {
        Add-Content -Path $gitignore -Value $gitignoreContent
        Write-Info "Updated .gitignore with development patterns"
    }
}

Write-Step "Development Setup Complete!"

Write-ColorOutput @"

Development environment is ready!

Quick Start:
------------
1. Open project in VS Code:
   code $ProjectRoot

2. Activate a module's virtual environment:
   cd user-gateway
   .\venv\Scripts\Activate.ps1

3. Run tests:
   pytest

4. Format code:
   black .
   isort .

5. Type check:
   mypy app/

Available Commands:
-------------------
- Run all tests:     .\scripts\run-tests.ps1
- Start services:    .\scripts\start-services.ps1
- Stop services:     .\scripts\stop-services.ps1

"@ "Green"
