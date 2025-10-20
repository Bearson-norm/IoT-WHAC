#!/usr/bin/env python3
"""
Test script for improved WHAC Integrated System
Tests the fixed system with centralized MQTT and GPIO management
"""

import logging
import time
import signal
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mqtt_manager():
    """Test MQTT Manager functionality"""
    try:
        logger.info("🧪 Testing MQTT Manager...")
        
        from mqtt_manager import get_mqtt_manager
        
        mqtt_manager = get_mqtt_manager()
        
        # Wait for connection
        logger.info("⏳ Waiting for MQTT connection...")
        for i in range(10):
            if mqtt_manager.is_connected():
                logger.info("✅ MQTT Manager connected successfully")
                break
            time.sleep(1)
        else:
            logger.error("❌ MQTT Manager connection timeout")
            return False
        
        # Test publish
        test_data = {
            "test": "mqtt_manager",
            "timestamp": datetime.now().isoformat(),
            "status": "testing"
        }
        
        success = mqtt_manager.publish(f"WHAC/{STORE_ID}/test", test_data)
        if success:
            logger.info("✅ MQTT publish test successful")
        else:
            logger.error("❌ MQTT publish test failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MQTT Manager test failed: {e}")
        return False

def test_gpio_manager():
    """Test GPIO Manager functionality"""
    try:
        logger.info("🧪 Testing GPIO Manager...")
        
        from gpio_manager import get_gpio_manager
        
        gpio_manager = get_gpio_manager()
        
        # Test output pin
        test_pin = 18  # Relay pin
        success = gpio_manager.setup_output_pin(test_pin, GPIO.LOW)
        if success:
            logger.info("✅ GPIO output pin setup successful")
            
            # Test write
            gpio_manager.write_pin(test_pin, GPIO.HIGH)
            time.sleep(0.5)
            gpio_manager.write_pin(test_pin, GPIO.LOW)
            logger.info("✅ GPIO write test successful")
            
            # Cleanup
            gpio_manager.remove_pin(test_pin)
        else:
            logger.error("❌ GPIO output pin setup failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ GPIO Manager test failed: {e}")
        return False

def test_exit_button_controller():
    """Test Exit Button Controller"""
    try:
        logger.info("🧪 Testing Exit Button Controller...")
        
        from exit_button_controller import ExitButtonController
        
        # Create controller
        exit_controller = ExitButtonController(exit_button_pin=24)
        
        # Wait a moment for setup
        time.sleep(2)
        
        # Test button functionality
        logger.info("🔘 Testing exit button...")
        exit_controller.test_button()
        
        # Cleanup
        exit_controller.cleanup()
        
        logger.info("✅ Exit Button Controller test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Exit Button Controller test failed: {e}")
        return False

def test_mp3_notification_system():
    """Test MP3 Notification System"""
    try:
        logger.info("🧪 Testing MP3 Notification System...")
        
        from mp3_notification_system import MP3NotificationSystem
        
        # Create system
        mp3_system = MP3NotificationSystem()
        
        # Wait a moment for setup
        time.sleep(2)
        
        # Test audio system
        logger.info("🔊 Testing MP3 system...")
        mp3_system.test_audio_system()
        
        # Cleanup
        mp3_system.cleanup()
        
        logger.info("✅ MP3 Notification System test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ MP3 Notification System test failed: {e}")
        return False

def test_integrated_system():
    """Test the complete integrated system"""
    try:
        logger.info("🧪 Testing Integrated System...")
        
        from whac_integrated_system import WHACIntegratedSystem
        
        # Create system
        system = WHACIntegratedSystem()
        
        # Wait for initialization
        time.sleep(3)
        
        # Test system components
        logger.info("🔧 Testing system components...")
        system.test_system()
        
        # Cleanup
        system.shutdown()
        
        logger.info("✅ Integrated System test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integrated System test failed: {e}")
        return False

def main():
    """Main test function"""
    try:
        logger.info("🚀 Starting WHAC System Tests...")
        logger.info("=" * 50)
        
        # Import config
        from config import STORE_ID
        logger.info(f"📋 Testing with Store ID: {STORE_ID}")
        
        # Test results
        test_results = []
        
        # Run individual component tests
        logger.info("\n🔧 Testing Individual Components...")
        test_results.append(("MQTT Manager", test_mqtt_manager()))
        test_results.append(("GPIO Manager", test_gpio_manager()))
        test_results.append(("Exit Button Controller", test_exit_button_controller()))
        test_results.append(("MP3 Notification System", test_mp3_notification_system()))
        
        # Run integrated system test
        logger.info("\n🔧 Testing Integrated System...")
        test_results.append(("Integrated System", test_integrated_system()))
        
        # Print results
        logger.info("\n" + "=" * 50)
        logger.info("📊 Test Results Summary:")
        logger.info("=" * 50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name:30} {status}")
            if result:
                passed += 1
        
        logger.info("=" * 50)
        logger.info(f"📈 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! System is working correctly.")
            return 0
        else:
            logger.error(f"⚠️  {total - passed} tests failed. Please check the logs.")
            return 1
            
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
