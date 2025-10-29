#!/usr/bin/env python3
"""
Simple sensor connection checker for Dual AS608
"""

import os
import glob
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_ports():
    """Check available serial ports"""
    logger.info("Checking available serial ports...")
    
    # Check USB ports
    usb_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    if usb_ports:
        logger.info(f"USB ports found: {usb_ports}")
    else:
        logger.warning("No USB serial ports found")
    
    # Check built-in serial ports
    serial_ports = []
    for i in range(5):
        port = f"/dev/serial{i}"
        if os.path.exists(port):
            serial_ports.append(port)
    
    if serial_ports:
        logger.info(f"Built-in serial ports: {serial_ports}")
    else:
        logger.warning("No built-in serial ports found")
    
    # Check other common ports
    other_ports = glob.glob('/dev/ttyS*')
    if other_ports:
        logger.info(f"Other serial ports: {other_ports}")
    
    all_ports = usb_ports + serial_ports + other_ports
    logger.info(f"Total ports found: {len(all_ports)}")
    
    return all_ports

def test_simple_connection(port):
    """Test simple connection to port"""
    try:
        import serial
        logger.info(f"Testing {port}...")
        
        # Try to open port
        uart = serial.Serial(port, baudrate=57600, timeout=1)
        time.sleep(0.5)
        uart.close()
        
        logger.info(f"✅ {port} - Port accessible")
        return True
        
    except Exception as e:
        logger.error(f"❌ {port} - Error: {e}")
        return False

def main():
    logger.info("SIMPLE SENSOR CONNECTION CHECKER")
    logger.info("=" * 50)
    
    # Check available ports
    ports = check_ports()
    
    if not ports:
        logger.error("No serial ports found!")
        logger.info("Make sure your AS608 sensors are connected via USB-to-Serial adapters")
        return 1
    
    # Test each port
    logger.info("\nTesting port connections...")
    working_ports = []
    
    for port in ports:
        if test_simple_connection(port):
            working_ports.append(port)
    
    logger.info(f"\nWorking ports: {working_ports}")
    
    if len(working_ports) >= 2:
        logger.info("✅ Found enough ports for dual sensor setup!")
        logger.info(f"Configure sensor_1: {working_ports[0]}")
        logger.info(f"Configure sensor_2: {working_ports[1]}")
    elif len(working_ports) == 1:
        logger.warning("⚠️  Only 1 working port found")
        logger.info("Connect second AS608 sensor")
    else:
        logger.error("❌ No working ports found")
        logger.info("Check sensor connections and permissions")
    
    return 0

if __name__ == "__main__":
    exit(main())


