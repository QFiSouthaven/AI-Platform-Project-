@echo off
setlocal enabledelayedexpansion

:: Set console color (bright white on blue)
color 1F

echo ============================================
echo   Installing dependencies for core-processing
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

:: Change to module directory
cd /d "%~dp0.."
if errorlevel 1 (
    color 4F
    echo [ERROR] Failed to change to module directory!
    goto :error
)

echo [INFO] Current directory: %CD%
echo.

:: Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    color 4F
    echo [ERROR] Failed to upgrade pip!
    goto :error
)

echo.

:: Install requirements
echo [INFO] Installing requirements...
if exist requirements.txt (
    pip install -r requirements.txt
    if errorlevel 1 (
        color 4F
        echo [ERROR] Failed to install requirements!
        goto :error
    )
) else (
    color 6F
    echo [WARNING] requirements.txt not found!
)

echo.
color 2F
echo ============================================
echo   Installation completed successfully!
echo ============================================
goto :end

:error
echo.
echo ============================================
echo   Installation failed!
echo ============================================

:end
echo.
pause
endlocal
