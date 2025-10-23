#!/usr/bin/env python3
"""
GPIO Manager for WHAC System
Centralized GPIO management with improved error handling and fallback mechanisms
"""

import RPi.GPIO as GPIO
import logging
import threading
import time
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GPIOManager:
    """Centralized GPIO management with improved error handling"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single GPIO instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GPIOManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize GPIO manager"""
        if hasattr(self, 'initialized'):
            return
            
        self.initialized = True
        self.gpio_initialized = False
        self.pins = {}  # Store pin configurations
        self.callbacks = {}  # Store callback functions
        self.polling_threads = {}  # Store polling threads
        self.running = True
        
        # Initialize GPIO
        self.setup_gpio()
        
        logger.info("✅ GPIO Manager initialized")
    
    def setup_gpio(self):
        """Setup GPIO with improved error handling"""
        try:
            if self.gpio_initialized:
                return
                
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            self.gpio_initialized = True
            logger.info("✓ GPIO setup complete")
            
        except Exception as e:
            logger.error(f"GPIO setup error: {e}")
            self.gpio_initialized = False
    
    def setup_input_pin(self, pin, pull_up_down=GPIO.PUD_UP, callback=None, debounce_time=300):
        """
        Setup input pin with improved error handling
        
        Args:
            pin: GPIO pin number
            pull_up_down: Pull up/down configuration
            callback: Callback function for button press
            debounce_time: Debounce time in milliseconds
        """
        try:
            if not self.gpio_initialized:
                logger.error("GPIO not initialized")
                return False
            
            # Configure pin as input
            GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
            self.pins[pin] = {
                'type': 'input',
                'pull_up_down': pull_up_down,
                'callback': callback,
                'debounce_time': debounce_time,
                'last_press_time': 0
            }
            
            # Try edge detection first
            if callback:
                try:
                    GPIO.add_event_detect(
                        pin, 
                        GPIO.FALLING, 
                        callback=self._button_callback_wrapper(pin), 
                        bouncetime=debounce_time
                    )
                    logger.info(f"✓ Edge detection setup for pin {pin}")
                    return True
                    
                except Exception as edge_error:
                    logger.warning(f"⚠️  Edge detection failed for pin {pin}: {edge_error}")
                    logger.info(f"🔄 Using polling mode for pin {pin}")
                    
                    # Fallback to polling mode
                    self._start_polling(pin)
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up input pin {pin}: {e}")
            return False
    
    def _button_callback_wrapper(self, pin):
        """Wrapper for button callback with debouncing"""
        def callback(channel):
            current_time = time.time()
            pin_config = self.pins.get(pin)
            
            if not pin_config:
                return
            
            # Debounce check
            if current_time - pin_config['last_press_time'] < (pin_config['debounce_time'] / 1000.0):
                return
            
            pin_config['last_press_time'] = current_time
            
            # Call the actual callback
            if pin_config['callback']:
                try:
                    pin_config['callback'](channel)
                except Exception as e:
                    logger.error(f"Error in button callback for pin {pin}: {e}")
        
        return callback
    
    def _start_polling(self, pin):
        """Start polling thread for pin"""
        try:
            if pin in self.polling_threads:
                return
            
            def poll_pin():
                pin_config = self.pins.get(pin)
                if not pin_config:
                    return
                
                last_state = GPIO.HIGH
                
                while self.running and pin in self.pins:
                    try:
                        current_state = GPIO.input(pin)
                        
                        # Detect falling edge (button press)
                        if last_state == GPIO.HIGH and current_state == GPIO.LOW:
                            self._button_callback_wrapper(pin)(pin)
                        
                        last_state = current_state
                        time.sleep(0.01)  # 10ms polling interval
                        
                    except Exception as e:
                        logger.error(f"Error polling pin {pin}: {e}")
                        time.sleep(0.1)
            
            thread = threading.Thread(target=poll_pin, daemon=True, name=f"GPIO_Poll_{pin}")
            thread.start()
            self.polling_threads[pin] = thread
            
            logger.info(f"✓ Polling started for pin {pin}")
            
        except Exception as e:
            logger.error(f"Error starting polling for pin {pin}: {e}")
    
    def setup_output_pin(self, pin, initial_value=GPIO.LOW):
        """
        Setup output pin
        
        Args:
            pin: GPIO pin number
            initial_value: Initial output value
        """
        try:
            if not self.gpio_initialized:
                logger.error("GPIO not initialized")
                return False
            
            GPIO.setup(pin, GPIO.OUT, initial=initial_value)
            self.pins[pin] = {
                'type': 'output',
                'value': initial_value
            }
            
            logger.info(f"✓ Output pin {pin} setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up output pin {pin}: {e}")
            return False
    
    def write_pin(self, pin, value):
        """Write value to output pin"""
        try:
            if pin not in self.pins or self.pins[pin]['type'] != 'output':
                logger.error(f"Pin {pin} not configured as output")
                return False
            
            GPIO.output(pin, value)
            self.pins[pin]['value'] = value
            return True
            
        except Exception as e:
            logger.error(f"Error writing to pin {pin}: {e}")
            return False
    
    def read_pin(self, pin):
        """Read value from input pin"""
        try:
            if pin not in self.pins or self.pins[pin]['type'] != 'input':
                logger.error(f"Pin {pin} not configured as input")
                return None
            
            return GPIO.input(pin)
            
        except Exception as e:
            logger.error(f"Error reading pin {pin}: {e}")
            return None
    
    def remove_pin(self, pin):
        """Remove pin configuration"""
        try:
            if pin in self.pins:
                # Stop polling if active
                if pin in self.polling_threads:
                    del self.polling_threads[pin]
                
                # Remove event detection
                try:
                    GPIO.remove_event_detect(pin)
                except:
                    pass
                
                del self.pins[pin]
                logger.info(f"✓ Pin {pin} configuration removed")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing pin {pin}: {e}")
            return False
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            logger.info("Cleaning up GPIO Manager...")
            self.running = False
            
            # Stop all polling threads
            for pin in list(self.polling_threads.keys()):
                self.remove_pin(pin)
            
            # Cleanup GPIO
            if self.gpio_initialized:
                GPIO.cleanup()
                self.gpio_initialized = False
                logger.info("✓ GPIO cleaned up")
            
            logger.info("✅ GPIO Manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up GPIO Manager: {e}")

# Global instance
gpio_manager = GPIOManager()

def get_gpio_manager():
    """Get the global GPIO manager instance"""
    return gpio_manager



