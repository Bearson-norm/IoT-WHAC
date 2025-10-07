#!/usr/bin/env python3
"""
Simple Fingerprint MQTT Client for AS608 Sensor
- Standby fingerprint scanning
- Simple JSON format
- MQTT command handling for user management
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
import glob
import os
from datetime import datetime
from config import *
from postgresql_integration import PostgreSQLIntegration
from relay_controller import RelayController

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

class SimpleFingerprintClient:
    def __init__(self):
        self.uart = None
        self.finger = None
        self.mqtt_client = None
        self.connected = False
        self.last_scan_time = 0
        self.running = True
        self.command_lock = threading.Lock()
        self.db_file = "fingerprints.db"
        self.init_database()
        
        # PostgreSQL integration
        self.postgres_db = PostgreSQLIntegration()
        
        # Relay controller
        self.relay_controller = RelayController()
        
        # Auto-detect fingerprint sensor port
        self.detected_port = self.auto_detect_fingerprint_port()
        
        # MQTT Topics
        self.SCAN_TOPIC = MQTT_TOPIC  # "WHAC/Store001/in" - for scan results
        self.ADD_USER_TOPIC = "WHAC/Store001/add_user"  # for adding users
        self.IMPORT_TOPIC = "WHAC/Store001/import"  # for importing users
        self.EXPORT_TOPIC = "WHAC/Store001/export"  # for exporting users
        self.ACTION_TOPIC = "WHAC/Store001/action"  # for relay control commands
        self.STATUS_TOPIC = "WHAC/Store001/relay_status"  # for status updates
    
    def auto_detect_fingerprint_port(self):
        """Auto-detect AS608 fingerprint sensor port"""
        logger.info("🔍 Auto-detecting fingerprint sensor port...")
        
        # Common ports for AS608 fingerprint sensors
        possible_ports = [
            "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyUSB3",
            "/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2", "/dev/ttyACM3",
            "/dev/ttyS0", "/dev/ttyS1", "/dev/ttyS2", "/dev/ttyS3",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8"
        ]
        
        # Try to find USB serial devices
        if os.name == 'posix':  # Linux/Unix
            usb_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
            possible_ports = usb_ports + possible_ports
        elif os.name == 'nt':  # Windows
            # On Windows, try to detect COM ports
            import serial.tools.list_ports
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            possible_ports = available_ports + possible_ports
        
        logger.info(f"Checking {len(possible_ports)} possible ports...")
        
        for port in possible_ports:
            if not os.path.exists(port):
                continue
                
            try:
                logger.info(f"Testing port: {port}")
                
                # Try to connect to the port
                test_uart = serial.Serial(port, baudrate=BAUD_RATE, timeout=1)
                time.sleep(0.5)
                
                # Try to create fingerprint object
                test_finger = adafruit_fingerprint.Adafruit_Fingerprint(test_uart)
                
                # Try to read templates (this will fail if not an AS608)
                result = test_finger.read_templates()
                
                if result == adafruit_fingerprint.OK:
                    logger.info(f"✓ AS608 fingerprint sensor found on {port}!")
                    logger.info(f"  Templates: {test_finger.template_count}")
                    test_uart.close()
                    return port
                else:
                    logger.debug(f"  Not an AS608 sensor on {port}")
                    test_uart.close()
                    
            except Exception as e:
                logger.debug(f"  Port {port} failed: {e}")
                continue
        
        # If auto-detection fails, use the configured port
        logger.warning(f"⚠️  Auto-detection failed, using configured port: {FINGERPRINT_PORT}")
        return FINGERPRINT_PORT
    
    def connect_sensor(self, retries=3):
        """Connect to AS608 fingerprint sensor"""
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to fingerprint sensor on {self.detected_port} (attempt {attempt + 1})")
                self.uart = serial.Serial(self.detected_port, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                
                if self.finger.read_templates() == adafruit_fingerprint.OK:
                    logger.info(f"✓ Sensor connected! Templates: {self.finger.template_count}")
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
                self.mqtt_client.subscribe(self.IMPORT_TOPIC, qos=MQTT_QOS)
                self.mqtt_client.subscribe(self.EXPORT_TOPIC, qos=MQTT_QOS)
                self.mqtt_client.subscribe(self.ACTION_TOPIC, qos=MQTT_QOS)
                logger.info(f"✓ Subscribed to command topics:")
                logger.info(f"  - {self.ADD_USER_TOPIC}")
                logger.info(f"  - {self.IMPORT_TOPIC}")
                logger.info(f"  - {self.EXPORT_TOPIC}")
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
            elif topic == self.IMPORT_TOPIC:
                self.handle_import_command(payload)
            elif topic == self.EXPORT_TOPIC:
                self.handle_export_command(payload)
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
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Database initialized: {self.db_file}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def handle_relay_command(self, payload):
        """Handle relay control command"""
        try:
            command = payload.get('command')
            user_id = payload.get('user_id')
            action = payload.get('action')
            source = payload.get('source')
            
            logger.info(f"Received relay command: {command} for user {user_id}")
            
            if command == 'grant':
                self.relay_controller.grant_access(user_id, action, source)
            elif command == 'deny':
                self.relay_controller.deny_access(user_id, action, source)
            else:
                logger.warning(f"Unknown relay command: {command}")
                
        except Exception as e:
            logger.error(f"Error handling relay command: {e}")
    
    def send_scan_result(self, action, fingerprint_id):
        """Send scan result in simple format"""
        if not self.connected:
            logger.error("MQTT not connected, cannot send data")
            return False
        
        try:
            # Simple JSON format as requested
            data = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "fingerprint_id": fingerprint_id,
                "device_id": "AS608_001"
            }
            
            payload = json.dumps(data)
            result = self.mqtt_client.publish(self.SCAN_TOPIC, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Scan result sent: {action} - ID: {fingerprint_id}")
                return True
            else:
                logger.error(f"✗ Failed to publish scan result (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending scan result: {e}")
            return False
    
    def handle_add_user_command(self, payload):
        """Handle add user command"""
        try:
            with self.command_lock:
                logger.info("Processing add user command...")
                
                # Extract command data
                fingerprint_id = payload.get("fingerprint_id")
                user_name = payload.get("user_name")
                
                if not fingerprint_id or not user_name:
                    logger.error("Missing fingerprint_id or user_name in add user command")
                    return
                
                # Enroll fingerprint
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
                    
        except Exception as e:
            logger.error(f"Error handling add user command: {e}")
            self.send_command_response("add_user", "error", {
                "message": f"Error: {str(e)}"
            })
    
    def handle_import_command(self, payload):
        """Handle import users command with fingerprint templates"""
        try:
            with self.command_lock:
                logger.info("Processing import users command...")
                
                users_data = payload.get("users", [])
                if not users_data:
                    logger.error("No users data in import command")
                    self.send_command_response("import", "error", {
                        "message": "No users data provided"
                    })
                    return
                
                imported_count = 0
                failed_count = 0
                
                for user_data in users_data:
                    fingerprint_id = user_data.get("fingerprint_id")
                    user_name = user_data.get("user_name")
                    template_data = user_data.get("template_data")  # Base64 encoded template
                    
                    if fingerprint_id and user_name and template_data:
                        try:
                            # Decode template data
                            import base64
                            template_bytes = base64.b64decode(template_data)
                            template_list = list(template_bytes)
                            
                            # Upload template to sensor
                            if self.finger.upload_model(fingerprint_id, template_list) == adafruit_fingerprint.OK:
                                # Store template in sensor
                                if self.finger.store_model(fingerprint_id) == adafruit_fingerprint.OK:
                                    # Save to database
                                    conn = sqlite3.connect(self.db_file)
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        INSERT OR REPLACE INTO users (fingerprint_id, user_name)
                                        VALUES (?, ?)
                                    ''', (fingerprint_id, user_name))
                                    conn.commit()
                                    conn.close()
                                    
                                    imported_count += 1
                                    logger.info(f"✓ Imported user: {user_name} (ID: {fingerprint_id})")
                                else:
                                    failed_count += 1
                                    logger.error(f"✗ Failed to store template for {user_name}")
                            else:
                                failed_count += 1
                                logger.error(f"✗ Failed to upload template for {user_name}")
                                
                        except Exception as e:
                            failed_count += 1
                            logger.error(f"✗ Error importing {user_name}: {e}")
                    else:
                        failed_count += 1
                        logger.error("Missing required fields: fingerprint_id, user_name, or template_data")
                
                logger.info(f"✓ Import completed: {imported_count} successful, {failed_count} failed")
                self.send_command_response("import", "success", {
                    "imported_count": imported_count,
                    "failed_count": failed_count,
                    "message": f"Imported {imported_count} users, {failed_count} failed"
                })
                
        except Exception as e:
            logger.error(f"Error handling import command: {e}")
            self.send_command_response("import", "error", {
                "message": f"Error: {str(e)}"
            })
    
    def handle_export_command(self, payload):
        """Handle export users command with fingerprint templates"""
        try:
            with self.command_lock:
                logger.info("Processing export users command...")
                
                # Get all users from database
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                cursor.execute('SELECT fingerprint_id, user_name, created_at FROM users ORDER BY fingerprint_id')
                users = cursor.fetchall()
                conn.close()
                
                # Format users data with templates
                users_data = []
                exported_count = 0
                failed_count = 0
                
                for user in users:
                    fingerprint_id = user[0]
                    user_name = user[1]
                    created_at = user[2]
                    
                    try:
                        # Load template from sensor
                        if self.finger.load_model(fingerprint_id) == adafruit_fingerprint.OK:
                            # Get template data
                            template_data = self.finger.get_fpdata("char", 1)
                            
                            # Encode template as base64
                            import base64
                            template_base64 = base64.b64encode(bytes(template_data)).decode('utf-8')
                            
                            users_data.append({
                                "fingerprint_id": fingerprint_id,
                                "user_name": user_name,
                                "created_at": created_at,
                                "template_data": template_base64,
                                "template_size": len(template_data)
                            })
                            exported_count += 1
                            logger.debug(f"✓ Exported template for {user_name} (ID: {fingerprint_id})")
                        else:
                            failed_count += 1
                            logger.warning(f"✗ Could not load template for {user_name} (ID: {fingerprint_id})")
                            
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"✗ Error exporting {user_name}: {e}")
                
                logger.info(f"✓ Export completed: {exported_count} successful, {failed_count} failed")
                self.send_command_response("export", "success", {
                    "users": users_data,
                    "exported_count": exported_count,
                    "failed_count": failed_count,
                    "message": f"Exported {exported_count} users with templates, {failed_count} failed"
                })
                
        except Exception as e:
            logger.error(f"Error handling export command: {e}")
            self.send_command_response("export", "error", {
                "message": f"Error: {str(e)}"
            })
    
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
    
    def enroll_fingerprint(self, location):
        """Enroll a new fingerprint at the specified location"""
        try:
            logger.info(f"Starting fingerprint enrollment at location {location}")
            
            # First scan
            logger.info("Place finger on sensor for first scan...")
            while True:
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                if i == adafruit_fingerprint.NOFINGER:
                    continue
                else:
                    logger.error(f"Error getting first image: {i}")
                    return False
            
            logger.info("First image captured!")
            
            if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
                logger.error("Error converting first image")
                return False
            
            logger.info("Remove finger...")
            time.sleep(2)
            
            while self.finger.get_image() != adafruit_fingerprint.NOFINGER:
                pass
            
            # Second scan
            logger.info("Place same finger again for second scan...")
            while True:
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                if i == adafruit_fingerprint.NOFINGER:
                    continue
                else:
                    logger.error(f"Error getting second image: {i}")
                    return False
            
            logger.info("Second image captured!")
            
            if self.finger.image_2_tz(2) != adafruit_fingerprint.OK:
                logger.error("Error converting second image")
                return False
            
            # Create model
            logger.info("Creating fingerprint model...")
            if self.finger.create_model() != adafruit_fingerprint.OK:
                logger.error("Error creating model - fingers didn't match?")
                return False
            
            # Store model
            logger.info(f"Storing model at location {location}...")
            if self.finger.store_model(location) != adafruit_fingerprint.OK:
                logger.error("Error storing model")
                return False
            
            logger.info(f"✓ Fingerprint enrolled successfully at location {location}!")
            return True
            
        except Exception as e:
            logger.error(f"Error during enrollment: {e}")
            return False
    
    def scan_fingerprint_standby(self):
        """Standby fingerprint scanning"""
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
                    
                    # Search for match
                    i = self.finger.finger_search()
                    
                    if i == adafruit_fingerprint.OK:
                        # Match found
                        finger_id = self.finger.finger_id
                        confidence = self.finger.confidence
                        
                        logger.info(f"✓ Match found! ID: {finger_id}, Confidence: {confidence}")
                        
                        # Check confidence threshold
                        if confidence >= CONFIDENCE_THRESHOLD:
                            # Send approved result
                            self.send_scan_result("access_granted", finger_id)
                            # Log to PostgreSQL
                            self.postgres_db.process_fingerprint_result(finger_id, confidence, "access_granted", STORE_ID)
                        else:
                            # Send rejected result
                            logger.warning(f"Confidence too low: {confidence} < {CONFIDENCE_THRESHOLD}")
                            self.send_scan_result("access_denied", finger_id)
                            # Log to PostgreSQL
                            self.postgres_db.process_fingerprint_result(finger_id, confidence, "access_denied", STORE_ID)
                        
                        self.last_scan_time = current_time
                        return True
                    else:
                        # No match found
                        logger.info("✗ No match found")
                        self.send_scan_result("no_match", 0)
                        # Log to PostgreSQL
                        self.postgres_db.process_fingerprint_result(0, 0, "no_match", STORE_ID)
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
    
    def run_standby_scanning(self):
        """Run standby fingerprint scanning with MQTT command interruption"""
        logger.info("Starting standby fingerprint scanning...")
        logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
        logger.info(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
        logger.info("✓ Listening for MQTT commands while scanning...")
        
        try:
            while self.running:
                # Check for commands first (non-blocking)
                # MQTT commands are handled in separate thread via on_mqtt_message
                
                # Perform fingerprint scan
                self.scan_fingerprint_standby()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Scanning stopped by user")
        except Exception as e:
            logger.error(f"Error in standby scanning: {e}")
    
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
        
        if self.postgres_db:
            self.postgres_db.close()
            logger.info("PostgreSQL connection closed")
        
        if self.relay_controller:
            self.relay_controller.cleanup()
            logger.info("Relay controller cleaned up")

def main():
    """Main function"""
    client = SimpleFingerprintClient()
    
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
        
        logger.info("=" * 70)
        logger.info("SIMPLE FINGERPRINT MQTT CLIENT - Ready!")
        logger.info("=" * 70)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Fingerprint Port: {client.detected_port} (auto-detected)")
        logger.info(f"Scan Topic: {client.SCAN_TOPIC}")
        logger.info(f"Add User Topic: {client.ADD_USER_TOPIC}")
        logger.info(f"Import Topic: {client.IMPORT_TOPIC}")
        logger.info(f"Export Topic: {client.EXPORT_TOPIC}")
        logger.info(f"Action Topic: {client.ACTION_TOPIC}")
        logger.info(f"Stored Templates: {template_count}")
        logger.info(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
        logger.info("=" * 70)
        logger.info("✓ Standby scanning active")
        logger.info("✓ MQTT commands can interrupt scanning")
        logger.info("=" * 70)
        
        # Start standby scanning
        client.run_standby_scanning()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        client.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
