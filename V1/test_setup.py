#!/usr/bin/env python3
"""
Test script to verify the setup of Fingerprint MQTT Client
Run this to check if all components are working correctly
"""

import sys
import time
import json
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import paho.mqtt.client as mqtt
        print("✓ paho-mqtt imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import paho-mqtt: {e}")
        return False
    
    try:
        import serial
        print("✓ pyserial imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyserial: {e}")
        return False
    
    try:
        from adafruit_fingerprint import AdafruitFingerprint
        print("✓ adafruit-fingerprint imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import adafruit-fingerprint: {e}")
        return False
    
    try:
        from config import *
        print("✓ config imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config: {e}")
        return False
    
    return True

def test_mqtt_connection():
    """Test MQTT connection"""
    print("\nTesting MQTT connection...")
    
    try:
        import paho.mqtt.client as mqtt
        from config import MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE
        
        client = mqtt.Client()
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("✓ MQTT connection successful")
                client.disconnect()
            else:
                print(f"✗ MQTT connection failed with code: {rc}")
        
        def on_disconnect(client, userdata, rc):
            print("MQTT test completed")
        
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        
        print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        client.loop_start()
        
        # Wait for connection
        time.sleep(3)
        
        if not client.is_connected():
            print("✗ MQTT connection timeout")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ MQTT connection test failed: {e}")
        return False

def test_fingerprint_sensor():
    """Test fingerprint sensor connection"""
    print("\nTesting fingerprint sensor...")
    
    try:
        import serial
        from adafruit_fingerprint import AdafruitFingerprint
        from config import FINGERPRINT_PORT, BAUD_RATE
        
        print(f"Trying to connect to {FINGERPRINT_PORT} at {BAUD_RATE} baud...")
        
        # Try to create serial connection
        uart = serial.Serial(FINGERPRINT_PORT, baudrate=BAUD_RATE, timeout=1)
        fingerprint = AdafruitFingerprint(uart)
        
        if fingerprint.begin():
            print("✓ Fingerprint sensor connected successfully")
            
            # Test basic functionality
            print("Testing sensor functionality...")
            result = fingerprint.get_image()
            if result == fingerprint.OK:
                print("✓ Sensor can capture images")
            else:
                print(f"⚠ Sensor image capture test: {result}")
            
            uart.close()
            return True
        else:
            print("✗ Failed to initialize fingerprint sensor")
            uart.close()
            return False
            
    except FileNotFoundError:
        print(f"✗ Device {FINGERPRINT_PORT} not found")
        print("Please check your fingerprint sensor connection")
        return False
    except PermissionError:
        print(f"✗ Permission denied for {FINGERPRINT_PORT}")
        print("Make sure your user is in the dialout group:")
        print("sudo usermod -a -G dialout $USER")
        return False
    except Exception as e:
        print(f"✗ Fingerprint sensor test failed: {e}")
        return False

def test_json_payload():
    """Test JSON payload format"""
    print("\nTesting JSON payload format...")
    
    try:
        from config import STORE_ID
        
        # Create test payload
        payload = {
            "store_id": STORE_ID,
            "finger_id": 123,
            "Timestamp": datetime.now().isoformat()
        }
        
        # Test JSON serialization
        message = json.dumps(payload)
        print("✓ JSON payload created successfully")
        print(f"Sample payload: {message}")
        
        # Test JSON deserialization
        parsed = json.loads(message)
        if parsed["store_id"] == STORE_ID and parsed["finger_id"] == 123:
            print("✓ JSON payload parsing successful")
            return True
        else:
            print("✗ JSON payload parsing failed")
            return False
            
    except Exception as e:
        print(f"✗ JSON payload test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Fingerprint MQTT Client Setup Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("MQTT Connection Test", test_mqtt_connection),
        ("Fingerprint Sensor Test", test_fingerprint_sensor),
        ("JSON Payload Test", test_json_payload)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! Your setup is ready.")
        print("You can now run: python3 fingerprint_mqtt_client.py")
    else:
        print("✗ Some tests failed. Please check the issues above.")
        print("Refer to the README.md for troubleshooting steps.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
