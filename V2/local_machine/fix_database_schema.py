#!/usr/bin/env python3
"""
Fix Database Schema - Migrate from 'username' to 'user_name'

This script fixes the SQLite database schema to match the correct column names.
Run this if you get error: "table users has no column named username"
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_FILE = "fingerprints.db"
BACKUP_DIR = "database_backups"

def backup_database():
    """Create backup of existing database"""
    if not os.path.exists(DB_FILE):
        print("ℹ️  No database file found, will create new one")
        return None
    
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"fingerprints_{timestamp}.db")
    
    shutil.copy2(DB_FILE, backup_file)
    print(f"✅ Database backed up to: {backup_file}")
    return backup_file

def check_schema():
    """Check current database schema"""
    if not os.path.exists(DB_FILE):
        return None
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        conn.close()
        
        print("\n📋 Current Database Schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        return [col[1] for col in columns]  # Return column names
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return None

def migrate_database():
    """Migrate database from old schema to new schema"""
    print("\n🔄 Starting database migration...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if old schema exists (with 'username' column)
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'username' in columns and 'user_name' not in columns:
            print("📝 Migrating from 'username' to 'user_name'...")
            
            # Create new table with correct schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    fingerprint_id INTEGER NOT NULL,
                    device_id TEXT DEFAULT 'AS608_001',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Copy data from old table to new table
            cursor.execute('''
                INSERT INTO users_new (id, user_name, fingerprint_id, created_at)
                SELECT id, username, fingerprint_id, created_at
                FROM users
            ''')
            
            # Drop old table
            cursor.execute("DROP TABLE users")
            
            # Rename new table
            cursor.execute("ALTER TABLE users_new RENAME TO users")
            
            conn.commit()
            print("✅ Migration completed successfully!")
            
        elif 'user_name' in columns:
            print("✅ Database schema is already correct (has 'user_name' column)")
            
            # Check if device_id column exists
            if 'device_id' not in columns:
                print("📝 Adding 'device_id' column...")
                cursor.execute("ALTER TABLE users ADD COLUMN device_id TEXT DEFAULT 'AS608_001'")
                conn.commit()
                print("✅ Added 'device_id' column")
        else:
            print("⚠️  Unknown schema, creating fresh table...")
            create_fresh_database(cursor)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    
    return True

def create_fresh_database(cursor=None):
    """Create fresh database with correct schema"""
    print("\n🆕 Creating fresh database...")
    
    try:
        if cursor is None:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
        else:
            conn = None
        
        # Drop old table if exists
        cursor.execute("DROP TABLE IF EXISTS users")
        
        # Create new table with correct schema
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                fingerprint_id INTEGER NOT NULL,
                device_id TEXT DEFAULT 'AS608_001',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        if conn:
            conn.commit()
            conn.close()
        
        print("✅ Fresh database created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating fresh database: {e}")
        return False

def verify_schema():
    """Verify the database schema is correct"""
    print("\n🔍 Verifying database schema...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ 'users' table does not exist")
            conn.close()
            return False
        
        # Get column info
        cursor.execute("PRAGMA table_info(users)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        # Check required columns
        required = ['user_name', 'fingerprint_id', 'device_id']
        missing = [col for col in required if col not in columns]
        
        if missing:
            print(f"❌ Missing columns: {', '.join(missing)}")
            conn.close()
            return False
        
        print("✅ Database schema is correct!")
        print("\n📋 Schema:")
        for col_name, col_type in columns.items():
            print(f"  - {col_name} ({col_type})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 Database Schema Fix Tool")
    print("=" * 60)
    
    # Check current schema
    current_columns = check_schema()
    
    # Backup existing database
    if current_columns:
        backup_file = backup_database()
        if backup_file:
            print(f"💾 Backup created: {backup_file}")
    
    # Migrate or create database
    if current_columns is None:
        create_fresh_database()
    else:
        migrate_database()
    
    # Verify final schema
    verify_schema()
    
    print("\n" + "=" * 60)
    print("✅ Database fix completed!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("  1. Restart fingerprint client")
    print("  2. Try enrolling a new user")
    print("  3. Check logs for errors")

if __name__ == "__main__":
    main()

