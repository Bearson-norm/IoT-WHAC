#!/usr/bin/env python3
"""
Fix Admin Password in Docker Container
This script can be run from host or inside Docker container
"""

import subprocess
import sys

def fix_admin_in_docker():
    """Fix admin password by executing SQL in Docker container"""
    print("=" * 60)
    print("Fixing Admin Password in Docker Database")
    print("=" * 60)
    
    # SQL to fix admin password
    sql = """
UPDATE web_users 
SET password_hash = '$2b$12$CSTFKuIf6vyTKPu5PifqVOJs14ULspN8ZuGUdu5yEgFpPh6y9X7me',
    is_active = TRUE,
    login_attempts = 0,
    locked_until = NULL
WHERE username = 'admin';

INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, login_attempts, locked_until)
SELECT 'admin', '$2b$12$CSTFKuIf6vyTKPu5PifqVOJs14ULspN8ZuGUdu5yEgFpPh6y9X7me', 'System Administrator', 'admin@whac.com', 'admin', TRUE, 0, NULL
WHERE NOT EXISTS (SELECT 1 FROM web_users WHERE username = 'admin');

SELECT id, username, is_active, login_attempts, locked_until FROM web_users WHERE username = 'admin';
"""
    
    try:
        print("[*] Executing SQL in Docker container...")
        result = subprocess.run(
            ['docker', 'exec', '-i', 'whac-postgres', 'psql', '-U', 'postgres', '-d', 'whac_master'],
            input=sql,
            text=True,
            capture_output=True,
            check=True
        )
        
        print(result.stdout)
        print("=" * 60)
        print("[OK] Admin password fixed successfully!")
        print("=" * 60)
        print("Login credentials:")
        print("   Username: admin")
        print("   Password: Admin123")
        print("=" * 60)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to execute SQL: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("[ERROR] Docker command not found. Make sure Docker is installed and in PATH.")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = fix_admin_in_docker()
    sys.exit(0 if success else 1)


