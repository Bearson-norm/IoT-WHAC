#!/usr/bin/env python3
"""
Fingerprint Scan Simulator
Simulates a fingerprint scan and sends it to MQTT
Use this to test if the web UI receives the message and shows the modal
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# Configuration
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"

print("=" * 60)
print("Fingerprint Scan Simulator")
print("=" * 60)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
    else:
        print(f"❌ Failed to connect (rc: {rc})")

def on_publish(client, userdata, mid):
    print(f"✅ Message published (mid: {mid})")

# Create MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish

try:
    print(f"\nConnecting to {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    time.sleep(2)
    
    # Simulate different scan scenarios
    scenarios = [
        {
            "name": "Successful Match",
            "data": {
                "store_id": "Store001",
                "timestamp": datetime.now().isoformat(),
                "status": "Match",
                "fingerprint_id": 1,
                "username": "John Doe",
                "confidence": 95,
                "device_id": "AS608_001"
            }
        },
        {
            "name": "No Match",
            "data": {
                "store_id": "Store001",
                "timestamp": datetime.now().isoformat(),
                "status": "Not Match",
                "fingerprint_id": -1,
                "username": None,
                "confidence": 0,
                "device_id": "AS608_001"
            }
        },
        {
            "name": "Different User",
            "data": {
                "store_id": "Store001",
                "timestamp": datetime.now().isoformat(),
                "status": "Match",
                "fingerprint_id": 5,
                "username": "Jane Smith",
                "confidence": 88,
                "device_id": "AS608_001"
            }
        }
    ]
    
    print("\nAvailable test scenarios:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
    
    while True:
        print("\n" + "=" * 60)
        choice = input("Enter scenario number (1-3) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            break
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(scenarios):
                scenario = scenarios[choice_idx]
                
                # Update timestamp to current time
                scenario['data']['timestamp'] = datetime.now().isoformat()
                
                print(f"\n📤 Sending: {scenario['name']}")
                print(f"   Payload: {json.dumps(scenario['data'], indent=2)}")
                
                result = client.publish(MQTT_TOPIC, json.dumps(scenario['data']), qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print("\n✅ Scan simulated successfully!")
                    print("   Check your web UI dashboard - the modal should popup!")
                else:
                    print(f"\n❌ Failed to publish (rc: {result.rc})")
                
                time.sleep(0.5)  # Wait for publish to complete
            else:
                print("❌ Invalid choice. Please enter 1-3.")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q'.")
    
except KeyboardInterrupt:
    print("\n\n⚠️  Stopped by user")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    client.loop_stop()
    client.disconnect()
    print("\n👋 Simulator stopped")


