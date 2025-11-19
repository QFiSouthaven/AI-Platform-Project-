@echo off
REM Model Management Module - Windows Installation Script
REM Requires Python 3.9+ to be installed and in PATH

echo ========================================
echo Model Management Module - Installation
echo ========================================
echo.

REM Check Python version
python --version 2>NUL
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create necessary directories
echo Creating storage directories...
if not exist "%LOCALAPPDATA%\model-management\models" mkdir "%LOCALAPPDATA%\model-management\models"
if not exist "%LOCALAPPDATA%\model-management\plugins" mkdir "%LOCALAPPDATA%\model-management\plugins"
if not exist "%LOCALAPPDATA%\model-management\secrets" mkdir "%LOCALAPPDATA%\model-management\secrets"
if not exist "%TEMP%\model-management" mkdir "%TEMP%\model-management"

REM Copy .env.example to .env if not exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file and update the configuration values
) else (
    echo .env file already exists
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Ensure MongoDB is running
echo 3. Run start.bat to start the service
echo.
pause
