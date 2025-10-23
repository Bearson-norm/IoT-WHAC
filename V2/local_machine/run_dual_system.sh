#!/bin/bash
# Run dual sensor system with correct configuration

echo "=========================================="
echo "RUNNING DUAL SENSOR SYSTEM"
echo "=========================================="

echo "1. Configuring dual sensor ports..."
python3 configure_dual_ports.py

echo ""
echo "2. Testing dual sensor scanning..."
python3 test_dual_scanning.py

echo ""
echo "3. Starting dual sensor MQTT client..."
echo "Press Ctrl+C to stop"
python3 dual_fingerprint_simple_client.py

echo ""
echo "=========================================="
echo "DUAL SENSOR SYSTEM STOPPED"
echo "=========================================="
