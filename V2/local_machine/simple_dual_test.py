#!/usr/bin/env python3
"""
Simple test script for Dual AS608 Fingerprint Sensors (3.3V)
Simplified version to avoid import conflicts
"""

import time
import logging
import sys
import os
import glob

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_available_ports():
    """Check what serial ports are available"""
    logger.info("=" * 60)
    logger.info("CHECKING AVAILABLE SERIAL PORTS")
    logger.info("=" * 60)
    
    all_ports = []
    
    # Check USB serial ports
    usb_patterns = ['/dev/ttyUSB*', '/dev/ttyACM*']
    for pattern in usb_patterns:
        found_ports = glob.glob(pattern)
        all_ports.extend(found_ports)
        if found_ports:
            logger.info(f"Found USB ports: {found_ports}")
    
    # Check built-in serial ports
    builtin_patterns = ['/dev/ttyS*', '/dev/serial*']
    for pattern in builtin_patterns:
        if pattern.startswith('/dev/serial'):
            # Check specific serial ports
            for i in range(5):
                port = f"/dev/serial{i}"
                if os.path.exists(port):
                    all_ports.append(port)
                    logger.info(f"Found serial port: {port}")
        else:
            found_ports = glob.glob(pattern)
            all_ports.extend(found_ports)
            if found_ports:
                logger.info(f"Found built-in ports: {found_ports}")
    
    # Remove duplicates and sort
    possible_ports = sorted(list(set(all_ports)))
    logger.info(f"Total available ports: {possible_ports}")
    
    return possible_ports

def test_port_connection(port):
    """Test connection to a specific port"""
    try:
        import serial
        import adafruit_fingerprint
        
        logger.info(f"Testing port: {port}")
        
        # Try to connect to the port
        uart = serial.Serial(port, baudrate=57600, timeout=2)
        time.sleep(0.5)
        
        # Try to create fingerprint object
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        
        # Try to read templates (this will fail if not an AS608)
        result = finger.read_templates()
        
        if result == adafruit_fingerprint.OK:
            logger.info(f"✅ AS608 fingerprint sensor found on {port}!")
            logger.info(f"   📊 Templates: {finger.template_count}")
            uart.close()
            return True
        else:
            logger.info(f"❌ Not an AS608 sensor on {port} (result: {result})")
            uart.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing {port}: {e}")
        return False

def main():
    """Main test function"""
    logger.info("SIMPLE DUAL AS608 SENSOR TEST (3.3V)")
    logger.info("=" * 60)
    
    try:
        # Check available ports
        available_ports = check_available_ports()
        
        if not available_ports:
            logger.warning("⚠️  No serial ports found!")
            logger.info("💡 Make sure your AS608 sensors are connected")
            logger.info("💡 Check USB-to-Serial adapters are working")
            return 1
        
        # Test each port
        logger.info("\n" + "=" * 60)
        logger.info("TESTING PORTS FOR AS608 SENSORS")
        logger.info("=" * 60)
        
        found_sensors = 0
        for port in available_ports:
            if test_port_connection(port):
                found_sensors += 1
        
        logger.info(f"\n✓ Found {found_sensors} AS608 sensor(s)")
        
        if found_sensors == 0:
            logger.warning("⚠️  No AS608 sensors found!")
            logger.info("💡 Check sensor connections")
            logger.info("💡 Make sure sensors are powered on")
            logger.info("💡 Verify USB-to-Serial adapters")
            return 1
        elif found_sensors == 1:
            logger.warning("⚠️  Only 1 sensor found, need 2 for dual setup")
            logger.info("💡 Connect second AS608 sensor")
        else:
            logger.info("✅ Multiple sensors found - dual setup possible!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"\nTest failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())


