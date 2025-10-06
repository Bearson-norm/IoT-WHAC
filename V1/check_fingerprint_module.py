#!/usr/bin/env python3
"""
Script to check what's available in the adafruit_fingerprint module
"""

try:
    import adafruit_fingerprint
    print("✓ adafruit_fingerprint module imported successfully")
    
    # Check what's available in the module
    print("\nAvailable attributes in adafruit_fingerprint:")
    for attr in dir(adafruit_fingerprint):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
    # Try different possible class names
    possible_classes = ['AdafruitFingerprint', 'Fingerprint', 'FingerprintSensor']
    
    for class_name in possible_classes:
        try:
            cls = getattr(adafruit_fingerprint, class_name)
            print(f"\n✓ Found class: {class_name}")
            print(f"  Type: {type(cls)}")
            if hasattr(cls, '__doc__') and cls.__doc__:
                print(f"  Doc: {cls.__doc__.strip()}")
        except AttributeError:
            print(f"✗ Class not found: {class_name}")
    
    # Check if there are any classes at all
    classes = [attr for attr in dir(adafruit_fingerprint) 
               if not attr.startswith('_') and isinstance(getattr(adafruit_fingerprint, attr), type)]
    
    print(f"\nAll classes found: {classes}")
    
except ImportError as e:
    print(f"✗ Failed to import adafruit_fingerprint: {e}")
except Exception as e:
    print(f"✗ Error checking module: {e}")
