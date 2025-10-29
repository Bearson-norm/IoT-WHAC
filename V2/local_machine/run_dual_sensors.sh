#!/bin/bash
# Run dual sensor system

echo "=========================================="
echo "RUNNING DUAL SENSOR SYSTEM"
echo "=========================================="

echo "1. Checking Python version..."
python3 --version

echo ""
echo "2. Checking dependencies..."
python3 -c "import serial; print('✅ pyserial')" 2>/dev/null || echo "❌ pyserial not found"
python3 -c "import paho.mqtt.client; print('✅ paho-mqtt')" 2>/dev/null || echo "❌ paho-mqtt not found"
python3 -c "import adafruit_fingerprint; print('✅ adafruit-circuitpython-fingerprint')" 2>/dev/null || echo "❌ adafruit-circuitpython-fingerprint not found"
python3 -c "import RPi.GPIO; print('✅ RPi.GPIO')" 2>/dev/null || echo "❌ RPi.GPIO not found"

echo ""
echo "3. Checking serial ports..."
ls /dev/ttyUSB* 2>/dev/null || echo "No USB ports found"
ls /dev/ttyACM* 2>/dev/null || echo "No ACM ports found"
ls /dev/serial* 2>/dev/null || echo "No serial ports found"

echo ""
echo "4. Testing sensor connection..."
python3 test_sensors_simple.py

echo ""
echo "5. Starting dual sensor system..."
echo "Press Ctrl+C to stop"
python3 dual_fingerprint_simple_client.py

echo ""
echo "=========================================="
echo "DUAL SENSOR SYSTEM STOPPED"
echo "=========================================="


