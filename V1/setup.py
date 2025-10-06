#!/usr/bin/env python3
"""
Setup script for Fingerprint MQTT Client
Run this script to install dependencies and configure the system
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("Setting up Fingerprint MQTT Client for Raspberry Pi 4...")
    print("=" * 60)
    
    # Update system packages
    if not run_command("sudo apt update", "Updating system packages"):
        print("Warning: Failed to update system packages")
    
    # Install required system packages
    system_packages = [
        "python3-pip",
        "python3-serial",
        "python3-dev",
        "build-essential"
    ]
    
    for package in system_packages:
        if not run_command(f"sudo apt install -y {package}", f"Installing {package}"):
            print(f"Warning: Failed to install {package}")
    
    # Install Python dependencies
    if not run_command("pip3 install -r requirements.txt", "Installing Python dependencies"):
        print("Error: Failed to install Python dependencies")
        return 1
    
    # Check if user is in dialout group (needed for serial access)
    try:
        import grp
        dialout_gid = grp.getgrnam('dialout').gr_gid
        if dialout_gid not in os.getgroups():
            print("Adding user to dialout group for serial access...")
            if not run_command("sudo usermod -a -G dialout $USER", "Adding user to dialout group"):
                print("Warning: Failed to add user to dialout group")
                print("You may need to manually add your user to the dialout group")
                print("Run: sudo usermod -a -G dialout $USER")
    except:
        print("Warning: Could not check dialout group membership")
    
    # Create log directory
    if not os.path.exists("logs"):
        os.makedirs("logs")
        print("✓ Created logs directory")
    
    print("\n" + "=" * 60)
    print("Setup completed!")
    print("\nNext steps:")
    print("1. Connect your AS608 fingerprint sensor to USB port")
    print("2. Check the device path (usually /dev/ttyUSB0 or /dev/ttyACM0)")
    print("3. Update the FINGERPRINT_PORT in fingerprint_mqtt_client.py if needed")
    print("4. Run the program: python3 fingerprint_mqtt_client.py")
    print("\nNote: You may need to reboot after adding user to dialout group")
    
    return 0

if __name__ == "__main__":
    exit(main())
