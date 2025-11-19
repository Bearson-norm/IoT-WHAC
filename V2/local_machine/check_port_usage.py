#!/usr/bin/env python3
"""
Program untuk memeriksa apakah port serial sedang digunakan
"""

import os
import subprocess
import sys

def check_port_in_use(port):
    """Cek apakah port sedang digunakan"""
    if not os.path.exists(port):
        print(f"✗ Port {port} tidak ada")
        return False
    
    print(f"\nMemeriksa penggunaan port: {port}")
    print("-" * 60)
    
    # Cek dengan lsof (Linux)
    try:
        result = subprocess.run(['lsof', port], capture_output=True, text=True, timeout=5)
        if result.stdout:
            print("⚠️  Port sedang digunakan oleh:")
            print(result.stdout)
            
            # Extract PID
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        try:
                            # Get process info
                            ps_result = subprocess.run(['ps', '-p', pid, '-o', 'pid,cmd'], 
                                                      capture_output=True, text=True, timeout=5)
                            if ps_result.stdout:
                                print(f"\nProcess info:")
                                print(ps_result.stdout)
                        except:
                            pass
            return True
        else:
            print("✓ Port tidak sedang digunakan")
            return False
    except FileNotFoundError:
        print("⚠️  lsof tidak tersedia, menggunakan metode lain...")
    except Exception as e:
        print(f"Error menggunakan lsof: {e}")
    
    # Cek dengan fuser (alternatif)
    try:
        result = subprocess.run(['fuser', port], capture_output=True, text=True, timeout=5)
        if result.stdout:
            print("⚠️  Port sedang digunakan")
            print(result.stdout)
            return True
        else:
            print("✓ Port tidak sedang digunakan")
            return False
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error menggunakan fuser: {e}")
    
    # Cek dengan Python - coba buka port
    try:
        import serial
        test_uart = serial.Serial(port, baudrate=57600, timeout=1)
        test_uart.close()
        print("✓ Port bisa dibuka (tidak digunakan)")
        return False
    except serial.SerialException as e:
        if "Permission denied" in str(e):
            print("⚠️  Permission denied - mungkin port digunakan atau user tidak ada di grup dialout")
        elif "could not open port" in str(e).lower() or "device or resource busy" in str(e).lower():
            print("⚠️  Port sedang digunakan atau device busy")
        else:
            print(f"⚠️  Error: {e}")
        return True
    except ImportError:
        print("⚠️  pyserial tidak tersedia untuk test")
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def find_python_processes_using_serial():
    """Cari proses Python yang mungkin menggunakan serial port"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        
        python_procs = []
        for line in lines:
            if 'python' in line.lower() and ('fingerprint' in line.lower() or 'serial' in line.lower()):
                python_procs.append(line)
        
        if python_procs:
            print("\n" + "=" * 60)
            print("Proses Python yang mungkin menggunakan serial:")
            print("=" * 60)
            for proc in python_procs:
                print(proc)
            return True
        else:
            print("\n✓ Tidak ada proses Python yang terlihat menggunakan serial")
            return False
    except Exception as e:
        print(f"Error mencari proses: {e}")
        return False

def main():
    """Fungsi utama"""
    print("=" * 60)
    print("PEMERIKSAAN PENGGUNAAN PORT SERIAL")
    print("=" * 60)
    
    # Port yang ingin dicek
    ports_to_check = ['/dev/ttyAMA3', '/dev/serial0', '/dev/ttyAMA0']
    
    for port in ports_to_check:
        if os.path.exists(port):
            in_use = check_port_in_use(port)
            if in_use:
                print(f"\n💡 Untuk menghentikan proses yang menggunakan {port}:")
                print(f"   sudo pkill -f fingerprint")
                print(f"   atau")
                print(f"   sudo killall python3")
    
    # Cari proses Python yang mungkin menggunakan serial
    find_python_processes_using_serial()
    
    print("\n" + "=" * 60)
    print("SOLUSI JIKA PORT SEDANG DIGUNAKAN:")
    print("=" * 60)
    print("1. Hentikan program yang menggunakan port:")
    print("   sudo pkill -f fingerprint_multi_client")
    print("   atau")
    print("   sudo killall python3")
    print("\n2. Atau cari PID dan kill manual:")
    print("   lsof /dev/ttyAMA3")
    print("   sudo kill <PID>")
    print("\n3. Pastikan hanya satu program yang menggunakan port")
    print("=" * 60)

if __name__ == "__main__":
    main()


