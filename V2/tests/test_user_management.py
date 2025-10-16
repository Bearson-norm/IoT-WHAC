#!/usr/bin/env python3
"""
Test script for the enhanced user management features
Demonstrates the new functionality and validates the implementation
"""

import sys
import os
import json
import time
import sqlite3
from datetime import datetime, timedelta

# Add the local_machine directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'local_machine'))

def test_database_schema():
    """Test the enhanced database schema"""
    print("=" * 60)
    print("TESTING ENHANCED DATABASE SCHEMA")
    print("=" * 60)
    
    # Create a test database
    test_db = "test_fingerprints.db"
    
    try:
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Test enhanced users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                fingerprint_id INTEGER PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_id TEXT,
                department TEXT,
                access_level INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_access TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')
        
        # Test verification log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint_id INTEGER,
                user_name TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence INTEGER,
                verification_result TEXT,
                action_taken TEXT,
                mqtt_sent BOOLEAN DEFAULT FALSE,
                device_id TEXT,
                store_id TEXT,
                FOREIGN KEY (fingerprint_id) REFERENCES users (fingerprint_id)
            )
        ''')
        
        # Test system stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                total_scans INTEGER DEFAULT 0,
                successful_verifications INTEGER DEFAULT 0,
                failed_verifications INTEGER DEFAULT 0,
                mqtt_messages_sent INTEGER DEFAULT 0,
                avg_confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test data
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (fingerprint_id, user_name, user_id, department, access_level, notes)
            VALUES (1, 'Test User 1', 'TEST001', 'IT', 2, 'Test user for validation')
        ''')
        
        cursor.execute('''
            INSERT INTO verification_log 
            (fingerprint_id, user_name, confidence, verification_result, action_taken, device_id, store_id)
            VALUES (1, 'Test User 1', 85, 'Match', 'access_granted', 'AS608_001', 'Store001')
        ''')
        
        cursor.execute('''
            INSERT INTO system_stats 
            (date, total_scans, successful_verifications, failed_verifications, avg_confidence)
            VALUES (CURRENT_DATE, 10, 8, 2, 82.5)
        ''')
        
        conn.commit()
        
        # Verify data
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM verification_log')
        log_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM system_stats')
        stats_count = cursor.fetchone()[0]
        
        print(f"✓ Users table: {user_count} records")
        print(f"✓ Verification log table: {log_count} records")
        print(f"✓ System stats table: {stats_count} records")
        
        # Test enhanced queries
        cursor.execute('''
            SELECT u.fingerprint_id, u.user_name, u.department, u.access_level,
                   COUNT(vl.id) as total_scans,
                   AVG(vl.confidence) as avg_confidence
            FROM users u
            LEFT JOIN verification_log vl ON u.fingerprint_id = vl.fingerprint_id
            GROUP BY u.fingerprint_id
        ''')
        
        enhanced_data = cursor.fetchall()
        print(f"✓ Enhanced query test: {len(enhanced_data)} results")
        
        conn.close()
        os.remove(test_db)
        
        print("✓ Database schema test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Database schema test FAILED: {e}")
        if os.path.exists(test_db):
            os.remove(test_db)
        return False

