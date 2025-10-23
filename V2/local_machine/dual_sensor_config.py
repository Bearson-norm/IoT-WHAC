"""
Configuration file for Dual AS608 Fingerprint Sensors
Based on existing system structure with 3.3V support
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

# Dual AS608 Fingerprint Sensor Configuration (3.3V compatible)
SENSORS = {
    "sensor_1": {
        "port": os.getenv("SENSOR_1_PORT", "/dev/ttyUSB0"),  # First sensor port
        "baudrate": int(os.getenv("SENSOR_1_BAUDRATE", "57600")),
        "device_id": "AS608_001",
        "enabled": True,
        "description": "Main Entry Sensor",
        "voltage": "3.3V"  # AS608 running on 3.3V
    },
    "sensor_2": {
        "port": os.getenv("SENSOR_2_PORT", "/dev/ttyUSB1"),  # Second sensor port
        "baudrate": int(os.getenv("SENSOR_2_BAUDRATE", "57600")),
        "device_id": "AS608_002", 
        "enabled": True,
        "description": "Secondary Entry Sensor",
        "voltage": "3.3V"  # AS608 running on 3.3V
    }
}

# Alternative configuration for different port setups
# Uncomment and modify as needed:

# For USB-to-Serial adapters (RECOMMENDED for 3.3V):
# SENSORS = {
#     "sensor_1": {
#         "port": "/dev/ttyUSB0",
#         "baudrate": 57600,
#         "device_id": "AS608_001",
#         "enabled": True,
#         "description": "Main Entry Sensor",
#         "voltage": "3.3V"
#     },
#     "sensor_2": {
#         "port": "/dev/ttyUSB1",
#         "baudrate": 57600,
#         "device_id": "AS608_002",
#         "enabled": True,
#         "description": "Secondary Entry Sensor",
#         "voltage": "3.3V"
#     }
# }

# For mixed USB/ACM ports:
# SENSORS = {
#     "sensor_1": {
#         "port": "/dev/ttyUSB0",
#         "baudrate": 57600,
#         "device_id": "AS608_001",
#         "enabled": True,
#         "description": "Main Entry Sensor",
#         "voltage": "3.3V"
#     },
#     "sensor_2": {
#         "port": "/dev/ttyACM0",
#         "baudrate": 57600,
#         "device_id": "AS608_002",
#         "enabled": True,
#         "description": "Secondary Entry Sensor",
#         "voltage": "3.3V"
#     }
# }

# For built-in serial ports (if using level shifters - NOT NEEDED for 3.3V):
# SENSORS = {
#     "sensor_1": {
#         "port": "/dev/serial0",
#         "baudrate": 57600,
#         "device_id": "AS608_001",
#         "enabled": True,
#         "description": "Main Entry Sensor",
#         "voltage": "3.3V"
#     },
#     "sensor_2": {
#         "port": "/dev/serial1",
#         "baudrate": 57600,
#         "device_id": "AS608_002",
#         "enabled": True,
#         "description": "Secondary Entry Sensor",
#         "voltage": "3.3V"
#     }
# }

# Application Configuration
CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD", "50"))  # Minimum confidence for fingerprint match
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "5"))  # Seconds between scans
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = os.getenv("LOG_FILE", "dual_fingerprint_mqtt.log")

# MQTT Topics Configuration (same as existing system)
MQTT_TOPICS = {
    "scan_result": MQTT_TOPIC,  # "WHAC/Store001/in"
    "add_user": "WHAC/Store001/add_user",
    "import_users": "WHAC/Store001/import",
    "export_users": "WHAC/Store001/export",
    "relay_action": "WHAC/Store001/action",
    "relay_status": "WHAC/Store001/relay_status",
    "exit_request": f"WHAC/{STORE_ID}/exit"
}

# Relay Control Configuration (same as existing system)
RELAY_CONFIG = {
    "enabled": True,
    "pin": int(os.getenv("RELAY_PIN", "18")),  # GPIO pin for relay control
    "access_duration": int(os.getenv("ACCESS_DURATION", "10"))  # seconds
}

# MQTT Authentication (same as existing system)
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# Database Configuration
DATABASE_FILE = os.getenv("DATABASE_FILE", "dual_fingerprints.db")

# Notification Configuration (same as existing system)
NOTIFICATIONS = {
    "enabled": True,
    "mp3_system": True,
    "access_granted_sound": "access_granted.mp3",
    "access_denied_sound": "access_denied.mp3"
}

# Hardware Configuration for 3.3V AS608
HARDWARE_CONFIG = {
    "voltage": "3.3V",
    "level_shifter_required": False,  # No level shifter needed for 3.3V
    "gpio_pins": {
        "relay": RELAY_CONFIG["pin"],  # GPIO18 - Relay control
        "exit_button": 16,  # GPIO pin for exit button (if used)
        "led_status": 21,   # GPIO pin for status LED (if used)
        # GPIO pins for dual AS608 sensors
        "sensor_1": {
            "tx": 14,  # GPIO14 - Hardware UART TX
            "rx": 15   # GPIO15 - Hardware UART RX
        },
        "sensor_2": {
            "tx": 20,  # GPIO20 - Software UART TX (alternative to GPIO18)
            "rx": 21   # GPIO21 - Software UART RX (alternative to GPIO19)
        }
    },
    "power_requirements": {
        "as608_current": "120mA",  # Typical current for AS608 at 3.3V
        "total_sensors": 2,
        "recommended_power_supply": "5V 2A"  # For Raspberry Pi + 2x AS608
    }
}
