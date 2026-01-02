#!/bin/bash
# Script untuk mengecek dan menampilkan semua port UART yang tersedia
# Jalankan di Raspberry Pi setelah konfigurasi UART

echo "=========================================="
echo "UART Port Checker - Raspberry Pi"
echo "=========================================="
echo ""

# Check model
echo "1. Raspberry Pi Model:"
if [ -f /proc/device-tree/model ]; then
    cat /proc/device-tree/model
else
    echo "   (Model tidak terdeteksi)"
fi
echo ""

# Check config.txt
echo "2. UART Configuration di /boot/config.txt:"
if [ -f /boot/config.txt ]; then
    echo "   UART-related lines:"
    grep -i "uart\|enable_uart" /boot/config.txt | grep -v "^#" | sed 's/^/   /'
elif [ -f /boot/firmware/config.txt ]; then
    echo "   UART-related lines:"
    grep -i "uart\|enable_uart" /boot/firmware/config.txt | grep -v "^#" | sed 's/^/   /'
else
    echo "   ❌ config.txt tidak ditemukan!"
fi
echo ""

# Check available ports
echo "3. Available Serial Ports:"
echo "   ttyAMA* ports:"
ls -1 /dev/ttyAMA* 2>/dev/null | sed 's/^/     ✓ /' || echo "     ❌ Tidak ada /dev/ttyAMA*"
echo ""
echo "   ttyS* ports:"
ls -1 /dev/ttyS* 2>/dev/null | sed 's/^/     ✓ /' || echo "     ❌ Tidak ada /dev/ttyS*"
echo ""
echo "   serial* ports:"
ls -1 /dev/serial* 2>/dev/null | sed 's/^/     ✓ /' || echo "     ❌ Tidak ada /dev/serial*"
echo ""
echo "   ttyUSB* ports (USB-to-Serial):"
ls -1 /dev/ttyUSB* 2>/dev/null | sed 's/^/     ✓ /' || echo "     (Tidak ada USB adapter)"
echo ""

# Check device tree
echo "4. Serial Devices di Device Tree:"
if [ -d /proc/device-tree/soc ]; then
    ls -1 /proc/device-tree/soc | grep serial | sed 's/^/     ✓ /' || echo "     ❌ Tidak ada serial device"
else
    echo "     ⚠️  /proc/device-tree/soc tidak tersedia"
fi
echo ""

# Check dmesg
echo "5. Recent UART Messages dari Kernel:"
dmesg | grep -i "uart\|tty.*serial" | tail -10 | sed 's/^/     /' || echo "     (Tidak ada messages)"
echo ""

# UART Mapping Info
echo "6. UART to Device Mapping:"
echo "     uart0 → /dev/ttyAMA0 or /dev/serial0 (default)"
echo "     uart1 → /dev/ttyS0 or /dev/serial1 (mini UART)"
echo "     uart2 → /dev/ttyAMA1"
echo "     uart3 → /dev/ttyAMA2  ⚠️  (Bukan ttyAMA3!)"
echo "     uart4 → /dev/ttyAMA3  ✅"
echo "     uart5 → /dev/ttyAMA4"
echo ""

# Recommendations
echo "7. Rekomendasi:"
if [ ! -f /dev/ttyAMA2 ] && [ ! -f /dev/ttyAMA3 ]; then
    echo "     ❌ ttyAMA2 dan ttyAMA3 tidak ditemukan"
    echo ""
    echo "     Solusi:"
    echo "     1. Edit /boot/config.txt dan tambahkan:"
    echo "        enable_uart=1"
    echo "        dtoverlay=uart3,pins_4_5  # Creates /dev/ttyAMA2"
    echo "        dtoverlay=uart4,pins_8_9  # Creates /dev/ttyAMA3"
    echo ""
    echo "     2. Reboot: sudo reboot"
    echo ""
    echo "     3. Setelah reboot, jalankan script ini lagi untuk verifikasi"
elif [ -f /dev/ttyAMA2 ] && [ -f /dev/ttyAMA3 ]; then
    echo "     ✅ ttyAMA2 dan ttyAMA3 tersedia!"
    echo ""
    echo "     Anda bisa menggunakan di config.py:"
    echo "     FINGERPRINT_PORTS=\"/dev/serial0,/dev/ttyAMA2,/dev/ttyAMA3\""
else
    echo "     ⚠️  Beberapa port tidak tersedia"
    echo "     Cek konfigurasi /boot/config.txt"
fi
echo ""

echo "=========================================="
echo "Selesai"
echo "=========================================="


