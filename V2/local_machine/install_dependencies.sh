#!/bin/bash
# Install dependencies for dual sensor setup

echo "=========================================="
echo "INSTALLING DEPENDENCIES FOR DUAL SENSORS"
echo "=========================================="

echo "1. Updating system packages..."
sudo apt update

echo ""
echo "2. Installing system dependencies..."
sudo apt install -y python3-pip python3-serial python3-dev build-essential

echo ""
echo "3. Installing Python packages..."
pip3 install pyserial paho-mqtt adafruit-circuitpython-fingerprint RPi.GPIO

echo ""
echo "4. Verifying installations..."
python3 -c "import serial; print('✅ pyserial installed')" 2>/dev/null || echo "❌ pyserial not found"
python3 -c "import paho.mqtt.client; print('✅ paho-mqtt installed')" 2>/dev/null || echo "❌ paho-mqtt not found"
python3 -c "import adafruit_fingerprint; print('✅ adafruit-circuitpython-fingerprint installed')" 2>/dev/null || echo "❌ adafruit-circuitpython-fingerprint not found"
python3 -c "import RPi.GPIO; print('✅ RPi.GPIO installed')" 2>/dev/null || echo "❌ RPi.GPIO not found"

echo ""
echo "=========================================="
echo "DEPENDENCY INSTALLATION COMPLETED!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run: chmod +x fix_permissions.sh && ./fix_permissions.sh"
echo "2. Log out and log back in"
echo "3. Run: python3 test_sensors_simple.py"
echo "4. If sensors are detected, run: python3 dual_fingerprint_simple_client.py"
echo "=========================================="


