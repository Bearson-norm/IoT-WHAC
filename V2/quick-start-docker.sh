#!/bin/bash

# Quick Start Script for WHAC Fingerprint System Docker Deployment
# This script helps you deploy the system components individually

set -e

echo "🚀 WHAC Fingerprint System - Docker Quick Start"
echo "=============================================="

# Function to display usage
usage() {
    echo "Usage: $0 [local|web|server|all]"
    echo ""
    echo "Options:"
    echo "  local   - Deploy local machine (Raspberry Pi)"
    echo "  web     - Deploy web UI (VPS)"
    echo "  server  - Deploy server (VPS)"
    echo "  all     - Deploy all components (reference only)"
    echo ""
    echo "Examples:"
    echo "  $0 local    # Deploy on Raspberry Pi"
    echo "  $0 web      # Deploy web UI on VPS"
    echo "  $0 server   # Deploy server on VPS"
}

# Function to deploy local machine
deploy_local() {
    echo "📱 Deploying Local Machine (Raspberry Pi)..."
    cd local_machine
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo "📝 Creating .env file from template..."
        cp env.example .env
        echo "⚠️  Please edit .env file with your configuration before running again"
        echo "   nano .env"
        exit 1
    fi
    
    echo "🔨 Building Docker image..."
    docker-compose build
    
    echo "🚀 Starting services..."
    docker-compose up -d
    
    echo "✅ Local machine deployed successfully!"
    echo "📊 View logs: docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
}

# Function to deploy web UI
deploy_web() {
    echo "🌐 Deploying Web UI (VPS)..."
    cd web_ui
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo "📝 Creating .env file from template..."
        cp env.example .env
        echo "⚠️  Please edit .env file with your configuration before running again"
        echo "   nano .env"
        exit 1
    fi
    
    echo "🔨 Building Docker image..."
    docker-compose build
    
    echo "🚀 Starting services..."
    docker-compose up -d
    
    echo "✅ Web UI deployed successfully!"
    echo "🌐 Access at: http://localhost:5000"
    echo "📊 View logs: docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
}

# Function to deploy server
deploy_server() {
    echo "🖥️  Deploying Server (VPS)..."
    cd server
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo "📝 Creating .env file from template..."
        cp env.example .env
        echo "⚠️  Please edit .env file with your configuration before running again"
        echo "   nano .env"
        exit 1
    fi
    
    echo "🔨 Building Docker image..."
    docker-compose build
    
    echo "🚀 Starting services..."
    docker-compose up -d
    
    echo "✅ Server deployed successfully!"
    echo "📊 View logs: docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
}

# Function to show all deployment info
deploy_all() {
    echo "📋 Complete System Deployment Guide"
    echo "=================================="
    echo ""
    echo "1. 🍓 Raspberry Pi (Local Machine):"
    echo "   cd local_machine && ./quick-start-docker.sh local"
    echo ""
    echo "2. 🌐 VPS (Web UI + Server):"
    echo "   cd web_ui && ./quick-start-docker.sh web"
    echo "   cd server && ./quick-start-docker.sh server"
    echo ""
    echo "3. 📚 Configuration:"
    echo "   - Edit .env files in each component directory"
    echo "   - Update MQTT broker IP addresses"
    echo "   - Configure database credentials"
    echo ""
    echo "4. 📖 Full documentation: DOCKER_DEPLOYMENT_GUIDE.md"
}

# Main script logic
case "${1:-}" in
    local)
        deploy_local
        ;;
    web)
        deploy_web
        ;;
    server)
        deploy_server
        ;;
    all)
        deploy_all
        ;;
    *)
        usage
        exit 1
        ;;
esac

