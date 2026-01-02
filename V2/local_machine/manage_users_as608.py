#!/usr/bin/env python3
"""
Program Manajemen User untuk Sensor AS608
Mengelola user yang tersimpan di sensor AS608 pada port ttySerial 0 (/dev/serial0)
"""

import serial
import adafruit_fingerprint
import sqlite3
import time
import sys
import os
from datetime import datetime
from config import *

# Konfigurasi
SENSOR_PORT = "/dev/serial0"  # ttySerial 0
DB_FILE = "fingerprints_multi.db"  # Database untuk menyimpan info user


class AS608UserManager:
    """Kelas untuk mengelola user di sensor AS608"""
    
    def __init__(self, port=SENSOR_PORT, db_file=DB_FILE):
        self.port = port
        self.db_file = db_file
        self.uart = None
        self.finger = None
        self.connected = False
        self.init_database()
    
    def init_database(self):
        """Inisialisasi database SQLite untuk menyimpan info user"""
        try:
            conn = sqlite3.connect(self.db_file, timeout=10.0)
            cursor = conn.cursor()
            
            # Buat tabel users jika belum ada
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    fingerprint_id INTEGER NOT NULL UNIQUE,
                    device_id TEXT DEFAULT 'AS608_001',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"✓ Database initialized: {self.db_file}")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
    
    def connect_sensor(self, retries=3):
        """Menghubungkan ke sensor AS608"""
        for attempt in range(retries):
            try:
                print(f"🔌 Menghubungkan ke sensor AS608 pada {self.port} (percobaan {attempt + 1}/{retries})...")
                
                # Cek apakah port ada
                if not os.path.exists(self.port):
                    print(f"❌ Port {self.port} tidak ditemukan!")
                    return False
                
                self.uart = serial.Serial(self.port, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)  # Beri waktu sensor untuk stabil
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                
                # Test koneksi dengan membaca template
                if self.finger.read_templates() == adafruit_fingerprint.OK:
                    template_count = self.finger.template_count
                    print(f"✅ Sensor terhubung! Template tersimpan: {template_count}")
                    self.connected = True
                    return True
                else:
                    raise Exception("Gagal membaca template dari sensor")
                    
            except serial.SerialException as e:
                error_msg = str(e)
                if "Permission denied" in error_msg or "could not open port" in error_msg.lower():
                    print(f"❌ Port {self.port} sedang digunakan atau tidak memiliki izin akses")
                    print("💡 Coba jalankan dengan sudo atau tambahkan user ke grup dialout:")
                    print("   sudo usermod -a -G dialout $USER")
                    return False
                print(f"❌ Percobaan {attempt + 1} gagal: {e}")
                if self.uart:
                    try:
                        self.uart.close()
                    except:
                        pass
                    self.uart = None
                if attempt < retries - 1:
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                if self.uart:
                    try:
                        self.uart.close()
                    except:
                        pass
                    self.uart = None
                if attempt < retries - 1:
                    time.sleep(2)
        
        self.connected = False
        return False
    
    def disconnect(self):
        """Memutus koneksi dari sensor"""
        self.connected = False
        if self.uart:
            try:
                self.uart.close()
                print("✓ Koneksi serial ditutup")
            except:
                pass
            self.uart = None
        self.finger = None
    
    def get_sensor_info(self):
        """Mendapatkan informasi sensor"""
        try:
            if not self.connected or not self.finger:
                return None
            
            if self.finger.read_templates() == adafruit_fingerprint.OK:
                return {
                    "template_count": self.finger.template_count,
                    "status_register": self.finger.status_reg,
                    "system_id": self.finger.sys_id,
                    "library_size": self.finger.library_size,
                    "security_level": self.finger.security_level,
                    "device_address": hex(self.finger.device_addr),
                    "packet_size": self.finger.packet_size,
                    "baud_rate": self.finger.baud_rate
                }
            return None
        except Exception as e:
            print(f"❌ Error getting sensor info: {e}")
            return None
    
    def list_users_from_sensor(self):
        """Mendapatkan daftar semua fingerprint yang tersimpan di sensor"""
        users = []
        try:
            if not self.connected or not self.finger:
                print("❌ Sensor tidak terhubung")
                return users
            
            # Baca template count
            if self.finger.read_templates() != adafruit_fingerprint.OK:
                print("❌ Gagal membaca template dari sensor")
                return users
            
            print(f"🔍 Memindai fingerprint di sensor (maksimal 128 slot)...")
            
            # Scan semua slot (1-128)
            for slot in range(1, 129):
                try:
                    # Coba load template dari slot ini
                    result = self.finger.load_model(slot)
                    if result == adafruit_fingerprint.OK:
                        # Template ada di slot ini
                        users.append(slot)
                except:
                    continue
            
            return sorted(users)
            
        except Exception as e:
            print(f"❌ Error listing users: {e}")
            return users
    
    def list_users_from_database(self):
        """Mendapatkan daftar user dari database"""
        try:
            conn = sqlite3.connect(self.db_file, timeout=10.0)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT fingerprint_id, user_name, device_id, created_at 
                FROM users 
                ORDER BY fingerprint_id
            ''')
            users = cursor.fetchall()
            conn.close()
            return users
        except Exception as e:
            print(f"❌ Error reading database: {e}")
            return []
    
    def get_user_name(self, fingerprint_id):
        """Mendapatkan nama user dari database berdasarkan fingerprint_id"""
        try:
            conn = sqlite3.connect(self.db_file, timeout=10.0)
            cursor = conn.cursor()
            cursor.execute('SELECT user_name FROM users WHERE fingerprint_id = ?', (fingerprint_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else f"User_{fingerprint_id}"
        except:
            return f"User_{fingerprint_id}"
    
    def display_users(self):
        """Menampilkan daftar semua user"""
        print("\n" + "=" * 70)
        print("DAFTAR USER DI SENSOR AS608")
        print("=" * 70)
        
        # Dapatkan user dari sensor
        sensor_users = self.list_users_from_sensor()
        
        # Dapatkan user dari database
        db_users = self.list_users_from_database()
        
        # Buat mapping fingerprint_id -> user_name
        user_map = {row[0]: row[1] for row in db_users}
        
        if not sensor_users:
            print("📭 Tidak ada user yang tersimpan di sensor")
        else:
            print(f"📊 Total user di sensor: {len(sensor_users)}")
            print(f"\n{'No':<5} {'ID':<8} {'Nama User':<30} {'Status':<15}")
            print("-" * 70)
            
            for idx, fingerprint_id in enumerate(sensor_users, 1):
                user_name = user_map.get(fingerprint_id, f"User_{fingerprint_id}")
                status = "✓ Terdaftar" if fingerprint_id in user_map else "⚠ Belum diberi nama"
                print(f"{idx:<5} {fingerprint_id:<8} {user_name:<30} {status:<15}")
        
        print("=" * 70)
        return sensor_users
    
    def enroll_user(self, fingerprint_id=None, user_name=None):
        """Mendaftarkan user baru ke sensor"""
        try:
            if not self.connected or not self.finger:
                print("❌ Sensor tidak terhubung")
                return False
            
            # Tentukan fingerprint_id jika tidak diberikan
            if fingerprint_id is None:
                sensor_users = self.list_users_from_sensor()
                # Cari slot kosong pertama
                for slot in range(1, 129):
                    if slot not in sensor_users:
                        fingerprint_id = slot
                        break
                
                if fingerprint_id is None:
                    print("❌ Sensor penuh! Tidak ada slot kosong (maksimal 128)")
                    return False
            else:
                # Cek apakah slot sudah terisi
                result = self.finger.load_model(fingerprint_id)
                if result == adafruit_fingerprint.OK:
                    print(f"⚠️  Slot {fingerprint_id} sudah terisi!")
                    overwrite = input("Apakah Anda ingin menimpa? (y/N): ").strip().lower()
                    if overwrite != 'y':
                        print("❌ Enrollment dibatalkan")
                        return False
                    # Hapus template lama
                    self.finger.delete_model(fingerprint_id)
            
            # Minta nama user jika tidak diberikan
            if user_name is None:
                user_name = input(f"Masukkan nama user untuk ID {fingerprint_id}: ").strip()
                if not user_name:
                    user_name = f"User_{fingerprint_id}"
            
            print(f"\n📝 Mendaftarkan user: {user_name} (ID: {fingerprint_id})")
            print("=" * 70)
            
            # Langkah 1: Scan pertama
            print("1️⃣  Letakkan jari pada sensor untuk scan pertama...")
            start_time = time.time()
            timeout = 30
            
            while True:
                if time.time() - start_time > timeout:
                    print(f"❌ Timeout: Tidak ada jari terdeteksi dalam {timeout} detik")
                    return False
                
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                elif i == adafruit_fingerprint.NOFINGER:
                    time.sleep(0.1)
                    continue
                else:
                    print(f"❌ Error mengambil gambar: {i}")
                    return False
            
            print("✓ Gambar pertama berhasil diambil")
            
            # Konversi ke template
            if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
                print("❌ Error mengkonversi gambar pertama ke template")
                return False
            
            print("✓ Template pertama dibuat")
            print("\n2️⃣  Angkat jari dari sensor...")
            time.sleep(2)
            
            # Tunggu jari diangkat
            start_time = time.time()
            while self.finger.get_image() != adafruit_fingerprint.NOFINGER:
                if time.time() - start_time > 10:
                    print("⚠️  Jari masih terdeteksi, melanjutkan...")
                    break
                time.sleep(0.1)
            
            print("✓ Jari diangkat")
            
            # Langkah 2: Scan kedua
            print("\n3️⃣  Letakkan jari yang sama lagi untuk scan kedua...")
            start_time = time.time()
            
            while True:
                if time.time() - start_time > timeout:
                    print(f"❌ Timeout: Tidak ada jari terdeteksi dalam {timeout} detik")
                    return False
                
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    break
                elif i == adafruit_fingerprint.NOFINGER:
                    time.sleep(0.1)
                    continue
                else:
                    print(f"❌ Error mengambil gambar: {i}")
                    return False
            
            print("✓ Gambar kedua berhasil diambil")
            
            # Konversi ke template
            if self.finger.image_2_tz(2) != adafruit_fingerprint.OK:
                print("❌ Error mengkonversi gambar kedua ke template")
                return False
            
            print("✓ Template kedua dibuat")
            
            # Buat model dari kedua template
            print("\n4️⃣  Membuat model fingerprint...")
            if self.finger.create_model() != adafruit_fingerprint.OK:
                print("❌ Error membuat model - jari mungkin tidak cocok")
                print("💡 Pastikan menggunakan jari yang sama untuk kedua scan")
                return False
            
            print("✓ Model fingerprint berhasil dibuat")
            
            # Simpan model ke sensor
            print(f"\n5️⃣  Menyimpan model ke slot {fingerprint_id}...")
            if self.finger.store_model(fingerprint_id) != adafruit_fingerprint.OK:
                print("❌ Error menyimpan model ke sensor")
                return False
            
            print("✓ Model berhasil disimpan ke sensor")
            
            # Simpan ke database
            try:
                conn = sqlite3.connect(self.db_file, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (fingerprint_id, user_name, device_id, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (fingerprint_id, user_name, 'AS608_001', datetime.now()))
                conn.commit()
                conn.close()
                print("✓ Data user disimpan ke database")
            except Exception as e:
                print(f"⚠️  Warning: Gagal menyimpan ke database: {e}")
            
            print("\n" + "=" * 70)
            print(f"✅ User berhasil didaftarkan!")
            print(f"   Nama: {user_name}")
            print(f"   ID: {fingerprint_id}")
            print("=" * 70)
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n❌ Enrollment dibatalkan oleh user")
            return False
        except Exception as e:
            print(f"❌ Error selama enrollment: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_user(self, fingerprint_id):
        """Menghapus user dari sensor dan database"""
        try:
            if not self.connected or not self.finger:
                print("❌ Sensor tidak terhubung")
                return False
            
            # Cek apakah user ada
            result = self.finger.load_model(fingerprint_id)
            if result != adafruit_fingerprint.OK:
                print(f"❌ User dengan ID {fingerprint_id} tidak ditemukan di sensor")
                return False
            
            # Tampilkan info user
            user_name = self.get_user_name(fingerprint_id)
            print(f"\n⚠️  Akan menghapus user:")
            print(f"   ID: {fingerprint_id}")
            print(f"   Nama: {user_name}")
            
            confirm = input("\nApakah Anda yakin? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Penghapusan dibatalkan")
                return False
            
            # Hapus dari sensor
            if self.finger.delete_model(fingerprint_id) != adafruit_fingerprint.OK:
                print(f"❌ Gagal menghapus user dari sensor")
                return False
            
            print(f"✓ User dihapus dari sensor")
            
            # Hapus dari database
            try:
                conn = sqlite3.connect(self.db_file, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE fingerprint_id = ?', (fingerprint_id,))
                conn.commit()
                conn.close()
                print(f"✓ User dihapus dari database")
            except Exception as e:
                print(f"⚠️  Warning: Gagal menghapus dari database: {e}")
            
            print(f"\n✅ User {user_name} (ID: {fingerprint_id}) berhasil dihapus")
            return True
            
        except Exception as e:
            print(f"❌ Error menghapus user: {e}")
            return False
    
    def sync_database(self):
        """Sinkronisasi database dengan sensor (update database berdasarkan sensor)"""
        try:
            print("\n🔄 Sinkronisasi database dengan sensor...")
            
            # Dapatkan user dari sensor
            sensor_users = self.list_users_from_sensor()
            
            # Dapatkan user dari database
            db_users = {row[0]: row[1] for row in self.list_users_from_database()}
            
            # Update database
            conn = sqlite3.connect(self.db_file, timeout=10.0)
            cursor = conn.cursor()
            
            added = 0
            removed = 0
            
            # Tambahkan user yang ada di sensor tapi tidak di database
            for fingerprint_id in sensor_users:
                if fingerprint_id not in db_users:
                    user_name = f"User_{fingerprint_id}"
                    cursor.execute('''
                        INSERT INTO users (fingerprint_id, user_name, device_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (fingerprint_id, user_name, 'AS608_001', datetime.now(), datetime.now()))
                    added += 1
            
            # Hapus user yang tidak ada di sensor tapi ada di database
            for fingerprint_id in db_users.keys():
                if fingerprint_id not in sensor_users:
                    cursor.execute('DELETE FROM users WHERE fingerprint_id = ?', (fingerprint_id,))
                    removed += 1
            
            conn.commit()
            conn.close()
            
            print(f"✓ Sinkronisasi selesai:")
            print(f"   Ditambahkan: {added} user")
            print(f"   Dihapus: {removed} user")
            
            return True
            
        except Exception as e:
            print(f"❌ Error sinkronisasi: {e}")
            return False
    
    def clear_all_users(self):
        """Menghapus semua user dari sensor dan database"""
        try:
            print("\n⚠️  PERINGATAN: Operasi ini akan menghapus SEMUA user!")
            print("   - Semua fingerprint di sensor akan dihapus")
            print("   - Semua data di database akan dihapus")
            
            confirm = input("\nApakah Anda benar-benar yakin? Ketik 'HAPUS SEMUA' untuk konfirmasi: ").strip()
            if confirm != 'HAPUS SEMUA':
                print("❌ Operasi dibatalkan")
                return False
            
            if not self.connected or not self.finger:
                print("❌ Sensor tidak terhubung")
                return False
            
            # Hapus semua dari sensor
            print("\n🗑️  Menghapus semua fingerprint dari sensor...")
            if self.finger.empty_library() != adafruit_fingerprint.OK:
                print("❌ Gagal menghapus fingerprint dari sensor")
                return False
            
            print("✓ Semua fingerprint dihapus dari sensor")
            
            # Hapus semua dari database
            try:
                conn = sqlite3.connect(self.db_file, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users')
                conn.commit()
                conn.close()
                print("✓ Semua data dihapus dari database")
            except Exception as e:
                print(f"⚠️  Warning: Gagal menghapus dari database: {e}")
            
            print("\n✅ Semua user berhasil dihapus")
            return True
            
        except Exception as e:
            print(f"❌ Error menghapus semua user: {e}")
            return False


def main():
    """Fungsi utama dengan menu interaktif"""
    print("=" * 70)
    print("PROGRAM MANAJEMEN USER SENSOR AS608")
    print("Port: /dev/serial0 (ttySerial 0)")
    print("=" * 70)
    
    manager = AS608UserManager()
    
    try:
        # Hubungkan ke sensor
        if not manager.connect_sensor():
            print("\n❌ Gagal menghubungkan ke sensor")
            print("💡 Pastikan:")
            print("   1. Sensor AS608 terhubung ke /dev/serial0")
            print("   2. Port tidak digunakan oleh program lain")
            print("   3. User memiliki izin akses (jalankan dengan sudo jika perlu)")
            return 1
        
        # Tampilkan info sensor
        info = manager.get_sensor_info()
        if info:
            print("\n📊 Informasi Sensor:")
            print(f"   Template tersimpan: {info['template_count']}")
            print(f"   Kapasitas maksimal: {info['library_size']}")
            print(f"   Security level: {info['security_level']}")
        
        # Menu utama
        while True:
            print("\n" + "=" * 70)
            print("MENU UTAMA")
            print("=" * 70)
            print("1. Tampilkan daftar user")
            print("2. Daftarkan user baru")
            print("3. Hapus user")
            print("4. Sinkronisasi database dengan sensor")
            print("5. Hapus semua user")
            print("6. Informasi sensor")
            print("7. Keluar")
            print("=" * 70)
            
            choice = input("\nPilih opsi (1-7): ").strip()
            
            if choice == "1":
                manager.display_users()
            
            elif choice == "2":
                print("\n📝 Pendaftaran User Baru")
                print("-" * 70)
                
                # Tanya apakah ingin menentukan ID manual
                use_custom_id = input("Gunakan ID manual? (y/N): ").strip().lower()
                fingerprint_id = None
                
                if use_custom_id == 'y':
                    try:
                        fingerprint_id = int(input("Masukkan ID (1-128): ").strip())
                        if fingerprint_id < 1 or fingerprint_id > 128:
                            print("❌ ID harus antara 1-128")
                            continue
                    except ValueError:
                        print("❌ ID harus berupa angka")
                        continue
                
                manager.enroll_user(fingerprint_id=fingerprint_id)
            
            elif choice == "3":
                print("\n🗑️  Hapus User")
                print("-" * 70)
                
                # Tampilkan daftar user dulu
                sensor_users = manager.list_users_from_sensor()
                if not sensor_users:
                    print("❌ Tidak ada user di sensor")
                    continue
                
                print("\nDaftar user:")
                for idx, fid in enumerate(sensor_users, 1):
                    user_name = manager.get_user_name(fid)
                    print(f"   {idx}. ID: {fid} - {user_name}")
                
                try:
                    user_input = input("\nMasukkan ID user yang akan dihapus: ").strip()
                    fingerprint_id = int(user_input)
                    manager.delete_user(fingerprint_id)
                except ValueError:
                    print("❌ ID harus berupa angka")
            
            elif choice == "4":
                manager.sync_database()
            
            elif choice == "5":
                manager.clear_all_users()
            
            elif choice == "6":
                print("\n📊 Informasi Sensor")
                print("-" * 70)
                info = manager.get_sensor_info()
                if info:
                    print(f"Template tersimpan: {info['template_count']}")
                    print(f"Kapasitas maksimal: {info['library_size']}")
                    print(f"Security level: {info['security_level']}")
                    print(f"System ID: {info['system_id']}")
                    print(f"Device address: {info['device_address']}")
                    print(f"Packet size: {info['packet_size']}")
                    print(f"Baud rate: {info['baud_rate']}")
                else:
                    print("❌ Gagal membaca informasi sensor")
            
            elif choice == "7":
                print("\n👋 Keluar dari program...")
                break
            
            else:
                print("❌ Opsi tidak valid. Pilih 1-7")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Program dihentikan oleh user")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        manager.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

