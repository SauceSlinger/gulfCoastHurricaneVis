#!/bin/bash
# Build script for creating self-extracting installer

set -e

echo "🏗️  Building Gulf Coast Hurricane Visualization Installer..."
echo ""

# Variables
INSTALLER_NAME="hurricane-vis-installer.run"
TEMP_BUILD="/tmp/hurricane-vis-build-$$"

# Cleanup function
cleanup() {
    if [ -d "$TEMP_BUILD" ]; then
        rm -rf "$TEMP_BUILD"
    fi
}
trap cleanup EXIT

# Create temporary build directory
mkdir -p "$TEMP_BUILD"

echo "📦 Copying application files..."

# Copy essential files
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
    "$TEMP_BUILD/" 2>/dev/null || true

# Copy directories
for dir in database docs .github; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "$TEMP_BUILD/"
    fi
done

# Exclude unnecessary files
rm -rf "$TEMP_BUILD"/.venv
rm -rf "$TEMP_BUILD"/__pycache__
rm -rf "$TEMP_BUILD"/.git
rm -rf "$TEMP_BUILD"/deprecated
rm -rf "$TEMP_BUILD"/*.db
rm -rf "$TEMP_BUILD"/*.log
rm -f "$TEMP_BUILD"/create-installer.sh
rm -f "$TEMP_BUILD"/build-installer.sh

echo "📝 Creating archive..."
cd "$TEMP_BUILD"
tar czf ../archive.tar.gz .
cd - > /dev/null

echo "🔨 Building self-extracting installer..."
cat create-installer.sh /tmp/archive.tar.gz > "$INSTALLER_NAME"
chmod +x "$INSTALLER_NAME"

# Cleanup temp archive
rm -f /tmp/archive.tar.gz

# Get file size
SIZE=$(du -h "$INSTALLER_NAME" | cut -f1)

echo ""
echo "✅ Installer created successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Installer: $INSTALLER_NAME"
echo "📏 Size: $SIZE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 To distribute:"
echo "   1. Share $INSTALLER_NAME with users"
echo "   2. Users run: chmod +x $INSTALLER_NAME && ./$INSTALLER_NAME"
echo ""
echo "📋 The installer will:"
echo "   ✓ Check and install Docker (if needed)"
echo "   ✓ Check and install Python 3 (if needed)"
echo "   ✓ Extract application files"
echo "   ✓ Create desktop entry"
echo "   ✓ Set up launcher scripts"
echo ""
