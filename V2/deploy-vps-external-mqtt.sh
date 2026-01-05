#!/bin/bash

# ============================================
# WHAC IoT System - VPS Deployment Script
# External MQTT Broker Version
# ============================================

set -e  # Exit on error

echo "======================================"
echo "WHAC IoT - VPS Deployment Script"
echo "Version: 2.0 (External MQTT)"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.vps-external-mqtt.yml"
ENV_FILE=".env"
ENV_EXAMPLE="vps-external-mqtt.env.example"

# Functions
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
    echo -e "ℹ $1"
}

check_requirements() {
    print_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo "Please install Docker first:"
        echo "curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "sudo sh get-docker.sh"
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        echo "Please install Docker Compose first:"
        echo "sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
        echo "sudo chmod +x /usr/local/bin/docker-compose"
        exit 1
    fi
    print_success "Docker Compose is installed"
    
    # Check if docker service is running
    if ! sudo systemctl is-active --quiet docker; then
        print_warning "Docker service is not running. Starting..."
        sudo systemctl start docker
    fi
    print_success "Docker service is running"
    
    echo ""
}

check_files() {
    print_info "Checking required files..."
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    print_success "Docker Compose file found"
    
    if [ ! -f "$ENV_EXAMPLE" ]; then
        print_error "Environment example file not found: $ENV_EXAMPLE"
        exit 1
    fi
    print_success "Environment example file found"
    
    if [ ! -d "web_ui" ]; then
        print_error "web_ui directory not found!"
        exit 1
    fi
    print_success "web_ui directory found"
    
    echo ""
}

setup_env() {
    print_info "Setting up environment file..."
    
    if [ -f "$ENV_FILE" ]; then
        print_warning "Environment file already exists: $ENV_FILE"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Using existing environment file"
            return
        fi
    fi
    
    # Copy example to .env
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    print_success "Created environment file: $ENV_FILE"
    
    # Generate secure passwords
    print_info "Generating secure passwords..."
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    SECRET_KEY=$(openssl rand -hex 64)
    
    # Update .env file (compatible with both Linux and macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" "$ENV_FILE"
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" "$ENV_FILE"
    else
        # Linux
        sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" "$ENV_FILE"
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" "$ENV_FILE"
    fi
    
    print_success "Generated secure DB_PASSWORD"
    print_success "Generated secure SECRET_KEY"
    
    # Set secure permissions
    chmod 600 "$ENV_FILE"
    print_success "Set secure permissions (600) on $ENV_FILE"
    
    echo ""
    print_warning "IMPORTANT: Review and update $ENV_FILE if needed!"
    print_info "Especially check MQTT_BROKER IP address"
    echo ""
}

check_mqtt_connectivity() {
    print_info "Checking MQTT broker connectivity..."
    
    # Get MQTT broker from .env
    if [ -f "$ENV_FILE" ]; then
        MQTT_BROKER=$(grep "^MQTT_BROKER=" "$ENV_FILE" | cut -d'=' -f2)
        MQTT_PORT=$(grep "^MQTT_PORT=" "$ENV_FILE" | cut -d'=' -f2)
    else
        MQTT_BROKER="103.87.67.139"
        MQTT_PORT="1883"
    fi
    
    print_info "Testing connection to MQTT broker: $MQTT_BROKER:$MQTT_PORT"
    
    # Test using nc (netcat) or telnet
    if command -v nc &> /dev/null; then
        if timeout 5 nc -zv "$MQTT_BROKER" "$MQTT_PORT" 2>&1 | grep -q succeeded; then
            print_success "MQTT broker is reachable"
        else
            print_warning "Cannot reach MQTT broker at $MQTT_BROKER:$MQTT_PORT"
            print_info "Please check:"
            print_info "  1. MQTT broker IP address is correct"
            print_info "  2. VPS can access the MQTT broker (firewall rules)"
            print_info "  3. MQTT broker is running"
        fi
    elif command -v telnet &> /dev/null; then
        if timeout 5 telnet "$MQTT_BROKER" "$MQTT_PORT" 2>&1 | grep -q Connected; then
            print_success "MQTT broker is reachable"
        else
            print_warning "Cannot reach MQTT broker at $MQTT_BROKER:$MQTT_PORT"
        fi
    else
        print_warning "nc or telnet not found, skipping MQTT connectivity test"
    fi
    
    echo ""
}

