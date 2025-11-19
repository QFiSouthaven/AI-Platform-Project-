@echo off
REM AI Platform Windows Setup Script
REM This is a wrapper for the PowerShell setup script

echo.
echo ====================================
echo AI Platform Windows Setup
echo ====================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: PowerShell is not available on this system.
    echo Please install PowerShell or run the .ps1 script directly.
    pause
    exit /b 1
)

REM Get the directory of this script
set SCRIPT_DIR=%~dp0

REM Check if the PowerShell script exists
if not exist "%SCRIPT_DIR%setup-windows.ps1" (
    echo ERROR: setup-windows.ps1 not found in %SCRIPT_DIR%
    pause
    exit /b 1
)

REM Run the PowerShell script
echo Running setup-windows.ps1...
echo.

REM Try PowerShell Core first, fall back to Windows PowerShell
where pwsh >nul 2>&1
if %ERRORLEVEL% equ 0 (
    pwsh -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup-windows.ps1" %*
) else (
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup-windows.ps1" %*
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo Setup completed with errors.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Setup completed successfully!
pause
