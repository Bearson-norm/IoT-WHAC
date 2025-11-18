#!/usr/bin/env python3
"""
Script untuk test API endpoint /api/admin/web_users
Membandingkan dengan data langsung dari database
"""

import requests
import json
import psycopg2
import psycopg2.extras
import os
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

def test_api_endpoint(base_url='http://localhost:5000', session_cookie=None):
    """Test API endpoint (requires authentication)"""
    try:
        url = f"{base_url}/api/admin/web_users"
        headers = {}
        if session_cookie:
            headers['Cookie'] = session_cookie
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            print("⚠️  API mengembalikan 403 (Access Denied)")
            print("   Anda perlu login sebagai admin terlebih dahulu")
            return None
        else:
            print(f"❌ API mengembalikan status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Tidak bisa connect ke API. Pastikan Flask app sedang berjalan.")
        return None
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return None

def compare_data():
    """Compare database data with API response"""
    print("=" * 80)
    print("🔍 Test: Perbandingan Data User (Database vs API)")
    print("=" * 80)
    
    # Get data from database
    print("\n[1] Mengambil data langsung dari database...")
    db_users = get_db_users()
    
    if not db_users:
        print("❌ Gagal mengambil data dari database!")
        return
    
    print(f"✅ Ditemukan {len(db_users)} user di database")
    
    # Display database data
    print("\n" + "=" * 80)
    print("📊 DATA DARI DATABASE:")
    print("=" * 80)
    print(f"{'ID':<5} {'Username':<15} {'Full Name':<25} {'Email':<30} {'Role':<10} {'Active':<8}")
    print("-" * 80)
    
    for user in db_users:
        active = 'Yes' if user['is_active'] else 'No'
        print(f"{user['id']:<5} {user['username']:<15} {(user['full_name'] or 'N/A'):<25} {(user['email'] or 'N/A'):<30} {user['role']:<10} {active:<8}")
    
    # Try to get API data
    print("\n" + "=" * 80)
    print("📡 MENGUJI API ENDPOINT:")
    print("=" * 80)
    print("⚠️  Catatan: API memerlukan authentication (login sebagai admin)")
    print("   Jika Anda sudah login, buka browser dan copy session cookie")
    print("   Atau test langsung di browser: http://localhost:5000/api/admin/web_users")
    
    api_users = test_api_endpoint()
    
    if api_users:
        print(f"\n✅ API mengembalikan {len(api_users)} user")
        
        print("\n" + "=" * 80)
        print("📊 DATA DARI API:")
        print("=" * 80)
        print(f"{'ID':<5} {'Username':<15} {'Full Name':<25} {'Email':<30} {'Role':<10} {'Active':<8}")
        print("-" * 80)
        
        for user in api_users:
            active = 'Yes' if user.get('is_active') else 'No'
            print(f"{user.get('id', 'N/A'):<5} {user.get('username', 'N/A'):<15} {(user.get('full_name') or 'N/A'):<25} {(user.get('email') or 'N/A'):<30} {user.get('role', 'N/A'):<10} {active:<8}")
        
        # Compare
        print("\n" + "=" * 80)
        print("🔍 PERBANDINGAN:")
        print("=" * 80)
        
        if len(db_users) != len(api_users):
            print(f"⚠️  JUMLAH USER BERBEDA!")
            print(f"   Database: {len(db_users)} user")
            print(f"   API: {len(api_users)} user")
        else:
            print(f"✅ Jumlah user sama: {len(db_users)} user")
        
        # Check each user
        db_usernames = {u['username']: u for u in db_users}
        api_usernames = {u.get('username'): u for u in api_users if u.get('username')}
        
        missing_in_api = set(db_usernames.keys()) - set(api_usernames.keys())
        missing_in_db = set(api_usernames.keys()) - set(db_usernames.keys())
        
        if missing_in_api:
            print(f"\n⚠️  User yang ada di database tapi TIDAK ada di API:")
            for username in missing_in_api:
                print(f"   - {username} (ID: {db_usernames[username]['id']})")
        
        if missing_in_db:
            print(f"\n⚠️  User yang ada di API tapi TIDAK ada di database:")
            for username in missing_in_db:
                print(f"   - {username}")
        
        if not missing_in_api and not missing_in_db:
            print("\n✅ Semua user ada di kedua tempat")
            
            # Check data consistency
            print("\n🔍 Memeriksa konsistensi data...")
            differences = []
            for username in db_usernames.keys():
                if username in api_usernames:
                    db_user = db_usernames[username]
                    api_user = api_usernames[username]
                    
                    # Check each field
                    fields_to_check = ['id', 'username', 'full_name', 'email', 'role', 'is_active']
                    for field in fields_to_check:
                        db_val = db_user.get(field)
                        api_val = api_user.get(field)
                        
                        # Handle None vs empty string
                        if db_val is None:
                            db_val = ''
                        if api_val is None:
                            api_val = ''
                        
                        if str(db_val) != str(api_val):
                            differences.append({
                                'username': username,
                                'field': field,
                                'database': db_val,
                                'api': api_val
                            })
            
            if differences:
                print("\n⚠️  Perbedaan data ditemukan:")
                for diff in differences:
                    print(f"   User: {diff['username']}, Field: {diff['field']}")
                    print(f"      Database: {diff['database']}")
                    print(f"      API: {diff['api']}")
            else:
                print("✅ Data konsisten antara database dan API")
    else:
        print("\n⚠️  Tidak bisa test API (perlu authentication)")
        print("   Untuk test manual:")
        print("   1. Login ke web UI sebagai admin")
        print("   2. Buka: http://localhost:5000/api/admin/web_users")
        print("   3. Bandingkan dengan data database di atas")
    
    print("\n" + "=" * 80)
    print("💡 TROUBLESHOOTING:")
    print("=" * 80)
    print("Jika data tidak matching:")
    print("1. Clear browser cache (Ctrl+Shift+Delete)")
    print("2. Hard refresh halaman (Ctrl+F5)")
    print("3. Cek console browser untuk error JavaScript (F12)")
    print("4. Cek log Flask app untuk error")
    print("5. Pastikan menggunakan database yang sama")
    print("6. Restart Flask app jika perlu")
    print("=" * 80)

if __name__ == '__main__':
    compare_data()

