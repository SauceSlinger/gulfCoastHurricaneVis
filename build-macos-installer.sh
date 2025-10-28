#!/bin/bash
# Build macOS installer (.dmg with installation script)

set -e

echo "🏗️  Building macOS Installer..."
echo ""

# Variables
INSTALLER_NAME="hurricane-vis-macos-installer.zip"
TEMP_BUILD="/tmp/hurricane-vis-macos-$$"
APP_NAME="HurricaneVisualization"

# Cleanup function
cleanup() {
    if [ -d "$TEMP_BUILD" ]; then
        rm -rf "$TEMP_BUILD"
    fi
}
trap cleanup EXIT

# Create temporary build directory
mkdir -p "$TEMP_BUILD/$APP_NAME"

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
    "$TEMP_BUILD/$APP_NAME/" 2>/dev/null || true

# Copy directories
for dir in database docs .github; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "$TEMP_BUILD/$APP_NAME/"
    fi
done

# Exclude unnecessary files
rm -rf "$TEMP_BUILD/$APP_NAME"/.venv
rm -rf "$TEMP_BUILD/$APP_NAME"/__pycache__
rm -rf "$TEMP_BUILD/$APP_NAME"/.git
rm -rf "$TEMP_BUILD/$APP_NAME"/deprecated
rm -rf "$TEMP_BUILD/$APP_NAME"/*.db
rm -rf "$TEMP_BUILD/$APP_NAME"/*.log

echo "📝 Creating macOS installer scripts..."

# Create installation script
cat > "$TEMP_BUILD/$APP_NAME/install.sh" << 'EOF'
#!/bin/bash
# Hurricane Visualization Dashboard - macOS Installer

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "BANNER"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║      🌀 Gulf Coast Hurricane Visualization Dashboard 🌀      ║
║                                                               ║
║                    macOS Installer                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
BANNER
echo -e "${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check Docker Desktop
if ! command_exists docker; then
    echo -e "${YELLOW}⚠️  Docker Desktop is not installed${NC}"
    echo ""
    echo "Docker Desktop is required for this application."
    echo ""
    echo "Please install Docker Desktop for Mac:"
    echo "  1. Visit: https://www.docker.com/products/docker-desktop/"
    echo "  2. Download Docker Desktop for Mac (Apple Silicon or Intel)"
    echo "  3. Install by dragging to Applications folder"
    echo "  4. Open Docker Desktop and complete setup"
    echo "  5. Run this installer again"
    echo ""
    
    read -p "$(echo -e ${YELLOW}Would you like to open the download page now? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "https://www.docker.com/products/docker-desktop/"
    fi
    exit 1
else
    echo -e "${GREEN}✅ Docker Desktop is installed${NC}"
    
    # Check if Docker is running
    if ! docker ps &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker Desktop is not running${NC}"
        echo -e "${BLUE}Starting Docker Desktop...${NC}"
        open -a Docker
        echo "Waiting for Docker to start (this may take 30-60 seconds)..."
        
        # Wait for Docker to be ready
        for i in {1..30}; do
            if docker ps &> /dev/null; then
                echo -e "${GREEN}✅ Docker is now running${NC}"
                break
            fi
            sleep 2
            echo -n "."
        done
        echo ""
    fi
fi

# Check Python 3
if ! command_exists python3; then
    echo -e "${YELLOW}⚠️  Python 3 is not installed${NC}"
    echo ""
    echo "Python 3 is required for this application."
    echo ""
    echo "Please install Python 3:"
    echo "  1. Visit: https://www.python.org/downloads/macos/"
    echo "  2. Download Python 3.12 for macOS"
    echo "  3. Install and run this installer again"
    echo ""
    
    read -p "$(echo -e ${YELLOW}Would you like to open the download page now? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "https://www.python.org/downloads/macos/"
    fi
    exit 1
else
    echo -e "${GREEN}✅ Python 3 is installed${NC}"
fi

# Installation directory
INSTALL_DIR="$HOME/Applications/HurricaneVisualization"

echo ""
echo -e "${BLUE}📁 Installation directory: $INSTALL_DIR${NC}"

# Create installation directory
if [ -d "$INSTALL_DIR" ]; then
    read -p "$(echo -e ${YELLOW}Installation directory exists. Overwrite? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"

# Copy files
echo -e "${BLUE}📦 Installing application files...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp -R "$SCRIPT_DIR"/* "$INSTALL_DIR/"
rm -f "$INSTALL_DIR/install.sh"

# Make scripts executable
chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true
chmod +x "$INSTALL_DIR"/*.py 2>/dev/null || true

# Create application wrapper
echo -e "${BLUE}🖥️  Creating application launcher...${NC}"

cat > "$INSTALL_DIR/Hurricane Visualization.command" << 'LAUNCHER_EOF'
#!/bin/bash
cd "$(dirname "$0")"
./run-macos.sh
LAUNCHER_EOF
chmod +x "$INSTALL_DIR/Hurricane Visualization.command"

# Create desktop shortcut (alias)
if [ -d "$HOME/Desktop" ]; then
    ln -sf "$INSTALL_DIR/Hurricane Visualization.command" "$HOME/Desktop/Hurricane Visualization"
fi

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                     Installation Summary                     ║${NC}"
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}📍 Location:${NC} $INSTALL_DIR"
echo -e "${BLUE}🖥️  Desktop Alias:${NC} Created"
echo ""
echo -e "${YELLOW}📖 To launch:${NC}"
echo -e "   • Double-click 'Hurricane Visualization' on Desktop"
echo -e "   • Or open: $INSTALL_DIR/Hurricane Visualization.command"
echo ""
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

read -p "$(echo -e ${YELLOW}Would you like to launch the application now? [y/N]: ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 Launching Hurricane Visualization Dashboard...${NC}"
    cd "$INSTALL_DIR"
    ./run-macos.sh &
    echo -e "${GREEN}✅ Application launched!${NC}"
fi

echo -e "${BLUE}Thank you for installing Hurricane Visualization Dashboard!${NC}"
EOF
chmod +x "$TEMP_BUILD/$APP_NAME/install.sh"

# Create launcher script
cat > "$TEMP_BUILD/$APP_NAME/run-macos.sh" << 'EOF'
#!/bin/bash
# Hurricane Visualization Dashboard - macOS Launcher

echo "🌀 Hurricane Visualization Dashboard"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker Desktop is not running"
    echo "   Starting Docker Desktop..."
    open -a Docker
    echo "   Waiting for Docker to start..."
    
    for i in {1..30}; do
        if docker ps &> /dev/null; then
            echo "✅ Docker is running"
            break
        fi
        sleep 2
    done
fi

# Ask for runtime mode
echo "Select runtime mode:"
echo "  1. Docker (Recommended)"
echo "  2. Local Python"
echo ""
read -p "Enter choice (1 or 2): " mode

if [ "$mode" = "1" ]; then
    echo ""
    echo "🐳 Launching with Docker..."
    echo ""
    
    # Build and run with Docker Compose
    docker-compose build
    docker-compose up
    
else
    echo ""
    echo "🐍 Launching with Python..."
    echo ""
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    if [ ! -f ".venv/.dependencies_installed" ]; then
        echo "Installing dependencies (this may take a few minutes)..."
        pip install --upgrade pip
        pip install -r requirements.txt
        touch .venv/.dependencies_installed
    fi
    
    # Launch application
    python3 launch_with_loading.py
fi

echo ""
echo "✅ Application closed"
EOF
chmod +x "$TEMP_BUILD/$APP_NAME/run-macos.sh"

# Create macOS README
cat > "$TEMP_BUILD/$APP_NAME/MACOS_INSTALL.md" << 'EOF'
# Hurricane Visualization Dashboard - macOS Installation

## Prerequisites

1. **Docker Desktop for Mac**
   - Download: https://www.docker.com/products/docker-desktop/
   - Choose: Apple Silicon (M1/M2/M3) or Intel
   - Install by dragging to Applications folder
   - Open Docker Desktop and complete initial setup

2. **Python 3.8+** (Usually pre-installed on macOS)
   - Check: `python3 --version` in Terminal
   - If needed, download from: https://www.python.org/downloads/macos/

## Installation

### Option 1: Graphical Install
1. Extract the downloaded .zip file
2. Open the extracted folder
3. Double-click `install.sh`
4. Follow the prompts

### Option 2: Terminal Install
1. Extract the .zip file
2. Open Terminal
3. Navigate to the extracted folder:
   ```bash
   cd ~/Downloads/HurricaneVisualization
   ```
4. Run the installer:
   ```bash
   ./install.sh
   ```

## Running the Application

After installation:
- **Desktop**: Double-click "Hurricane Visualization" alias on Desktop
- **Applications**: Navigate to ~/Applications/HurricaneVisualization/
- **Manual**: Run `Hurricane Visualization.command`

## Troubleshooting

### "Docker is not running"
- Make sure Docker Desktop app is running
- Look for Docker icon in menu bar
- Wait ~30 seconds after starting Docker Desktop

### "Permission denied"
```bash
chmod +x install.sh
./install.sh
```

### "Python3 not found"
- macOS 10.15+ includes Python 3
- Or install from: https://www.python.org/downloads/macos/

### XQuartz (if GUI doesn't appear)
Some systems may need XQuartz for X11 display:
1. Install XQuartz: https://www.xquartz.org/
2. Log out and back in
3. Run the application again

## Uninstallation

1. Delete desktop alias: `~/Desktop/Hurricane Visualization`
2. Delete application folder: `~/Applications/HurricaneVisualization`
3. (Optional) Uninstall Docker Desktop from Applications

## Apple Silicon (M1/M2/M3) Notes

- Use Docker Desktop for Apple Silicon
- Python native ARM support available
- Performance is excellent on Apple Silicon

## Support

- GitHub: https://github.com/SauceSlinger/gulfCoastHurricaneVis
- Issues: https://github.com/SauceSlinger/gulfCoastHurricaneVis/issues
EOF

echo "📝 Creating archive..."
cd "$TEMP_BUILD"
zip -r "../$INSTALLER_NAME" "$APP_NAME"
cd - > /dev/null
mv "/tmp/$INSTALLER_NAME" .

# Get file size
SIZE=$(du -h "$INSTALLER_NAME" | cut -f1)

echo ""
echo "✅ macOS installer created successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Package: $INSTALLER_NAME"
echo "📏 Size: $SIZE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 macOS Installation Instructions:"
echo "   1. Extract the .zip file"
echo "   2. Double-click 'install.sh' in the folder"
echo "   3. Or run in Terminal: ./install.sh"
echo ""
echo "📋 Prerequisites for macOS users:"
echo "   • Docker Desktop: https://www.docker.com/products/docker-desktop/"
echo "   • Python 3 (usually pre-installed on macOS)"
echo ""
echo "🍎 Compatible with:"
echo "   • Intel Macs"
echo "   • Apple Silicon (M1/M2/M3)"
echo ""
