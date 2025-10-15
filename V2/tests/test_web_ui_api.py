#!/usr/bin/env python3
"""
Test Web UI API endpoint directly
"""

import requests
import json

def test_enrollment_api():
    """Test the enrollment API endpoint"""
    
    print("🔍 Testing Web UI Enrollment API")
    print("=" * 50)
    
    # Test data
    test_data = {
        "user_id": 99,  # Use a high number to avoid conflicts
        "username": "API Test User"
    }
    
    print(f"📤 Sending test enrollment request...")
    print(f"   Data: {test_data}")
    
    try:
        # Send POST request to enrollment endpoint
        response = requests.post(
            "http://localhost:5000/api/enroll_user",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"📥 Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print(f"📥 Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ API call successful!")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Web UI server not running on localhost:5000")
        print("💡 Make sure to start the web UI: cd web_ui && python3 app.py")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_enrollment_api()

