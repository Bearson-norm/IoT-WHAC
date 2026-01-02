#!/usr/bin/env python3
"""
UART Diagnostic Script untuk Raspberry Pi
Mendiagnosis masalah UART yang tidak muncul setelah konfigurasi dtoverlay
"""

import os
import subprocess
import glob
import sys

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def check_config_txt():
    """Check /boot/config.txt for UART overlays"""
    print("=" * 70)
    print("1. CHECKING /boot/config.txt")
    print("=" * 70)
    
    config_paths = [
        "/boot/config.txt",
        "/boot/firmware/config.txt"  # For newer Raspberry Pi OS
    ]
    
    found_config = None
    for path in config_paths:
        if os.path.exists(path):
            found_config = path
            break
    
    if not found_config:
        print("❌ /boot/config.txt tidak ditemukan!")
        return False
    
    print(f"✓ Found config: {found_config}")
    print()
    
    with open(found_config, 'r') as f:
        lines = f.readlines()
    
    uart_overlays = []
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if 'uart' in line_stripped.lower() and not line_stripped.startswith('#'):
            uart_overlays.append((i, line_stripped))
            print(f"  Line {i}: {line_stripped}")
    
    if not uart_overlays:
        print("⚠️  Tidak ada dtoverlay=uart* ditemukan di config.txt")
        print("   Pastikan Anda sudah menambahkan:")
        print("   dtoverlay=uart1")
        print("   dtoverlay=uart2")
        print("   dtoverlay=uart3")
        print("   dtoverlay=uart4")
        print("   dtoverlay=uart5")
        return False
    
    print(f"\n✓ Found {len(uart_overlays)} UART overlay(s)")
    return True

def check_loaded_overlays():
    """Check which device tree overlays are loaded"""
    print("\n" + "=" * 70)
    print("2. CHECKING LOADED DEVICE TREE OVERLAYS")
    print("=" * 70)
    
    # Check /proc/device-tree
    overlay_path = "/proc/device-tree/soc/serial@"
    if os.path.exists("/proc/device-tree"):
        print("✓ /proc/device-tree exists")
        
        # List serial devices
        serial_devices = []
        for item in os.listdir("/proc/device-tree/soc"):
            if "serial@" in item:
                serial_devices.append(item)
        
        if serial_devices:
            print(f"✓ Found {len(serial_devices)} serial device(s) in device tree:")
            for dev in sorted(serial_devices):
                print(f"  - {dev}")
        else:
            print("⚠️  Tidak ada serial device ditemukan di device tree")
    else:
        print("⚠️  /proc/device-tree tidak tersedia")
    
    # Check loaded overlays
    overlay_dir = "/sys/kernel/config/device-tree/overlays"
    if os.path.exists(overlay_dir):
        overlays = [d for d in os.listdir(overlay_dir) if os.path.isdir(os.path.join(overlay_dir, d))]
        if overlays:
            print(f"\n✓ Loaded overlays: {len(overlays)}")
            for overlay in overlays:
                print(f"  - {overlay}")
        else:
            print("\n⚠️  Tidak ada overlay yang ter-load")
    else:
        print(f"\n⚠️  {overlay_dir} tidak tersedia")

def check_available_ports():
    """Check all available serial ports"""
    print("\n" + "=" * 70)
    print("3. CHECKING AVAILABLE SERIAL PORTS")
    print("=" * 70)
    
    # Check common UART patterns
    patterns = [
        '/dev/ttyAMA*',
        '/dev/ttyS*',
        '/dev/serial*',
        '/dev/ttyUSB*',
        '/dev/ttyACM*'
    ]
    
    all_ports = []
    for pattern in patterns:
        found = glob.glob(pattern)
        all_ports.extend(found)
    
    if all_ports:
        print(f"✓ Found {len(all_ports)} serial port(s):")
        for port in sorted(all_ports):
            # Check if port exists and is readable
            exists = os.path.exists(port)
            readable = os.access(port, os.R_OK) if exists else False
            status = "✓" if (exists and readable) else "⚠️"
            print(f"  {status} {port}")
    else:
        print("❌ Tidak ada serial port ditemukan!")
    
    return all_ports

def check_dmesg():
    """Check dmesg for UART-related messages"""
    print("\n" + "=" * 70)
    print("4. CHECKING KERNEL MESSAGES (dmesg)")
    print("=" * 70)
    
    output, code = run_command("dmesg | grep -i 'uart\|tty\|serial' | tail -20")
    if output:
        print(output)
    else:
        print("⚠️  Tidak ada UART-related messages di dmesg")

