#!/usr/bin/env python3
"""
Simple port test for dual sensors
"""

import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_port_simple(port):
    """Test port with simple connection"""
    try:
        import serial
        logger.info(f"Testing {port}...")
        
        # Try to open port
        uart = serial.Serial(port, baudrate=57600, timeout=2)
        time.sleep(0.5)
        
        # Try to close
        uart.close()
        
        logger.info(f"✅ {port} - Accessible")
        return True
        
    except Exception as e:
        logger.error(f"❌ {port} - Error: {e}")
        return False

def test_as608_sensor(port):
    """Test AS608 sensor on port"""
    try:
        import serial
        import adafruit_fingerprint
        
        logger.info(f"Testing AS608 sensor on {port}...")
        
        uart = serial.Serial(port, baudrate=57600, timeout=2)
        time.sleep(0.5)
        
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        result = finger.read_templates()
        
        if result == adafruit_fingerprint.OK:
            logger.info(f"✅ AS608 sensor found on {port}")
            logger.info(f"   Templates: {finger.template_count}")
            uart.close()
            return True
        else:
            logger.info(f"❌ Not an AS608 sensor on {port}")
            uart.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing {port}: {e}")
        return False

def main():
    """Main function"""
    logger.info("SIMPLE PORT TEST FOR DUAL SENSORS")
    logger.info("=" * 50)
    
    ports = ['/dev/serial0', '/dev/ttyS0']
    
    # Test port accessibility
    logger.info("Testing port accessibility...")
    accessible_ports = []
    
    for port in ports:
        if test_port_simple(port):
            accessible_ports.append(port)
    
    if not accessible_ports:
        logger.error("❌ No accessible ports found!")
        logger.info("Check permissions: sudo chmod 666 /dev/serial* /dev/ttyS*")
        return 1
    
    # Test AS608 sensors
    logger.info(f"\nTesting AS608 sensors on {len(accessible_ports)} ports...")
    as608_ports = []
    
    for port in accessible_ports:
        if test_as608_sensor(port):
            as608_ports.append(port)
    
    # Results
    logger.info(f"\nResults:")
    logger.info(f"Accessible ports: {len(accessible_ports)}")
    logger.info(f"AS608 sensors found: {len(as608_ports)}")
    
    if len(as608_ports) >= 2:
        logger.info("✅ Dual sensor setup ready!")
        logger.info(f"Sensor 1: {as608_ports[0]}")
        logger.info(f"Sensor 2: {as608_ports[1]}")
        return 0
    elif len(as608_ports) == 1:
        logger.warning("⚠️  Only 1 AS608 sensor found")
        logger.info("Connect second AS608 sensor")
        return 1
    else:
        logger.error("❌ No AS608 sensors found")
        logger.info("Check sensor connections and power")
        return 1

if __name__ == "__main__":
    exit(main())
