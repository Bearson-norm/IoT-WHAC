#!/bin/bash
# Check sensor issue

echo "=========================================="
echo "CHECKING SENSOR ISSUE"
echo "=========================================="

echo "1. Checking processes using serial ports..."
lsof /dev/serial* /dev/ttyS* 2>/dev/null || echo "No processes using serial ports"

echo ""
echo "2. Checking serial port permissions..."
ls -la /dev/serial* /dev/ttyS* 2>/dev/null || echo "No serial ports found"

echo ""
echo "3. Testing individual sensors..."
python3 diagnose_dual_sensors.py

echo ""
echo "4. If sensors are working, try fixing the issue..."
python3 fix_sensor_issue.py

echo ""
echo "=========================================="
echo "SENSOR ISSUE CHECK COMPLETED"
echo "=========================================="


