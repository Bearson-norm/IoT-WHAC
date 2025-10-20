#!/usr/bin/env python3
"""
WHAC Simple System - Simplified version for debugging
Handles common Raspberry Pi issues gracefully
"""

import logging
import time
import threading
import signal
import sys
import os
from datetime import datetime
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whac_simple_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WHACSimpleSystem:
    def __init__(self):
        """Initialize the simplified WHAC system"""
        self.running = True
        self.components = {}
        
        logger.info("🚀 Initializing WHAC Simple System...")
        
        # Initialize components with error handling
        self.initialize_components()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def initialize_components(self):
        """Initialize system components with error handling"""
        try:
            # 1. Initialize MP3 notification system (most important for UAT)
            logger.info("🔊 Initializing MP3 notification system...")
            try:
                from mp3_notification_system import MP3NotificationSystem
                self.components['mp3_system'] = MP3NotificationSystem()
                logger.info("✅ MP3 notification system initialized")
            except Exception as e:
                logger.warning(f"⚠️  MP3 system initialization failed: {e}")
                self.components['mp3_system'] = None
            
            # 2. Initialize exit button controller
            logger.info("🔘 Initializing exit button controller...")
            try:
                from exit_button_controller import ExitButtonController
                self.components['exit_button'] = ExitButtonController()
                logger.info("✅ Exit button controller initialized")
            except Exception as e:
                logger.warning(f"⚠️  Exit button controller initialization failed: {e}")
                self.components['exit_button'] = None
            
            # 3. Initialize fingerprint client (optional for testing)
            logger.info("🔐 Initializing fingerprint client...")
            try:
                from fingerprint_simple_client import SimpleFingerprintClient
                self.components['fingerprint'] = SimpleFingerprintClient()
                logger.info("✅ Fingerprint client initialized")
            except Exception as e:
                logger.warning(f"⚠️  Fingerprint client initialization failed: {e}")
                self.components['fingerprint'] = None
            
            logger.info("🎉 Component initialization complete!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
    
    def start_system(self):
        """Start the simplified system"""
        try:
            logger.info("🚀 Starting WHAC Simple System...")
            
            # Start system monitoring
            monitor_thread = threading.Thread(
                target=self.system_monitor,
                daemon=True,
                name="SystemMonitor"
            )
            monitor_thread.start()
            
            # Start fingerprint scanning if available
            if self.components.get('fingerprint'):
                fingerprint_thread = threading.Thread(
                    target=self.run_fingerprint_scanning,
                    daemon=True,
                    name="FingerprintScanner"
                )
                fingerprint_thread.start()
            
            logger.info("✅ WHAC Simple System started successfully!")
            self.log_system_status()
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error starting system: {e}")
            self.shutdown()
    
    def run_fingerprint_scanning(self):
        """Run fingerprint scanning loop"""
        try:
            fingerprint_client = self.components.get('fingerprint')
            if not fingerprint_client:
                logger.info("ℹ️  Fingerprint client not available, skipping scanning")
                return
            
            logger.info("🔍 Starting fingerprint scanning loop...")
            
            while self.running:
                try:
                    # Run fingerprint scan with error handling
                    if hasattr(fingerprint_client, 'scan_fingerprint_standby'):
                        fingerprint_client.scan_fingerprint_standby()
                    time.sleep(1)  # Longer delay to reduce errors
                    
                except Exception as e:
                    logger.debug(f"Fingerprint scan error: {e}")
                    time.sleep(5)  # Wait longer on error
                    
        except Exception as e:
            logger.error(f"❌ Fatal error in fingerprint scanning thread: {e}")
    
    def system_monitor(self):
        """Monitor system health and status"""
        try:
            logger.info("📊 Starting system monitor...")
            
            while self.running:
                try:
                    # Check component health
                    self.check_component_health()
                    
                    # Log system status every 5 minutes
                    if int(time.time()) % 300 == 0:
                        self.log_system_status()
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"❌ Error in system monitor: {e}")
                    time.sleep(60)
                    
        except Exception as e:
            logger.error(f"❌ Fatal error in system monitor thread: {e}")
    
    def check_component_health(self):
        """Check health of all system components"""
        try:
            # Check MP3 system
            if self.components.get('mp3_system'):
                if not hasattr(self.components['mp3_system'], 'connected') or not self.components['mp3_system'].connected:
                    logger.debug("MP3 notification system MQTT connection lost")
            
            # Check exit button controller
            if self.components.get('exit_button'):
                if not hasattr(self.components['exit_button'], 'connected') or not self.components['exit_button'].connected:
                    logger.debug("Exit button controller MQTT connection lost")
            
            # Check fingerprint client
            if self.components.get('fingerprint'):
                if not hasattr(self.components['fingerprint'], 'connected') or not self.components['fingerprint'].connected:
                    logger.debug("Fingerprint client MQTT connection lost")
                    
        except Exception as e:
            logger.error(f"❌ Error checking component health: {e}")
    
    def log_system_status(self):
        """Log current system status"""
        try:
            logger.info("📊 System Status Report:")
            logger.info(f"   - Timestamp: {datetime.now().isoformat()}")
            logger.info(f"   - Store ID: {STORE_ID}")
            logger.info(f"   - MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
            
            active_components = 0
            for name, component in self.components.items():
                if component:
                    active_components += 1
                    logger.info(f"   - {name}: ✅ Active")
                else:
                    logger.info(f"   - {name}: ❌ Inactive")
            
            logger.info(f"   - Components Active: {active_components}/{len(self.components)}")
            
        except Exception as e:
            logger.error(f"❌ Error logging system status: {e}")
    
    def test_components(self):
        """Test all available components"""
        try:
            logger.info("🧪 Testing WHAC Simple System components...")
            
            # Test MP3 system
            if self.components.get('mp3_system'):
                logger.info("🔊 Testing MP3 notification system...")
                try:
                    self.components['mp3_system'].test_audio_system()
                except Exception as e:
                    logger.warning(f"⚠️  MP3 system test failed: {e}")
            
            # Test exit button
            if self.components.get('exit_button'):
                logger.info("🔘 Testing exit button...")
                try:
                    self.components['exit_button'].test_button()
                except Exception as e:
                    logger.warning(f"⚠️  Exit button test failed: {e}")
            
            logger.info("✅ Component testing completed")
            
        except Exception as e:
            logger.error(f"❌ Error during component testing: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the system"""
        try:
            logger.info("🛑 Shutting down WHAC Simple System...")
            self.running = False
            
            # Cleanup all components
            for name, component in self.components.items():
                if component and hasattr(component, 'cleanup'):
                    try:
                        logger.info(f"🧹 Cleaning up {name}...")
                        component.cleanup()
                        logger.info(f"✅ {name} cleaned up successfully")
                    except Exception as e:
                        logger.error(f"❌ Error cleaning up {name}: {e}")
            
            logger.info("✅ WHAC Simple System shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        finally:
            sys.exit(0)

def main():
    """Main function"""
    try:
        # Create and start the simplified system
        system = WHACSimpleSystem()
        system.start_time = time.time()
        
        # Run component tests
        system.test_components()
        
        # Start the main system
        system.start_system()
        
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
    finally:
        if 'system' in locals():
            system.shutdown()

if __name__ == "__main__":
    main()



