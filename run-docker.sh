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

# Detect if we need sudo for Docker
DOCKER_CMD="docker"
COMPOSE_CMD="docker-compose"
if ! docker ps &> /dev/null; then
    if sudo docker ps &> /dev/null 2>&1; then
        echo "⚠️  Docker requires sudo (you may need to log out/in for group permissions)"
        DOCKER_CMD="sudo docker"
        COMPOSE_CMD="sudo docker-compose"
    else
        echo "❌ Cannot access Docker. Please check Docker installation."
        exit 1
    fi
fi

# Allow X11 connections from localhost (for GUI display)
echo "🔧 Configuring X11 display access..."
xhost +local:docker > /dev/null 2>&1 || true

# Build the Docker image
echo "🏗️  Building Docker image..."
$COMPOSE_CMD build

# Run the application
echo "🚀 Starting Hurricane Dashboard..."
echo ""
echo "📊 The dashboard will open in a new window."
echo "   Press Ctrl+C to stop the application."
echo ""

# Use the appropriate compose command
$COMPOSE_CMD up

# Cleanup X11 permissions on exit
echo ""
echo "🧹 Cleaning up..."
xhost -local:docker > /dev/null 2>&1 || true

echo "✅ Dashboard stopped successfully."
