#!/usr/bin/env python3
"""
Relay Controller for WHAC Fingerprint System
Controls relay based on MQTT commands from web UI
"""

import paho.mqtt.client as mqtt
import json
import logging
import RPi.GPIO as GPIO
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RelayController:
    def __init__(self, relay_pin=18, mqtt_broker="103.87.67.139", mqtt_port=1883):
        """
        Initialize relay controller
        
        Args:
            relay_pin: GPIO pin number for relay control
            mqtt_broker: MQTT broker IP address
            mqtt_port: MQTT broker port
        """
        self.relay_pin = relay_pin
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.connected = False
        
        # MQTT Topics
        self.ACTION_TOPIC = "WHAC/Store001/action"
        self.STATUS_TOPIC = "WHAC/Store001/relay_status"
        
        # Setup GPIO
        self.setup_gpio()
        
        # Setup MQTT
        self.setup_mqtt()
    
    def setup_gpio(self):
        """Setup GPIO for relay control"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.relay_pin, GPIO.OUT)
            GPIO.output(self.relay_pin, GPIO.LOW)  # Start with relay OFF
            logger.info(f"✓ GPIO setup complete - Relay on pin {self.relay_pin}")
        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("✓ MQTT client connected for relay control")
            else:
                logger.error("✗ Failed to connect to MQTT broker within timeout")
                
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT client connected")
            client.subscribe(self.ACTION_TOPIC)
            logger.info(f"Subscribed to {self.ACTION_TOPIC}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning(f"MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT action messages"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received relay command: {payload}")
            
            command = payload.get('command')
            user_id = payload.get('user_id')
            action = payload.get('action')
            source = payload.get('source')
            
            if command == 'grant':
                self.grant_access(user_id, action, source)
            elif command == 'deny':
                self.deny_access(user_id, action, source)
            else:
                logger.warning(f"Unknown command: {command}")
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def grant_access(self, user_id, action, source):
        """Grant access by activating relay"""
        try:
            logger.info(f"Granting access for user {user_id}")
            
            # Activate relay (assuming relay is active HIGH)
            GPIO.output(self.relay_pin, GPIO.HIGH)
            
            # Send status update
            self.send_status_update('granted', user_id, action, source)
            
            # Keep relay active for 3 seconds
            time.sleep(3)
            
            # Deactivate relay
            GPIO.output(self.relay_pin, GPIO.LOW)
            
            logger.info(f"✓ Access granted for user {user_id} - Relay activated for 3 seconds")
            
        except Exception as e:
            logger.error(f"Error granting access: {e}")
    
    def deny_access(self, user_id, action, source):
        """Deny access by keeping relay off"""
        try:
            logger.info(f"Denying access for user {user_id}")
            
            # Ensure relay is off
            GPIO.output(self.relay_pin, GPIO.LOW)
            
            # Send status update
            self.send_status_update('denied', user_id, action, source)
            
            logger.info(f"✓ Access denied for user {user_id} - Relay remains off")
            
        except Exception as e:
            logger.error(f"Error denying access: {e}")
    
    def send_status_update(self, status, user_id, action, source):
        """Send relay status update via MQTT"""
        try:
            if not self.connected:
                logger.error("MQTT not connected, cannot send status update")
                return False
            
            payload = {
                'status': status,
                'user_id': user_id,
                'action': action,
                'source': source,
                'timestamp': datetime.now().isoformat(),
                'relay_pin': self.relay_pin,
                'device_id': 'AS608_001'
            }
            
            result = self.mqtt_client.publish(self.STATUS_TOPIC, json.dumps(payload))
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Status update sent: {status} for user {user_id}")
                return True
            else:
                logger.error(f"✗ Failed to send status update (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return False
    
    def test_relay(self):
        """Test relay functionality"""
        try:
            logger.info("Testing relay...")
            
            # Turn on relay
            GPIO.output(self.relay_pin, GPIO.HIGH)
            logger.info("Relay ON")
            time.sleep(2)
            
            # Turn off relay
            GPIO.output(self.relay_pin, GPIO.LOW)
            logger.info("Relay OFF")
            
            logger.info("✓ Relay test completed")
            
        except Exception as e:
            logger.error(f"Relay test error: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up relay controller...")
            
            # Turn off relay
            GPIO.output(self.relay_pin, GPIO.LOW)
            
            # Disconnect MQTT
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("MQTT client disconnected")
            
            # Cleanup GPIO
            GPIO.cleanup()
            logger.info("GPIO cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main function for testing relay controller"""
    relay = RelayController()
    
    try:
        logger.info("=" * 60)
        logger.info("WHAC Relay Controller - Running!")
        logger.info("=" * 60)
        logger.info(f"Relay Pin: {relay.relay_pin}")
        logger.info(f"MQTT Broker: {relay.mqtt_broker}:{relay.mqtt_port}")
        logger.info(f"Action Topic: {relay.ACTION_TOPIC}")
        logger.info("=" * 60)
        logger.info("✓ Listening for relay control commands...")
        logger.info("✓ Ready to control relay based on web UI decisions")
        logger.info("=" * 60)
        
        # Test relay
        relay.test_relay()
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Relay controller stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        relay.cleanup()

if __name__ == "__main__":
    main()
