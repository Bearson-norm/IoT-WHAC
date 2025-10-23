#!/usr/bin/env python3
"""
Quick test script for AS608 sensor connection
Run this on Raspberry Pi to test sensor before enrollment
"""

import serial
import time
import sys
import os

def test_sensor_quick():
    """Quick sensor connection test"""
    print("🔍 Quick AS608 Sensor Test")
    print("=" * 40)
    
    # Try common ports
    ports_to_try = [
        "/dev/ttyUSB0",
        "/dev/ttyUSB1", 
        "/dev/ttyACM0",
        "/dev/ttyACM1"
    ]
    
    for port in ports_to_try:
        if not os.path.exists(port):
            continue
            
        print(f"\n🔌 Testing {port}...")
        
        try:
            # Fix permissions
            os.system(f"sudo chmod 666 {port}")
            
            # Try to connect
            ser = serial.Serial(port, baudrate=57600, timeout=2)
            time.sleep(0.5)
            
            print(f"✅ Connected to {port}")
            
            # Try to import and test adafruit library
            try:
                import adafruit_fingerprint
                finger = adafruit_fingerprint.Adafruit_Fingerprint(ser)
                
                # Test read templates
                result = finger.read_templates()
                if result == adafruit_fingerprint.OK:
                    print(f"✅ AS608 sensor working! Templates: {finger.template_count}")
                    ser.close()
                    return port
                else:
                    print(f"❌ AS608 error: {result}")
                    
            except ImportError:
                print("❌ adafruit_fingerprint not installed")
            except Exception as e:
                print(f"❌ Sensor test error: {e}")
            
            ser.close()
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    print("\n❌ No working AS608 sensor found!")
    return None

if __name__ == "__main__":
    working_port = test_sensor_quick()
    if working_port:
        print(f"\n🎉 Use this port: {working_port}")
    else:
        print("\n💡 Check sensor power and connections!")
