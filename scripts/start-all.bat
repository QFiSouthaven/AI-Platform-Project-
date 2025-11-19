@echo off
setlocal enabledelayedexpansion

:: Set console color (bright white on purple)
color 5F

echo ============================================
echo   AI Platform - Start All Services
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
    echo Please run install-all.bat first.
    pause
    exit /b 1
)

:: Store root directory
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

echo [INFO] Project root: %ROOT_DIR%
echo.
echo [INFO] Starting all services in separate windows...
echo.

:: Port assignments
echo Service Ports:
echo   - user-gateway:          http://localhost:8001
echo   - workflow-orchestration: http://localhost:8002
echo   - core-processing:       http://localhost:8003
echo   - data-integration:      http://localhost:8004
echo   - model-management:      http://localhost:8005
echo   - infrastructure:        http://localhost:8006
echo.

:: Start user-gateway
echo [INFO] Starting user-gateway on port 8001...
if exist "%ROOT_DIR%\user-gateway\app\main.py" (
    start "user-gateway (8001)" cmd /k "cd /d "%ROOT_DIR%\user-gateway" && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
) else (
    echo [WARNING] user-gateway/app/main.py not found, skipping...
)

:: Small delay between starts
timeout /t 2 /nobreak >nul

:: Start workflow-orchestration
echo [INFO] Starting workflow-orchestration on port 8002...
if exist "%ROOT_DIR%\workflow-orchestration\app\main.py" (
    start "workflow-orchestration (8002)" cmd /k "cd /d "%ROOT_DIR%\workflow-orchestration" && uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"
) else (
    echo [WARNING] workflow-orchestration/app/main.py not found, skipping...
)

timeout /t 2 /nobreak >nul

:: Start core-processing
echo [INFO] Starting core-processing on port 8003...
if exist "%ROOT_DIR%\core-processing\app\main.py" (
    start "core-processing (8003)" cmd /k "cd /d "%ROOT_DIR%\core-processing" && uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload"
) else (
    echo [WARNING] core-processing/app/main.py not found, skipping...
)

timeout /t 2 /nobreak >nul

:: Start data-integration
echo [INFO] Starting data-integration on port 8004...
if exist "%ROOT_DIR%\data-integration\app\main.py" (
    start "data-integration (8004)" cmd /k "cd /d "%ROOT_DIR%\data-integration" && uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload"
) else (
    echo [WARNING] data-integration/app/main.py not found, skipping...
)

timeout /t 2 /nobreak >nul

:: Start model-management
echo [INFO] Starting model-management on port 8005...
if exist "%ROOT_DIR%\model-management\app\main.py" (
    start "model-management (8005)" cmd /k "cd /d "%ROOT_DIR%\model-management" && uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload"
) else (
    echo [WARNING] model-management/app/main.py not found, skipping...
)

timeout /t 2 /nobreak >nul

:: Start infrastructure
echo [INFO] Starting infrastructure on port 8006...
if exist "%ROOT_DIR%\infrastructure\app\main.py" (
    start "infrastructure (8006)" cmd /k "cd /d "%ROOT_DIR%\infrastructure" && uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload"
) else (
    echo [WARNING] infrastructure/app/main.py not found, skipping...
)

echo.
color 2F
echo ============================================
echo   All services started!
echo ============================================
echo.
echo [INFO] Services are running in separate windows.
echo [INFO] Close this window or the service windows to stop.
echo.

pause
endlocal
