#!/bin/bash

# ============================================
# Docker Installation Script for VPS
# Ubuntu/Debian
# ============================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root or with sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run with sudo or as root"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "Cannot detect OS"
        exit 1
    fi
    
    print_info "Detected OS: $OS $VER"
}

# Update system
update_system() {
    print_header "Updating System"
    apt update
    apt upgrade -y
    print_success "System updated"
    echo ""
}

# Install Docker
install_docker() {
    print_header "Installing Docker"
    
    # Check if Docker already installed
    if command -v docker &> /dev/null; then
        print_info "Docker is already installed: $(docker --version)"
        read -p "Reinstall Docker? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    # Install dependencies
    print_info "Installing dependencies..."
    apt install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker GPG key
    print_info "Adding Docker GPG key..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    print_info "Adding Docker repository..."
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update package database
    apt update
    
    # Install Docker Engine
    print_info "Installing Docker Engine..."
    apt install -y docker-ce docker-ce-cli containerd.io
    
    # Verify installation
    if command -v docker &> /dev/null; then
        print_success "Docker installed: $(docker --version)"
    else
        print_error "Docker installation failed"
        exit 1
    fi
    
    echo ""
}

# Install Docker Compose
install_docker_compose() {
    print_header "Installing Docker Compose"
    
    # Check if already installed
    if command -v docker-compose &> /dev/null; then
        print_info "Docker Compose is already installed: $(docker-compose --version)"
        read -p "Reinstall Docker Compose? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    # Download latest version
    print_info "Downloading Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make executable
    chmod +x /usr/local/bin/docker-compose
    
    # Verify installation
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose installed: $(docker-compose --version)"
    else
        print_error "Docker Compose installation failed"
        exit 1
    fi
    
    echo ""
}

# Configure Docker
configure_docker() {
    print_header "Configuring Docker"
    
    # Start Docker service
    print_info "Starting Docker service..."
    systemctl start docker
    systemctl enable docker
    
    # Check status
    if systemctl is-active --quiet docker; then
        print_success "Docker service is running"
    else
        print_error "Docker service failed to start"
        exit 1
    fi
    
    # Add current user to docker group (if not root)
    if [ -n "$SUDO_USER" ]; then
        print_info "Adding $SUDO_USER to docker group..."
        usermod -aG docker $SUDO_USER
        print_success "User added to docker group"
        print_info "You may need to logout and login again for group changes to take effect"
    fi
    
    echo ""
}

# Configure firewall
configure_firewall() {
    print_header "Configuring Firewall"
    
    # Check if ufw is installed
    if ! command -v ufw &> /dev/null; then
        print_info "Installing ufw..."
        apt install -y ufw
    fi
    
    print_info "Configuring firewall rules..."
    
    # Allow SSH (important!)
    ufw allow 22/tcp
    print_success "Allowed SSH (port 22)"
    
    # Allow Web UI
    ufw allow 4545/tcp
    print_success "Allowed Web UI (port 4545)"
    
    # Ask about other ports
    read -p "Allow PostgreSQL external access (port 5432)? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ufw allow 5432/tcp
        print_success "Allowed PostgreSQL (port 5432)"
    fi
    
    read -p "Allow MQTT external access (port 1883)? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ufw allow 1883/tcp
        print_success "Allowed MQTT (port 1883)"
    fi
    
    # Enable firewall
    read -p "Enable firewall now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "y" | ufw enable
        print_success "Firewall enabled"
    else
        print_info "Firewall not enabled. Enable later with: sudo ufw enable"
    fi
    
    # Show status
    ufw status
    echo ""
}

# Test Docker installation
test_docker() {
    print_header "Testing Docker Installation"
    
    print_info "Running hello-world container..."
    docker run --rm hello-world
    
    if [ $? -eq 0 ]; then
        print_success "Docker is working correctly!"
    else
        print_error "Docker test failed"
        exit 1
    fi
    
    echo ""
}

# Display summary
display_summary() {
    print_header "Installation Complete!"
    
    VPS_IP=$(curl -s ifconfig.me)
    
    echo ""
    echo -e "${GREEN}✓ Docker setup completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Installed Software:${NC}"
    echo "  Docker:         $(docker --version)"
    echo "  Docker Compose: $(docker-compose --version)"
    echo ""
    echo -e "${BLUE}VPS Information:${NC}"
    echo "  IP Address: $VPS_IP"
    echo "  OS: $OS $VER"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Clone your Git repository"
    echo "  2. Configure vps.env file"
    echo "  3. Run deployment script: ./deploy-vps.sh"
    echo ""
    echo -e "${YELLOW}Important Notes:${NC}"
    if [ -n "$SUDO_USER" ]; then
        echo "  • Logout and login again to use docker without sudo"
    fi
    echo "  • Make sure firewall is properly configured"
    echo "  • See VPS_DEPLOYMENT_GUIDE.md for detailed instructions"
    echo ""
}

# Main installation process
main() {
    clear
    print_header "Docker Installation for VPS - Port 4545"
    echo ""
    
    # Check prerequisites
    check_sudo
    detect_os
    
    # Confirm installation
    read -p "This will install Docker and Docker Compose. Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Installation cancelled"
        exit 1
    fi
    echo ""
    
    # Execute installation
    update_system
    install_docker
    install_docker_compose
    configure_docker
    
    # Ask about firewall
    read -p "Configure firewall now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        configure_firewall
    else
        print_info "Skipping firewall configuration"
        echo ""
    fi
    
    test_docker
    display_summary
    
    print_success "Setup script completed!"
}

# Run main function
main

