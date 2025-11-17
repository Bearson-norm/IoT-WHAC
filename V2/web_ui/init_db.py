#!/usr/bin/env python3
"""
Database Initialization Script
Runs database_setup.sql every time the container starts
"""

import psycopg2
import sys
import time
import os
from pathlib import Path

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'whac_master'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Admin123'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# Path to database setup script
SETUP_SCRIPT = Path('/app/database_setup.sql')

def wait_for_postgres(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready"""
    print("⏳ Waiting for PostgreSQL to be ready...")
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            print("✅ PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"   Attempt {i+1}/{max_retries}: PostgreSQL not ready yet, waiting {delay}s...")
                time.sleep(delay)
            else:
                print(f"❌ Failed to connect to PostgreSQL after {max_retries} attempts")
                print(f"   Error: {e}")
                return False
    return False

def execute_setup_script():
    """Execute the database setup script"""
    if not SETUP_SCRIPT.exists():
        print(f"❌ Setup script not found: {SETUP_SCRIPT}")
        return False
    
    print(f"📄 Reading setup script: {SETUP_SCRIPT}")
    
    try:
        # Read the SQL file
        with open(SETUP_SCRIPT, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Connect to database
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        
        cursor = conn.cursor()
        
        # Execute SQL statements one by one
        # psycopg2.execute() only handles one statement at a time
        # Split script into individual statements
        statements = []
        current_statement = []
        
        # Remove comments and split by semicolons
        for line in sql_script.split('\n'):
            # Remove inline comments
            if '--' in line:
                line = line[:line.index('--')]
            
            stripped = line.strip()
            if not stripped:
                continue
            
            current_statement.append(line)
            
            # If line ends with semicolon, it's the end of a statement
            if stripped.endswith(';'):
                stmt = '\n'.join(current_statement).strip()
                if stmt and stmt != ';':
                    statements.append(stmt)
                current_statement = []
        
        # Add any remaining statement
        if current_statement:
            stmt = '\n'.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
        
        print(f"📊 Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        executed = 0
        skipped = 0
        errors = 0
        
        try:
            for i, statement in enumerate(statements, 1):
                if not statement or statement == ';':
                    continue
                
                try:
                    cursor.execute(statement)
                    executed += 1
                    if i % 5 == 0 or i == len(statements):  # Print every 5 statements
                        print(f"   ✓ Executed {executed}/{len(statements)} statements...")
                except Exception as e:
                    error_msg = str(e).lower()
                    # Some errors are expected (like "already exists"), so we'll continue
                    if any(keyword in error_msg for keyword in ['already exists', 'duplicate', 'conflict', 'does not exist']):
                        skipped += 1
                        # Don't print every skip to reduce noise
                    else:
                        errors += 1
                        if errors <= 3:  # Only print first 3 real errors
                            print(f"   ⚠️  Statement {i} error: {str(e)[:150]}")
            
            conn.commit()
            print(f"✅ Database setup completed!")
            print(f"   ✓ Executed: {executed}")
            if skipped > 0:
                print(f"   ⚠️  Skipped (already exist): {skipped}")
            if errors > 0:
                print(f"   ❌ Errors: {errors}")
        except Exception as e:
            print(f"❌ Fatal error executing statements: {e}")
            conn.rollback()
            raise
        
        # Close cursor from SQL execution
        cursor.close()
        
        # After executing SQL script, ensure admin user exists with correct password
        print("\n[*] Ensuring admin user exists with correct password...")
        try:
            # Reopen connection for admin user fix
            admin_cursor = conn.cursor()
            
            # Check if admin user exists
            admin_cursor.execute("SELECT password_hash FROM web_users WHERE username = 'admin'")
            admin_exists = admin_cursor.fetchone()
            
            # Import bcrypt to generate/verify password
            import bcrypt
            
            # Password hash for 'admin123' - verified working hash
            correct_hash = '$2b$12$7cD0.neGPVGRNL3X9nzY6uc5G1Ek8OB/PBhYDvcjKvZ0mcYK9yOyS'
            test_password = 'admin123'
            
            if admin_exists:
                # Verify current password
                current_hash = admin_exists[0]
                try:
                    is_valid = bcrypt.checkpw(test_password.encode('utf-8'), current_hash.encode('utf-8'))
                    if not is_valid:
                        print("[*] Admin password is incorrect, updating...")
                        admin_cursor.execute("""
                            UPDATE web_users 
                            SET password_hash = %s,
                                is_active = TRUE,
                                login_attempts = 0,
                                locked_until = NULL
                            WHERE username = 'admin'
                        """, (correct_hash,))
                        conn.commit()
                        print("[OK] Admin password updated!")
                    else:
                        print("[OK] Admin password is correct")
                except Exception as verify_error:
                    print(f"[*] Password verification error, updating password...")
                    admin_cursor.execute("""
                        UPDATE web_users 
                        SET password_hash = %s,
                            is_active = TRUE,
                            login_attempts = 0,
                            locked_until = NULL
                        WHERE username = 'admin'
                    """, (correct_hash,))
                    conn.commit()
                    print("[OK] Admin password updated!")
                
                # Ensure account is unlocked and active
                admin_cursor.execute("""
                    UPDATE web_users 
                    SET locked_until = NULL, login_attempts = 0, is_active = TRUE
                    WHERE username = 'admin'
                """)
                conn.commit()
            else:
                print("[*] Admin user not found, creating...")
                admin_cursor.execute("""
                    INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, login_attempts, locked_until)
                    VALUES ('admin', %s, 'System Administrator', 'admin@whac.com', 'admin', TRUE, 0, NULL)
                """, (correct_hash,))
                conn.commit()
                print("[OK] Admin user created!")
            
            admin_cursor.close()
        except Exception as e:
            print(f"[WARNING] Error ensuring admin user: {e}")
            import traceback
            traceback.print_exc()
            # Continue anyway
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error executing setup script: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 Database Initialization Script")
    print("=" * 60)
    
    # Wait for PostgreSQL
    if not wait_for_postgres():
        sys.exit(1)
    
    # Execute setup script
    if not execute_setup_script():
        print("⚠️  Some errors occurred during setup, but continuing...")
    
    print("=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

