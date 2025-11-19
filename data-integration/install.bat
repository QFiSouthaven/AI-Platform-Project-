@echo off
REM Installation script for Data Integration module on Windows
REM This script sets up the Python environment and installs dependencies

echo ==========================================
echo Data Integration Module - Windows Installer
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies from requirements.txt...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found
    echo Installing core dependencies...
    pip install fastapi uvicorn pydantic-settings structlog
    pip install redis aiokafka
)

REM Create .env file from example if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env file from .env.example...
        copy ".env.example" ".env"
        echo Please edit .env file with your configuration
    )
)

echo.
echo ==========================================
echo Installation completed successfully!
echo ==========================================
echo.
echo Prerequisites:
echo - Redis server must be running on localhost:6379
echo - Kafka broker must be running on localhost:9092
echo.
echo To start the service, run: start.bat
echo To activate the environment manually: venv\Scripts\activate.bat
echo.
pause
