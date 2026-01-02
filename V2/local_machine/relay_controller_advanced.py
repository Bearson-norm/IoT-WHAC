#!/usr/bin/env python3
"""
Advanced Relay Controller for WHAC Fingerprint System
Controls GPIO pins with complex logic:
- GPIO(1): Relay control (HIGH → wait 5s → LOW)
- GPIO(2): Digital input from door sensor (monitor LOW/HIGH)
- GPIO(3): Output control (HIGH when GPIO(2) LOW, LOW when GPIO(2) HIGH)
- Log GPIO(2) status after 5 seconds GPIO(1) LOW
"""

import paho.mqtt.client as mqtt
import json
import logging
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedRelayController:
    def __init__(self, 
                 relay_pin=None,        # GPIO pin for relay control (default: 23)
                 input_pin=None,        # GPIO pin for digital input (default: 24)
                 output_pin=None,       # GPIO pin for output control (default: 25)
                 mqtt_broker="103.87.67.139", 
                 mqtt_port=1883):
        """
        Initialize advanced relay controller
        
        Args:
            relay_pin: GPIO pin number for relay control (default: 23)
                      GPIO 1, 2, 3 tidak disarankan (GPIO sistem)
                      GPIO 18 sudah digunakan oleh fingerprint_multi_client.py
            input_pin: GPIO pin number for digital input - door sensor (default: 24)
            output_pin: GPIO pin number for output control (default: 25)
            mqtt_broker: MQTT broker IP address
            mqtt_port: MQTT broker port
        """
        # Use environment variables or defaults
        # GPIO 23 untuk relay (GPIO 18 sudah digunakan oleh fingerprint_multi_client.py - relay di fingerprint_multi_client.py sudah dinonaktifkan)
        self.relay_pin = relay_pin or int(os.getenv('RELAY_GPIO_PIN', '23'))
        self.input_pin = input_pin or int(os.getenv('INPUT_GPIO_PIN', '24'))
        self.output_pin = output_pin or int(os.getenv('OUTPUT_GPIO_PIN', '25'))
        # GPIO pins are set above from parameters or environment variables
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.connected = False
        
        # State tracking
        self.gpio_1_active = False
        self.gpio_2_last_state = None
        self.gpio_2_check_timer = None
        
        # MQTT Topics
        self.ACTION_TOPIC = "WHAC/Store001/action"
        self.STATUS_TOPIC = "WHAC/Store001/relay_status"
        self.GPIO_LOG_TOPIC = "WHAC/Store001/gpio_log"
        self.ALARM_TOPIC = "WHAC/Store001/alarm"
        
        # Setup GPIO
        self.setup_gpio()
        
        # Start monitoring thread for GPIO(2) and GPIO(3)
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_gpio_2_and_3, daemon=True)
        self.monitor_thread.start()
        
        # Setup MQTT
        self.setup_mqtt()
    
    def setup_gpio(self):
        """Setup GPIO pins"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # GPIO(1) - Relay control (OUTPUT)
            GPIO.setup(self.relay_pin, GPIO.OUT)
            GPIO.output(self.relay_pin, GPIO.LOW)  # Start with relay OFF
            logger.info(f"✓ GPIO({self.relay_pin}) setup - Relay control (OUTPUT)")
            
            # GPIO(2) - Digital input (INPUT with pull-up)
            GPIO.setup(self.input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.gpio_2_last_state = GPIO.input(self.input_pin)
            logger.info(f"✓ GPIO({self.input_pin}) setup - Digital input (INPUT)")
            logger.info(f"   Initial state: {'HIGH' if self.gpio_2_last_state == GPIO.HIGH else 'LOW'}")
            
            # GPIO(3) - Output control (OUTPUT)
            GPIO.setup(self.output_pin, GPIO.OUT)
            # Set initial state to HIGH (alarm inactive)
            GPIO.output(self.output_pin, GPIO.HIGH)
            logger.info(f"✓ GPIO({self.output_pin}) setup - Output control (OUTPUT)")
            logger.info(f"   Initial state: HIGH (alarm inactive)")
            
        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
    
    def monitor_gpio_2_and_3(self):
        """Monitor GPIO(2) and control GPIO(3) accordingly"""
        logger.info("🔄 Starting GPIO(2) and GPIO(3) monitoring thread...")
        
        while self.monitoring:
            try:
                current_state = GPIO.input(self.input_pin)
                
                # Check if state changed
                if current_state != self.gpio_2_last_state:
                    self.gpio_2_last_state = current_state
                    
                    # Control GPIO(3) based on GPIO(2) state
                    if current_state == GPIO.LOW:
                        # GPIO(2) is LOW → Set GPIO(3) HIGH
                        GPIO.output(self.output_pin, GPIO.HIGH)
                        logger.info(f"🔄 GPIO({self.input_pin}) changed to LOW → GPIO({self.output_pin}) set to HIGH")
                        self.log_gpio_status(self.output_pin, 'HIGH', 'output_control', 
                                           f'GPIO({self.output_pin}) set HIGH because GPIO({self.input_pin}) is LOW')
                    else:
                        # GPIO(2) is HIGH → Set GPIO(3) LOW
                        GPIO.output(self.output_pin, GPIO.LOW)
                        logger.info(f"🔄 GPIO({self.input_pin}) changed to HIGH → GPIO({self.output_pin}) set to LOW")
                        self.log_gpio_status(self.output_pin, 'LOW', 'output_control',
                                           f'GPIO({self.output_pin}) set LOW because GPIO({self.input_pin}) is HIGH')
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                logger.error(f"Error in GPIO monitoring: {e}")
                time.sleep(1)
        
        logger.info("🔄 GPIO monitoring thread stopped")
    
    def check_gpio_2_after_delay(self):
        """Check GPIO(2) status after 5 seconds GPIO(1) LOW"""
        time.sleep(5)  # Wait 5 seconds
        
        if not self.gpio_1_active:
            # GPIO(1) is LOW, check GPIO(2)
            gpio_2_state = GPIO.input(self.input_pin)
            state_str = 'HIGH' if gpio_2_state == GPIO.HIGH else 'LOW'
            
            logger.info(f"📊 GPIO({self.input_pin}) status after 5s GPIO({self.relay_pin}) LOW: {state_str}")
            
            # Log to database
            self.log_gpio_status(self.input_pin, state_str, 'door_sensor',
                                f'GPIO({self.input_pin}) read {state_str} after 5 seconds GPIO({self.relay_pin}) LOW')
    
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
            logger.info(f"Received MQTT message on topic {msg.topic}: {payload}")
            
            # Handle alarm commands
            if msg.topic == self.ALARM_TOPIC:
                command = payload.get('command')
                gpio_pin = payload.get('gpio_pin')
                gpio_state = payload.get('gpio_state')
                user_id = payload.get('user_id')
                username = payload.get('username', 'Unknown')
                
                if command == 'activate' and gpio_pin == 25:
                    self.activate_alarm(user_id, username)
                elif command == 'deactivate' and gpio_pin == 25:
                    self.deactivate_alarm(user_id, username)
                else:
                    logger.warning(f"Unknown alarm command: {command} or invalid GPIO pin: {gpio_pin}")
                return
            
            # Handle relay action commands
            if msg.topic == self.ACTION_TOPIC:
                command = payload.get('command')
                user_id = payload.get('user_id')
                action = payload.get('action')
                device_id = payload.get('device_id')
                
                if command == 'grant':
                    self.grant_access(user_id, action, device_id)
                elif command == 'deny':
                    self.deny_access(user_id, action, device_id)
                else:
                    logger.warning(f"Unknown command: {command}")
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def grant_access(self, user_id, action, device_id):
        """Grant access by activating relay (GPIO 1)"""
        try:
            logger.info(f"Granting access for user {user_id} (device: {device_id})")
            
            # Activate GPIO(1) - Relay control (HIGH)
            self.gpio_1_active = True
            GPIO.output(self.relay_pin, GPIO.HIGH)
            logger.info(f"✓ GPIO({self.relay_pin}) set to HIGH (relay activated)")
            
            # Log GPIO(1) HIGH
            self.log_gpio_status(self.relay_pin, 'HIGH', 'relay_control',
                               f'Relay activated for user {user_id}', user_id, device_id)
            
            # Send status update
            self.send_status_update('granted', user_id, action, device_id)
            
            # Wait 5 seconds
            logger.info("⏳ Waiting 5 seconds...")
            time.sleep(5)
            
            # Deactivate GPIO(1) - Relay control (LOW)
            GPIO.output(self.relay_pin, GPIO.LOW)
            self.gpio_1_active = False
            logger.info(f"✓ GPIO({self.relay_pin}) set to LOW (relay deactivated)")
            
            # Log GPIO(1) LOW
            self.log_gpio_status(self.relay_pin, 'LOW', 'relay_control',
                               f'Relay deactivated for user {user_id}', user_id, device_id)
            
            # Check GPIO(2) after 5 seconds delay (in background thread)
            check_thread = threading.Thread(target=self.check_gpio_2_after_delay, daemon=True)
            check_thread.start()
            
            logger.info(f"✓ Access granted for user {user_id} - Relay activated for 5 seconds")
            
        except Exception as e:
            logger.error(f"Error granting access: {e}")
    
    def deny_access(self, user_id, action, device_id):
        """Deny access by keeping relay off"""
        try:
            logger.info(f"Denying access for user {user_id} (device: {device_id})")
            
            # Ensure GPIO(1) is LOW
            GPIO.output(self.relay_pin, GPIO.LOW)
            self.gpio_1_active = False
            
            # Send status update
            self.send_status_update('denied', user_id, action, device_id)
            
            logger.info(f"✓ Access denied for user {user_id} - Relay remains off")
            
        except Exception as e:
            logger.error(f"Error denying access: {e}")
    
    def activate_alarm(self, user_id, username):
        """Activate alarm by setting GPIO 25 to LOW"""
        try:
            logger.info(f"Activating alarm for user {user_id} ({username})")
            
            # Set GPIO 25 to LOW (alarm active)
            GPIO.output(self.output_pin, GPIO.LOW)
            logger.info(f"✓ GPIO({self.output_pin}) set to LOW (alarm activated)")
            
            # Log GPIO 25 LOW
            self.log_gpio_status(self.output_pin, 'LOW', 'alarm_control',
                               f'Alarm activated by {username}', user_id, None)
            
            logger.info(f"✓ Alarm activated for user {user_id} ({username})")
            
        except Exception as e:
            logger.error(f"Error activating alarm: {e}")
    
    def deactivate_alarm(self, user_id, username):
        """Deactivate alarm by setting GPIO 25 to HIGH"""
        try:
            logger.info(f"Deactivating alarm for user {user_id} ({username})")
            
            # Set GPIO 25 to HIGH (alarm inactive)
            GPIO.output(self.output_pin, GPIO.HIGH)
            logger.info(f"✓ GPIO({self.output_pin}) set to HIGH (alarm deactivated)")
            
            # Log GPIO 25 HIGH
            self.log_gpio_status(self.output_pin, 'HIGH', 'alarm_control',
                               f'Alarm deactivated by {username}', user_id, None)
            
            logger.info(f"✓ Alarm deactivated for user {user_id} ({username})")
            
        except Exception as e:
            logger.error(f"Error deactivating alarm: {e}")
    
    def log_gpio_status(self, gpio_pin, gpio_state, event_type, description, user_id=None, device_id=None):
        """Log GPIO status via MQTT to web-ui (which saves to database)"""
        try:
            if not self.connected:
                logger.warning("MQTT not connected, cannot send GPIO log")
                return False
            
            # Prepare payload for GPIO log
            payload = {
                'gpio_pin': gpio_pin,
                'gpio_state': gpio_state,
                'event_type': event_type,
                'user_id': user_id,
                'device_id': device_id,
                'description': description,
                'timestamp': datetime.now().isoformat(),
                'source': 'relay_controller'
            }
            
            # Publish to GPIO log topic
            result = self.mqtt_client.publish(self.GPIO_LOG_TOPIC, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ GPIO log sent via MQTT: GPIO({gpio_pin}) = {gpio_state} ({event_type})")
                return True
            else:
                logger.error(f"✗ Failed to send GPIO log via MQTT (rc: {result.rc})")
                return False
            
        except Exception as e:
            logger.error(f"Error sending GPIO log via MQTT: {e}")
            return False
    
    def send_status_update(self, status, user_id, action, device_id):
        """Send relay status update via MQTT"""
        try:
            if not self.connected:
                logger.error("MQTT not connected, cannot send status update")
                return False
            
            payload = {
                'status': status,
                'user_id': user_id,
                'action': action,
                'device_id': device_id,
                'timestamp': datetime.now().isoformat(),
                'relay_pin': self.relay_pin,
                'input_pin': self.input_pin,
                'output_pin': self.output_pin
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
    
    def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up advanced relay controller...")
            
            # Stop monitoring
            self.monitoring = False
            if self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
            
            # Turn off all GPIO outputs
            GPIO.output(self.relay_pin, GPIO.LOW)
            GPIO.output(self.output_pin, GPIO.LOW)
            
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
    """Main function for testing advanced relay controller"""
    relay = AdvancedRelayController()
    
    try:
        logger.info("=" * 60)
        logger.info("WHAC Advanced Relay Controller - Running!")
        logger.info("=" * 60)
        logger.info(f"GPIO({relay.relay_pin}): Relay control (OUTPUT)")
        logger.info(f"GPIO({relay.input_pin}): Digital input (INPUT)")
        logger.info(f"GPIO({relay.output_pin}): Output control (OUTPUT)")
        logger.info(f"MQTT Broker: {relay.mqtt_broker}:{relay.mqtt_port}")
        logger.info(f"Action Topic: {relay.ACTION_TOPIC}")
        logger.info("=" * 60)
        logger.info("✓ Listening for relay control commands...")
        logger.info("✓ GPIO monitoring active")
        logger.info("=" * 60)
        
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



