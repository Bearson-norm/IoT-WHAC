#!/bin/bash
# Quick test for dual sensor system

echo "=========================================="
echo "QUICK DUAL SENSOR TEST"
echo "=========================================="

echo "1. Testing port connections..."
python3 simple_port_test.py

echo ""
echo "2. If ports are working, run dual system..."
echo "Press Ctrl+C to stop"
python3 run_dual_sensors_fixed.py

echo ""
echo "=========================================="
echo "DUAL SENSOR TEST COMPLETED"
echo "=========================================="


