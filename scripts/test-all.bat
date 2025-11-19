@echo off
setlocal enabledelayedexpansion

:: Set console color (bright white on purple)
color 5F

echo ============================================
echo   AI Platform - Run All Tests
echo ============================================
echo.

:: Check for Python availability
python --version >nul 2>&1
if errorlevel 1 (
    color 4F
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.9+ and try again.
    goto :error
)

:: Check for pytest availability
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    color 4F
    echo [ERROR] pytest is not installed!
    echo Please run install-all.bat first.
    goto :error
)

:: Store root directory
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

echo [INFO] Project root: %ROOT_DIR%
echo.

:: Track results
set "FAILED_MODULES="
set "PASSED_COUNT=0"
set "TOTAL_COUNT=0"

:: Test user-gateway
echo ============================================
echo   [1/6] Testing user-gateway
echo ============================================
if exist "%ROOT_DIR%\user-gateway\tests" (
    set /a TOTAL_COUNT+=1
    cd /d "%ROOT_DIR%\user-gateway"
    pytest tests/ -v --tb=short
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! user-gateway"
    ) else (
        set /a PASSED_COUNT+=1
    )
) else (
    echo [WARNING] user-gateway/tests not found, skipping...
)
echo.

:: Test workflow-orchestration
echo ============================================
echo   [2/6] Testing workflow-orchestration
echo ============================================
if exist "%ROOT_DIR%\workflow-orchestration\tests" (
    set /a TOTAL_COUNT+=1
    cd /d "%ROOT_DIR%\workflow-orchestration"
    pytest tests/ -v --tb=short
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! workflow-orchestration"
    ) else (
        set /a PASSED_COUNT+=1
    )
) else (
    echo [WARNING] workflow-orchestration/tests not found, skipping...
)
echo.

:: Test core-processing
echo ============================================
echo   [3/6] Testing core-processing
echo ============================================
if exist "%ROOT_DIR%\core-processing\tests" (
    set /a TOTAL_COUNT+=1
    cd /d "%ROOT_DIR%\core-processing"
    pytest tests/ -v --tb=short
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! core-processing"
    ) else (
        set /a PASSED_COUNT+=1
    )
) else (
    echo [WARNING] core-processing/tests not found, skipping...
)
echo.

:: Test data-integration
echo ============================================
echo   [4/6] Testing data-integration
echo ============================================
if exist "%ROOT_DIR%\data-integration\tests" (
    set /a TOTAL_COUNT+=1
    cd /d "%ROOT_DIR%\data-integration"
    pytest tests/ -v --tb=short
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! data-integration"
    ) else (
        set /a PASSED_COUNT+=1
    )
) else (
    echo [WARNING] data-integration/tests not found, skipping...
)
echo.

:: Test model-management
echo ============================================
echo   [5/6] Testing model-management
echo ============================================
if exist "%ROOT_DIR%\model-management\tests" (
    set /a TOTAL_COUNT+=1
    cd /d "%ROOT_DIR%\model-management"
    pytest tests/ -v --tb=short
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! model-management"
    ) else (
        set /a PASSED_COUNT+=1
    )
) else (
    echo [WARNING] model-management/tests not found, skipping...
)
echo.

:: Test infrastructure
echo ============================================
echo   [6/6] Testing infrastructure
echo ============================================
if exist "%ROOT_DIR%\infrastructure\tests" (
    set /a TOTAL_COUNT+=1
    cd /d "%ROOT_DIR%\infrastructure"
    pytest tests/ -v --tb=short
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! infrastructure"
    ) else (
        set /a PASSED_COUNT+=1
    )
) else (
    echo [WARNING] infrastructure/tests not found, skipping...
)
echo.

:: Summary
echo ============================================
echo   Test Summary
echo ============================================
echo.
echo Passed: %PASSED_COUNT%/%TOTAL_COUNT% modules

if defined FAILED_MODULES (
    color 4F
    echo.
    echo [ERROR] Failed modules:%FAILED_MODULES%
    goto :error
)

if %TOTAL_COUNT% EQU 0 (
    color 6F
    echo.
    echo [WARNING] No test directories found!
    goto :end
)

color 2F
echo.
echo ============================================
echo   All tests passed successfully!
echo ============================================
goto :end

:error
echo.
echo ============================================
echo   Test run completed with failures!
echo ============================================

:end
echo.
pause
endlocal
