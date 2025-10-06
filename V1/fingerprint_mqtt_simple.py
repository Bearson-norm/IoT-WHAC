#!/usr/bin/env python3
"""
Simplified Fingerprint MQTT Client for Raspberry Pi 4
Compatible with newer versions of adafruit-circuitpython-fingerprint
"""

import time
import json
import logging
from datetime import datetime
import paho.mqtt.client as mqtt
import serial

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

# Configuration - you can modify these values
STORE_ID = "Store001"
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"
FINGERPRINT_PORT = "/dev/ttyUSB0"  # Change to /dev/ttyACM0 if needed
BAUD_RATE = 57600
CONFIDENCE_THRESHOLD = 50

class SimpleFingerprintMQTTClient:
    def __init__(self):
        self.store_id = STORE_ID
        self.mqtt_client = None
        self.serial_conn = None
        self.setup_fingerprint_sensor()
        self.setup_mqtt_client()
    
    def setup_fingerprint_sensor(self):
        """Initialize the AS608 fingerprint sensor"""
        try:
            # Create serial connection
            self.serial_conn = serial.Serial(FINGERPRINT_PORT, baudrate=BAUD_RATE, timeout=1)
            logger.info("Serial connection to fingerprint sensor established")
            
            # Test basic communication
            self.send_command([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x07, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1B])
            response = self.read_response()
            if response:
                logger.info("Fingerprint sensor communication test successful")
            else:
                logger.warning("Fingerprint sensor communication test failed")
                
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
    
    def send_command(self, command):
        """Send command to fingerprint sensor"""
        try:
            self.serial_conn.write(bytes(command))
            return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False
    
    def read_response(self, timeout=1):
        """Read response from fingerprint sensor"""
        try:
            start_time = time.time()
            response = []
            
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    byte = self.serial_conn.read(1)
                    if byte:
                        response.append(ord(byte))
                        if len(response) >= 12:  # Minimum response length
                            break
                time.sleep(0.01)
            
            return response if response else None
            
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            return None
    
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
        """Get fingerprint image and return finger ID (simplified)"""
        try:
            logger.info("Waiting for fingerprint...")
            
            # Send get image command
            command = [0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x03, 0x01, 0x00, 0x05]
            self.send_command(command)
            
            # Wait for response
            time.sleep(2)
            response = self.read_response()
            
            if response and len(response) >= 12:
                if response[9] == 0x00:  # OK response
                    logger.info("Fingerprint image captured")
                    
                    # For this simplified version, we'll simulate a fingerprint match
                    # In a real implementation, you'd need to implement the full protocol
                    finger_id = 123  # Simulated finger ID
                    confidence = 75  # Simulated confidence
                    
                    logger.info(f"Simulated fingerprint found! ID: {finger_id}, Confidence: {confidence}")
                    return finger_id
                else:
                    logger.warning(f"Fingerprint capture failed with code: {response[9]}")
                    return None
            else:
                logger.warning("No response from fingerprint sensor")
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
                time.sleep(2)
                
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
            
            if self.serial_conn:
                self.serial_conn.close()
                logger.info("Serial connection closed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main function"""
    try:
        client = SimpleFingerprintMQTTClient()
        client.run()
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
