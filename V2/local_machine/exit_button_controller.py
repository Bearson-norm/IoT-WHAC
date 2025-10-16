#!/usr/bin/env python3
"""
Exit Button Controller for WHAC Fingerprint System
Handles exit warehouse flow with GPIO pushbutton trigger
"""

import paho.mqtt.client as mqtt
import json
import logging
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExitButtonController:
    def __init__(self, exit_button_pin=24, mqtt_broker=MQTT_BROKER, mqtt_port=MQTT_PORT):
        """
        Initialize exit button controller
        
        Args:
            exit_button_pin: GPIO pin number for exit button (default: 24)
            mqtt_broker: MQTT broker IP address
            mqtt_port: MQTT broker port
        """
        self.exit_button_pin = exit_button_pin
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.connected = False
        self.running = True
        self.button_pressed = False
        self.last_press_time = 0
        self.debounce_time = 0.5  # 500ms debounce
        
        # MQTT Topics
        self.EXIT_TOPIC = f"WHAC/{STORE_ID}/exit"
        self.STATUS_TOPIC = f"WHAC/{STORE_ID}/exit_status"
        
        # Setup GPIO
        self.setup_gpio()
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Start button monitoring thread
        self.button_thread = threading.Thread(target=self.monitor_button, daemon=True)
        self.button_thread.start()
    
    def setup_gpio(self):
        """Setup GPIO for exit button"""
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.exit_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Add interrupt for button press
            GPIO.add_event_detect(self.exit_button_pin, GPIO.FALLING, 
                                callback=self.button_callback, bouncetime=300)
            
            logger.info(f"✓ Exit button setup complete - Button on pin {self.exit_button_pin}")
        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(client_id=f"exit_button_{STORE_ID}", clean_session=True)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            logger.info("✓ MQTT client setup complete for exit button")
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Exit button MQTT client connected successfully")
            
            # Subscribe to status topic for acknowledgments
            client.subscribe(self.STATUS_TOPIC, qos=1)
            logger.info(f"✅ Subscribed to status topic: {self.STATUS_TOPIC}")
        else:
            logger.error(f"❌ Exit button MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning(f"Exit button MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message on {topic}: {payload}")
            
            # Handle status acknowledgments
            if "exit_status" in topic:
                status = payload.get('status')
                if status == 'acknowledged':
                    logger.info("✅ Exit request acknowledged by server")
                elif status == 'processed':
                    logger.info("✅ Exit request processed successfully")
                    
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def button_callback(self, channel):
        """Button press callback with debouncing"""
        current_time = time.time()
        
        # Debounce check
        if current_time - self.last_press_time < self.debounce_time:
            return
        
        self.last_press_time = current_time
        self.button_pressed = True
        logger.info("🔘 Exit button pressed!")
    
    def monitor_button(self):
        """Monitor button state in separate thread"""
        while self.running:
            if self.button_pressed:
                self.handle_exit_request()
                self.button_pressed = False
            time.sleep(0.1)
    
    def handle_exit_request(self):
        """Handle exit button press"""
        try:
            logger.info("🚪 Processing exit request...")
            
            # Create exit request payload
            exit_data = {
                "action": "exit_request",
                "timestamp": datetime.now().isoformat(),
                "source": "exit_button",
                "store_id": STORE_ID,
                "button_pin": self.exit_button_pin,
                "status": "requested"
            }
            
            # Send exit request via MQTT
            if self.connected:
                self.mqtt_client.publish(self.EXIT_TOPIC, json.dumps(exit_data), qos=1)
                logger.info(f"📤 Exit request sent to topic: {self.EXIT_TOPIC}")
                
                # Send status update
                self.send_status_update("exit_requested", exit_data)
            else:
                logger.error("❌ Cannot send exit request - MQTT not connected")
                
        except Exception as e:
            logger.error(f"Error handling exit request: {e}")
    
    def send_status_update(self, status, data):
        """Send status update via MQTT"""
        try:
            status_data = {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            if self.connected:
                self.mqtt_client.publish(self.STATUS_TOPIC, json.dumps(status_data), qos=1)
                logger.info(f"📤 Status update sent: {status}")
            else:
                logger.error("❌ Cannot send status update - MQTT not connected")
                
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
    
    def test_button(self):
        """Test button functionality"""
        try:
            logger.info("Testing exit button...")
            
            # Simulate button press
            self.handle_exit_request()
            
            logger.info("✓ Exit button test completed")
            
        except Exception as e:
            logger.error(f"Exit button test error: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up exit button controller...")
            
            self.running = False
            
            # Disconnect MQTT
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("Exit button MQTT client disconnected")
            
            # Cleanup GPIO
            GPIO.cleanup()
            logger.info("Exit button GPIO cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main function for testing exit button controller"""
    try:
        logger.info("🚀 Starting Exit Button Controller...")
        
        # Create exit button controller
        exit_controller = ExitButtonController()
        
        # Wait for MQTT connection
        time.sleep(2)
        
        # Test button functionality
        logger.info("Testing exit button functionality...")
        exit_controller.test_button()
        
        # Keep running
        logger.info("✅ Exit Button Controller is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Exit Button Controller...")
        exit_controller.cleanup()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        if 'exit_controller' in locals():
            exit_controller.cleanup()

if __name__ == "__main__":
    main()
