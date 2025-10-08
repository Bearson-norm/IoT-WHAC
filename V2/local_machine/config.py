"""
Configuration file for Fingerprint MQTT Client
Modify these settings according to your setup
"""

# Store Configuration
STORE_ID = "Store001"

# MQTT Configuration
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"
MQTT_KEEPALIVE = 60
MQTT_QOS = 1

# Fingerprint Sensor Configuration
FINGERPRINT_PORT = "/dev/serial0"  # Raspberry Pi UART - change to /dev/ttyUSB0 for USB adapter
BAUD_RATE = 57600
CONFIDENCE_THRESHOLD = 50  # Minimum confidence for fingerprint match

# Application Configuration
SCAN_INTERVAL = 5  # Seconds between scans
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "fingerprint_mqtt.log"

# MQTT Authentication (uncomment and fill if your broker requires authentication)
# MQTT_USERNAME = "your_username"
# MQTT_PASSWORD = "your_password"
