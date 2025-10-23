#!/usr/bin/env python3
"""
Diagnose dual sensor issues
"""

import time
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_individual_sensors():
    """Test each sensor individually"""
    logger.info("TESTING INDIVIDUAL SENSORS")
    logger.info("=" * 50)
    
    try:
        from dual_sensor_manager import DualSensorManager
        from dual_sensor_config import SENSORS, CONFIDENCE_THRESHOLD
        
        # Initialize sensor manager
        sensor_manager = DualSensorManager(SENSORS)
        
        # Connect to sensors
        if not sensor_manager.connect_all_sensors():
            logger.error("❌ Failed to connect to sensors")
            return False
        
        # Test sensor 1
        logger.info("Testing sensor_1 (/dev/serial0)...")
        result1 = sensor_manager.scan_sensor('sensor_1', CONFIDENCE_THRESHOLD)
        if result1:
            logger.info(f"✅ sensor_1: {result1['status']}")
            logger.info(f"  Device ID: {result1['device_id']}")
            logger.info(f"  Voltage: {result1['voltage']}")
            logger.info(f"  Timestamp: {result1['timestamp']}")
        else:
            logger.info("❌ sensor_1: No response")
        
        # Test sensor 2
        logger.info("Testing sensor_2 (/dev/ttyS0)...")
        result2 = sensor_manager.scan_sensor('sensor_2', CONFIDENCE_THRESHOLD)
        if result2:
            logger.info(f"✅ sensor_2: {result2['status']}")
            logger.info(f"  Device ID: {result2['device_id']}")
            logger.info(f"  Voltage: {result2['voltage']}")
            logger.info(f"  Timestamp: {result2['timestamp']}")
        else:
            logger.info("❌ sensor_2: No response")
        
        # Test concurrent scanning
        logger.info("Testing concurrent scanning...")
        results = sensor_manager.scan_all_sensors(CONFIDENCE_THRESHOLD)
        logger.info(f"Concurrent scan results: {len(results)} sensors responded")
        
        for result in results:
            logger.info(f"  {result['sensor_id']}: {result['status']}")
            logger.info(f"    Device ID: {result['device_id']}")
            logger.info(f"    Voltage: {result['voltage']}")
        
        # Cleanup
        sensor_manager.disconnect_all_sensors()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during sensor test: {e}")
        return False

def test_sensor_connections():
    """Test sensor connections individually"""
    logger.info("TESTING SENSOR CONNECTIONS")
    logger.info("=" * 50)
    
    ports = ['/dev/serial0', '/dev/ttyS0']
    sensor_names = ['sensor_1', 'sensor_2']
    
    for i, port in enumerate(ports):
        sensor_name = sensor_names[i]
        logger.info(f"Testing {sensor_name} on {port}...")
        
        try:
            import serial
            import adafruit_fingerprint
            
            # Connect to port
            uart = serial.Serial(port, baudrate=57600, timeout=2)
            time.sleep(0.5)
            
            # Create fingerprint object
            finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
            
            # Test connection
            result = finger.read_templates()
            
            if result == adafruit_fingerprint.OK:
                logger.info(f"✅ {sensor_name} connected successfully")
                logger.info(f"  Port: {port}")
                logger.info(f"  Templates: {finger.template_count}")
                
                # Test scanning
                logger.info(f"  Testing scan on {sensor_name}...")
                scan_result = finger.get_image()
                if scan_result == adafruit_fingerprint.OK:
                    logger.info(f"  ✅ {sensor_name} can capture images")
                elif scan_result == adafruit_fingerprint.NOFINGER:
                    logger.info(f"  ✅ {sensor_name} ready for scanning (no finger detected)")
                else:
                    logger.warning(f"  ⚠️  {sensor_name} scan error: {scan_result}")
            else:
                logger.error(f"❌ {sensor_name} connection failed: {result}")
            
            uart.close()
            
        except Exception as e:
            logger.error(f"❌ Error testing {sensor_name}: {e}")

def test_sensor_status():
    """Test sensor status monitoring"""
    logger.info("TESTING SENSOR STATUS")
    logger.info("=" * 50)
    
    try:
        from dual_sensor_manager import DualSensorManager
        from dual_sensor_config import SENSORS
        
        sensor_manager = DualSensorManager(SENSORS)
        
        if not sensor_manager.connect_all_sensors():
            logger.error("❌ Failed to connect to sensors")
            return False
        
        # Get sensor status
        status = sensor_manager.get_sensor_status()
        
        for sensor_id, sensor_status in status.items():
            logger.info(f"{sensor_id}:")
            logger.info(f"  Device ID: {sensor_status['device_id']}")
            logger.info(f"  Description: {sensor_status['description']}")
            logger.info(f"  Port: {sensor_status['port']}")
            logger.info(f"  Voltage: {sensor_status['voltage']}")
            logger.info(f"  Connected: {sensor_status['connected']}")
            logger.info(f"  Enabled: {sensor_status['enabled']}")
            logger.info(f"  Last Scan: {sensor_status['last_scan']}")
        
        # Get template counts
        template_counts = sensor_manager.get_template_count()
        logger.info(f"Template counts: {template_counts}")
        
        # Get ready sensors
        ready_sensors = sensor_manager.get_ready_sensors()
        logger.info(f"Ready sensors: {ready_sensors}")
        
        # Cleanup
        sensor_manager.disconnect_all_sensors()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during status test: {e}")
        return False

def main():
    """Main function"""
    logger.info("DUAL SENSOR DIAGNOSIS")
    logger.info("=" * 50)
    
    try:
        # Test sensor connections
        test_sensor_connections()
        
        # Test sensor status
        test_sensor_status()
        
        # Test individual sensors
        test_individual_sensors()
        
        logger.info("✅ Diagnosis completed!")
        
    except KeyboardInterrupt:
        logger.info("\nDiagnosis interrupted by user")
    except Exception as e:
        logger.error(f"Diagnosis failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
