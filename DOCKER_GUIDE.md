# 🐳 Docker Quick Start Guide

This guide will help you run the Gulf Coast Hurricane Visualization Dashboard using Docker.

## Prerequisites

- **Docker**: Install from [docker.com](https://docs.docker.com/get-docker/)
- **Docker Compose**: Usually included with Docker Desktop
- **X11 Server**: 
  - Linux: Already installed
  - macOS: Install [XQuartz](https://www.xquartz.org/)
  - Windows: Install [VcXsrv](https://sourceforge.net/projects/vcxsrv/)

## Quick Start (Linux)

### One-Command Launch

```bash
./run-docker.sh
```

That's it! The script will:
1. ✅ Configure X11 display access
2. ✅ Build the Docker image
3. ✅ Start the application
4. ✅ Clean up on exit

### Manual Docker Commands

```bash
# Allow Docker to access your display
xhost +local:docker

# Build the image
docker-compose build

# Run the dashboard
docker-compose up

# Stop the dashboard
docker-compose down

# Clean up
xhost -local:docker
```

## macOS Setup

### 1. Install XQuartz

```bash
brew install --cask xquartz
```

### 2. Configure XQuartz

1. Open XQuartz
2. Go to Preferences → Security
3. Enable "Allow connections from network clients"
4. Restart XQuartz

### 3. Set Display Variable

```bash
# Get your IP address
IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')

# Allow X11 forwarding
xhost + $IP

# Set DISPLAY variable
export DISPLAY=$IP:0

# Run with docker-compose
docker-compose up
```

## Windows Setup

### 1. Install VcXsrv

Download and install from [SourceForge](https://sourceforge.net/projects/vcxsrv/)

### 2. Configure VcXsrv

1. Launch XLaunch
2. Select "Multiple windows"
3. Select "Start no client"
4. **Important**: Check "Disable access control"
5. Save configuration

### 3. Set Display Variable

```powershell
# In PowerShell
$env:DISPLAY="host.docker.internal:0"

# Run with docker-compose
docker-compose up
```

## Docker Compose Profiles

### Run with Database (PostgreSQL)

```bash
docker-compose --profile database up
```

This starts both:
- Hurricane Dashboard
- PostgreSQL database

### Run Dashboard Only (CSV Mode)

```bash
docker-compose up hurricane-dashboard
```

Uses CSV file for data (no database needed)

## Troubleshooting

### GUI Not Displaying (Linux)

```bash
# Check X11 is working
xeyes

# Reset X11 permissions
xhost +local:docker

# Check DISPLAY variable
echo $DISPLAY
```

### Permission Denied (Linux)

```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test
docker run hello-world
```

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild without cache
docker-compose build --no-cache

# Remove old containers
docker-compose down -v
```

### Display Issues (macOS)

```bash
# Restart XQuartz
killall XQuartz
open -a XQuartz

# Reset display variable
IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
export DISPLAY=$IP:0
xhost + $IP
```

### Display Issues (Windows)

1. Make sure VcXsrv is running
2. Check "Disable access control" is enabled
3. Restart VcXsrv
4. Try: `$env:DISPLAY="localhost:0"` instead

## Advanced Usage

### Build Specific Version

```bash
# Build with custom tag
docker build -t hurricane-vis:v1.0 .

# Run specific version
docker run --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  hurricane-vis:v1.0
```

### Development Mode

```bash
# Mount source code for live updates
docker-compose -f docker-compose.dev.yml up
```

### Production Deployment

```bash
# Build optimized image
docker build -t hurricane-vis:prod \
  --build-arg PYTHON_VERSION=3.12-slim \
  .

# Run in detached mode
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Volume Management

### Persistent Settings

Settings are automatically saved in:
```
./dashboard_settings.json
```

### Database Data

PostgreSQL data is stored in Docker volume:
```bash
# List volumes
docker volume ls

# Backup database
docker-compose exec postgres pg_dump -U hurricane_user hurricane_data > backup.sql

# Restore database
docker-compose exec -T postgres psql -U hurricane_user hurricane_data < backup.sql
```

### Clean Up Volumes

```bash
# Remove all volumes
docker-compose down -v

# Remove specific volume
docker volume rm gulfcoasthurricanevis_postgres_data
```

## Performance Tips

### Increase Memory (Docker Desktop)

1. Open Docker Desktop
2. Go to Settings → Resources
3. Increase Memory to 4GB+ for large datasets
4. Click "Apply & Restart"

### Optimize Build

```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker-compose build

# Multi-stage build (already configured)
docker build --target production .
```

### Reduce Image Size

```bash
# Check image size
docker images | grep hurricane

# Remove unused images
docker image prune -a
```

## Updating

### Update Application

```bash
# Pull latest code
git pull origin master

# Rebuild image
docker-compose build --no-cache

# Restart
docker-compose up
```

### Update Dependencies

```bash
# Update requirements.txt
# Then rebuild
docker-compose build --no-cache
```

## Security Considerations

### Production Deployment

1. **Don't use** `xhost +` in production
2. **Use** specific user permissions
3. **Configure** firewall rules
4. **Enable** Docker security scanning
5. **Use** secrets management for credentials

### Secure X11 Forwarding

```bash
# More secure: only allow docker containers
xhost +local:docker

# Remove permissions after use
xhost -local:docker
```

## Help & Support

### Check Version

```bash
docker --version
docker-compose --version
python --version
```

### View Logs

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs hurricane-dashboard
```

### Interactive Shell

```bash
# Access container shell
docker-compose exec hurricane-dashboard bash

# Check Python environment
docker-compose exec hurricane-dashboard python -c "import sys; print(sys.version)"
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [XQuartz (macOS)](https://www.xquartz.org/)
- [VcXsrv (Windows)](https://sourceforge.net/projects/vcxsrv/)

---

**Need help?** Open an issue on GitHub or check the main README.md for more information.
