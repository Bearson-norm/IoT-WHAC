#!/bin/bash
# Quick fix for dual sensor setup

echo "=========================================="
echo "QUICK FIX FOR DUAL SENSOR SETUP"
echo "=========================================="

echo "1. Installing dependencies..."
pip3 install pyserial paho-mqtt adafruit-circuitpython-fingerprint RPi.GPIO

echo ""
echo "2. Setting permissions..."
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB* /dev/ttyACM* /dev/serial* 2>/dev/null || true

echo ""
echo "3. Testing simple connection..."
python3 test_sensors_simple.py

echo ""
echo "=========================================="
echo "QUICK FIX COMPLETED!"
echo "=========================================="
echo ""
echo "IMPORTANT: You need to log out and log back in for group changes to take effect!"
echo ""
echo "After logging back in, run:"
echo "  python3 dual_fingerprint_simple_client.py"
echo "=========================================="


