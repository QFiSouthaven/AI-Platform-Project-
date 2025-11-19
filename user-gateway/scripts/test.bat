@echo off
setlocal enabledelayedexpansion

:: Set console color (bright white on blue)
color 1F

echo ============================================
echo   Running tests for user-gateway
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
    echo Please run install.bat first.
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

:: Run pytest
if exist tests (
    echo [INFO] Running pytest...
    pytest tests/ -v --tb=short
    if errorlevel 1 (
        color 4F
        echo.
        echo [ERROR] Some tests failed!
        goto :error
    )
) else (
    color 6F
    echo [WARNING] tests directory not found!
    goto :end
)

echo.
color 2F
echo ============================================
echo   All tests passed successfully!
echo ============================================
goto :end

:error
echo.
echo ============================================
echo   Test run completed with errors!
echo ============================================

:end
echo.
pause
endlocal
