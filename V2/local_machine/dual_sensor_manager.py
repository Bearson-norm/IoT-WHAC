#!/usr/bin/env python3
"""
Dual AS608 Fingerprint Sensor Manager
Based on existing system structure with 3.3V support
"""

import serial
import adafruit_fingerprint
import time
import logging
import threading
import glob
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DualSensorManager:
    """Manages multiple AS608 fingerprint sensors with 3.3V support"""
    
    def __init__(self, sensors_config):
        """
        Initialize dual sensor manager
        
        Args:
            sensors_config (dict): Configuration for each sensor
        """
        self.sensors_config = sensors_config
        self.sensors = {}
        self.sensor_locks = {}
        self.connected_sensors = {}
        self.last_scan_times = {}
        
        # Initialize each sensor
        for sensor_id, config in sensors_config.items():
            if config.get('enabled', True):
                self.initialize_sensor(sensor_id, config)
    
    def initialize_sensor(self, sensor_id, config):
        """Initialize a single sensor"""
        try:
            logger.info(f"Initializing {sensor_id}: {config['description']} ({config['voltage']})")
            
            # Create lock for thread safety
            self.sensor_locks[sensor_id] = threading.Lock()
            
            # Store sensor configuration
            self.sensors[sensor_id] = {
                'config': config,
                'uart': None,
                'finger': None,
                'connected': False,
                'last_scan': 0
            }
            
            logger.info(f"✓ {sensor_id} initialized on {config['port']} ({config['voltage']})")
            
        except Exception as e:
            logger.error(f"Failed to initialize {sensor_id}: {e}")
            self.sensors[sensor_id] = {
                'config': config,
                'uart': None,
                'finger': None,
                'connected': False,
                'last_scan': 0
            }
    
    def auto_detect_sensor_port(self, sensor_id, configured_port):
        """Auto-detect sensor port if configured port doesn't exist"""
        logger.info(f"🔍 Auto-detecting port for {sensor_id}...")
        
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
            return configured_port
        
        # Prioritize the configured port if it exists
        if configured_port in possible_ports:
            possible_ports.remove(configured_port)
            possible_ports.insert(0, configured_port)
            logger.info(f"🎯 Prioritizing configured port: {configured_port}")
        
        logger.info(f"🔍 Testing {len(possible_ports)} ports for AS608 sensor...")
        
        for port in possible_ports:
            if not os.path.exists(port):
                logger.debug(f"  Port {port} does not exist, skipping")
                continue
                
            try:
                logger.info(f"🔌 Testing port: {port}")
                
                # Try to connect to the port
                test_uart = serial.Serial(port, baudrate=57600, timeout=2)
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
        logger.warning(f"⚠️  Auto-detection failed, using configured port: {configured_port}")
        logger.warning("💡 Make sure your AS608 sensor is connected and powered on")
        logger.warning("💡 You can also manually set the port in dual_sensor_config.py")
        
        return configured_port
    
    def connect_all_sensors(self, retries=3):
        """Connect to all enabled sensors"""
        connected_count = 0
        
        for sensor_id, sensor_data in self.sensors.items():
            config = sensor_data['config']
            if not config.get('enabled', True):
                logger.info(f"Skipping disabled sensor: {sensor_id}")
                continue
            
            # Auto-detect port if configured port doesn't exist
            detected_port = config['port']
            if not os.path.exists(detected_port):
                logger.warning(f"⚠️  Configured port {detected_port} does not exist!")
                logger.info("🔍 Falling back to auto-detection...")
                detected_port = self.auto_detect_sensor_port(sensor_id, config['port'])
            
            for attempt in range(retries):
                try:
                    logger.info(f"Connecting to {sensor_id} on {detected_port} (attempt {attempt + 1})")
                    
                    # Check if port is already in use
                    try:
                        import subprocess
                        result = subprocess.run(['lsof', detected_port], capture_output=True, text=True)
                        if result.stdout:
                            logger.warning(f"⚠️  Port {detected_port} is already in use:")
                            logger.warning(f"   {result.stdout}")
                            logger.info("💡 Try: sudo pkill -f python3")
                    except:
                        pass  # lsof not available, continue anyway
                    
                    # Create UART connection
                    uart = serial.Serial(detected_port, baudrate=config['baudrate'], timeout=2)
                    time.sleep(0.5)  # Give sensor time to stabilize
                    
                    # Create fingerprint object
                    finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
                    
                    # Test connection by reading templates
                    if finger.read_templates() == adafruit_fingerprint.OK:
                        sensor_data['uart'] = uart
                        sensor_data['finger'] = finger
                        sensor_data['connected'] = True
                        self.connected_sensors[sensor_id] = sensor_data
                        connected_count += 1
                        
                        # Get template count
                        count = finger.template_count
                        logger.info(f"✓ {sensor_id} connected - Templates: {count} ({config['voltage']})")
                        break
                    else:
                        logger.warning(f"Connection test failed for {sensor_id}")
                        uart.close()
                        if attempt < retries - 1:
                            time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error connecting to {sensor_id}: {e}")
                    if sensor_data['uart']:
                        sensor_data['uart'].close()
                    if attempt < retries - 1:
                        time.sleep(1)
        
        logger.info(f"Connected to {connected_count}/{len(self.sensors)} sensors")
        return connected_count > 0
    
    def disconnect_all_sensors(self):
        """Disconnect from all sensors"""
        for sensor_id, sensor_data in self.sensors.items():
            if sensor_data['connected'] and sensor_data['uart']:
                try:
                    sensor_data['uart'].close()
                    sensor_data['connected'] = False
                    logger.info(f"Disconnected from {sensor_id}")
                except Exception as e:
                    logger.error(f"Error disconnecting from {sensor_id}: {e}")
        
        self.connected_sensors.clear()
    
    def get_sensor_status(self):
        """Get status of all sensors"""
        status = {}
        for sensor_id, sensor_data in self.sensors.items():
            config = sensor_data['config']
            status[sensor_id] = {
                'device_id': config['device_id'],
                'description': config['description'],
                'port': config['port'],
                'voltage': config['voltage'],
                'connected': sensor_data['connected'],
                'enabled': config.get('enabled', True),
                'last_scan': sensor_data['last_scan']
            }
        return status
    
    def scan_sensor(self, sensor_id, confidence_threshold=50):
        """
        Scan a specific sensor for fingerprint
        
        Args:
            sensor_id (str): ID of the sensor to scan
            confidence_threshold (int): Minimum confidence for match
            
        Returns:
            dict: Scan result with sensor info and fingerprint data
        """
        if sensor_id not in self.connected_sensors:
            logger.warning(f"Sensor {sensor_id} not connected")
            return None
        
        sensor_data = self.connected_sensors[sensor_id]
        config = sensor_data['config']
        finger = sensor_data['finger']
        
        # Use lock to prevent concurrent access
        with self.sensor_locks[sensor_id]:
            try:
                # Get fingerprint image
                i = finger.get_image()
                if i == adafruit_fingerprint.OK:
                    logger.debug(f"Fingerprint image captured on {sensor_id}")
                    
                    # Convert image to template
                    if finger.image_2_tz(1) == adafruit_fingerprint.OK:
                        logger.debug(f"Image converted to template on {sensor_id}")
                        
                        # Search for match
                        i = finger.finger_search()
                        
                        if i == adafruit_fingerprint.OK:
                            # Match found
                            finger_id = finger.finger_id
                            confidence = finger.confidence
                            
                            result = {
                                'sensor_id': sensor_id,
                                'device_id': config['device_id'],
                                'description': config['description'],
                                'voltage': config['voltage'],
                                'finger_id': finger_id,
                                'confidence': confidence,
                                'timestamp': datetime.now().isoformat(),
                                'status': 'Match'
                            }
                            
                            sensor_data['last_scan'] = time.time()
                            logger.info(f"✓ {sensor_id} match: ID={finger_id}, Confidence={confidence}")
                            return result
                        else:
                            # No match found
                            result = {
                                'sensor_id': sensor_id,
                                'device_id': config['device_id'],
                                'description': config['description'],
                                'voltage': config['voltage'],
                                'finger_id': 0,
                                'confidence': 0,
                                'timestamp': datetime.now().isoformat(),
                                'status': 'Not Match'
                            }
                            
                            sensor_data['last_scan'] = time.time()
                            logger.debug(f"{sensor_id}: No match found")
                            return result
                    else:
                        logger.error(f"Failed to convert image to template on {sensor_id}")
                        return None
                elif i == adafruit_fingerprint.NOFINGER:
                    # No finger detected, this is normal
                    return None
                else:
                    logger.error(f"Error getting fingerprint image on {sensor_id}: {i}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error scanning {sensor_id}: {e}")
                return None
    
    def scan_all_sensors(self, confidence_threshold=50):
        """
        Scan all connected sensors concurrently
        
        Args:
            confidence_threshold (int): Minimum confidence for match
            
        Returns:
            list: List of scan results from all sensors
        """
        results = []
        
        # Create threads for concurrent scanning
        threads = []
        
        for sensor_id in self.connected_sensors.keys():
            thread = threading.Thread(
                target=self._scan_sensor_thread,
                args=(sensor_id, confidence_threshold, results)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)  # 5 second timeout per sensor
        
        return results
    
    def _scan_sensor_thread(self, sensor_id, confidence_threshold, results):
        """Thread function for scanning a single sensor"""
        try:
            result = self.scan_sensor(sensor_id, confidence_threshold)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Thread error scanning {sensor_id}: {e}")
    
    def get_template_count(self, sensor_id=None):
        """
        Get template count for a specific sensor or all sensors
        
        Args:
            sensor_id (str, optional): Specific sensor ID. If None, returns all counts.
            
        Returns:
            dict or int: Template counts
        """
        if sensor_id:
            if sensor_id in self.connected_sensors:
                finger = self.connected_sensors[sensor_id]['finger']
                if finger.read_templates() == adafruit_fingerprint.OK:
                    return finger.template_count
                else:
                    return 0
            else:
                return 0
        else:
            counts = {}
            for sid, sensor_data in self.connected_sensors.items():
                finger = sensor_data['finger']
                if finger.read_templates() == adafruit_fingerprint.OK:
                    counts[sid] = finger.template_count
                else:
                    counts[sid] = 0
            return counts
    
    def enroll_fingerprint(self, sensor_id, location):
        """
        Enroll a new fingerprint on a specific sensor
        
        Args:
            sensor_id (str): ID of the sensor to use
            location (int): Template location to store fingerprint
            
        Returns:
            bool: True if enrollment successful
        """
        if sensor_id not in self.connected_sensors:
            logger.error(f"Sensor {sensor_id} not connected")
            return False
        
        sensor_data = self.connected_sensors[sensor_id]
        config = sensor_data['config']
        finger = sensor_data['finger']
        
        with self.sensor_locks[sensor_id]:
            try:
                logger.info(f"Starting enrollment on {sensor_id} at location {location}")
                
                # First scan
                logger.info("Place finger on sensor for first scan...")
                while True:
                    i = finger.get_image()
                    if i == adafruit_fingerprint.OK:
                        break
                    if i == adafruit_fingerprint.NOFINGER:
                        continue
                    else:
                        logger.error(f"Error getting first image: {i}")
                        logger.error("💡 Check sensor connection and try again")
                        return False
                
                logger.info("First image captured!")
                
                if finger.image_2_tz(1) != adafruit_fingerprint.OK:
                    logger.error("Error converting first image")
                    return False
                
                logger.info("Remove finger...")
                time.sleep(2)
                
                while finger.get_image() != adafruit_fingerprint.NOFINGER:
                    pass
                
                # Second scan
                logger.info("Place same finger again for second scan...")
                while True:
                    i = finger.get_image()
                    if i == adafruit_fingerprint.OK:
                        break
                    if i == adafruit_fingerprint.NOFINGER:
                        continue
                    else:
                        logger.error(f"Error getting second image: {i}")
                        return False
                
                logger.info("Second image captured!")
                
                if finger.image_2_tz(2) != adafruit_fingerprint.OK:
                    logger.error("Error converting second image")
                    return False
                
                # Create model
                logger.info("Creating fingerprint model...")
                if finger.create_model() != adafruit_fingerprint.OK:
                    logger.error("Error creating model - fingers didn't match?")
                    return False
                
                # Store model
                logger.info(f"Storing model at location {location}...")
                if finger.store_model(location) != adafruit_fingerprint.OK:
                    logger.error("Error storing model")
                    return False
                
                logger.info(f"✓ Fingerprint enrolled successfully on {sensor_id} at location {location}!")
                return True
                
            except Exception as e:
                logger.error(f"Error during enrollment on {sensor_id}: {e}")
                return False
    
    def is_sensor_ready(self, sensor_id):
        """Check if a sensor is ready for scanning"""
        if sensor_id not in self.connected_sensors:
            return False
        
        sensor_data = self.connected_sensors[sensor_id]
        current_time = time.time()
        
        # Check if enough time has passed since last scan
        return (current_time - sensor_data['last_scan']) >= 1.0  # 1 second minimum between scans
    
    def get_ready_sensors(self):
        """Get list of sensors that are ready for scanning"""
        ready_sensors = []
        for sensor_id in self.connected_sensors.keys():
            if self.is_sensor_ready(sensor_id):
                ready_sensors.append(sensor_id)
        return ready_sensors
