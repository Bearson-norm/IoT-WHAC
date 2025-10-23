#!/bin/bash
# Fix sensor connection issues for Dual AS608

echo "=========================================="
echo "FIXING DUAL AS608 SENSOR CONNECTION"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

echo "1. Checking current user groups..."
groups

echo ""
echo "2. Adding user to dialout group..."
sudo usermod -a -G dialout $USER

echo ""
echo "3. Setting permissions for serial ports..."
sudo chmod 666 /dev/ttyUSB* 2>/dev/null || echo "No USB ports found"
sudo chmod 666 /dev/ttyACM* 2>/dev/null || echo "No ACM ports found"
sudo chmod 666 /dev/serial* 2>/dev/null || echo "No serial ports found"

echo ""
echo "4. Checking available ports..."
echo "USB ports:"
ls /dev/ttyUSB* 2>/dev/null || echo "No USB ports found"
echo "ACM ports:"
ls /dev/ttyACM* 2>/dev/null || echo "No ACM ports found"
echo "Serial ports:"
ls /dev/serial* 2>/dev/null || echo "No serial ports found"

echo ""
echo "5. Testing port access..."
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
echo "FIX COMPLETED!"
echo "=========================================="
echo ""
echo "IMPORTANT: You need to log out and log back in for group changes to take effect!"
echo ""
echo "After logging back in, run:"
echo "  python3 check_sensors.py"
echo ""
echo "If sensors are detected, run:"
echo "  python3 simple_dual_test.py"
echo ""
echo "Then run the full system:"
echo "  python3 dual_fingerprint_simple_client.py"
echo "=========================================="
