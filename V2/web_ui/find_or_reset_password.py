#!/usr/bin/env python3
"""
Find or Reset User Password Utility
This script can:
1. Try common passwords to see if any match
2. Reset password to a new one if you can't remember

Usage: 
  python find_or_reset_password.py <username> [--reset] [--password <new_password>]
"""

import psycopg2
import bcrypt
import os
import sys
import argparse

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'whac_master'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Admin123'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        return False

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Common passwords to try
COMMON_PASSWORDS = [
    'admin123',
    'admin',
    'password',
    'password123',
    '123456',
    '12345678',
    'qwerty',
    'abc123',
    'admin@123',
    'Admin123',
    'ADMIN123',
    'whac123',
    'foom123',
    'hilal123',
    'ramadhan123',
    'mamat123',
]

def try_common_passwords(username, password_hash):
    """Try common passwords to see if any match"""
    print("\n" + "=" * 60)
    print("🔍 Mencoba Password Umum...")
    print("=" * 60)
    print("⚠️  PENTING: Password asli TIDAK BISA ditemukan dari hash!")
    print("    Script ini hanya mencoba password umum yang mungkin Anda gunakan.")
    print("=" * 60 + "\n")
    
    found = False
    for i, test_password in enumerate(COMMON_PASSWORDS, 1):
        print(f"[{i}/{len(COMMON_PASSWORDS)}] Mencoba: '{test_password}'...", end=' ')
        if verify_password(test_password, password_hash):
            print("✅ COCOK!")
            print("\n" + "=" * 60)
            print("🎉 PASSWORD DITEMUKAN!")
            print("=" * 60)
            print(f"Username: {username}")
            print(f"Password: {test_password}")
            print("=" * 60)
            found = True
            break
        else:
            print("❌")
    
    if not found:
        print("\n" + "=" * 60)
        print("❌ Tidak ada password umum yang cocok")
        print("=" * 60)
        print("Password asli TIDAK BISA ditemukan dari hash bcrypt.")
        print("Ini adalah fitur keamanan - hash adalah one-way encryption.")
        print("\n💡 Solusi: Reset password ke nilai baru")
        print("=" * 60)
    
    return found

def reset_user_password(username, new_password='password123'):
    """Reset user password"""
    print("\n" + "=" * 60)
    print("🔐 Mereset Password...")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, username, full_name, email, role FROM web_users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User '{username}' tidak ditemukan!")
            conn.close()
            return False
        
        user_id, db_username, full_name, email, role = user
        print(f"✓ User ditemukan: {db_username} ({full_name or 'N/A'})")
        
        # Update password
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
        
        print("✅ Password berhasil direset!")
        print("=" * 60)
        print("Login Credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {new_password}")
        print("=" * 60)
        print("⚠️  Silakan ubah password setelah login!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Find or reset user password',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  # Coba password umum dulu
  python find_or_reset_password.py admin
  
  # Langsung reset password
  python find_or_reset_password.py admin --reset
  
  # Reset dengan password custom
  python find_or_reset_password.py admin --reset --password mynewpass123
        """
    )
    parser.add_argument('username', help='Username yang ingin dicari/reset passwordnya')
    parser.add_argument('--reset', action='store_true', help='Langsung reset password tanpa mencoba password umum')
    parser.add_argument('--password', default='password123', help='Password baru jika menggunakan --reset (default: password123)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔐 Password Recovery Utility")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("""
            SELECT id, username, password_hash, full_name, email, role 
            FROM web_users 
            WHERE username = %s
        """, (args.username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User '{args.username}' tidak ditemukan!")
            print("\nUser yang tersedia:")
            cursor.execute("SELECT username, full_name, email, role FROM web_users ORDER BY username")
            users = cursor.fetchall()
            for u in users:
                print(f"   - {u[0]} ({u[1] or 'N/A'}) - {u[3]}")
            conn.close()
            return 1
        
        user_id, username, password_hash, full_name, email, role = user
        print(f"\n✓ User ditemukan:")
        print(f"   ID: {user_id}")
        print(f"   Username: {username}")
        print(f"   Full Name: {full_name or 'N/A'}")
        print(f"   Email: {email or 'N/A'}")
        print(f"   Role: {role}")
        
        conn.close()
        
        # If reset flag, skip trying passwords
        if args.reset:
            return 0 if reset_user_password(username, args.password) else 1
        
        # Try common passwords first
        found = try_common_passwords(username, password_hash)
        
        if not found:
            print("\n" + "=" * 60)
            response = input("Apakah Anda ingin mereset password? (y/n): ").strip().lower()
            if response == 'y':
                new_password = input("Masukkan password baru (atau tekan Enter untuk 'password123'): ").strip()
                if not new_password:
                    new_password = 'password123'
                return 0 if reset_user_password(username, new_password) else 1
            else:
                print("Password tidak direset.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())














