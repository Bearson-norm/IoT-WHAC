#!/usr/bin/env python3
"""
Raspberry Pi 4 Fingerprint Sensor AS608 MQTT Client
Sends fingerprint data to MQTT server at 103.87.67.139
"""

import time
import json
import logging
from datetime import datetime
import paho.mqtt.client as mqtt
import serial
from adafruit_fingerprint import AdafruitFingerprint
from config import *

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
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
            # Create serial connection
            uart = serial.Serial(FINGERPRINT_PORT, baudrate=BAUD_RATE, timeout=1)
            self.fingerprint = AdafruitFingerprint(uart)
            
            if self.fingerprint.begin():
                logger.info("Fingerprint sensor initialized successfully")
            else:
                logger.error("Failed to initialize fingerprint sensor")
                raise Exception("Fingerprint sensor initialization failed")
                
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
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
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
            
            # Wait for fingerprint
            while self.fingerprint.get_image() != AdafruitFingerprint.OK:
                pass
            
            logger.info("Fingerprint image captured")
            
            # Convert image
            if self.fingerprint.image_2_tz(1) != AdafruitFingerprint.OK:
                logger.error("Failed to convert image")
                return None
            
            # Search for fingerprint
            if self.fingerprint.finger_search() != AdafruitFingerprint.OK:
                logger.warning("Fingerprint not found in database")
                return None
            
            finger_id = self.fingerprint.finger_id
            confidence = self.fingerprint.confidence
            
            logger.info(f"Fingerprint found! ID: {finger_id}, Confidence: {confidence}")
            
            if confidence >= CONFIDENCE_THRESHOLD:
                return finger_id
            else:
                logger.warning(f"Low confidence match: {confidence}")
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
            result = self.mqtt_client.publish(MQTT_TOPIC, message, qos=MQTT_QOS)
            
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
                # Close serial connection
                if hasattr(self.fingerprint, '_uart'):
                    self.fingerprint._uart.close()
                logger.info("Fingerprint sensor connection closed")
                
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
