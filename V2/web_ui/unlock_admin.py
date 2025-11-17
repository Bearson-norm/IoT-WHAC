#!/usr/bin/env python3
"""
Unlock Admin Account Utility
Use this script to unlock the admin account if it's locked due to failed login attempts
"""

import psycopg2
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

def unlock_admin_account():
    """Unlock admin account"""
    print("=" * 60)
    print("🔓 Admin Account Unlock Utility")
    print("=" * 60)
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check admin user status
        cursor.execute("""
            SELECT id, username, is_active, login_attempts, locked_until 
            FROM web_users 
            WHERE username = 'admin'
        """)
        user = cursor.fetchone()
        
        if not user:
            print("❌ Admin user not found!")
            conn.close()
            return False
        
        user_id, username, is_active, login_attempts, locked_until = user
        
        print(f"✓ Found admin user (ID: {user_id})")
        print(f"   Active: {is_active}")
        print(f"   Login attempts: {login_attempts}")
        print(f"   Locked until: {locked_until if locked_until else 'Not locked'}")
        
        # Unlock account
        cursor.execute("""
            UPDATE web_users 
            SET locked_until = NULL,
                login_attempts = 0,
                is_active = TRUE
            WHERE username = 'admin'
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Admin account unlocked successfully!")
        print("=" * 60)
        print("You can now login with:")
        print("   Username: admin")
        print("   Password: admin123")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error unlocking account: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = unlock_admin_account()
    sys.exit(0 if success else 1)


