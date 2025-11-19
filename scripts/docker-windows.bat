@echo off
REM =============================================================================
REM AI Platform - Windows Docker Operations Batch Wrapper
REM =============================================================================
REM This batch file wraps the PowerShell script for easy command-line usage.
REM
REM Usage:
REM   docker-windows.bat                    - Start all services
REM   docker-windows.bat start              - Start all services
REM   docker-windows.bat stop               - Stop all services
REM   docker-windows.bat restart            - Restart all services
REM   docker-windows.bat status             - Show service status
REM   docker-windows.bat logs               - Show logs
REM   docker-windows.bat build              - Build images
REM   docker-windows.bat clean              - Remove containers
REM   docker-windows.bat help               - Show help
REM
REM Note: This script calls docker-windows.ps1 with the provided arguments.
REM       For advanced options, use the PowerShell script directly.
REM =============================================================================

setlocal EnableDelayedExpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Check if PowerShell is available
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PowerShell is not installed or not in PATH
    echo Please install PowerShell or use the PowerShell script directly.
    exit /b 1
)

REM Set default action if none provided
set "ACTION=%1"
if "%ACTION%"=="" set "ACTION=start"

REM Map batch arguments to PowerShell parameters
set "PS_ARGS=-Action %ACTION%"

REM Handle additional arguments
shift
:parse_args
if "%1"=="" goto run_script
set "PS_ARGS=%PS_ARGS% %1"
shift
goto parse_args

:run_script
REM Run the PowerShell script with execution policy bypass
REM The -NoProfile flag speeds up execution by not loading user profile
REM The -ExecutionPolicy Bypass allows running unsigned scripts

echo.
echo ============================================================
echo   AI Platform - Docker Windows Operations
echo ============================================================
echo.
echo Running: powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%docker-windows.ps1" %PS_ARGS%
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%docker-windows.ps1" %PS_ARGS%

REM Capture exit code from PowerShell
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% neq 0 (
    echo.
    echo [ERROR] Script completed with errors (exit code: %EXIT_CODE%)
)

exit /b %EXIT_CODE%
