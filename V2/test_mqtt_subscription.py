#!/usr/bin/env python3
"""
Test MQTT subscription to verify enrollment commands are received
"""

import paho.mqtt.client as mqtt
import json
import time

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ MQTT connected!")
        # Subscribe to enrollment topic
        client.subscribe("WHAC/Store001/add_user", qos=1)
        print("✓ Subscribed to WHAC/Store001/add_user")
    else:
        print(f"❌ MQTT connection failed: {rc}")

def on_message(client, userdata, msg):
    print(f"📥 Received message on {msg.topic}:")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"   📦 Payload: {payload}")
    except:
        print(f"   📦 Raw: {msg.payload.decode()}")

def on_disconnect(client, userdata, rc):
    print(f"📡 MQTT disconnected: {rc}")

def main():
    print("🔍 Testing MQTT Subscription")
    print("=" * 40)
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to broker
        print("Connecting to MQTT broker...")
        client.connect("103.87.67.139", 1883, 60)
        client.loop_start()
        
        print("⏳ Listening for enrollment commands...")
        print("💡 Now try enrolling a user from the web UI!")
        print("💡 Or run the test script to send a command")
        print("💡 Press Ctrl+C to stop")
        
        # Keep listening
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("✓ Disconnected")

if __name__ == "__main__":
    main()
