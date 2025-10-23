#!/usr/bin/env python3
"""
Configure dual sensor ports correctly
"""

import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_dual_sensor_config():
    """Update dual sensor configuration with correct ports"""
    logger.info("Updating dual sensor configuration...")
    
    try:
        # Read current config
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
        
        # Write updated config
        with open('dual_sensor_config.py', 'w') as f:
            f.write(content)
        
        logger.info("✅ Configuration updated successfully!")
        logger.info("  Sensor 1: /dev/serial0")
        logger.info("  Sensor 2: /dev/ttyS0")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return False

def test_port_connections():
    """Test connections to both ports"""
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

def test_as608_sensors():
    """Test AS608 sensors on both ports"""
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

def main():
    """Main function"""
    logger.info("DUAL SENSOR PORT CONFIGURATION")
    logger.info("=" * 50)
    
    # Update configuration
    if update_dual_sensor_config():
        logger.info("✅ Configuration updated")
    else:
        logger.error("❌ Failed to update configuration")
        return 1
    
    # Test port connections
    logger.info("\nTesting port connections...")
    port_results = test_port_connections()
    
    # Test AS608 sensors
    logger.info("\nTesting AS608 sensors...")
    sensor_results = test_as608_sensors()
    
    # Results
    logger.info("\n" + "=" * 50)
    logger.info("RESULTS")
    logger.info("=" * 50)
    
    accessible_ports = sum(1 for result in port_results.values() if result)
    working_sensors = sum(1 for result in sensor_results.values() if result)
    
    logger.info(f"Accessible ports: {accessible_ports}/2")
    logger.info(f"Working AS608 sensors: {working_sensors}/2")
    
    if working_sensors >= 2:
        logger.info("✅ Dual sensor setup ready!")
        logger.info("You can now run: python3 dual_fingerprint_simple_client.py")
        return 0
    elif working_sensors == 1:
        logger.warning("⚠️  Only 1 AS608 sensor working")
        logger.info("Check second sensor connection and power")
        return 1
    else:
        logger.error("❌ No AS608 sensors working")
        logger.info("Check sensor connections and power supply")
        return 1

if __name__ == "__main__":
    exit(main())
