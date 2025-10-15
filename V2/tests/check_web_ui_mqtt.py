#!/usr/bin/env python3
"""
Quick Web UI MQTT Status Checker
"""

import requests
import json

def check_web_ui_mqtt():
    """Check Web UI MQTT connection status"""
    try:
        print("Checking Web UI MQTT status...")
        response = requests.get("http://localhost:5000/api/mqtt_status", timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Status: {data.get('status')}")
                print(f"Connected: {data.get('connected')}")
                print(f"Broker: {data.get('broker')}")
                
                if data.get('connected'):
                    print("[OK] Web UI MQTT is connected!")
                    return True
                else:
                    print("[FAILED] Web UI MQTT is NOT connected!")
                    print(f"Error: {data.get('error', 'Unknown')}")
                    return False
            except json.JSONDecodeError:
                print(f"[ERROR] Invalid JSON response: {response.text}")
                return False
        else:
            print(f"[FAILED] Could not check status (HTTP {response.status_code})")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[FAILED] Web UI is not running!")
        print("Solution: cd web_ui && python app.py")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    check_web_ui_mqtt()
