#!/usr/bin/env python3
"""
Debug script to test AS608 fingerprint sensor connection
Run this on the Raspberry Pi to diagnose connection issues
"""

import serial
import time
import glob
import os
import sys

def list_serial_ports():
    """List all available serial ports"""
    print("=" * 60)
    print("AVAILABLE SERIAL PORTS")
    print("=" * 60)
    
    if os.name == 'posix':  # Linux/Unix (Raspberry Pi)
        # Check USB serial patterns
        usb_patterns = ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/tty.usbserial*']
        for pattern in usb_patterns:
            found_ports = glob.glob(pattern)
            if found_ports:
                print(f"USB ports ({pattern}): {found_ports}")
        
        # Check built-in serial ports
        builtin_patterns = ['/dev/ttyS*', '/dev/ttyAMA*', '/dev/serial0', '/dev/serial1']
        for pattern in builtin_patterns:
            if pattern.startswith('/dev/serial'):
                if os.path.exists(pattern):
                    print(f"Serial port: {pattern}")
            else:
                found_ports = glob.glob(pattern)
                if found_ports:
                    print(f"Built-in ports ({pattern}): {found_ports}")
    else:
        print("This script is designed for Linux/Raspberry Pi")

def test_port_connection(port, baudrate=57600):
    """Test connection to a specific port"""
    print(f"\n🔌 Testing port: {port}")
    
    try:
        # Check if port exists
        if not os.path.exists(port):
            print(f"❌ Port {port} does not exist")
            return False
        
        # Check permissions
        if not os.access(port, os.R_OK | os.W_OK):
            print(f"❌ No read/write permission on {port}")
            print(f"💡 Try: sudo chmod 666 {port}")
            return False
        
        print(f"✅ Port {port} exists and is accessible")
        
        # Try to open serial connection
        print(f"🔗 Opening serial connection at {baudrate} baud...")
        ser = serial.Serial(port, baudrate=baudrate, timeout=2)
        time.sleep(0.5)
        
        print(f"✅ Serial connection opened successfully")
        
        # Try to read some data
        print(f"📖 Attempting to read data...")
        try:
            data = ser.read(10)  # Try to read 10 bytes
            print(f"📊 Read {len(data)} bytes: {data}")
        except Exception as e:
            print(f"⚠️  Read error: {e}")
        
        # Close connection
        ser.close()
        print(f"✅ Connection closed successfully")
        return True
        
    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
        return False
    except Exception as e:
        print(f"❌ General error: {e}")
        return False

def test_adafruit_fingerprint(port, baudrate=57600):
    """Test AS608 sensor with adafruit_fingerprint library"""
    print(f"\n👆 Testing AS608 sensor on {port}")
    
    try:
        import adafruit_fingerprint
        
        # Open serial connection
        ser = serial.Serial(port, baudrate=baudrate, timeout=2)
        time.sleep(0.5)
        
        # Create fingerprint object
        finger = adafruit_fingerprint.Adafruit_Fingerprint(ser)
        
        # Try to read templates
        print("📋 Attempting to read templates...")
        result = finger.read_templates()
        
        if result == adafruit_fingerprint.OK:
            print(f"✅ AS608 sensor working! Templates: {finger.template_count}")
            ser.close()
            return True
        else:
            print(f"❌ AS608 sensor error: {result}")
            ser.close()
            return False
            
    except ImportError:
        print("❌ adafruit_fingerprint library not installed")
        print("💡 Install with: pip3 install adafruit-circuitpython-fingerprint")
        return False
    except Exception as e:
        print(f"❌ AS608 test error: {e}")
        return False

def main():
    """Main debug function"""
    print("🔍 AS608 FINGERPRINT SENSOR DEBUG")
    print("=" * 60)
    
    # List available ports
    list_serial_ports()
    
    # Common AS608 ports to test
    common_ports = [
        "/dev/ttyUSB0",
        "/dev/ttyUSB1", 
        "/dev/ttyACM0",
        "/dev/ttyACM1",
        "/dev/serial0",
        "/dev/serial1"
    ]
    
    print("\n" + "=" * 60)
    print("TESTING COMMON AS608 PORTS")
    print("=" * 60)
    
    working_ports = []
    
    for port in common_ports:
        if test_port_connection(port):
            working_ports.append(port)
    
    if not working_ports:
        print("\n❌ No working serial ports found!")
        print("\n💡 Troubleshooting steps:")
        print("1. Check AS608 sensor is powered on (LED should be on)")
        print("2. Check USB cable connection")
        print("3. Try different USB port on Raspberry Pi")
        print("4. Check if sensor is recognized: lsusb")
        print("5. Check permissions: sudo chmod 666 /dev/ttyUSB0")
        return
    
    print(f"\n✅ Working ports: {working_ports}")
    
    # Test AS608 sensor on working ports
    print("\n" + "=" * 60)
    print("TESTING AS608 SENSOR")
    print("=" * 60)
    
    as608_found = False
    for port in working_ports:
        if test_adafruit_fingerprint(port):
            as608_found = True
            print(f"\n🎉 AS608 sensor found on {port}!")
            print(f"💡 Use this port in your config: FINGERPRINT_PORT = '{port}'")
            break
    
    if not as608_found:
        print("\n❌ AS608 sensor not found on any working port!")
        print("\n💡 Possible issues:")
        print("1. AS608 sensor not connected or powered")
        print("2. Wrong baud rate (try 9600, 19200, 38400, 57600, 115200)")
        print("3. Sensor malfunction")
        print("4. Wrong library version")
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
