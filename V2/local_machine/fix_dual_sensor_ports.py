#!/usr/bin/env python3
"""
Fix dual sensor port configuration
"""

import os
import glob
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_available_ports():
    """Find available serial ports"""
    logger.info("Finding available serial ports...")
    
    # Check USB ports
    usb_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    logger.info(f"USB ports: {usb_ports}")
    
    # Check built-in serial ports
    serial_ports = []
    for i in range(5):
        port = f"/dev/serial{i}"
        if os.path.exists(port):
            serial_ports.append(port)
    logger.info(f"Built-in serial ports: {serial_ports}")
    
    # Check other ports
    other_ports = glob.glob('/dev/ttyS*')
    logger.info(f"Other ports: {other_ports}")
    
    all_ports = usb_ports + serial_ports + other_ports
    logger.info(f"Total ports found: {len(all_ports)}")
    
    return all_ports

def test_port_access(port):
    """Test if port is accessible"""
    try:
        import serial
        uart = serial.Serial(port, baudrate=57600, timeout=1)
        time.sleep(0.5)
        uart.close()
        return True
    except Exception as e:
        logger.error(f"Port {port} not accessible: {e}")
        return False

def test_as608_sensor(port):
    """Test if port has AS608 sensor"""
    try:
        import serial
        import adafruit_fingerprint
        
        uart = serial.Serial(port, baudrate=57600, timeout=2)
        time.sleep(0.5)
        
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        result = finger.read_templates()
        
        if result == adafruit_fingerprint.OK:
            logger.info(f"✅ AS608 sensor found on {port}")
            uart.close()
            return True
        else:
            logger.info(f"❌ Not an AS608 sensor on {port}")
            uart.close()
            return False
            
    except Exception as e:
        logger.error(f"Error testing {port}: {e}")
        return False

def update_config_file(sensor_1_port, sensor_2_port):
    """Update configuration file with correct ports"""
    logger.info("Updating dual_sensor_config.py...")
    
    try:
        with open('dual_sensor_config.py', 'r') as f:
            content = f.read()
        
        # Replace sensor 1 port
        content = content.replace('/dev/ttyUSB0', sensor_1_port)
        content = content.replace('"port": os.getenv("SENSOR_1_PORT", "/dev/ttyUSB0")', f'"port": os.getenv("SENSOR_1_PORT", "{sensor_1_port}")')
        
        # Replace sensor 2 port
        content = content.replace('/dev/ttyUSB1', sensor_2_port)
        content = content.replace('"port": os.getenv("SENSOR_2_PORT", "/dev/ttyUSB1")', f'"port": os.getenv("SENSOR_2_PORT", "{sensor_2_port}")')
        
        with open('dual_sensor_config.py', 'w') as f:
            f.write(content)
        
        logger.info(f"✅ Configuration updated!")
        logger.info(f"  Sensor 1: {sensor_1_port}")
        logger.info(f"  Sensor 2: {sensor_2_port}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return False

def main():
    """Main function"""
    logger.info("DUAL SENSOR PORT FIX")
    logger.info("=" * 50)
    
    # Find available ports
    ports = find_available_ports()
    
    if len(ports) < 2:
        logger.error("❌ Not enough serial ports found!")
        logger.info("You need at least 2 serial ports for dual sensor setup")
        logger.info("Connect second USB-to-Serial adapter")
        return 1
    
    # Test port access
    logger.info("\nTesting port accessibility...")
    accessible_ports = []
    for port in ports:
        if test_port_access(port):
            accessible_ports.append(port)
    
    if len(accessible_ports) < 2:
        logger.error("❌ Not enough accessible ports!")
        logger.info("Check permissions: sudo chmod 666 /dev/ttyUSB* /dev/ttyACM* /dev/serial*")
        return 1
    
    # Test for AS608 sensors
    logger.info(f"\nTesting {len(accessible_ports)} ports for AS608 sensors...")
    as608_ports = []
    
    for port in accessible_ports:
        if test_as608_sensor(port):
            as608_ports.append(port)
    
    if len(as608_ports) < 2:
        logger.warning("⚠️  Less than 2 AS608 sensors found!")
        logger.info("Make sure both AS608 sensors are:")
        logger.info("1. Connected via USB-to-Serial adapters")
        logger.info("2. Powered on (3.3V)")
        logger.info("3. Properly wired")
        
        if len(as608_ports) == 1:
            logger.info("Found 1 AS608 sensor, need 1 more")
            logger.info("Connect second AS608 sensor")
        else:
            logger.info("No AS608 sensors found")
            logger.info("Check sensor connections and power")
        
        return 1
    
    # Update configuration
    logger.info(f"\nFound {len(as608_ports)} AS608 sensors!")
    logger.info(f"Sensors found on: {as608_ports}")
    
    if update_config_file(as608_ports[0], as608_ports[1]):
        logger.info("✅ Configuration updated successfully!")
        logger.info("You can now run: python3 dual_fingerprint_simple_client.py")
        return 0
    else:
        logger.error("❌ Failed to update configuration")
        return 1

if __name__ == "__main__":
    exit(main())
