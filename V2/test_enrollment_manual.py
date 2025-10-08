#!/usr/bin/env python3
"""
Manual test for enrollment functionality
Run this on Raspberry Pi to test enrollment directly
"""

import serial
import adafruit_fingerprint
import time
import json
import paho.mqtt.client as mqtt

def test_enrollment():
    """Test enrollment functionality"""
    print("🔍 Testing Enrollment Functionality")
    print("=" * 50)
    
    # Connect to sensor
    print("Connecting to AS608 sensor...")
    try:
        uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=2)
        time.sleep(0.5)
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        print("✓ Sensor connected!")
    except Exception as e:
        print(f"❌ Sensor connection failed: {e}")
        return False
    
    # Test enrollment
    print("\n🖐️  Testing fingerprint enrollment...")
    print("Place finger on sensor for first scan...")
    
    try:
        # First scan
        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                break
            if i == adafruit_fingerprint.NOFINGER:
                continue
            else:
                print(f"❌ Error getting first image: {i}")
                return False
        
        print("✓ First image captured!")
        
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("❌ Error converting first image")
            return False
        
        print("Remove finger...")
        time.sleep(2)
        
        while finger.get_image() != adafruit_fingerprint.NOFINGER:
            pass
        
        print("Place same finger again for second scan...")
        
        # Second scan
        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                break
            if i == adafruit_fingerprint.NOFINGER:
                continue
            else:
                print(f"❌ Error getting second image: {i}")
                return False
        
        print("✓ Second image captured!")
        
        if finger.image_2_tz(2) != adafruit_fingerprint.OK:
            print("❌ Error converting second image")
            return False
        
        print("Creating model...")
        if finger.create_model() != adafruit_fingerprint.OK:
            print("❌ Error creating model - fingers didn't match?")
            return False
        
        print("Storing model at location 99...")
        if finger.store_model(99) != adafruit_fingerprint.OK:
            print("❌ Error storing model")
            return False
        
        print("✓ Fingerprint enrolled successfully at location 99!")
        
        # Test recognition
        print("\n🔍 Testing recognition...")
        print("Place same finger on sensor...")
        
        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                break
            if i == adafruit_fingerprint.NOFINGER:
                continue
            else:
                print(f"❌ Error getting image: {i}")
                return False
        
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("❌ Error processing image")
            return False
        
        i = finger.finger_search()
        if i == adafruit_fingerprint.OK:
            print(f"✓ Match found! ID: {finger.finger_id}, Confidence: {finger.confidence}")
            return True
        else:
            print("❌ No match found")
            return False
            
    except Exception as e:
        print(f"❌ Enrollment test failed: {e}")
        return False
    finally:
        uart.close()

def test_mqtt_enrollment():
    """Test MQTT enrollment command"""
    print("\n📡 Testing MQTT Enrollment Command")
    print("=" * 50)
    
    try:
        # Create MQTT client
        client = mqtt.Client()
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("✓ MQTT connected!")
                # Send test enrollment command
                command = {
                    "fingerprint_id": 98,
                    "user_name": "MQTT Test User",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "source": "test_script"
                }
                result = client.publish("WHAC/Store001/add_user", json.dumps(command))
                print(f"📤 Sent enrollment command: {command}")
                print(f"📡 Publish result: {result.rc}")
            else:
                print(f"❌ MQTT connection failed: {rc}")
        
        def on_message(client, userdata, msg):
            print(f"📥 Received: {msg.topic} - {msg.payload.decode()}")
        
        client.on_connect = on_connect
        client.on_message = on_message
        
        # Connect and send command
        client.connect("103.87.67.139", 1883, 60)
        client.loop_start()
        
        # Wait for response
        time.sleep(5)
        
        client.loop_stop()
        client.disconnect()
        
    except Exception as e:
        print(f"❌ MQTT test failed: {e}")

if __name__ == "__main__":
    print("🧪 ENROLLMENT FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test 1: Direct sensor enrollment
    if test_enrollment():
        print("\n✅ Direct enrollment test PASSED!")
    else:
        print("\n❌ Direct enrollment test FAILED!")
    
    # Test 2: MQTT enrollment command
    test_mqtt_enrollment()
    
    print("\n" + "=" * 60)
    print("Test completed!")
