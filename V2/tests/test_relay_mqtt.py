#!/usr/bin/env python3
"""
Test script for MQTT relay command functionality
This script tests the MQTT connection and relay command sending
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# MQTT configuration (same as web_ui/app.py)
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_ACTION_TOPIC = "WHAC/Store001/action"

def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    if rc == 0:
        print("✅ MQTT client connected successfully")
    else:
        print(f"❌ MQTT connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    """MQTT disconnection callback"""
    print(f"⚠️  MQTT client disconnected (code: {rc})")

def test_relay_command():
    """Test sending relay command via MQTT"""
    try:
        # Create MQTT client
        client = mqtt.Client(client_id="test_relay_client", clean_session=True)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        
        print(f"🔌 Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Wait for connection
        time.sleep(2)
        
        if not client.is_connected():
            print("❌ Failed to connect to MQTT broker")
            return False
        
        # Test payload
        payload = {
            'command': 'grant',
            'user_id': 999,
            'action': 'test_access',
            'timestamp': datetime.now().isoformat(),
            'source': 'test_script'
        }
        
        print(f"📤 Sending test relay command...")
        print(f"📤 Topic: {MQTT_ACTION_TOPIC}")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        # Send command
        result = client.publish(MQTT_ACTION_TOPIC, json.dumps(payload), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("✅ Relay command sent successfully!")
            print("✅ Check your Raspberry Pi relay controller for the command")
            return True
        else:
            print(f"❌ Failed to send relay command (rc: {result.rc})")
            return False
            
    except Exception as e:
        print(f"❌ Error testing relay command: {e}")
        return False
    finally:
        if 'client' in locals():
            client.loop_stop()
            client.disconnect()
            print("🔌 MQTT client disconnected")

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 MQTT RELAY COMMAND TEST")
    print("=" * 60)
    print(f"🎯 Target: Raspberry Pi Relay Controller")
    print(f"🌐 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"📡 Topic: {MQTT_ACTION_TOPIC}")
    print("=" * 60)
    
    success = test_relay_command()
    
    print("=" * 60)
    if success:
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("✅ If your Raspberry Pi relay controller is running,")
        print("✅ you should see the relay activate for 3 seconds")
    else:
        print("❌ TEST FAILED")
        print("❌ Check your MQTT broker connection and Raspberry Pi setup")
    print("=" * 60)

if __name__ == "__main__":
    main()

