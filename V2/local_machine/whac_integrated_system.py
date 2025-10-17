#!/usr/bin/env python3
"""
WHAC Integrated System
Combines all UAT requirements into a single integrated system:
1. Exit warehouse flow with GPIO pushbutton
2. MP3 notification for violations
3. Interrupt notification on operator dashboard
4. MP3 template system for user commands
"""

import logging
import time
import threading
import signal
import sys
from datetime import datetime
from config import *

# Import all system components
from fingerprint_simple_client import SimpleFingerprintClient
from exit_button_controller import ExitButtonController
from mp3_notification_system import MP3NotificationSystem

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whac_integrated_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WHACIntegratedSystem:
    def __init__(self):
        """Initialize the integrated WHAC system"""
        self.running = True
        self.components = {}
        
        logger.info("🚀 Initializing WHAC Integrated System...")
        
        # Initialize all system components
        self.initialize_components()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def initialize_components(self):
        """Initialize all system components"""
        try:
            # 1. Initialize fingerprint client (main component)
            logger.info("🔐 Initializing fingerprint client...")
            self.components['fingerprint'] = SimpleFingerprintClient()
            logger.info("✅ Fingerprint client initialized")
            
            # 2. Initialize exit button controller
            logger.info("🔘 Initializing exit button controller...")
            self.components['exit_button'] = ExitButtonController()
            logger.info("✅ Exit button controller initialized")
            
            # 3. Initialize MP3 notification system
            logger.info("🔊 Initializing MP3 notification system...")
            self.components['mp3_system'] = MP3NotificationSystem()
            logger.info("✅ MP3 notification system initialized")
            
            logger.info("🎉 All system components initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            raise
    
    def start_system(self):
        """Start the integrated system"""
        try:
            logger.info("🚀 Starting WHAC Integrated System...")
            
            # Start fingerprint scanning in a separate thread
            fingerprint_thread = threading.Thread(
                target=self.run_fingerprint_scanning,
                daemon=True,
                name="FingerprintScanner"
            )
            fingerprint_thread.start()
            
            # Start system monitoring
            monitor_thread = threading.Thread(
                target=self.system_monitor,
                daemon=True,
                name="SystemMonitor"
            )
            monitor_thread.start()
            
            logger.info("✅ WHAC Integrated System started successfully!")
            logger.info("📋 System Status:")
            logger.info(f"   - Fingerprint Scanner: {'✅ Active' if self.components.get('fingerprint') else '❌ Inactive'}")
            logger.info(f"   - Exit Button: {'✅ Active' if self.components.get('exit_button') else '❌ Inactive'}")
            logger.info(f"   - MP3 Notifications: {'✅ Active' if self.components.get('mp3_system') else '❌ Inactive'}")
            logger.info("🎯 System is ready for UAT testing!")
            
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
                logger.error("❌ Fingerprint client not available")
                return
            
            logger.info("🔍 Starting fingerprint scanning loop...")
            
            while self.running:
                try:
                    # Run fingerprint scan
                    fingerprint_client.scan_fingerprint_standby()
                    time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                    
                except Exception as e:
                    logger.error(f"❌ Error in fingerprint scanning: {e}")
                    time.sleep(1)
                    
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
                    
                    time.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    logger.error(f"❌ Error in system monitor: {e}")
                    time.sleep(30)
                    
        except Exception as e:
            logger.error(f"❌ Fatal error in system monitor thread: {e}")
    
    def check_component_health(self):
        """Check health of all system components"""
        try:
            # Check fingerprint client
            if self.components.get('fingerprint'):
                if not hasattr(self.components['fingerprint'], 'connected') or not self.components['fingerprint'].connected:
                    logger.warning("⚠️  Fingerprint client MQTT connection lost")
            
            # Check exit button controller
            if self.components.get('exit_button'):
                if not hasattr(self.components['exit_button'], 'connected') or not self.components['exit_button'].connected:
                    logger.warning("⚠️  Exit button controller MQTT connection lost")
            
            # Check MP3 notification system
            if self.components.get('mp3_system'):
                if not hasattr(self.components['mp3_system'], 'connected') or not self.components['mp3_system'].connected:
                    logger.warning("⚠️  MP3 notification system MQTT connection lost")
                    
        except Exception as e:
            logger.error(f"❌ Error checking component health: {e}")
    
    def log_system_status(self):
        """Log current system status"""
        try:
            logger.info("📊 System Status Report:")
            logger.info(f"   - Timestamp: {datetime.now().isoformat()}")
            logger.info(f"   - Store ID: {STORE_ID}")
            logger.info(f"   - MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
            logger.info(f"   - Components Active: {len([c for c in self.components.values() if c])}")
            logger.info(f"   - System Uptime: {time.time() - self.start_time:.0f} seconds")
            
        except Exception as e:
            logger.error(f"❌ Error logging system status: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the system"""
        try:
            logger.info("🛑 Shutting down WHAC Integrated System...")
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
            
            logger.info("✅ WHAC Integrated System shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        finally:
            sys.exit(0)
    
    def test_system(self):
        """Test all system components"""
        try:
            logger.info("🧪 Testing WHAC Integrated System...")
            
            # Test fingerprint client
            if self.components.get('fingerprint'):
                logger.info("🔐 Testing fingerprint client...")
                # Add fingerprint test here if needed
            
            # Test exit button
            if self.components.get('exit_button'):
                logger.info("🔘 Testing exit button...")
                self.components['exit_button'].test_button()
            
            # Test MP3 system
            if self.components.get('mp3_system'):
                logger.info("🔊 Testing MP3 notification system...")
                self.components['mp3_system'].test_audio_system()
            
            logger.info("✅ System test completed")
            
        except Exception as e:
            logger.error(f"❌ Error during system test: {e}")

def main():
    """Main function"""
    try:
        # Create and start the integrated system
        system = WHACIntegratedSystem()
        system.start_time = time.time()
        
        # Run system test
        system.test_system()
        
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

