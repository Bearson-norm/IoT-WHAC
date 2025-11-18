#!/usr/bin/env python3
"""
Script untuk melihat informasi user admin dan memverifikasi password
Usage: python check_admin_info.py [username]
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

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        return False

def check_user_info(username='admin'):
    """Check user information and verify password"""
    print("=" * 70)
    print("🔍 Informasi User Admin")
    print("=" * 70)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("""
            SELECT id, username, password_hash, full_name, email, role, 
                   is_active, created_at, last_login, login_attempts, locked_until
            FROM web_users 
            WHERE username = %s
        """, (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User '{username}' tidak ditemukan!")
            print("\n[*] Mencari semua user yang tersedia...")
            cursor.execute("""
                SELECT username, full_name, email, role, is_active 
                FROM web_users 
                ORDER BY username
            """)
            users = cursor.fetchall()
            if users:
                print("\nUser yang tersedia:")
                for u in users:
                    status = "✓ Aktif" if u[4] else "✗ Nonaktif"
                    print(f"   - {u[0]} ({u[1] or 'N/A'}) - {u[3]} - {status}")
            conn.close()
            return False
        
        user_id, db_username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until = user
        
        # Display user information
        print(f"\n✓ User ditemukan:")
        print(f"   ID: {user_id}")
        print(f"   Username: {db_username}")
        print(f"   Full Name: {full_name or 'N/A'}")
        print(f"   Email: {email or 'N/A'}")
        print(f"   Role: {role}")
        print(f"   Status: {'✓ Aktif' if is_active else '✗ Nonaktif'}")
        print(f"   Created At: {created_at}")
        print(f"   Last Login: {last_login or 'Belum pernah login'}")
        print(f"   Login Attempts: {login_attempts}")
        print(f"   Locked Until: {locked_until or 'Tidak terkunci'}")
        
        # Password hash info (first 50 chars for display)
        print(f"\n   Password Hash: {password_hash[:50]}...")
        print(f"   Hash Length: {len(password_hash)} characters")
        
        # Try to verify common passwords
        print("\n" + "=" * 70)
        print("🔐 Verifikasi Password")
        print("=" * 70)
        print("⚠️  PENTING: Password asli TIDAK BISA dibaca dari hash!")
        print("    Script ini hanya memverifikasi apakah password tertentu cocok.\n")
        
        # Common passwords to check
        passwords_to_check = [
            'admin123',
            'admin',
            'Admin123',
            'ADMIN123',
            'password123',
            'password',
            '123456',
        ]
        
        found = False
        for test_password in passwords_to_check:
            print(f"   Mencoba: '{test_password}'...", end=' ')
            if verify_password(test_password, password_hash):
                print("✅ COCOK!")
                print("\n" + "=" * 70)
                print("🎉 PASSWORD DITEMUKAN!")
                print("=" * 70)
                print(f"Username: {db_username}")
                print(f"Password: {test_password}")
                print("=" * 70)
                found = True
                break
            else:
                print("❌")
        
        if not found:
            print("\n" + "=" * 70)
            print("❌ Password umum tidak cocok")
            print("=" * 70)
            print("Password yang digunakan kemungkinan bukan password umum.")
            print("Jika Anda yakin password adalah 'admin123', mungkin hash sudah berubah.")
            print("\n💡 Solusi:")
            print("   1. Reset password menggunakan script reset:")
            print("      python reset_user_password.py admin admin123")
            print("   2. Atau gunakan DBeaver untuk melihat data user")
            print("=" * 70)
        
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error koneksi database: {e}")
        print("\nPastikan:")
        print("   1. Database PostgreSQL sedang berjalan")
        print("   2. Kredensial database benar")
        print("   3. Jika menggunakan Docker, pastikan container berjalan")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    username = sys.argv[1] if len(sys.argv) > 1 else 'admin'
    success = check_user_info(username)
    sys.exit(0 if success else 1)

