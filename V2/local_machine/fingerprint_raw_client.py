#!/usr/bin/env python3
"""
Fingerprint Raw Data MQTT Client for AS608 Sensor
Sends raw fingerprint data or compact hash to MQTT broker
"""

import serial
import adafruit_fingerprint
import paho.mqtt.client as mqtt
import json
import time
import logging
import sys
import hashlib
import base64
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

class FingerprintRawMQTTClient:
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
    
    def get_fingerprint_image_data(self):
        """Get raw fingerprint image data from sensor"""
        try:
            # Get image
            i = self.finger.get_image()
            if i != adafruit_fingerprint.OK:
                return None
            
            # Get image data (this gets the raw image bytes)
            # Note: The AS608 sensor stores images internally, we need to read them
            image_data = self.finger.get_fpdata("image", 1)
            return image_data
            
        except Exception as e:
            logger.error(f"Error getting fingerprint image data: {e}")
            return None
    
    def create_fingerprint_hash(self, image_data, hash_length=8):
        """Create a compact hash from fingerprint image data"""
        try:
            if not image_data:
                return None
            
            # Convert image data to bytes
            if isinstance(image_data, list):
                image_bytes = bytes(image_data)
            else:
                image_bytes = image_data
            
            # Create hash
            hash_obj = hashlib.sha256(image_bytes)
            hash_hex = hash_obj.hexdigest()
            
            # Take first N characters for compact hash
            compact_hash = hash_hex[:hash_length]
            return compact_hash
            
        except Exception as e:
            logger.error(f"Error creating fingerprint hash: {e}")
            return None
    
    def create_fingerprint_checksum(self, image_data, length=6):
        """Create a simple checksum from fingerprint data"""
        try:
            if not image_data:
                return None
            
            # Convert to bytes
            if isinstance(image_data, list):
                image_bytes = bytes(image_data)
            else:
                image_bytes = image_data
            
            # Simple checksum calculation
            checksum = 0
            for byte in image_bytes:
                checksum = (checksum + byte) % (10 ** length)
            
            # Format as string with leading zeros
            return f"{checksum:0{length}d}"
            
        except Exception as e:
            logger.error(f"Error creating fingerprint checksum: {e}")
            return None
    
    def send_fingerprint_data(self, data_type, data_value, confidence=None):
        """Send fingerprint data to MQTT broker"""
        if not self.connected:
            logger.error("MQTT not connected, cannot send data")
            return False
        
        try:
            # Prepare data payload
            payload_data = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "data_type": data_type,
                "device_type": "fingerprint_scanner",
                "device_id": "AS608_001"
            }
            
            # Add data based on type
            if data_type == "raw_image":
                # Encode raw image data as base64
                if isinstance(data_value, list):
                    image_bytes = bytes(data_value)
                else:
                    image_bytes = data_value
                payload_data["image_data"] = base64.b64encode(image_bytes).decode('utf-8')
                payload_data["data_size"] = len(image_bytes)
                
            elif data_type == "compact_hash":
                payload_data["fingerprint_hash"] = data_value
                payload_data["hash_length"] = len(data_value)
                
            elif data_type == "checksum":
                payload_data["fingerprint_checksum"] = data_value
                payload_data["checksum_length"] = len(data_value)
                
            elif data_type == "template":
                # Send template data (mathematical representation)
                if isinstance(data_value, list):
                    template_bytes = bytes(data_value)
                else:
                    template_bytes = data_value
                payload_data["template_data"] = base64.b64encode(template_bytes).decode('utf-8')
                payload_data["template_size"] = len(template_bytes)
            
            if confidence is not None:
                payload_data["confidence"] = confidence
            
            # Convert to JSON
            payload = json.dumps(payload_data)
            
            # Publish to MQTT
            result = self.mqtt_client.publish(MQTT_TOPIC, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ {data_type} data sent to MQTT")
                return True
            else:
                logger.error(f"✗ Failed to publish to MQTT (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending data to MQTT: {e}")
            return False
    
    def scan_fingerprint_raw(self, mode="hash"):
        """Scan fingerprint and send raw data or compact identifier"""
        try:
            # Check if enough time has passed since last scan
            current_time = time.time()
            if current_time - self.last_scan_time < SCAN_INTERVAL:
                return False
            
            # Get fingerprint image
            i = self.finger.get_image()
            if i == adafruit_fingerprint.OK:
                logger.debug("Fingerprint image captured")
                
                if mode == "raw_image":
                    # Get raw image data
                    image_data = self.get_fingerprint_image_data()
                    if image_data:
                        logger.info("Sending raw fingerprint image data")
                        self.send_fingerprint_data("raw_image", image_data)
                        self.last_scan_time = current_time
                        return True
                
                elif mode == "hash":
                    # Create compact hash
                    image_data = self.get_fingerprint_image_data()
                    if image_data:
                        compact_hash = self.create_fingerprint_hash(image_data, 8)
                        if compact_hash:
                            logger.info(f"Sending fingerprint hash: {compact_hash}")
                            self.send_fingerprint_data("compact_hash", compact_hash)
                            self.last_scan_time = current_time
                            return True
                
                elif mode == "checksum":
                    # Create checksum
                    image_data = self.get_fingerprint_image_data()
                    if image_data:
                        checksum = self.create_fingerprint_checksum(image_data, 6)
                        if checksum:
                            logger.info(f"Sending fingerprint checksum: {checksum}")
                            self.send_fingerprint_data("checksum", checksum)
                            self.last_scan_time = current_time
                            return True
                
                elif mode == "template":
                    # Get template data (mathematical representation)
                    if self.finger.image_2_tz(1) == adafruit_fingerprint.OK:
                        template_data = self.finger.get_fpdata("char", 1)
                        if template_data:
                            logger.info("Sending fingerprint template data")
                            self.send_fingerprint_data("template", template_data)
                            self.last_scan_time = current_time
                            return True
                
                else:
                    logger.error(f"Unknown mode: {mode}")
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
    
    def run_continuous_scan(self, mode="hash"):
        """Run continuous fingerprint scanning with specified mode"""
        logger.info(f"Starting continuous fingerprint scanning in {mode} mode...")
        logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
        
        try:
            while True:
                self.scan_fingerprint_raw(mode)
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Fingerprint Raw Data MQTT Client')
    parser.add_argument('--mode', choices=['raw_image', 'hash', 'checksum', 'template'], 
                       default='hash', help='Data mode to send (default: hash)')
    args = parser.parse_args()
    
    client = FingerprintRawMQTTClient()
    
    try:
        # Connect to fingerprint sensor
        if not client.connect_sensor():
            logger.error("Failed to connect to fingerprint sensor")
            return 1
        
        # Connect to MQTT broker
        if not client.connect_mqtt():
            logger.error("Failed to connect to MQTT broker")
            return 1
        
        logger.info("=" * 60)
        logger.info("Fingerprint Raw Data MQTT Client - Ready!")
        logger.info("=" * 60)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"MQTT Topic: {MQTT_TOPIC}")
        logger.info(f"Data Mode: {args.mode}")
        logger.info("=" * 60)
        
        # Start continuous scanning
        client.run_continuous_scan(args.mode)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        client.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
