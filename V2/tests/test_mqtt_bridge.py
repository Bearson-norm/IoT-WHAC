#!/usr/bin/env python3
"""
MQTT Bridge Diagnostic Tool
Tests the connection between fingerprint scanner and web UI
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import sys

# Configuration
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"
MQTT_ACTION_TOPIC = "WHAC/Store001/action"

print("=" * 60)
print("WHAC MQTT Bridge Diagnostic Tool")
print("=" * 60)

# Test 1: MQTT Broker Connection
print("\n[Test 1] Testing MQTT Broker Connection...")
print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")

test_client = mqtt.Client()
connection_success = False

def on_connect(client, userdata, flags, rc):
    global connection_success
    if rc == 0:
        print("✅ Successfully connected to MQTT broker!")
        connection_success = True
    else:
        print(f"❌ Failed to connect to MQTT broker (rc: {rc})")
        if rc == 1:
            print("   Error: Connection refused - incorrect protocol version")
        elif rc == 2:
            print("   Error: Connection refused - invalid client identifier")
        elif rc == 3:
            print("   Error: Connection refused - server unavailable")
        elif rc == 4:
            print("   Error: Connection refused - bad username or password")
        elif rc == 5:
            print("   Error: Connection refused - not authorized")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"⚠️  Unexpected disconnection from MQTT broker (rc: {rc})")

def on_message(client, userdata, msg):
    print(f"\n📥 Received message on topic: {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"   Payload: {json.dumps(payload, indent=2)}")
    except:
        print(f"   Payload (raw): {msg.payload.decode()}")

test_client.on_connect = on_connect
test_client.on_disconnect = on_disconnect
test_client.on_message = on_message

try:
    print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
    test_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    test_client.loop_start()
    time.sleep(2)  # Wait for connection
    
    if not connection_success:
        print("\n❌ CRITICAL: Cannot connect to MQTT broker!")
        print("   Possible issues:")
        print("   1. MQTT broker is not running")
        print("   2. Firewall blocking connection")
        print("   3. Incorrect broker address")
        print("   4. Network connectivity issues")
        sys.exit(1)
    
    # Test 2: Subscribe to scan topic
    print(f"\n[Test 2] Subscribing to topic: {MQTT_TOPIC}")
    test_client.subscribe(MQTT_TOPIC)
    print("✅ Subscribed successfully")
    
    # Also subscribe to action topic
    print(f"         Subscribing to topic: {MQTT_ACTION_TOPIC}")
    test_client.subscribe(MQTT_ACTION_TOPIC)
    print("✅ Subscribed successfully")
    
    # Test 3: Publish test scan message
    print(f"\n[Test 3] Publishing test scan message to: {MQTT_TOPIC}")
    test_scan = {
        "store_id": "Store001",
        "timestamp": datetime.now().isoformat(),
        "status": "Match",
        "fingerprint_id": 1,
        "username": "Test User",
        "confidence": 85,
        "device_id": "TEST_DEVICE"
    }
    
    result = test_client.publish(MQTT_TOPIC, json.dumps(test_scan), qos=1)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("✅ Test message published successfully!")
        print(f"   Message: {json.dumps(test_scan, indent=2)}")
    else:
        print(f"❌ Failed to publish message (rc: {result.rc})")
    
    # Wait for message to loop back
    print("\n⏳ Waiting 3 seconds to receive the message back...")
    time.sleep(3)
    
    # Test 4: Instructions for next steps
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("\n1. Keep this script running in one terminal")
    print("2. In another terminal, run the fingerprint client:")
    print("   cd local_machine")
    print("   python fingerprint_simple_client.py")
    print("\n3. In a third terminal, run the web UI:")
    print("   cd web_ui")
    print("   python app.py")
    print("\n4. When you scan a fingerprint, you should see:")
    print("   - Message received in THIS terminal")
    print("   - Log message in fingerprint client terminal")
    print("   - Log message in web UI terminal")
    print("   - Popup modal in web browser")
    print("\n" + "=" * 60)
    print("Listening for MQTT messages... (Press Ctrl+C to exit)")
    print("=" * 60)
    
    # Keep listening
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n⚠️  Stopped by user")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    test_client.loop_stop()
    test_client.disconnect()
    print("\n👋 Diagnostic tool stopped")


