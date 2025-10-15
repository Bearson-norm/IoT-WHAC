#!/usr/bin/env python3
"""
Debug script to test enrollment endpoint
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
USERNAME = "admin"  # Your admin username
PASSWORD = "admin"  # Your admin password

def login():
    """Login and get session"""
    session = requests.Session()
    
    # Login
    login_data = {
        'username': USERNAME,
        'password': PASSWORD
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
    
    if response.status_code == 200:
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def test_enrollment(session, user_id, username):
    """Test enrollment endpoint"""
    print(f"\n📝 Testing enrollment with user_id={user_id}, username={username}")
    
    data = {
        'user_id': user_id,
        'username': username
    }
    
    response = session.post(
        f"{BASE_URL}/api/enroll_user",
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"📊 Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"📦 Response: {json.dumps(response_data, indent=2)}")
    except:
        print(f"📦 Response (text): {response.text}")
    
    return response.status_code == 200

def test_next_user_id(session):
    """Test next user ID endpoint"""
    print("\n🔍 Getting next available User ID...")
    
    response = session.get(f"{BASE_URL}/api/next_user_id")
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📦 Next available User ID: {data.get('next_id')}")
        return data.get('next_id')
    else:
        print(f"❌ Error: {response.text}")
        return None

def main():
    """Main test function"""
    print("=" * 60)
    print("ENROLLMENT DEBUG TEST")
    print("=" * 60)
    
    # Login
    session = login()
    if not session:
        print("❌ Cannot proceed without login")
        return
    
    # Get next available User ID
    next_id = test_next_user_id(session)
    
    # Test cases
    test_cases = [
        # Test with empty user_id (should fail with 400)
        {'user_id': None, 'username': 'Test User', 'should_pass': False},
        {'user_id': 0, 'username': 'Test User', 'should_pass': False},
        {'user_id': '', 'username': 'Test User', 'should_pass': False},
        
        # Test with empty username (should fail with 400)
        {'user_id': 99, 'username': None, 'should_pass': False},
        {'user_id': 99, 'username': '', 'should_pass': False},
        
        # Test with valid data (should pass if User ID doesn't exist)
        {'user_id': next_id if next_id else 100, 'username': 'Debug Test User', 'should_pass': True},
    ]
    
    print("\n" + "=" * 60)
    print("RUNNING TEST CASES")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        result = test_enrollment(session, test_case['user_id'], test_case['username'])
        
        if result == test_case['should_pass']:
            print(f"✅ Test {i}: PASSED (Expected: {test_case['should_pass']}, Got: {result})")
        else:
            print(f"❌ Test {i}: FAILED (Expected: {test_case['should_pass']}, Got: {result})")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()


