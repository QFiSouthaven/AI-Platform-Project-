@echo off
REM Windows installation script for User Gateway module
REM This script sets up the development environment on Windows 11

setlocal enabledelayedexpansion

echo ============================================
echo  User Gateway - Windows Installation Script
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [2/5] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo [2/5] Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated.
echo.

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [5/5] Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found
)

if exist "requirements-dev.txt" (
    pip install -r requirements-dev.txt
)

echo.
echo ============================================
echo  Installation Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Copy .env.example to .env
echo   2. Update .env with your configuration
echo   3. Run start.bat to start the service
echo.

REM Keep console open
pause
