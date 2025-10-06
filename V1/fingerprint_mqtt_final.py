#!/usr/bin/env python3
"""
Final Fingerprint MQTT Client for Raspberry Pi 4
Uses custom AS608 driver for reliable operation
"""

import time
import json
import logging
from datetime import datetime
import paho.mqtt.client as mqtt
from as608_driver import AS608Driver

# Configuration
STORE_ID = "Store001"
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"
FINGERPRINT_PORT = "/dev/ttyUSB0"  # Change to /dev/ttyACM0 if needed
BAUD_RATE = 57600
CONFIDENCE_THRESHOLD = 50
SCAN_INTERVAL = 2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fingerprint_mqtt.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FingerprintMQTTClient:
    def __init__(self):
        self.store_id = STORE_ID
        self.mqtt_client = None
        self.fingerprint = None
        self.setup_fingerprint_sensor()
        self.setup_mqtt_client()
    
    def setup_fingerprint_sensor(self):
        """Initialize the AS608 fingerprint sensor"""
        try:
            self.fingerprint = AS608Driver(FINGERPRINT_PORT, BAUD_RATE)
            
            if self.fingerprint.connect():
                logger.info("Fingerprint sensor connected successfully")
                
                # Get template count
                count = self.fingerprint.get_template_count()
                logger.info(f"Stored templates: {count}")
            else:
                logger.error("Failed to connect to fingerprint sensor")
                raise Exception("Fingerprint sensor connection failed")
                
        except Exception as e:
            logger.error(f"Error setting up fingerprint sensor: {e}")
            raise
    
    def setup_mqtt_client(self):
        """Initialize MQTT client"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_publish = self.on_mqtt_publish
            
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
        except Exception as e:
            logger.error(f"Error setting up MQTT client: {e}")
            raise
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def on_mqtt_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        logger.info(f"Message published successfully. Message ID: {mid}")
    
    def get_fingerprint_image(self):
        """Get fingerprint image and return finger ID"""
        try:
            logger.info("Waiting for fingerprint...")
            
            # Get fingerprint and search for match
            finger_id = self.fingerprint.get_fingerprint(CONFIDENCE_THRESHOLD)
            
            if finger_id is not None:
                logger.info(f"Fingerprint match found: ID={finger_id}, Confidence={self.fingerprint.confidence}")
                return finger_id
            else:
                logger.info("No fingerprint match found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting fingerprint: {e}")
            return None
    
    def send_fingerprint_data(self, finger_id):
        """Send fingerprint data to MQTT server"""
        try:
            timestamp = datetime.now().isoformat()
            
            payload = {
                "store_id": self.store_id,
                "finger_id": finger_id,
                "Timestamp": timestamp
            }
            
            message = json.dumps(payload)
            
            logger.info(f"Sending data: {message}")
            
            # Publish to MQTT
            result = self.mqtt_client.publish(MQTT_TOPIC, message, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info("Data sent successfully to MQTT server")
                return True
            else:
                logger.error(f"Failed to send data. Error code: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending fingerprint data: {e}")
            return False
    
    def run(self):
        """Main loop"""
        logger.info("Starting fingerprint sensor monitoring...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                # Get fingerprint
                finger_id = self.get_fingerprint_image()
                
                if finger_id is not None:
                    # Send data to server
                    if self.send_fingerprint_data(finger_id):
                        logger.info("Fingerprint data sent successfully")
                    else:
                        logger.error("Failed to send fingerprint data")
                else:
                    logger.info("No valid fingerprint detected")
                
                # Wait before next scan
                time.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Stopping fingerprint sensor monitoring...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("MQTT client disconnected")
            
            if self.fingerprint:
                self.fingerprint.disconnect()
                logger.info("Fingerprint sensor disconnected")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main function"""
    try:
        client = FingerprintMQTTClient()
        client.run()
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
