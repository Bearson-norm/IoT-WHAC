#!/usr/bin/env python3
"""
Dual AS608 Fingerprint MQTT Client
Supports multiple AS608 sensors with the same functionality
"""

import time
import json
import logging
import threading
import sqlite3
from datetime import datetime
import paho.mqtt.client as mqtt
from dual_sensor_manager import DualSensorManager
from dual_sensor_config import *

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DualFingerprintMQTTClient:
    """MQTT client for dual AS608 fingerprint sensors"""
    
    def __init__(self):
        self.store_id = STORE_ID
        self.mqtt_client = None
        self.sensor_manager = None
        self.connected = False
        self.running = True
        self.enrolling = False
        self.command_lock = threading.Lock()
        self.db_file = DATABASE_FILE
        
        # Initialize database
        self.init_database()
        
        # Initialize sensor manager
        self.sensor_manager = DualSensorManager(SENSORS)
        
        # Setup MQTT client
        self.setup_mqtt_client()
    
    def init_database(self):
        """Initialize SQLite database for user management"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    fingerprint_id INTEGER PRIMARY KEY,
                    user_name TEXT NOT NULL,
                    sensor_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            ''')
            
            # Create scan_logs table
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
    
    def setup_mqtt_client(self):
        """Initialize MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(client_id="dual_whac_fingerprint_client")
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            # Set authentication if provided
            if hasattr(self, 'MQTT_USERNAME') and hasattr(self, 'MQTT_PASSWORD'):
                self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.mqtt_client.loop_start()
            
        except Exception as e:
            logger.error(f"Error setting up MQTT client: {e}")
            raise
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✓ MQTT broker connected successfully")
            
            # Subscribe to command topics
            self.mqtt_client.subscribe(MQTT_TOPICS["add_user"], qos=MQTT_QOS)
            self.mqtt_client.subscribe(MQTT_TOPICS["import_users"], qos=MQTT_QOS)
            self.mqtt_client.subscribe(MQTT_TOPICS["export_users"], qos=MQTT_QOS)
            self.mqtt_client.subscribe(MQTT_TOPICS["relay_action"], qos=MQTT_QOS)
            
            logger.info("✓ Subscribed to command topics:")
            for topic_name, topic in MQTT_TOPICS.items():
                if topic_name != "scan_result":
                    logger.info(f"  - {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT commands"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received command on {topic}: {payload}")
            
            # Handle different command topics
            if topic == MQTT_TOPICS["add_user"]:
                self.handle_add_user_command(payload)
            elif topic == MQTT_TOPICS["import_users"]:
                self.handle_import_command(payload)
            elif topic == MQTT_TOPICS["export_users"]:
                self.handle_export_command(payload)
            elif topic == MQTT_TOPICS["relay_action"]:
                self.handle_relay_command(payload)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def send_scan_result(self, scan_result):
        """Send scan result to MQTT server"""
        if not self.connected:
            logger.error("MQTT not connected, cannot send data")
            return False
        
        try:
            # Get user info from database
            user_info = self.get_user_info(scan_result['finger_id'])
            username = user_info.get('username') if user_info else None
            
            # Prepare scan data
            data = {
                "store_id": self.store_id,
                "timestamp": scan_result['timestamp'],
                "status": scan_result['status'],
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
            
            # Send to MQTT
            payload = json.dumps(data)
            result = self.mqtt_client.publish(MQTT_TOPICS["scan_result"], payload, qos=MQTT_QOS)
            
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
        """Get user information from database"""
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
        """Log scan result to database"""
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
        """Handle add user command"""
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
        """Handle import users command"""
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
                            # in the AS608Driver class
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
        """Handle export users command"""
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
        """Handle relay control command"""
        try:
            command = payload.get('command')
            user_id = payload.get('user_id')
            action = payload.get('action')
            source = payload.get('source')
            
            logger.info(f"Received relay command: {command} for user {user_id}")
            
            # Note: Relay control would need to be implemented
            # based on your hardware setup
            
            # Send status update
            self.send_relay_status(command, user_id, action, source)
                
        except Exception as e:
            logger.error(f"Error handling relay command: {e}")
    
    def send_relay_status(self, command, user_id, action, source):
        """Send relay status update"""
        try:
            if not self.connected:
                return False
            
            payload = {
                'command': command,
                'user_id': user_id,
                'action': action,
                'source': source,
                'timestamp': datetime.now().isoformat(),
                'device_id': 'DUAL_AS608',
                'status': 'completed'
            }
            
            result = self.mqtt_client.publish(MQTT_TOPICS["relay_status"], json.dumps(payload))
            
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
        """Send command response back to MQTT"""
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
        """Standby scanning for all sensors"""
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
            
            # Send results
            for result in results:
                self.send_scan_result(result)
                
        except Exception as e:
            logger.error(f"Error during standby scanning: {e}")
    
    def run_standby_scanning(self):
        """Run standby fingerprint scanning"""
        logger.info("Starting dual sensor standby fingerprint scanning...")
        logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
        logger.info(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
        
        # Show sensor status
        status = self.sensor_manager.get_sensor_status()
        for sensor_id, sensor_status in status.items():
            if sensor_status['enabled']:
                logger.info(f"✓ {sensor_id}: {sensor_status['description']} - {sensor_status['port']} - {'Connected' if sensor_status['connected'] else 'Disconnected'}")
        
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
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        self.running = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        
        if self.sensor_manager:
            self.sensor_manager.disconnect_all_sensors()
            logger.info("All sensors disconnected")

def main():
    """Main function"""
    client = DualFingerprintMQTTClient()
    
    try:
        # Connect to all sensors
        if not client.sensor_manager.connect_all_sensors():
            logger.error("Failed to connect to any sensors")
            return 1
        
        # Wait for MQTT connection
        timeout = 10
        start_time = time.time()
        while not client.connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not client.connected:
            logger.error("Failed to connect to MQTT broker")
            return 1
        
        # Show initial status
        template_counts = client.sensor_manager.get_template_count()
        
        logger.info("=" * 70)
        logger.info("DUAL AS608 FINGERPRINT MQTT CLIENT - Ready!")
        logger.info("=" * 70)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Scan Topic: {MQTT_TOPICS['scan_result']}")
        logger.info(f"Add User Topic: {MQTT_TOPICS['add_user']}")
        logger.info(f"Import Topic: {MQTT_TOPICS['import_users']}")
        logger.info(f"Export Topic: {MQTT_TOPICS['export_users']}")
        logger.info(f"Action Topic: {MQTT_TOPICS['relay_action']}")
        
        for sensor_id, count in template_counts.items():
            logger.info(f"Stored Templates ({sensor_id}): {count}")
        
        logger.info(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
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
    exit(main())
