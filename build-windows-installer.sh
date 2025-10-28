#!/bin/bash
# Build Windows installer (.zip with PowerShell installer)

set -e

echo "🏗️  Building Windows Installer..."
echo ""

# Variables
INSTALLER_NAME="hurricane-vis-windows-installer.zip"
TEMP_BUILD="/tmp/hurricane-vis-windows-$$"

# Cleanup function
cleanup() {
    if [ -d "$TEMP_BUILD" ]; then
        rm -rf "$TEMP_BUILD"
    fi
}
trap cleanup EXIT

# Create temporary build directory
mkdir -p "$TEMP_BUILD/HurricaneVisualization"

echo "📦 Copying application files..."

# Copy essential files
cp -r \
    *.py \
    *.csv \
    *.md \
    requirements.txt \
    Dockerfile \
    docker-compose.yml \
    .dockerignore \
    LICENSE \
    .flake8 \
    "$TEMP_BUILD/HurricaneVisualization/" 2>/dev/null || true

# Copy directories
for dir in database docs .github; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "$TEMP_BUILD/HurricaneVisualization/"
    fi
done

# Exclude unnecessary files
rm -rf "$TEMP_BUILD/HurricaneVisualization"/.venv
rm -rf "$TEMP_BUILD/HurricaneVisualization"/__pycache__
rm -rf "$TEMP_BUILD/HurricaneVisualization"/.git
rm -rf "$TEMP_BUILD/HurricaneVisualization"/deprecated
rm -rf "$TEMP_BUILD/HurricaneVisualization"/*.db
rm -rf "$TEMP_BUILD/HurricaneVisualization"/*.log

echo "📝 Creating Windows installer scripts..."

# Create PowerShell installer
cat > "$TEMP_BUILD/HurricaneVisualization/install.ps1" << 'EOF'
# Hurricane Visualization Dashboard - Windows Installer
# Run this script in PowerShell as Administrator

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   Hurricane Visualization Dashboard - Installer    " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  Please run PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "   Right-click PowerShell → 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "📋 Checking prerequisites..." -ForegroundColor Blue

# Check Docker Desktop
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  Docker Desktop is not installed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install Docker Desktop for Windows:" -ForegroundColor Yellow
    Write-Host "  1. Visit: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "  2. Download Docker Desktop for Windows" -ForegroundColor White
    Write-Host "  3. Install and restart your computer" -ForegroundColor White
    Write-Host "  4. Run this installer again" -ForegroundColor White
    Write-Host ""
    
    $download = Read-Host "Would you like to open the download page now? (y/N)"
    if ($download -eq "y" -or $download -eq "Y") {
        Start-Process "https://www.docker.com/products/docker-desktop/"
    }
    pause
    exit 1
} else {
    Write-Host "✅ Docker Desktop is installed" -ForegroundColor Green
}

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  Python is not installed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install Python 3.8 or higher:" -ForegroundColor Yellow
    Write-Host "  1. Visit: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "  2. Download Python 3.12 for Windows" -ForegroundColor White
    Write-Host "  3. Install (check 'Add Python to PATH')" -ForegroundColor White
    Write-Host "  4. Run this installer again" -ForegroundColor White
    Write-Host ""
    
    $download = Read-Host "Would you like to open the download page now? (y/N)"
    if ($download -eq "y" -or $download -eq "Y") {
        Start-Process "https://www.python.org/downloads/"
    }
    pause
    exit 1
} else {
    Write-Host "✅ Python is installed" -ForegroundColor Green
}

# Installation directory
$installDir = "$env:LOCALAPPDATA\HurricaneVisualization"
Write-Host ""
Write-Host "📁 Installation directory: $installDir" -ForegroundColor Blue

# Create installation directory
if (Test-Path $installDir) {
    $overwrite = Read-Host "Installation directory exists. Overwrite? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Installation cancelled." -ForegroundColor Yellow
        pause
        exit 0
    }
    Remove-Item -Recurse -Force $installDir
}

New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Copy files
Write-Host "📦 Installing application files..." -ForegroundColor Blue
Copy-Item -Recurse -Force "$PSScriptRoot\*" -Destination $installDir -Exclude "install.ps1","install.bat"

# Create desktop shortcut
Write-Host "🖥️  Creating desktop shortcut..." -ForegroundColor Blue
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Hurricane Visualization.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$installDir\run-windows.ps1`""
$Shortcut.WorkingDirectory = $installDir
$Shortcut.IconLocation = "shell32.dll,13"
$Shortcut.Description = "Gulf Coast Hurricane Visualization Dashboard"
$Shortcut.Save()

# Create start menu shortcut
$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
New-Item -ItemType Directory -Force -Path $startMenuPath | Out-Null
$Shortcut = $WshShell.CreateShortcut("$startMenuPath\Hurricane Visualization.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$installDir\run-windows.ps1`""
$Shortcut.WorkingDirectory = $installDir
$Shortcut.IconLocation = "shell32.dll,13"
$Shortcut.Description = "Gulf Coast Hurricane Visualization Dashboard"
$Shortcut.Save()

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "                 Installation Summary                 " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "📍 Location: $installDir" -ForegroundColor Blue
Write-Host "🖥️  Desktop Shortcut: Created" -ForegroundColor Blue
Write-Host "📋 Start Menu: Created" -ForegroundColor Blue
Write-Host ""
Write-Host "📖 To launch:" -ForegroundColor Yellow
Write-Host "   • Double-click the desktop shortcut" -ForegroundColor White
Write-Host "   • Or search 'Hurricane Visualization' in Start Menu" -ForegroundColor White
Write-Host ""

$launch = Read-Host "Would you like to launch the application now? (y/N)"
if ($launch -eq "y" -or $launch -eq "Y") {
    Write-Host "🚀 Launching Hurricane Visualization Dashboard..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$installDir\run-windows.ps1`""
}

Write-Host ""
Write-Host "Thank you for installing Hurricane Visualization Dashboard!" -ForegroundColor Blue
pause
EOF

# Create launcher script
cat > "$TEMP_BUILD/HurricaneVisualization/run-windows.ps1" << 'EOF'
# Hurricane Visualization Dashboard - Windows Launcher

Write-Host "🌀 Hurricane Visualization Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# Check if Docker Desktop is running
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Docker Desktop is not running" -ForegroundColor Yellow
    Write-Host "   Please start Docker Desktop and try again" -ForegroundColor Yellow
    Write-Host ""
    
    $startDocker = Read-Host "Would you like to start Docker Desktop now? (y/N)"
    if ($startDocker -eq "y" -or $startDocker -eq "Y") {
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        Write-Host "Waiting for Docker to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    } else {
        pause
        exit 1
    }
}

# Check mode preference
Write-Host "Select runtime mode:" -ForegroundColor Blue
Write-Host "  1. Docker (Recommended - Containerized)" -ForegroundColor White
Write-Host "  2. Local Python (Direct execution)" -ForegroundColor White
Write-Host ""
$mode = Read-Host "Enter choice (1 or 2)"

if ($mode -eq "1") {
    Write-Host ""
    Write-Host "🐳 Launching with Docker..." -ForegroundColor Blue
    Write-Host ""
    
    # Build and run with Docker Compose
    docker-compose build
    docker-compose up
    
} else {
    Write-Host ""
    Write-Host "🐍 Launching with Python..." -ForegroundColor Blue
    Write-Host ""
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        python -m venv .venv
    }
    
    # Activate virtual environment
    .\.venv\Scripts\Activate.ps1
    
    # Install dependencies
    if (-not (Test-Path ".venv\.dependencies_installed")) {
        Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        New-Item -ItemType File -Path ".venv\.dependencies_installed" | Out-Null
    }
    
    # Launch application
    python launch_with_loading.py
}

Write-Host ""
Write-Host "✅ Application closed" -ForegroundColor Green
pause
EOF

# Create batch file launcher (for double-click support)
cat > "$TEMP_BUILD/HurricaneVisualization/install.bat" << 'EOF'
@echo off
echo.
echo Starting Hurricane Visualization Installer...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
EOF

cat > "$TEMP_BUILD/HurricaneVisualization/run.bat" << 'EOF'
@echo off
powershell.exe -ExecutionPolicy Bypass -File "%~dp0run-windows.ps1"
EOF

# Create README for Windows
cat > "$TEMP_BUILD/HurricaneVisualization/WINDOWS_INSTALL.md" << 'EOF'
# Hurricane Visualization Dashboard - Windows Installation

## Prerequisites

1. **Docker Desktop** (Recommended)
   - Download: https://www.docker.com/products/docker-desktop/
   - Install and restart your computer
   - Ensure Docker Desktop is running before launching the app

2. **Python 3.8+** (Alternative to Docker)
   - Download: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

## Installation

### Option 1: Easy Install (Recommended)
1. Double-click `install.bat`
2. Follow the prompts
3. Launch from desktop shortcut or Start Menu

### Option 2: PowerShell Install
1. Right-click PowerShell → "Run as Administrator"
2. Navigate to this folder
3. Run: `.\install.ps1`

## Running the Application

After installation:
- **Desktop**: Double-click "Hurricane Visualization" shortcut
- **Start Menu**: Search for "Hurricane Visualization"
- **Manual**: Run `run.bat` in installation folder

## Troubleshooting

**"Docker is not running"**
- Start Docker Desktop before launching the app
- Wait ~30 seconds for Docker to fully start

**"Python not found"**
- Install Python from https://www.python.org/downloads/
- Ensure "Add Python to PATH" was checked during installation
- Restart PowerShell after installation

**"Access Denied"**
- Run PowerShell as Administrator
- Right-click PowerShell → "Run as Administrator"

## Uninstallation

1. Delete desktop and Start Menu shortcuts
2. Delete installation folder:
   - Location: `%LOCALAPPDATA%\HurricaneVisualization`
3. (Optional) Uninstall Docker Desktop from Windows Settings

## Support

GitHub: https://github.com/SauceSlinger/gulfCoastHurricaneVis
Issues: https://github.com/SauceSlinger/gulfCoastHurricaneVis/issues
EOF

echo "📝 Creating archive..."
cd "$TEMP_BUILD"
zip -r "../$INSTALLER_NAME" HurricaneVisualization
cd - > /dev/null
mv "/tmp/$INSTALLER_NAME" .

# Get file size
SIZE=$(du -h "$INSTALLER_NAME" | cut -f1)

echo ""
echo "✅ Windows installer created successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Package: $INSTALLER_NAME"
echo "📏 Size: $SIZE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Windows Installation Instructions:"
echo "   1. Extract the .zip file"
echo "   2. Double-click 'install.bat'"
echo "   3. Follow the installation prompts"
echo ""
echo "📋 Prerequisites for Windows users:"
echo "   • Docker Desktop: https://www.docker.com/products/docker-desktop/"
echo "   • Python 3.8+: https://www.python.org/downloads/"
echo ""
