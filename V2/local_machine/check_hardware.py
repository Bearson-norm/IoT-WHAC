#!/usr/bin/env python3
"""
Check hardware connection for dual sensors
"""

import os
import glob
import logging
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_usb_devices():
    """Check USB devices"""
    logger.info("Checking USB devices...")
    
    try:
        # Check lsusb output
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("USB devices found:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        else:
            logger.warning("lsusb command failed")
    except Exception as e:
        logger.error(f"Error checking USB devices: {e}")

def check_serial_ports():
    """Check available serial ports"""
    logger.info("Checking serial ports...")
    
    # Check USB serial ports
    usb_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    logger.info(f"USB serial ports: {usb_ports}")
    
    # Check built-in serial ports
    serial_ports = []
    for i in range(5):
        port = f"/dev/serial{i}"
        if os.path.exists(port):
            serial_ports.append(port)
    logger.info(f"Built-in serial ports: {serial_ports}")
    
    # Check other ports
    other_ports = glob.glob('/dev/ttyS*')
    logger.info(f"Other serial ports: {other_ports}")
    
    all_ports = usb_ports + serial_ports + other_ports
    logger.info(f"Total ports found: {len(all_ports)}")
    
    return all_ports

def check_dmesg():
    """Check kernel messages for USB devices"""
    logger.info("Checking kernel messages for USB devices...")
    
    try:
        result = subprocess.run(['dmesg'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            usb_lines = [line for line in lines if 'usb' in line.lower() and 'tty' in line.lower()]
            if usb_lines:
                logger.info("USB serial device messages:")
                for line in usb_lines[-10:]:  # Last 10 lines
                    if line.strip():
                        logger.info(f"  {line}")
            else:
                logger.info("No USB serial device messages found")
        else:
            logger.warning("dmesg command failed")
    except Exception as e:
        logger.error(f"Error checking dmesg: {e}")

def check_hardware_connection():
    """Check hardware connection"""
    logger.info("DUAL SENSOR HARDWARE CHECK")
    logger.info("=" * 50)
    
    # Check USB devices
    check_usb_devices()
    
    # Check serial ports
    ports = check_serial_ports()
    
    # Check kernel messages
    check_dmesg()
    
    # Analysis
    logger.info("\n" + "=" * 50)
    logger.info("HARDWARE ANALYSIS")
    logger.info("=" * 50)
    
    if len(ports) < 2:
        logger.warning("⚠️  Less than 2 serial ports found!")
        logger.info("For dual sensor setup, you need:")
        logger.info("1. Two USB-to-Serial adapters")
        logger.info("2. Two AS608 sensors (3.3V)")
        logger.info("3. Proper connections:")
        logger.info("   AS608_1 → USB-to-Serial_1 → Pi USB port 1")
        logger.info("   AS608_2 → USB-to-Serial_2 → Pi USB port 2")
        logger.info("")
        logger.info("Expected ports:")
        logger.info("  /dev/ttyUSB0 (first sensor)")
        logger.info("  /dev/ttyUSB1 (second sensor)")
        return False
    else:
        logger.info("✅ Found enough serial ports for dual setup")
        logger.info(f"Available ports: {ports}")
        return True

def main():
    """Main function"""
    return check_hardware_connection()

if __name__ == "__main__":
    exit(main())
