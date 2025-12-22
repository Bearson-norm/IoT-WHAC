#!/usr/bin/env python3
"""
Script untuk cek data di database Docker dan sync jika perlu
"""

import subprocess
import sys

def check_docker_db():
    """Check data in Docker database"""
    print("=" * 80)
    print("🔍 Checking Database in Docker Container")
    print("=" * 80)
    
    # Check if container is running
    print("\n[1] Checking if PostgreSQL container is running...")
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=whac-postgres', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            print(f"✅ Container found: {result.stdout.strip()}")
        else:
            print("❌ Container whac-postgres is not running!")
            print("   Start it with: docker-compose up -d postgres")
            return False
    except Exception as e:
        print(f"❌ Error checking container: {e}")
        return False
    
    # Query database
    print("\n[2] Querying web_users table...")
    query = """
    SELECT id, username, full_name, email, role, is_active, created_at, last_login 
    FROM web_users 
    ORDER BY created_at DESC;
    """
    
    try:
        result = subprocess.run(
            ['docker', 'exec', '-i', 'whac-postgres', 'psql', '-U', 'postgres', '-d', 'whac_master', '-c', query],
            capture_output=True,
            text=True,
            check=True
        )
        
        output = result.stdout
        print("\n" + "=" * 80)
        print("📊 DATA DI DATABASE DOCKER:")
        print("=" * 80)
        print(output)
        
        # Count users
        lines = output.strip().split('\n')
        user_count = 0
        for line in lines:
            if '|' in line and not line.startswith('-') and 'id' not in line.lower() and 'rows' not in line.lower():
                user_count += 1
        
        print(f"\n📈 Total users found: {user_count}")
        
        if user_count == 1:
            print("\n⚠️  Hanya 1 user ditemukan di database Docker!")
            print("   Ini menjelaskan mengapa API hanya mengembalikan 1 user.")
            print("\n💡 Solusi: Sync data dari database lokal ke Docker")
            return False
        elif user_count == 5:
            print("\n✅ Semua 5 user ditemukan di database Docker!")
            print("   Masalah mungkin ada di koneksi atau query.")
            return True
        else:
            print(f"\n⚠️  Ditemukan {user_count} user (harusnya 5)")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error querying database: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def sync_data_from_local():
    """Sync data from localhost database to Docker"""
    print("\n" + "=" * 80)
    print("🔄 Sync Data dari Localhost ke Docker")
    print("=" * 80)
    
    print("\n⚠️  PERINGATAN:")
    print("   Script ini akan menyalin data dari database lokal ke Docker.")
    print("   Pastikan data lokal sudah benar dan lengkap.")
    
    response = input("\nLanjutkan? (y/n): ").strip().lower()
    if response != 'y':
        print("Dibatalkan.")
        return
    
    # Export from localhost
    print("\n[1] Exporting data from localhost database...")
    try:
        result = subprocess.run(
            ['pg_dump', '-h', 'localhost', '-U', 'postgres', '-d', 'whac_master', 
             '-t', 'web_users', '--data-only', '--column-inserts'],
            capture_output=True,
            text=True,
            check=True,
            env={**subprocess.os.environ, 'PGPASSWORD': 'Admin123'}
        )
        
        sql_data = result.stdout
        print("✅ Data exported successfully")
        
        # Filter out existing users (ON CONFLICT)
        # We'll insert with ON CONFLICT DO UPDATE
        print("\n[2] Preparing SQL for Docker database...")
        
        # Simple approach: Use INSERT ... ON CONFLICT DO UPDATE
        # But we need to be careful with password hashes
        
        print("\n[3] Inserting/updating data in Docker database...")
        
        # For now, just show what would be done
        print("\n💡 Untuk sync data, gunakan salah satu metode berikut:")
        print("\n   Metode 1: Export dan Import")
        print("   pg_dump -h localhost -U postgres -d whac_master -t web_users --data-only > web_users_backup.sql")
        print("   docker exec -i whac-postgres psql -U postgres -d whac_master < web_users_backup.sql")
        
        print("\n   Metode 2: Manual INSERT dengan ON CONFLICT")
        print("   (Lihat file sync_users_to_docker.sql)")
        
    except FileNotFoundError:
        print("❌ pg_dump tidak ditemukan!")
        print("   Install PostgreSQL client tools terlebih dahulu.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    has_all_users = check_docker_db()
    
    if not has_all_users:
        print("\n" + "=" * 80)
        response = input("Apakah Anda ingin sync data dari database lokal? (y/n): ").strip().lower()
        if response == 'y':
            sync_data_from_local()
    
    print("\n" + "=" * 80)


