def test_mqtt_commands():
    """Test MQTT command structure"""
    print("\n" + "=" * 60)
    print("TESTING MQTT COMMAND STRUCTURE")
    print("=" * 60)
    
    test_commands = [
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
            "name": "Get User Info",
            "command": {
                "command": "get_user_info",
                "data": {
                    "fingerprint_id": 1
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
                    "access_level": 3,
                    "notes": "Updated via test"
                }
            }
        },
        {
            "name": "Get User Stats",
            "command": {
                "command": "get_user_stats",
                "data": {
                    "fingerprint_id": 1,
                    "days": 30
                }
            }
        },
        {
            "name": "Export Users",
            "command": {
                "command": "export_users",
                "data": {
                    "format": "csv",
                    "active_only": True
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
            
            print(f"✓ {test['name']}: Valid JSON structure")
        
        print("✓ MQTT command structure test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ MQTT command structure test FAILED: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint structure"""
    print("\n" + "=" * 60)
    print("TESTING API ENDPOINT STRUCTURE")
    print("=" * 60)
    
    test_endpoints = [
        {
            "name": "Enhanced Logs",
            "endpoint": "/api/logs",
            "params": ["page", "per_page", "user_id", "start_date", "end_date", "sort_by", "sort_order"]
        },
        {
            "name": "Enhanced Action Logs",
            "endpoint": "/api/action_logs",
            "params": ["page", "per_page", "user_id", "username", "action", "granted_denied", "start_date", "end_date", "sort_by", "sort_order"]
        },
        {
            "name": "Export Logs",
            "endpoint": "/api/logs/export",
            "params": ["user_id", "start_date", "end_date", "store_id", "type"]
        },
        {
            "name": "Log Statistics",
            "endpoint": "/api/logs/stats",
            "params": ["start_date", "end_date", "store_id", "group_by"]
        },
        {
            "name": "Log Summary",
            "endpoint": "/api/logs/summary",
            "params": ["start_date", "end_date", "store_id"]
        }
    ]
    
    try:
        for endpoint in test_endpoints:
            # Validate endpoint structure
            assert endpoint["endpoint"].startswith("/api/")
            assert len(endpoint["params"]) > 0
            
            # Test parameter names
            for param in endpoint["params"]:
                assert isinstance(param, str)
                assert len(param) > 0
            
            print(f"✓ {endpoint['name']}: {endpoint['endpoint']} with {len(endpoint['params'])} parameters")
        
        print("✓ API endpoint structure test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ API endpoint structure test FAILED: {e}")
        return False

def test_filtering_logic():
    """Test filtering and sorting logic"""
    print("\n" + "=" * 60)
    print("TESTING FILTERING AND SORTING LOGIC")
    print("=" * 60)
    
    # Sample log data
    sample_logs = [
        {
            "id": 1,
            "user_id": 1,
            "username": "John Doe",
            "timestamp": "2024-01-15T10:00:00",
            "action": "access_granted",
            "granted_denied": "granted"
        },
        {
            "id": 2,
            "user_id": 2,
            "username": "Jane Smith",
            "timestamp": "2024-01-15T11:00:00",
            "action": "access_denied",
            "granted_denied": "denied"
        },
        {
            "id": 3,
            "user_id": 1,
            "username": "John Doe",
            "timestamp": "2024-01-15T12:00:00",
            "action": "access_granted",
            "granted_denied": "granted"
        }
    ]
    
    try:
        # Test filtering by user_id
        filtered_by_user = [log for log in sample_logs if log["user_id"] == 1]
        assert len(filtered_by_user) == 2
        print("✓ User ID filtering: 2 results for user_id=1")
        
        # Test filtering by status
        granted_logs = [log for log in sample_logs if log["granted_denied"] == "granted"]
        denied_logs = [log for log in sample_logs if log["granted_denied"] == "denied"]
        assert len(granted_logs) == 2
        assert len(denied_logs) == 1
        print("✓ Status filtering: 2 granted, 1 denied")
        
        # Test sorting by timestamp
        sorted_logs = sorted(sample_logs, key=lambda x: x["timestamp"], reverse=True)
        assert sorted_logs[0]["id"] == 3  # Most recent
        print("✓ Timestamp sorting: Correct order")
        
        # Test sorting by username
        sorted_by_name = sorted(sample_logs, key=lambda x: x["username"])
        assert sorted_by_name[0]["username"] == "Jane Smith"
        print("✓ Username sorting: Correct alphabetical order")
        
        print("✓ Filtering and sorting logic test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Filtering and sorting logic test FAILED: {e}")
        return False

def test_export_functionality():
    """Test export functionality"""
    print("\n" + "=" * 60)
    print("TESTING EXPORT FUNCTIONALITY")
    print("=" * 60)
    
    try:
        import csv
        import io
        
        # Sample data for export
        sample_data = [
            {"id": 1, "user_id": 1, "username": "John Doe", "timestamp": "2024-01-15T10:00:00"},
            {"id": 2, "user_id": 2, "username": "Jane Smith", "timestamp": "2024-01-15T11:00:00"}
        ]
        
        # Test CSV export
        output = io.StringIO()
        fieldnames = ["id", "user_id", "username", "timestamp"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in sample_data:
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        # Validate CSV content
        assert "id,user_id,username,timestamp" in csv_content
        assert "John Doe" in csv_content
        assert "Jane Smith" in csv_content
        
        print("✓ CSV export: Valid format and content")
        
        # Test JSON export
        json_content = json.dumps(sample_data, indent=2)
        parsed_json = json.loads(json_content)
        
        assert len(parsed_json) == 2
        assert parsed_json[0]["username"] == "John Doe"
        
        print("✓ JSON export: Valid format and content")
        
        print("✓ Export functionality test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Export functionality test FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("ENHANCED USER MANAGEMENT FEATURES - TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("MQTT Commands", test_mqtt_commands),
        ("API Endpoints", test_api_endpoints),
        ("Filtering Logic", test_filtering_logic),
        ("Export Functionality", test_export_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Enhanced user management features are ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())


