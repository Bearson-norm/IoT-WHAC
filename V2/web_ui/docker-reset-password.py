#!/usr/bin/env python3
"""
Reset User Password in Docker Container
Script ini bisa dijalankan dari host machine untuk mereset password user di database Docker

Usage:
  python docker-reset-password.py <username> [new_password]
  python docker-reset-password.py admin
  python docker-reset-password.py admin mynewpassword
  python docker-reset-password.py Mamat
"""

import subprocess
import sys
import bcrypt
import os

# Database configuration (from docker-compose.yml)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'whac_master'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Admin123'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# Container name from docker-compose.yml
POSTGRES_CONTAINER = 'whac-postgres'

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_container_name():
    """Try to find PostgreSQL container name"""
    try:
        # Try common container names
        containers = ['whac-postgres', 'postgres', 'whac_postgres']
        for container in containers:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.stdout.strip():
                return result.stdout.strip()
        
        # If not found, list all containers
        print("⚠️  Container PostgreSQL tidak ditemukan dengan nama standar.")
        print("Mencari container yang tersedia...")
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout.strip():
            print("Container yang tersedia:")
            for name in result.stdout.strip().split('\n'):
                if 'postgres' in name.lower():
                    return name
        
        return None
    except Exception as e:
        print(f"⚠️  Error mencari container: {e}")
        return POSTGRES_CONTAINER  # Default fallback

def reset_password_docker(username, new_password='password123'):
    """Reset user password in Docker database"""
    print("=" * 60)
    print("🔐 Reset Password di Docker Container")
    print("=" * 60)
    
    # Find container
    container_name = get_container_name()
    if not container_name:
        print("❌ Container PostgreSQL tidak ditemukan!")
        print("Pastikan Docker container sudah berjalan:")
        print("   docker ps")
        return False
    
    print(f"✓ Menggunakan container: {container_name}")
    
    try:
        # First, check if user exists
        check_sql = f"""
SELECT id, username, full_name, email, role 
FROM web_users 
WHERE username = '{username}';
"""
        
        print(f"\n[*] Mengecek user '{username}'...")
        result = subprocess.run(
            ['docker', 'exec', '-i', container_name, 'psql', '-U', DB_CONFIG['user'], '-d', DB_CONFIG['database'], '-t', '-A', '-F', '|'],
            input=check_sql,
            text=True,
            capture_output=True,
            check=False
        )
        
        if not result.stdout.strip():
            print(f"❌ User '{username}' tidak ditemukan!")
            print("\n[*] Mencari user yang tersedia...")
            list_sql = "SELECT username, full_name, email, role FROM web_users ORDER BY username;"
            list_result = subprocess.run(
                ['docker', 'exec', '-i', container_name, 'psql', '-U', DB_CONFIG['user'], '-d', DB_CONFIG['database']],
                input=list_sql,
                text=True,
                capture_output=True,
                check=False
            )
            if list_result.stdout:
                print(list_result.stdout)
            return False
        
        # User exists, show info
        user_info = result.stdout.strip().split('|')
        if len(user_info) >= 5:
            print(f"✓ User ditemukan:")
            print(f"   ID: {user_info[0]}")
            print(f"   Username: {user_info[1]}")
            print(f"   Full Name: {user_info[2] or 'N/A'}")
            print(f"   Email: {user_info[3] or 'N/A'}")
            print(f"   Role: {user_info[4]}")
        
        # Generate password hash using Python in web-ui container (has bcrypt installed)
        print(f"\n[*] Membuat password hash untuk '{new_password}'...")
        
        hash_script = f"import bcrypt; print(bcrypt.hashpw('{new_password}'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))"
        
        # Try web-ui container first (definitely has bcrypt)
        web_ui_containers = ['whac-web-ui', 'web-ui', 'whac_web_ui']
        password_hash = None
        
        for web_container in web_ui_containers:
            try:
                result = subprocess.run(
                    ['docker', 'ps', '--filter', f'name={web_container}', '--format', '{{.Names}}'],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5
                )
                if result.stdout.strip():
                    web_container_name = result.stdout.strip()
                    print(f"   Menggunakan container: {web_container_name}")
                    hash_result = subprocess.run(
                        ['docker', 'exec', web_container_name, 'python3', '-c', hash_script],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=10
                    )
                    password_hash = hash_result.stdout.strip()
                    break
            except:
                continue
        
        # Fallback: try postgres container
        if not password_hash:
            try:
                hash_result = subprocess.run(
                    ['docker', 'exec', container_name, 'python3', '-c', hash_script],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10
                )
                password_hash = hash_result.stdout.strip()
            except:
                pass
        
        # Final fallback: generate hash locally
        if not password_hash:
            print("   [*] Python tidak tersedia di container, membuat hash lokal...")
            password_hash = hash_password(new_password)
        
        print(f"✓ Password hash dibuat")
        
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
        result = subprocess.run(
            ['docker', 'exec', '-i', container_name, 'psql', '-U', DB_CONFIG['user'], '-d', DB_CONFIG['database']],
            input=update_sql,
            text=True,
            capture_output=True,
            check=True
        )
        
        print(result.stdout)
        print("=" * 60)
        print("✅ Password berhasil direset!")
        print("=" * 60)
        print("Login Credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {new_password}")
        print("=" * 60)
        print("⚠️  Silakan ubah password setelah login!")
        print("=" * 60)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error menjalankan SQL: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return False
    except FileNotFoundError:
        print("❌ Docker command tidak ditemukan!")
        print("Pastikan Docker sudah terinstall dan ada di PATH.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python docker-reset-password.py <username> [new_password]")
        print("\nContoh:")
        print("  python docker-reset-password.py admin")
        print("  python docker-reset-password.py admin mynewpassword")
        print("  python docker-reset-password.py Mamat")
        print("  python docker-reset-password.py Greyoungter newpass123")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2] if len(sys.argv) > 2 else 'password123'
    
    success = reset_password_docker(username, new_password)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

