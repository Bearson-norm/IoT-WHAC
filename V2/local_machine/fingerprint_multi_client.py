#!/usr/bin/env python3
"""
Multi-Sensor Fingerprint MQTT Client for AS608 Sensors
- Supports multiple AS608 sensors simultaneously
- Standby fingerprint scanning from all sensors
- Simple JSON format (same protocol as single sensor)
- MQTT command handling for user management
- Each sensor has unique device_id
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
import errno
from datetime import datetime
from config import *

# Import audio controller
try:
    from audio_controller import get_audio_controller
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("⚠️  audio_controller not available, audio features disabled")

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


class SensorConnection:
    """Represents a single AS608 sensor connection"""
    def __init__(self, port, device_id, index, parent_client=None):
        self.port = port
        self.device_id = device_id
        self.index = index
        self.uart = None
        self.finger = None
        self.connected = False
        self.last_scan_time = 0
        self.lock = threading.Lock()  # Lock for thread-safe operations
        self.parent_client = parent_client  # Reference to parent client for port locking
        self.port_lock_file = None
        
    def acquire_port_lock(self):
        """Acquire exclusive lock on serial port"""
        if os.name != 'posix':
            return True
        
        lock_file_path = f"/tmp/serial_port_{os.path.basename(self.port)}.lock"
        
        if os.path.exists(lock_file_path):
            try:
                with open(lock_file_path, 'r') as f:
                    old_pid = int(f.read().strip())
                try:
                    os.kill(old_pid, 0)
                    logger.error(f"[{self.device_id}] ❌ Port {self.port} is locked by process {old_pid}")
                    return False
                except OSError:
                    os.remove(lock_file_path)
            except (ValueError, IOError):
                os.remove(lock_file_path)
        
        try:
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            self.port_lock_file = lock_file_path
            if self.parent_client:
                self.parent_client.port_lock_files[self.port] = lock_file_path
            logger.debug(f"[{self.device_id}] ✓ Port lock acquired: {lock_file_path}")
            return True
        except Exception as e:
            logger.error(f"[{self.device_id}] Failed to create port lock: {e}")
            return False
    
    def release_port_lock(self):
        """Release port lock"""
        if self.port_lock_file and os.path.exists(self.port_lock_file):
            try:
                os.remove(self.port_lock_file)
                logger.debug(f"[{self.device_id}] ✓ Port lock released")
            except Exception as e:
                logger.warning(f"[{self.device_id}] Failed to remove port lock: {e}")
        
    def connect(self, retries=3):
        """Connect to AS608 fingerprint sensor with port locking"""
        # Acquire port lock first
        if not self.acquire_port_lock():
            logger.error(f"[{self.device_id}] ❌ Cannot acquire lock on port {self.port}")
            return False
        
        for attempt in range(retries):
            try:
                logger.info(f"[{self.device_id}] Connecting to sensor on {self.port} (attempt {attempt + 1})")
                
                # Additional check if port is already in use
                try:
                    import subprocess
                    result = subprocess.run(['lsof', self.port], capture_output=True, text=True)
                    if result.stdout:
                        logger.warning(f"[{self.device_id}] ⚠️  Port {self.port} is already in use")
                except:
                    pass  # lsof not available, continue anyway
                
                self.uart = serial.Serial(self.port, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)  # Give sensor time to stabilize
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                
                # Test connection
                if self.finger.read_templates() == adafruit_fingerprint.OK:
                    logger.info(f"[{self.device_id}] ✓ Sensor connected! Templates: {self.finger.template_count}")
                    self.connected = True
                    return True
                else:
                    raise Exception("Failed to read templates from sensor")
                    
            except serial.SerialException as e:
                logger.error(f"[{self.device_id}] Connection attempt {attempt + 1} failed: {e}")
                if "Permission denied" in str(e) or "could not open port" in str(e).lower():
                    logger.error(f"[{self.device_id}] ❌ Port is already in use by another process")
                    self.release_port_lock()
                    return False
                if self.uart:
                    try:
                        self.uart.close()
                    except:
                        pass
                    self.uart = None
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    self.connected = False
                    self.release_port_lock()
                    raise
            except Exception as e:
                logger.error(f"[{self.device_id}] Connection attempt {attempt + 1} failed: {e}")
                if self.uart:
                    try:
                        self.uart.close()
                    except:
                        pass
                    self.uart = None
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    self.connected = False
                    self.release_port_lock()
                    raise
        return False
    
    def disconnect(self):
        """Disconnect from sensor"""
        self.connected = False
        self.release_port_lock()  # Release port lock
        if self.uart:
            try:
                self.uart.close()
                logger.info(f"[{self.device_id}] Serial connection closed")
            except:
                pass
            self.uart = None
        self.finger = None
    
    def get_template_count(self):
        """Get number of stored fingerprints"""
        try:
            if not self.connected or not self.finger:
                return 0
            if self.finger.read_templates() == adafruit_fingerprint.OK:
                return self.finger.template_count
            return 0
        except Exception as e:
            logger.error(f"[{self.device_id}] Error getting template count: {e}")
            return 0


class MultiSensorFingerprintClient:
    """Multi-sensor fingerprint client supporting multiple AS608 sensors"""
    def __init__(self):
        self.sensors = []  # List of SensorConnection objects
        self.mqtt_client = None
        self.connected = False
        self.running = True
        self.enrolling = False  # Flag to pause scanning during enrollment
        self.command_lock = threading.Lock()
        self.db_file = "fingerprints_multi.db"  # Separate DB file to avoid conflicts
        self.scan_threads = []  # Threads for each sensor scanning
        self.port_lock_files = {}  # Track port locks
        self.gpio_lock_file = None  # File lock for GPIO
        self.pid_file = None  # PID file to prevent multiple instances
        
        # Check for existing instances
        self.check_existing_instance()
        
        self.init_database()
        
        # Relay control
        # DISABLED: Relay control di-nonaktifkan karena menggunakan relay_controller_advanced.py
        # Jika ingin menggunakan relay built-in, uncomment baris di bawah dan comment relay_controller_advanced.py
        # self.relay_pin = 18  # GPIO pin for relay
        # self.setup_gpio()
        self.relay_pin = None  # Disabled - using relay_controller_advanced.py instead
        
        # Initialize sensors from config
        self.init_sensors()
        
        # MQTT Topics
        self.SCAN_TOPIC = MQTT_TOPIC  # "WHAC/Store001/in" - for scan results
        self.ADD_USER_TOPIC = "WHAC/Store001/add_user"  # for adding users
        self.IMPORT_TOPIC = "WHAC/Store001/import"  # for importing users
        self.EXPORT_TOPIC = "WHAC/Store001/export"  # for exporting users
        self.ACTION_TOPIC = "WHAC/Store001/action"  # for relay control commands
        self.AUDIO_TOPIC = "WHAC/Store001/audio"  # for audio commands (self-inspection)
        self.STATUS_TOPIC = "WHAC/Store001/relay_status"  # for status updates
        
        # Initialize audio controller
        self.audio_controller = None
        if AUDIO_AVAILABLE:
            try:
                audio_dir = os.path.join(os.path.dirname(__file__), "audio")
                os.makedirs(audio_dir, exist_ok=True)
                self.audio_controller = get_audio_controller(audio_dir=audio_dir, use_tts=True)
                logger.info("✅ Audio controller initialized")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize audio controller: {e}")
                self.audio_controller = None
    
    def init_sensors(self):
        """Initialize sensor connections from config"""
        # Check if multiple ports are configured
        if FINGERPRINT_PORTS and len(FINGERPRINT_PORTS) > 0:
            ports = FINGERPRINT_PORTS
            logger.info(f"🔧 Configuring {len(ports)} sensors from FINGERPRINT_PORTS")
        else:
            # Fallback to single port
            ports = [FINGERPRINT_PORT]
            logger.info(f"🔧 Using single sensor from FINGERPRINT_PORT")
        
        # Create sensor connections
        for idx, port in enumerate(ports):
            # Generate device_id: AS608_001, AS608_002, etc.
            device_id = f"AS608_{idx + 1:03d}"
            sensor = SensorConnection(port.strip(), device_id, idx, parent_client=self)
            
            # Verify port exists
            if not os.path.exists(sensor.port):
                logger.warning(f"⚠️  Port {sensor.port} does not exist for {sensor.device_id}")
                # Try auto-detection for this sensor
                detected = self.auto_detect_fingerprint_port(sensor.device_id)
                if detected:
                    sensor.port = detected
                    logger.info(f"✅ Auto-detected port {detected} for {sensor.device_id}")
            
            self.sensors.append(sensor)
            logger.info(f"📌 Sensor {idx + 1}: {sensor.device_id} -> {sensor.port}")
        
        if len(self.sensors) == 0:
            logger.error("❌ No sensors configured!")
            raise ValueError("No sensors configured")
    
    def auto_detect_fingerprint_port(self, device_id):
        """Auto-detect AS608 fingerprint sensor port for a specific device"""
        logger.info(f"[{device_id}] 🔍 Auto-detecting fingerprint sensor port...")
        
        if os.name == 'posix':  # Linux/Unix (Raspberry Pi)
            all_ports = []
            
            # Check common USB serial patterns
            usb_patterns = ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/tty.usbserial*', '/dev/tty.usbmodem*']
            for pattern in usb_patterns:
                found_ports = glob.glob(pattern)
                all_ports.extend(found_ports)
            
            # Check built-in serial ports
            builtin_patterns = ['/dev/ttyS*', '/dev/ttyAMA*', '/dev/serial0', '/dev/serial1']
            for pattern in builtin_patterns:
                if pattern.startswith('/dev/serial'):
                    if os.path.exists(pattern):
                        all_ports.append(pattern)
                else:
                    found_ports = glob.glob(pattern)
                    all_ports.extend(found_ports)
            
            possible_ports = sorted(list(set(all_ports)))
            
            # Filter out ports already used by other sensors
            used_ports = [s.port for s in self.sensors if s.port]
            possible_ports = [p for p in possible_ports if p not in used_ports]
            
        elif os.name == 'nt':  # Windows
            try:
                import serial.tools.list_ports
                available_ports = [port.device for port in serial.tools.list_ports.comports()]
                possible_ports = available_ports
            except ImportError:
                possible_ports = []
        else:
            possible_ports = []
        
        logger.info(f"[{device_id}] Testing {len(possible_ports)} available ports...")
        
        for port in possible_ports:
            if not os.path.exists(port):
                continue
                
            try:
                test_uart = serial.Serial(port, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)
                test_finger = adafruit_fingerprint.Adafruit_Fingerprint(test_uart)
                result = test_finger.read_templates()
                
                if result == adafruit_fingerprint.OK:
                    logger.info(f"[{device_id}] ✅ AS608 found on {port}!")
                    test_uart.close()
                    return port
                else:
                    test_uart.close()
            except:
                continue
        
        logger.warning(f"[{device_id}] ⚠️  Auto-detection failed")
        return None
    
    def check_existing_instance(self):
        """Check if another instance of this program is already running"""
        try:
            pid_file_path = "/tmp/fingerprint_multi_client.pid"
            if os.path.exists(pid_file_path):
                try:
                    with open(pid_file_path, 'r') as f:
                        old_pid = int(f.read().strip())
                    if os.name == 'posix':
                        try:
                            os.kill(old_pid, 0)
                            logger.error(f"❌ Another instance is already running (PID: {old_pid})")
                            logger.error("💡 Stop the existing instance first or remove /tmp/fingerprint_multi_client.pid")
                            raise SystemExit(1)
                        except OSError:
                            os.remove(pid_file_path)
                except (ValueError, IOError):
                    os.remove(pid_file_path)
            
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
            
            # Check if GPIO is already in use
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
                            os.remove(gpio_lock_path)
                except (ValueError, IOError):
                    os.remove(gpio_lock_path)
            
            # Create GPIO lock file
            with open(gpio_lock_path, 'w') as f:
                f.write(str(os.getpid()))
            self.gpio_lock_file = gpio_lock_path
            
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.relay_pin, GPIO.OUT)
            GPIO.output(self.relay_pin, GPIO.LOW)
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
        
        NOTE: Relay control is disabled when using relay_controller_advanced.py
        """
        if not self.relay_pin:
            # Relay control disabled - using relay_controller_advanced.py instead
            logger.debug("Relay control disabled - using relay_controller_advanced.py")
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
    
    def init_database(self):
        """Initialize SQLite database for fingerprint management with timeout"""
        try:
            # Use timeout to handle database locking better
            conn = sqlite3.connect(self.db_file, timeout=10.0)
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    fingerprint_id INTEGER NOT NULL,
                    device_id TEXT DEFAULT 'AS608_001',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✓ Database initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def connect_all_sensors(self):
        """Connect to all configured sensors"""
        connected_count = 0
        for sensor in self.sensors:
            try:
                if sensor.connect():
                    connected_count += 1
                else:
                    logger.error(f"[{sensor.device_id}] Failed to connect")
            except Exception as e:
                logger.error(f"[{sensor.device_id}] Connection error: {e}")
        
        if connected_count == 0:
            logger.error("❌ No sensors connected!")
            return False
        
        logger.info(f"✅ {connected_count}/{len(self.sensors)} sensors connected successfully")
        return True
    
    def connect_mqtt(self):
        """Connect to MQTT broker with unique client ID"""
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            # Create unique client ID to prevent conflicts
            unique_id = f"whac_multi_fingerprint_client_{os.getpid()}_{int(time.time())}"
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
                self.mqtt_client.subscribe(self.AUDIO_TOPIC, qos=MQTT_QOS)
                logger.info(f"✓ Subscribed to command topics (including audio)")
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
            
            # Handle commands in separate thread to avoid blocking
            threading.Thread(target=self.handle_command, args=(topic, payload), daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def handle_command(self, topic, payload):
        """Handle MQTT command in separate thread"""
        with self.command_lock:
            try:
                if topic == self.ADD_USER_TOPIC:
                    self.handle_add_user(payload)
                elif topic == self.IMPORT_TOPIC:
                    self.handle_import(payload)
                elif topic == self.EXPORT_TOPIC:
                    self.handle_export(payload)
                elif topic == self.ACTION_TOPIC:
                    self.handle_relay_action(payload)
                elif topic == self.AUDIO_TOPIC:
                    self.handle_audio_command(payload)
            except Exception as e:
                logger.error(f"Error handling command: {e}")
    
    def handle_add_user(self, payload):
        """Handle add user command - smart enrollment to sensors
        
        Supports:
        1. Target sensor selection (if 'target_sensor' specified)
        2. Smart enrollment (enroll to sensor that doesn't have this fingerprint ID yet)
        3. Re-enrollment (allow updating existing fingerprint)
        """
        try:
            # Extract command data - using 'user_name' to match Web UI
            fingerprint_id = payload.get('fingerprint_id')
            user_name = payload.get('user_name')
            target_sensor = payload.get('target_sensor')  # Optional: specific sensor to enroll
            
            if not fingerprint_id or not user_name:
                logger.error(f"Missing required fields: fingerprint_id={fingerprint_id}, user_name={user_name}")
                self.send_command_response("add_user", "error", {
                    "message": "Missing fingerprint_id or user_name in add user command"
                })
                return
            
            # Check which sensors already have this fingerprint ID
            enrolled_sensors = self.check_fingerprint_enrollment(fingerprint_id)
            
            if enrolled_sensors:
                logger.info(f"ℹ️  Fingerprint ID {fingerprint_id} already enrolled on: {', '.join(enrolled_sensors)}")
            
            logger.info(f"📝 Adding user '{user_name}' (ID: {fingerprint_id}) to sensors...")
            if target_sensor:
                logger.info(f"🎯 Target sensor: {target_sensor}")
            
            # Set enrolling flag to pause scanning
            self.enrolling = True
            logger.info("⏸️  Pausing fingerprint scanning during enrollment...")
            
            # Wait for scanning loops to stop
            time.sleep(0.5)
            
            enrollment_success = False
            enrolled_sensor = None
            
            try:
                # Select sensors to try enrollment
                sensors_to_try = []
                
                if target_sensor:
                    # Try specific sensor if specified
                    for sensor in self.sensors:
                        if sensor.device_id == target_sensor and sensor.connected:
                            sensors_to_try = [sensor]
                            break
                    if not sensors_to_try:
                        logger.error(f"Target sensor {target_sensor} not found or not connected")
                        raise Exception(f"Target sensor {target_sensor} not available")
                else:
                    # Smart selection: prioritize sensors that don't have this fingerprint yet
                    for sensor in self.sensors:
                        if not sensor.connected:
                            continue
                        # Enroll to first available sensor (user can enroll again for other sensor)
                        if sensor.device_id not in enrolled_sensors:
                            sensors_to_try = [sensor]
                            break
                    
                    # If all sensors already have it, use first available (re-enrollment)
                    if not sensors_to_try:
                        for sensor in self.sensors:
                            if sensor.connected:
                                sensors_to_try = [sensor]
                                logger.info(f"ℹ️  Re-enrolling on {sensor.device_id} (fingerprint will be updated)")
                                break
                
                # Try enrollment on selected sensor
                for sensor in sensors_to_try:
                    try:
                        with sensor.lock:
                            logger.info(f"[{sensor.device_id}] Starting enrollment for {user_name}...")
                            
                            # Enroll fingerprint
                            if self.enroll_fingerprint_on_sensor(sensor, fingerprint_id):
                                # Save to database
                                conn = sqlite3.connect(self.db_file, timeout=10.0)
                                cursor = conn.cursor()
                                cursor.execute('''
                                    INSERT OR REPLACE INTO users (fingerprint_id, user_name, device_id)
                                    VALUES (?, ?, ?)
                                ''', (fingerprint_id, user_name, sensor.device_id))
                                conn.commit()
                                conn.close()
                                
                                logger.info(f"[{sensor.device_id}] ✓ User enrolled successfully: {user_name} (ID: {fingerprint_id})")
                                enrollment_success = True
                                enrolled_sensor = sensor.device_id
                                break
                            else:
                                logger.error(f"[{sensor.device_id}] ✗ Failed to enroll fingerprint")
                                
                    except Exception as e:
                        logger.error(f"[{sensor.device_id}] Enrollment error: {e}")
                        continue
                
                # Send response to Web UI
                if enrollment_success:
                    # Check updated enrollment status
                    updated_enrolled = self.check_fingerprint_enrollment(fingerprint_id)
                    remaining_sensors = [s.device_id for s in self.sensors if s.connected and s.device_id not in updated_enrolled]
                    
                    response_message = f"User enrolled successfully on {enrolled_sensor}"
                    if remaining_sensors:
                        response_message += f". You can enroll the same user on remaining sensors: {', '.join(remaining_sensors)}"
                    
                    self.send_command_response("add_user", "success", {
                        "fingerprint_id": fingerprint_id,
                        "user_name": user_name,
                        "device_id": enrolled_sensor,
                        "enrolled_sensors": updated_enrolled,
                        "remaining_sensors": remaining_sensors,
                        "message": response_message
                    })
                    logger.info(f"✅ Enrollment completed successfully on {enrolled_sensor}")
                    if remaining_sensors:
                        logger.info(f"ℹ️  Remaining sensors for enrollment: {', '.join(remaining_sensors)}")
                else:
                    self.send_command_response("add_user", "error", {
                        "message": "Failed to enroll fingerprint on any sensor"
                    })
                    logger.error(f"❌ Enrollment failed on all sensors")
                    
            finally:
                # Always resume scanning after enrollment
                self.enrolling = False
                logger.info("▶️  Resuming fingerprint scanning...")
                    
        except Exception as e:
            logger.error(f"Error in handle_add_user: {e}")
            self.enrolling = False  # Ensure flag is reset on error
            self.send_command_response("add_user", "error", {
                "message": f"Error: {str(e)}"
            })
    
    def check_fingerprint_enrollment(self, fingerprint_id):
        """Check which sensors have this fingerprint ID enrolled
        
        Returns:
            list: Device IDs that have this fingerprint enrolled
        """
        try:
            enrolled_sensors = []
            
            for sensor in self.sensors:
                if not sensor.connected:
                    continue
                
                try:
                    with sensor.lock:
                        # Check if fingerprint exists on sensor
                        result = sensor.finger.load_model(fingerprint_id)
                        if result == adafruit_fingerprint.OK:
                            enrolled_sensors.append(sensor.device_id)
                            logger.debug(f"[{sensor.device_id}] Fingerprint {fingerprint_id} exists")
                        else:
                            logger.debug(f"[{sensor.device_id}] Fingerprint {fingerprint_id} not found")
                except Exception as e:
                    logger.debug(f"[{sensor.device_id}] Error checking fingerprint: {e}")
                    continue
            
            return enrolled_sensors
            
        except Exception as e:
            logger.error(f"Error checking fingerprint enrollment: {e}")
            return []
    
    def handle_import(self, payload):
        """Handle import command"""
        logger.info("Import command received (not fully implemented)")
    
    def handle_export(self, payload):
        """Handle export command"""
        logger.info("Export command received (not fully implemented)")
    
    def handle_relay_action(self, payload):
        """Handle relay control command"""
        try:
            action = payload.get('action', 'deny')
            duration = payload.get('duration', 10)
            user_id = payload.get('user_id', 'unknown')
            command = payload.get('command', 'relay_control')
            
            self.control_relay(action, duration)
            self.send_relay_status(command, user_id, action, "MQTT")
        except Exception as e:
            logger.error(f"Error handling relay command: {e}")
    
    def handle_audio_command(self, payload):
        """Handle audio command (self-inspection) - NON-BLOCKING"""
        try:
            command_type = payload.get('command', 'self_inspection')
            source = payload.get('source', 'web_ui')
            requested_by = payload.get('requested_by', 'unknown')
            
            logger.info(f"🔊 Audio command received: {command_type} from {source} (requested by: {requested_by})")
            
            if not self.audio_controller:
                logger.warning("⚠️  Audio controller not available")
                self.send_audio_response(command_type, 'error', {'message': 'Audio controller not available'})
                return
            
            # Check if audio is already playing
            if self.audio_controller.is_busy():
                logger.warning("⚠️  Audio is already playing, queuing request")
                # Still queue it, but send warning response
                self.send_audio_response(command_type, 'queued', {'message': 'Audio queued (already playing)'})
            
            # Handle different audio commands
            if command_type == 'self_inspection':
                success = self.audio_controller.play_self_inspection(
                    callback=lambda result: self._on_audio_complete(command_type, result)
                )
                if success:
                    logger.info("✅ Self-inspection audio queued successfully")
                    self.send_audio_response(command_type, 'queued', {'message': 'Self-inspection audio started'})
                else:
                    logger.error("❌ Failed to queue self-inspection audio")
                    self.send_audio_response(command_type, 'error', {'message': 'Failed to queue audio'})
            elif command_type == 'play_file':
                filename = payload.get('filename', '')
                if filename:
                    success = self.audio_controller.play_file(
                        filename,
                        callback=lambda result: self._on_audio_complete(command_type, result)
                    )
                    if success:
                        self.send_audio_response(command_type, 'queued', {'message': f'Audio file {filename} queued'})
                    else:
                        self.send_audio_response(command_type, 'error', {'message': 'Failed to queue audio file'})
                else:
                    self.send_audio_response(command_type, 'error', {'message': 'Filename not provided'})
            elif command_type == 'play_tts':
                text = payload.get('text', '')
                if text:
                    success = self.audio_controller.play_tts(
                        text,
                        callback=lambda result: self._on_audio_complete(command_type, result)
                    )
                    if success:
                        self.send_audio_response(command_type, 'queued', {'message': 'TTS queued'})
                    else:
                        self.send_audio_response(command_type, 'error', {'message': 'Failed to queue TTS'})
                else:
                    self.send_audio_response(command_type, 'error', {'message': 'Text not provided'})
            elif command_type == 'stop':
                self.audio_controller.stop()
                self.send_audio_response(command_type, 'success', {'message': 'Audio stopped'})
            else:
                logger.warning(f"⚠️  Unknown audio command: {command_type}")
                self.send_audio_response(command_type, 'error', {'message': f'Unknown command: {command_type}'})
                
        except Exception as e:
            logger.error(f"❌ Error handling audio command: {e}")
            self.send_audio_response(payload.get('command', 'unknown'), 'error', {'message': str(e)})
    
    def _on_audio_complete(self, command_type, success):
        """Callback when audio playback completes"""
        try:
            if success:
                logger.info(f"✅ Audio playback completed: {command_type}")
                self.send_audio_response(command_type, 'completed', {'message': 'Audio playback completed'})
            else:
                logger.warning(f"⚠️  Audio playback failed: {command_type}")
                self.send_audio_response(command_type, 'error', {'message': 'Audio playback failed'})
        except Exception as e:
            logger.error(f"Error in audio completion callback: {e}")
    
    def send_audio_response(self, command_type, status, data):
        """Send audio command response back to MQTT"""
        try:
            if not self.connected:
                return False
            
            response = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "command": command_type,
                "status": status,
                "data": data,
                "device_id": "MULTI_SENSOR"
            }
            
            response_topic = f"WHAC/Store001/audio_response"
            payload = json.dumps(response)
            result = self.mqtt_client.publish(response_topic, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Audio response sent: {command_type} - {status}")
                return True
            else:
                logger.error(f"✗ Failed to send audio response (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending audio response: {e}")
            return False
    
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
                'device_id': 'MULTI_SENSOR',
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
        """Send command response back to MQTT"""
        try:
            response = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "command": command_type,
                "status": status,
                "data": data,
                "device_id": "MULTI_SENSOR"
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
    
    def enroll_fingerprint_on_sensor(self, sensor, location):
        """Enroll a new fingerprint on specified sensor at the specified location"""
        ENROLLMENT_TIMEOUT = 30  # seconds timeout for each step
        PROGRESS_INTERVAL = 5    # seconds between progress logs
        
        try:
            logger.info(f"[{sensor.device_id}] Starting fingerprint enrollment at location {location}")
            
            # Check if sensor is connected
            if not sensor.connected or not sensor.finger:
                logger.error(f"[{sensor.device_id}] ❌ Fingerprint sensor not connected!")
                return False
            
            # First scan with timeout
            logger.info(f"[{sensor.device_id}] Place finger on sensor for first scan...")
            start_time = time.time()
            last_progress_time = start_time
            
            while True:
                # Check timeout
                if time.time() - start_time > ENROLLMENT_TIMEOUT:
                    logger.error(f"[{sensor.device_id}] ❌ Enrollment timeout: No finger detected within {ENROLLMENT_TIMEOUT} seconds")
                    return False
                
                # Progress feedback every PROGRESS_INTERVAL seconds
                current_time = time.time()
                if current_time - last_progress_time >= PROGRESS_INTERVAL:
                    elapsed = int(current_time - start_time)
                    logger.info(f"[{sensor.device_id}] ⏳ Waiting for finger... ({elapsed}/{ENROLLMENT_TIMEOUT}s)")
                    last_progress_time = current_time
                
                i = sensor.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                elif i == adafruit_fingerprint.NOFINGER:
                    time.sleep(0.1)
                    continue
                else:
                    logger.error(f"[{sensor.device_id}] Error getting first image: {i}")
                    return False
            
            logger.info(f"[{sensor.device_id}] ✓ First image captured!")
            
            if sensor.finger.image_2_tz(1) != adafruit_fingerprint.OK:
                logger.error(f"[{sensor.device_id}] Error converting first image to template")
                return False
            
            logger.info(f"[{sensor.device_id}] ✓ First image converted to template")
            logger.info(f"[{sensor.device_id}] Remove finger...")
            time.sleep(2)
            
            # Wait for finger removal with timeout
            logger.info(f"[{sensor.device_id}] Waiting for finger removal...")
            start_time = time.time()
            while sensor.finger.get_image() != adafruit_fingerprint.NOFINGER:
                if time.time() - start_time > 10:
                    logger.warning(f"[{sensor.device_id}] ⚠️ Finger still detected after 10 seconds, continuing anyway...")
                    break
                time.sleep(0.1)
            
            logger.info(f"[{sensor.device_id}] ✓ Finger removed")
            
            # Second scan with timeout
            logger.info(f"[{sensor.device_id}] Place same finger again for second scan...")
            start_time = time.time()
            last_progress_time = start_time
            
            while True:
                # Check timeout
                if time.time() - start_time > ENROLLMENT_TIMEOUT:
                    logger.error(f"[{sensor.device_id}] ❌ Enrollment timeout: No finger detected for second scan within {ENROLLMENT_TIMEOUT} seconds")
                    return False
                
                # Progress feedback
                current_time = time.time()
                if current_time - last_progress_time >= PROGRESS_INTERVAL:
                    elapsed = int(current_time - start_time)
                    logger.info(f"[{sensor.device_id}] ⏳ Waiting for second scan... ({elapsed}/{ENROLLMENT_TIMEOUT}s)")
                    last_progress_time = current_time
                
                i = sensor.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                elif i == adafruit_fingerprint.NOFINGER:
                    time.sleep(0.1)
                    continue
                else:
                    logger.error(f"[{sensor.device_id}] Error getting second image: {i}")
                    return False
            
            logger.info(f"[{sensor.device_id}] ✓ Second image captured!")
            
            if sensor.finger.image_2_tz(2) != adafruit_fingerprint.OK:
                logger.error(f"[{sensor.device_id}] Error converting second image to template")
                return False
            
            logger.info(f"[{sensor.device_id}] ✓ Second image converted to template")
            
            # Create model
            logger.info(f"[{sensor.device_id}] Creating fingerprint model...")
            if sensor.finger.create_model() != adafruit_fingerprint.OK:
                logger.error(f"[{sensor.device_id}] Error creating model - fingers may not match")
                return False
            
            logger.info(f"[{sensor.device_id}] ✓ Fingerprint model created successfully")
            
            # Store model
            logger.info(f"[{sensor.device_id}] Storing model at location {location}...")
            if sensor.finger.store_model(location) != adafruit_fingerprint.OK:
                logger.error(f"[{sensor.device_id}] Error storing model")
                return False
            
            logger.info(f"[{sensor.device_id}] ✅ Fingerprint enrolled successfully at location {location}!")
            return True
            
        except Exception as e:
            logger.error(f"[{sensor.device_id}] Error during enrollment: {e}")
            return False
    
    def send_scan_result(self, sensor, status, fingerprint_id, confidence=None):
        """Send scan result in simple format (same protocol as single sensor)"""
        if not self.connected:
            logger.error("MQTT not connected, cannot send data")
            return False
        
        try:
            # Get user info from local database
            user_info = self.get_user_info(fingerprint_id)
            username = user_info.get('username') if user_info else None
            
            # Simple JSON format - SAME PROTOCOL as single sensor
            # Only difference: device_id identifies which sensor detected the fingerprint
            data = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "status": status,  # "Match" or "Not Match"
                "fingerprint_id": fingerprint_id,
                "device_id": sensor.device_id  # This identifies which sensor (e.g., "AS608_001" or "AS608_002")
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
                logger.info(f"[{sensor.device_id}] ✓ Scan result sent: {status} - ID: {fingerprint_id} ({username})")
                return True
            else:
                logger.error(f"[{sensor.device_id}] ✗ Failed to publish scan result (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"[{sensor.device_id}] Error sending scan result: {e}")
            return False
    
    def get_user_info(self, fingerprint_id):
        """Get user information from local database"""
        try:
            conn = sqlite3.connect(self.db_file, timeout=10.0)
            cursor = conn.cursor()
            cursor.execute("SELECT user_name, device_id FROM users WHERE fingerprint_id = ?", (fingerprint_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "username": result[0],  # Keep as 'username' for MQTT compatibility
                    "device_id": result[1] if len(result) > 1 else None
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def scan_fingerprint_standby(self, sensor):
        """Standby fingerprint scanning for a specific sensor"""
        try:
            # Skip scanning if enrollment is in progress
            if self.enrolling:
                return False
            
            # Check if sensor is connected
            if not sensor.connected or not sensor.finger:
                return False
            
            # Check if enough time has passed since last scan
            current_time = time.time()
            if current_time - sensor.last_scan_time < SCAN_INTERVAL:
                return False
            
            # Thread-safe scan operation
            with sensor.lock:
                # Get fingerprint image
                i = sensor.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    logger.debug(f"[{sensor.device_id}] Fingerprint image captured")
                    
                    # Convert image to template
                    if sensor.finger.image_2_tz(1) == adafruit_fingerprint.OK:
                        logger.debug(f"[{sensor.device_id}] Image converted to template")
                        
                        # Search for match
                        i = sensor.finger.finger_search()
                        
                        if i == adafruit_fingerprint.OK:
                            # Match found
                            finger_id = sensor.finger.finger_id
                            confidence = sensor.finger.confidence
                            
                            logger.info(f"[{sensor.device_id}] ✓ Match found! ID: {finger_id}, Confidence: {confidence}")
                            
                            # Send scan result with device_id identifying the sensor
                            self.send_scan_result(sensor, "Match", finger_id, confidence)
                            
                            sensor.last_scan_time = current_time
                            return True
                        else:
                            # No match found
                            logger.debug(f"[{sensor.device_id}] No match found")
                            # Only send "Not Match" occasionally to avoid spam
                            if current_time - sensor.last_scan_time > SCAN_INTERVAL * 2:
                                self.send_scan_result(sensor, "Not Match", 0, 0)
                                sensor.last_scan_time = current_time
                            return False
                    else:
                        logger.error(f"[{sensor.device_id}] Failed to convert image to template")
                        return False
                elif i == adafruit_fingerprint.NOFINGER:
                    # No finger detected, this is normal
                    return False
                else:
                    logger.error(f"[{sensor.device_id}] Error getting fingerprint image: {i}")
                    return False
                    
        except Exception as e:
            logger.error(f"[{sensor.device_id}] Error during fingerprint scan: {e}")
            return False
    
    def sensor_scan_loop(self, sensor):
        """Scanning loop for a specific sensor (runs in separate thread)"""
        logger.info(f"[{sensor.device_id}] Starting standby scanning on {sensor.port}...")
        logger.info(f"[{sensor.device_id}] Scan interval: {SCAN_INTERVAL} seconds")
        
        try:
            while self.running and sensor.connected:
                # Perform fingerprint scan
                self.scan_fingerprint_standby(sensor)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"[{sensor.device_id}] Error in scan loop: {e}")
        finally:
            logger.info(f"[{sensor.device_id}] Scan loop stopped")
    
    def run_standby_scanning(self):
        """Run standby fingerprint scanning from all sensors in parallel"""
        logger.info("Starting multi-sensor standby fingerprint scanning...")
        logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
        logger.info(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
        logger.info(f"Total sensors: {len(self.sensors)}")
        logger.info("✓ Listening for MQTT commands while scanning...")
        
        # Start scanning thread for each sensor
        self.scan_threads = []
        for sensor in self.sensors:
            if sensor.connected:
                thread = threading.Thread(target=self.sensor_scan_loop, args=(sensor,), daemon=True)
                thread.start()
                self.scan_threads.append(thread)
                logger.info(f"✓ Started scan thread for {sensor.device_id}")
        
        if len(self.scan_threads) == 0:
            logger.error("❌ No scan threads started!")
            return
        
        try:
            # Keep main thread alive
            while self.running:
                # Check if any scan thread is still alive
                alive_count = sum(1 for t in self.scan_threads if t.is_alive())
                if alive_count == 0:
                    logger.warning("All scan threads stopped!")
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Scanning stopped by user")
        except Exception as e:
            logger.error(f"Error in standby scanning: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        self.running = False
        
        # Wait for scan threads to finish
        for thread in self.scan_threads:
            thread.join(timeout=2)
        
        # Release all port locks
        for port, lock_file in self.port_lock_files.items():
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                    logger.debug(f"✓ Port lock released: {lock_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove port lock {lock_file}: {e}")
        
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
        
        # Disconnect all sensors
        for sensor in self.sensors:
            sensor.disconnect()
        
        # Cleanup GPIO
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            logger.info("GPIO cleaned up")
        except:
            pass


def main():
    """Main function"""
    client = MultiSensorFingerprintClient()
    
    try:
        # Connect to all fingerprint sensors
        if not client.connect_all_sensors():
            logger.error("Failed to connect to sensors")
            return 1
        
        # Connect to MQTT broker
        if not client.connect_mqtt():
            logger.error("Failed to connect to MQTT broker")
            return 1
        
        # Show initial status
        logger.info("=" * 70)
        logger.info("MULTI-SENSOR FINGERPRINT MQTT CLIENT - Ready!")
        logger.info("=" * 70)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Scan Topic: {client.SCAN_TOPIC}")
        logger.info(f"Total Sensors: {len(client.sensors)}")
        
        for sensor in client.sensors:
            if sensor.connected:
                template_count = sensor.get_template_count()
                logger.info(f"  - {sensor.device_id}: {sensor.port} ({template_count} templates)")
            else:
                logger.info(f"  - {sensor.device_id}: {sensor.port} (DISCONNECTED)")
        
        logger.info(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
        logger.info("=" * 70)
        logger.info("✓ Standby scanning active on all sensors")
        logger.info("✓ MQTT commands can interrupt scanning")
        logger.info("✓ Each sensor sends data with unique device_id")
        logger.info("=" * 70)
        
        # Wait for sensors to fully stabilize
        logger.info("⏳ Waiting for sensors to fully stabilize...")
        time.sleep(5.0)
        logger.info("🚀 Starting multi-sensor fingerprint scanning...")
        
        # Start standby scanning (this will block)
        client.run_standby_scanning()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        client.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


