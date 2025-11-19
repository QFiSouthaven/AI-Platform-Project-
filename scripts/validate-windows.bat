@echo off
REM Windows validation batch wrapper
REM This script runs the PowerShell validation script

echo.
echo ============================================================
echo   AI Platform - Windows Environment Validation
echo ============================================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PowerShell not found. Please install PowerShell.
    exit /b 1
)

REM Get the script directory
set SCRIPT_DIR=%~dp0

REM Run the PowerShell validation script
powershell -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%validate-windows.ps1" %*

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% EQU 0 (
    echo Validation completed successfully.
) else (
    echo Validation completed with errors. Please review the output above.
)

exit /b %EXIT_CODE%
