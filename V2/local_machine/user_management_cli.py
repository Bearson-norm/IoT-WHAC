#!/usr/bin/env python3
"""
Command Line Interface for Fingerprint User Management
Provides easy access to user management functions
"""

import sys
import json
import time
from datetime import datetime, timedelta
from fingerprint_user_controller import FingerprintUserController

def print_header():
    """Print application header"""
    print("\n" + "=" * 80)
    print("FINGERPRINT USER MANAGEMENT CLI")
    print("=" * 80)
    print("Advanced user management for WHAC Fingerprint System")
    print("Based on fingerprint_simple_client.py configuration")
    print("=" * 80)

def print_menu():
    """Print main menu"""
    print("\n" + "=" * 60)
    print("USER MANAGEMENT OPTIONS")
    print("=" * 60)
    print("1.  List all users")
    print("2.  Get user information")
    print("3.  Update user profile")
    print("4.  Activate/Deactivate user")
    print("5.  Delete user")
    print("6.  Get user statistics")
    print("7.  Export users to CSV")
    print("8.  View verification logs")
    print("9.  Get system statistics")
    print("10. Test MQTT connection")
    print("11. Test fingerprint sensor")
    print("12. Exit")
    print("=" * 60)

def list_users(controller):
    """List all users"""
    try:
        print("\n--- Listing Users ---")
        
        # Get filter options
        active_only = input("Show only active users? (y/N): ").lower() == 'y'
        department = input("Filter by department (optional): ").strip() or None
        
        # Send MQTT command
        command = {
            "command": "list_users",
            "data": {
                "active_only": active_only,
                "department": department
            }
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        # Wait for response
        print("Waiting for response...")
        time.sleep(2)
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except Exception as e:
        print(f"Error listing users: {e}")

def get_user_info(controller):
    """Get user information"""
    try:
        print("\n--- Get User Information ---")
        
        fingerprint_id = int(input("Enter fingerprint ID: "))
        
        command = {
            "command": "get_user_info",
            "data": {
                "fingerprint_id": fingerprint_id
            }
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except ValueError:
        print("Invalid fingerprint ID. Please enter a number.")
    except Exception as e:
        print(f"Error getting user info: {e}")

def update_user(controller):
    """Update user profile"""
    try:
        print("\n--- Update User Profile ---")
        
        fingerprint_id = int(input("Enter fingerprint ID to update: "))
        
        print("Enter new values (press Enter to skip):")
        user_name = input("User name: ").strip() or None
        user_id = input("User ID: ").strip() or None
        department = input("Department: ").strip() or None
        access_level = input("Access level (1-5): ").strip() or None
        notes = input("Notes: ").strip() or None
        
        if access_level:
            access_level = int(access_level)
        
        command = {
            "command": "update_user",
            "data": {
                "fingerprint_id": fingerprint_id,
                "user_name": user_name,
                "user_id": user_id,
                "department": department,
                "access_level": access_level,
                "notes": notes
            }
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error updating user: {e}")

def activate_deactivate_user(controller):
    """Activate or deactivate user"""
    try:
        print("\n--- Activate/Deactivate User ---")
        
        fingerprint_id = int(input("Enter fingerprint ID: "))
        action = input("Action (activate/deactivate): ").lower()
        
        if action not in ['activate', 'deactivate']:
            print("Invalid action. Please enter 'activate' or 'deactivate'.")
            return
        
        command = {
            "command": f"{action}_user",
            "data": {
                "fingerprint_id": fingerprint_id
            }
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except ValueError:
        print("Invalid fingerprint ID. Please enter a number.")
    except Exception as e:
        print(f"Error updating user status: {e}")

def delete_user(controller):
    """Delete user"""
    try:
        print("\n--- Delete User ---")
        
        fingerprint_id = int(input("Enter fingerprint ID to delete: "))
        
        confirm = input(f"Are you sure you want to delete user {fingerprint_id}? (y/N): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled.")
            return
        
        command = {
            "command": "delete_user",
            "data": {
                "fingerprint_id": fingerprint_id
            }
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except ValueError:
        print("Invalid fingerprint ID. Please enter a number.")
    except Exception as e:
        print(f"Error deleting user: {e}")

def get_user_stats(controller):
    """Get user statistics"""
    try:
        print("\n--- Get User Statistics ---")
        
        fingerprint_id = input("Enter fingerprint ID (or press Enter for system stats): ").strip()
        days = input("Number of days to analyze (default 30): ").strip() or "30"
        
        data = {"days": int(days)}
        if fingerprint_id:
            data["fingerprint_id"] = int(fingerprint_id)
        
        command = {
            "command": "get_user_stats",
            "data": data
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error getting user stats: {e}")

def export_users(controller):
    """Export users to CSV"""
    try:
        print("\n--- Export Users ---")
        
        format_type = input("Export format (json/csv, default csv): ").strip() or "csv"
        active_only = input("Export only active users? (y/N): ").lower() == 'y'
        
        command = {
            "command": "export_users",
            "data": {
                "format": format_type,
                "active_only": active_only
            }
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except Exception as e:
        print(f"Error exporting users: {e}")

def view_verification_logs(controller):
    """View verification logs"""
    try:
        print("\n--- View Verification Logs ---")
        
        fingerprint_id = input("Enter fingerprint ID (or press Enter for all): ").strip()
        days = input("Number of days to view (default 7): ").strip() or "7"
        limit = input("Number of records to show (default 50): ").strip() or "50"
        
        data = {
            "days": int(days),
            "limit": int(limit)
        }
        
        if fingerprint_id:
            data["fingerprint_id"] = int(fingerprint_id)
        
        command = {
            "command": "get_verification_logs",
            "data": data
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error getting verification logs: {e}")

def get_system_stats(controller):
    """Get system statistics"""
    try:
        print("\n--- Get System Statistics ---")
        
        days = input("Number of days to analyze (default 30): ").strip() or "30"
        
        command = {
            "command": "get_system_stats",
            "data": {
                "days": int(days)
            }
        }
        
        print("Sending command to user controller...")
        controller.mqtt_client.publish(controller.USER_MGMT_TOPIC, json.dumps(command))
        
        print("✓ Command sent successfully!")
        print("Check the user controller logs for the response.")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error getting system stats: {e}")

def test_mqtt_connection(controller):
    """Test MQTT connection"""
    try:
        print("\n--- Testing MQTT Connection ---")
        
        if controller.connected:
            print("✓ MQTT client is connected")
            print(f"  Broker: {controller.mqtt_client._host}:{controller.mqtt_client._port}")
            print(f"  Client ID: {controller.mqtt_client._client_id}")
        else:
            print("✗ MQTT client is not connected")
            print("Attempting to reconnect...")
            
            if controller.connect_mqtt():
                print("✓ MQTT reconnection successful")
            else:
                print("✗ MQTT reconnection failed")
        
    except Exception as e:
        print(f"Error testing MQTT connection: {e}")

def test_fingerprint_sensor(controller):
    """Test fingerprint sensor"""
    try:
        print("\n--- Testing Fingerprint Sensor ---")
        
        if controller.finger:
            print("✓ Fingerprint sensor is connected")
            print(f"  Port: {controller.detected_port}")
            
            # Try to get template count
            try:
                if controller.finger.read_templates() == 0:  # adafruit_fingerprint.OK
                    print(f"  Templates stored: {controller.finger.template_count}")
                else:
                    print("  Warning: Could not read template count")
            except Exception as e:
                print(f"  Warning: Error reading templates: {e}")
        else:
            print("✗ Fingerprint sensor is not connected")
            print("Attempting to reconnect...")
            
            if controller.connect_sensor():
                print("✓ Fingerprint sensor reconnection successful")
            else:
                print("✗ Fingerprint sensor reconnection failed")
        
    except Exception as e:
        print(f"Error testing fingerprint sensor: {e}")

def main():
    """Main function"""
    print_header()
    
    # Initialize controller
    print("Initializing user controller...")
    controller = FingerprintUserController()
    
    try:
        # Connect to fingerprint sensor
        print("Connecting to fingerprint sensor...")
        if not controller.connect_sensor():
            print("Warning: Failed to connect to fingerprint sensor")
            print("Some functions may not work properly")
        
        # Connect to MQTT broker
        print("Connecting to MQTT broker...")
        if not controller.connect_mqtt():
            print("Error: Failed to connect to MQTT broker")
            print("User management commands will not work")
            return 1
        
        print("✓ User controller initialized successfully!")
        
        # Main menu loop
        while True:
            print_menu()
            choice = input("\nSelect option (1-12): ").strip()
            
            if choice == "1":
                list_users(controller)
            elif choice == "2":
                get_user_info(controller)
            elif choice == "3":
                update_user(controller)
            elif choice == "4":
                activate_deactivate_user(controller)
            elif choice == "5":
                delete_user(controller)
            elif choice == "6":
                get_user_stats(controller)
            elif choice == "7":
                export_users(controller)
            elif choice == "8":
                view_verification_logs(controller)
            elif choice == "9":
                get_system_stats(controller)
            elif choice == "10":
                test_mqtt_connection(controller)
            elif choice == "11":
                test_fingerprint_sensor(controller)
            elif choice == "12":
                print("\nExiting... Goodbye!")
                break
            else:
                print("Invalid option. Please select 1-12")
            
            input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
    finally:
        controller.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())




