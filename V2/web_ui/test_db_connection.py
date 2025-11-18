#!/usr/bin/env python3
"""
Script untuk test koneksi database dengan konfigurasi yang sama seperti Web UI
Membantu mengidentifikasi apakah Web UI menggunakan database yang berbeda
"""

import psycopg2
import psycopg2.extras
import os
import sys

def test_connection(host, database, user, password, port, label):
    """Test database connection with specific config"""
    print(f"\n{'='*80}")
    print(f"🔍 Testing: {label}")
    print(f"{'='*80}")
    print(f"Host: {host}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print(f"Port: {port}")
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, username, full_name, email, role, is_active, 
                   created_at, last_login, login_attempts, locked_until
            FROM web_users
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        print(f"✅ Connection successful!")
        print(f"📊 Found {len(users)} users:")
        for user in users:
            print(f"   - ID {user['id']}: {user['username']} ({user['role']})")
        
        return [dict(user) for user in users]
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def main():
    print("="*80)
    print("🔍 Database Connection Test - Web UI Configuration")
    print("="*80)
    
    # Test 1: Default localhost (seperti script debug)
    print("\n[TEST 1] Konfigurasi Default (localhost)")
    users_localhost = test_connection(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'whac_master'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'Admin123'),
        port=int(os.getenv('DB_PORT', '5432')),
        label="Default (localhost)"
    )
    
    # Test 2: Docker configuration (postgres sebagai host)
    print("\n[TEST 2] Konfigurasi Docker (host: postgres)")
    users_docker = test_connection(
        host='postgres',  # Seperti di docker-compose.yml
        database=os.getenv('DB_NAME', 'whac_master'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'Admin123'),
        port=int(os.getenv('DB_PORT', '5432')),
        label="Docker (postgres host)"
    )
    
    # Test 3: Check .env file if exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("\n[TEST 3] Konfigurasi dari .env file")
        # Read .env file
        env_vars = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        users_env = test_connection(
            host=env_vars.get('DB_HOST', 'localhost'),
            database=env_vars.get('DB_NAME', 'whac_master'),
            user=env_vars.get('DB_USER', 'postgres'),
            password=env_vars.get('DB_PASSWORD', 'Admin123'),
            port=int(env_vars.get('DB_PORT', '5432')),
            label="From .env file"
        )
    else:
        print("\n[TEST 3] .env file tidak ditemukan")
        users_env = None
    
    # Compare results
    print("\n" + "="*80)
    print("📊 PERBANDINGAN HASIL:")
    print("="*80)
    
    all_configs = [
        ("Localhost (default)", users_localhost),
        ("Docker (postgres)", users_docker),
        (".env file", users_env)
    ]
    
    for label, users in all_configs:
        if users is not None:
            print(f"\n{label}: {len(users)} users")
            if len(users) == 1:
                print(f"   ⚠️  Hanya 1 user ditemukan: {users[0]['username']}")
            elif len(users) == 5:
                print(f"   ✅ Semua 5 user ditemukan")
            else:
                print(f"   ⚠️  Jumlah user tidak sesuai (harusnya 5)")
        else:
            print(f"\n{label}: ❌ Connection failed")
    
    # Find which config matches API response (1 user)
    print("\n" + "="*80)
    print("💡 KESIMPULAN:")
    print("="*80)
    
    if users_localhost and len(users_localhost) == 5:
        print("✅ Localhost config memiliki semua 5 user")
        print("   Ini adalah konfigurasi yang benar")
    
    if users_docker and len(users_docker) == 1:
        print("⚠️  Docker config (postgres host) hanya memiliki 1 user")
        print("   Kemungkinan Web UI menggunakan konfigurasi ini")
        print("   Web UI mungkin connect ke database yang berbeda!")
    
    if users_env and len(users_env) == 1:
        print("⚠️  .env config hanya memiliki 1 user")
        print("   Web UI mungkin menggunakan konfigurasi dari .env file")
    
    print("\n🔧 REKOMENDASI:")
    print("1. Cek environment variables yang digunakan Web UI")
    print("2. Jika menggunakan Docker, pastikan DB_HOST='postgres'")
    print("3. Jika running lokal, pastikan DB_HOST='localhost'")
    print("4. Pastikan Web UI menggunakan database yang sama dengan DBeaver")
    print("="*80)

if __name__ == '__main__':
    main()

