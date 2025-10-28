#!/bin/bash
# Build .deb package for Debian/Ubuntu/Linux Mint

set -e

echo "🏗️  Building Debian package..."
echo ""

# Variables
PACKAGE_NAME="gulf-coast-hurricane-vis"
VERSION="1.0.0"
ARCHITECTURE="all"
MAINTAINER="SauceSlinger <your-email@example.com>"
BUILD_DIR="build-deb"
PACKAGE_DIR="$BUILD_DIR/${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}"

# Cleanup old build
if [ -d "$BUILD_DIR" ]; then
    rm -rf "$BUILD_DIR"
fi

# Create directory structure
echo "📁 Creating package structure..."
mkdir -p "$PACKAGE_DIR/DEBIAN"
mkdir -p "$PACKAGE_DIR/opt/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR/usr/share/applications"
mkdir -p "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR/usr/bin"

# Create control file
echo "📝 Creating control file..."
cat > "$PACKAGE_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: science
Priority: optional
Architecture: $ARCHITECTURE
Depends: python3 (>= 3.8), python3-pip, python3-venv, docker.io (>= 20.10) | docker-ce (>= 20.10)
Recommends: docker-compose
Maintainer: $MAINTAINER
Description: Gulf Coast Hurricane Visualization Dashboard
 Interactive hurricane visualization dashboard featuring timeline analysis,
 geographic mapping, and statistical insights. Built with Python, CustomTkinter,
 Cartopy, and Docker. Analyze 19,066+ Gulf Coast hurricanes from 1975-2021.
 .
 Features:
  - Overview: Dataset summary with statistics and top storms
  - Timeline: Interactive charts with year/month/category sliders
  - Map: Geographic visualization with storm track filtering
  - Analysis: Statistical breakdowns and trend analysis
Homepage: https://github.com/SauceSlinger/gulfCoastHurricaneVis
EOF

# Create postinst script (run after installation)
echo "📝 Creating post-installation script..."
cat > "$PACKAGE_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "🌀 Configuring Gulf Coast Hurricane Visualization Dashboard..."

# Add user to docker group if Docker is installed
if command -v docker >/dev/null 2>&1; then
    if [ -n "$SUDO_USER" ]; then
        usermod -aG docker "$SUDO_USER" 2>/dev/null || true
        echo "✅ Added user to docker group (logout required for changes to take effect)"
    fi
fi

# Make scripts executable
chmod +x /opt/gulf-coast-hurricane-vis/*.sh 2>/dev/null || true
chmod +x /opt/gulf-coast-hurricane-vis/*.py 2>/dev/null || true
chmod +x /usr/bin/hurricane-vis 2>/dev/null || true

echo "✅ Gulf Coast Hurricane Visualization Dashboard installed successfully!"
echo ""
echo "To launch, run: hurricane-vis"
echo "Or search for 'Hurricane Visualization' in your applications menu"

exit 0
EOF
chmod 755 "$PACKAGE_DIR/DEBIAN/postinst"

# Create postrm script (run after removal)
cat > "$PACKAGE_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

# Remove virtual environment if it exists
rm -rf /opt/gulf-coast-hurricane-vis/.venv 2>/dev/null || true

echo "Gulf Coast Hurricane Visualization Dashboard has been removed."
exit 0
EOF
chmod 755 "$PACKAGE_DIR/DEBIAN/postrm"

# Copy application files
echo "📦 Copying application files..."
cp -r \
    *.py \
    *.sh \
    *.csv \
    *.md \
    requirements.txt \
    Dockerfile \
    docker-compose.yml \
    .dockerignore \
    LICENSE \
    .flake8 \
    "$PACKAGE_DIR/opt/$PACKAGE_NAME/" 2>/dev/null || true

# Copy directories
for dir in database docs .github; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "$PACKAGE_DIR/opt/$PACKAGE_NAME/"
    fi
done

# Create launcher script
cat > "$PACKAGE_DIR/usr/bin/hurricane-vis" << 'EOF'
#!/bin/bash
cd /opt/gulf-coast-hurricane-vis

# Check if running with Docker or local Python
if command -v docker >/dev/null 2>&1 && [ -f "Dockerfile" ]; then
    # Try Docker first
    if groups | grep -q docker || [ "$EUID" -eq 0 ]; then
        echo "🐳 Launching with Docker..."
        ./run-docker.sh
        exit 0
    fi
fi

# Fall back to local Python
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
    echo "Installing dependencies (this may take a few minutes)..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch .venv/.dependencies_installed
fi

# Launch application
python3 launch_with_loading.py
EOF
chmod 755 "$PACKAGE_DIR/usr/bin/hurricane-vis"

# Create desktop entry
cat > "$PACKAGE_DIR/usr/share/applications/$PACKAGE_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Hurricane Visualization Dashboard
GenericName=Hurricane Data Analysis
Comment=Interactive Gulf Coast Hurricane Data Visualization
Exec=/usr/bin/hurricane-vis
Icon=weather-storm
Terminal=false
Categories=Science;Education;DataVisualization;Geography;
Keywords=hurricane;weather;visualization;data;analysis;storm;
StartupNotify=true
EOF

# Copy documentation
cp README.md "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME/"
cp CHANGELOG.md "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME/" 2>/dev/null || true
cp LICENSE "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME/"

# Build the package
echo "🔨 Building .deb package..."
dpkg-deb --build "$PACKAGE_DIR"

# Move to root directory
mv "$PACKAGE_DIR.deb" .

# Get file size
SIZE=$(du -h "${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb" | cut -f1)

echo ""
echo "✅ Debian package created successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Package: ${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
echo "📏 Size: $SIZE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 To install:"
echo "   sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
echo "   sudo apt-get install -f  # Fix dependencies if needed"
echo ""
echo "📋 After installation:"
echo "   ✓ Run: hurricane-vis"
echo "   ✓ Or search 'Hurricane Visualization' in application menu"
echo ""
echo "🗑️  To uninstall:"
echo "   sudo apt-get remove $PACKAGE_NAME"
echo ""
