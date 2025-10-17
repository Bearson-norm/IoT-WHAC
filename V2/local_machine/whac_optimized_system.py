#!/usr/bin/env python3
"""
WHAC Optimized System - Resource-efficient version
Minimizes network, I/O, and CPU usage
"""

import logging
import time
import threading
import signal
import sys
import os
from datetime import datetime
from config import *

# Configure logging with reduced verbosity
logging.basicConfig(
    level=logging.WARNING,  # Reduced from INFO to WARNING
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whac_optimized_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WHACOptimizedSystem:
    def __init__(self):
        """Initialize the optimized WHAC system"""
        self.running = True
        self.components = {}
        self.start_time = time.time()
        
        logger.info("🚀 Initializing WHAC Optimized System...")
        
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
        """Start the optimized system"""
        try:
            logger.info("🚀 Starting WHAC Optimized System...")
            
            # Start system monitoring with reduced frequency
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
            
            logger.info("✅ WHAC Optimized System started successfully!")
            self.log_system_status()
            
            # Keep main thread alive
            while self.running:
                time.sleep(5)  # Reduced from 1 second to 5 seconds
                
        except Exception as e:
            logger.error(f"❌ Error starting system: {e}")
            self.shutdown()
    
    def run_fingerprint_scanning(self):
        """Run fingerprint scanning loop with reduced frequency"""
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
                    time.sleep(2)  # Increased from 1 second to 2 seconds
                    
                except Exception as e:
                    logger.debug(f"Fingerprint scan error: {e}")
                    time.sleep(10)  # Increased from 5 seconds to 10 seconds
                    
        except Exception as e:
            logger.error(f"❌ Fatal error in fingerprint scanning thread: {e}")
    
    def system_monitor(self):
        """Monitor system health with reduced frequency"""
        try:
            logger.info("📊 Starting system monitor...")
            
            while self.running:
                try:
                    # Check component health
                    self.check_component_health()
                    
                    # Log system status every 10 minutes (reduced from 5 minutes)
                    if int(time.time()) % 600 == 0:
                        self.log_system_status()
                    
                    time.sleep(60)  # Increased from 30 seconds to 60 seconds
                    
                except Exception as e:
                    logger.error(f"❌ Error in system monitor: {e}")
                    time.sleep(120)  # Increased from 60 seconds to 120 seconds
                    
        except Exception as e:
            logger.error(f"❌ Fatal error in system monitor thread: {e}")
    
    def check_component_health(self):
        """Check health of all system components with reduced logging"""
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
        """Log current system status with reduced frequency"""
        try:
            uptime = time.time() - self.start_time
            logger.info(f"📊 System Status - Uptime: {uptime:.0f}s")
            
            active_components = 0
            for name, component in self.components.items():
                if component:
                    active_components += 1
            
            logger.info(f"📊 Active Components: {active_components}/{len(self.components)}")
            
        except Exception as e:
            logger.error(f"❌ Error logging system status: {e}")
    
    def test_components(self):
        """Test all available components with reduced output"""
        try:
            logger.info("🧪 Testing WHAC Optimized System components...")
            
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
            logger.info("🛑 Shutting down WHAC Optimized System...")
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
            
            logger.info("✅ WHAC Optimized System shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        finally:
            sys.exit(0)

def main():
    """Main function"""
    try:
        # Create and start the optimized system
        system = WHACOptimizedSystem()
        
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

