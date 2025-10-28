# 📦 Installation Guide

This guide explains how to build and distribute installation packages for the Gulf Coast Hurricane Visualization Dashboard.

## 🎯 Available Package Formats

### 1. Self-Extracting Installer (.run file) - **Recommended for Easy Distribution**

A single executable file that contains everything needed and installs itself.

**Advantages:**
- ✅ Single file to distribute
- ✅ No package manager required
- ✅ Works on any Linux distribution
- ✅ Automatically installs dependencies
- ✅ Creates desktop entry
- ✅ Interactive installation

**Build Command:**
```bash
./build-installer.sh
```

**Output:** `hurricane-vis-installer.run`

**User Installation:**
```bash
chmod +x hurricane-vis-installer.run
./hurricane-vis-installer.run
```

---

### 2. Debian Package (.deb file) - **Recommended for Linux Mint/Ubuntu/Debian**

Traditional Debian package for system-wide installation.

**Advantages:**
- ✅ Integrated with package manager
- ✅ Easy updates and removal
- ✅ Dependency management
- ✅ System-wide installation
- ✅ Professional deployment

**Build Command:**
```bash
./build-deb-package.sh
```

**Output:** `gulf-coast-hurricane-vis_1.0.0_all.deb`

**User Installation:**
```bash
sudo dpkg -i gulf-coast-hurricane-vis_1.0.0_all.deb
sudo apt-get install -f  # Fix dependencies if needed
```

---

## 🏗️ Building Packages

### Prerequisites

**For Self-Extracting Installer:**
- Bash
- tar
- gzip

**For Debian Package:**
- dpkg-deb
- Standard Debian build tools

### Build Process

#### Option 1: Self-Extracting Installer

```bash
# Navigate to project directory
cd /path/to/gulfCoastHurricaneVis

# Build the installer
./build-installer.sh

# Result: hurricane-vis-installer.run (ready to distribute)
```

#### Option 2: Debian Package

```bash
# Navigate to project directory
cd /path/to/gulfCoastHurricaneVis

# Build the package
./build-deb-package.sh

# Result: gulf-coast-hurricane-vis_1.0.0_all.deb (ready to distribute)
```

---

## 📤 Distribution

### Hosting Options

1. **GitHub Releases**
   ```bash
   # Upload to GitHub Releases page
   # https://github.com/SauceSlinger/gulfCoastHurricaneVis/releases/new
   ```

2. **Direct Download**
   - Host on your web server
   - Share via cloud storage (Google Drive, Dropbox, etc.)

3. **PPA (Personal Package Archive)** - For .deb packages
   - Create a Launchpad PPA
   - Users can add it with `add-apt-repository`

---

## 👥 User Installation Instructions

### Method 1: Self-Extracting Installer

**Step 1: Download**
```bash
wget https://github.com/SauceSlinger/gulfCoastHurricaneVis/releases/download/v1.0.0/hurricane-vis-installer.run
```

**Step 2: Make Executable**
```bash
chmod +x hurricane-vis-installer.run
```

**Step 3: Run Installer**
```bash
./hurricane-vis-installer.run
```

**Step 4: Follow Prompts**
- The installer will check for Docker and Python
- Install missing dependencies (requires sudo)
- Extract files to `~/.local/share/gulfCoastHurricaneVis`
- Create desktop entry
- Optionally launch the application

**Step 5: Launch**
```bash
# From terminal
~/.local/share/gulfCoastHurricaneVis/run-local.sh

# Or search "Hurricane Visualization" in application menu
```

---

### Method 2: Debian Package

**Step 1: Download**
```bash
wget https://github.com/SauceSlinger/gulfCoastHurricaneVis/releases/download/v1.0.0/gulf-coast-hurricane-vis_1.0.0_all.deb
```

**Step 2: Install**
```bash
sudo dpkg -i gulf-coast-hurricane-vis_1.0.0_all.deb
sudo apt-get install -f  # Install dependencies
```

**Step 3: Launch**
```bash
# From terminal
hurricane-vis

# Or search "Hurricane Visualization" in application menu
```

**Uninstall:**
```bash
sudo apt-get remove gulf-coast-hurricane-vis
```

---

## 🔍 What Gets Installed

### Self-Extracting Installer

**Files:**
- Application: `~/.local/share/gulfCoastHurricaneVis/`
- Desktop Entry: `~/.local/share/applications/gulf-coast-hurricane-vis.desktop`

**Launcher Script:**
- `run-local.sh` - Runs with Python or Docker

### Debian Package

**Files:**
- Application: `/opt/gulf-coast-hurricane-vis/`
- Command: `/usr/bin/hurricane-vis`
- Desktop Entry: `/usr/share/applications/gulf-coast-hurricane-vis.desktop`
- Documentation: `/usr/share/doc/gulf-coast-hurricane-vis/`

---

## ⚙️ Runtime Options

Both installers support two runtime modes:

### Docker Mode (Recommended)
- Requires Docker installed
- Fully containerized environment
- Consistent across all systems
- Run with: `./run-docker.sh`

### Local Python Mode
- Requires Python 3.8+
- Creates virtual environment automatically
- Installs dependencies on first run
- Run with: `./run-local.sh` or `hurricane-vis`

---

## 🐛 Troubleshooting

### Installer Issues

**"Docker not found"**
- Installer will attempt to install Docker
- Requires sudo access
- Log out and back in after installation

**"Permission denied"**
```bash
chmod +x hurricane-vis-installer.run
# Or for .deb:
ls -l gulf-coast-hurricane-vis_*.deb
```

**"Failed to extract"**
- Check available disk space
- Ensure /tmp has write permissions

### Runtime Issues

**"Cannot connect to Docker daemon"**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

**"Module not found"**
```bash
# For local Python mode, reinstall dependencies
cd ~/.local/share/gulfCoastHurricaneVis
rm -rf .venv
./run-local.sh  # Will recreate environment
```

---

## 📊 Package Sizes

Approximate sizes:
- **Self-extracting installer:** ~5-10 MB (compressed)
- **Debian package:** ~5-10 MB
- **After installation:** ~100-200 MB (with dependencies)

---

## 🔄 Updates

### Self-Extracting Installer
- Download new version
- Run installer (will overwrite existing installation)

### Debian Package
- Download new .deb file
- Install with `sudo dpkg -i gulf-coast-hurricane-vis_X.X.X_all.deb`
- Or add to PPA for automatic updates

---

## 📝 Customization

### Modify Installation Location

**Self-Extracting Installer:**
Edit `create-installer.sh`:
```bash
INSTALL_DIR="/your/custom/path"
```

**Debian Package:**
Edit `build-deb-package.sh`:
```bash
# Change package directory structure
mkdir -p "$PACKAGE_DIR/your/custom/path"
```

### Change Package Version

Edit `build-deb-package.sh`:
```bash
VERSION="1.0.1"  # Update version number
```

---

## 🎉 Ready to Distribute!

After building, you'll have:
- ✅ Professional installation package
- ✅ Desktop integration
- ✅ Automatic dependency management
- ✅ User-friendly installation process
- ✅ Support for both Docker and local Python

Share your package and make hurricane data analysis accessible to everyone! 🌀
