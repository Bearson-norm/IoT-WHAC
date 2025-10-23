#!/bin/bash
# Installation script for Dual AS608 Fingerprint Sensor System

echo "=========================================="
echo "Dual AS608 Fingerprint Sensor Installation"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Install required packages
echo "Installing required packages..."
sudo apt update
sudo apt install -y python3-pip python3-serial

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install pyserial paho-mqtt

# Check for available serial ports
echo "Checking available serial ports..."
echo "USB Serial ports:"
ls /dev/ttyUSB* 2>/dev/null || echo "No USB serial ports found"
echo "ACM ports:"
ls /dev/ttyACM* 2>/dev/null || echo "No ACM ports found"
echo "Built-in serial ports:"
ls /dev/serial* 2>/dev/null || echo "No built-in serial ports found"

# Add user to dialout group for serial access
echo "Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Set permissions for common serial ports
echo "Setting permissions for serial ports..."
sudo chmod 666 /dev/ttyUSB* 2>/dev/null || true
sudo chmod 666 /dev/ttyACM* 2>/dev/null || true
sudo chmod 666 /dev/serial* 2>/dev/null || true

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/dual-fingerprint-mqtt.service > /dev/null <<EOF
[Unit]
Description=Dual AS608 Fingerprint MQTT Client
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/dual_fingerprint_mqtt_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "Installation completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit dual_sensor_config.py to configure your sensor ports"
echo "2. Test the setup: python3 test_dual_sensors.py"
echo "3. Run the system: python3 dual_fingerprint_mqtt_client.py"
echo ""
echo "To enable auto-start on boot:"
echo "  sudo systemctl enable dual-fingerprint-mqtt.service"
echo ""
echo "To start the service:"
echo "  sudo systemctl start dual-fingerprint-mqtt.service"
echo ""
echo "To check service status:"
echo "  sudo systemctl status dual-fingerprint-mqtt.service"
echo ""
echo "IMPORTANT: You need to log out and log back in for group changes to take effect!"
echo "=========================================="
