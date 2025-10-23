#!/usr/bin/env python3
"""
Simple sensor test without complex imports
"""

import os
import sys
import time
import logging
import glob

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Simple sensor test"""
    logger.info("SIMPLE SENSOR TEST")
    logger.info("=" * 50)
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check available ports
    logger.info("Checking available serial ports...")
    
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
    
    if not all_ports:
        logger.error("No serial ports found!")
        logger.info("Make sure your AS608 sensors are connected")
        return 1
    
    # Test each port
    logger.info("\nTesting port accessibility...")
    accessible_ports = []
    
    for port in all_ports:
        try:
            logger.info(f"Testing {port}...")
            
            # Try to import serial
            import serial
            
            # Try to open port
            uart = serial.Serial(port, baudrate=57600, timeout=1)
            time.sleep(0.5)
            uart.close()
            
            logger.info(f"✅ {port} - Accessible")
            accessible_ports.append(port)
            
        except ImportError:
            logger.error("❌ pyserial module not found")
            logger.info("Install with: pip3 install pyserial")
            return 1
        except Exception as e:
            logger.error(f"❌ {port} - Error: {e}")
    
    logger.info(f"\nAccessible ports: {accessible_ports}")
    
    if len(accessible_ports) >= 2:
        logger.info("✅ Found enough ports for dual sensor setup!")
        logger.info(f"Configure sensor_1: {accessible_ports[0]}")
        logger.info(f"Configure sensor_2: {accessible_ports[1]}")
        
        # Update config file
        try:
            logger.info("Updating dual_sensor_config.py...")
            
            with open('dual_sensor_config.py', 'r') as f:
                content = f.read()
            
            # Replace ports
            content = content.replace('/dev/ttyUSB0', accessible_ports[0])
            if len(accessible_ports) > 1:
                content = content.replace('/dev/ttyUSB1', accessible_ports[1])
            
            with open('dual_sensor_config.py', 'w') as f:
                f.write(content)
            
            logger.info("✅ Configuration updated!")
            
        except Exception as e:
            logger.error(f"❌ Error updating config: {e}")
    
    elif len(accessible_ports) == 1:
        logger.warning("⚠️  Only 1 accessible port found")
        logger.info("Connect second AS608 sensor")
    else:
        logger.error("❌ No accessible ports found")
        logger.info("Check permissions: sudo chmod 666 /dev/ttyUSB* /dev/ttyACM* /dev/serial*")
        return 1
    
    # Test for AS608 sensors
    if accessible_ports:
        logger.info(f"\nTesting {len(accessible_ports)} ports for AS608 sensors...")
        
        try:
            import adafruit_fingerprint
            
            as608_ports = []
            for port in accessible_ports:
                try:
                    logger.info(f"Testing {port} for AS608...")
                    
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
            
            logger.info(f"\nAS608 sensors found: {len(as608_ports)}")
            
            if len(as608_ports) >= 2:
                logger.info("✅ Found enough AS608 sensors for dual setup!")
                logger.info("You can now run: python3 dual_fingerprint_simple_client.py")
            elif len(as608_ports) == 1:
                logger.warning("⚠️  Only 1 AS608 sensor found")
                logger.info("Connect second AS608 sensor")
            else:
                logger.error("❌ No AS608 sensors found")
                logger.info("Check sensor connections and power")
        
        except ImportError:
            logger.error("❌ adafruit-circuitpython-fingerprint module not found")
            logger.info("Install with: pip3 install adafruit-circuitpython-fingerprint")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
