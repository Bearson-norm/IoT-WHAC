#!/usr/bin/env python3
"""
Hybrid Fingerprint MQTT Client for AS608 Sensor
- Uses AS608 built-in verification (most reliable)
- Stores all verification results locally in SQLite
- Sends only approved fingerprints to MQTT server
"""

import serial
import adafruit_fingerprint
import paho.mqtt.client as mqtt
import json
import time
import logging
import sys
import sqlite3
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

class HybridFingerprintClient:
    def __init__(self, database_file="fingerprint_log.db"):
        self.uart = None
        self.finger = None
        self.mqtt_client = None
        self.connected = False
        self.last_scan_time = 0
        self.db_file = database_file
        self.init_database()
        
    def connect_sensor(self, retries=3):
        """Connect to AS608 fingerprint sensor with retry logic"""
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to fingerprint sensor on {FINGERPRINT_PORT} (attempt {attempt + 1})")
                self.uart = serial.Serial(FINGERPRINT_PORT, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)  # Give sensor time to stabilize
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                
                # Test connection
                if self.finger.read_templates() == adafruit_fingerprint.OK:
                    logger.info(f"✓ Fingerprint sensor connected successfully! Templates: {self.finger.template_count}")
                    return True
                else:
                    raise Exception("Failed to read templates from sensor")
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self.uart:
                    self.uart.close()
                if attempt < retries - 1:
                    time.sleep(2)
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
            self.mqtt_client.on_publish = self.on_mqtt_publish
            
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
    
    def on_mqtt_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        logger.debug(f"Message published (mid: {mid})")
    
    def init_database(self):
        """Initialize SQLite database for storing verification results"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create verification_log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fingerprint_id INTEGER,
                    confidence INTEGER,
                    verification_result TEXT,
                    action_taken TEXT,
                    mqtt_sent BOOLEAN DEFAULT FALSE,
                    mqtt_timestamp TIMESTAMP,
                    device_id TEXT DEFAULT 'AS608_001',
                    store_id TEXT DEFAULT ?
                )
            ''', (STORE_ID,))
            
            # Create user_profiles table (optional - for storing user info)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    fingerprint_id INTEGER PRIMARY KEY,
                    user_name TEXT,
                    user_id TEXT,
                    department TEXT,
                    access_level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_access TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Create system_stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    total_scans INTEGER DEFAULT 0,
                    successful_verifications INTEGER DEFAULT 0,
                    failed_verifications INTEGER DEFAULT 0,
                    mqtt_messages_sent INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0.0
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Database initialized: {self.db_file}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def log_verification_result(self, fingerprint_id, confidence, verification_result, action_taken, mqtt_sent=False):
        """Log verification result to local database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Insert verification log
            cursor.execute('''
                INSERT INTO verification_log 
                (fingerprint_id, confidence, verification_result, action_taken, mqtt_sent, mqtt_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (fingerprint_id, confidence, verification_result, action_taken, mqtt_sent, 
                  datetime.now() if mqtt_sent else None))
            
            # Update user profile if exists
            if fingerprint_id > 0:
                cursor.execute('''
                    UPDATE user_profiles 
                    SET last_access = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE fingerprint_id = ?
                ''', (fingerprint_id,))
            
            # Update daily stats
            today = datetime.now().date()
            cursor.execute('''
                INSERT OR REPLACE INTO system_stats (date, total_scans, successful_verifications, failed_verifications, mqtt_messages_sent)
                VALUES (?, 
                    COALESCE((SELECT total_scans FROM system_stats WHERE date = ?), 0) + 1,
                    COALESCE((SELECT successful_verifications FROM system_stats WHERE date = ?), 0) + ?,
                    COALESCE((SELECT failed_verifications FROM system_stats WHERE date = ?), 0) + ?,
                    COALESCE((SELECT mqtt_messages_sent FROM system_stats WHERE date = ?), 0) + ?
                )
            ''', (today, today, today, 1 if verification_result == "success" else 0, 
                  today, 1 if verification_result == "failed" else 0, 
                  today, 1 if mqtt_sent else 0))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Verification result logged: ID={fingerprint_id}, Result={verification_result}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging verification result: {e}")
            return False
    
    def send_approved_fingerprint_to_mqtt(self, fingerprint_id, confidence, action="access_granted"):
        """Send only approved fingerprints to MQTT broker"""
        if not self.connected:
            logger.error("MQTT not connected, cannot send data")
            return False
        
        try:
            # Get user profile if exists
            user_info = self.get_user_profile(fingerprint_id)
            
            # Prepare data payload
            data = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "fingerprint_id": fingerprint_id,
                "confidence": confidence,
                "device_type": "fingerprint_scanner",
                "device_id": "AS608_001"
            }
            
            # Add user info if available
            if user_info:
                data.update({
                    "user_name": user_info.get("user_name"),
                    "user_id": user_info.get("user_id"),
                    "department": user_info.get("department"),
                    "access_level": user_info.get("access_level")
                })
            
            # Convert to JSON
            payload = json.dumps(data)
            
            # Publish to MQTT
            result = self.mqtt_client.publish(MQTT_TOPIC, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Approved fingerprint sent to MQTT: ID={fingerprint_id}, Confidence={confidence}")
                return True
            else:
                logger.error(f"✗ Failed to publish to MQTT (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending approved fingerprint to MQTT: {e}")
            return False
    
    def get_user_profile(self, fingerprint_id):
        """Get user profile information"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_name, user_id, department, access_level 
                FROM user_profiles 
                WHERE fingerprint_id = ? AND is_active = TRUE
            ''', (fingerprint_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "user_name": result[0],
                    "user_id": result[1],
                    "department": result[2],
                    "access_level": result[3]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def add_user_profile(self, fingerprint_id, user_name, user_id=None, department=None, access_level=1):
        """Add or update user profile"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (fingerprint_id, user_name, user_id, department, access_level, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (fingerprint_id, user_name, user_id, department, access_level))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ User profile added/updated: {user_name} (ID: {fingerprint_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user profile: {e}")
            return False
    
    def scan_fingerprint(self):
        """Scan and process fingerprint with local verification and selective MQTT transmission"""
        try:
            # Check if enough time has passed since last scan
            current_time = time.time()
            if current_time - self.last_scan_time < SCAN_INTERVAL:
                return False
            
            # Get fingerprint image
            i = self.finger.get_image()
            if i == adafruit_fingerprint.OK:
                logger.debug("Fingerprint image captured")
                
                # Convert image to template
                if self.finger.image_2_tz(1) == adafruit_fingerprint.OK:
                    logger.debug("Image converted to template")
                    
                    # Search for match using AS608 built-in verification
                    i = self.finger.finger_search()
                    
                    if i == adafruit_fingerprint.OK:
                        # Match found
                        finger_id = self.finger.finger_id
                        confidence = self.finger.confidence
                        
                        logger.info(f"✓ Match found! ID: {finger_id}, Confidence: {confidence}")
                        
                        # Check confidence threshold
                        if confidence >= CONFIDENCE_THRESHOLD:
                            # APPROVED - Send to MQTT and log
                            mqtt_success = self.send_approved_fingerprint_to_mqtt(finger_id, confidence, "access_granted")
                            self.log_verification_result(finger_id, confidence, "success", "access_granted", mqtt_success)
                            self.last_scan_time = current_time
                            return True
                        else:
                            # REJECTED - Log only, don't send to MQTT
                            logger.warning(f"Confidence too low: {confidence} < {CONFIDENCE_THRESHOLD}")
                            self.log_verification_result(finger_id, confidence, "rejected", "access_denied_low_confidence", False)
                            self.last_scan_time = current_time
                            return True
                    else:
                        # No match found - Log only, don't send to MQTT
                        logger.info("✗ No match found")
                        self.log_verification_result(0, 0, "failed", "no_match", False)
                        self.last_scan_time = current_time
                        return True
                else:
                    logger.error("Failed to convert image to template")
                    return False
            elif i == adafruit_fingerprint.NOFINGER:
                # No finger detected, this is normal
                return False
            else:
                logger.error(f"Error getting fingerprint image: {i}")
                return False
                
        except Exception as e:
            logger.error(f"Error during fingerprint scan: {e}")
            return False
    
    def get_daily_stats(self):
        """Get daily statistics"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            today = datetime.now().date()
            cursor.execute('''
                SELECT total_scans, successful_verifications, failed_verifications, mqtt_messages_sent, avg_confidence
                FROM system_stats 
                WHERE date = ?
            ''', (today,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "date": str(today),
                    "total_scans": result[0],
                    "successful_verifications": result[1],
                    "failed_verifications": result[2],
                    "mqtt_messages_sent": result[3],
                    "avg_confidence": result[4]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return None
    
    def run_continuous_scan(self):
        """Run continuous fingerprint scanning"""
        logger.info("Starting continuous fingerprint scanning...")
        logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
        logger.info(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
        logger.info("✓ All scans logged locally, only approved fingerprints sent to MQTT")
        
        try:
            while True:
                self.scan_fingerprint()
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
        except KeyboardInterrupt:
            logger.info("Scanning stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous scan: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        
        if self.uart:
            self.uart.close()
            logger.info("Serial connection closed")

def main():
    """Main function"""
    client = HybridFingerprintClient()
    
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
        if client.finger.read_templates() == adafruit_fingerprint.OK:
            template_count = client.finger.template_count
        else:
            template_count = 0
        
        # Show daily stats
        stats = client.get_daily_stats()
        
        logger.info("=" * 70)
        logger.info("HYBRID FINGERPRINT MQTT CLIENT - Ready!")
        logger.info("=" * 70)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"MQTT Topic: {MQTT_TOPIC}")
        logger.info(f"Stored Templates: {template_count}")
        logger.info(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
        logger.info(f"Database: {client.db_file}")
        
        if stats:
            logger.info(f"Today's Stats: {stats['total_scans']} scans, {stats['successful_verifications']} approved, {stats['mqtt_messages_sent']} sent to MQTT")
        
        logger.info("=" * 70)
        logger.info("✓ All scans logged locally")
        logger.info("✓ Only approved fingerprints sent to MQTT")
        logger.info("✓ AS608 built-in verification (most reliable)")
        logger.info("=" * 70)
        
        # Start continuous scanning
        client.run_continuous_scan()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        client.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

