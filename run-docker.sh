#!/bin/bash

# Gulf Coast Hurricane Visualization Dashboard - Docker Runner
# This script builds and runs the containerized dashboard

set -e

echo "🌀 Gulf Coast Hurricane Visualization Dashboard"
echo "================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Allow X11 connections from localhost (for GUI display)
echo "🔧 Configuring X11 display access..."
xhost +local:docker > /dev/null 2>&1 || true

# Build the Docker image
echo "🏗️  Building Docker image..."
docker-compose build

# Run the application
echo "🚀 Starting Hurricane Dashboard..."
echo ""
echo "📊 The dashboard will open in a new window."
echo "   Press Ctrl+C to stop the application."
echo ""

# Use docker-compose or docker compose based on what's available
if command -v docker-compose &> /dev/null; then
    docker-compose up
else
    docker compose up
fi

# Cleanup X11 permissions on exit
echo ""
echo "🧹 Cleaning up..."
xhost -local:docker > /dev/null 2>&1 || true

echo "✅ Dashboard stopped successfully."
