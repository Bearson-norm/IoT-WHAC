#!/bin/bash

# Installation script for Fingerprint MQTT Client on Raspberry Pi 4

echo "Fingerprint MQTT Client Installation Script"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing from: $SCRIPT_DIR"

# Update system packages
echo "Updating system packages..."
sudo apt update

# Install required system packages
echo "Installing system packages..."
sudo apt install -y python3-pip python3-serial python3-dev build-essential

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Add user to dialout group for serial access
echo "Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Create logs directory
mkdir -p logs
echo "Created logs directory"

# Make scripts executable
chmod +x fingerprint_mqtt_client.py
chmod +x test_setup.py
chmod +x setup.py

echo ""
echo "Installation completed!"
echo ""
echo "IMPORTANT: You need to reboot or logout/login for the dialout group changes to take effect."
echo ""
echo "Next steps:"
echo "1. Connect your AS608 fingerprint sensor to a USB port"
echo "2. Check the device path: ls /dev/tty*"
echo "3. Update FINGERPRINT_PORT in config.py if needed"
echo "4. Run the test script: python3 test_setup.py"
echo "5. If tests pass, run the main program: python3 fingerprint_mqtt_client.py"
echo ""
echo "To install as a system service:"
echo "1. Copy fingerprint-mqtt.service to /etc/systemd/system/"
echo "2. Edit the service file to update the WorkingDirectory path"
echo "3. Run: sudo systemctl enable fingerprint-mqtt.service"
echo "4. Run: sudo systemctl start fingerprint-mqtt.service"
echo ""
echo "Would you like to reboot now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Rebooting in 5 seconds..."
    sleep 5
    sudo reboot
fi
