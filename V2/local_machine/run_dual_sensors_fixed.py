#!/usr/bin/env python3
"""
Run dual sensor system with fixed configuration
"""

import time
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_config():
    """Update configuration with correct ports"""
    logger.info("Updating dual sensor configuration...")
    
    try:
        with open('dual_sensor_config.py', 'r') as f:
            content = f.read()
        
        # Update sensor 1 port
        content = content.replace(
            '"port": os.getenv("SENSOR_1_PORT", "/dev/ttyUSB0")',
            '"port": os.getenv("SENSOR_1_PORT", "/dev/serial0")'
        )
        
        # Update sensor 2 port
        content = content.replace(
            '"port": os.getenv("SENSOR_2_PORT", "/dev/ttyUSB1")',
            '"port": os.getenv("SENSOR_2_PORT", "/dev/ttyS0")'
        )
        
        with open('dual_sensor_config.py', 'w') as f:
            f.write(content)
        
        logger.info("✅ Configuration updated!")
        logger.info("  Sensor 1: /dev/serial0")
        logger.info("  Sensor 2: /dev/ttyS0")
        return True
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return False

def test_ports():
    """Test port connections"""
    logger.info("Testing port connections...")
    
    ports = ['/dev/serial0', '/dev/ttyS0']
    results = {}
    
    for port in ports:
        try:
            import serial
            uart = serial.Serial(port, baudrate=57600, timeout=2)
            time.sleep(0.5)
            uart.close()
            results[port] = True
            logger.info(f"✅ {port} - Accessible")
        except Exception as e:
            results[port] = False
            logger.error(f"❌ {port} - Error: {e}")
    
    return results

def test_sensors():
    """Test AS608 sensors"""
    logger.info("Testing AS608 sensors...")
    
    ports = ['/dev/serial0', '/dev/ttyS0']
    sensor_results = {}
    
    for port in ports:
        try:
            import serial
            import adafruit_fingerprint
            
            uart = serial.Serial(port, baudrate=57600, timeout=2)
            time.sleep(0.5)
            
            finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
            result = finger.read_templates()
            
            if result == adafruit_fingerprint.OK:
                sensor_results[port] = True
                logger.info(f"✅ AS608 sensor found on {port}")
                logger.info(f"   Templates: {finger.template_count}")
            else:
                sensor_results[port] = False
                logger.info(f"❌ Not an AS608 sensor on {port}")
            
            uart.close()
            
        except Exception as e:
            sensor_results[port] = False
            logger.error(f"❌ Error testing {port}: {e}")
    
    return sensor_results

def run_dual_system():
    """Run dual sensor system"""
    logger.info("Starting dual sensor system...")
    
    try:
        from dual_fingerprint_simple_client import main as dual_main
        dual_main()
    except Exception as e:
        logger.error(f"Error running dual system: {e}")
        return False
    
    return True

def main():
    """Main function"""
    logger.info("DUAL SENSOR SYSTEM - FIXED VERSION")
    logger.info("=" * 50)
    
    # Update configuration
    if not update_config():
        logger.error("❌ Failed to update configuration")
        return 1
    
    # Test ports
    port_results = test_ports()
    accessible_ports = sum(1 for result in port_results.values() if result)
    
    if accessible_ports < 2:
        logger.error("❌ Not enough accessible ports!")
        logger.info("Check permissions: sudo chmod 666 /dev/serial* /dev/ttyS*")
        return 1
    
    # Test sensors
    sensor_results = test_sensors()
    working_sensors = sum(1 for result in sensor_results.values() if result)
    
    if working_sensors < 2:
        logger.warning("⚠️  Less than 2 AS608 sensors working")
        logger.info("Check sensor connections and power supply")
        return 1
    
    # Run dual system
    logger.info("✅ All tests passed!")
    logger.info("Starting dual sensor system...")
    
    try:
        run_dual_system()
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
