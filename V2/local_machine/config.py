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
FINGERPRINT_PORT = os.getenv("FINGERPRINT_PORT", "/dev/serial0")  # Raspberry Pi UART - change to /dev/ttyUSB0 for USB adapter
BAUD_RATE = int(os.getenv("BAUD_RATE", "57600"))
CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD", "50"))  # Minimum confidence for fingerprint match

# Application Configuration
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "5"))  # Seconds between scans
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = os.getenv("LOG_FILE", "fingerprint_mqtt.log")

# MQTT Authentication
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
