#!/usr/bin/env python3
"""
System check for dual sensor setup
"""

import os
import sys
import logging
import glob

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python():
    """Check Python version"""
    logger.info(f"Python version: {sys.version}")
    return True

def check_imports():
    """Check required imports"""
    logger.info("Checking required modules...")
    
    modules = [
        ('serial', 'pyserial'),
        ('paho.mqtt.client', 'paho-mqtt'),
        ('adafruit_fingerprint', 'adafruit-circuitpython-fingerprint'),
        ('RPi.GPIO', 'RPi.GPIO')
    ]
    
    all_ok = True
    for module, package in modules:
        try:
            __import__(module)
            logger.info(f"✅ {package}")
        except ImportError:
            logger.error(f"❌ {package} not found")
            all_ok = False
    
    return all_ok

def check_ports():
    """Check available serial ports"""
    logger.info("Checking serial ports...")
    
    # USB ports
    usb_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    logger.info(f"USB ports: {usb_ports}")
    
    # Built-in serial ports
    serial_ports = []
    for i in range(5):
        port = f"/dev/serial{i}"
        if os.path.exists(port):
            serial_ports.append(port)
    logger.info(f"Built-in serial ports: {serial_ports}")
    
    # Other ports
    other_ports = glob.glob('/dev/ttyS*')
    logger.info(f"Other ports: {other_ports}")
    
    all_ports = usb_ports + serial_ports + other_ports
    logger.info(f"Total ports found: {len(all_ports)}")
    
    return all_ports

def check_permissions():
    """Check port permissions"""
    logger.info("Checking port permissions...")
    
    ports = check_ports()
    accessible_ports = []
    
    for port in ports:
        try:
            import serial
            uart = serial.Serial(port, baudrate=57600, timeout=1)
            uart.close()
            logger.info(f"✅ {port} - Accessible")
            accessible_ports.append(port)
        except Exception as e:
            logger.error(f"❌ {port} - Error: {e}")
    
    return accessible_ports

def check_sensors():
    """Check for AS608 sensors"""
    logger.info("Checking for AS608 sensors...")
    
    accessible_ports = check_permissions()
    as608_ports = []
    
    for port in accessible_ports:
        try:
            import serial
            import adafruit_fingerprint
            
            uart = serial.Serial(port, baudrate=57600, timeout=2)
            time.sleep(0.5)
            
            finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
            result = finger.read_templates()
            
            if result == adafruit_fingerprint.OK:
                logger.info(f"✅ AS608 sensor found on {port}!")
                logger.info(f"   Templates: {finger.template_count}")
                as608_ports.append(port)
            else:
                logger.info(f"❌ Not an AS608 sensor on {port}")
            
            uart.close()
            
        except Exception as e:
            logger.error(f"❌ Error testing {port}: {e}")
    
    return as608_ports

def main():
    """Main system check"""
    logger.info("DUAL SENSOR SYSTEM CHECK")
    logger.info("=" * 50)
    
    # Check Python
    check_python()
    
    # Check imports
    if not check_imports():
        logger.error("Missing required modules. Please install them first.")
        return 1
    
    # Check ports
    ports = check_ports()
    if not ports:
        logger.error("No serial ports found!")
        return 1
    
    # Check permissions
    accessible_ports = check_permissions()
    if not accessible_ports:
        logger.error("No accessible ports found!")
        logger.info("Run: sudo chmod 666 /dev/ttyUSB* /dev/ttyACM* /dev/serial*")
        return 1
    
    # Check sensors
    as608_ports = check_sensors()
    
    # Results
    logger.info(f"\nResults:")
    logger.info(f"Total ports found: {len(ports)}")
    logger.info(f"Accessible ports: {len(accessible_ports)}")
    logger.info(f"AS608 sensors found: {len(as608_ports)}")
    
    if len(as608_ports) >= 2:
        logger.info("✅ System ready for dual sensor setup!")
        logger.info(f"Configure sensor_1: {as608_ports[0]}")
        logger.info(f"Configure sensor_2: {as608_ports[1]}")
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


