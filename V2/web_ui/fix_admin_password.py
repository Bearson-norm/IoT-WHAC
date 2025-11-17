#!/usr/bin/env python3
"""
Fix Admin Password Script
This script will reset admin password and unlock account
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

def fix_admin_account():
    """Fix admin account - reset password and unlock"""
    print("=" * 60)
    print("Fixing Admin Account")
    print("=" * 60)
    
    try:
        # Connect to database
        print("[*] Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Generate new password hash
        new_password = 'admin123'
        print(f"[*] Generating password hash for '{new_password}'...")
        password_hash = hash_password(new_password)
        
        # Verify hash works
        if not bcrypt.checkpw(new_password.encode('utf-8'), password_hash.encode('utf-8')):
            print("[ERROR] Generated hash is invalid!")
            return False
        
        print("[OK] Password hash generated and verified!")
        print(f"     Hash: {password_hash}")
        
        # Update admin user
        print("[*] Updating admin user in database...")
        cursor.execute("""
            UPDATE web_users 
            SET password_hash = %s,
                is_active = TRUE,
                login_attempts = 0,
                locked_until = NULL
            WHERE username = 'admin'
        """, (password_hash,))
        
        if cursor.rowcount == 0:
            # User doesn't exist, create it
            print("[*] Admin user not found, creating new user...")
            cursor.execute("""
                INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, login_attempts, locked_until)
                VALUES ('admin', %s, 'System Administrator', 'admin@whac.com', 'admin', TRUE, 0, NULL)
            """, (password_hash,))
        
        conn.commit()
        conn.close()
        
        print("[OK] Admin account updated successfully!")
        print("=" * 60)
        print("Login Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("=" * 60)
        print("[*] Try logging in now!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_admin_account()
    sys.exit(0 if success else 1)


