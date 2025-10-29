#!/usr/bin/env python3
"""
Fix sensor issue - only one sensor working
"""

import time
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sensor_individually(port, sensor_name):
    """Test individual sensor"""
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
            
            uart.close()
            return True
        else:
            logger.error(f"❌ {sensor_name} connection failed: {result}")
            uart.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing {sensor_name}: {e}")
        return False

def test_sensor_with_delay(port, sensor_name, delay=2):
    """Test sensor with delay"""
    logger.info(f"Testing {sensor_name} on {port} with {delay}s delay...")
    
    try:
        import serial
        import adafruit_fingerprint
        
        # Connect to port
        uart = serial.Serial(port, baudrate=57600, timeout=2)
        time.sleep(delay)  # Wait longer for sensor to stabilize
        
        # Create fingerprint object
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        
        # Test connection
        result = finger.read_templates()
        
        if result == adafruit_fingerprint.OK:
            logger.info(f"✅ {sensor_name} connected successfully with delay")
            logger.info(f"  Port: {port}")
            logger.info(f"  Templates: {finger.template_count}")
            
            uart.close()
            return True
        else:
            logger.error(f"❌ {sensor_name} connection failed with delay: {result}")
            uart.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing {sensor_name} with delay: {e}")
        return False

def test_sensor_with_retry(port, sensor_name, retries=3):
    """Test sensor with retry"""
    logger.info(f"Testing {sensor_name} on {port} with {retries} retries...")
    
    for attempt in range(retries):
        logger.info(f"  Attempt {attempt + 1}/{retries}")
        
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
                logger.info(f"✅ {sensor_name} connected successfully on attempt {attempt + 1}")
                logger.info(f"  Port: {port}")
                logger.info(f"  Templates: {finger.template_count}")
                
                uart.close()
                return True
            else:
                logger.warning(f"  ⚠️  {sensor_name} attempt {attempt + 1} failed: {result}")
                uart.close()
                time.sleep(1)  # Wait before retry
                
        except Exception as e:
            logger.warning(f"  ⚠️  {sensor_name} attempt {attempt + 1} error: {e}")
            time.sleep(1)  # Wait before retry
    
    logger.error(f"❌ {sensor_name} failed after {retries} attempts")
    return False

def main():
    """Main function"""
    logger.info("FIXING SENSOR ISSUE")
    logger.info("=" * 50)
    
    # Test sensors individually
    logger.info("Testing sensors individually...")
    
    # Test sensor 1
    sensor1_ok = test_sensor_individually('/dev/serial0', 'sensor_1')
    
    # Test sensor 2
    sensor2_ok = test_sensor_individually('/dev/ttyS0', 'sensor_2')
    
    # If sensor 2 failed, try with delay
    if not sensor2_ok:
        logger.info("Sensor 2 failed, trying with delay...")
        sensor2_ok = test_sensor_with_delay('/dev/ttyS0', 'sensor_2', delay=3)
    
    # If sensor 2 still failed, try with retry
    if not sensor2_ok:
        logger.info("Sensor 2 still failed, trying with retry...")
        sensor2_ok = test_sensor_with_retry('/dev/ttyS0', 'sensor_2', retries=3)
    
    # Results
    logger.info(f"\nResults:")
    logger.info(f"Sensor 1 (/dev/serial0): {'✅ Working' if sensor1_ok else '❌ Failed'}")
    logger.info(f"Sensor 2 (/dev/ttyS0): {'✅ Working' if sensor2_ok else '❌ Failed'}")
    
    if sensor1_ok and sensor2_ok:
        logger.info("✅ Both sensors working!")
        logger.info("You can now run: python3 start_dual_sensors.py")
        return 0
    elif sensor1_ok and not sensor2_ok:
        logger.warning("⚠️  Only sensor 1 working")
        logger.info("Check sensor 2 connection and power")
        return 1
    elif not sensor1_ok and sensor2_ok:
        logger.warning("⚠️  Only sensor 2 working")
        logger.info("Check sensor 1 connection and power")
        return 1
    else:
        logger.error("❌ No sensors working")
        logger.info("Check both sensor connections and power")
        return 1

if __name__ == "__main__":
    exit(main())


