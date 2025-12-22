#!/usr/bin/env python3
"""
Test Dashboard Stats API
Test the /api/dashboard_stats endpoint directly
"""

import requests
from datetime import datetime

# Configuration
WEB_UI_URL = "http://localhost:5000"
USERNAME = "admin"  # Change to your username
PASSWORD = "admin123"  # Change to your password

def test_dashboard_stats():
    """Test dashboard stats endpoint"""
    
    print("=" * 60)
    print("🧪 Testing Dashboard Stats API")
    print("=" * 60)
    
    # Create session for login
    session = requests.Session()
    
    # Step 1: Login
    print("\n1️⃣  Logging in...")
    login_url = f"{WEB_UI_URL}/login"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = session.post(login_url, data=login_data, allow_redirects=False)
        if response.status_code in [200, 302]:
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return
    
    # Step 2: Get dashboard stats
    print("\n2️⃣  Fetching dashboard stats...")
    stats_url = f"{WEB_UI_URL}/api/dashboard_stats"
    
    try:
        response = session.get(stats_url)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n   📊 Dashboard Stats:")
            print(f"      Total Users: {data.get('total_users', 'N/A')}")
            print(f"      Scans Today: {data.get('total_scans_today', 'N/A')}")
            print(f"      Access Granted: {data.get('successful_access_today', 'N/A')}")
            print(f"      Access Denied: {data.get('denied_access_today', 'N/A')}")
            print(f"      Recent Activity: {len(data.get('recent_activity', []))} records")
            
            # Show raw response
            print("\n   📦 Raw Response:")
            import json
            print(json.dumps(data, indent=2))
            
            print("\n   ✅ Stats fetched successfully")
        else:
            print(f"   ❌ Failed to fetch stats")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error fetching stats: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Check database directly
    print("\n3️⃣  Checking database directly...")
    try:
        import psycopg2
        import psycopg2.extras
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'fingerprint_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check total users
        cursor.execute("SELECT COUNT(*) as count FROM store_001")
        total_users = cursor.fetchone()['count']
        print(f"   Total users in DB: {total_users}")
        
        # Check today's data
        today = datetime.now().date()
        print(f"   Checking data for: {today}")
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM log_data 
            WHERE DATE(timestamp) = %s
        """, (today,))
        scans_today = cursor.fetchone()['count']
        print(f"   Scans today in DB: {scans_today}")
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM log_action 
            WHERE DATE(timestamp) = %s AND granted_denied = 'granted'
        """, (today,))
        granted_today = cursor.fetchone()['count']
        print(f"   Access granted today in DB: {granted_today}")
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM log_action 
            WHERE DATE(timestamp) = %s AND granted_denied = 'denied'
        """, (today,))
        denied_today = cursor.fetchone()['count']
        print(f"   Access denied today in DB: {denied_today}")
        
        # Show sample data
        print("\n   📋 Sample log_data (last 5):")
        cursor.execute("""
            SELECT id, finger_id, confidence, timestamp 
            FROM log_data 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"      ID: {row['id']}, Finger: {row['finger_id']}, "
                  f"Confidence: {row['confidence']}, Time: {row['timestamp']}")
        
        print("\n   📋 Sample log_action (last 5):")
        cursor.execute("""
            SELECT id, user_id, granted_denied, timestamp 
            FROM log_action 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"      ID: {row['id']}, User: {row['user_id']}, "
                  f"Status: {row['granted_denied']}, Time: {row['timestamp']}")
        
        conn.close()
        print("\n   ✅ Database check complete")
        
    except ImportError:
        print("   ⚠️  psycopg2 not installed, skipping database check")
    except Exception as e:
        print(f"   ❌ Database check error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_dashboard_stats()




















