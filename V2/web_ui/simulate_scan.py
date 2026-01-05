#!/usr/bin/env python3
"""
Simulate Fingerprint Scan for Testing
This script simulates fingerprint scans at both sensors for testing attendance linking
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import sys

# MQTT Configuration - MUST MATCH WEB UI SETTINGS!
MQTT_BROKER = "103.87.67.139"  # Change to your MQTT broker IP (default: remote broker)
MQTT_PORT = 1883
MQTT_SCAN_TOPIC = "WHAC/Store001/in"  # ✓ Correct topic that Web UI subscribes to

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"✅ Connected to MQTT broker successfully!")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected"""
    if rc != 0:
        print(f"⚠️  Unexpected disconnection (code: {rc})")

def on_publish(client, userdata, mid):
    """Callback when message is published"""
    print(f"✅ Message {mid} published successfully!")

def simulate_scan(user_id, device_id, confidence=95, status="Match"):
    """
    Simulate a fingerprint scan
    
    Args:
        user_id: User ID yang akan di-scan
        device_id: "AS608_001" (Sensor Masuk) atau "AS608_002" (Sensor Keluar)
        confidence: Confidence level (0-100)
        status: "Match" atau "Not Match"
    """
    
    # Create MQTT client with callbacks
    client = mqtt.Client(client_id=f"simulator_{int(time.time())}")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    
    try:
        # Connect to broker
        print(f"\n🔌 Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()  # Start network loop
        
        # Wait for connection
        time.sleep(1)
        
        # Check if connected
        if not client.is_connected():
            print(f"❌ Failed to connect to MQTT broker!")
            print(f"   Make sure broker is running at {MQTT_BROKER}:{MQTT_PORT}")
            return False
        
        # Create scan payload matching the format expected by Web UI
        payload = {
            "store_id": "Store001",
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "fingerprint_id": user_id,
            "user_id": user_id,
            "device_id": device_id,
            "confidence": confidence,
            "sensor_location": "masuk" if device_id == "AS608_001" else "keluar"
        }
        
        sensor_name = "Pintu Masuk" if device_id == "AS608_001" else "Pintu Keluar"
        
        # Publish scan
        print(f"\n📡 Publishing scan to topic: {MQTT_SCAN_TOPIC}")
        print(f"👤 User ID: {user_id}")
        print(f"📍 Sensor: {sensor_name} ({device_id})")
        print(f"✓ Status: {status}")
        print(f"📊 Confidence: {confidence}%")
        print(f"⏰ Timestamp: {payload['timestamp']}")
        print(f"\n📦 Payload: {json.dumps(payload, indent=2)}")
        
        result = client.publish(MQTT_SCAN_TOPIC, json.dumps(payload), qos=1)
        
        # Wait for publish to complete
        result.wait_for_publish()
        
        if result.is_published():
            print(f"\n✅ Scan published successfully!")
            print(f"💡 Check Web UI dashboard - modal should pop up!")
        else:
            print(f"\n❌ Failed to publish scan (error code: {result.rc})")
        
        # Wait a bit before disconnecting
        time.sleep(1)
        
        # Disconnect
        client.loop_stop()
        client.disconnect()
        
        return result.is_published()
        
    except ConnectionRefusedError:
        print(f"\n❌ Connection Refused!")
        print(f"   MQTT broker not running at {MQTT_BROKER}:{MQTT_PORT}")
        print(f"\n💡 Solutions:")
        print(f"   1. Check if MQTT broker (Mosquitto) is running")
        print(f"   2. Update MQTT_BROKER in this script to correct IP")
        print(f"   3. Check firewall settings")
        return False
    except TimeoutError:
        print(f"\n❌ Connection Timeout!")
        print(f"   Cannot reach MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_scenario_linked_user():
    """
    Test Scenario: User dengan nama lengkap yang sama scan di kedua sensor
    Expected: Attendance harus merge jadi 1 baris
    """
    print("\n" + "="*70)
    print("🧪 TEST SCENARIO: Linked User Attendance")
    print("="*70)
    print("\nScenario: User 'Hilal Akbar Quddus Ramadhan' scan di kedua sensor")
    print("Expected: 1 baris attendance dengan clock_in dan clock_out terisi")
    print("\n" + "-"*70)
    
    # Simulate scan at Sensor 1 (Masuk)
    print("\n[1/2] Simulating scan at Sensor 1 (Pintu Masuk)...")
    simulate_scan(user_id=1, device_id="AS608_001", confidence=98)
    
    print("\n⏳ Waiting 3 seconds before next scan...")
    time.sleep(3)
    
    # Simulate scan at Sensor 2 (Keluar)
    print("\n[2/2] Simulating scan at Sensor 2 (Pintu Keluar)...")
    simulate_scan(user_id=2, device_id="AS608_002", confidence=96)
    
    print("\n" + "="*70)
    print("✅ Simulation completed!")
    print("="*70)
    print("\n📋 Next steps:")
    print("1. Open Web UI and grant access for both scans")
    print("2. Check Attendance table - should show 1 row with:")
    print("   - Full Name: Hilal Akbar Quddus Ramadhan")
    print("   - User ID In: 1")
    print("   - User ID Out: 2")
    print("   - Clock In: (earlier timestamp)")
    print("   - Clock Out: (later timestamp)")
    print("\n")

def test_scenario_unlinked_users():
    """
    Test Scenario: 2 User berbeda dengan nama lengkap berbeda
    Expected: 2 baris attendance terpisah
    """
    print("\n" + "="*70)
    print("🧪 TEST SCENARIO: Unlinked Users Attendance")
    print("="*70)
    print("\nScenario: 2 user berbeda scan di sensor yang berbeda")
    print("Expected: 2 baris attendance terpisah")
    print("\n" + "-"*70)
    
    # User 1 at Sensor 1
    print("\n[1/2] User 1 scanning at Sensor 1...")
    simulate_scan(user_id=3, device_id="AS608_001", confidence=97)
    
    time.sleep(2)
    
    # User 2 at Sensor 2
    print("\n[2/2] User 2 scanning at Sensor 2...")
    simulate_scan(user_id=4, device_id="AS608_002", confidence=95)
    
    print("\n" + "="*70)
    print("✅ Simulation completed!")
    print("="*70)

def test_scenario_multiple_scans():
    """
    Test Scenario: User scan multiple kali di sensor yang sama
    Expected: Clock in/out updated ke earliest/latest timestamp
    """
    print("\n" + "="*70)
    print("🧪 TEST SCENARIO: Multiple Scans Same User")
    print("="*70)
    print("\nScenario: User scan beberapa kali di sensor yang sama")
    print("Expected: Clock in = earliest, Clock out = latest")
    print("\n" + "-"*70)
    
    print("\n[1/4] First scan at Sensor 1...")
    simulate_scan(user_id=1, device_id="AS608_001", confidence=98)
    time.sleep(2)
    
    print("\n[2/4] Second scan at Sensor 1 (should keep earliest)...")
    simulate_scan(user_id=1, device_id="AS608_001", confidence=97)
    time.sleep(2)
    
    print("\n[3/4] First scan at Sensor 2...")
    simulate_scan(user_id=2, device_id="AS608_002", confidence=96)
    time.sleep(2)
    
    print("\n[4/4] Second scan at Sensor 2 (should use latest)...")
    simulate_scan(user_id=2, device_id="AS608_002", confidence=95)
    
    print("\n" + "="*70)
    print("✅ Simulation completed!")
    print("="*70)

def manual_scan():
    """Interactive manual scan simulation"""
    print("\n" + "="*70)
    print("🎮 MANUAL SCAN SIMULATION")
    print("="*70)
    
    try:
        # Get user input
        user_id = int(input("\n👤 Enter User ID: "))
        
        print("\n📍 Select Sensor:")
        print("  1. AS608_001 (Pintu Masuk)")
        print("  2. AS608_002 (Pintu Keluar)")
        sensor_choice = input("Choice (1/2): ").strip()
        
        device_id = "AS608_001" if sensor_choice == "1" else "AS608_002"
        
        confidence = int(input("\n📊 Enter Confidence (0-100) [default: 95]: ") or "95")
        
        print("\n✓ Select Status:")
        print("  1. Match")
        print("  2. Not Match")
        status_choice = input("Choice (1/2) [default: 1]: ").strip() or "1"
        
        status = "Match" if status_choice == "1" else "Not Match"
        
        # Confirm
        print("\n" + "-"*70)
        print("📋 Scan Summary:")
        print(f"   User ID: {user_id}")
        print(f"   Device: {device_id}")
        print(f"   Confidence: {confidence}%")
        print(f"   Status: {status}")
        print("-"*70)
        
        confirm = input("\n✓ Publish this scan? (y/n): ").lower()
        
        if confirm == 'y':
            simulate_scan(user_id, device_id, confidence, status)
        else:
            print("❌ Scan cancelled")
            
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*70)
        print("📱 FINGERPRINT SCAN SIMULATOR")
        print("="*70)
        print("\nTest Scenarios:")
        print("  1. Linked User (Same full_name, different sensors)")
        print("  2. Unlinked Users (Different full_names)")
        print("  3. Multiple Scans (Same user, multiple times)")
        print("  4. Manual Scan (Custom parameters)")
        print("  0. Exit")
        print("\n" + "="*70)
        
        choice = input("\n🎯 Select option (0-4): ").strip()
        
        if choice == "1":
            test_scenario_linked_user()
        elif choice == "2":
            test_scenario_unlinked_users()
        elif choice == "3":
            test_scenario_multiple_scans()
        elif choice == "4":
            manual_scan()
        elif choice == "0":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option!")
        
        if choice in ["1", "2", "3", "4"]:
            input("\n⏸️  Press Enter to continue...")

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         WHAC Fingerprint Scan Simulator v1.1                  ║
    ║                                                               ║
    ║  This tool simulates fingerprint scans for testing            ║
    ║  attendance linking functionality                             ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚙️  Configuration:")
    print(f"   MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"   MQTT Topic: {MQTT_SCAN_TOPIC}")
    print(f"\n💡 Important Notes:")
    print(f"   1. Make sure MQTT broker is running at {MQTT_BROKER}:{MQTT_PORT}")
    print(f"   2. Web UI must be active and connected to same MQTT broker")
    print(f"   3. You need to grant access in Web UI after each scan")
    print(f"   4. If using different broker, update MQTT_BROKER in this script")
    
    # Test connection first
    print(f"\n🔍 Testing MQTT connection...")
    test_client = mqtt.Client(client_id="test_connection")
    try:
        test_client.connect(MQTT_BROKER, MQTT_PORT, 5)
        test_client.disconnect()
        print(f"✅ MQTT broker is reachable!")
    except Exception as e:
        print(f"❌ Cannot connect to MQTT broker: {e}")
        print(f"\n⚠️  Please check:")
        print(f"   1. Is MQTT broker running? (mosquitto service)")
        print(f"   2. Is {MQTT_BROKER}:{MQTT_PORT} correct?")
        print(f"   3. Firewall blocking connection?")
        
        change_broker = input(f"\n🔧 Want to change broker address? (y/n): ").lower()
        if change_broker == 'y':
            new_broker = input("   Enter broker IP [localhost]: ").strip() or "localhost"
            MQTT_BROKER = new_broker
            print(f"   ✓ Broker changed to: {MQTT_BROKER}")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Simulator stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()





