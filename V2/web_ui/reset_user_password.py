#!/usr/bin/env python3
"""
Reset User Password Utility
Use this script to reset any user's password if login fails
Usage: python reset_user_password.py <username> [new_password]
"""

import psycopg2
import bcrypt
import os
import sys

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'whac_master'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Admin123'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def reset_user_password(username, new_password='password123'):
    """Reset user password by username"""
    print("=" * 60)
    print("🔐 User Password Reset Utility")
    print("=" * 60)
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, username, full_name, email, role FROM web_users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User '{username}' not found!")
            print("\nAvailable users:")
            cursor.execute("SELECT id, username, full_name, email, role FROM web_users ORDER BY username")
            users = cursor.fetchall()
            for u in users:
                print(f"   - {u[1]} ({u[2] or 'N/A'}) - {u[4]}")
            conn.close()
            return False
        
        user_id, db_username, full_name, email, role = user
        print(f"✓ Found user:")
        print(f"   ID: {user_id}")
        print(f"   Username: {db_username}")
        print(f"   Full Name: {full_name or 'N/A'}")
        print(f"   Email: {email or 'N/A'}")
        print(f"   Role: {role}")
        
        # Update password
        print(f"\n[*] Resetting password...")
        password_hash = hash_password(new_password)
        cursor.execute("""
            UPDATE web_users 
            SET password_hash = %s, 
                is_active = TRUE,
                locked_until = NULL,
                login_attempts = 0
            WHERE username = %s
        """, (password_hash, username))
        
        conn.commit()
        conn.close()
        
        print("✅ Password reset successfully!")
        print("=" * 60)
        print(f"Login Credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {new_password}")
        print("=" * 60)
        print("⚠️  Please change your password after logging in!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python reset_user_password.py <username> [new_password]")
        print("\nExample:")
        print("  python reset_user_password.py admin")
        print("  python reset_user_password.py admin mynewpassword")
        print("  python reset_user_password.py Mamat")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else 'password123'
    
    success = reset_user_password(username, password)
    sys.exit(0 if success else 1)

