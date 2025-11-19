@echo off
REM Installation script for Core Processing module on Windows
REM This script sets up the Python environment and installs dependencies

echo ==========================================
echo Core Processing Module - Windows Installer
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install PyTorch with CUDA support (optional)
echo.
echo Do you want to install PyTorch with CUDA support? (y/n)
set /p INSTALL_CUDA=
if /i "%INSTALL_CUDA%"=="y" (
    echo Installing PyTorch with CUDA support...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
) else (
    echo Installing PyTorch (CPU only)...
    pip install torch torchvision torchaudio
)

REM Install requirements
echo Installing dependencies from requirements.txt...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found
)

REM Create necessary directories
echo Creating cache directories...
if not exist "%LOCALAPPDATA%\model_cache" mkdir "%LOCALAPPDATA%\model_cache"

REM Create .env file from example if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env file from .env.example...
        copy ".env.example" ".env"
        echo Please edit .env file with your configuration
    )
)

echo.
echo ==========================================
echo Installation completed successfully!
echo ==========================================
echo.
echo To start the service, run: start.bat
echo To activate the environment manually: venv\Scripts\activate.bat
echo.
pause
