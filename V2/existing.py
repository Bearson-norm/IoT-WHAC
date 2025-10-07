import serial
import adafruit_fingerprint
import time

def connect_sensor(retries=3):
    """Connect to sensor with retry logic"""
    for attempt in range(retries):
        try:
            uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=2)
            time.sleep(0.5)  # Give sensor time to stabilize
            finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
            print("✓ Sensor connected successfully!")
            return uart, finger
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(1)
            else:
                raise

# Initialize connection
print("Connecting to AS608 Fingerprint Sensor...")
uart, finger = connect_sensor()

def enroll_fingerprint(location):
    """Enroll a new fingerprint at the specified location (1-127)"""
    print(f"\n=== Enrolling fingerprint at location {location} ===")
    print("Place finger on sensor...")
    
    # First scan
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            break
        if i == adafruit_fingerprint.NOFINGER:
            continue
        else:
            print(f"Error getting image: {i}")
            return False
    
    print("Image captured!")
    
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("Error converting image")
        return False
    
    print("Remove finger")
    time.sleep(2)
    
    while finger.get_image() != adafruit_fingerprint.NOFINGER:
        pass
    
    print("Place same finger again...")
    
    # Second scan
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            break
        if i == adafruit_fingerprint.NOFINGER:
            continue
        else:
            print(f"Error getting image: {i}")
            return False
    
    print("Image captured!")
    
    if finger.image_2_tz(2) != adafruit_fingerprint.OK:
        print("Error converting second image")
        return False
    
    print("Creating model...")
    if finger.create_model() != adafruit_fingerprint.OK:
        print("Error creating model - fingers didn't match?")
        return False
    
    print(f"Storing model at location {location}...")
    if finger.store_model(location) != adafruit_fingerprint.OK:
        print("Error storing model")
        return False
    
    print(f"✓ Fingerprint enrolled successfully at location {location}!")
    return True

def verify_fingerprint():
    """Check if a fingerprint matches any stored prints"""
    print("\n=== Verifying fingerprint ===")
    print("Place finger on sensor...")
    
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            break
        if i == adafruit_fingerprint.NOFINGER:
            continue
        else:
            print(f"Error: {i}")
            return False
    
    print("Image captured, processing...")
    
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("Error processing image")
        return False
    
    print("Searching database...")
    i = finger.finger_search()
    
    if i == adafruit_fingerprint.OK:
        print(f"✓ Match found!")
        print(f"  ID: {finger.finger_id}")
        print(f"  Confidence: {finger.confidence}")
        return True
    else:
        print("✗ No match found")
        return False

def get_template_count():
    """Get number of stored fingerprints"""
    if finger.read_templates() == adafruit_fingerprint.OK:
        print(f"Stored fingerprints: {finger.template_count}")
        return finger.template_count
    else:
        print("Failed to read template count")
        return -1

def delete_fingerprint(location):
    """Delete a fingerprint at specified location"""
    if finger.delete_model(location) == adafruit_fingerprint.OK:
        print(f"✓ Fingerprint at location {location} deleted")
        return True
    else:
        print(f"✗ Failed to delete fingerprint at location {location}")
        return False

def empty_database():
    """Delete all fingerprints"""
    print("⚠ Warning: This will delete ALL fingerprints!")
    confirm = input("Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        if finger.empty_library() == adafruit_fingerprint.OK:
            print("✓ All fingerprints deleted")
            return True
        else:
            print("✗ Failed to empty database")
            return False
    else:
        print("Cancelled")
        return False

# Main program
try:
    print("\n" + "=" * 50)
    print("AS608 Fingerprint Sensor - Ready!")
    print("=" * 50)
    
    # Show current status
    count = get_template_count()
    
    while True:
        print("\n" + "=" * 50)
        print("MENU")
        print("=" * 50)
        print("1. Enroll new fingerprint")
        print("2. Verify fingerprint")
        print("3. Delete fingerprint")
        print("4. Show template count")
        print("5. Empty database (delete all)")
        print("6. Exit")
        print("=" * 50)
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            try:
                location = int(input("Enter storage location (1-127): "))
                if 1 <= location <= 127:
                    enroll_fingerprint(location)
                else:
                    print("Location must be between 1 and 127")
            except ValueError:
                print("Please enter a valid number")
        
        elif choice == "2":
            verify_fingerprint()
        
        elif choice == "3":
            try:
                location = int(input("Enter location to delete (1-127): "))
                if 1 <= location <= 127:
                    delete_fingerprint(location)
                else:
                    print("Location must be between 1 and 127")
            except ValueError:
                print("Please enter a valid number")
        
        elif choice == "4":
            get_template_count()
        
        elif choice == "5":
            empty_database()
        
        elif choice == "6":
            print("\nExiting... Goodbye!")
            break
        
        else:
            print("Invalid option. Please select 1-6")

except KeyboardInterrupt:
    print("\n\nProgram interrupted by user")
except Exception as e:
    print(f"\nError: {e}")
finally:
    if 'uart' in locals():
        uart.close()
        print("Connection closed")