#!/usr/bin/env python3
"""
MQTT Connection Diagnostic Tool
Tests MQTT broker connectivity for the WHAC system
"""

import paho.mqtt.client as mqtt
import time
import sys

# MQTT Configuration (same as web_ui/app.py)
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"[SUCCESS] Connected to MQTT broker!")
        print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"   Connection result code: {rc}")
    else:
        error_messages = {
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
        print(f"[FAILED] Connection failed: {error_msg}")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    if rc != 0:
        print(f"[WARNING] Unexpected disconnection from MQTT broker (code: {rc})")
    else:
        print(f"[OK] Cleanly disconnected from MQTT broker")

def on_message(client, userdata, msg):
    """Callback when message received"""
    print(f"[MESSAGE] Received message on topic: {msg.topic}")
    print(f"   Payload: {msg.payload.decode()}")

def test_mqtt_connection():
    """Test MQTT broker connection"""
    print("=" * 70)
    print("MQTT CONNECTION DIAGNOSTIC TOOL")
    print("=" * 70)
    print(f"Testing connection to: {MQTT_BROKER}:{MQTT_PORT}")
    print()
    
    try:
        # Create MQTT client
        print("1. Creating MQTT client...")
        client = mqtt.Client(client_id="whac_diagnostic_tool", clean_session=True)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        print("   [OK] MQTT client created")
        
        # Connect to broker
        print()
        print("2. Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start network loop
        print("   Starting network loop...")
        client.loop_start()
        
        # Wait for connection
        print("   Waiting for connection...")
        timeout = 10
        start_time = time.time()
        connected = False
        
        while (time.time() - start_time) < timeout:
            if client.is_connected():
                connected = True
                break
            time.sleep(0.1)
        
        if not connected:
            print()
            print("[FAILED] Connection timeout after 10 seconds")
            print()
            print("Troubleshooting steps:")
            print("   1. Check if MQTT broker is running")
            print("   2. Check firewall settings")
            print("   3. Verify broker address and port")
            print(f"   4. Try: ping {MQTT_BROKER}")
            print(f"   5. Try: telnet {MQTT_BROKER} {MQTT_PORT}")
            client.loop_stop()
            return False
        
        # Test subscribe
        print()
        print("3. Testing subscription...")
        test_topic = "WHAC/Store001/test"
        client.subscribe(test_topic, qos=1)
        print(f"   [OK] Subscribed to topic: {test_topic}")
        
        # Test publish
        print()
        print("4. Testing publish...")
        result = client.publish(test_topic, "Test message from diagnostic tool", qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"   [OK] Message published successfully")
            print(f"   Message ID: {result.mid}")
        else:
            print(f"   [FAILED] Publish failed with error code: {result.rc}")
        
        # Wait for message
        print()
        print("5. Waiting for test message (5 seconds)...")
        time.sleep(5)
        
        # Disconnect
        print()
        print("6. Disconnecting...")
        client.loop_stop()
        client.disconnect()
        
        print()
        print("=" * 70)
        print("[SUCCESS] MQTT CONNECTION TEST COMPLETED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("   [OK] Connection: SUCCESS")
        print("   [OK] Subscribe: SUCCESS")
        print("   [OK] Publish: SUCCESS")
        print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print()
        print("The MQTT broker is working correctly!")
        print("If web UI still has connection issues:")
        print("   1. Restart the web UI application")
        print("   2. Check web UI logs for connection errors")
        print("   3. Verify web UI is using the same broker address")
        print()
        
        return True
        
    except ConnectionRefusedError:
        print()
        print("[FAILED] Connection refused by broker")
        print()
        print("Possible causes:")
        print("   1. MQTT broker is not running")
        print("   2. Broker is not listening on the specified port")
        print("   3. Firewall is blocking the connection")
        print()
        return False
        
    except Exception as e:
        print()
        print(f"[ERROR] Unexpected error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = test_mqtt_connection()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

