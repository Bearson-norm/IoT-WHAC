#!/usr/bin/env python3
"""
Start dual sensor system with correct configuration
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

def main():
    """Main function"""
    logger.info("DUAL SENSOR SYSTEM STARTUP")
    logger.info("=" * 50)
    
    # Update configuration
    if not update_config():
        logger.error("❌ Failed to update configuration")
        return 1
    
    # Start dual sensor system
    logger.info("Starting dual sensor MQTT client...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        from dual_fingerprint_simple_client import main as dual_main
        dual_main()
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())


