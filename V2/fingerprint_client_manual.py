#!/usr/bin/env python3
"""
Manual Fingerprint Client - Based on your working example
This version doesn't auto-scan, waits for MQTT commands only
"""

import serial
import adafruit_fingerprint
import paho.mqtt.client as mqtt
import json
import time
import logging
import sys
import sqlite3
import threading
import os
from datetime import datetime
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ManualFingerprintClient:
    def __init__(self):
        self.uart = None
        self.finger = None
        self.mqtt_client = None
        self.connected = False
        self.running = True
        self.enrolling = False
        self.command_lock = threading.Lock()
        self.db_file = "fingerprints.db"
        self.init_database()
        
        # MQTT Topics
        self.SCAN_TOPIC = MQTT_TOPIC
        self.ADD_USER_TOPIC = "WHAC/Store001/add_user"
        self.ACTION_TOPIC = "WHAC/Store001/action"
    
    def connect_sensor(self, retries=3):
        """Connect to AS608 fingerprint sensor - based on your working example"""
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to fingerprint sensor on /dev/serial0 (attempt {attempt + 1})")
                self.uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=2)
                time.sleep(0.5)  # Give sensor time to stabilize
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                logger.info("✓ Sensor connected successfully!")
                return True
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self.uart:
                    self.uart.close()
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    raise
        return False
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client = mqtt.Client()
            
            # Set up callbacks
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            # Connect to broker
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("✓ MQTT broker connected successfully!")
                # Subscribe to command topics
                self.mqtt_client.subscribe(self.ADD_USER_TOPIC, qos=MQTT_QOS)
                self.mqtt_client.subscribe(self.ACTION_TOPIC, qos=MQTT_QOS)
                logger.info(f"✓ Subscribed to command topics:")
                logger.info(f"  - {self.ADD_USER_TOPIC}")
                logger.info(f"  - {self.ACTION_TOPIC}")
                return True
            else:
                logger.error("✗ Failed to connect to MQTT broker within timeout")
                return False
                
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT client connected")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning(f"MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT commands"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received command on {topic}: {payload}")
            
            # Handle different command topics
            if topic == self.ADD_USER_TOPIC:
                self.handle_add_user_command(payload)
            elif topic == self.ACTION_TOPIC:
                self.handle_relay_command(payload)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def init_database(self):
        """Initialize simple SQLite database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Simple users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    fingerprint_id INTEGER PRIMARY KEY,
                    user_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add a test user if database is empty
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                cursor.execute("INSERT INTO users (fingerprint_id, user_name) VALUES (1, 'Test User')")
                logger.info("✓ Added test user: Test User (ID: 1)")
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Database initialized: {self.db_file}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def handle_add_user_command(self, payload):
        """Handle add user command - based on your working example"""
        try:
            with self.command_lock:
                logger.info("Processing add user command...")
                
                # Extract command data
                fingerprint_id = payload.get("fingerprint_id")
                user_name = payload.get("user_name")
                
                if not fingerprint_id or not user_name:
                    logger.error("Missing fingerprint_id or user_name in add user command")
                    return
                
                # Set enrolling flag
                self.enrolling = True
                logger.info("⏸️  Starting enrollment process...")
                
                try:
                    # Enroll fingerprint using your working method
                    if self.enroll_fingerprint(fingerprint_id):
                        # Save to database
                        conn = sqlite3.connect(self.db_file)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO users (fingerprint_id, user_name)
                            VALUES (?, ?)
                        ''', (fingerprint_id, user_name))
                        conn.commit()
                        conn.close()
                        
                        logger.info(f"✓ User added: {user_name} (ID: {fingerprint_id})")
                        
                        # Send confirmation
                        self.send_command_response("add_user", "success", {
                            "fingerprint_id": fingerprint_id,
                            "user_name": user_name,
                            "message": "User added successfully"
                        })
                    else:
                        logger.error(f"✗ Failed to enroll fingerprint for user: {user_name}")
                        self.send_command_response("add_user", "error", {
                            "message": "Failed to enroll fingerprint"
                        })
                finally:
                    # Always reset enrolling flag
                    self.enrolling = False
                    logger.info("▶️  Enrollment process completed")
                    
        except Exception as e:
            logger.error(f"Error handling add user command: {e}")
            self.enrolling = False
            self.send_command_response("add_user", "error", {
                "message": f"Error: {str(e)}"
            })
    
    def enroll_fingerprint(self, location):
        """Enroll a new fingerprint - based on your working example"""
        try:
            logger.info(f"\n=== Enrolling fingerprint at location {location} ===")
            logger.info("Place finger on sensor...")
            
            # First scan
            while True:
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                if i == adafruit_fingerprint.NOFINGER:
                    continue
                else:
                    logger.error(f"Error getting image: {i}")
                    return False
            
            logger.info("Image captured!")
            
            if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
                logger.error("Error converting image")
                return False
            
            logger.info("Remove finger")
            time.sleep(2)
            
            while self.finger.get_image() != adafruit_fingerprint.NOFINGER:
                pass
            
            logger.info("Place same finger again...")
            
            # Second scan
            while True:
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                if i == adafruit_fingerprint.NOFINGER:
                    continue
                else:
                    logger.error(f"Error getting image: {i}")
                    return False
            
            logger.info("Image captured!")
            
            if self.finger.image_2_tz(2) != adafruit_fingerprint.OK:
                logger.error("Error converting second image")
                return False
            
            logger.info("Creating model...")
            if self.finger.create_model() != adafruit_fingerprint.OK:
                logger.error("Error creating model - fingers didn't match?")
                return False
            
            logger.info(f"Storing model at location {location}...")
            if self.finger.store_model(location) != adafruit_fingerprint.OK:
                logger.error("Error storing model")
                return False
            
            logger.info(f"✓ Fingerprint enrolled successfully at location {location}!")
            return True
            
        except Exception as e:
            logger.error(f"Error during enrollment: {e}")
            return False
    
    def handle_relay_command(self, payload):
        """Handle relay control command"""
        try:
            command = payload.get('command')
            user_id = payload.get('user_id')
            action = payload.get('action')
            source = payload.get('source')
            
            logger.info(f"Received relay command: {command} for user {user_id}")
            # Add relay control logic here if needed
            
        except Exception as e:
            logger.error(f"Error handling relay command: {e}")
    
    def send_command_response(self, command_type, status, data):
        """Send command response back to MQTT"""
        try:
            response = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "command": command_type,
                "status": status,
                "data": data,
                "device_id": "AS608_001"
            }
            
            response_topic = f"WHAC/Store001/{command_type}_response"
            payload = json.dumps(response)
            result = self.mqtt_client.publish(response_topic, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Command response sent: {command_type} - {status}")
            else:
                logger.error(f"✗ Failed to send command response (rc: {result.rc})")
                
        except Exception as e:
            logger.error(f"Error sending command response: {e}")
    
    def get_template_count(self):
        """Get number of stored fingerprints"""
        try:
            if self.finger.read_templates() == adafruit_fingerprint.OK:
                count = self.finger.template_count
                logger.info(f"Stored fingerprints: {count}")
                return count
            else:
                logger.warning("Failed to read template count")
                return 0
        except Exception as e:
            logger.error(f"Error getting template count: {e}")
            return 0
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        self.running = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        
        if self.uart:
            self.uart.close()
            logger.info("Serial connection closed")

def main():
    """Main function"""
    client = ManualFingerprintClient()
    
    try:
        # Connect to fingerprint sensor
        if not client.connect_sensor():
            logger.error("Failed to connect to fingerprint sensor")
            return 1
        
        # Connect to MQTT broker
        if not client.connect_mqtt():
            logger.error("Failed to connect to MQTT broker")
            return 1
        
        # Show initial status
        template_count = client.get_template_count()
        
        logger.info("=" * 70)
        logger.info("MANUAL FINGERPRINT MQTT CLIENT - Ready!")
        logger.info("=" * 70)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Fingerprint Port: /dev/serial0")
        logger.info(f"Add User Topic: {client.ADD_USER_TOPIC}")
        logger.info(f"Action Topic: {client.ACTION_TOPIC}")
        logger.info(f"Stored Templates: {template_count}")
        logger.info("=" * 70)
        logger.info("✓ Listening for MQTT commands...")
        logger.info("✓ No auto-scanning - commands only")
        logger.info("=" * 70)
        
        # Keep running and wait for MQTT commands
        try:
            while client.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Program interrupted by user")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        client.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
