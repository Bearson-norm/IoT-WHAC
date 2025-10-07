#!/usr/bin/env python3
"""
User Management Script for WHAC Web UI
Create new users for the web interface
"""

import psycopg2
import bcrypt
import getpass
import sys
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'whac_master',
    'user': 'postgres',
    'password': 'Admin123',
    'port': 5432
}

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def create_user():
    """Create a new user"""
    print("=" * 60)
    print("WHAC Web UI - User Creation")
    print("=" * 60)
    
    # Get user input
    username = input("Enter username: ").strip()
    if not username:
        print("Username cannot be empty!")
        return False
    
    full_name = input("Enter full name: ").strip()
    email = input("Enter email: ").strip()
    
    # Role selection
    print("\nAvailable roles:")
    print("1. admin - Full access to all features")
    print("2. operator - Access to monitoring and basic operations")
    print("3. viewer - Read-only access")
    
    role_choice = input("Select role (1-3): ").strip()
    role_map = {'1': 'admin', '2': 'operator', '3': 'viewer'}
    role = role_map.get(role_choice, 'viewer')
    
    # Password input
    while True:
        password = getpass.getpass("Enter password: ")
        if len(password) < 6:
            print("Password must be at least 6 characters long!")
            continue
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match!")
            continue
        
        break
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database!")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM web_users WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"Username '{username}' already exists!")
            return False
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert user
        cursor.execute("""
            INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (username, password_hash, full_name, email, role, True, datetime.now()))
        
        conn.commit()
        print(f"\n✓ User '{username}' created successfully!")
        print(f"  Full Name: {full_name}")
        print(f"  Email: {email}")
        print(f"  Role: {role}")
        print(f"  Status: Active")
        
        return True
        
    except Exception as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def list_users():
    """List all users"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database!")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, email, role, is_active, created_at, last_login
            FROM web_users
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("No users found!")
            return
        
        print("\n" + "=" * 100)
        print("WHAC Web UI - User List")
        print("=" * 100)
        print(f"{'ID':<3} {'Username':<15} {'Full Name':<20} {'Email':<25} {'Role':<10} {'Status':<8} {'Created':<12} {'Last Login':<12}")
        print("-" * 100)
        
        for user in users:
            id, username, full_name, email, role, is_active, created_at, last_login = user
            status = "Active" if is_active else "Inactive"
            created_str = created_at.strftime("%Y-%m-%d") if created_at else "N/A"
            last_login_str = last_login.strftime("%Y-%m-%d") if last_login else "Never"
            
            print(f"{id:<3} {username:<15} {full_name or 'N/A':<20} {email or 'N/A':<25} {role:<10} {status:<8} {created_str:<12} {last_login_str:<12}")
        
        print("=" * 100)
        
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        conn.close()

def deactivate_user():
    """Deactivate a user"""
    username = input("Enter username to deactivate: ").strip()
    if not username:
        print("Username cannot be empty!")
        return False
    
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database!")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, is_active FROM web_users WHERE username = %s", (username,))
        result = cursor.fetchone()
        
        if not result:
            print(f"User '{username}' not found!")
            return False
        
        user_id, is_active = result
        
        if not is_active:
            print(f"User '{username}' is already inactive!")
            return False
        
        # Deactivate user
        cursor.execute("UPDATE web_users SET is_active = FALSE WHERE id = %s", (user_id,))
        conn.commit()
        
        print(f"✓ User '{username}' deactivated successfully!")
        return True
        
    except Exception as e:
        print(f"Error deactivating user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function"""
    while True:
        print("\n" + "=" * 60)
        print("WHAC Web UI - User Management")
        print("=" * 60)
        print("1. Create new user")
        print("2. List all users")
        print("3. Deactivate user")
        print("4. Exit")
        print("-" * 60)
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == '1':
            create_user()
        elif choice == '2':
            list_users()
        elif choice == '3':
            deactivate_user()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option! Please select 1-4.")

if __name__ == "__main__":
    main()

