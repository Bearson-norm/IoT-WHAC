"""
Configuration file for Fingerprint Raw Data MQTT Client
Modify these settings according to your setup
"""

# Store Configuration
STORE_ID = "Store001"

# MQTT Configuration
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/raw"  # Different topic for raw data
MQTT_KEEPALIVE = 60
MQTT_QOS = 1

# Fingerprint Sensor Configuration
FINGERPRINT_PORT = "/dev/ttyUSB0"  # Change to /dev/ttyACM0 if needed
BAUD_RATE = 57600

# Raw Data Configuration
HASH_LENGTH = 8  # Length of compact hash (6-12 digits)
CHECKSUM_LENGTH = 6  # Length of checksum (6-12 digits)

# Application Configuration
SCAN_INTERVAL = 2  # Seconds between scans
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "fingerprint_raw_mqtt.log"

# MQTT Authentication (uncomment and fill if your broker requires authentication)
# MQTT_USERNAME = "your_username"
# MQTT_PASSWORD = "your_password"
