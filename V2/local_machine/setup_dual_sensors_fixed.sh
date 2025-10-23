#!/bin/bash
# Fixed installation script for Dual AS608 Fingerprint Sensor System (3.3V)

echo "=========================================="
echo "DUAL AS608 SENSOR SETUP (FIXED VERSION)"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

echo "1. Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo ""
echo "2. Installing system packages..."
sudo apt update
sudo apt install -y python3-pip python3-serial python3-dev build-essential

echo ""
echo "3. Installing Python dependencies..."
pip3 install pyserial paho-mqtt adafruit-circuitpython-fingerprint RPi.GPIO

echo ""
echo "4. Setting up permissions..."
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Set permissions for serial ports
sudo chmod 666 /dev/ttyUSB* 2>/dev/null || echo "No USB ports found"
sudo chmod 666 /dev/ttyACM* 2>/dev/null || echo "No ACM ports found"
sudo chmod 666 /dev/serial* 2>/dev/null || echo "No serial ports found"

echo ""
echo "5. Checking available ports..."
echo "USB Serial ports:"
ls /dev/ttyUSB* 2>/dev/null || echo "No USB serial ports found"
echo "ACM ports:"
ls /dev/ttyACM* 2>/dev/null || echo "No ACM ports found"
echo "Built-in serial ports:"
ls /dev/serial* 2>/dev/null || echo "No built-in serial ports found"

echo ""
echo "6. Testing port access..."
for port in /dev/ttyUSB* /dev/ttyACM* /dev/serial*; do
    if [ -e "$port" ]; then
        echo "Testing $port..."
        if timeout 3 python3 -c "import serial; serial.Serial('$port', 57600, timeout=1)" 2>/dev/null; then
            echo "✅ $port - Accessible"
        else
            echo "❌ $port - Not accessible"
        fi
    fi
done

echo ""
echo "7. Creating systemd service..."
sudo tee /etc/systemd/system/dual-fingerprint-mqtt.service > /dev/null <<EOF
[Unit]
Description=Dual AS608 Fingerprint MQTT Client (3.3V)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/dual_fingerprint_simple_client.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=$(pwd)

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "SETUP COMPLETED!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Log out and log back in for group changes to take effect"
echo "2. Run: python3 quick_sensor_test.py"
echo "3. If sensors are detected, run: python3 dual_fingerprint_simple_client.py"
echo ""
echo "Hardware Setup for 3.3V AS608:"
echo "1. Connect AS608 VCC to 3.3V (not 5V!)"
echo "2. Connect AS608 GND to GND"
echo "3. Connect AS608 TX to USB-to-Serial RX"
echo "4. Connect AS608 RX to USB-to-Serial TX"
echo "5. Connect USB-to-Serial to Raspberry Pi USB port"
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
echo "3.3V AS608 Benefits:"
echo "✓ No level shifter required"
echo "✓ Direct GPIO connection"
echo "✓ Lower power consumption"
echo "✓ More stable operation"
echo "=========================================="
