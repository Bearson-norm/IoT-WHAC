"""
Configuration file for Fingerprint MQTT Client
Supports environment variables for Docker deployment
"""

import os

# Store Configuration
STORE_ID = os.getenv("STORE_ID", "Store001")

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "103.87.67.139")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "WHAC/Store001/in")
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
MQTT_QOS = int(os.getenv("MQTT_QOS", "1"))

# Fingerprint Sensor Configuration
# For single sensor:
FINGERPRINT_PORT = os.getenv("FINGERPRINT_PORT", "/dev/serial0")  # Raspberry Pi UART - change to /dev/ttyUSB0 for USB adapter

# For multiple sensors (comma-separated ports):
# Example: FINGERPRINT_PORTS="/dev/ttyUSB0,/dev/ttyUSB1" or "/dev/serial0,/dev/ttyAMA2"
# 
# IMPORTANT: UART to Device Mapping:
#   uart0 → /dev/ttyAMA0 or /dev/serial0 (default UART)
#   uart1 → /dev/ttyS0 or /dev/serial1 (mini UART, usually for Bluetooth)
#   uart2 → /dev/ttyAMA1
#   uart3 → /dev/ttyAMA2  ⚠️ Note: uart3 maps to ttyAMA2, not ttyAMA3!
#   uart4 → /dev/ttyAMA3  ✅
#   uart5 → /dev/ttyAMA4
#
# To enable uart3 and uart4 in /boot/config.txt:
#   enable_uart=1
#   dtoverlay=uart3,pins_4_5  # This creates /dev/ttyAMA2
#   dtoverlay=uart4,pins_8_9  # This creates /dev/ttyAMA3
#
# Default: Use 2 sensors - /dev/ttyAMA2 (uart3) and /dev/ttyAMA3 (uart4)
# Note: /dev/serial0 might point to ttyS0 (mini UART) instead of ttyAMA0
# To use single sensor, set FINGERPRINT_PORTS="" in environment variable
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/ttyAMA2,/dev/ttyAMA3")
if env_ports.strip() == "":
    # If explicitly set to empty string, use single sensor mode
    FINGERPRINT_PORTS = []
else:
    FINGERPRINT_PORTS = [p.strip() for p in env_ports.split(",") if p.strip()]

BAUD_RATE = int(os.getenv("BAUD_RATE", "57600"))
CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD", "50"))  # Minimum confidence for fingerprint match

# Application Configuration
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "5"))  # Seconds between scans
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = os.getenv("LOG_FILE", "fingerprint_mqtt.log")

# MQTT Authentication
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
