#!/usr/bin/env python3
"""
Script untuk test create user dan debug masalah
"""

import psycopg2
import bcrypt
import os
from datetime import datetime

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

def test_create_user(username, password, full_name=None, email=None, role='viewer'):
    """Test creating a user directly in database"""
    print("=" * 80)
    print("🧪 Test Create User")
    print("=" * 80)
    print(f"Username: {username}")
    print(f"Full Name: {full_name or 'N/A'}")
    print(f"Email: {email or 'N/A'}")
    print(f"Role: {role}")
    print()
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if username exists
        print("[1] Checking if username already exists...")
        cursor.execute("SELECT id, username FROM web_users WHERE username = %s", (username,))
        existing = cursor.fetchone()
        if existing:
            print(f"❌ Username '{username}' already exists (ID: {existing[0]})")
            conn.close()
            return False
        
        print("✅ Username is available")
        
        # Hash password
        print("[2] Hashing password...")
        password_hash = hash_password(password)
        print("✅ Password hashed")
        
        # Insert user
        print("[3] Inserting user into database...")
        cursor.execute("""
            INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (username, password_hash, full_name, email, role, True, datetime.now()))
        
        print("✅ User inserted")
        
        # Commit
        print("[4] Committing transaction...")
        conn.commit()
        print("✅ Transaction committed")
        
        # Verify
        print("[5] Verifying user was created...")
        cursor.execute("SELECT id, username, full_name, email, role, is_active FROM web_users WHERE username = %s", (username,))
        created = cursor.fetchone()
        
        if created:
            print("✅ User verified in database:")
            print(f"   ID: {created[0]}")
            print(f"   Username: {created[1]}")
            print(f"   Full Name: {created[2] or 'N/A'}")
            print(f"   Email: {created[3] or 'N/A'}")
            print(f"   Role: {created[4]}")
            print(f"   Active: {created[5]}")
        else:
            print("❌ User not found after creation!")
            conn.close()
            return False
        
        conn.close()
        print("\n" + "=" * 80)
        print("✅ User created successfully!")
        print("=" * 80)
        return True
        
    except psycopg2.IntegrityError as e:
        print(f"\n❌ Integrity Error: {e}")
        if 'unique constraint' in str(e).lower():
            print("   Username already exists!")
        conn.rollback()
        conn.close()
        return False
    except psycopg2.Error as e:
        print(f"\n❌ Database Error: {e}")
        conn.rollback()
        conn.close()
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_create_user.py <username> <password> [full_name] [email] [role]")
        print("\nExample:")
        print("  python test_create_user.py testuser password123")
        print("  python test_create_user.py testuser password123 'Test User' 'test@example.com' operator")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else None
    email = sys.argv[4] if len(sys.argv) > 4 else None
    role = sys.argv[5] if len(sys.argv) > 5 else 'viewer'
    
    success = test_create_user(username, password, full_name, email, role)
    sys.exit(0 if success else 1)


























