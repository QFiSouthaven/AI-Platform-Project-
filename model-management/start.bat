@echo off
REM Model Management Module - Windows Start Script

echo ========================================
echo Model Management Module - Starting...
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

echo.
echo Starting Model Management service...
echo Environment: %APP_ENV%
echo.

REM Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

pause
