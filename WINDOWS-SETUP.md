# AI Platform - Windows 11 Setup Guide

This guide provides detailed instructions for setting up the AI Platform development environment on Windows 11.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step-by-Step Installation](#step-by-step-installation)
- [Docker Desktop Configuration](#docker-desktop-configuration)
- [WSL2 Memory Configuration](#wsl2-memory-configuration)
- [Quick Start](#quick-start)
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Performance Optimization](#performance-optimization)
- [Useful Commands](#useful-commands)

## Prerequisites

### Required Software

| Software | Minimum Version | Download Link |
|----------|----------------|---------------|
| Windows 11 | 21H2 or later | Built-in |
| Python | 3.9+ | [python.org](https://www.python.org/downloads/windows/) |
| Docker Desktop | 4.0+ | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Git | 2.30+ | [git-scm.com](https://git-scm.com/download/win) |
| Visual Studio Code | Latest | [code.visualstudio.com](https://code.visualstudio.com/) |
| Windows Terminal | Latest | [Microsoft Store](https://aka.ms/terminal) |

### System Requirements

- **CPU**: 64-bit processor with virtualization support (Intel VT-x or AMD-V)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 20GB free disk space minimum (50GB recommended)
- **OS**: Windows 11 Pro, Enterprise, or Education (for Hyper-V)

## Step-by-Step Installation

### Step 1: Enable Windows Features

Open PowerShell as Administrator and run:

```powershell
# Enable WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Enable Hyper-V (optional but recommended)
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart
```

Restart your computer after running these commands.

### Step 2: Install WSL2

After restart, open PowerShell as Administrator:

```powershell
# Set WSL2 as default
wsl --set-default-version 2

# Install Ubuntu (or your preferred distribution)
wsl --install -d Ubuntu

# Update WSL
wsl --update
```

### Step 3: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/windows/)
2. Run the installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:

```powershell
python --version
pip --version
```

### Step 4: Install Git

1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Run the installer with default options
3. Configure Git:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global core.autocrlf true
```

### Step 5: Install Docker Desktop

1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Run the installer
3. **Important**: Ensure "Use WSL 2 instead of Hyper-V" is checked
4. Restart your computer
5. Start Docker Desktop
6. Accept the service agreement
7. Verify installation:

```powershell
docker --version
docker compose version
```

### Step 6: Clone the Repository

```powershell
cd C:\Projects  # or your preferred directory
git clone https://github.com/your-org/AI-Platform-Project-.git
cd AI-Platform-Project-
```

### Step 7: Run Validation

```powershell
.\scripts\validate-windows.ps1
```

## Docker Desktop Configuration

### General Settings

1. Open Docker Desktop Settings (gear icon)
2. Under **General**:
   - Enable "Start Docker Desktop when you log in"
   - Enable "Use the WSL 2 based engine"

### Resources Settings

1. Go to **Resources** > **WSL Integration**
2. Enable integration with your default WSL distro
3. Go to **Resources** > **Advanced**:
   - CPUs: At least 2 (4+ recommended)
   - Memory: At least 4GB (8GB+ recommended)
   - Swap: 1GB
   - Disk image size: 60GB minimum

### Network Settings

1. Go to **Resources** > **Network**
2. Enable "Use kernel networking for UDP"
3. Docker subnet: Keep default unless conflicts exist

## WSL2 Memory Configuration

Create or edit `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
# Limits VM memory to 4GB
memory=4GB

# Sets the VM to use 2 virtual processors
processors=2

# Sets amount of swap storage space
swap=2GB

# Sets swapfile path location
swapFile=C:\\temp\\wsl-swap.vhdx

# Turns on default connection to bind WSL 2 localhost to Windows localhost
localhostForwarding=true

# Boolean specifying if ports bound to wildcard or localhost in the WSL 2 VM should be connectable from the host
nestedVirtualization=true
```

After editing, restart WSL:

```powershell
wsl --shutdown
```

## Quick Start

Once all prerequisites are installed, run the quick start script:

```powershell
# Navigate to project directory
cd C:\Projects\AI-Platform-Project-

# Run quick start
.\scripts\quick-start-windows.ps1
```

This script will:
1. Validate your environment
2. Install Python dependencies
3. Create `.env` files from examples
4. Start Docker services
5. Display access URLs

## Common Issues and Solutions

### Issue: Docker Desktop Won't Start

**Symptoms**: Docker Desktop hangs or shows error on startup

**Solutions**:
1. Run the troubleshooter:
   ```powershell
   .\scripts\troubleshoot-windows.ps1 -Action ResetDocker
   ```
2. Check Hyper-V is enabled
3. Ensure BIOS virtualization is enabled
4. Reset Docker to factory settings

### Issue: WSL2 Backend Failed

**Symptoms**: Error "WSL 2 installation is incomplete"

**Solutions**:
1. Download and install the [WSL2 Linux kernel update](https://aka.ms/wsl2kernel)
2. Run:
   ```powershell
   wsl --set-default-version 2
   ```

### Issue: Port Already in Use

**Symptoms**: Error "port is already allocated"

**Solutions**:
1. Find the process using the port:
   ```powershell
   netstat -ano | findstr :PORT_NUMBER
   ```
2. Kill the process:
   ```powershell
   taskkill /PID PROCESS_ID /F
   ```
3. Or change the port in docker-compose.yml

### Issue: Slow File System Performance

**Symptoms**: Very slow builds or file operations

**Solutions**:
1. Store project files in WSL filesystem instead of Windows:
   ```powershell
   # Access WSL filesystem
   cd \\wsl$\Ubuntu\home\username
   ```
2. Add exclusions to Windows Defender:
   - Open Windows Security
   - Virus & threat protection > Manage settings
   - Add exclusion for project directory

### Issue: Python Not Found

**Symptoms**: 'python' is not recognized as a command

**Solutions**:
1. Reinstall Python with "Add to PATH" checked
2. Manually add Python to PATH:
   ```powershell
   $env:Path += ";C:\Users\YourUser\AppData\Local\Programs\Python\Python39"
   $env:Path += ";C:\Users\YourUser\AppData\Local\Programs\Python\Python39\Scripts"
   ```

### Issue: Permission Denied Errors

**Symptoms**: Cannot create files or access directories

**Solutions**:
1. Run PowerShell as Administrator
2. Fix permissions:
   ```powershell
   .\scripts\troubleshoot-windows.ps1 -Action FixPermissions
   ```

### Issue: Docker Compose Services Fail to Start

**Symptoms**: Services exit immediately or fail health checks

**Solutions**:
1. Check logs:
   ```powershell
   docker compose logs SERVICE_NAME
   ```
2. Ensure all required ports are available
3. Check `.env` files are properly configured
4. Increase Docker memory allocation

### Issue: Git Line Ending Warnings

**Symptoms**: Warnings about CRLF being replaced by LF

**Solutions**:
1. Configure Git:
   ```powershell
   git config --global core.autocrlf true
   ```
2. Add `.gitattributes` file:
   ```
   * text=auto eol=lf
   *.{cmd,[cC][mM][dD]} text eol=crlf
   *.{bat,[bB][aA][tT]} text eol=crlf
   ```

## Performance Optimization

### 1. Use WSL2 Filesystem

Store your project in the WSL2 filesystem for better I/O performance:

```bash
# In WSL terminal
cd /home/username
git clone https://github.com/your-org/AI-Platform-Project-.git
```

Access from Windows:
```
\\wsl$\Ubuntu\home\username\AI-Platform-Project-
```

### 2. Configure Windows Defender Exclusions

Add exclusions for:
- Project directory
- Python installation directory
- Docker data directory
- Node modules (if applicable)

```powershell
# Run as Administrator
Add-MpPreference -ExclusionPath "C:\Projects\AI-Platform-Project-"
Add-MpPreference -ExclusionPath "C:\Users\YourUser\AppData\Local\Programs\Python"
Add-MpPreference -ExclusionProcess "python.exe"
Add-MpPreference -ExclusionProcess "docker.exe"
```

### 3. Optimize Docker

1. Enable BuildKit:
   ```powershell
   $env:DOCKER_BUILDKIT = 1
   ```

2. Use build cache:
   ```yaml
   # In docker-compose.yml
   services:
     app:
       build:
         cache_from:
           - app:latest
   ```

3. Prune unused resources regularly:
   ```powershell
   docker system prune -af --volumes
   ```

### 4. Use Windows Terminal

Windows Terminal provides better performance than CMD or PowerShell ISE:
- Install from Microsoft Store
- Configure with profile for your project
- Use split panes for multiple terminals

### 5. Allocate Appropriate Resources

Based on your system:
- 8GB RAM system: 3-4GB for Docker
- 16GB RAM system: 6-8GB for Docker
- 32GB+ RAM system: 12-16GB for Docker

## Useful Commands

### Docker Commands

```powershell
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f SERVICE_NAME

# Restart a service
docker compose restart SERVICE_NAME

# Rebuild and start
docker compose up -d --build

# Remove all containers and volumes
docker compose down -v

# Check resource usage
docker stats
```

### PowerShell Scripts

```powershell
# Validate environment
.\scripts\validate-windows.ps1

# Check service health
.\scripts\health-check.ps1

# Run integration tests
.\scripts\run-integration-tests.ps1

# Quick start
.\scripts\quick-start-windows.ps1

# Troubleshooting menu
.\scripts\troubleshoot-windows.ps1
```

### Git Commands

```powershell
# Check status
git status

# Pull latest changes
git pull origin main

# Create feature branch
git checkout -b feature/your-feature

# Commit changes
git add .
git commit -m "feat: your message"

# Push changes
git push origin feature/your-feature
```

### Python Commands

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .

# Type checking
mypy .
```

## Getting Help

If you encounter issues not covered in this guide:

1. Run the troubleshooting script:
   ```powershell
   .\scripts\troubleshoot-windows.ps1
   ```

2. Check the Docker logs:
   ```powershell
   docker compose logs
   ```

3. Review the main [CLAUDE.md](CLAUDE.md) documentation

4. Search existing GitHub issues

5. Create a new issue with:
   - Windows version (`winver`)
   - Docker version (`docker --version`)
   - Python version (`python --version`)
   - Error message and stack trace
   - Steps to reproduce

## Next Steps

After completing the setup:

1. Read the [CLAUDE.md](CLAUDE.md) for project overview
2. Explore the module specifications
3. Start with Module 1 (User Gateway)
4. Run the integration tests to verify setup
5. Begin development!

---

**Document Version**: 1.0.0
**Last Updated**: 2024-01-15
**Maintained By**: AI Platform Development Team
