#!/usr/bin/env python3
"""
Database Migration Script for WHAC Fingerprint System
Migrates from simple schema to enhanced schema with backward compatibility
"""

import sqlite3
import sys
import os
from datetime import datetime

def backup_database(db_file):
    """Create a backup of the existing database"""
    backup_file = f"{db_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Read the original database
        with open(db_file, 'rb') as original:
            with open(backup_file, 'wb') as backup:
                backup.write(original.read())
        
        print(f"✓ Database backed up to: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"✗ Failed to create backup: {e}")
        return None

def check_current_schema(db_file):
    """Check the current database schema"""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Current users table schema:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        # Check if enhanced columns exist
        column_names = [col[1] for col in columns]
        has_enhanced_schema = 'user_id' in column_names
        
        conn.close()
        
        return has_enhanced_schema, column_names
        
    except Exception as e:
        print(f"Error checking schema: {e}")
        return False, []

def migrate_database(db_file):
    """Migrate database from simple to enhanced schema"""
    try:
        print(f"🔄 Starting database migration for: {db_file}")
        
        # Check if database exists
        if not os.path.exists(db_file):
            print(f"✗ Database file not found: {db_file}")
            return False
        
        # Create backup
        backup_file = backup_database(db_file)
        if not backup_file:
            print("✗ Cannot proceed without backup")
            return False
        
        # Check current schema
        has_enhanced_schema, column_names = check_current_schema(db_file)
        
        if has_enhanced_schema:
            print("✓ Database already has enhanced schema")
            return True
        
        print("📋 Current schema is simple, proceeding with migration...")
        
        # Start migration
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create new table with enhanced schema
        print("📝 Creating enhanced users table...")
        cursor.execute('''
            CREATE TABLE users_new (
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
        
        # Copy existing data
        print("📋 Copying existing user data...")
        cursor.execute('''
            INSERT INTO users_new (fingerprint_id, user_name, created_at)
            SELECT fingerprint_id, user_name, created_at FROM users
        ''')
        
        # Get count of migrated records
        cursor.execute("SELECT COUNT(*) FROM users_new")
        migrated_count = cursor.fetchone()[0]
        print(f"✓ Migrated {migrated_count} user records")
        
        # Drop old table and rename new one
        print("🔄 Replacing old table with enhanced version...")
        cursor.execute('DROP TABLE users')
        cursor.execute('ALTER TABLE users_new RENAME TO users')
        
        # Create verification log table
        print("📝 Creating verification log table...")
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
                store_id TEXT
            )
        ''')
        
        # Create system statistics table
        print("📝 Creating system statistics table...")
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
        
        # Create indexes for better performance
        print("📝 Creating database indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_log_timestamp ON verification_log(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_log_fingerprint_id ON verification_log(fingerprint_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_stats_date ON system_stats(date)')
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully!")
        print(f"📁 Backup saved as: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print(f"💡 You can restore from backup: {backup_file}")
        return False

def verify_migration(db_file):
    """Verify the migration was successful"""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\n📋 Enhanced users table schema:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        # Check if all required columns exist
        column_names = [col[1] for col in columns]
        required_columns = ['fingerprint_id', 'user_name', 'user_id', 'department', 'access_level', 'is_active']
        
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"⚠️  Missing columns: {missing_columns}")
            return False
        
        # Check other tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['users', 'verification_log', 'system_stats']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            print(f"⚠️  Missing tables: {missing_tables}")
            return False
        
        # Test a query
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✓ Users table has {user_count} records")
        
        conn.close()
        
        print("✅ Migration verification successful!")
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("WHAC FINGERPRINT SYSTEM - DATABASE MIGRATION")
    print("=" * 60)
    print("This script migrates the database from simple to enhanced schema")
    print("=" * 60)
    
    # Default database file
    db_file = "fingerprints.db"
    
    # Check if custom database file is provided
    if len(sys.argv) > 1:
        db_file = sys.argv[1]
    
    print(f"📁 Database file: {db_file}")
    
    # Check if database exists
    if not os.path.exists(db_file):
        print(f"✗ Database file not found: {db_file}")
        print("💡 Make sure you're running this from the local_machine directory")
        return 1
    
    # Check current schema
    has_enhanced_schema, column_names = check_current_schema(db_file)
    
    if has_enhanced_schema:
        print("✅ Database already has enhanced schema")
        print("💡 No migration needed")
        return 0
    
    # Ask for confirmation
    print(f"\n⚠️  This will modify the database: {db_file}")
    print("📁 A backup will be created automatically")
    
    confirm = input("\nDo you want to proceed with the migration? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Migration cancelled")
        return 0
    
    # Perform migration
    if migrate_database(db_file):
        # Verify migration
        if verify_migration(db_file):
            print("\n🎉 Database migration completed successfully!")
            print("💡 You can now use the enhanced user management features")
            return 0
        else:
            print("\n⚠️  Migration completed but verification failed")
            return 1
    else:
        print("\n❌ Migration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())


