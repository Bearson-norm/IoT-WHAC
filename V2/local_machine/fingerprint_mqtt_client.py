#!/usr/bin/env python3
"""
Fingerprint MQTT Client for AS608 Sensor
Reads fingerprints and sends data to MQTT broker
"""

import serial
import adafruit_fingerprint
import paho.mqtt.client as mqtt
import json
import time
import logging
import sys
from datetime import datetime
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FingerprintMQTTClient:
    def __init__(self):
        self.uart = None
        self.finger = None
        self.mqtt_client = None
        self.connected = False
        self.last_scan_time = 0
        
    def connect_sensor(self, retries=3):
        """Connect to AS608 fingerprint sensor with retry logic"""
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to fingerprint sensor on {FINGERPRINT_PORT} (attempt {attempt + 1})")
                self.uart = serial.Serial(FINGERPRINT_PORT, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)  # Give sensor time to stabilize
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                
                # Test connection
                if self.finger.read_templates() == adafruit_fingerprint.OK:
                    logger.info(f"✓ Fingerprint sensor connected successfully! Templates: {self.finger.template_count}")
                    return True
                else:
                    raise Exception("Failed to read templates from sensor")
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self.uart:
                    self.uart.close()
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    raise
        return False
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client = mqtt.Client()
            
            # Set up callbacks
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_publish = self.on_mqtt_publish
            
            # Connect to broker
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("✓ MQTT broker connected successfully!")
                return True
            else:
                logger.error("✗ Failed to connect to MQTT broker within timeout")
                return False
                
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT client connected")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning(f"MQTT client disconnected (code: {rc})")
    
    def on_mqtt_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        logger.debug(f"Message published (mid: {mid})")
    
    def send_fingerprint_data(self, finger_id, confidence, action="scan"):
        """Send fingerprint data to MQTT broker"""
        if not self.connected:
            logger.error("MQTT not connected, cannot send data")
            return False
        
        try:
            # Prepare data payload
            data = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "fingerprint_id": finger_id,
                "confidence": confidence,
                "device_type": "fingerprint_scanner",
                "device_id": "AS608_001"
            }
            
            # Convert to JSON
            payload = json.dumps(data)
            
            # Publish to MQTT
            result = self.mqtt_client.publish(MQTT_TOPIC, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Data sent to MQTT: ID={finger_id}, Confidence={confidence}")
                return True
            else:
                logger.error(f"✗ Failed to publish to MQTT (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending data to MQTT: {e}")
            return False
    
    def scan_fingerprint(self):
        """Scan and process fingerprint"""
        try:
            # Check if enough time has passed since last scan
            current_time = time.time()
            if current_time - self.last_scan_time < SCAN_INTERVAL:
                return False
            
            # Get fingerprint image
            i = self.finger.get_image()
            if i == adafruit_fingerprint.OK:
                logger.debug("Fingerprint image captured")
                
                # Convert image to template
                if self.finger.image_2_tz(1) == adafruit_fingerprint.OK:
                    logger.debug("Image converted to template")
                    
                    # Search for match
                    i = self.finger.finger_search()
                    
                    if i == adafruit_fingerprint.OK:
                        # Match found
                        finger_id = self.finger.finger_id
                        confidence = self.finger.confidence
                        
                        logger.info(f"✓ Match found! ID: {finger_id}, Confidence: {confidence}")
                        
                        # Check confidence threshold
                        if confidence >= CONFIDENCE_THRESHOLD:
                            # Send data to MQTT
                            self.send_fingerprint_data(finger_id, confidence, "access_granted")
                            self.last_scan_time = current_time
                            return True
                        else:
                            logger.warning(f"Confidence too low: {confidence} < {CONFIDENCE_THRESHOLD}")
                            self.send_fingerprint_data(finger_id, confidence, "access_denied_low_confidence")
                            self.last_scan_time = current_time
                            return True
                    else:
                        # No match found
                        logger.info("✗ No match found")
                        self.send_fingerprint_data(0, 0, "no_match")
                        self.last_scan_time = current_time
                        return True
                else:
                    logger.error("Failed to convert image to template")
                    return False
            elif i == adafruit_fingerprint.NOFINGER:
                # No finger detected, this is normal
                return False
            else:
                logger.error(f"Error getting fingerprint image: {i}")
                return False
                
        except Exception as e:
            logger.error(f"Error during fingerprint scan: {e}")
            return False
    
    def enroll_fingerprint(self, location):
        """Enroll a new fingerprint at the specified location"""
        logger.info(f"Starting fingerprint enrollment at location {location}")
        
        try:
            # First scan
            logger.info("Place finger on sensor for first scan...")
            while True:
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                if i == adafruit_fingerprint.NOFINGER:
                    continue
                else:
                    logger.error(f"Error getting first image: {i}")
                    return False
            
            logger.info("First image captured!")
            
            if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
                logger.error("Error converting first image")
                return False
            
            logger.info("Remove finger...")
            time.sleep(2)
            
            while self.finger.get_image() != adafruit_fingerprint.NOFINGER:
                pass
            
            # Second scan
            logger.info("Place same finger again for second scan...")
            while True:
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                if i == adafruit_fingerprint.NOFINGER:
                    continue
                else:
                    logger.error(f"Error getting second image: {i}")
                    return False
            
            logger.info("Second image captured!")
            
            if self.finger.image_2_tz(2) != adafruit_fingerprint.OK:
                logger.error("Error converting second image")
                return False
            
            # Create model
            logger.info("Creating fingerprint model...")
            if self.finger.create_model() != adafruit_fingerprint.OK:
                logger.error("Error creating model - fingers didn't match?")
                return False
            
            # Store model
            logger.info(f"Storing model at location {location}...")
            if self.finger.store_model(location) != adafruit_fingerprint.OK:
                logger.error("Error storing model")
                return False
            
            logger.info(f"✓ Fingerprint enrolled successfully at location {location}!")
            
            # Send enrollment notification to MQTT
            self.send_fingerprint_data(location, 100, "enrollment_complete")
            return True
            
        except Exception as e:
            logger.error(f"Error during enrollment: {e}")
            return False
    
    def get_template_count(self):
        """Get number of stored fingerprints"""
        try:
            if self.finger.read_templates() == adafruit_fingerprint.OK:
                count = self.finger.template_count
                logger.info(f"Stored fingerprints: {count}")
                return count
            else:
                logger.error("Failed to read template count")
                return -1
        except Exception as e:
            logger.error(f"Error getting template count: {e}")
            return -1
    
    def run_continuous_scan(self):
        """Run continuous fingerprint scanning"""
        logger.info("Starting continuous fingerprint scanning...")
        logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
        logger.info(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
        
        try:
            while True:
                self.scan_fingerprint()
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
        except KeyboardInterrupt:
            logger.info("Scanning stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous scan: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        
        if self.uart:
            self.uart.close()
            logger.info("Serial connection closed")

def main():
    """Main function"""
    client = FingerprintMQTTClient()
    
    try:
        # Connect to fingerprint sensor
        if not client.connect_sensor():
            logger.error("Failed to connect to fingerprint sensor")
            return 1
        
        # Connect to MQTT broker
        if not client.connect_mqtt():
            logger.error("Failed to connect to MQTT broker")
            return 1
        
        # Show initial status
        template_count = client.get_template_count()
        
        logger.info("=" * 60)
        logger.info("Fingerprint MQTT Client - Ready!")
        logger.info("=" * 60)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"MQTT Topic: {MQTT_TOPIC}")
        logger.info(f"Stored Templates: {template_count}")
        logger.info("=" * 60)
        
        # Start continuous scanning
        client.run_continuous_scan()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        client.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
