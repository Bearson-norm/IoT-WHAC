#!/usr/bin/env python3
"""
Program sederhana untuk membaca sensor AS608 pada Raspberry Pi
Menggunakan port /dev/ttyAMA3
"""

import serial
import adafruit_fingerprint
import time
import sys

# Konfigurasi
SENSOR_PORT = "/dev/ttyAMA3"
BAUD_RATE = 57600

def check_port_in_use(port):
    """Cek apakah port sedang digunakan"""
    try:
        import subprocess
        result = subprocess.run(['lsof', port], capture_output=True, text=True, timeout=3)
        if result.stdout:
            return True, result.stdout
        return False, None
    except:
        return None, None

def connect_sensor(port, baudrate, retries=3):
    """Menghubungkan ke sensor AS608"""
    uart = None
    finger = None
    
    # Cek apakah port sedang digunakan
    print(f"Memeriksa status port {port}...")
    port_in_use, port_info = check_port_in_use(port)
    if port_in_use:
        print("⚠️  PERINGATAN: Port sedang digunakan oleh proses lain!")
        print("   Detail:")
        for line in port_info.split('\n')[:5]:  # Tampilkan beberapa baris pertama
            if line.strip():
                print(f"   {line}")
        print("\n💡 Solusi:")
        print("   1. Hentikan program lain yang menggunakan port ini:")
        print("      sudo pkill -f fingerprint_multi_client")
        print("   2. Atau cek proses dengan: lsof /dev/ttyAMA3")
        print("   3. Lalu kill proses tersebut: sudo kill <PID>")
        print()
        response = input("Lanjutkan tetap mencoba koneksi? (y/n): ")
        if response.lower() != 'y':
            return None, None
    
    for attempt in range(retries):
        try:
            print(f"Menghubungkan ke sensor pada {port} (percobaan {attempt + 1}/{retries})...")
            
            # Buka koneksi serial
            uart = serial.Serial(port, baudrate=baudrate, timeout=2)
            time.sleep(0.5)  # Beri waktu sensor untuk stabil
            
            # Buat objek fingerprint
            finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
            
            # Test koneksi dengan membaca template count
            if finger.read_templates() == adafruit_fingerprint.OK:
                print(f"✓ Sensor terhubung dengan sukses!")
                print(f"  Jumlah template tersimpan: {finger.template_count}")
                return uart, finger
            else:
                raise Exception("Gagal membaca template dari sensor")
                
        except serial.SerialException as e:
            error_msg = str(e)
            print(f"✗ Error serial: {error_msg}")
            
            # Deteksi jenis error
            if "Permission denied" in error_msg:
                print("   → Masalah permission. Coba:")
                print("     sudo python3 read_as608_sensor.py")
                print("     atau tambahkan user ke grup dialout:")
                print("     sudo usermod -a -G dialout $USER")
            elif "could not open port" in error_msg.lower() or "device or resource busy" in error_msg.lower():
                print("   → Port sedang digunakan atau device busy")
                print("   → Cek dengan: python3 check_port_usage.py")
                print("   → Atau: lsof /dev/ttyAMA3")
            elif "No such file or directory" in error_msg:
                print("   → Port tidak ditemukan")
                print("   → Cek dengan: ls -l /dev/ttyAMA3")
            
            if uart:
                try:
                    uart.close()
                except:
                    pass
            if attempt < retries - 1:
                print("  Menunggu 2 detik sebelum mencoba lagi...")
                time.sleep(2)
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Error: {error_msg}")
            
            # Deteksi error spesifik
            if "Failed to read data from sensor" in error_msg:
                print("   → Sensor tidak merespon")
                print("   → Kemungkinan:")
                print("     - Sensor tidak terhubung dengan benar")
                print("     - Kabel TX/RX terbalik")
                print("     - Baud rate tidak sesuai")
                print("     - Sensor tidak menyala")
                print("     - Port sedang digunakan program lain")
            
            if uart:
                try:
                    uart.close()
                except:
                    pass
            if attempt < retries - 1:
                print("  Menunggu 2 detik sebelum mencoba lagi...")
                time.sleep(2)
    
    return None, None

def get_sensor_info(finger):
    """Mendapatkan informasi sensor"""
    try:
        print("\n" + "="*50)
        print("INFORMASI SENSOR")
        print("="*50)
        
        # Baca template count
        if finger.read_templates() == adafruit_fingerprint.OK:
            print(f"Jumlah template tersimpan: {finger.template_count}")
        else:
            print("Gagal membaca jumlah template")
        
        # Baca parameter sistem
        params = finger.get_sysparam()
        if params:
            print(f"Status register: {params[0]}")
            print(f"System ID: {params[1]}")
            print(f"Library size: {params[2]}")
            print(f"Security level: {params[3]}")
            print(f"Device address: {params[4]}")
            print(f"Packet size: {params[5]}")
            print(f"Baud rate: {params[6]}")
        
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"Error mendapatkan info sensor: {e}")

