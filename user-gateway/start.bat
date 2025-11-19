@echo off
REM Windows startup script for User Gateway module
REM This script starts the FastAPI application on Windows 11

setlocal enabledelayedexpansion

echo ============================================
echo  User Gateway - Windows Startup Script
echo ============================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found.
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env
    ) else (
        echo Please create a .env file with your configuration.
    )
)

REM Set default values if not in .env
if not defined HOST set HOST=0.0.0.0
if not defined PORT set PORT=8000

echo Starting User Gateway on %HOST%:%PORT%...
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Start the FastAPI application with uvicorn
python -m uvicorn app.main:app --host %HOST% --port %PORT% --reload

REM If uvicorn exits with error, pause to see the error
if errorlevel 1 (
    echo.
    echo ERROR: Server stopped unexpectedly.
    pause
)
