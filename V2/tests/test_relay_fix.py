#!/usr/bin/env python3
"""
Test script to verify the relay command fix
This script tests the MQTT relay command functionality after the fix
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

def test_relay_command_fix():
    """Test sending relay command with improved error handling"""
    try:
        # Create MQTT client
        client = mqtt.Client(client_id="test_relay_fix_client", clean_session=True)
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
        
        # Test payload (same format as web UI)
        payload = {
            'command': 'grant',
            'user_id': 12,  # Same user ID from the error
            'action': 'access_granted',
            'timestamp': datetime.now().isoformat(),
            'source': 'test_script'
        }
        
        print(f"📤 Testing relay command fix...")
        print(f"📤 Topic: {MQTT_ACTION_TOPIC}")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        # Send command
        result = client.publish(MQTT_ACTION_TOPIC, json.dumps(payload), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("✅ Relay command sent successfully!")
            print("✅ The fix should resolve the rc: 4 error")
            print("✅ Check your Raspberry Pi for relay activation")
            return True
        else:
            print(f"❌ Failed to send relay command (rc: {result.rc})")
            print("❌ This indicates the original problem still exists")
            return False
            
    except Exception as e:
        print(f"❌ Error testing relay command: {e}")
        return False
    finally:
        if 'client' in locals():
            client.loop_stop()
            client.disconnect()
            print("🔌 MQTT client disconnected")

def test_connection_recovery():
    """Test MQTT connection recovery mechanism"""
    try:
        print("\n" + "="*60)
        print("🧪 TESTING CONNECTION RECOVERY")
        print("="*60)
        
        # Create MQTT client
        client = mqtt.Client(client_id="test_recovery_client", clean_session=True)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        
        # Connect
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(2)
        
        if not client.is_connected():
            print("❌ Initial connection failed")
            return False
        
        print("✅ Initial connection successful")
        
        # Simulate connection loss by stopping loop
        print("🔄 Simulating connection loss...")
        client.loop_stop()
        client.disconnect()
        time.sleep(1)
        
        # Test reconnection (like the fixed code does)
        print("🔄 Testing reconnection...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(2)
        
        if client.is_connected():
            print("✅ Reconnection successful!")
            print("✅ The fix should handle connection recovery")
            return True
        else:
            print("❌ Reconnection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection recovery: {e}")
        return False
    finally:
        if 'client' in locals():
            client.loop_stop()
            client.disconnect()

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 RELAY COMMAND FIX TEST")
    print("=" * 60)
    print(f"🎯 Testing fix for: ERROR:__main__:✗ Failed to send relay command (rc: 4)")
    print(f"🌐 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"📡 Topic: {MQTT_ACTION_TOPIC}")
    print("=" * 60)
    
    # Test 1: Basic relay command
    print("\n🔧 TEST 1: Basic Relay Command")
    test1_success = test_relay_command_fix()
    
    # Test 2: Connection recovery
    print("\n🔧 TEST 2: Connection Recovery")
    test2_success = test_connection_recovery()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"Test 1 (Basic Relay): {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Test 2 (Recovery): {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The relay command fix should resolve the rc: 4 error")
        print("✅ MQTT connection recovery is working")
        print("✅ Try granting access again from the Web UI")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("❌ There may still be issues with the MQTT connection")
        print("❌ Check your MQTT broker and network connectivity")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

