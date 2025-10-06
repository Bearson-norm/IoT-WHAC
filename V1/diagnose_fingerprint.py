#!/usr/bin/env python3
"""
Diagnostic script to help troubleshoot fingerprint sensor issues
Run this on your Raspberry Pi to check what's available
"""

print("Fingerprint Sensor Diagnostic Tool")
print("=" * 40)

# Test 1: Check Python version
import sys
print(f"Python version: {sys.version}")

# Test 2: Check if we're in a virtual environment
import os
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("✓ Running in virtual environment")
else:
    print("⚠ Not running in virtual environment")

# Test 3: Check imports
print("\nTesting imports...")

try:
    import serial
    print("✓ pyserial imported successfully")
    print(f"  Version: {serial.__version__}")
except ImportError as e:
    print(f"✗ pyserial import failed: {e}")

try:
    import paho.mqtt.client as mqtt
    print("✓ paho-mqtt imported successfully")
except ImportError as e:
    print(f"✗ paho-mqtt import failed: {e}")

try:
    import adafruit_fingerprint
    print("✓ adafruit_fingerprint imported successfully")
    
    # Check what's in the module
    print("\nContents of adafruit_fingerprint module:")
    for item in dir(adafruit_fingerprint):
        if not item.startswith('_'):
            obj = getattr(adafruit_fingerprint, item)
            if isinstance(obj, type):
                print(f"  Class: {item}")
            elif callable(obj):
                print(f"  Function: {item}")
            else:
                print(f"  Constant: {item} = {obj}")
    
    # Try to find the fingerprint class
    print("\nLooking for fingerprint class...")
    fingerprint_class = None
    
    for item in dir(adafruit_fingerprint):
        obj = getattr(adafruit_fingerprint, item)
        if (isinstance(obj, type) and 
            hasattr(obj, 'begin') and 
            hasattr(obj, 'get_image')):
            fingerprint_class = obj
            print(f"✓ Found fingerprint class: {item}")
            break
    
    if not fingerprint_class:
        print("✗ No suitable fingerprint class found")
        
except ImportError as e:
    print(f"✗ adafruit_fingerprint import failed: {e}")

# Test 4: Check serial ports
print("\nChecking available serial ports...")
try:
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    if ports:
        print("Available serial ports:")
        for port in ports:
            print(f"  {port.device} - {port.description}")
    else:
        print("No serial ports found")
except Exception as e:
    print(f"Error listing ports: {e}")

# Test 5: Check permissions
print("\nChecking permissions...")
import os
import stat

serial_ports = ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyS0']
for port in serial_ports:
    if os.path.exists(port):
        try:
            port_stat = os.stat(port)
            mode = stat.filemode(port_stat.st_mode)
            print(f"  {port}: {mode}")
        except Exception as e:
            print(f"  {port}: Error checking permissions - {e}")

# Test 6: Check groups
print("\nChecking user groups...")
try:
    import grp
    user_groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
    print(f"User groups: {user_groups}")
    if 'dialout' in user_groups:
        print("✓ User is in dialout group")
    else:
        print("⚠ User is NOT in dialout group")
        print("  Run: sudo usermod -a -G dialout $USER")
        print("  Then reboot or logout/login")
except Exception as e:
    print(f"Error checking groups: {e}")

print("\n" + "=" * 40)
print("Diagnostic complete!")
