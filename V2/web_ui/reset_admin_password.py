#!/usr/bin/env python3
"""
Reset Admin Password Utility
Use this script to reset the admin password if login fails
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

def reset_admin_password(new_password='admin123'):
    """Reset admin password"""
    print("=" * 60)
    print("🔐 Admin Password Reset Utility")
    print("=" * 60)
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id, username FROM web_users WHERE username = 'admin'")
        user = cursor.fetchone()
        
        if not user:
            print("❌ Admin user not found! Creating new admin user...")
            # Create admin user
            password_hash = hash_password(new_password)
            cursor.execute("""
                INSERT INTO web_users (username, password_hash, full_name, email, role, is_active)
                VALUES ('admin', %s, 'System Administrator', 'admin@whac.com', 'admin', TRUE)
            """, (password_hash,))
            print("✅ Admin user created successfully!")
        else:
            print(f"✓ Found admin user (ID: {user[0]})")
            # Update password
            password_hash = hash_password(new_password)
            cursor.execute("""
                UPDATE web_users 
                SET password_hash = %s, 
                    is_active = TRUE,
                    locked_until = NULL,
                    login_attempts = 0
                WHERE username = 'admin'
            """, (password_hash,))
            print("✅ Admin password updated successfully!")
        
        conn.commit()
        conn.close()
        
        print("=" * 60)
        print(f"✅ Password reset complete!")
        print(f"   Username: admin")
        print(f"   Password: {new_password}")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Get password from command line or use default
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = 'admin123'
    
    success = reset_admin_password(password)
    sys.exit(0 if success else 1)


