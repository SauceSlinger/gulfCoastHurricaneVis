#!/bin/bash
# Gulf Coast Hurricane Visualization Dashboard - Self-Extracting Installer
# This is a self-extracting archive. Run it to install and launch the application.

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║      🌀 Gulf Coast Hurricane Visualization Dashboard 🌀      ║
║                                                               ║
║                  Self-Extracting Installer                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Variables
INSTALL_DIR="$HOME/.local/share/gulfCoastHurricaneVis"
DESKTOP_FILE="$HOME/.local/share/applications/gulf-coast-hurricane-vis.desktop"
ICON_FILE="$HOME/.local/share/icons/hurricane-vis.png"
TEMP_EXTRACT="/tmp/hurricane-vis-install-$$"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup on exit
cleanup() {
    if [ -d "$TEMP_EXTRACT" ]; then
        rm -rf "$TEMP_EXTRACT"
    fi
}
trap cleanup EXIT

echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check if Docker is installed
if ! command_exists docker; then
    echo -e "${YELLOW}⚠️  Docker is not installed.${NC}"
    echo -e "${BLUE}Installing Docker...${NC}"
    
    # Detect if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}This script needs sudo access to install Docker.${NC}"
        sudo apt-get update
        sudo apt-get install -y docker.io docker-compose
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker $USER
        echo -e "${GREEN}✅ Docker installed successfully${NC}"
        echo -e "${YELLOW}⚠️  You'll need to log out and back in for Docker permissions to take effect.${NC}"
    else
        apt-get update
        apt-get install -y docker.io docker-compose
        systemctl start docker
        systemctl enable docker
    fi
else
    echo -e "${GREEN}✅ Docker is already installed${NC}"
fi

# Check if Python 3 is installed
if ! command_exists python3; then
    echo -e "${YELLOW}⚠️  Python 3 is not installed.${NC}"
    if [ "$EUID" -ne 0 ]; then
        sudo apt-get install -y python3 python3-pip python3-venv
    else
        apt-get install -y python3 python3-pip python3-venv
    fi
    echo -e "${GREEN}✅ Python 3 installed${NC}"
else
    echo -e "${GREEN}✅ Python 3 is already installed${NC}"
fi

# Extract archive
echo -e "${BLUE}📦 Extracting application files...${NC}"
ARCHIVE_LINE=$(awk '/^__ARCHIVE_BELOW__/ {print NR + 1; exit 0; }' "$0")
mkdir -p "$TEMP_EXTRACT"
tail -n +$ARCHIVE_LINE "$0" | tar xzf - -C "$TEMP_EXTRACT"

# Create installation directory
echo -e "${BLUE}📁 Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
cp -r "$TEMP_EXTRACT"/* "$INSTALL_DIR/"

# Create desktop entry
echo -e "${BLUE}🖥️  Creating desktop entry...${NC}"
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Hurricane Visualization Dashboard
Comment=Interactive Gulf Coast Hurricane Data Analysis
Exec=$INSTALL_DIR/run-local.sh
Icon=weather-storm
Terminal=false
Categories=Science;Education;DataVisualization;
Keywords=hurricane;weather;visualization;data;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"

# Create launcher script
cat > "$INSTALL_DIR/run-local.sh" << 'LAUNCHER_EOF'
#!/bin/bash
cd "$(dirname "$0")"

# Check if running with Docker or local Python
if command -v docker >/dev/null 2>&1 && [ -f "Dockerfile" ]; then
    echo "🐳 Launching with Docker..."
    ./run-docker.sh
else
    echo "🐍 Launching with local Python..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    if [ ! -f ".venv/.dependencies_installed" ]; then
        echo "Installing dependencies..."
        pip install --upgrade pip
        pip install -r requirements.txt
        touch .venv/.dependencies_installed
    fi
    
    # Launch application
    python3 launch_with_loading.py
fi
LAUNCHER_EOF
chmod +x "$INSTALL_DIR/run-local.sh"

# Make other scripts executable
chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true
chmod +x "$INSTALL_DIR"/*.py 2>/dev/null || true

echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                     Installation Summary                     ║${NC}"
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}📍 Installation Location:${NC} $INSTALL_DIR"
echo -e "${BLUE}🖥️  Desktop Entry:${NC} $DESKTOP_FILE"
echo ""
echo -e "${YELLOW}📖 How to Launch:${NC}"
echo -e "   1. Search for 'Hurricane Visualization' in your application menu"
echo -e "   2. Or run: ${GREEN}$INSTALL_DIR/run-local.sh${NC}"
echo -e "   3. Or run with Docker: ${GREEN}cd $INSTALL_DIR && ./run-docker.sh${NC}"
echo ""
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Ask if user wants to launch now
read -p "$(echo -e ${YELLOW}Would you like to launch the application now? [y/N]: ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 Launching Hurricane Visualization Dashboard...${NC}"
    cd "$INSTALL_DIR"
    ./run-local.sh &
    echo -e "${GREEN}✅ Application launched!${NC}"
fi

echo -e "${BLUE}Thank you for installing Gulf Coast Hurricane Visualization Dashboard!${NC}"
exit 0

__ARCHIVE_BELOW__
