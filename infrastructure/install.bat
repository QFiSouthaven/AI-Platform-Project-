@echo off
REM Infrastructure Module - Windows Installation Script
REM Requires Python 3.9+ to be installed and in PATH

echo ========================================
echo Infrastructure Module - Installation
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

REM Install Ray with Windows compatibility
echo Installing Ray...
pip install "ray[default]"

REM Create necessary directories
echo Creating directories...
if not exist "%TEMP%\ray" mkdir "%TEMP%\ray"

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
echo 2. Ensure Redis is running (optional)
echo 3. Run start.bat to start the service
echo.
echo Note: Ray dashboard is disabled on Windows by default
echo       due to compatibility issues.
echo.
pause
