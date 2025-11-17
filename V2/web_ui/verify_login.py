#!/usr/bin/env python3
"""
Verify Login Credentials
Check if admin username and password work correctly
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

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def verify_admin_login():
    """Verify admin login credentials"""
    print("=" * 60)
    print("Verifying Admin Login Credentials")
    print("=" * 60)
    
    try:
        # Connect to database
        print("[*] Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get admin user
        cursor.execute("""
            SELECT id, username, password_hash, is_active, login_attempts, locked_until
            FROM web_users 
            WHERE username = 'admin'
        """)
        user = cursor.fetchone()
        
        if not user:
            print("[ERROR] Admin user not found in database!")
            print("        Creating admin user with password 'admin123'...")
            
            # Create admin user with correct password hash
            password_hash = hash_password('admin123')
            cursor.execute("""
                INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, login_attempts, locked_until)
                VALUES ('admin', %s, 'System Administrator', 'admin@whac.com', 'admin', TRUE, 0, NULL)
            """, (password_hash,))
            conn.commit()
            
            print("[OK] Admin user created!")
            print("     Username: admin")
            print("     Password: admin123")
            print(f"     Password Hash: {password_hash}")
            conn.close()
            return True
        
        user_id, username, password_hash, is_active, login_attempts, locked_until = user
        
        print(f"[OK] Found admin user:")
        print(f"     ID: {user_id}")
        print(f"     Username: {username}")
        print(f"     Active: {is_active}")
        print(f"     Login Attempts: {login_attempts}")
        print(f"     Locked Until: {locked_until if locked_until else 'Not locked'}")
        print(f"     Password Hash: {password_hash[:50]}...")
        
        # Test password 'admin123'
        test_password = 'admin123'
        print(f"\n[*] Testing password: '{test_password}'")
        
        is_valid = verify_password(test_password, password_hash)
        
        if is_valid:
            print("[OK] Password 'admin123' is VALID!")
        else:
            print("[ERROR] Password 'admin123' is INVALID!")
            print(f"\n[*] Resetting password to 'admin123'...")
            
            # Reset password
            new_hash = hash_password('admin123')
            cursor.execute("""
                UPDATE web_users 
                SET password_hash = %s,
                    is_active = TRUE,
                    login_attempts = 0,
                    locked_until = NULL
                WHERE username = 'admin'
            """, (new_hash,))
            conn.commit()
            
            print("[OK] Password reset successfully!")
            print(f"     New Hash: {new_hash}")
            
            # Verify new password
            if verify_password('admin123', new_hash):
                print("[OK] Verified: New password works!")
            else:
                print("[ERROR] New password verification failed!")
                conn.close()
                return False
        
        # Unlock account
        if locked_until:
            print(f"\n[*] Unlocking account...")
            cursor.execute("""
                UPDATE web_users 
                SET locked_until = NULL, login_attempts = 0
                WHERE username = 'admin'
            """,)
            conn.commit()
            print("[OK] Account unlocked!")
        
        # Ensure account is active
        if not is_active:
            print(f"\n[*] Activating account...")
            cursor.execute("""
                UPDATE web_users 
                SET is_active = TRUE
                WHERE username = 'admin'
            """,)
            conn.commit()
            print("[OK] Account activated!")
        
        conn.close()
        
        print("=" * 60)
        print("[OK] Login credentials verified and fixed!")
        print("=" * 60)
        print("You can now login with:")
        print("   Username: admin")
        print("   Password: admin123")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = verify_admin_login()
    sys.exit(0 if success else 1)

