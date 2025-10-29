#!/usr/bin/env python3
"""
Test dual sensor scanning functionality
"""

import time
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dual_sensor_scanning():
    """Test dual sensor scanning"""
    logger.info("DUAL SENSOR SCANNING TEST")
    logger.info("=" * 50)
    
    try:
        # Import dual sensor manager
        from dual_sensor_manager import DualSensorManager
        from dual_sensor_config import SENSORS, CONFIDENCE_THRESHOLD
        
        # Initialize sensor manager
        sensor_manager = DualSensorManager(SENSORS)
        
        # Connect to sensors
        if not sensor_manager.connect_all_sensors():
            logger.error("❌ Failed to connect to sensors")
            return False
        
        # Show sensor status
        status = sensor_manager.get_sensor_status()
        logger.info("Sensor status:")
        for sensor_id, sensor_status in status.items():
            logger.info(f"  {sensor_id}: {sensor_status['description']}")
            logger.info(f"    Port: {sensor_status['port']}")
            logger.info(f"    Connected: {sensor_status['connected']}")
            logger.info(f"    Voltage: {sensor_status['voltage']}")
        
        # Test scanning
        logger.info("\nTesting dual sensor scanning...")
        logger.info("Place fingers on both sensors...")
        logger.info("Scanning for 30 seconds...")
        
        start_time = time.time()
        scan_count = 0
        sensor_1_scans = 0
        sensor_2_scans = 0
        
        while time.time() - start_time < 30:
            # Get ready sensors
            ready_sensors = sensor_manager.get_ready_sensors()
            
            if ready_sensors:
                # Scan all ready sensors
                for sensor_id in ready_sensors:
                    result = sensor_manager.scan_sensor(sensor_id, CONFIDENCE_THRESHOLD)
                    if result:
                        scan_count += 1
                        if sensor_id == 'sensor_1':
                            sensor_1_scans += 1
                        elif sensor_id == 'sensor_2':
                            sensor_2_scans += 1
                        
                        logger.info(f"Scan #{scan_count}: {result['sensor_id']} - {result['status']}")
                        if result['status'] == 'Match':
                            logger.info(f"  Finger ID: {result['finger_id']}")
                            logger.info(f"  Confidence: {result['confidence']}")
                            logger.info(f"  Device ID: {result['device_id']}")
                            logger.info(f"  Voltage: {result['voltage']}")
            
            time.sleep(0.5)
        
        # Results
        logger.info(f"\nScanning test completed!")
        logger.info(f"Total scans: {scan_count}")
        logger.info(f"Sensor 1 scans: {sensor_1_scans}")
        logger.info(f"Sensor 2 scans: {sensor_2_scans}")
        
        # Test concurrent scanning
        logger.info("\nTesting concurrent scanning...")
        results = sensor_manager.scan_all_sensors(CONFIDENCE_THRESHOLD)
        logger.info(f"Concurrent scan results: {len(results)} sensors responded")
        
        for result in results:
            logger.info(f"  {result['sensor_id']}: {result['status']}")
            if result['status'] == 'Match':
                logger.info(f"    Finger ID: {result['finger_id']}, Confidence: {result['confidence']}")
        
        # Cleanup
        sensor_manager.disconnect_all_sensors()
        
        if scan_count > 0:
            logger.info("✅ Dual sensor scanning working!")
            return True
        else:
            logger.warning("⚠️  No scans detected")
            logger.info("Check sensor connections and finger placement")
            return False
            
    except Exception as e:
        logger.error(f"Error during dual sensor test: {e}")
        return False

def test_individual_sensors():
    """Test individual sensors"""
    logger.info("INDIVIDUAL SENSOR TEST")
    logger.info("=" * 50)
    
    try:
        from dual_sensor_manager import DualSensorManager
        from dual_sensor_config import SENSORS, CONFIDENCE_THRESHOLD
        
        sensor_manager = DualSensorManager(SENSORS)
        
        if not sensor_manager.connect_all_sensors():
            logger.error("❌ Failed to connect to sensors")
            return False
        
        # Test sensor 1
        logger.info("Testing sensor_1...")
        result1 = sensor_manager.scan_sensor('sensor_1', CONFIDENCE_THRESHOLD)
        if result1:
            logger.info(f"✅ sensor_1: {result1['status']}")
            if result1['status'] == 'Match':
                logger.info(f"  Finger ID: {result1['finger_id']}")
                logger.info(f"  Confidence: {result1['confidence']}")
        else:
            logger.info("❌ sensor_1: No response")
        
        # Test sensor 2
        logger.info("Testing sensor_2...")
        result2 = sensor_manager.scan_sensor('sensor_2', CONFIDENCE_THRESHOLD)
        if result2:
            logger.info(f"✅ sensor_2: {result2['status']}")
            if result2['status'] == 'Match':
                logger.info(f"  Finger ID: {result2['finger_id']}")
                logger.info(f"  Confidence: {result2['confidence']}")
        else:
            logger.info("❌ sensor_2: No response")
        
        # Cleanup
        sensor_manager.disconnect_all_sensors()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during individual sensor test: {e}")
        return False

def main():
    """Main function"""
    logger.info("DUAL SENSOR TESTING SUITE")
    logger.info("=" * 50)
    
    try:
        # Test individual sensors first
        if not test_individual_sensors():
            logger.error("❌ Individual sensor test failed")
            return 1
        
        # Test dual sensor scanning
        if not test_dual_sensor_scanning():
            logger.error("❌ Dual sensor scanning test failed")
            return 1
        
        logger.info("✅ All tests passed!")
        logger.info("Dual sensor system is ready!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())


