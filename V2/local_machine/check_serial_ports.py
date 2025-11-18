#!/usr/bin/env python3
"""
Program untuk memeriksa port serial yang tersedia di Raspberry Pi
Termasuk /dev/serial0, /dev/serial1, dan port lainnya
"""

import os
import glob
import subprocess

def check_port_exists(port):
    """Cek apakah port ada"""
    return os.path.exists(port)

def check_port_info(port):
    """Cek informasi detail tentang port"""
    if not os.path.exists(port):
        return None
    
    try:
        # Cek apakah itu symlink
        if os.path.islink(port):
            real_path = os.readlink(port)
            return {
                'exists': True,
                'is_symlink': True,
                'real_path': real_path,
                'absolute_path': os.path.realpath(port)
            }
        else:
            # Cek permission
            stat_info = os.stat(port)
            return {
                'exists': True,
                'is_symlink': False,
                'real_path': port,
                'permissions': oct(stat_info.st_mode)[-3:]
            }
    except Exception as e:
        return {'exists': True, 'error': str(e)}

def list_all_serial_ports():
    """List semua port serial yang mungkin ada"""
    ports = []
    
    # Port serial standar
    standard_ports = [
        '/dev/serial0',
        '/dev/serial1',
        '/dev/ttyAMA0',
        '/dev/ttyAMA1',
        '/dev/ttyAMA2',
        '/dev/ttyAMA3',
        '/dev/ttyS0',
        '/dev/ttyS1',
        '/dev/ttyS2',
        '/dev/ttyS3',
    ]
    
    # Port USB serial
    usb_patterns = ['/dev/ttyUSB*', '/dev/ttyACM*']
    for pattern in usb_patterns:
        ports.extend(glob.glob(pattern))
    
    # Port built-in
    for port in standard_ports:
        if os.path.exists(port):
            ports.append(port)
    
    return sorted(list(set(ports)))

def main():
    """Fungsi utama"""
    print("="*60)
    print("PEMERIKSAAN PORT SERIAL")
    print("="*60)
    
    # Cek /dev/serial0 secara khusus
    print("\n1. Pemeriksaan /dev/serial0:")
    print("-" * 60)
    serial0_exists = check_port_exists('/dev/serial0')
    
    if serial0_exists:
        print("✓ /dev/serial0 ADA")
        info = check_port_info('/dev/serial0')
        if info:
            if info.get('is_symlink'):
                print(f"  → Ini adalah symlink ke: {info.get('real_path')}")
                print(f"  → Path absolut: {info.get('absolute_path')}")
            else:
                print(f"  → Path: {info.get('real_path')}")
                print(f"  → Permissions: {info.get('permissions')}")
    else:
        print("✗ /dev/serial0 TIDAK ADA")
    
    # Cek /dev/serial1
    print("\n2. Pemeriksaan /dev/serial1:")
    print("-" * 60)
    serial1_exists = check_port_exists('/dev/serial1')
    
    if serial1_exists:
        print("✓ /dev/serial1 ADA")
        info = check_port_info('/dev/serial1')
        if info:
            if info.get('is_symlink'):
                print(f"  → Ini adalah symlink ke: {info.get('real_path')}")
                print(f"  → Path absolut: {info.get('absolute_path')}")
    else:
        print("✗ /dev/serial1 TIDAK ADA")
    
    # List semua port serial yang tersedia
    print("\n3. Semua Port Serial yang Tersedia:")
    print("-" * 60)
    all_ports = list_all_serial_ports()
    
    if all_ports:
        print(f"✓ Ditemukan {len(all_ports)} port serial:")
        for port in all_ports:
            info = check_port_info(port)
            if info and info.get('is_symlink'):
                print(f"  • {port} → {info.get('real_path')}")
            else:
                print(f"  • {port}")
    else:
        print("✗ Tidak ada port serial yang ditemukan")
    
    # Cek port ttyAMA khusus
    print("\n4. Port ttyAMA (UART Hardware):")
    print("-" * 60)
    for i in range(4):
        port = f"/dev/ttyAMA{i}"
        if os.path.exists(port):
            print(f"✓ {port} ADA")
        else:
            print(f"✗ {port} TIDAK ADA")
    
    # Cek permission
    print("\n5. Pemeriksaan Permission:")
    print("-" * 60)
    try:
        # Cek apakah user ada di grup dialout
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip()
        if 'dialout' in groups:
            print("✓ User berada di grup 'dialout' (bisa akses serial)")
        else:
            print("✗ User TIDAK berada di grup 'dialout'")
            print("  → Untuk menambahkan: sudo usermod -a -G dialout $USER")
            print("  → Lalu logout dan login lagi")
    except:
        print("⚠ Tidak bisa mengecek grup user")
    
    # Informasi tambahan
    print("\n6. Informasi Tambahan:")
    print("-" * 60)
    print("Cara mengecek dengan command line:")
    print("  ls -l /dev/serial0")
    print("  ls -l /dev/serial1")
    print("  ls -l /dev/ttyAMA*")
    print("\nCara mengecek apakah symlink:")
    print("  readlink -f /dev/serial0")
    print("\nCara melihat semua port serial:")
    print("  ls -l /dev/tty* | grep -E 'tty(USB|ACM|AMA|S)'")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

