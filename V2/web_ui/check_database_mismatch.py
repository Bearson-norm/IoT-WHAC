#!/usr/bin/env python3
"""
Script untuk cek database mismatch antara Web UI dan DBeaver
"""

import psycopg2
import psycopg2.extras
import os
import subprocess

def check_docker_db():
    """Check database in Docker container"""
    print("=" * 80)
    print("🔍 Checking Database in Docker Container")
    print("=" * 80)
    
    try:
        # Query via Docker
        query = "SELECT id, username, full_name, email, role, is_active, created_at FROM web_users ORDER BY created_at DESC;"
        result = subprocess.run(
            ['docker', 'exec', '-i', 'whac-postgres', 'psql', '-U', 'postgres', '-d', 'whac_master', '-t', '-A', '-F', '|'],
            input=query,
            text=True,
            capture_output=True,
            check=True
        )
        
        lines = [line for line in result.stdout.strip().split('\n') if line.strip() and '|' in line]
        
        print(f"✅ Found {len(lines)} users in Docker database:")
        print()
        print(f"{'ID':<5} {'Username':<15} {'Full Name':<25} {'Email':<30} {'Role':<10}")
        print("-" * 80)
        
        docker_users = []
        for line in lines:
            parts = line.split('|')
            if len(parts) >= 6:
                user_id = parts[0].strip()
                username = parts[1].strip()
                full_name = parts[2].strip() if parts[2].strip() else 'N/A'
                email = parts[3].strip() if parts[3].strip() else 'N/A'
                role = parts[4].strip()
                print(f"{user_id:<5} {username:<15} {full_name:<25} {email:<30} {role:<10}")
                docker_users.append(username)
        
        return docker_users
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error querying Docker database: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return None
    except FileNotFoundError:
        print("❌ Docker command not found!")
        return None

def check_localhost_db():
    """Check database via localhost"""
    print("\n" + "=" * 80)
    print("🔍 Checking Database via Localhost")
    print("=" * 80)
    
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'whac_master',
        'user': 'postgres',
        'password': 'Admin123',
        'port': 5432
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, username, full_name, email, role, is_active, created_at 
            FROM web_users 
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        conn.close()
        
        print(f"✅ Found {len(users)} users in localhost database:")
        print()
        print(f"{'ID':<5} {'Username':<15} {'Full Name':<25} {'Email':<30} {'Role':<10}")
        print("-" * 80)
        
        localhost_users = []
        for user in users:
            print(f"{user['id']:<5} {user['username']:<15} {(user['full_name'] or 'N/A'):<25} {(user['email'] or 'N/A'):<30} {user['role']:<10}")
            localhost_users.append(user['username'])
        
        return localhost_users
        
    except psycopg2.OperationalError as e:
        print(f"❌ Cannot connect to localhost database: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def compare_databases():
    """Compare users in both databases"""
    print("\n" + "=" * 80)
    print("📊 COMPARISON")
    print("=" * 80)
    
    docker_users = check_docker_db()
    localhost_users = check_localhost_db()
    
    if docker_users is None or localhost_users is None:
        print("\n⚠️  Cannot complete comparison due to connection errors")
        return
    
    docker_set = set(docker_users)
    localhost_set = set(localhost_users)
    
    print("\n" + "=" * 80)
    print("🔍 ANALYSIS")
    print("=" * 80)
    
    # Users only in Docker
    only_docker = docker_set - localhost_set
    if only_docker:
        print(f"\n⚠️  Users ONLY in Docker database ({len(only_docker)}):")
        for user in sorted(only_docker):
            print(f"   - {user}")
    
    # Users only in localhost
    only_localhost = localhost_set - docker_set
    if only_localhost:
        print(f"\n⚠️  Users ONLY in localhost database ({len(only_localhost)}):")
        for user in sorted(only_localhost):
            print(f"   - {user}")
    
    # Users in both
    in_both = docker_set & localhost_set
    if in_both:
        print(f"\n✅ Users in BOTH databases ({len(in_both)}):")
        for user in sorted(in_both):
            print(f"   - {user}")
    
    # Summary
    print("\n" + "=" * 80)
    print("💡 KESIMPULAN")
    print("=" * 80)
    
    if docker_set == localhost_set:
        print("✅ Both databases have the same users")
    else:
        print("⚠️  Databases are OUT OF SYNC!")
        print("\n🔧 REKOMENDASI:")
        print("1. Web UI menggunakan database Docker (postgres host)")
        print("2. DBeaver menggunakan database localhost")
        print("3. Perlu sync data antara kedua database")
        print("\nUntuk sync:")
        print("  - Jika user 'Iman' ada di Docker tapi tidak di localhost:")
        print("    → Export dari Docker dan import ke localhost")
        print("  - Jika user 'testuser' ada di localhost tapi tidak di Docker:")
        print("    → Export dari localhost dan import ke Docker")
        print("\nAtau gunakan script sync_users_simple.ps1 untuk sync")

if __name__ == '__main__':
    compare_databases()

