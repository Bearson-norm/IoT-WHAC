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
        self.db_file = "fingerprints_simple.db"  # Separate DB file to avoid conflicts
        self.port_lock_file = None  # File lock for serial port
        self.gpio_lock_file = None  # File lock for GPIO
        self.pid_file = None  # PID file to prevent multiple instances
        
        # Check for existing instances
        self.check_existing_instance()
        
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
    
    def check_existing_instance(self):
        """Check if another instance of this program is already running"""
        try:
            pid_file_path = "/tmp/fingerprint_simple_client.pid"
            if os.path.exists(pid_file_path):
                # Check if the process is still running
                try:
                    with open(pid_file_path, 'r') as f:
                        old_pid = int(f.read().strip())
                    # Check if process exists (Unix only)
                    if os.name == 'posix':
                        try:
                            os.kill(old_pid, 0)  # Signal 0 doesn't kill, just checks
                            logger.error(f"❌ Another instance is already running (PID: {old_pid})")
                            logger.error("💡 Stop the existing instance first or remove /tmp/fingerprint_simple_client.pid")
                            raise SystemExit(1)
                        except OSError:
                            # Process doesn't exist, remove stale PID file
                            os.remove(pid_file_path)
                except (ValueError, IOError):
                    # Invalid PID file, remove it
                    os.remove(pid_file_path)
            
            # Create PID file
            with open(pid_file_path, 'w') as f:
                f.write(str(os.getpid()))
            self.pid_file = pid_file_path
            logger.debug(f"✓ PID file created: {pid_file_path}")
        except Exception as e:
            logger.warning(f"Could not create PID file: {e}")
    
    def setup_gpio(self):
        """Setup GPIO for relay control with conflict detection"""
        try:
            import RPi.GPIO as GPIO
            
            # Check if GPIO is already in use by another process
            gpio_lock_path = f"/tmp/gpio_pin_{self.relay_pin}.lock"
            if os.path.exists(gpio_lock_path):
                try:
                    with open(gpio_lock_path, 'r') as f:
                        old_pid = int(f.read().strip())
                    if os.name == 'posix':
                        try:
                            os.kill(old_pid, 0)
                            logger.error(f"❌ GPIO pin {self.relay_pin} is already in use by process {old_pid}")
                            logger.error("💡 Stop the other process first or remove the lock file")
                            raise SystemExit(1)
                        except OSError:
                            # Process doesn't exist, remove stale lock
                            os.remove(gpio_lock_path)
                except (ValueError, IOError):
                    os.remove(gpio_lock_path)
            
            # Create GPIO lock file
            with open(gpio_lock_path, 'w') as f:
                f.write(str(os.getpid()))
            self.gpio_lock_file = gpio_lock_path
            
            GPIO.setwarnings(False)  # Disable GPIO warnings
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.relay_pin, GPIO.OUT)
            GPIO.output(self.relay_pin, GPIO.LOW)  # Start with relay OFF
            logger.info(f"✓ GPIO setup complete - Relay on pin {self.relay_pin}")
        except ImportError:
            logger.warning("RPi.GPIO not available - relay control disabled")
            self.relay_pin = None
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
            self.relay_pin = None
    
    def control_relay(self, action, duration=10):
        """Control relay for specified duration (NON-BLOCKING)
        
        FIXED: Previously used time.sleep() which blocked the thread.
        Now uses background thread to handle relay timer without blocking.
        """
        if not self.relay_pin:
            logger.warning("Relay control not available")
            return
        
        try:
            import RPi.GPIO as GPIO
            
            if action == "grant":
                # Cancel previous relay timer if still running
                if hasattr(self, '_relay_thread') and self._relay_thread.is_alive():
                    logger.warning("⚠️ Previous relay command still running, new command will override")
                
                logger.info(f"🔓 Granting access - Relay ON for {duration} seconds")
                GPIO.output(self.relay_pin, GPIO.HIGH)
                
                # Start timer in separate thread (NON-BLOCKING)
                # This prevents blocking MQTT loop or scanning operations
                self._relay_thread = threading.Thread(
                    target=self._relay_timer_thread,
                    args=(duration,),
                    daemon=True,
                    name="RelayTimer"
                )
                self._relay_thread.start()
                logger.debug("✅ Relay timer started in background thread")
                
            elif action == "deny":
                logger.info("🚫 Access denied - Relay remains OFF")
                GPIO.output(self.relay_pin, GPIO.LOW)
                
        except Exception as e:
            logger.error(f"Relay control error: {e}")
    
    def _relay_timer_thread(self, duration):
        """Background thread to turn off relay after specified duration
        
        This runs in a separate thread so it doesn't block the main execution.
        """
        try:
            import RPi.GPIO as GPIO
            time.sleep(duration)
            GPIO.output(self.relay_pin, GPIO.LOW)
            logger.info("🔒 Access period ended - Relay OFF")
        except Exception as e:
            logger.error(f"Relay timer thread error: {e}")
            # Ensure relay is turned off on error
            try:
                import RPi.GPIO as GPIO
                GPIO.output(self.relay_pin, GPIO.LOW)
            except:
                pass
    
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
    
    def acquire_port_lock(self, port):
        """Acquire exclusive lock on serial port to prevent conflicts"""
        if os.name != 'posix':
            return True  # File locking not available on Windows
        
        lock_file_path = f"/tmp/serial_port_{os.path.basename(port)}.lock"
        
        # Check if lock exists and process is still running
        if os.path.exists(lock_file_path):
            try:
                with open(lock_file_path, 'r') as f:
                    old_pid = int(f.read().strip())
                try:
                    os.kill(old_pid, 0)  # Check if process exists
                    logger.error(f"❌ Port {port} is locked by process {old_pid}")
                    logger.error("💡 Stop the other process first or remove the lock file")
                    return False
                except OSError:
                    # Process doesn't exist, remove stale lock
                    os.remove(lock_file_path)
            except (ValueError, IOError):
                os.remove(lock_file_path)
        
        # Create lock file
        try:
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            self.port_lock_file = lock_file_path
            logger.debug(f"✓ Port lock acquired: {lock_file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create port lock: {e}")
            return False
    
    def release_port_lock(self):
        """Release port lock"""
        if self.port_lock_file and os.path.exists(self.port_lock_file):
            try:
                os.remove(self.port_lock_file)
                logger.debug(f"✓ Port lock released: {self.port_lock_file}")
            except Exception as e:
                logger.warning(f"Failed to remove port lock: {e}")
    
    def connect_sensor(self, retries=3):
        """Connect to AS608 fingerprint sensor with port locking"""
        # Acquire port lock first
        if not self.acquire_port_lock(self.detected_port):
            logger.error(f"❌ Cannot acquire lock on port {self.detected_port}")
            return False
        
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to fingerprint sensor on {self.detected_port} (attempt {attempt + 1})")
                
                # Additional check if port is already in use (using lsof)
                try:
                    import subprocess
                    result = subprocess.run(['lsof', self.detected_port], capture_output=True, text=True)
                    if result.stdout:
                        logger.warning(f"⚠️  Port {self.detected_port} is already in use:")
                        logger.warning(f"   {result.stdout}")
                        logger.info("💡 Try: sudo pkill -f python3")
                except:
                    pass  # lsof not available, continue anyway
                
                self.uart = serial.Serial(self.detected_port, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)  # Give sensor time to stabilize
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                logger.info("✓ Sensor connected successfully!")
                return True
                    
            except serial.SerialException as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if "Permission denied" in str(e) or "could not open port" in str(e).lower():
                    logger.error("❌ Port is already in use by another process")
                    self.release_port_lock()
                    return False
                if self.uart:
                    try:
                        self.uart.close()
                    except:
                        pass
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    self.release_port_lock()
                    raise
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self.uart:
                    try:
                        self.uart.close()
                    except:
                        pass
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    self.release_port_lock()
                    raise
        return False
    
    def connect_mqtt(self):
        """Connect to MQTT broker with unique client ID"""
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            # Create unique client ID to prevent conflicts
            unique_id = f"whac_fingerprint_client_{os.getpid()}_{int(time.time())}"
            self.mqtt_client = mqtt.Client(client_id=unique_id)
            
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
        """Handle incoming MQTT commands (NON-BLOCKING)
        
        FIXED: Previously processed commands directly in MQTT callback,
        which blocked the MQTT network loop. Now uses background thread
        to process commands asynchronously.
        """
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received command on {topic}: {payload}")
            
            # Handle commands in separate thread to avoid blocking MQTT loop
            # CRITICAL: MQTT callback must return quickly to avoid losing messages
            command_thread = threading.Thread(
                target=self.handle_command_wrapper,
                args=(topic, payload),
                daemon=True,
                name=f"MQTTCommand_{topic.split('/')[-1]}"
            )
            command_thread.start()
            logger.debug(f"✅ Command processing started in background thread")
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def handle_command_wrapper(self, topic, payload):
        """Wrapper to handle MQTT commands with proper error handling
        
        This runs in a separate thread so MQTT callback can return immediately.
        """
        try:
            if topic == self.ADD_USER_TOPIC:
                self.handle_add_user_command(payload)
            elif topic == self.IMPORT_TOPIC:
                self.handle_import_command(payload)
            elif topic == self.EXPORT_TOPIC:
                self.handle_export_command(payload)
            elif topic == self.ACTION_TOPIC:
                self.handle_relay_command(payload)
            else:
                logger.warning(f"Unknown command topic: {topic}")
        except Exception as e:
            logger.error(f"Error in command handler: {e}", exc_info=True)
    
    def init_database(self):
        """Initialize simple SQLite database with timeout for concurrent access"""
        try:
            # Use timeout to handle database locking better
            conn = sqlite3.connect(self.db_file, timeout=10.0)
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
            conn = sqlite3.connect(self.db_file, timeout=10.0)
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
                        conn = sqlite3.connect(self.db_file, timeout=10.0)
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
                                    conn = sqlite3.connect(self.db_file, timeout=10.0)
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
                conn = sqlite3.connect(self.db_file, timeout=10.0)
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
        """Enroll a new fingerprint at the specified location (NON-BLOCKING with timeout)
        
        FIXED: Previously had infinite loops without timeout, causing system to hang.
        Now includes timeout protection and progress feedback.
        """
        ENROLLMENT_TIMEOUT = 30  # seconds timeout for each step
        PROGRESS_INTERVAL = 5    # seconds between progress logs
        
        try:
            logger.info(f"Starting fingerprint enrollment at location {location}")
            logger.info(f"Using sensor on port: {self.detected_port}")
            
            # Check if sensor is still connected
            if not self.finger:
                logger.error("❌ Fingerprint sensor not connected!")
                return False
            
            # First scan with timeout
            logger.info("Place finger on sensor for first scan...")
            start_time = time.time()
            last_progress_time = start_time
            
            while True:
                # Check timeout
                if time.time() - start_time > ENROLLMENT_TIMEOUT:
                    logger.error(f"❌ Enrollment timeout: No finger detected within {ENROLLMENT_TIMEOUT} seconds")
                    logger.error("💡 Please place finger on sensor and try again")
                    return False
                
                # Progress feedback every PROGRESS_INTERVAL seconds
                current_time = time.time()
                if current_time - last_progress_time >= PROGRESS_INTERVAL:
                    elapsed = int(current_time - start_time)
                    logger.info(f"⏳ Waiting for finger... ({elapsed}/{ENROLLMENT_TIMEOUT}s)")
                    last_progress_time = current_time
                
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                elif i == adafruit_fingerprint.NOFINGER:
                    time.sleep(0.1)  # Small delay to reduce CPU usage
                    continue
                else:
                    logger.error(f"Error getting first image: {i}")
                    logger.error("💡 Check sensor connection and try again")
                    return False
            
            logger.info("✓ First image captured!")
            
            if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
                logger.error("Error converting first image to template")
                return False
            
            logger.info("✓ First image converted to template")
            logger.info("Remove finger...")
            time.sleep(2)
            
            # Wait for finger removal with timeout
            logger.info("Waiting for finger removal...")
            start_time = time.time()
            while self.finger.get_image() != adafruit_fingerprint.NOFINGER:
                if time.time() - start_time > 10:  # 10 second timeout for removal
                    logger.warning("⚠️ Finger still detected after 10 seconds, continuing anyway...")
                    break
                time.sleep(0.1)
            
            logger.info("✓ Finger removed")
            
            # Second scan with timeout
            logger.info("Place same finger again for second scan...")
            start_time = time.time()
            last_progress_time = start_time
            
            while True:
                # Check timeout
                if time.time() - start_time > ENROLLMENT_TIMEOUT:
                    logger.error(f"❌ Enrollment timeout: No finger detected for second scan within {ENROLLMENT_TIMEOUT} seconds")
                    return False
                
                # Progress feedback
                current_time = time.time()
                if current_time - last_progress_time >= PROGRESS_INTERVAL:
                    elapsed = int(current_time - start_time)
                    logger.info(f"⏳ Waiting for second scan... ({elapsed}/{ENROLLMENT_TIMEOUT}s)")
                    last_progress_time = current_time
                
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                elif i == adafruit_fingerprint.NOFINGER:
                    time.sleep(0.1)
                    continue
                else:
                    logger.error(f"Error getting second image: {i}")
                    return False
            
            logger.info("✓ Second image captured!")
            
            if self.finger.image_2_tz(2) != adafruit_fingerprint.OK:
                logger.error("Error converting second image to template")
                return False
            
            logger.info("✓ Second image converted to template")
            
            # Create model
            logger.info("Creating fingerprint model...")
            if self.finger.create_model() != adafruit_fingerprint.OK:
                logger.error("Error creating model - fingers may not match or sensor error")
                logger.error("💡 Please try again with better finger placement")
                return False
            
            logger.info("✓ Fingerprint model created successfully")
            
            # Store model
            logger.info(f"Storing model at location {location}...")
            if self.finger.store_model(location) != adafruit_fingerprint.OK:
                logger.error("Error storing model - location may be full or invalid")
                return False
            
            logger.info(f"✅ Fingerprint enrolled successfully at location {location}!")
            return True
            
        except Exception as e:
            logger.error(f"Error during enrollment: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def scan_fingerprint_standby(self):
        """Standby fingerprint scanning (THREAD-SAFE)
        
        FIXED: Previously had no lock protection, causing race conditions
        when command handlers (enrollment/import) accessed sensor simultaneously.
        Now uses command_lock to ensure only one operation accesses sensor at a time.
        """
        try:
            # Skip scanning if enrollment is in progress
            if self.enrolling:
                return False
            
            # Check if enough time has passed since last scan
            current_time = time.time()
            if current_time - self.last_scan_time < SCAN_INTERVAL:
                return False
            
            # CRITICAL: Lock sensor access to prevent race condition
            # Serial port (UART) can only handle one operation at a time
            # This ensures scanning and command operations don't conflict
            with self.command_lock:
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
                            # Match found - store values before releasing lock
                            finger_id = self.finger.finger_id
                            confidence = self.finger.confidence
                            scan_result = {
                                "status": "Match",
                                "fingerprint_id": finger_id,
                                "confidence": confidence
                            }
                        else:
                            # No match found
                            logger.debug("No match found")
                            scan_result = {
                                "status": "Not Match",
                                "fingerprint_id": 0,
                                "confidence": 0
                            }
                    else:
                        logger.error("Failed to convert image to template")
                        return False
                elif i == adafruit_fingerprint.NOFINGER:
                    # No finger detected, this is normal
                    return False
                else:
                    logger.error(f"Error getting fingerprint image: {i}")
                    return False
            
            # Send result OUTSIDE lock to prevent blocking other sensor operations
            # Network operations (MQTT publish) should not hold sensor lock
            if 'scan_result' in locals():
                self.send_scan_result(
                    scan_result["status"],
                    scan_result["fingerprint_id"],
                    scan_result.get("confidence")
                )
                self.last_scan_time = current_time
                return True
                
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
        
        # Release port lock
        self.release_port_lock()
        
        # Release GPIO lock
        if self.gpio_lock_file and os.path.exists(self.gpio_lock_file):
            try:
                os.remove(self.gpio_lock_file)
                logger.debug(f"✓ GPIO lock released: {self.gpio_lock_file}")
            except Exception as e:
                logger.warning(f"Failed to remove GPIO lock: {e}")
        
        # Remove PID file
        if self.pid_file and os.path.exists(self.pid_file):
            try:
                os.remove(self.pid_file)
                logger.debug(f"✓ PID file removed: {self.pid_file}")
            except Exception as e:
                logger.warning(f"Failed to remove PID file: {e}")
        
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
        
        # Wait for sensor to fully stabilize before starting scanning
        logger.info("⏳ Waiting for sensor to fully stabilize...")
        time.sleep(5.0)
        logger.info("🚀 Starting fingerprint scanning...")
        
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
