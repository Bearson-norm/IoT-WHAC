#!/usr/bin/env python3
"""
Test database connection and table structure
"""

import psycopg2

def test_database():
    """Test database connection and structure"""
    
    print("🔍 Testing Database Connection")
    print("=" * 50)
    
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'whac_master',
        'user': 'postgres',
        'password': 'Admin123',
        'port': 5432
    }
    
    try:
        # Test connection
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connection successful!")
        
        # Test table existence
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'store_001'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ store_001 table exists!")
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'store_001'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            print("📋 Table structure:")
            for col_name, col_type in columns:
                print(f"   - {col_name}: {col_type}")
            
            # Check for finger_template_id column
            has_template_id = any(col[0] == 'finger_template_id' for col in columns)
            if has_template_id:
                print("✅ finger_template_id column exists!")
            else:
                print("❌ finger_template_id column missing!")
                print("💡 Add it with: ALTER TABLE store_001 ADD COLUMN finger_template_id INTEGER;")
            
            # Test insert
            try:
                cursor.execute("""
                    INSERT INTO store_001 (user_id, username, finger_template_id)
                    VALUES (999, 'Test User', 999)
                    ON CONFLICT (user_id) DO NOTHING;
                """)
                conn.commit()
                print("✅ Test insert successful!")
                
                # Clean up test data
                cursor.execute("DELETE FROM store_001 WHERE user_id = 999;")
                conn.commit()
                print("✅ Test data cleaned up!")
                
            except Exception as e:
                print(f"❌ Test insert failed: {e}")
                conn.rollback()
        else:
            print("❌ store_001 table does not exist!")
            print("💡 Create it with the SQL command in the error message above")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print("💡 Check PostgreSQL is running and accessible")

if __name__ == "__main__":
    test_database()

