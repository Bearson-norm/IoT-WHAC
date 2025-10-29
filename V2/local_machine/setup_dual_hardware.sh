#!/bin/bash
# Setup dual sensor hardware

echo "=========================================="
echo "DUAL SENSOR HARDWARE SETUP"
echo "=========================================="

echo "1. Checking current hardware..."
python3 check_hardware.py

echo ""
echo "2. Checking USB devices..."
lsusb

echo ""
echo "3. Checking serial ports..."
echo "USB ports:"
ls /dev/ttyUSB* 2>/dev/null || echo "No USB ports found"
echo "ACM ports:"
ls /dev/ttyACM* 2>/dev/null || echo "No ACM ports found"
echo "Serial ports:"
ls /dev/serial* 2>/dev/null || echo "No serial ports found"

echo ""
echo "4. Checking kernel messages..."
dmesg | grep -i usb | tail -10

echo ""
echo "=========================================="
echo "HARDWARE SETUP GUIDE"
echo "=========================================="
echo ""
echo "For dual sensor setup, you need:"
echo "1. Two AS608 sensors (3.3V)"
echo "2. Two USB-to-Serial adapters (3.3V compatible)"
echo "3. Proper connections:"
echo ""
echo "Sensor 1:"
echo "  AS608_1 VCC → USB-to-Serial_1 3.3V"
echo "  AS608_1 GND → USB-to-Serial_1 GND"
echo "  AS608_1 TX  → USB-to-Serial_1 RX"
echo "  AS608_1 RX  → USB-to-Serial_1 TX"
echo "  USB-to-Serial_1 → Pi USB port 1"
echo ""
echo "Sensor 2:"
echo "  AS608_2 VCC → USB-to-Serial_2 3.3V"
echo "  AS608_2 GND → USB-to-Serial_2 GND"
echo "  AS608_2 TX  → USB-to-Serial_2 RX"
echo "  AS608_2 RX  → USB-to-Serial_2 TX"
echo "  USB-to-Serial_2 → Pi USB port 2"
echo ""
echo "Expected ports after connection:"
echo "  /dev/ttyUSB0 (first sensor)"
echo "  /dev/ttyUSB1 (second sensor)"
echo ""
echo "If you see only /dev/serial0, you need:"
echo "1. Connect second USB-to-Serial adapter"
echo "2. Check power supply for AS608 (3.3V)"
echo "3. Verify wiring connections"
echo "=========================================="


