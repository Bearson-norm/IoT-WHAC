#!/usr/bin/env python3
"""
Fix same port issue for dual sensors
"""

import os
import glob
import logging
import time
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_current_setup():
    """Check current sensor setup"""
    logger.info("Checking current sensor setup...")
    
    # Check available ports
    usb_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    serial_ports = []
    for i in range(5):
        port = f"/dev/serial{i}"
        if os.path.exists(port):
            serial_ports.append(port)
    
    logger.info(f"USB ports: {usb_ports}")
    logger.info(f"Serial ports: {serial_ports}")
    
    return usb_ports, serial_ports

def check_processes_using_ports():
    """Check which processes are using serial ports"""
    logger.info("Checking processes using serial ports...")
    
    try:
        result = subprocess.run(['lsof', '/dev/serial*', '/dev/ttyUSB*', '/dev/ttyACM*'], 
                              capture_output=True, text=True)
        if result.stdout:
            logger.info("Processes using serial ports:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        else:
            logger.info("No processes using serial ports")
    except Exception as e:
        logger.error(f"Error checking processes: {e}")

def create_virtual_ports():
    """Create virtual serial ports for testing"""
    logger.info("Creating virtual serial ports for testing...")
    
    try:
        # Create virtual serial ports using socat
        logger.info("Creating virtual serial ports...")
        
        # Kill any existing socat processes
        subprocess.run(['pkill', 'socat'], capture_output=True)
        
        # Create virtual serial ports
        subprocess.Popen(['socat', 'pty,link=/tmp/virtual1', 'pty,link=/tmp/virtual2'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(1)
        
        # Check if virtual ports were created
        if os.path.exists('/tmp/virtual1') and os.path.exists('/tmp/virtual2'):
            logger.info("✅ Virtual serial ports created")
            logger.info("  /tmp/virtual1")
            logger.info("  /tmp/virtual2")
            return True
        else:
            logger.error("❌ Failed to create virtual serial ports")
            return False
            
    except Exception as e:
        logger.error(f"Error creating virtual ports: {e}")
        return False

def update_config_for_testing():
    """Update configuration for testing with virtual ports"""
    logger.info("Updating configuration for testing...")
    
    try:
        with open('dual_sensor_config.py', 'r') as f:
            content = f.read()
        
        # Replace ports with virtual ports
        content = content.replace('/dev/ttyUSB0', '/tmp/virtual1')
        content = content.replace('/dev/ttyUSB1', '/tmp/virtual2')
        
        with open('dual_sensor_config.py', 'w') as f:
            f.write(content)
        
        logger.info("✅ Configuration updated for testing")
        return True
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return False

def provide_hardware_solution():
    """Provide hardware solution"""
    logger.info("HARDWARE SOLUTION FOR DUAL SENSORS")
    logger.info("=" * 50)
    
    logger.info("Current issue: Both sensors using same port (/dev/serial0)")
    logger.info("")
    logger.info("SOLUTION: Connect second USB-to-Serial adapter")
    logger.info("")
    logger.info("Required hardware:")
    logger.info("1. Two AS608 sensors (3.3V)")
    logger.info("2. Two USB-to-Serial adapters (3.3V compatible)")
    logger.info("3. Proper connections:")
    logger.info("")
    logger.info("Sensor 1 (Main Entry):")
    logger.info("  AS608_1 VCC → USB-to-Serial_1 3.3V")
    logger.info("  AS608_1 GND → USB-to-Serial_1 GND")
    logger.info("  AS608_1 TX  → USB-to-Serial_1 RX")
    logger.info("  AS608_1 RX  → USB-to-Serial_1 TX")
    logger.info("  USB-to-Serial_1 → Pi USB port 1")
    logger.info("")
    logger.info("Sensor 2 (Secondary Entry):")
    logger.info("  AS608_2 VCC → USB-to-Serial_2 3.3V")
    logger.info("  AS608_2 GND → USB-to-Serial_2 GND")
    logger.info("  AS608_2 TX  → USB-to-Serial_2 RX")
    logger.info("  AS608_2 RX  → USB-to-Serial_2 TX")
    logger.info("  USB-to-Serial_2 → Pi USB port 2")
    logger.info("")
    logger.info("Expected ports after connection:")
    logger.info("  /dev/ttyUSB0 (first sensor)")
    logger.info("  /dev/ttyUSB1 (second sensor)")
    logger.info("")
    logger.info("After connecting second adapter:")
    logger.info("1. Run: python3 fix_dual_sensor_ports.py")
    logger.info("2. Run: python3 dual_fingerprint_simple_client.py")

def main():
    """Main function"""
    logger.info("DUAL SENSOR PORT ISSUE FIX")
    logger.info("=" * 50)
    
    # Check current setup
    usb_ports, serial_ports = check_current_setup()
    
    # Check processes using ports
    check_processes_using_ports()
    
    # Analysis
    logger.info("\n" + "=" * 50)
    logger.info("ANALYSIS")
    logger.info("=" * 50)
    
    if len(usb_ports) < 2:
        logger.warning("⚠️  Less than 2 USB serial ports found!")
        logger.info("Current USB ports: {usb_ports}")
        logger.info("")
        logger.info("PROBLEM: You need 2 USB-to-Serial adapters for dual sensor setup")
        logger.info("")
        logger.info("Current setup:")
        logger.info("  - Only 1 USB-to-Serial adapter connected")
        logger.info("  - Both sensors trying to use same port")
        logger.info("")
        logger.info("SOLUTION:")
        logger.info("1. Connect second USB-to-Serial adapter")
        logger.info("2. Connect second AS608 sensor")
        logger.info("3. Verify both sensors are powered (3.3V)")
        logger.info("4. Check wiring connections")
        
        # Provide hardware solution
        provide_hardware_solution()
        
        return 1
    else:
        logger.info("✅ Found enough USB serial ports")
        logger.info(f"USB ports: {usb_ports}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run: python3 fix_dual_sensor_ports.py")
        logger.info("2. Run: python3 dual_fingerprint_simple_client.py")
        
        return 0

if __name__ == "__main__":
    exit(main())
