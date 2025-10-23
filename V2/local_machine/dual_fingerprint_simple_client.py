#!/usr/bin/env python3
"""
Dual AS608 Fingerprint MQTT Client
Based on existing system structure with 3.3V support
- Standby fingerprint scanning on dual sensors
- Simple JSON format
- MQTT command handling for user management
"""

import time
import json
import logging
import sys
import sqlite3
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from dual_sensor_manager import DualSensorManager
from dual_sensor_config import *

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

class DualFingerprintSimpleClient:
    """Dual AS608 Fingerprint MQTT Client based on existing system"""
    
    def __init__(self):
        self.store_id = STORE_ID
        self.mqtt_client = None
        self.sensor_manager = None
        self.connected = False
        self.running = True
        self.enrolling = False  # Flag to pause scanning during enrollment
        self.command_lock = threading.Lock()
        self.db_file = DATABASE_FILE
        self.init_database()
        
        # Relay control (same as existing system)
        self.relay_pin = RELAY_CONFIG["pin"]
        self.setup_gpio()
        
        # Initialize sensor manager
        self.sensor_manager = DualSensorManager(SENSORS)
        
        # MQTT Topics (same as existing system)
        self.SCAN_TOPIC = MQTT_TOPICS["scan_result"]  # "WHAC/Store001/in" - for scan results
        self.ADD_USER_TOPIC = MQTT_TOPICS["add_user"]  # for adding users
        self.IMPORT_TOPIC = MQTT_TOPICS["import_users"]  # for importing users
        self.EXPORT_TOPIC = MQTT_TOPICS["export_users"]  # for exporting users
        self.ACTION_TOPIC = MQTT_TOPICS["relay_action"]  # for relay control commands
        self.STATUS_TOPIC = MQTT_TOPICS["relay_status"]  # for status updates
        self.EXIT_TOPIC = MQTT_TOPICS["exit_request"]  # for exit requests
        
        # Initialize exit button controller (same as existing system)
        self.exit_controller = None
        try:
            from exit_button_controller import ExitButtonController
            self.exit_controller = ExitButtonController()
            logger.info("✅ Exit button controller initialized")
        except Exception as e:
            logger.warning(f"⚠️  Exit button controller initialization failed: {e}")
        
        # Initialize MP3 notification system (same as existing system)
        self.mp3_system = None
        try:
            from mp3_notification_system import MP3NotificationSystem
            self.mp3_system = MP3NotificationSystem()
            logger.info("✅ MP3 notification system initialized")
        except Exception as e:
            logger.warning(f"⚠️  MP3 notification system initialization failed: {e}")
    
    def setup_gpio(self):
        """Setup GPIO for relay control (same as existing system)"""
        try:
            import RPi.GPIO as GPIO
            GPIO.setwarnings(False)  # Disable GPIO warnings
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.relay_pin, GPIO.OUT)
            GPIO.output(self.relay_pin, GPIO.LOW)  # Start with relay OFF
            logger.info(f"✓ GPIO setup complete - Relay on pin {self.relay_pin}")
        except ImportError:
            logger.warning("RPi.GPIO not available - relay control disabled")
            self.relay_pin = None
        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
            self.relay_pin = None
    
    def control_relay(self, action, duration=10):
        """Control relay for specified duration (same as existing system)"""
        if not self.relay_pin:
            logger.warning("Relay control not available")
            return
        
        try:
            import RPi.GPIO as GPIO
            
            if action == "grant":
                logger.info(f"🔓 Granting access - Relay ON for {duration} seconds")
                GPIO.output(self.relay_pin, GPIO.HIGH)
                time.sleep(duration)
                GPIO.output(self.relay_pin, GPIO.LOW)
                logger.info("🔒 Access period ended - Relay OFF")
            elif action == "deny":
                logger.info("🚫 Access denied - Relay remains OFF")
                GPIO.output(self.relay_pin, GPIO.LOW)
                
        except Exception as e:
            logger.error(f"Relay control error: {e}")
    
    def init_database(self):
        """Initialize SQLite database for user management (same as existing system)"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create users table (enhanced for dual sensor)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    fingerprint_id INTEGER PRIMARY KEY,
                    user_name TEXT NOT NULL,
                    sensor_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            ''')
            
            # Create scan_logs table (enhanced for dual sensor)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT,
                    device_id TEXT,
                    fingerprint_id INTEGER,
                    user_name TEXT,
                    confidence INTEGER,
                    status TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add test user if database is empty
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                cursor.execute("INSERT INTO users (fingerprint_id, user_name, sensor_id) VALUES (1, 'Test User', 'sensor_1')")
                logger.info("✓ Added test user: Test User (ID: 1)")
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Database initialized: {self.db_file}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def connect_mqtt(self):
        """Connect to MQTT broker (same as existing system)"""
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client = mqtt.Client(client_id="dual_whac_fingerprint_client")
            
            # Set authentication if provided
            if MQTT_USERNAME and MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
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
        """MQTT connection callback (same as existing system)"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT client connected")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback (same as existing system)"""
        self.connected = False
        logger.warning(f"MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT commands (same as existing system)"""
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
    
    def send_scan_result(self, scan_result):
        """Send scan result in simple format (same as existing system)"""
        if not self.connected:
            logger.error("MQTT not connected, cannot send data")
            return False
        
        try:
            # Get user info from local database
            user_info = self.get_user_info(scan_result['finger_id'])
            username = user_info.get('username') if user_info else None
            
            # Simple JSON format as requested (enhanced for dual sensor)
            data = {
                "store_id": self.store_id,
                "timestamp": scan_result['timestamp'],
                "status": scan_result['status'],  # "Match" or "Not Match"
                "fingerprint_id": scan_result['finger_id'],
                "device_id": scan_result['device_id'],
                "sensor_id": scan_result['sensor_id'],
                "sensor_description": scan_result['description']
            }
            
            # Add username if available
            if username:
                data["username"] = username
            
            # Add confidence if provided
            if scan_result['confidence'] > 0:
                data["confidence"] = scan_result['confidence']
            
            # Log scan to database
            self.log_scan(scan_result, username)
            
            payload = json.dumps(data)
            result = self.mqtt_client.publish(self.SCAN_TOPIC, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Scan result sent: {scan_result['status']} - {scan_result['sensor_id']} - ID: {scan_result['finger_id']} ({username})")
                return True
            else:
                logger.error(f"✗ Failed to publish scan result (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending scan result: {e}")
            return False
    
    def get_user_info(self, fingerprint_id):
        """Get user information from local database (same as existing system)"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT user_name FROM users WHERE fingerprint_id = ?", (fingerprint_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {"username": result[0]}
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def log_scan(self, scan_result, username):
        """Log scan result to database (enhanced for dual sensor)"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_logs (sensor_id, device_id, fingerprint_id, user_name, confidence, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                scan_result['sensor_id'],
                scan_result['device_id'],
                scan_result['finger_id'],
                username,
                scan_result['confidence'],
                scan_result['status']
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging scan: {e}")
    
    def handle_add_user_command(self, payload):
        """Handle add user command (same as existing system)"""
        try:
            with self.command_lock:
                logger.info("Processing add user command...")
                
                # Extract command data
                fingerprint_id = payload.get("fingerprint_id")
                user_name = payload.get("user_name")
                sensor_id = payload.get("sensor_id", "sensor_1")  # Default to first sensor
                
                if not fingerprint_id or not user_name:
                    logger.error("Missing fingerprint_id or user_name in add user command")
                    self.send_command_response("add_user", "error", {
                        "message": "Missing required fields: fingerprint_id, user_name"
                    })
                    return
                
                # Set enrolling flag to pause scanning
                self.enrolling = True
                logger.info("⏸️  Pausing fingerprint scanning during enrollment...")
                
                # Wait a moment for scanning loop to stop
                time.sleep(0.5)
                
                try:
                    # Enroll fingerprint on specified sensor
                    if self.sensor_manager.enroll_fingerprint(sensor_id, fingerprint_id):
                        # Save to database
                        conn = sqlite3.connect(self.db_file)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO users (fingerprint_id, user_name, sensor_id)
                            VALUES (?, ?, ?)
                        ''', (fingerprint_id, user_name, sensor_id))
                        conn.commit()
                        conn.close()
                        
                        logger.info(f"✓ User added: {user_name} (ID: {fingerprint_id}) on {sensor_id}")
                        
                        # Send confirmation
                        self.send_command_response("add_user", "success", {
                            "fingerprint_id": fingerprint_id,
                            "user_name": user_name,
                            "sensor_id": sensor_id,
                            "message": "User added successfully"
                        })
                    else:
                        logger.error(f"✗ Failed to enroll fingerprint for user: {user_name}")
                        self.send_command_response("add_user", "error", {
                            "message": "Failed to enroll fingerprint"
                        })
                finally:
                    # Always resume scanning after enrollment
                    self.enrolling = False
                    logger.info("▶️  Resuming fingerprint scanning...")
                    
        except Exception as e:
            logger.error(f"Error handling add user command: {e}")
            self.enrolling = False
            self.send_command_response("add_user", "error", {
                "message": f"Error: {str(e)}"
            })
    
    def handle_import_command(self, payload):
        """Handle import users command (same as existing system)"""
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
                    sensor_id = user_data.get("sensor_id", "sensor_1")
                    template_data = user_data.get("template_data")
                    
                    if fingerprint_id and user_name and template_data:
                        try:
                            # Note: Template import would need to be implemented
                            # in the sensor manager
                            logger.warning(f"Template import not yet implemented for {user_name}")
                            failed_count += 1
                            
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
        """Handle export users command (same as existing system)"""
        try:
            with self.command_lock:
                logger.info("Processing export users command...")
                
                # Get all users from database
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                cursor.execute('SELECT fingerprint_id, user_name, sensor_id, created_at FROM users ORDER BY fingerprint_id')
                users = cursor.fetchall()
                conn.close()
                
                # Format users data
                users_data = []
                for user in users:
                    fingerprint_id = user[0]
                    user_name = user[1]
                    sensor_id = user[2]
                    created_at = user[3]
                    
                    users_data.append({
                        "fingerprint_id": fingerprint_id,
                        "user_name": user_name,
                        "sensor_id": sensor_id,
                        "created_at": created_at
                    })
                
                logger.info(f"✓ Export completed: {len(users_data)} users")
                self.send_command_response("export", "success", {
                    "users": users_data,
                    "exported_count": len(users_data),
                    "message": f"Exported {len(users_data)} users"
                })
                
        except Exception as e:
            logger.error(f"Error handling export command: {e}")
            self.send_command_response("export", "error", {
                "message": f"Error: {str(e)}"
            })
    
    def handle_relay_command(self, payload):
        """Handle relay control command (same as existing system)"""
        try:
            command = payload.get('command')
            user_id = payload.get('user_id')
            action = payload.get('action')
            source = payload.get('source')
            
            logger.info(f"Received relay command: {command} for user {user_id}")
            
            # Control relay based on command
            self.control_relay(command, duration=RELAY_CONFIG["access_duration"])
            
            # Send status update
            self.send_relay_status(command, user_id, action, source)
                
        except Exception as e:
            logger.error(f"Error handling relay command: {e}")
    
    def send_relay_status(self, command, user_id, action, source):
        """Send relay status update (same as existing system)"""
        try:
            if not self.connected:
                return False
            
            payload = {
                'command': command,
                'user_id': user_id,
                'action': action,
                'source': source,
                'timestamp': datetime.now().isoformat(),
                'relay_pin': self.relay_pin,
                'device_id': 'DUAL_AS608',
                'status': 'completed'
            }
            
            result = self.mqtt_client.publish(self.STATUS_TOPIC, json.dumps(payload))
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Relay status sent: {command} for user {user_id}")
                return True
            else:
                logger.error(f"✗ Failed to send relay status (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending relay status: {e}")
            return False
    
    def send_command_response(self, command_type, status, data):
        """Send command response back to MQTT (same as existing system)"""
        try:
            response = {
                "store_id": self.store_id,
                "timestamp": datetime.now().isoformat(),
                "command": command_type,
                "status": status,
                "data": data,
                "device_id": "DUAL_AS608"
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
    
    def scan_all_sensors_standby(self):
        """Standby scanning for all sensors (enhanced for dual sensor)"""
        try:
            # Skip scanning if enrollment is in progress
            if self.enrolling:
                return
            
            # Get ready sensors
            ready_sensors = self.sensor_manager.get_ready_sensors()
            
            if not ready_sensors:
                return
            
            # Scan all ready sensors
            results = []
            for sensor_id in ready_sensors:
                result = self.sensor_manager.scan_sensor(sensor_id, CONFIDENCE_THRESHOLD)
                if result:
                    results.append(result)
            
            # Send results and handle notifications
            for result in results:
                self.send_scan_result(result)
                
                # Play notifications (same as existing system)
                if result['status'] == 'Match':
                    # Play access granted notification
                    if self.mp3_system:
                        self.mp3_system.play_access_granted(result['finger_id'])
                else:
                    # Play access denied notification
                    if self.mp3_system:
                        self.mp3_system.play_access_denied("unknown")
                
        except Exception as e:
            logger.error(f"Error during standby scanning: {e}")
    
    def run_standby_scanning(self):
        """Run standby fingerprint scanning (same as existing system)"""
        logger.info("Starting dual sensor standby fingerprint scanning...")
        logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
        logger.info(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
        
        # Show sensor status
        status = self.sensor_manager.get_sensor_status()
        for sensor_id, sensor_status in status.items():
            if sensor_status['enabled']:
                logger.info(f"✓ {sensor_id}: {sensor_status['description']} - {sensor_status['port']} ({sensor_status['voltage']}) - {'Connected' if sensor_status['connected'] else 'Disconnected'}")
        
        logger.info("✓ Listening for MQTT commands while scanning...")
        
        try:
            while self.running:
                # Perform fingerprint scan on all sensors
                self.scan_all_sensors_standby()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Scanning stopped by user")
        except Exception as e:
            logger.error(f"Error in standby scanning: {e}")
    
    def cleanup(self):
        """Clean up resources (same as existing system)"""
        logger.info("Cleaning up resources...")
        self.running = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        
        if self.sensor_manager:
            self.sensor_manager.disconnect_all_sensors()
            logger.info("All sensors disconnected")
        
        # Cleanup GPIO
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            logger.info("GPIO cleaned up")
        except:
            pass

def main():
    """Main function (same as existing system)"""
    client = DualFingerprintSimpleClient()
    
    try:
        # Connect to all sensors
        if not client.sensor_manager.connect_all_sensors():
            logger.error("Failed to connect to any sensors")
            return 1
        
        # Connect to MQTT broker
        if not client.connect_mqtt():
            logger.error("Failed to connect to MQTT broker")
            return 1
        
        # Show initial status
        template_counts = client.sensor_manager.get_template_count()
        
        logger.info("=" * 70)
        logger.info("DUAL AS608 FINGERPRINT MQTT CLIENT - Ready!")
        logger.info("=" * 70)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Fingerprint Ports: {[config['port'] for config in SENSORS.values()]}")
        logger.info(f"Scan Topic: {client.SCAN_TOPIC}")
        logger.info(f"Add User Topic: {client.ADD_USER_TOPIC}")
        logger.info(f"Import Topic: {client.IMPORT_TOPIC}")
        logger.info(f"Export Topic: {client.EXPORT_TOPIC}")
        logger.info(f"Action Topic: {client.ACTION_TOPIC}")
        
        for sensor_id, count in template_counts.items():
            logger.info(f"Stored Templates ({sensor_id}): {count}")
        
        logger.info(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
        logger.info(f"Hardware: 3.3V AS608 sensors (no level shifter needed)")
        logger.info("=" * 70)
        logger.info("✓ Dual sensor scanning active")
        logger.info("✓ MQTT commands can interrupt scanning")
        logger.info("=" * 70)
        
        # Wait for sensors to fully stabilize
        logger.info("⏳ Waiting for sensors to fully stabilize...")
        time.sleep(5.0)
        logger.info("🚀 Starting dual fingerprint scanning...")
        
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
