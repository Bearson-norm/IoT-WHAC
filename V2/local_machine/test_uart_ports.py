#!/usr/bin/env python3
"""
Test script untuk memverifikasi port UART bisa digunakan untuk sensor fingerprint
Jalankan script ini untuk memastikan port siap digunakan sebelum menjalankan fingerprint_multi_client.py
"""

import serial
import sys
import os
import glob
import time

def test_port(port, baudrate=57600):
    """Test if a port can be opened and used"""
    print(f"\n{'='*60}")
    print(f"Testing: {port}")
    print(f"{'='*60}")
    
    # Check if port exists
    if not os.path.exists(port):
        print(f"❌ Port {port} tidak ada!")
        return False
    
    # Check permissions
    if not os.access(port, os.R_OK | os.W_OK):
        print(f"⚠️  Permission denied untuk {port}")
        print(f"   Solusi: sudo usermod -a -G dialout $USER")
        print(f"   Atau jalankan dengan: sudo python3 {sys.argv[0]}")
        return False
    
    print(f"✓ Port exists dan accessible")
    
    # Try to open port
    try:
        print(f"  Mencoba membuka port dengan baudrate {baudrate}...")
        ser = serial.Serial(port, baudrate=baudrate, timeout=2)
        print(f"✓ Port berhasil dibuka!")
        
        # Try to read (should timeout if no device connected)
        print(f"  Mencoba membaca data (timeout 2 detik)...")
        time.sleep(0.5)
        try:
            data = ser.read(10)
            if data:
                print(f"  ✓ Data diterima: {data.hex()}")
            else:
                print(f"  ✓ Port terbuka, tidak ada data (normal jika sensor belum terhubung)")
        except Exception as e:
            print(f"  ⚠️  Error membaca: {e}")
        
        ser.close()
        print(f"✓ Port berhasil ditutup")
        return True
        
    except serial.SerialException as e:
        print(f"❌ Error membuka port: {e}")
        if "Permission denied" in str(e):
            print(f"   Solusi: sudo usermod -a -G dialout $USER")
        elif "could not open port" in str(e).lower() or "device or resource busy" in str(e).lower():
            print(f"   Port mungkin sedang digunakan oleh proses lain")
            print(f"   Cek dengan: sudo lsof {port}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*70)
    print("UART PORT TESTER - Verifikasi Port untuk Fingerprint Sensor")
    print("="*70)
    
    # Get ports from config or command line
    if len(sys.argv) > 1:
        ports = sys.argv[1:]
    else:
        # Default ports from config
        ports = [
            "/dev/serial0",
            "/dev/ttyAMA2",
            "/dev/ttyAMA3",
            "/dev/ttyAMA4",
            "/dev/ttyAMA5"
        ]
    
    print(f"\nPort yang akan di-test: {', '.join(ports)}")
    print(f"\n💡 Tip: Jika port tidak ada, script akan otomatis mencari port yang tersedia")
    
    # Check all available ports
    all_ports = []
    patterns = ['/dev/ttyAMA*', '/dev/ttyS*', '/dev/serial*', '/dev/ttyUSB*']
    for pattern in patterns:
        all_ports.extend(glob.glob(pattern))
    all_ports = sorted(list(set(all_ports)))
    
    print(f"\n📋 Semua port yang tersedia: {len(all_ports)}")
    for port in all_ports:
        print(f"   - {port}")
    
    # Test each port
    results = {}
    for port in ports:
        if os.path.exists(port):
            results[port] = test_port(port)
        else:
            print(f"\n⚠️  Port {port} tidak ada, melewati test")
            results[port] = None
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results.values() if r is True)
    total_count = sum(1 for r in results.values() if r is not None)
    
    for port, result in results.items():
        if result is True:
            print(f"✓ {port}: READY")
        elif result is False:
            print(f"❌ {port}: FAILED")
        else:
            print(f"⚠️  {port}: NOT FOUND")
    
    print(f"\n{'='*70}")
    if success_count == total_count and total_count > 0:
        print(f"✅ {success_count}/{total_count} port(s) siap digunakan!")
        print(f"\n💡 Port yang bisa digunakan di config.py:")
        ready_ports = [p for p, r in results.items() if r is True]
        if ready_ports:
            print(f"   FINGERPRINT_PORTS=\"{','.join(ready_ports)}\"")
    elif success_count > 0:
        print(f"⚠️  {success_count}/{total_count} port(s) siap, beberapa port bermasalah")
    else:
        print(f"❌ Tidak ada port yang siap digunakan")
        print(f"\n💡 Coba:")
        print(f"   1. Pastikan user ada di group dialout: sudo usermod -a -G dialout $USER")
        print(f"   2. Atau jalankan dengan sudo: sudo python3 {sys.argv[0]}")
        print(f"   3. Cek apakah port benar-benar ada: ls -la /dev/ttyAMA*")
    
    print(f"{'='*70}")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())

