# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:0

# Install system dependencies for GUI and geographic libraries
RUN apt-get update && apt-get install -y \
    # GUI support
    python3-tk \
    x11-apps \
    # Geographic libraries for Cartopy
    libgeos-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    # Build tools
    gcc \
    g++ \
    make \
    # Fonts
    fonts-dejavu-core \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directory for database (if needed later)
RUN mkdir -p /app/database

# Set permissions
RUN chmod +x launch_with_loading.py

# Expose port for potential web interface (future enhancement)
EXPOSE 8050

# Default command to run the application
CMD ["python", "launch_with_loading.py"]