setup_firewall() {
    print_info "Checking firewall configuration..."
    
    if ! command -v ufw &> /dev/null; then
        print_warning "UFW (firewall) is not installed"
        read -p "Do you want to install UFW? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt update
            sudo apt install -y ufw
            print_success "UFW installed"
        else
            print_info "Skipping firewall configuration"
            return
        fi
    fi
    
    # Check if UFW is active
    if ! sudo ufw status | grep -q "Status: active"; then
        print_warning "UFW is not active"
        read -p "Do you want to configure and enable UFW? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Allow SSH first (IMPORTANT!)
            sudo ufw allow 22/tcp
            print_success "Allowed SSH (port 22)"
            
            # Allow Web UI port
            sudo ufw allow 4545/tcp
            print_success "Allowed Web UI (port 4545)"
            
            # Enable UFW
            echo "y" | sudo ufw enable
            print_success "UFW enabled"
        fi
    else
        # UFW is active, just add rules if needed
        if ! sudo ufw status | grep -q "4545"; then
            sudo ufw allow 4545/tcp
            print_success "Allowed Web UI (port 4545)"
        else
            print_success "Port 4545 already allowed"
        fi
    fi
    
    echo ""
}

deploy_containers() {
    print_info "Starting deployment..."
    echo ""
    
    # Stop existing containers (if any)
    print_info "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down 2>/dev/null || true
    print_success "Existing containers stopped"
    
    # Pull latest images
    print_info "Pulling Docker images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    print_success "Images pulled"
    
    # Build custom images
    print_info "Building application images..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache
    print_success "Images built"
    
    # Start containers
    print_info "Starting containers..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    print_success "Containers started"
    
    echo ""
    print_info "Waiting for services to be ready..."
    sleep 10
    
    # Check container status
    print_info "Checking container status..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    echo ""
}

show_logs() {
    print_info "Showing recent logs..."
    echo ""
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs --tail=50
    echo ""
}

show_summary() {
    echo ""
    echo "======================================"
    print_success "Deployment completed!"
    echo "======================================"
    echo ""
    
    # Get VPS IP
    VPS_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_VPS_IP")
    
    echo "📊 Access Information:"
    echo "   Web UI: http://$VPS_IP:4545"
    echo "   Default Login:"
    echo "     Username: admin"
    echo "     Password: admin123"
    echo ""
    
    echo "🔐 IMPORTANT Security Steps:"
    echo "   1. Change default admin password after first login"
    echo "   2. Review and update .env file if needed"
    echo "   3. Keep .env file secure (chmod 600)"
    echo ""
    
    echo "📋 Useful Commands:"
    echo "   View logs:"
    echo "     docker-compose -f $COMPOSE_FILE logs -f"
    echo ""
    echo "   Check status:"
    echo "     docker-compose -f $COMPOSE_FILE ps"
    echo ""
    echo "   Restart services:"
    echo "     docker-compose -f $COMPOSE_FILE restart"
    echo ""
    echo "   Stop services:"
    echo "     docker-compose -f $COMPOSE_FILE down"
    echo ""
    echo "   Update from Git:"
    echo "     git pull && docker-compose -f $COMPOSE_FILE build && docker-compose -f $COMPOSE_FILE up -d"
    echo ""
    
    echo "🔧 Troubleshooting:"
    echo "   If Web UI is not accessible:"
    echo "     1. Check logs: docker logs whac-web-ui"
    echo "     2. Check firewall: sudo ufw status"
    echo "     3. Test locally: curl http://localhost:4545"
    echo ""
    
    echo "📚 Documentation:"
    echo "   Full guide: PANDUAN_DEPLOY_VPS_DOCKER.md"
    echo ""
}

# Main execution
main() {
    echo ""
    check_requirements
    check_files
    setup_env
    check_mqtt_connectivity
    setup_firewall
    
    read -p "Ready to deploy? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        deploy_containers
        
        read -p "Show logs? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            show_logs
        fi
        
        show_summary
    else
        print_info "Deployment cancelled"
    fi
}

# Run main
main


