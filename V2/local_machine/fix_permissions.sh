#!/bin/bash
# Fix permissions for dual sensor setup

echo "=========================================="
echo "FIXING PERMISSIONS FOR DUAL SENSORS"
echo "=========================================="

echo "1. Adding user to dialout group..."
sudo usermod -a -G dialout $USER

echo ""
echo "2. Setting permissions for serial ports..."
sudo chmod 666 /dev/ttyUSB* 2>/dev/null || echo "No USB ports found"
sudo chmod 666 /dev/ttyACM* 2>/dev/null || echo "No ACM ports found"
sudo chmod 666 /dev/serial* 2>/dev/null || echo "No serial ports found"

echo ""
echo "3. Checking current permissions..."
for port in /dev/ttyUSB* /dev/ttyACM* /dev/serial*; do
    if [ -e "$port" ]; then
        echo "Port: $port"
        ls -la "$port"
    fi
done

echo ""
echo "4. Testing port access..."
for port in /dev/ttyUSB* /dev/ttyACM* /dev/serial*; do
    if [ -e "$port" ]; then
        echo "Testing $port..."
        if timeout 2 python3 -c "import serial; serial.Serial('$port', 57600, timeout=1)" 2>/dev/null; then
            echo "✅ $port - Accessible"
        else
            echo "❌ $port - Not accessible"
        fi
    fi
done

echo ""
echo "=========================================="
echo "PERMISSION FIX COMPLETED!"
echo "=========================================="
echo ""
echo "IMPORTANT: You need to log out and log back in for group changes to take effect!"
echo ""
echo "After logging back in, run:"
echo "  python3 test_sensors_simple.py"
echo ""
echo "If sensors are detected, run:"
echo "  python3 dual_fingerprint_simple_client.py"
echo "=========================================="


