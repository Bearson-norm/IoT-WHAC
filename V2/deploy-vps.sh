#!/bin/bash

# ============================================
# VPS Deployment Script for WHAC Fingerprint System
# Port 4545
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running with correct permissions
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo "Please install Docker first. See VPS_DEPLOYMENT_GUIDE.md"
        exit 1
    fi
    print_success "Docker is installed: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        echo "Please install Docker Compose first. See VPS_DEPLOYMENT_GUIDE.md"
        exit 1
    fi
    print_success "Docker Compose is installed: $(docker-compose --version)"
    
    # Check if .env file exists
    if [ ! -f "vps.env" ]; then
        print_warning "vps.env file not found!"
        echo ""
        read -p "Do you want to create vps.env from template? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp vps-env.example vps.env
            print_success "Created vps.env from template"
            print_warning "IMPORTANT: Please edit vps.env and change DB_PASSWORD and SECRET_KEY!"
            echo ""
            read -p "Press Enter after you've edited vps.env..." -r
        else
            print_error "Deployment cancelled. Please create vps.env first."
            exit 1
        fi
    fi
    print_success "vps.env file found"
    
    # Check if required files exist
    if [ ! -f "docker-compose.vps.yml" ]; then
        print_error "docker-compose.vps.yml not found!"
        exit 1
    fi
    print_success "docker-compose.vps.yml found"
    
    echo ""
}

# Check if default passwords are still being used
check_security() {
    print_header "Security Check"
    
    # Load env file
    source vps.env
    
    # Check DB_PASSWORD
    if [ "$DB_PASSWORD" == "Admin123" ] || [ "$DB_PASSWORD" == "ChangeThisToAStrongPassword123!" ]; then
        print_error "You are using the default database password!"
        print_warning "This is a security risk. Please change DB_PASSWORD in vps.env"
        read -p "Do you want to continue anyway? (NOT RECOMMENDED) (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Custom database password detected"
    fi
    
    # Check SECRET_KEY
    if [ "$SECRET_KEY" == "whac_fingerprint_secret_key" ] || [[ "$SECRET_KEY" == *"ChangeThis"* ]]; then
        print_error "You are using the default SECRET_KEY!"
        print_warning "This is a security risk. Please change SECRET_KEY in vps.env"
        read -p "Do you want to continue anyway? (NOT RECOMMENDED) (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Custom SECRET_KEY detected"
    fi
    
    echo ""
}

# Stop existing containers
stop_existing() {
    print_header "Stopping Existing Containers"
    
    if [ "$(docker ps -q -f name=whac)" ]; then
        print_info "Stopping existing WHAC containers..."
        docker-compose -f docker-compose.vps.yml --env-file vps.env down
        print_success "Existing containers stopped"
    else
        print_info "No existing containers to stop"
    fi
    
    echo ""
}

# Build Docker images
build_images() {
    print_header "Building Docker Images"
    
    print_info "This may take 5-10 minutes on first run..."
    docker-compose -f docker-compose.vps.yml --env-file vps.env build
    
    print_success "Docker images built successfully"
    echo ""
}

# Start services
start_services() {
    print_header "Starting Services"
    
    print_info "Starting all services in background..."
    docker-compose -f docker-compose.vps.yml --env-file vps.env up -d
    
    print_success "Services started"
    echo ""
    
    print_info "Waiting for services to initialize (60 seconds)..."
    for i in {1..60}; do
        echo -n "."
        sleep 1
    done
    echo ""
    echo ""
}

# Check service status
check_status() {
    print_header "Checking Service Status"
    
    # Get running containers
    RUNNING=$(docker-compose -f docker-compose.vps.yml ps | grep "Up" | wc -l)
    
    echo ""
    docker-compose -f docker-compose.vps.yml ps
    echo ""
    
    if [ $RUNNING -ge 3 ]; then
        print_success "All services are running!"
    else
        print_warning "Some services may not be running properly"
        print_info "Check logs with: docker-compose -f docker-compose.vps.yml logs"
    fi
    
    echo ""
}

# Display access information
display_info() {
    print_header "Deployment Complete!"
    
    # Get VPS IP
    VPS_IP=$(curl -s ifconfig.me)
    
    # Load port from env
    source vps.env
    PORT=${WEB_PORT:-4545}
    
    echo ""
    echo -e "${GREEN}✓ WHAC Fingerprint System is now running!${NC}"
    echo ""
    echo -e "${BLUE}Access Information:${NC}"
    echo -e "  URL: ${GREEN}http://$VPS_IP:$PORT${NC}"
    echo -e "  Username: ${GREEN}admin${NC}"
    echo -e "  Password: ${GREEN}admin123${NC} ${YELLOW}(Change this after first login!)${NC}"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  View logs:     docker-compose -f docker-compose.vps.yml logs -f"
    echo "  Stop services: docker-compose -f docker-compose.vps.yml down"
    echo "  Restart:       docker-compose -f docker-compose.vps.yml restart"
    echo "  Status:        docker-compose -f docker-compose.vps.yml ps"
    echo ""
    echo -e "${BLUE}Database Backup:${NC}"
    echo "  docker exec whac-postgres pg_dump -U postgres whac_master > backup.sql"
    echo ""
    echo -e "${YELLOW}IMPORTANT Security Notes:${NC}"
    echo "  1. Change admin password after first login"
    echo "  2. Setup firewall if not already done"
    echo "  3. Setup regular database backups"
    echo "  4. Consider setting up HTTPS/SSL"
    echo ""
    print_info "See VPS_DEPLOYMENT_GUIDE.md for detailed documentation"
    echo ""
}

# Main deployment process
main() {
    clear
    print_header "WHAC Fingerprint System - VPS Deployment"
    echo ""
    
    # Run checks and deployment
    check_prerequisites
    check_security
    
    # Confirm deployment
    read -p "Ready to deploy to VPS. Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled"
        exit 1
    fi
    echo ""
    
    # Execute deployment
    stop_existing
    build_images
    start_services
    check_status
    display_info
    
    print_success "Deployment script completed!"
}

# Run main function
main

