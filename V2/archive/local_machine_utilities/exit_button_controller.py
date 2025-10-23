#!/usr/bin/env python3
"""
Exit Button Controller for WHAC Fingerprint System
Handles exit warehouse flow with GPIO pushbutton trigger
"""

import json
import logging
import time
import threading
from datetime import datetime
from config import *
from mqtt_manager import get_mqtt_manager
from gpio_manager import get_gpio_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExitButtonController:
    def __init__(self, exit_button_pin=24):
        """
        Initialize exit button controller
        
        Args:
            exit_button_pin: GPIO pin number for exit button (default: 24)
        """
        self.exit_button_pin = exit_button_pin
        self.mqtt_manager = get_mqtt_manager()
        self.gpio_manager = get_gpio_manager()
        self.running = True
        self.button_pressed = False
        
        # MQTT Topics
        self.EXIT_TOPIC = f"WHAC/{STORE_ID}/exit"
        self.STATUS_TOPIC = f"WHAC/{STORE_ID}/exit_status"
        
        # Setup GPIO
        self.setup_gpio()
        
        # Setup MQTT subscriptions
        self.setup_mqtt()
    
    def setup_gpio(self):
        """Setup GPIO for exit button using GPIO manager"""
        try:
            # Setup input pin with callback
            import RPi.GPIO as GPIO
            success = self.gpio_manager.setup_input_pin(
                pin=self.exit_button_pin,
                pull_up_down=GPIO.PUD_UP,
                callback=self.button_callback,
                debounce_time=300
            )
            
            if success:
                logger.info(f"✓ Exit button setup complete - Button on pin {self.exit_button_pin}")
            else:
                logger.error(f"❌ Failed to setup exit button on pin {self.exit_button_pin}")
            
        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
    
    def setup_mqtt(self):
        """Setup MQTT subscriptions"""
        try:
            # Subscribe to status topic for acknowledgments
            self.mqtt_manager.subscribe(self.STATUS_TOPIC, self.on_mqtt_message)
            logger.info("✓ MQTT subscriptions setup complete for exit button")
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_message(self, topic, payload):
        """Handle incoming MQTT messages"""
        try:
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
        """Button press callback"""
        self.button_pressed = True
        logger.info("🔘 Exit button pressed!")
        self.handle_exit_request()
    
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
            if self.mqtt_manager.is_connected():
                self.mqtt_manager.publish(self.EXIT_TOPIC, exit_data)
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
            
            if self.mqtt_manager.is_connected():
                self.mqtt_manager.publish(self.STATUS_TOPIC, status_data)
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
            
            # Unsubscribe from MQTT topics
            if hasattr(self, 'mqtt_manager'):
                self.mqtt_manager.unsubscribe(self.STATUS_TOPIC)
                logger.info("Exit button MQTT subscriptions removed")
            
            # Remove GPIO pin
            if hasattr(self, 'gpio_manager'):
                self.gpio_manager.remove_pin(self.exit_button_pin)
                logger.info("Exit button GPIO pin removed")
            
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