def check_uart_mapping():
    """Check UART to ttyAMA mapping"""
    print("\n" + "=" * 70)
    print("5. UART TO TTY MAPPING")
    print("=" * 70)
    
    # Raspberry Pi UART mapping:
    # uart0 (PL011) -> /dev/ttyAMA0 or /dev/serial0
    # uart1 (mini UART) -> /dev/ttyS0 or /dev/serial1
    # uart2-5 (additional) -> /dev/ttyAMA1-4 (depending on configuration)
    
    mappings = {
        "uart0": ["/dev/ttyAMA0", "/dev/serial0"],
        "uart1": ["/dev/ttyS0", "/dev/serial1"],
        "uart2": ["/dev/ttyAMA1"],
        "uart3": ["/dev/ttyAMA2"],
        "uart4": ["/dev/ttyAMA3"],
        "uart5": ["/dev/ttyAMA4"],
    }
    
    print("Expected UART to device mapping:")
    for uart, devices in mappings.items():
        found_devices = [d for d in devices if os.path.exists(d)]
        status = "✓" if found_devices else "❌"
        print(f"  {status} {uart} -> {', '.join(devices)}")
        if found_devices:
            print(f"      Found: {', '.join(found_devices)}")

def check_serial_console():
    """Check if serial console is enabled (can conflict with UART)"""
    print("\n" + "=" * 70)
    print("6. CHECKING SERIAL CONSOLE CONFIGURATION")
    print("=" * 70)
    
    # Check cmdline.txt
    cmdline_paths = [
        "/boot/cmdline.txt",
        "/boot/firmware/cmdline.txt"
    ]
    
    for path in cmdline_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                cmdline = f.read()
            
            if 'console=serial' in cmdline or 'console=ttyAMA' in cmdline:
                print(f"⚠️  Serial console enabled di {path}")
                print(f"   Ini bisa mengkonflik dengan UART untuk sensor")
                print(f"   Content: {cmdline[:100]}...")
            else:
                print(f"✓ Serial console tidak aktif di {path}")
            break
    else:
        print("⚠️  cmdline.txt tidak ditemukan")

def provide_solutions():
    """Provide solutions for common UART issues"""
    print("\n" + "=" * 70)
    print("7. SOLUSI YANG DISARANKAN")
    print("=" * 70)
    
    print("""
Jika ttyAMA2 dan ttyAMA3 tidak muncul, coba langkah berikut:

1. VERIFIKASI CONFIG.TXT:
   Pastikan di /boot/config.txt ada:
   ```
   enable_uart=1
   dtoverlay=uart2
   dtoverlay=uart3
   dtoverlay=uart4
   dtoverlay=uart5
   ```
   
   Catatan: uart1 biasanya sudah default, tidak perlu dtoverlay=uart1

2. TENTUKAN GPIO PINS:
   Untuk Raspberry Pi, UART tambahan perlu GPIO pins yang spesifik.
   Coba dengan parameter GPIO:
   ```
   dtoverlay=uart2,pins_2_3
   dtoverlay=uart3,pins_4_5
   dtoverlay=uart4,pins_8_9
   dtoverlay=uart5,pins_12_13
   ```
   
   Atau gunakan GPIO alternatif:
   ```
   dtoverlay=uart2,ctsrts
   dtoverlay=uart3,ctsrts
   ```

3. CEK MODEL RASPBERRY PI:
   Tidak semua model Pi mendukung banyak UART.
   - Pi 4: Mendukung uart0-5
   - Pi 3: Mendukung uart0-2
   - Pi Zero: Terbatas
   
   Cek model dengan: cat /proc/device-tree/model

4. REBOOT SETELAH PERUBAHAN:
   Pastikan sudah reboot setelah mengubah config.txt

5. CEK KONFLIK GPIO:
   Pastikan GPIO pins yang digunakan tidak konflik dengan fungsi lain

6. ALTERNATIF: GUNAKAN USB-TO-SERIAL:
   Jika UART GPIO bermasalah, gunakan USB-to-Serial adapter:
   - Lebih mudah setup
   - Tidak perlu konfigurasi GPIO
   - Port: /dev/ttyUSB0, /dev/ttyUSB1, dll
""")

def main():
    print("\n" + "=" * 70)
    print("UART DIAGNOSTIC TOOL - Raspberry Pi")
    print("=" * 70)
    print()
    
    # Check if running on Raspberry Pi
    if not os.path.exists("/proc/device-tree"):
        print("⚠️  Tidak terdeteksi sebagai Raspberry Pi")
        print("   Script ini dirancang untuk Raspberry Pi")
        print()
    
    check_config_txt()
    check_loaded_overlays()
    ports = check_available_ports()
    check_dmesg()
    check_uart_mapping()
    check_serial_console()
    provide_solutions()
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS SELESAI")
    print("=" * 70)
    
    if not ports:
        print("\n❌ TIDAK ADA PORT YANG DITEMUKAN")
        print("   Ikuti solusi di atas untuk mengaktifkan UART")
    else:
        print(f"\n✓ Ditemukan {len(ports)} port(s)")
        print("   Port yang tersedia:")
        for port in sorted(ports):
            print(f"     - {port}")

if __name__ == "__main__":
    main()