def scan_fingerprint(finger):
    """Scan sidik jari dan cari match"""
    try:
        print("Tempatkan jari pada sensor...")
        
        # Tunggu sampai jari terdeteksi
        max_wait = 10  # detik
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("✓ Gambar sidik jari berhasil diambil")
                break
            elif i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
                time.sleep(0.5)
            else:
                print(f"\n✗ Error mengambil gambar: {i}")
                return False
        
        if time.time() - start_time >= max_wait:
            print("\n✗ Timeout: Tidak ada jari terdeteksi")
            return False
        
        # Konversi gambar ke template
        print("Mengkonversi gambar ke template...")
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("✗ Gagal mengkonversi gambar ke template")
            return False
        
        print("✓ Template berhasil dibuat")
        
        # Cari match
        print("Mencari match dalam database...")
        i = finger.finger_search()
        
        if i == adafruit_fingerprint.OK:
            finger_id = finger.finger_id
            confidence = finger.confidence
            print(f"\n{'='*50}")
            print("✓ MATCH DITEMUKAN!")
            print(f"  ID Sidik Jari: {finger_id}")
            print(f"  Confidence: {confidence}")
            print(f"{'='*50}\n")
            return True
        elif i == adafruit_fingerprint.NOTFOUND:
            print("\n✗ Tidak ada match ditemukan")
            return False
        else:
            print(f"\n✗ Error mencari match: {i}")
            return False
            
    except Exception as e:
        print(f"Error saat scan: {e}")
        return False

def continuous_scan(finger):
    """Mode scan kontinyu"""
    print("\n" + "="*50)
    print("MODE SCAN KONTINYU")
    print("Tekan Ctrl+C untuk berhenti")
    print("="*50 + "\n")
    
    try:
        while True:
            # Cek apakah ada jari
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Jari terdeteksi, memproses...")
                
                # Konversi ke template
                if finger.image_2_tz(1) == adafruit_fingerprint.OK:
                    # Cari match
                    i = finger.finger_search()
                    if i == adafruit_fingerprint.OK:
                        finger_id = finger.finger_id
                        confidence = finger.confidence
                        print(f"✓ MATCH! ID: {finger_id}, Confidence: {confidence}")
                    else:
                        print("✗ Tidak ada match")
                
            elif i == adafruit_fingerprint.NOFINGER:
                time.sleep(0.1)
            else:
                print(f"Error: {i}")
                time.sleep(0.5)
                
    except KeyboardInterrupt:
        print("\n\nScan dihentikan oleh user")

def main():
    """Fungsi utama"""
    print("="*50)
    print("PROGRAM PEMBACA SENSOR AS608")
    print(f"Port: {SENSOR_PORT}")
    print("="*50)
    
    # Cek apakah port ada
    import os
    if not os.path.exists(SENSOR_PORT):
        print(f"\n✗ ERROR: Port {SENSOR_PORT} tidak ditemukan!")
        print("\nPastikan:")
        print("  1. Sensor AS608 sudah terhubung")
        print("  2. Port benar (cek dengan: ls -l /dev/ttyAMA*)")
        print("  3. User memiliki akses ke port (jalankan dengan sudo atau tambahkan user ke grup dialout)")
        return 1
    
    # Hubungkan ke sensor
    uart, finger = connect_sensor(SENSOR_PORT, BAUD_RATE)
    
    if not finger:
        print("\n✗ Gagal menghubungkan ke sensor")
        print("\nTips:")
        print("  - Pastikan sensor sudah terhubung dan menyala")
        print("  - Cek koneksi kabel")
        print("  - Coba jalankan dengan sudo: sudo python3 read_as608_sensor.py")
        return 1
    
    try:
        # Tampilkan info sensor
        get_sensor_info(finger)
        
        # Menu
        print("Pilih mode:")
        print("  1. Scan sekali (single scan)")
        print("  2. Scan kontinyu (continuous scan)")
        print("  3. Hanya tampilkan info sensor")
        
        choice = input("\nPilihan (1/2/3): ").strip()
        
        if choice == "1":
            scan_fingerprint(finger)
        elif choice == "2":
            continuous_scan(finger)
        elif choice == "3":
            print("Info sensor sudah ditampilkan di atas")
        else:
            print("Pilihan tidak valid, melakukan single scan...")
            scan_fingerprint(finger)
            
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan oleh user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Tutup koneksi
        if uart:
            uart.close()
            print("\n✓ Koneksi serial ditutup")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


