@echo off
REM Start script for Core Processing module on Windows

echo ==========================================
echo Starting Core Processing Module
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found
    echo Using default configuration
)

REM Set Windows-specific environment variables
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM Start the application
echo Starting FastAPI application...
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

REM If uvicorn fails, try alternative method
if errorlevel 1 (
    echo.
    echo Trying alternative startup method...
    python app/main.py
)

pause
