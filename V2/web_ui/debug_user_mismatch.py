#!/usr/bin/env python3
"""
Script untuk debug masalah data user yang tidak matching antara Web UI dan database
"""

import psycopg2
import psycopg2.extras
import os
import json
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'whac_master'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Admin123'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

def get_db_users():
    """Get users directly from database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, username, full_name, email, role, is_active, 
                   created_at, last_login, login_attempts, locked_until
            FROM web_users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        conn.close()
        return [dict(user) for user in users]
    except Exception as e:
        print(f"❌ Error getting users from database: {e}")
        return None

def compare_data():
    """Compare database data with what API should return"""
    print("=" * 80)
    print("🔍 Debug: Perbandingan Data User")
    print("=" * 80)
    
    # Get data from database
    print("\n[1] Mengambil data langsung dari database...")
    db_users = get_db_users()
    
    if not db_users:
        print("❌ Gagal mengambil data dari database!")
        return
    
    print(f"✅ Ditemukan {len(db_users)} user di database\n")
    
    # Display database data
    print("=" * 80)
    print("📊 DATA DARI DATABASE (web_users table):")
    print("=" * 80)
    print(f"{'ID':<5} {'Username':<15} {'Full Name':<25} {'Email':<30} {'Role':<10} {'Active':<8} {'Last Login':<20}")
    print("-" * 80)
    
    for user in db_users:
        last_login = user['last_login'].strftime('%Y-%m-%d %H:%M:%S') if user['last_login'] else 'Never'
        active = 'Yes' if user['is_active'] else 'No'
        print(f"{user['id']:<5} {user['username']:<15} {(user['full_name'] or 'N/A'):<25} {(user['email'] or 'N/A'):<30} {user['role']:<10} {active:<8} {last_login:<20}")
    
    # Show what API should return
    print("\n" + "=" * 80)
    print("📡 DATA YANG SEHARUSNYA DIKEMBALIKAN API (/api/admin/web_users):")
    print("=" * 80)
    
    # Simulate API response (same query as in app.py)
    api_users = []
    for user in db_users:
        api_user = {
            'id': user['id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'email': user['email'],
            'role': user['role'],
            'is_active': user['is_active'],
            'created_at': user['created_at'].isoformat() if user['created_at'] else None,
            'last_login': user['last_login'].isoformat() if user['last_login'] else None,
            'login_attempts': user['login_attempts'],
            'locked_until': user['locked_until'].isoformat() if user['locked_until'] else None
        }
        api_users.append(api_user)
    
    print(json.dumps(api_users, indent=2, default=str))
    
    # Check for potential issues
    print("\n" + "=" * 80)
    print("🔍 ANALISIS POTENSI MASALAH:")
    print("=" * 80)
    
    issues = []
    
    # Check for duplicate usernames
    usernames = [u['username'] for u in db_users]
    if len(usernames) != len(set(usernames)):
        issues.append("⚠️  Ada username duplikat!")
    
    # Check for null values
    for user in db_users:
        if not user['username']:
            issues.append(f"⚠️  User ID {user['id']} tidak memiliki username!")
        if not user['role']:
            issues.append(f"⚠️  User ID {user['id']} ({user['username']}) tidak memiliki role!")
    
    # Check database connection config
    print("\n📋 Konfigurasi Database:")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Database: {DB_CONFIG['database']}")
    print(f"   User: {DB_CONFIG['user']}")
    print(f"   Port: {DB_CONFIG['port']}")
    
    if issues:
        print("\n⚠️  Masalah yang ditemukan:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ Tidak ada masalah yang terdeteksi di data database")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("💡 REKOMENDASI:")
    print("=" * 80)
    print("1. Pastikan Web UI menggunakan koneksi database yang sama")
    print("2. Cek apakah ada caching di browser (clear cache atau hard refresh)")
    print("3. Cek console browser untuk error JavaScript")
    print("4. Cek log aplikasi Flask untuk error")
    print("5. Pastikan API endpoint /api/admin/web_users mengembalikan data yang sama")
    print("\nUntuk test API endpoint, buka di browser:")
    print("   http://localhost:5000/api/admin/web_users")
    print("   (perlu login sebagai admin dulu)")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    compare_data()


























