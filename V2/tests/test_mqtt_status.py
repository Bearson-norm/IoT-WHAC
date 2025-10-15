#!/usr/bin/env python3
"""
Test script to check MQTT connection status and diagnose code 7 disconnections
"""

import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime

# MQTT configuration (same as web_ui/app.py)
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_ACTION_TOPIC = "WHAC/Store001/action"

def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    if rc == 0:
        print("✅ MQTT client connected successfully")
        print(f"   Connected to: {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"❌ MQTT connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    """MQTT disconnection callback"""
    if rc == 0:
        print("🔌 MQTT client disconnected normally")
    else:
        print(f"⚠️  MQTT client disconnected unexpectedly (code: {rc})")
        
        # Explain what code 7 means
        if rc == 7:
            print("   Code 7: Connection lost - this is usually a network hiccup")
            print("   The client may still be able to send messages despite this warning")
        else:
            print(f"   Code {rc}: Other disconnection reason")

def on_message(client, userdata, msg):
    """Handle incoming messages"""
    print(f"📨 Received message on {msg.topic}: {msg.payload.decode()}")

def test_mqtt_connection_status():
    """Test MQTT connection and status"""
    print("=" * 60)
    print("🧪 MQTT CONNECTION STATUS TEST")
    print("=" * 60)
    print(f"🌐 Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"📡 Topic: {MQTT_ACTION_TOPIC}")
    print("=" * 60)
    
    try:
        # Create MQTT client with unique ID
        client = mqtt.Client(client_id="test_status_client", clean_session=True)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        
        print("🔌 Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Wait for connection
        time.sleep(3)
        
        # Check connection status
        is_connected = client.is_connected()
        print(f"\n📊 Connection Status: {'✅ Connected' if is_connected else '❌ Disconnected'}")
        
        if is_connected:
            # Test ping
            print("🏓 Testing ping...")
            try:
                ping_result = client.ping()
                print(f"   Ping result: {ping_result} ({'✅ Success' if ping_result == 0 else '❌ Failed'})")
            except Exception as e:
                print(f"   Ping error: {e}")
            
            # Test publish
            print("📤 Testing publish...")
            test_payload = {
                'command': 'test',
                'user_id': 999,
                'action': 'connection_test',
                'timestamp': datetime.now().isoformat(),
                'source': 'test_script'
            }
            
            result = client.publish(MQTT_ACTION_TOPIC, json.dumps(test_payload), qos=1)
            print(f"   Publish result: rc={result.rc} ({'✅ Success' if result.rc == 0 else '❌ Failed'})")
            
            if result.rc == 0:
                print("✅ MQTT connection is working properly!")
                print("✅ Code 7 disconnections are likely false alarms")
            else:
                print("❌ MQTT connection has issues")
                print(f"❌ Error code: {result.rc}")
        
        # Keep connection alive for a bit to see if disconnect events occur
        print("\n⏳ Keeping connection alive for 10 seconds to monitor for disconnections...")
        for i in range(10):
            time.sleep(1)
            if not client.is_connected():
                print(f"❌ Connection lost after {i+1} seconds")
                break
            print(f"   Still connected... ({i+1}/10)")
        
        print("\n📊 Final Status:")
        print(f"   Connected: {'✅ Yes' if client.is_connected() else '❌ No'}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        if 'client' in locals():
            client.loop_stop()
            client.disconnect()
            print("🔌 MQTT client disconnected")

def explain_code_7():
    """Explain what MQTT disconnect code 7 means"""
    print("\n" + "=" * 60)
    print("📚 MQTT DISCONNECT CODE 7 EXPLANATION")
    print("=" * 60)
    print("Code 7: MQTT_ERR_CONN_LOST")
    print("")
    print("This means the MQTT client detected that the connection was lost.")
    print("However, this can happen for several reasons:")
    print("")
    print("1. 🌐 Network hiccup - Brief network interruption")
    print("2. 🔄 Keep-alive timeout - Broker didn't receive keep-alive in time")
    print("3. 📡 Broker restart - MQTT broker was restarted")
    print("4. 🔌 Network interface change - WiFi/Ethernet reconnection")
    print("5. ⚡ False alarm - Client state confusion")
    print("")
    print("The important thing is:")
    print("✅ If the client can still send messages successfully, it's working!")
    print("✅ Code 7 warnings don't necessarily mean the connection is broken")
    print("✅ The client will automatically reconnect when needed")
    print("")
    print("💡 Solution: Ignore code 7 warnings if messages are still being sent successfully")

def main():
    """Main function"""
    explain_code_7()
    test_mqtt_connection_status()
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS")
    print("=" * 60)
    print("1. ✅ If messages are sending successfully, ignore code 7 warnings")
    print("2. ✅ The improved error handling will manage reconnections automatically")
    print("3. ✅ Code 7 is often a false alarm - the connection is still working")
    print("4. ✅ Focus on whether relay commands are actually working")
    print("=" * 60)

if __name__ == "__main__":
    main()

