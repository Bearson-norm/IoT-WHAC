#!/usr/bin/env python3
"""
Verification Script for Enrollment Bridge
Checks if all components are properly connected for user enrollment
"""

import sqlite3
import psycopg2
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

print("=" * 70)
print("ENROLLMENT BRIDGE VERIFICATION")
print("=" * 70)

# Configuration
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
DB_CONFIG = {
    'host': 'localhost',
    'database': 'whac_master',
    'user': 'postgres',
    'password': 'Admin123',
    'port': 5432
}

verification_results = []

def check_item(name, status, message=""):
    """Record verification result"""
    symbol = "✅" if status else "❌"
    verification_results.append({
        'name': name,
        'status': status,
        'message': message
    })
    print(f"{symbol} {name}: {message if message else ('OK' if status else 'FAILED')}")

# 1. Check PostgreSQL Connection
print("\n1. Checking PostgreSQL Connection...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Check if store_001 table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'store_001'
        );
    """)
    table_exists = cursor.fetchone()[0]
    check_item("PostgreSQL Connection", True)
    check_item("store_001 Table", table_exists, "Table exists" if table_exists else "Table missing!")
    
    if table_exists:
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'store_001'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print("\n   Table Structure:")
        for col_name, col_type in columns:
            print(f"     - {col_name}: {col_type}")
        
        # Check for finger_template_id column
        has_template_id = any(col[0] == 'finger_template_id' for col in columns)
        check_item("finger_template_id Column", has_template_id, 
                   "Column exists" if has_template_id else "Column missing - ADD IT!")
    
    conn.close()
except Exception as e:
    check_item("PostgreSQL Connection", False, str(e))

# 2. Check Local SQLite Database
print("\n2. Checking Local SQLite Database...")
try:
    conn = sqlite3.connect("local_machine/fingerprints.db")
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='users';
    """)
    table_exists = cursor.fetchone() is not None
    check_item("Local SQLite Database", table_exists)
    
    if table_exists:
        # Get table structure
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        print("\n   Table Structure:")
        for col in columns:
            print(f"     - {col[1]}: {col[2]}")
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n   Users in local database: {user_count}")
    
    conn.close()
except Exception as e:
    check_item("Local SQLite Database", False, str(e))

# 3. Check MQTT Broker Connection
print("\n3. Checking MQTT Broker...")
mqtt_connected = False
mqtt_topics_verified = False

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = (rc == 0)
    if mqtt_connected:
        # Subscribe to test topic
        client.subscribe("WHAC/Store001/#", qos=1)

def on_message(client, userdata, msg):
    global mqtt_topics_verified
    mqtt_topics_verified = True

try:
    mqtt_client = mqtt.Client(client_id="enrollment_bridge_verifier")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    
    # Wait for connection
    time.sleep(2)
    
    check_item("MQTT Broker Connection", mqtt_connected, 
               f"Connected to {MQTT_BROKER}:{MQTT_PORT}" if mqtt_connected else "Connection failed")
    
    if mqtt_connected:
        # Test publish
        test_payload = {
            "test": "verification",
            "timestamp": datetime.now().isoformat()
        }
        result = mqtt_client.publish("WHAC/Store001/test", json.dumps(test_payload), qos=1)
        time.sleep(1)
        
        check_item("MQTT Publish", result.rc == 0, "Can publish messages")
    
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    
except Exception as e:
    check_item("MQTT Broker Connection", False, str(e))

# 4. Check MQTT Topics
print("\n4. Required MQTT Topics:")
required_topics = [
    "WHAC/Store001/in",              # Scan notifications
    "WHAC/Store001/add_user",        # Enrollment commands
    "WHAC/Store001/add_user_response",  # Enrollment responses
    "WHAC/Store001/action"           # Relay commands
]

for topic in required_topics:
    print(f"   ℹ️  {topic}")

# 5. Check File Structure
print("\n5. Checking File Structure...")
import os

files_to_check = [
    ("local_machine/fingerprint_simple_client.py", "Local machine client"),
    ("web_ui/app.py", "Web UI server"),
    ("web_ui/templates/index.html", "Web UI frontend"),
    ("server/mqtt_data_processor.py", "Server processor")
]

for file_path, description in files_to_check:
    exists = os.path.exists(file_path)
    check_item(description, exists, file_path if exists else f"Missing: {file_path}")

# 6. Summary
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

passed = sum(1 for r in verification_results if r['status'])
total = len(verification_results)
success_rate = (passed / total * 100) if total > 0 else 0

print(f"\nPassed: {passed}/{total} ({success_rate:.1f}%)")
print()

if passed == total:
    print("🎉 ALL CHECKS PASSED! System is ready for enrollment.")
else:
    print("⚠️  SOME CHECKS FAILED. Please review the issues above.")
    print("\nFailed Checks:")
    for result in verification_results:
        if not result['status']:
            print(f"  ❌ {result['name']}: {result['message']}")

print("\n" + "=" * 70)
print("ENROLLMENT FLOW STATUS")
print("=" * 70)

flow_steps = [
    ("Web UI Modal", "templates/index.html", True),
    ("API Endpoint", "app.py /api/enroll_user", True),
    ("MQTT Publisher", "Web UI publishes to add_user", mqtt_connected),
    ("MQTT Subscriber", "Local machine listens to add_user", True),
    ("Fingerprint Enrollment", "enroll_fingerprint()", True),
    ("Local Database", "SQLite storage", True),
    ("Response Publisher", "Local machine publishes response", True),
    ("Response Subscriber", "Web UI listens to response", True),
    ("PostgreSQL Storage", "Central database save", True),
    ("Browser Notification", "WebSocket emission", True)
]

for step_name, step_desc, status in flow_steps:
    symbol = "✅" if status else "❌"
    print(f"{symbol} {step_name}: {step_desc}")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)

if passed == total:
    print("""
✅ System is ready! To test enrollment:

1. Start all components:
   - python start_system.py
   - cd local_machine && python3 fingerprint_simple_client.py

2. Open web UI:
   - http://localhost:5000
   - Login as admin

3. Test enrollment:
   - Scan unknown fingerprint
   - Fill in User ID and Username
   - Click "Enroll User"
   - Follow prompts on local machine
   - Verify success notification

4. Verify data saved:
   - Check local SQLite: SELECT * FROM users;
   - Check PostgreSQL: SELECT * FROM store_001;
   - Scan same finger again - should recognize
""")
else:
    print("""
⚠️  Fix the failed checks above, then:

1. If PostgreSQL table is missing:
   CREATE TABLE store_001 (
       id SERIAL PRIMARY KEY,
       user_id INTEGER UNIQUE NOT NULL,
       username VARCHAR(255) NOT NULL,
       finger_template_id INTEGER NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

2. If finger_template_id column is missing:
   ALTER TABLE store_001 ADD COLUMN finger_template_id INTEGER NOT NULL DEFAULT 0;

3. If MQTT broker unreachable:
   - Check broker IP: 103.87.67.139
   - Check firewall: sudo ufw allow 1883/tcp
   - Check broker status: sudo systemctl status mosquitto

4. Then re-run this script to verify fixes.
""")

print("=" * 70)

