#!/usr/bin/env python3
"""
Quick Test Script
Tests if the MQTT bridge between fingerprint scanner and web UI is working
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import sys

MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"

print("\n" + "="*70)
print("  WHAC FINGERPRINT SYSTEM - QUICK CONNECTION TEST")
print("="*70)

# Step 1: Test MQTT Connection
print("\n[1/4] Testing MQTT broker connection...")
print(f"      Connecting to {MQTT_BROKER}:{MQTT_PORT}...")

connected = False

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        connected = True

client = mqtt.Client()
client.on_connect = on_connect

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    time.sleep(2)
    
    if connected:
        print("      ✅ MQTT broker connection: SUCCESS")
    else:
        print("      ❌ MQTT broker connection: FAILED")
        print("\n      💡 TIP: Make sure MQTT broker is running at", MQTT_BROKER)
        print("      Run: mosquitto -v  (if broker is local)")
        sys.exit(1)
    
    # Step 2: Test publish
    print("\n[2/4] Testing MQTT publish...")
    test_data = {
        "store_id": "Store001",
        "timestamp": datetime.now().isoformat(),
        "status": "Match",
        "fingerprint_id": 999,
        "username": "Quick Test User",
        "confidence": 100,
        "device_id": "QUICK_TEST"
    }
    
    result = client.publish(MQTT_TOPIC, json.dumps(test_data), qos=1)
    if result.rc == 0:
        print("      ✅ MQTT publish: SUCCESS")
    else:
        print(f"      ❌ MQTT publish: FAILED (rc={result.rc})")
    
    # Step 3: Instructions
    print("\n[3/4] Checking web UI...")
    print("      ⚠️  Make sure web UI is running!")
    print("      Run in another terminal: cd web_ui && python app.py")
    
    print("\n[4/4] Next steps...")
    print("      1. Open browser: http://localhost:5000")
    print("      2. Login to dashboard")
    print("      3. Keep this window open")
    print("      4. Press ENTER to send a test scan...")
    
    input()
    
    print("\n📤 Sending test fingerprint scan...")
    test_scan = {
        "store_id": "Store001",
        "timestamp": datetime.now().isoformat(),
        "status": "Match",
        "fingerprint_id": 1,
        "username": "Test User",
        "confidence": 95,
        "device_id": "AS608_001"
    }
    
    client.publish(MQTT_TOPIC, json.dumps(test_scan), qos=1)
    print("✅ Test scan sent!")
    print("\n" + "="*70)
    print("CHECK YOUR BROWSER - THE MODAL SHOULD POPUP NOW!")
    print("="*70)
    print("\nIf modal appeared: ✅ Everything is working!")
    print("If modal didn't appear: ❌ Check browser console (F12)")
    print("\nPress Ctrl+C to exit, or press ENTER to send another test scan...")
    
    while True:
        input()
        print("\n📤 Sending another test scan...")
        test_scan["timestamp"] = datetime.now().isoformat()
        test_scan["fingerprint_id"] = (test_scan["fingerprint_id"] % 10) + 1
        client.publish(MQTT_TOPIC, json.dumps(test_scan), qos=1)
        print("✅ Test scan sent! Check your browser...")
        print("Press ENTER for another, or Ctrl+C to exit...")

except KeyboardInterrupt:
    print("\n\n👋 Test stopped")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    client.loop_stop()
    client.disconnect()

print("\n" + "="*70)
print("For detailed testing, run: python test_mqtt_bridge.py")
print("To simulate scans, run: python simulate_fingerprint_scan.py")
print("For help, see: BRIDGE_TESTING_GUIDE.md")
print("="*70 + "\n")


