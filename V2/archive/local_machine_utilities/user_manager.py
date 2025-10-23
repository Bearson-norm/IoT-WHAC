#!/usr/bin/env python3
"""
User Management Utility for Hybrid Fingerprint System
Manage user profiles and view verification logs
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from fingerprint_hybrid_client import HybridFingerprintClient

def show_menu():
    """Display main menu"""
    print("\n" + "=" * 60)
    print("USER MANAGEMENT SYSTEM")
    print("=" * 60)
    print("1. Add new user profile")
    print("2. View all users")
    print("3. Update user profile")
    print("4. Deactivate user")
    print("5. View verification logs")
    print("6. View daily statistics")
    print("7. View user access history")
    print("8. Export logs to CSV")
    print("9. Exit")
    print("=" * 60)

def add_user_profile(client):
    """Add new user profile"""
    try:
        print("\n--- Add New User Profile ---")
        
        fingerprint_id = int(input("Enter fingerprint ID (1-128): "))
        if not (1 <= fingerprint_id <= 128):
            print("Fingerprint ID must be between 1 and 128")
            return
        
        user_name = input("Enter user name: ").strip()
        if not user_name:
            print("User name cannot be empty")
            return
        
        user_id = input("Enter user ID (optional): ").strip() or None
        department = input("Enter department (optional): ").strip() or None
        
        access_level = 1
        try:
            access_input = input("Enter access level (1-5, default 1): ").strip()
            if access_input:
                access_level = int(access_input)
                if not (1 <= access_level <= 5):
                    print("Access level must be between 1 and 5, using default 1")
                    access_level = 1
        except ValueError:
            print("Invalid access level, using default 1")
        
        if client.add_user_profile(fingerprint_id, user_name, user_id, department, access_level):
            print(f"✓ User profile added successfully: {user_name}")
        else:
            print("✗ Failed to add user profile")
            
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error: {e}")

def view_all_users(client):
    """View all user profiles"""
    try:
        conn = sqlite3.connect(client.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fingerprint_id, user_name, user_id, department, access_level, 
                   created_at, last_access, access_count, is_active
            FROM user_profiles 
            ORDER BY fingerprint_id
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            print("\nNo user profiles found.")
            return
        
        print(f"\n--- User Profiles ({len(users)} total) ---")
        print(f"{'ID':<4} {'Name':<20} {'User ID':<15} {'Dept':<15} {'Level':<5} {'Accesses':<8} {'Status':<8}")
        print("-" * 90)
        
        for user in users:
            status = "Active" if user[8] else "Inactive"
            last_access = user[6][:10] if user[6] else "Never"
            print(f"{user[0]:<4} {user[1]:<20} {user[2] or 'N/A':<15} {user[3] or 'N/A':<15} "
                  f"{user[4]:<5} {user[7]:<8} {status:<8}")
        
    except Exception as e:
        print(f"Error viewing users: {e}")

def update_user_profile(client):
    """Update user profile"""
    try:
        print("\n--- Update User Profile ---")
        
        fingerprint_id = int(input("Enter fingerprint ID to update: "))
        
        # Check if user exists
        conn = sqlite3.connect(client.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT user_name FROM user_profiles WHERE fingerprint_id = ?', (fingerprint_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print(f"User with fingerprint ID {fingerprint_id} not found.")
            return
        
        print(f"Updating profile for: {result[0]}")
        
        user_name = input("Enter new user name (or press Enter to keep current): ").strip()
        user_id = input("Enter new user ID (or press Enter to keep current): ").strip()
        department = input("Enter new department (or press Enter to keep current): ").strip()
        
        access_level = None
        try:
            access_input = input("Enter new access level 1-5 (or press Enter to keep current): ").strip()
            if access_input:
                access_level = int(access_input)
                if not (1 <= access_level <= 5):
                    print("Invalid access level, keeping current")
                    access_level = None
        except ValueError:
            print("Invalid access level, keeping current")
        
        # Get current values
        conn = sqlite3.connect(client.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_name, user_id, department, access_level 
            FROM user_profiles WHERE fingerprint_id = ?
        ''', (fingerprint_id,))
        current = cursor.fetchone()
        
        # Update with new values or keep current
        new_name = user_name if user_name else current[0]
        new_user_id = user_id if user_id else current[1]
        new_department = department if department else current[2]
        new_access_level = access_level if access_level else current[3]
        
        cursor.execute('''
            UPDATE user_profiles 
            SET user_name = ?, user_id = ?, department = ?, access_level = ?
            WHERE fingerprint_id = ?
        ''', (new_name, new_user_id, new_department, new_access_level, fingerprint_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ User profile updated successfully")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error: {e}")

def deactivate_user(client):
    """Deactivate user profile"""
    try:
        print("\n--- Deactivate User ---")
        
        fingerprint_id = int(input("Enter fingerprint ID to deactivate: "))
        
        conn = sqlite3.connect(client.db_file)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT user_name, is_active FROM user_profiles WHERE fingerprint_id = ?', (fingerprint_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"User with fingerprint ID {fingerprint_id} not found.")
            conn.close()
            return
        
        user_name, is_active = result
        
        if not is_active:
            print(f"User {user_name} is already inactive.")
            conn.close()
            return
        
        confirm = input(f"Are you sure you want to deactivate {user_name}? (y/N): ")
        if confirm.lower() == 'y':
            cursor.execute('UPDATE user_profiles SET is_active = FALSE WHERE fingerprint_id = ?', (fingerprint_id,))
            conn.commit()
            print(f"✓ User {user_name} deactivated successfully")
        else:
            print("Deactivation cancelled")
        
        conn.close()
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error: {e}")

def view_verification_logs(client):
    """View recent verification logs"""
    try:
        print("\n--- Recent Verification Logs ---")
        
        days = input("Enter number of days to view (default 1): ").strip()
        days = int(days) if days else 1
        
        conn = sqlite3.connect(client.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vl.timestamp, vl.fingerprint_id, up.user_name, vl.confidence, 
                   vl.verification_result, vl.action_taken, vl.mqtt_sent
            FROM verification_log vl
            LEFT JOIN user_profiles up ON vl.fingerprint_id = up.fingerprint_id
            WHERE vl.timestamp >= datetime('now', '-{} days')
            ORDER BY vl.timestamp DESC
            LIMIT 50
        '''.format(days))
        
        logs = cursor.fetchall()
        conn.close()
        
        if not logs:
            print(f"No verification logs found for the last {days} day(s).")
            return
        
        print(f"\n--- Last {len(logs)} verification logs ---")
        print(f"{'Time':<19} {'ID':<4} {'Name':<15} {'Conf':<4} {'Result':<10} {'Action':<20} {'MQTT':<5}")
        print("-" * 85)
        
        for log in logs:
            timestamp = log[0][:19]  # Remove microseconds
            user_name = log[2] or f"ID:{log[1]}" if log[1] > 0 else "Unknown"
            mqtt_status = "Yes" if log[6] else "No"
            print(f"{timestamp:<19} {log[1]:<4} {user_name:<15} {log[3]:<4} "
                  f"{log[4]:<10} {log[5]:<20} {mqtt_status:<5}")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error: {e}")

def view_daily_stats(client):
    """View daily statistics"""
    try:
        print("\n--- Daily Statistics ---")
        
        days = input("Enter number of days to view (default 7): ").strip()
        days = int(days) if days else 7
        
        conn = sqlite3.connect(client.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, total_scans, successful_verifications, failed_verifications, 
                   mqtt_messages_sent, avg_confidence
            FROM system_stats 
            WHERE date >= date('now', '-{} days')
            ORDER BY date DESC
        '''.format(days))
        
        stats = cursor.fetchall()
        conn.close()
        
        if not stats:
            print(f"No statistics found for the last {days} day(s).")
            return
        
        print(f"\n--- Statistics for last {len(stats)} day(s) ---")
        print(f"{'Date':<12} {'Scans':<6} {'Success':<8} {'Failed':<7} {'MQTT':<5} {'Avg Conf':<8}")
        print("-" * 60)
        
        for stat in stats:
            avg_conf = f"{stat[5]:.1f}" if stat[5] else "N/A"
            print(f"{stat[0]:<12} {stat[1]:<6} {stat[2]:<8} {stat[3]:<7} {stat[4]:<5} {avg_conf:<8}")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error: {e}")

def view_user_access_history(client):
    """View access history for a specific user"""
    try:
        print("\n--- User Access History ---")
        
        fingerprint_id = int(input("Enter fingerprint ID: "))
        
        conn = sqlite3.connect(client.db_file)
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute('SELECT user_name FROM user_profiles WHERE fingerprint_id = ?', (fingerprint_id,))
        user_result = cursor.fetchone()
        
        if not user_result:
            print(f"User with fingerprint ID {fingerprint_id} not found.")
            conn.close()
            return
        
        user_name = user_result[0]
        
        # Get access history
        cursor.execute('''
            SELECT timestamp, confidence, verification_result, action_taken, mqtt_sent
            FROM verification_log 
            WHERE fingerprint_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
        ''', (fingerprint_id,))
        
        history = cursor.fetchall()
        conn.close()
        
        if not history:
            print(f"No access history found for {user_name}.")
            return
        
        print(f"\n--- Access History for {user_name} (ID: {fingerprint_id}) ---")
        print(f"{'Time':<19} {'Confidence':<10} {'Result':<10} {'Action':<20} {'MQTT':<5}")
        print("-" * 75)
        
        for record in history:
            timestamp = record[0][:19]
            mqtt_status = "Yes" if record[4] else "No"
            print(f"{timestamp:<19} {record[1]:<10} {record[2]:<10} {record[3]:<20} {mqtt_status:<5}")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error: {e}")

def export_logs_to_csv(client):
    """Export verification logs to CSV"""
    try:
        print("\n--- Export Logs to CSV ---")
        
        days = input("Enter number of days to export (default 30): ").strip()
        days = int(days) if days else 30
        
        filename = f"fingerprint_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        conn = sqlite3.connect(client.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vl.timestamp, vl.fingerprint_id, up.user_name, up.user_id, up.department,
                   vl.confidence, vl.verification_result, vl.action_taken, vl.mqtt_sent
            FROM verification_log vl
            LEFT JOIN user_profiles up ON vl.fingerprint_id = up.fingerprint_id
            WHERE vl.timestamp >= datetime('now', '-{} days')
            ORDER BY vl.timestamp DESC
        '''.format(days))
        
        logs = cursor.fetchall()
        conn.close()
        
        if not logs:
            print(f"No logs found for the last {days} day(s).")
            return
        
        # Write CSV file
        with open(filename, 'w') as f:
            f.write("Timestamp,Fingerprint_ID,User_Name,User_ID,Department,Confidence,Result,Action,MQTT_Sent\n")
            for log in logs:
                f.write(f"{log[0]},{log[1]},{log[2] or ''},{log[3] or ''},{log[4] or ''},"
                       f"{log[5]},{log[6]},{log[7]},{log[8]}\n")
        
        print(f"✓ Exported {len(logs)} records to {filename}")
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function"""
    client = HybridFingerprintClient()
    
    try:
        while True:
            show_menu()
            choice = input("\nSelect option (1-9): ").strip()
            
            if choice == "1":
                add_user_profile(client)
            elif choice == "2":
                view_all_users(client)
            elif choice == "3":
                update_user_profile(client)
            elif choice == "4":
                deactivate_user(client)
            elif choice == "5":
                view_verification_logs(client)
            elif choice == "6":
                view_daily_stats(client)
            elif choice == "7":
                view_user_access_history(client)
            elif choice == "8":
                export_logs_to_csv(client)
            elif choice == "9":
                print("\nExiting... Goodbye!")
                break
            else:
                print("Invalid option. Please select 1-9")
    
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
