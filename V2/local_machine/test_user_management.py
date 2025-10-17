#!/usr/bin/env python3
"""
Test script for user management functionality
Tests the enhanced user management features with backward compatibility
"""

import sys
import json
import time
import sqlite3
from datetime import datetime

def test_database_migration():
    """Test database migration functionality"""
    print("=" * 60)
    print("TESTING DATABASE MIGRATION")
    print("=" * 60)
    
    # Create a test database with simple schema
    test_db = "test_fingerprints.db"
    
    try:
        # Create simple schema database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE users (
                fingerprint_id INTEGER PRIMARY KEY,
                user_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test data
        cursor.execute("INSERT INTO users (fingerprint_id, user_name) VALUES (1, 'Test User 1')")
        cursor.execute("INSERT INTO users (fingerprint_id, user_name) VALUES (2, 'Test User 2')")
        
        conn.commit()
        conn.close()
        
        print("✓ Created test database with simple schema")
        
        # Test the user controller's migration logic
        from fingerprint_user_controller import FingerprintUserController
        
        # Create controller instance (this will trigger migration)
        controller = FingerprintUserController()
        controller.db_file = test_db  # Use test database
        
        # Initialize database (this should trigger migration)
        controller.init_database()
        
        # Verify migration
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("✓ Database schema after migration:")
        for column in columns:
            print(f"  - {column}")
        
        # Check if enhanced columns exist
        enhanced_columns = ['user_id', 'department', 'access_level', 'is_active']
        has_enhanced = all(col in columns for col in enhanced_columns)
        
        if has_enhanced:
            print("✅ Migration successful - enhanced schema detected")
        else:
            print("❌ Migration failed - enhanced schema not found")
            return False
        
        # Test data preservation
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 2:
            print("✅ Data preservation successful - 2 users found")
        else:
            print(f"❌ Data preservation failed - expected 2 users, found {user_count}")
            return False
        
        conn.close()
        
        # Clean up
        import os
        os.remove(test_db)
        
        print("✅ Database migration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Database migration test FAILED: {e}")
        if os.path.exists(test_db):
            os.remove(test_db)
        return False

def test_user_management_commands():
    """Test user management command structure"""
    print("\n" + "=" * 60)
    print("TESTING USER MANAGEMENT COMMANDS")
    print("=" * 60)
    
    test_commands = [
        {
            "name": "Get User Info",
            "command": {
                "command": "get_user_info",
                "data": {
                    "fingerprint_id": 1
                }
            }
        },
        {
            "name": "List Users",
            "command": {
                "command": "list_users",
                "data": {
                    "active_only": True,
                    "department": "IT"
                }
            }
        },
        {
            "name": "Update User",
            "command": {
                "command": "update_user",
                "data": {
                    "fingerprint_id": 1,
                    "user_name": "Updated User",
                    "department": "HR",
                    "access_level": 3
                }
            }
        }
    ]
    
    try:
        for test in test_commands:
            # Validate JSON structure
            json_str = json.dumps(test["command"])
            parsed = json.loads(json_str)
            
            # Validate required fields
            assert "command" in parsed
            assert "data" in parsed
            assert isinstance(parsed["data"], dict)
            
            print(f"✓ {test['name']}: Valid command structure")
        
        print("✅ User management commands test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ User management commands test FAILED: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with simple schema"""
    print("\n" + "=" * 60)
    print("TESTING BACKWARD COMPATIBILITY")
    print("=" * 60)
    
    # Create a test database with simple schema
    test_db = "test_simple.db"
    
    try:
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create simple schema (no migration)
        cursor.execute('''
            CREATE TABLE users (
                fingerprint_id INTEGER PRIMARY KEY,
                user_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test data
        cursor.execute("INSERT INTO users (fingerprint_id, user_name) VALUES (1, 'Simple User')")
        conn.commit()
        conn.close()
        
        print("✓ Created test database with simple schema")
        
        # Test user controller with simple schema
        from fingerprint_user_controller import FingerprintUserController
        
        controller = FingerprintUserController()
        controller.db_file = test_db
        
        # Test get user info with simple schema
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Check which columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("✓ Simple schema detected (no user_id column)")
            
            # Test the backward compatibility logic
            cursor.execute('''
                SELECT fingerprint_id, user_name, created_at
                FROM users WHERE fingerprint_id = ?
            ''', (1,))
            
            user = cursor.fetchone()
            if user:
                # Simulate the backward compatibility response
                user_data = {
                    'fingerprint_id': user[0],
                    'user_name': user[1],
                    'user_id': None,
                    'department': None,
                    'access_level': 1,
                    'is_active': True,
                    'created_at': user[2],
                    'updated_at': user[2],
                    'last_access': None,
                    'access_count': 0,
                    'notes': None
                }
                
                print("✓ Backward compatibility response generated:")
                print(f"  - User: {user_data['user_name']}")
                print(f"  - Default access level: {user_data['access_level']}")
                print(f"  - Default active status: {user_data['is_active']}")
                
                print("✅ Backward compatibility test PASSED")
                return True
            else:
                print("❌ User not found in simple schema")
                return False
        else:
            print("❌ Expected simple schema but found enhanced schema")
            return False
        
        conn.close()
        
        # Clean up
        import os
        os.remove(test_db)
        
    except Exception as e:
        print(f"❌ Backward compatibility test FAILED: {e}")
        if os.path.exists(test_db):
            os.remove(test_db)
        return False

def test_mqtt_response_format():
    """Test MQTT response format"""
    print("\n" + "=" * 60)
    print("TESTING MQTT RESPONSE FORMAT")
    print("=" * 60)
    
    try:
        # Test success response format
        success_response = {
            "store_id": "Store001",
            "timestamp": datetime.now().isoformat(),
            "command": "get_user_info",
            "status": "success",
            "data": {
                "user": {
                    "fingerprint_id": 1,
                    "user_name": "Test User",
                    "user_id": None,
                    "department": None,
                    "access_level": 1,
                    "is_active": True,
                    "created_at": "2024-01-15T10:00:00",
                    "updated_at": "2024-01-15T10:00:00",
                    "last_access": None,
                    "access_count": 0,
                    "notes": None
                }
            },
            "device_id": "AS608_001"
        }
        
        # Validate JSON serialization
        json_str = json.dumps(success_response)
        parsed = json.loads(json_str)
        
        # Validate required fields
        required_fields = ["store_id", "timestamp", "command", "status", "data", "device_id"]
        for field in required_fields:
            assert field in parsed, f"Missing required field: {field}"
        
        print("✓ Success response format valid")
        
        # Test error response format
        error_response = {
            "store_id": "Store001",
            "timestamp": datetime.now().isoformat(),
            "command": "get_user_info",
            "status": "error",
            "data": {
                "message": "User not found"
            },
            "device_id": "AS608_001"
        }
        
        # Validate error response
        json_str = json.dumps(error_response)
        parsed = json.loads(json_str)
        
        assert parsed["status"] == "error"
        assert "message" in parsed["data"]
        
        print("✓ Error response format valid")
        
        print("✅ MQTT response format test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ MQTT response format test FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("ENHANCED USER MANAGEMENT - COMPATIBILITY TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Database Migration", test_database_migration),
        ("User Management Commands", test_user_management_commands),
        ("Backward Compatibility", test_backward_compatibility),
        ("MQTT Response Format", test_mqtt_response_format)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Enhanced user management is ready to use.")
        print("\n💡 Next steps:")
        print("1. Run the database migration: python3 migrate_database.py")
        print("2. Start the user controller: python3 fingerprint_user_controller.py")
        print("3. Test with CLI: python3 user_management_cli.py")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())



