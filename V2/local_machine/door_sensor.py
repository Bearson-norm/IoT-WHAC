#!/usr/bin/env python3
"""
Door Sensor Monitor for WHAC Fingerprint System
Detects door open/closed status using GPIO input from magnetic door sensor
Supports NC (Normally Closed), COM (Common), and NO (Normally Open) configurations
"""

import paho.mqtt.client as mqtt
import json
import logging
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
import os
import sys
from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, STORE_ID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('door_sensor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DoorSensor:
    def __init__(self, door_sensor_pin=24, mqtt_broker=None, mqtt_port=None):
        """
        Initialize door sensor monitor
        
        Args:
            door_sensor_pin: GPIO pin number for door sensor input (default: 24)
                            This pin reads 3.3V when door is closed (if using NC configuration)
            mqtt_broker: MQTT broker IP address (default: from config)
            mqtt_port: MQTT broker port (default: from config)
        """
        self.door_sensor_pin = door_sensor_pin
        self.mqtt_broker = mqtt_broker or MQTT_BROKER
        self.mqtt_port = mqtt_port or MQTT_PORT
        self.mqtt_client = None
        self.connected = False
        self.running = True
        self.last_door_state = None
        self.debounce_time = 0.1  # 100ms debounce to prevent false triggers
        
        # MQTT Topics
        self.DOOR_STATUS_TOPIC = f"WHAC/{STORE_ID}/door_status"
        
        # Door sensor configuration
        # NC (Normally Closed): Door closed = HIGH (3.3V), Door open = LOW (0V)
        # NO (Normally Open): Door closed = LOW (0V), Door open = HIGH (3.3V)
        # Default: NC configuration (most common for magnetic door sensors)
        self.sensor_type = os.getenv("DOOR_SENSOR_TYPE", "NC").upper()  # NC or NO
        
        # Setup GPIO
        self.setup_gpio()
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Start monitoring thread
        self.monitor_thread = None
        self.start_monitoring()
    
    def setup_gpio(self):
        """Setup GPIO for door sensor input"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Configure pin as input with pull-down resistor
            # This ensures stable reading when sensor is disconnected
            GPIO.setup(self.door_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            
            logger.info(f"✓ GPIO setup complete - Door sensor on pin {self.door_sensor_pin}")
            logger.info(f"✓ Sensor type: {self.sensor_type} (NC=Normally Closed, NO=Normally Open)")
            
            # Read initial state
            initial_state = self.read_door_state()
            logger.info(f"✓ Initial door state: {'CLOSED' if initial_state else 'OPEN'}")
            
        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
            raise
    
    def read_door_state(self):
        """
        Read door state from GPIO pin
        
        Returns:
            bool: True if door is CLOSED, False if door is OPEN
        """
        try:
            pin_value = GPIO.input(self.door_sensor_pin)
            
            if self.sensor_type == "NC":
                # NC (Normally Closed): HIGH = door closed, LOW = door open
                return pin_value == GPIO.HIGH
            else:
                # NO (Normally Open): LOW = door closed, HIGH = door open
                return pin_value == GPIO.LOW
                
        except Exception as e:
            logger.error(f"Error reading door state: {e}")
            return None
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            import time
            unique_client_id = f"door_sensor_{int(time.time())}"
            self.mqtt_client = mqtt.Client(client_id=unique_client_id)
            
            # Set authentication if provided
            if MQTT_USERNAME and MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("✓ MQTT client connected for door status updates")
            else:
                logger.error("✗ Failed to connect to MQTT broker within timeout")
                
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✓ MQTT client connected")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning(f"MQTT client disconnected (code: {rc})")
    
    def send_door_status(self, is_closed, timestamp=None):
        """
        Send door status update via MQTT
        
        Args:
            is_closed: bool - True if door is closed, False if open
            timestamp: str - ISO format timestamp (optional)
        """
        try:
            if not self.connected:
                logger.warning("MQTT not connected, cannot send door status")
                return False
            
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            payload = {
                'store_id': STORE_ID,
                'door_status': 'closed' if is_closed else 'open',
                'is_closed': is_closed,
                'timestamp': timestamp,
                'sensor_pin': self.door_sensor_pin,
                'sensor_type': self.sensor_type
            }
            
            result = self.mqtt_client.publish(
                self.DOOR_STATUS_TOPIC,
                json.dumps(payload),
                qos=1
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                status_text = "CLOSED" if is_closed else "OPEN"
                logger.info(f"✓ Door status sent: {status_text}")
                return True
            else:
                logger.error(f"✗ Failed to send door status (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending door status: {e}")
            return False
    
    def monitor_door(self):
        """Monitor door state continuously in background thread"""
        logger.info("🚪 Starting door monitoring thread...")
        
        last_state = None
        last_change_time = time.time()
        
        while self.running:
            try:
                current_state = self.read_door_state()
                
                # Check if state has changed
                if current_state != last_state:
                    # Debounce: wait a bit to confirm the change
                    time.sleep(self.debounce_time)
                    confirmed_state = self.read_door_state()
                    
                    if confirmed_state == current_state:
                        # State change confirmed
                        state_text = "CLOSED" if current_state else "OPEN"
                        logger.info(f"🚪 Door state changed: {state_text}")
                        
                        # Send status update
                        self.send_door_status(current_state)
                        
                        last_state = current_state
                        last_change_time = time.time()
                    else:
                        # False trigger, ignore
                        logger.debug("⚠️  False trigger detected, ignoring...")
                
                # Send periodic status update every 30 seconds (heartbeat)
                if time.time() - last_change_time > 30:
                    if current_state is not None:
                        self.send_door_status(current_state)
                        last_change_time = time.time()
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in door monitoring: {e}")
                time.sleep(1)
        
        logger.info("🚪 Door monitoring thread stopped")
    
    def start_monitoring(self):
        """Start door monitoring in background thread"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self.monitor_door, daemon=True)
            self.monitor_thread.start()
            logger.info("✓ Door monitoring thread started")
    
    def get_current_status(self):
        """Get current door status"""
        is_closed = self.read_door_state()
        if is_closed is None:
            return None
        return {
            'is_closed': is_closed,
            'status': 'closed' if is_closed else 'open',
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up door sensor...")
            self.running = False
            
            # Wait for monitoring thread to finish
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
            
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
    """Main function for door sensor monitor"""
    # Get door sensor pin from environment or use default
    door_pin = int(os.getenv("DOOR_SENSOR_PIN", "24"))
    
    door_sensor = DoorSensor(door_sensor_pin=door_pin)
    
    try:
        logger.info("=" * 60)
        logger.info("WHAC Door Sensor Monitor - Running!")
        logger.info("=" * 60)
        logger.info(f"Door Sensor Pin: {door_sensor.door_sensor_pin}")
        logger.info(f"Sensor Type: {door_sensor.sensor_type}")
        logger.info(f"MQTT Broker: {door_sensor.mqtt_broker}:{door_sensor.mqtt_port}")
        logger.info(f"Door Status Topic: {door_sensor.DOOR_STATUS_TOPIC}")
        logger.info("=" * 60)
        logger.info("✓ Monitoring door status...")
        logger.info("✓ Publishing status updates via MQTT")
        logger.info("=" * 60)
        
        # Send initial status
        initial_status = door_sensor.get_current_status()
        if initial_status:
            door_sensor.send_door_status(initial_status['is_closed'])
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Door sensor monitor stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        door_sensor.cleanup()

if __name__ == "__main__":
    main()





