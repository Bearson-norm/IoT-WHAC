#!/usr/bin/env python3
"""
System Status Checker for WHAC Fingerprint System
Checks if all components are running and connected
"""

import requests
import paho.mqtt.client as mqtt
import time
import json

MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
WEB_UI_URL = "http://localhost:5000"

def check_web_ui():
    """Check if Web UI is running"""
    print("\n1. Checking Web UI...")
    try:
        response = requests.get(f"{WEB_UI_URL}/", timeout=5)
        if response.status_code == 200:
            print("   [OK] Web UI is running")
            return True
        else:
            print(f"   [FAILED] Web UI returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   [FAILED] Web UI is not running")
        print("   Solution: cd web_ui && python app.py")
        return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

def check_web_ui_mqtt():
    """Check Web UI MQTT connection"""
    print("\n2. Checking Web UI MQTT connection...")
    try:
        response = requests.get(f"{WEB_UI_URL}/api/mqtt_status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('connected'):
                print(f"   [OK] Web UI MQTT connected to {data.get('broker')}")
                return True
            else:
                print(f"   [FAILED] Web UI MQTT not connected")
                print(f"   Broker: {data.get('broker')}")
                print(f"   Error: {data.get('error', 'Unknown')}")
                return False
        else:
            print(f"   [FAILED] Could not check MQTT status")
            return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

def check_mqtt_broker():
    """Check if MQTT broker is accessible"""
    print("\n3. Checking MQTT Broker...")
    try:
        client = mqtt.Client(client_id="status_checker", clean_session=True)
        connected = False
        
        def on_connect(c, userdata, flags, rc):
            nonlocal connected
            connected = (rc == 0)
        
        client.on_connect = on_connect
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Wait for connection
        timeout = 5
        start_time = time.time()
        while not connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        if connected:
            print(f"   [OK] MQTT Broker accessible at {MQTT_BROKER}:{MQTT_PORT}")
            return True
        else:
            print(f"   [FAILED] Could not connect to MQTT Broker")
            print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
            return False
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

def check_local_machine():
    """Check if local machine is publishing"""
    print("\n4. Checking Local Machine Client...")
    print("   Listening for scan messages for 5 seconds...")
    
    messages_received = []
    
    def on_message(client, userdata, msg):
        messages_received.append(msg.topic)
        print(f"   [MESSAGE] Received on: {msg.topic}")
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("WHAC/Store001/#", qos=1)
    
    try:
        client = mqtt.Client(client_id="local_machine_checker", clean_session=True)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Listen for 5 seconds
        time.sleep(5)
        
        client.loop_stop()
        client.disconnect()
        
        if "WHAC/Store001/in" in messages_received:
            print(f"   [OK] Local machine is sending scan data")
            return True
        else:
            print(f"   [WARNING] No scan messages received from local machine")
            print(f"   This could mean:")
            print(f"   - Local machine client is not running")
            print(f"   - No fingerprints were scanned in last 5 seconds")
            print(f"   Solution: cd local_machine && python3 fingerprint_simple_client.py")
            return False
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

def test_enrollment_subscription():
    """Check if anyone is subscribed to enrollment topic"""
    print("\n5. Testing Enrollment Topic Subscription...")
    print("   Publishing test message to WHAC/Store001/add_user...")
    
    response_received = False
    
    def on_message(client, userdata, msg):
        nonlocal response_received
        if "add_user_response" in msg.topic:
            response_received = True
            print(f"   [OK] Received response on: {msg.topic}")
            data = json.loads(msg.payload.decode())
            print(f"   Response: {data}")
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("WHAC/Store001/add_user_response", qos=1)
    
    try:
        client = mqtt.Client(client_id="enrollment_tester", clean_session=True)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        time.sleep(1)
        
        # Send test enrollment command
        test_payload = {
            'fingerprint_id': 999,
            'user_name': 'Test User',
            'timestamp': '2025-10-13T00:00:00',
            'source': 'status_checker'
        }
        
        result = client.publish('WHAC/Store001/add_user', json.dumps(test_payload), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"   Test message published successfully")
        else:
            print(f"   [FAILED] Could not publish test message (rc: {result.rc})")
        
        # Wait for response
        print("   Waiting for response (10 seconds)...")
        time.sleep(10)
        
        client.loop_stop()
        client.disconnect()
        
        if response_received:
            print(f"   [OK] Local machine responded to enrollment command")
            return True
        else:
            print(f"   [FAILED] No response from local machine")
            print(f"   This means local machine client is NOT running or NOT subscribed")
            print(f"   Solution: Start local machine client!")
            return False
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

def main():
    """Main function"""
    print("=" * 70)
    print("WHAC FINGERPRINT SYSTEM - STATUS CHECK")
    print("=" * 70)
    
    results = []
    
    # Check all components
    results.append(("Web UI", check_web_ui()))
    results.append(("Web UI MQTT", check_web_ui_mqtt()))
    results.append(("MQTT Broker", check_mqtt_broker()))
    results.append(("Local Machine", check_local_machine()))
    results.append(("Enrollment Topic", test_enrollment_subscription()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for component, status in results:
        status_text = "[OK]" if status else "[FAILED]"
        print(f"{status_text} {component}")
    
    all_ok = all(status for _, status in results)
    
    print("\n" + "=" * 70)
    if all_ok:
        print("[SUCCESS] All components are working!")
        print("=" * 70)
        print("\nYou can now try enrollment from the Web UI")
    else:
        print("[FAILED] Some components are not working")
        print("=" * 70)
        print("\nMost likely issue: Local machine client is NOT running")
        print("\nSolution:")
        print("1. On Raspberry Pi: cd local_machine")
        print("2. Run: python3 fingerprint_simple_client.py")
        print("3. Verify you see: 'Subscribed to command topics: WHAC/Store001/add_user'")
        print("4. Try enrollment again")
    print()

if __name__ == "__main__":
    main()



