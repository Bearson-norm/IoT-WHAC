#!/bin/bash
# Final dual sensor system startup

echo "=========================================="
echo "DUAL SENSOR SYSTEM - FINAL STARTUP"
echo "=========================================="

echo "1. Testing dual sensor setup..."
python3 simple_port_test.py

echo ""
echo "2. Starting dual sensor MQTT client..."
echo "Press Ctrl+C to stop"
python3 start_dual_sensors.py

echo ""
echo "=========================================="
echo "DUAL SENSOR SYSTEM STOPPED"
echo "=========================================="


