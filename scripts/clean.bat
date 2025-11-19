@echo off
setlocal enabledelayedexpansion

:: Set console color (bright white on purple)
color 5F

echo ============================================
echo   AI Platform - Clean Project
echo ============================================
echo.

:: Store root directory
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

echo [INFO] Project root: %ROOT_DIR%
echo.
echo [INFO] This will remove:
echo   - Python cache files (__pycache__, *.pyc, *.pyo)
echo   - Pytest cache (.pytest_cache)
echo   - Coverage files (.coverage, htmlcov)
echo   - Build directories (build, dist, *.egg-info)
echo   - Temporary files (*.tmp, *.log)
echo   - Virtual environment cache
echo.

:: Confirm action
set /p CONFIRM="Are you sure you want to clean? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo [INFO] Clean cancelled.
    goto :end
)

echo.
echo [INFO] Cleaning Python cache files...

:: Clean __pycache__ directories
for /d /r "%ROOT_DIR%" %%d in (__pycache__) do (
    if exist "%%d" (
        echo Removing: %%d
        rd /s /q "%%d" 2>nul
    )
)

:: Clean .pyc and .pyo files
for /r "%ROOT_DIR%" %%f in (*.pyc *.pyo) do (
    if exist "%%f" (
        echo Removing: %%f
        del /f /q "%%f" 2>nul
    )
)

echo.
echo [INFO] Cleaning pytest cache...

:: Clean .pytest_cache directories
for /d /r "%ROOT_DIR%" %%d in (.pytest_cache) do (
    if exist "%%d" (
        echo Removing: %%d
        rd /s /q "%%d" 2>nul
    )
)

echo.
echo [INFO] Cleaning coverage files...

:: Clean coverage files
for /r "%ROOT_DIR%" %%f in (.coverage) do (
    if exist "%%f" (
        echo Removing: %%f
        del /f /q "%%f" 2>nul
    )
)

:: Clean htmlcov directories
for /d /r "%ROOT_DIR%" %%d in (htmlcov) do (
    if exist "%%d" (
        echo Removing: %%d
        rd /s /q "%%d" 2>nul
    )
)

echo.
echo [INFO] Cleaning build directories...

:: Clean build directories
for /d /r "%ROOT_DIR%" %%d in (build dist) do (
    if exist "%%d" (
        echo Removing: %%d
        rd /s /q "%%d" 2>nul
    )
)

:: Clean egg-info directories
for /d /r "%ROOT_DIR%" %%d in (*.egg-info) do (
    if exist "%%d" (
        echo Removing: %%d
        rd /s /q "%%d" 2>nul
    )
)

echo.
echo [INFO] Cleaning temporary files...

:: Clean temporary files
for /r "%ROOT_DIR%" %%f in (*.tmp *.temp) do (
    if exist "%%f" (
        echo Removing: %%f
        del /f /q "%%f" 2>nul
    )
)

echo.
echo [INFO] Cleaning mypy cache...

:: Clean .mypy_cache directories
for /d /r "%ROOT_DIR%" %%d in (.mypy_cache) do (
    if exist "%%d" (
        echo Removing: %%d
        rd /s /q "%%d" 2>nul
    )
)

echo.
echo [INFO] Cleaning ruff cache...

:: Clean .ruff_cache directories
for /d /r "%ROOT_DIR%" %%d in (.ruff_cache) do (
    if exist "%%d" (
        echo Removing: %%d
        rd /s /q "%%d" 2>nul
    )
)

echo.
color 2F
echo ============================================
echo   Clean completed successfully!
echo ============================================

:end
echo.
pause
endlocal
