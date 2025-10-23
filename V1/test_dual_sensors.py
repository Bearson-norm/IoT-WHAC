#!/usr/bin/env python3
"""
Test script for Dual AS608 Fingerprint Sensors
Tests the dual sensor setup and functionality
"""

import time
import logging
import sys
from dual_sensor_manager import DualSensorManager
from dual_sensor_config import *

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_sensor_connection():
    """Test connection to all configured sensors"""
    logger.info("=" * 60)
    logger.info("TESTING DUAL AS608 SENSOR CONNECTION")
    logger.info("=" * 60)
    
    # Initialize sensor manager
    sensor_manager = DualSensorManager(SENSORS)
    
    # Test connection
    if sensor_manager.connect_all_sensors():
        logger.info("✓ Successfully connected to sensors")
        
        # Show sensor status
        status = sensor_manager.get_sensor_status()
        for sensor_id, sensor_status in status.items():
            logger.info(f"  {sensor_id}: {sensor_status['description']}")
            logger.info(f"    Port: {sensor_status['port']}")
            logger.info(f"    Device ID: {sensor_status['device_id']}")
            logger.info(f"    Connected: {sensor_status['connected']}")
            logger.info(f"    Enabled: {sensor_status['enabled']}")
        
        # Get template counts
        template_counts = sensor_manager.get_template_count()
        logger.info("\nTemplate counts:")
        for sensor_id, count in template_counts.items():
            logger.info(f"  {sensor_id}: {count} templates")
        
        return sensor_manager
    else:
        logger.error("✗ Failed to connect to any sensors")
        return None

def test_sensor_scanning(sensor_manager):
    """Test fingerprint scanning on all sensors"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING FINGERPRINT SCANNING")
    logger.info("=" * 60)
    
    if not sensor_manager:
        logger.error("No sensor manager available")
        return
    
    logger.info("Place a finger on any sensor...")
    logger.info("Scanning for 30 seconds...")
    
    start_time = time.time()
    scan_count = 0
    
    while time.time() - start_time < 30:
        # Get ready sensors
        ready_sensors = sensor_manager.get_ready_sensors()
        
        if ready_sensors:
            # Scan all ready sensors
            results = []
            for sensor_id in ready_sensors:
                result = sensor_manager.scan_sensor(sensor_id, CONFIDENCE_THRESHOLD)
                if result:
                    results.append(result)
            
            # Display results
            for result in results:
                scan_count += 1
                logger.info(f"Scan #{scan_count}: {result['sensor_id']} - {result['status']}")
                if result['status'] == 'Match':
                    logger.info(f"  Finger ID: {result['finger_id']}")
                    logger.info(f"  Confidence: {result['confidence']}")
                    logger.info(f"  Device ID: {result['device_id']}")
        
        time.sleep(0.5)
    
    logger.info(f"\n✓ Scanning test completed. Total scans: {scan_count}")

def test_concurrent_scanning(sensor_manager):
    """Test concurrent scanning on multiple sensors"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING CONCURRENT SCANNING")
    logger.info("=" * 60)
    
    if not sensor_manager:
        logger.error("No sensor manager available")
        return
    
    logger.info("Testing concurrent scanning on all sensors...")
    logger.info("Place fingers on multiple sensors simultaneously...")
    
    # Test concurrent scanning
    results = sensor_manager.scan_all_sensors(CONFIDENCE_THRESHOLD)
    
    logger.info(f"Concurrent scan results: {len(results)} sensors responded")
    for result in results:
        logger.info(f"  {result['sensor_id']}: {result['status']}")
        if result['status'] == 'Match':
            logger.info(f"    Finger ID: {result['finger_id']}, Confidence: {result['confidence']}")

def test_sensor_status(sensor_manager):
    """Test sensor status monitoring"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING SENSOR STATUS MONITORING")
    logger.info("=" * 60)
    
    if not sensor_manager:
        logger.error("No sensor manager available")
        return
    
    # Monitor sensor status for 10 seconds
    logger.info("Monitoring sensor status for 10 seconds...")
    
    start_time = time.time()
    while time.time() - start_time < 10:
        status = sensor_manager.get_sensor_status()
        ready_sensors = sensor_manager.get_ready_sensors()
        
        logger.info(f"Ready sensors: {len(ready_sensors)} - {ready_sensors}")
        
        for sensor_id, sensor_status in status.items():
            if sensor_status['connected']:
                logger.info(f"  {sensor_id}: Ready for scanning")
        
        time.sleep(2)

def test_configuration():
    """Test configuration loading"""
    logger.info("=" * 60)
    logger.info("TESTING CONFIGURATION")
    logger.info("=" * 60)
    
    logger.info(f"Store ID: {STORE_ID}")
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
    logger.info(f"Scan Interval: {SCAN_INTERVAL}")
    
    logger.info("\nSensor Configuration:")
    for sensor_id, config in SENSORS.items():
        logger.info(f"  {sensor_id}:")
        logger.info(f"    Port: {config['port']}")
        logger.info(f"    Baudrate: {config['baudrate']}")
        logger.info(f"    Device ID: {config['device_id']}")
        logger.info(f"    Description: {config['description']}")
        logger.info(f"    Enabled: {config.get('enabled', True)}")
    
    logger.info("\nMQTT Topics:")
    for topic_name, topic in MQTT_TOPICS.items():
        logger.info(f"  {topic_name}: {topic}")

def main():
    """Main test function"""
    logger.info("DUAL AS608 SENSOR TEST SUITE")
    logger.info("=" * 60)
    
    try:
        # Test configuration
        test_configuration()
        
        # Test sensor connection
        sensor_manager = test_sensor_connection()
        
        if sensor_manager:
            # Test sensor scanning
            test_sensor_scanning(sensor_manager)
            
            # Test concurrent scanning
            test_concurrent_scanning(sensor_manager)
            
            # Test sensor status monitoring
            test_sensor_status(sensor_manager)
            
            # Cleanup
            sensor_manager.disconnect_all_sensors()
            logger.info("\n✓ All tests completed successfully")
        else:
            logger.error("\n✗ Sensor connection test failed - skipping other tests")
            return 1
        
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"\nTest failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
