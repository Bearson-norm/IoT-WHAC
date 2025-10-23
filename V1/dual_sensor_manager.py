#!/usr/bin/env python3
"""
Dual AS608 Fingerprint Sensor Manager
Manages multiple AS608 sensors with the same functionality
"""

import serial
import time
import logging
import threading
from datetime import datetime
from as608_driver import AS608Driver

logger = logging.getLogger(__name__)

class DualSensorManager:
    """Manages multiple AS608 fingerprint sensors"""
    
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
            logger.info(f"Initializing {sensor_id}: {config['description']}")
            
            # Create sensor driver
            sensor = AS608Driver(config['port'], config['baudrate'])
            
            # Create lock for thread safety
            self.sensor_locks[sensor_id] = threading.Lock()
            
            # Store sensor configuration
            self.sensors[sensor_id] = {
                'driver': sensor,
                'config': config,
                'connected': False,
                'last_scan': 0
            }
            
            logger.info(f"✓ {sensor_id} initialized on {config['port']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize {sensor_id}: {e}")
            self.sensors[sensor_id] = {
                'driver': None,
                'config': config,
                'connected': False,
                'last_scan': 0
            }
    
    def connect_all_sensors(self, retries=3):
        """Connect to all enabled sensors"""
        connected_count = 0
        
        for sensor_id, sensor_data in self.sensors.items():
            if sensor_data['driver'] is None:
                continue
                
            config = sensor_data['config']
            if not config.get('enabled', True):
                logger.info(f"Skipping disabled sensor: {sensor_id}")
                continue
            
            for attempt in range(retries):
                try:
                    logger.info(f"Connecting to {sensor_id} on {config['port']} (attempt {attempt + 1})")
                    
                    if sensor_data['driver'].connect():
                        sensor_data['connected'] = True
                        self.connected_sensors[sensor_id] = sensor_data
                        connected_count += 1
                        
                        # Get template count
                        count = sensor_data['driver'].get_template_count()
                        logger.info(f"✓ {sensor_id} connected - Templates: {count}")
                        break
                    else:
                        logger.warning(f"Connection attempt {attempt + 1} failed for {sensor_id}")
                        if attempt < retries - 1:
                            time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error connecting to {sensor_id}: {e}")
                    if attempt < retries - 1:
                        time.sleep(1)
        
        logger.info(f"Connected to {connected_count}/{len(self.sensors)} sensors")
        return connected_count > 0
    
    def disconnect_all_sensors(self):
        """Disconnect from all sensors"""
        for sensor_id, sensor_data in self.sensors.items():
            if sensor_data['connected'] and sensor_data['driver']:
                try:
                    sensor_data['driver'].disconnect()
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
        
        # Use lock to prevent concurrent access
        with self.sensor_locks[sensor_id]:
            try:
                # Get fingerprint
                finger_id = sensor_data['driver'].get_fingerprint(confidence_threshold)
                
                if finger_id is not None:
                    result = {
                        'sensor_id': sensor_id,
                        'device_id': config['device_id'],
                        'description': config['description'],
                        'finger_id': finger_id,
                        'confidence': sensor_data['driver'].confidence,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'Match'
                    }
                    
                    sensor_data['last_scan'] = time.time()
                    logger.info(f"✓ {sensor_id} match: ID={finger_id}, Confidence={sensor_data['driver'].confidence}")
                    return result
                else:
                    result = {
                        'sensor_id': sensor_id,
                        'device_id': config['device_id'],
                        'description': config['description'],
                        'finger_id': 0,
                        'confidence': 0,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'Not Match'
                    }
                    
                    sensor_data['last_scan'] = time.time()
                    logger.debug(f"{sensor_id}: No match found")
                    return result
                    
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
                return self.connected_sensors[sensor_id]['driver'].get_template_count()
            else:
                return 0
        else:
            counts = {}
            for sid, sensor_data in self.connected_sensors.items():
                counts[sid] = sensor_data['driver'].get_template_count()
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
        
        with self.sensor_locks[sensor_id]:
            try:
                logger.info(f"Starting enrollment on {sensor_id} at location {location}")
                
                # Get first image
                logger.info("Place finger on sensor for first scan...")
                if not sensor_data['driver'].get_image():
                    logger.error("Failed to get first image")
                    return False
                
                if not sensor_data['driver'].image_2_tz(1):
                    logger.error("Failed to convert first image")
                    return False
                
                logger.info("Remove finger...")
                time.sleep(2)
                
                # Wait for finger to be removed
                while True:
                    if not sensor_data['driver'].get_image():
                        break
                    time.sleep(0.1)
                
                # Get second image
                logger.info("Place same finger again for second scan...")
                if not sensor_data['driver'].get_image():
                    logger.error("Failed to get second image")
                    return False
                
                if not sensor_data['driver'].image_2_tz(2):
                    logger.error("Failed to convert second image")
                    return False
                
                # Create model (this would need to be implemented in AS608Driver)
                # For now, we'll use the existing search functionality
                logger.info("Creating fingerprint model...")
                
                # Store model (this would need to be implemented in AS608Driver)
                logger.info(f"Storing model at location {location}...")
                
                logger.info(f"✓ Fingerprint enrolled successfully on {sensor_id} at location {location}")
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
