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
        self.enrolling = False  # Flag to pause scanning during enrollment
        self.command_lock = threading.Lock()
        self.db_file = "fingerprints.db"
        self.init_database()
        
        # Relay control
        self.relay_pin = 18  # GPIO pin for relay
        self.setup_gpio()
        
        # Use configured port directly (skip auto-detection)
        self.detected_port = FINGERPRINT_PORT
        logger.info(f"🎯 Using configured port: {self.detected_port}")
        
        # Verify the port exists
        if not os.path.exists(self.detected_port):
            logger.warning(f"⚠️  Configured port {self.detected_port} does not exist!")
            logger.info("🔍 Falling back to auto-detection...")
            self.detected_port = self.auto_detect_fingerprint_port()
        
        # MQTT Topics
        self.SCAN_TOPIC = MQTT_TOPIC  # "WHAC/Store001/in" - for scan results
        self.ADD_USER_TOPIC = "WHAC/Store001/add_user"  # for adding users
        self.IMPORT_TOPIC = "WHAC/Store001/import"  # for importing users
        self.EXPORT_TOPIC = "WHAC/Store001/export"  # for exporting users
        self.ACTION_TOPIC = "WHAC/Store001/action"  # for relay control commands
        self.STATUS_TOPIC = "WHAC/Store001/relay_status"  # for status updates
    
    def setup_gpio(self):
        """Setup GPIO for relay control"""
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
        """Control relay for specified duration"""
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
    
    def auto_detect_fingerprint_port(self):
        """Auto-detect AS608 fingerprint sensor port"""
        logger.info("🔍 Auto-detecting fingerprint sensor port...")
        
        # Import serial at the beginning of the function
        import serial
        
        # First, let's see what ports are actually available
        if os.name == 'posix':  # Linux/Unix (Raspberry Pi)
            logger.info("📋 Scanning for available serial ports...")
            all_ports = []
            
            # Check common USB serial patterns
            usb_patterns = ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/tty.usbserial*', '/dev/tty.usbmodem*']
            for pattern in usb_patterns:
                found_ports = glob.glob(pattern)
                all_ports.extend(found_ports)
                if found_ports:
                    logger.info(f"  Found USB ports: {found_ports}")
            
            # Check built-in serial ports
            builtin_patterns = ['/dev/ttyS*', '/dev/ttyAMA*', '/dev/serial0', '/dev/serial1']
            for pattern in builtin_patterns:
                if pattern.startswith('/dev/serial'):
                    # Add specific serial ports
                    if os.path.exists(pattern):
                        all_ports.append(pattern)
                        logger.info(f"  Found serial port: {pattern}")
                else:
                    found_ports = glob.glob(pattern)
                    all_ports.extend(found_ports)
                    if found_ports:
                        logger.info(f"  Found built-in ports: {found_ports}")
            
            # Remove duplicates and sort
            possible_ports = sorted(list(set(all_ports)))
            logger.info(f"📋 Total available ports: {possible_ports}")
            
        elif os.name == 'nt':  # Windows
            try:
                import serial.tools.list_ports
                available_ports = [port.device for port in serial.tools.list_ports.comports()]
                possible_ports = available_ports
                logger.info(f"📋 Windows COM ports: {possible_ports}")
            except ImportError:
                possible_ports = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8"]
                logger.info(f"📋 Using default COM ports: {possible_ports}")
        else:
            # Fallback for other systems
            possible_ports = [
                "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyUSB3",
                "/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2", "/dev/ttyACM3",
                "/dev/ttyS0", "/dev/ttyS1", "/dev/ttyS2", "/dev/ttyS3"
            ]
            logger.info(f"📋 Using fallback ports: {possible_ports}")
        
        if not possible_ports:
            logger.warning("⚠️  No serial ports found! Check your AS608 connection.")
            return FINGERPRINT_PORT
        
        # Prioritize the configured port if it exists
        if FINGERPRINT_PORT in possible_ports:
            possible_ports.remove(FINGERPRINT_PORT)
            possible_ports.insert(0, FINGERPRINT_PORT)
            logger.info(f"🎯 Prioritizing configured port: {FINGERPRINT_PORT}")
        
        logger.info(f"🔍 Testing {len(possible_ports)} ports for AS608 sensor...")
        
        for port in possible_ports:
            if not os.path.exists(port):
                logger.debug(f"  Port {port} does not exist, skipping")
                continue
                
            try:
                logger.info(f"🔌 Testing port: {port}")
                
                # Try to connect to the port
                test_uart = serial.Serial(port, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)
                
                # Try to create fingerprint object
                test_finger = adafruit_fingerprint.Adafruit_Fingerprint(test_uart)
                
                # Try to read templates (this will fail if not an AS608)
                result = test_finger.read_templates()
                
                if result == adafruit_fingerprint.OK:
                    logger.info(f"✅ AS608 fingerprint sensor found on {port}!")
                    logger.info(f"   📊 Templates: {test_finger.template_count}")
                    test_uart.close()
                    return port
                else:
                    logger.debug(f"   ❌ Not an AS608 sensor on {port} (result: {result})")
                    test_uart.close()
                    
            except serial.SerialException as e:
                logger.debug(f"   ❌ Serial error on {port}: {e}")
                continue
            except Exception as e:
                logger.debug(f"   ❌ General error on {port}: {e}")
                continue
        
        # If auto-detection fails, use the configured port
        logger.warning(f"⚠️  Auto-detection failed, using configured port: {FINGERPRINT_PORT}")
        logger.warning("💡 Make sure your AS608 sensor is connected and powered on")
        logger.warning("💡 You can also manually set the port in config.py")
        
        # List available ports for debugging
        self.list_available_ports()
        
        return FINGERPRINT_PORT
    
    def list_available_ports(self):
        """List all available serial ports for debugging"""
        logger.info("🔍 Available serial ports:")
        if os.name == 'posix':  # Linux/Unix
            import glob
            patterns = ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyS*', '/dev/ttyAMA*']
            for pattern in patterns:
                ports = glob.glob(pattern)
                if ports:
                    logger.info(f"  {pattern}: {ports}")
            
            # Check specific serial ports
            serial_ports = ['/dev/serial0', '/dev/serial1']
            for port in serial_ports:
                if os.path.exists(port):
                    logger.info(f"  Serial port: {port}")
        elif os.name == 'nt':  # Windows
            try:
                import serial.tools.list_ports
                ports = [port.device for port in serial.tools.list_ports.comports()]
                logger.info(f"  COM ports: {ports}")
            except ImportError:
                logger.info("  serial.tools.list_ports not available")
    
    def connect_sensor(self, retries=3):
        """Connect to AS608 fingerprint sensor"""
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to fingerprint sensor on {self.detected_port} (attempt {attempt + 1})")
                self.uart = serial.Serial(self.detected_port, baudrate=BAUD_RATE, timeout=2)
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
    
    def handle_relay_command(self, payload):
        """Handle relay control command"""
        try:
            command = payload.get('command')
            user_id = payload.get('user_id')
            action = payload.get('action')
            source = payload.get('source')
            
            logger.info(f"Received relay command: {command} for user {user_id}")
            
            # Control relay based on command
            self.control_relay(command, duration=10)
            
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
                'relay_pin': self.relay_pin,
                'device_id': 'AS608_001',
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
    
    def send_scan_result(self, status, fingerprint_id, confidence=None):
        """Send scan result in simple format"""
        if not self.connected:
            logger.error("MQTT not connected, cannot send data")
            return False
        
        try:
            # Get user info from local database
            user_info = self.get_user_info(fingerprint_id)
            username = user_info.get('username') if user_info else None
            
            # Simple JSON format as requested
            data = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "status": status,  # "Match" or "Not Match"
                "fingerprint_id": fingerprint_id,
                "device_id": "AS608_001"
            }
            
            # Add username if available
            if username:
                data["username"] = username
            
            # Add confidence if provided
            if confidence is not None:
                data["confidence"] = confidence
            
            payload = json.dumps(data)
            result = self.mqtt_client.publish(self.SCAN_TOPIC, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Scan result sent: {status} - ID: {fingerprint_id} ({username})")
                return True
            else:
                logger.error(f"✗ Failed to publish scan result (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending scan result: {e}")
            return False
    
    def get_user_info(self, fingerprint_id):
        """Get user information from local database"""
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
                
                # Set enrolling flag to pause scanning
                self.enrolling = True
                logger.info("⏸️  Pausing fingerprint scanning during enrollment...")
                
                # Wait a moment for scanning loop to stop
                time.sleep(0.5)
                
                try:
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
                finally:
                    # Always resume scanning after enrollment (success or failure)
                    self.enrolling = False
                    logger.info("▶️  Resuming fingerprint scanning...")
                    
        except Exception as e:
            logger.error(f"Error handling add user command: {e}")
            self.enrolling = False  # Ensure flag is reset on error
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
            logger.info(f"Using sensor on port: {self.detected_port}")
            
            # Check if sensor is still connected
            if not self.finger:
                logger.error("❌ Fingerprint sensor not connected!")
                return False
            
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
                    logger.error("💡 Check sensor connection and try again")
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
            # Skip scanning if enrollment is in progress
            if self.enrolling:
                return False
            
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
                        
                        # Always send scan result with status "Match" and confidence
                        self.send_scan_result("Match", finger_id, confidence)
                        
                        self.last_scan_time = current_time
                        return True
                    else:
                        # No match found
                        logger.info("✗ No match found")
                        self.send_scan_result("Not Match", 0, 0)
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
        
        # Cleanup GPIO
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            logger.info("GPIO cleaned up")
        except:
            pass

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
        template_count = client.get_template_count()
        
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
