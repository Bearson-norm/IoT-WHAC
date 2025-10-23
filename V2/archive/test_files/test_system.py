#!/usr/bin/env python3
"""
Test script for WHAC system components
Helps debug issues on Raspberry Pi
"""

import os
import sys
import logging
import time
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_gpio():
    """Test GPIO functionality"""
    logger.info("🔧 Testing GPIO...")
    try:
        import RPi.GPIO as GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Test basic GPIO setup
        test_pin = 24
        GPIO.setup(test_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        state = GPIO.input(test_pin)
        logger.info(f"✅ GPIO test successful - Pin {test_pin} state: {state}")
        
        # Test edge detection
        try:
            GPIO.add_event_detect(test_pin, GPIO.FALLING, bouncetime=300)
            logger.info("✅ GPIO edge detection test successful")
            GPIO.remove_event_detect(test_pin)
        except Exception as e:
            logger.warning(f"⚠️  GPIO edge detection failed: {e}")
        
        GPIO.cleanup()
        return True
        
    except ImportError:
        logger.error("❌ RPi.GPIO not available")
        return False
    except Exception as e:
        logger.error(f"❌ GPIO test failed: {e}")
        return False

def test_audio():
    """Test audio system"""
    logger.info("🔊 Testing audio system...")
    
    # Check audio tools
    tools = ['espeak', 'ffmpeg', 'mpg123']
    for tool in tools:
        try:
            result = subprocess.run(['which', tool], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ {tool} found")
            else:
                logger.warning(f"⚠️  {tool} not found")
        except Exception as e:
            logger.warning(f"⚠️  Error checking {tool}: {e}")
    
    # Test audio directory creation
    audio_dir = os.path.join(os.getcwd(), "whac_audio")
    try:
        os.makedirs(audio_dir, exist_ok=True)
        logger.info(f"✅ Audio directory created: {audio_dir}")
        
        # Test file creation
        test_file = os.path.join(audio_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        logger.info("✅ Audio directory write test successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Audio directory test failed: {e}")
        return False

def test_fingerprint_sensor():
    """Test fingerprint sensor connection"""
    logger.info("🔐 Testing fingerprint sensor...")
    
    try:
        import serial
        import adafruit_fingerprint
        
        # Check serial ports
        ports = ['/dev/serial0', '/dev/ttyUSB0', '/dev/ttyACM0']
        for port in ports:
            if os.path.exists(port):
                logger.info(f"✅ Serial port found: {port}")
                try:
                    uart = serial.Serial(port, baudrate=57600, timeout=1)
                    finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
                    
                    # Test basic communication
                    if finger.get_image() == adafruit_fingerprint.OK:
                        logger.info(f"✅ Fingerprint sensor communication successful on {port}")
                        uart.close()
                        return True
                    else:
                        logger.warning(f"⚠️  Fingerprint sensor not responding on {port}")
                        uart.close()
                        
                except Exception as e:
                    logger.warning(f"⚠️  Error testing {port}: {e}")
            else:
                logger.info(f"ℹ️  Serial port not found: {port}")
        
        logger.warning("⚠️  No working fingerprint sensor found")
        return False
        
    except ImportError as e:
        logger.error(f"❌ Fingerprint libraries not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Fingerprint sensor test failed: {e}")
        return False

def test_mqtt():
    """Test MQTT connection"""
    logger.info("📡 Testing MQTT connection...")
    
    try:
        import paho.mqtt.client as mqtt
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("✅ MQTT connection successful")
                client.disconnect()
            else:
                logger.error(f"❌ MQTT connection failed with code {rc}")
        
        client = mqtt.Client()
        client.on_connect = on_connect
        
        try:
            client.connect("103.87.67.139", 1883, 10)
            client.loop_start()
            time.sleep(2)
            client.loop_stop()
            return True
        except Exception as e:
            logger.error(f"❌ MQTT connection test failed: {e}")
            return False
            
    except ImportError:
        logger.error("❌ paho-mqtt not available")
        return False

def test_audio_generation():
    """Test audio file generation"""
    logger.info("🎵 Testing audio file generation...")
    
    try:
        audio_dir = os.path.join(os.getcwd(), "whac_audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        # Test espeak
        test_wav = os.path.join(audio_dir, "test.wav")
        test_mp3 = os.path.join(audio_dir, "test.mp3")
        
        # Generate test audio
        espeak_cmd = ['espeak', '-s', '150', '-v', 'en', '-w', test_wav, 'Test message']
        result = subprocess.run(espeak_cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(test_wav):
            logger.info("✅ espeak test successful")
            
            # Test ffmpeg conversion
            ffmpeg_cmd = ['ffmpeg', '-i', test_wav, '-acodec', 'mp3', '-ab', '128k', '-y', test_mp3]
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(test_mp3):
                logger.info("✅ ffmpeg conversion test successful")
                
                # Cleanup
                os.remove(test_wav)
                os.remove(test_mp3)
                return True
            else:
                logger.error("❌ ffmpeg conversion test failed")
        else:
            logger.error("❌ espeak test failed")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Audio generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 Starting WHAC System Tests...")
    
    tests = [
        ("GPIO", test_gpio),
        ("Audio Directory", test_audio),
        ("Fingerprint Sensor", test_fingerprint_sensor),
        ("MQTT", test_mqtt),
        ("Audio Generation", test_audio_generation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} Test")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! System is ready.")
    else:
        logger.info("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()




