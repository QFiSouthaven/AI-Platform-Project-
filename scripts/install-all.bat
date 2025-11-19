@echo off
setlocal enabledelayedexpansion

:: Set console color (bright white on purple)
color 5F

echo ============================================
echo   AI Platform - Install All Dependencies
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

:: Check for pip availability
pip --version >nul 2>&1
if errorlevel 1 (
    color 4F
    echo [ERROR] pip is not installed or not in PATH!
    echo Please install pip and try again.
    goto :error
)

:: Store root directory
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

echo [INFO] Project root: %ROOT_DIR%
echo.

:: Track success/failure
set "FAILED_MODULES="
set "SUCCESS_COUNT=0"

:: Install user-gateway
echo ============================================
echo   [1/6] Installing user-gateway
echo ============================================
if exist "%ROOT_DIR%\user-gateway\requirements.txt" (
    cd /d "%ROOT_DIR%\user-gateway"
    pip install -r requirements.txt
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! user-gateway"
    ) else (
        set /a SUCCESS_COUNT+=1
    )
) else (
    echo [WARNING] user-gateway/requirements.txt not found
)
echo.

:: Install workflow-orchestration
echo ============================================
echo   [2/6] Installing workflow-orchestration
echo ============================================
if exist "%ROOT_DIR%\workflow-orchestration\requirements.txt" (
    cd /d "%ROOT_DIR%\workflow-orchestration"
    pip install -r requirements.txt
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! workflow-orchestration"
    ) else (
        set /a SUCCESS_COUNT+=1
    )
) else (
    echo [WARNING] workflow-orchestration/requirements.txt not found
)
echo.

:: Install core-processing
echo ============================================
echo   [3/6] Installing core-processing
echo ============================================
if exist "%ROOT_DIR%\core-processing\requirements.txt" (
    cd /d "%ROOT_DIR%\core-processing"
    pip install -r requirements.txt
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! core-processing"
    ) else (
        set /a SUCCESS_COUNT+=1
    )
) else (
    echo [WARNING] core-processing/requirements.txt not found
)
echo.

:: Install data-integration
echo ============================================
echo   [4/6] Installing data-integration
echo ============================================
if exist "%ROOT_DIR%\data-integration\requirements.txt" (
    cd /d "%ROOT_DIR%\data-integration"
    pip install -r requirements.txt
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! data-integration"
    ) else (
        set /a SUCCESS_COUNT+=1
    )
) else (
    echo [WARNING] data-integration/requirements.txt not found
)
echo.

:: Install model-management
echo ============================================
echo   [5/6] Installing model-management
echo ============================================
if exist "%ROOT_DIR%\model-management\requirements.txt" (
    cd /d "%ROOT_DIR%\model-management"
    pip install -r requirements.txt
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! model-management"
    ) else (
        set /a SUCCESS_COUNT+=1
    )
) else (
    echo [WARNING] model-management/requirements.txt not found
)
echo.

:: Install infrastructure
echo ============================================
echo   [6/6] Installing infrastructure
echo ============================================
if exist "%ROOT_DIR%\infrastructure\requirements.txt" (
    cd /d "%ROOT_DIR%\infrastructure"
    pip install -r requirements.txt
    if errorlevel 1 (
        set "FAILED_MODULES=!FAILED_MODULES! infrastructure"
    ) else (
        set /a SUCCESS_COUNT+=1
    )
) else (
    echo [WARNING] infrastructure/requirements.txt not found
)
echo.

:: Summary
echo ============================================
echo   Installation Summary
echo ============================================
echo.
echo Successfully installed: %SUCCESS_COUNT%/6 modules

if defined FAILED_MODULES (
    color 4F
    echo.
    echo [ERROR] Failed modules:%FAILED_MODULES%
    goto :error
)

color 2F
echo.
echo ============================================
echo   All installations completed successfully!
echo ============================================
goto :end

:error
echo.
echo ============================================
echo   Installation completed with errors!
echo ============================================

:end
echo.
pause
endlocal
