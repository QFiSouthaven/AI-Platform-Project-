@echo off
REM Infrastructure Module - Windows Start Script

echo ========================================
echo Infrastructure Module - Starting...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found
    echo Copying from .env.example...
    copy .env.example .env
    echo Please edit .env with your configuration
)

REM Set default environment variables if not set
if not defined APP_ENV set APP_ENV=development

REM Create Ray temp directory
if not exist "%TEMP%\ray" mkdir "%TEMP%\ray"

echo.
echo Starting Infrastructure service...
echo Environment: %APP_ENV%
echo.
echo Note: Ray dashboard is disabled on Windows
echo       Check console output for task status
echo.

REM Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload

pause
