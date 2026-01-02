#!/usr/bin/env python3
"""
Script untuk mengecek apakah fingerprint sudah ter-enroll di sensor
Membantu debugging masalah "Not Match" yang terus muncul
"""

import serial
import adafruit_fingerprint
import sys
import time
from config import *

def check_enrollment(port, fingerprint_id):
    """Check if fingerprint ID is enrolled on sensor"""
    try:
        print(f"🔍 Checking enrollment for fingerprint ID {fingerprint_id} on {port}...")
        
        # Connect to sensor
        uart = serial.Serial(port, baudrate=BAUD_RATE, timeout=2)
        time.sleep(0.5)
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        
        # Get template count
        if finger.read_templates() == adafruit_fingerprint.OK:
            print(f"✓ Sensor connected")
            print(f"📊 Total templates in sensor: {finger.template_count}")
        else:
            print(f"❌ Failed to read templates from sensor")
            uart.close()
            return False
        
        # Try to load the fingerprint template
        print(f"🔍 Checking if fingerprint ID {fingerprint_id} exists...")
        result = finger.load_model(fingerprint_id)
        
        if result == adafruit_fingerprint.OK:
            print(f"✅ Fingerprint ID {fingerprint_id} is enrolled in sensor!")
            print(f"   Location: {fingerprint_id}")
            uart.close()
            return True
        elif result == adafruit_fingerprint.NOTFOUND:
            print(f"❌ Fingerprint ID {fingerprint_id} is NOT enrolled in sensor")
            print(f"   The fingerprint needs to be enrolled first!")
            uart.close()
            return False
        else:
            print(f"❌ Error checking fingerprint: {result}")
            uart.close()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_all_enrolled(port):
    """List all enrolled fingerprints"""
    try:
        print(f"📋 Listing all enrolled fingerprints on {port}...")
        
        # Connect to sensor
        uart = serial.Serial(port, baudrate=BAUD_RATE, timeout=2)
        time.sleep(0.5)
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        
        # Get template count
        if finger.read_templates() == adafruit_fingerprint.OK:
            print(f"✓ Sensor connected")
            print(f"📊 Total templates: {finger.template_count}")
            
            if finger.template_count == 0:
                print("⚠️  No fingerprints enrolled in sensor!")
                uart.close()
                return
            
            print("\n📝 Enrolled fingerprints:")
            print("=" * 50)
            
            # Try to check each possible location (1-162 for AS608)
            enrolled_ids = []
            for location in range(1, min(163, finger.template_count + 10)):  # Check up to template_count + 10
                result = finger.load_model(location)
                if result == adafruit_fingerprint.OK:
                    enrolled_ids.append(location)
                    print(f"  ✓ ID: {location}")
            
            if enrolled_ids:
                print(f"\n✅ Found {len(enrolled_ids)} enrolled fingerprint(s): {enrolled_ids}")
            else:
                print(f"\n⚠️  No fingerprints found (but template_count = {finger.template_count})")
                print("   This might indicate a sensor issue or template corruption")
            
            uart.close()
        else:
            print(f"❌ Failed to read templates from sensor")
            uart.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_scan(port, fingerprint_id=None):
    """Test fingerprint scan and search"""
    try:
        print(f"🧪 Testing fingerprint scan on {port}...")
        
        # Connect to sensor
        uart = serial.Serial(port, baudrate=BAUD_RATE, timeout=2)
        time.sleep(0.5)
        finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        
        print("📸 Place your finger on the sensor...")
        print("   (Waiting for finger, timeout: 30 seconds)")
        
        start_time = time.time()
        while time.time() - start_time < 30:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("✓ Fingerprint image captured!")
                break
            elif i == adafruit_fingerprint.NOFINGER:
                time.sleep(0.5)
                print(".", end="", flush=True)
                continue
            else:
                print(f"\n❌ Error getting image: {i}")
                uart.close()
                return
        
        if time.time() - start_time >= 30:
            print("\n❌ Timeout: No finger detected")
            uart.close()
            return
        
        # Convert to template
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("❌ Failed to convert image to template")
            uart.close()
            return
        
        print("✓ Image converted to template")
        
        # Search for match
        print("🔍 Searching for match...")
        i = finger.finger_search()
        
        if i == adafruit_fingerprint.OK:
            finger_id = finger.finger_id
            confidence = finger.confidence
            
            print(f"✅ Match found!")
            print(f"   Fingerprint ID: {finger_id}")
            print(f"   Confidence: {confidence}")
            print(f"   Threshold: {CONFIDENCE_THRESHOLD}")
            
            if confidence >= CONFIDENCE_THRESHOLD:
                print(f"   ✓ Confidence {confidence} >= threshold {CONFIDENCE_THRESHOLD} - Match accepted")
            else:
                print(f"   ⚠️  Confidence {confidence} < threshold {CONFIDENCE_THRESHOLD} - Match would be rejected")
            
            if fingerprint_id and finger_id != fingerprint_id:
                print(f"   ⚠️  Expected ID {fingerprint_id} but got {finger_id}")
        else:
            error_codes = {
                adafruit_fingerprint.NOTFOUND: "NOTFOUND - No matching fingerprint in database",
                adafruit_fingerprint.ENROLLMISMATCH: "ENROLLMISMATCH - Fingerprints did not match",
                adafruit_fingerprint.UNKNOWN: "UNKNOWN - Unknown error"
            }
            error_msg = error_codes.get(i, f"Error code: {i}")
            print(f"❌ No match found - {error_msg}")
            
            if fingerprint_id:
                print(f"\n💡 Troubleshooting:")
                print(f"   1. Check if fingerprint ID {fingerprint_id} is enrolled:")
                print(f"      python check_fingerprint_enrollment.py {port} {fingerprint_id}")
                print(f"   2. List all enrolled fingerprints:")
                print(f"      python check_fingerprint_enrollment.py {port} --list")
                print(f"   3. Try enrolling the fingerprint again")
        
        uart.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python check_fingerprint_enrollment.py <port> <fingerprint_id>  # Check specific ID")
        print("  python check_fingerprint_enrollment.py <port> --list            # List all enrolled")
        print("  python check_fingerprint_enrollment.py <port> --test [id]       # Test scan")
        print("\nExample:")
        print("  python check_fingerprint_enrollment.py /dev/serial0 1")
        print("  python check_fingerprint_enrollment.py /dev/serial0 --list")
        print("  python check_fingerprint_enrollment.py /dev/serial0 --test 1")
        sys.exit(1)
    
    port = sys.argv[1]
    
    if len(sys.argv) >= 3:
        if sys.argv[2] == "--list":
            list_all_enrolled(port)
        elif sys.argv[2] == "--test":
            fingerprint_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
            test_scan(port, fingerprint_id)
        else:
            fingerprint_id = int(sys.argv[2])
            check_enrollment(port, fingerprint_id)
    else:
        list_all_enrolled(port)

