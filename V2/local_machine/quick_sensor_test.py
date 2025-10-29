#!/usr/bin/env python3
"""
Quick sensor test - simplified version to avoid import conflicts
"""

import os
import sys
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_imports():
    """Check if required modules are available"""
    logger.info("Checking required modules...")
    
    try:
        import serial
        logger.info("✅ pyserial module available")
    except ImportError:
        logger.error("❌ pyserial module not found")
        logger.info("Install with: pip3 install pyserial")
        return False
    
    try:
        import adafruit_fingerprint
        logger.info("✅ adafruit-circuitpython-fingerprint module available")
    except ImportError:
        logger.error("❌ adafruit-circuitpython-fingerprint module not found")
        logger.info("Install with: pip3 install adafruit-circuitpython-fingerprint")
        return False
    
    return True

def find_serial_ports():
    """Find available serial ports"""
    logger.info("Finding serial ports...")
    
    import glob
    
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
        
        logger.info(f"✅ {port} - Port accessible")
        return True
        
    except Exception as e:
        logger.error(f"❌ {port} - Error: {e}")
        return False

def test_port_with_fingerprint(port):
    """Test port with fingerprint sensor"""
    try:
        import serial
        import adafruit_fingerprint
        
        logger.info(f"Testing {port} for AS608 sensor...")
        
        # Try to connect
        uart = serial.Serial(port, baudrate=57600, timeout=2)
        time.sleep(0.5)
        
        # Try to create fingerprint object
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        
        # Try to read templates
        result = finger.read_templates()
        
        if result == adafruit_fingerprint.OK:
            logger.info(f"✅ AS608 sensor found on {port}!")
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
    """Main test function"""
    logger.info("QUICK SENSOR TEST")
    logger.info("=" * 50)
    
    # Check imports
    if not check_imports():
        logger.error("Missing required modules. Please install them first.")
        return 1
    
    # Find ports
    ports = find_serial_ports()
    
    if not ports:
        logger.error("No serial ports found!")
        logger.info("Make sure your AS608 sensors are connected")
        return 1
    
    # Test each port
    logger.info("\nTesting port accessibility...")
    accessible_ports = []
    
    for port in ports:
        if test_port_simple(port):
            accessible_ports.append(port)
    
    if not accessible_ports:
        logger.error("No accessible ports found!")
        logger.info("Check permissions: sudo chmod 666 /dev/ttyUSB* /dev/ttyACM* /dev/serial*")
        return 1
    
    # Test for AS608 sensors
    logger.info(f"\nTesting {len(accessible_ports)} accessible ports for AS608 sensors...")
    as608_ports = []
    
    for port in accessible_ports:
        if test_port_with_fingerprint(port):
            as608_ports.append(port)
    
    # Results
    logger.info(f"\nResults:")
    logger.info(f"Total ports found: {len(ports)}")
    logger.info(f"Accessible ports: {len(accessible_ports)}")
    logger.info(f"AS608 sensors found: {len(as608_ports)}")
    
    if len(as608_ports) >= 2:
        logger.info("✅ Found enough AS608 sensors for dual setup!")
        logger.info(f"Configure sensor_1: {as608_ports[0]}")
        logger.info(f"Configure sensor_2: {as608_ports[1]}")
        
        # Update config
        logger.info("\nUpdating dual_sensor_config.py...")
        try:
            with open('dual_sensor_config.py', 'r') as f:
                content = f.read()
            
            # Replace ports
            content = content.replace('/dev/ttyUSB0', as608_ports[0])
            if len(as608_ports) > 1:
                content = content.replace('/dev/ttyUSB1', as608_ports[1])
            
            with open('dual_sensor_config.py', 'w') as f:
                f.write(content)
            
            logger.info("✅ Configuration updated!")
            
        except Exception as e:
            logger.error(f"❌ Error updating config: {e}")
        
    elif len(as608_ports) == 1:
        logger.warning("⚠️  Only 1 AS608 sensor found")
        logger.info("Connect second AS608 sensor")
    else:
        logger.error("❌ No AS608 sensors found")
        logger.info("Check sensor connections and power")
    
    return 0

if __name__ == "__main__":
    exit(main())


