#!/usr/bin/env python3
"""
Simple script to reset password - no emoji, works on Windows
Usage: python reset_password_simple.py <username> [new_password]
"""

import subprocess
import sys
import bcrypt
import os

# Container name
POSTGRES_CONTAINER = 'whac-postgres'
DB_USER = 'postgres'
DB_NAME = 'whac_master'
DB_PASSWORD = 'Admin123'

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def reset_password(username, new_password='admin123'):
    """Reset user password in Docker database"""
    print("=" * 60)
    print("Reset Password di Docker Container")
    print("=" * 60)
    
    # Check container
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={POSTGRES_CONTAINER}', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        if not result.stdout.strip():
            print(f"[ERROR] Container {POSTGRES_CONTAINER} tidak ditemukan!")
            print("Pastikan Docker container berjalan:")
            print("   docker ps")
            return False
        print(f"[OK] Menggunakan container: {result.stdout.strip()}")
    except:
        print(f"[ERROR] Container {POSTGRES_CONTAINER} tidak ditemukan!")
        return False
    
    # Check if user exists
    check_sql = f"SELECT id, username, full_name, email, role FROM web_users WHERE username = '{username}';"
    try:
        result = subprocess.run(
            ['docker', 'exec', '-i', POSTGRES_CONTAINER, 'psql', '-U', DB_USER, '-d', DB_NAME, '-t', '-A', '-F', '|'],
            input=check_sql,
            text=True,
            capture_output=True,
            check=True
        )
        
        if not result.stdout.strip():
            print(f"[ERROR] User '{username}' tidak ditemukan!")
            print("\nUser yang tersedia:")
            list_sql = "SELECT username, full_name, email, role FROM web_users ORDER BY username;"
            list_result = subprocess.run(
                ['docker', 'exec', '-i', POSTGRES_CONTAINER, 'psql', '-U', DB_USER, '-d', DB_NAME],
                input=list_sql,
                text=True,
                capture_output=True,
                check=True
            )
            if list_result.stdout:
                print(list_result.stdout)
            return False
        
        # User exists
        user_info = result.stdout.strip().split('|')
        if len(user_info) >= 5:
            print(f"[OK] User ditemukan:")
            print(f"   ID: {user_info[0]}")
            print(f"   Username: {user_info[1]}")
            print(f"   Full Name: {user_info[2] or 'N/A'}")
            print(f"   Email: {user_info[3] or 'N/A'}")
            print(f"   Role: {user_info[4]}")
    except Exception as e:
        print(f"[ERROR] Error checking user: {e}")
        return False
    
    # Generate password hash
    print(f"\n[*] Membuat password hash untuk '{new_password}'...")
    password_hash = hash_password(new_password)
    print(f"[OK] Password hash dibuat")
    
    # Update password
    update_sql = f"""
UPDATE web_users 
SET password_hash = '{password_hash}',
    is_active = TRUE,
    locked_until = NULL,
    login_attempts = 0
WHERE username = '{username}';

SELECT id, username, is_active, login_attempts, locked_until 
FROM web_users 
WHERE username = '{username}';
"""
    
    print(f"\n[*] Mereset password...")
    try:
        result = subprocess.run(
            ['docker', 'exec', '-i', POSTGRES_CONTAINER, 'psql', '-U', DB_USER, '-d', DB_NAME],
            input=update_sql,
            text=True,
            capture_output=True,
            check=True
        )
        
        print(result.stdout)
        print("=" * 60)
        print("[OK] Password berhasil direset!")
        print("=" * 60)
        print("Login Credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {new_password}")
        print("=" * 60)
        print("[WARNING] Silakan ubah password setelah login!")
        print("=" * 60)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error menjalankan SQL: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python reset_password_simple.py <username> [new_password]")
        print("\nContoh:")
        print("  python reset_password_simple.py admin")
        print("  python reset_password_simple.py admin admin123")
        print("  python reset_password_simple.py admin passwordbaru123")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2] if len(sys.argv) > 2 else 'admin123'
    
    success = reset_password(username, new_password)
    sys.exit(0 if success else 1)













