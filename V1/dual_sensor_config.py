"""
Configuration file for Dual AS608 Fingerprint Sensors
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

# Dual AS608 Fingerprint Sensor Configuration
SENSORS = {
    "sensor_1": {
        "port": "/dev/ttyUSB0",  # First sensor port
        "baudrate": 57600,
        "device_id": "AS608_001",
        "enabled": True,
        "description": "Main Entry Sensor"
    },
    "sensor_2": {
        "port": "/dev/ttyUSB1",  # Second sensor port
        "baudrate": 57600,
        "device_id": "AS608_002", 
        "enabled": True,
        "description": "Secondary Entry Sensor"
    }
}

# Alternative configuration for different port setups
# Uncomment and modify as needed:

# For USB-to-Serial adapters:
# SENSORS = {
#     "sensor_1": {
#         "port": "/dev/ttyUSB0",
#         "baudrate": 57600,
#         "device_id": "AS608_001",
#         "enabled": True,
#         "description": "Main Entry Sensor"
#     },
#     "sensor_2": {
#         "port": "/dev/ttyUSB1",
#         "baudrate": 57600,
#         "device_id": "AS608_002",
#         "enabled": True,
#         "description": "Secondary Entry Sensor"
#     }
# }

# For mixed USB/ACM ports:
# SENSORS = {
#     "sensor_1": {
#         "port": "/dev/ttyUSB0",
#         "baudrate": 57600,
#         "device_id": "AS608_001",
#         "enabled": True,
#         "description": "Main Entry Sensor"
#     },
#     "sensor_2": {
#         "port": "/dev/ttyACM0",
#         "baudrate": 57600,
#         "device_id": "AS608_002",
#         "enabled": True,
#         "description": "Secondary Entry Sensor"
#     }
# }

# For built-in serial ports (if using level shifters):
# SENSORS = {
#     "sensor_1": {
#         "port": "/dev/serial0",
#         "baudrate": 57600,
#         "device_id": "AS608_001",
#         "enabled": True,
#         "description": "Main Entry Sensor"
#     },
#     "sensor_2": {
#         "port": "/dev/serial1",
#         "baudrate": 57600,
#         "device_id": "AS608_002",
#         "enabled": True,
#         "description": "Secondary Entry Sensor"
#     }
# }

# Application Configuration
CONFIDENCE_THRESHOLD = 50  # Minimum confidence for fingerprint match
SCAN_INTERVAL = 2  # Seconds between scans for each sensor
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "dual_fingerprint_mqtt.log"

# MQTT Topics Configuration
MQTT_TOPICS = {
    "scan_result": "WHAC/Store001/in",
    "add_user": "WHAC/Store001/add_user",
    "import_users": "WHAC/Store001/import",
    "export_users": "WHAC/Store001/export",
    "relay_action": "WHAC/Store001/action",
    "relay_status": "WHAC/Store001/relay_status",
    "exit_request": "WHAC/Store001/exit"
}

# Relay Control Configuration (optional)
RELAY_CONFIG = {
    "enabled": True,
    "pin": 18,  # GPIO pin for relay control
    "access_duration": 10  # seconds
}

# MQTT Authentication (uncomment and fill if your broker requires authentication)
# MQTT_USERNAME = "your_username"
# MQTT_PASSWORD = "your_password"

# Database Configuration
DATABASE_FILE = "dual_fingerprints.db"

# Notification Configuration
NOTIFICATIONS = {
    "enabled": True,
    "mp3_system": True,
    "access_granted_sound": "access_granted.mp3",
    "access_denied_sound": "access_denied.mp3"
}
