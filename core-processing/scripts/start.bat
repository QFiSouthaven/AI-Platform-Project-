@echo off
setlocal enabledelayedexpansion

:: Set console color (bright white on blue)
color 1F

echo ============================================
echo   Starting core-processing on port 8003
echo ============================================
echo.

:: Check for Python availability
python --version >nul 2>&1
if errorlevel 1 (
    color 4F
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.9+ and try again.
    pause
    exit /b 1
)

:: Check for uvicorn availability
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    color 4F
    echo [ERROR] uvicorn is not installed!
    echo Please run install.bat first.
    pause
    exit /b 1
)

:: Change to module directory
cd /d "%~dp0.."
if errorlevel 1 (
    color 4F
    echo [ERROR] Failed to change to module directory!
    pause
    exit /b 1
)

echo [INFO] Current directory: %CD%
echo [INFO] Starting FastAPI application...
echo [INFO] Press Ctrl+C to stop the server
echo.

:: Start uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

if errorlevel 1 (
    color 4F
    echo.
    echo [ERROR] Server stopped with error!
    pause
    exit /b 1
)

endlocal
