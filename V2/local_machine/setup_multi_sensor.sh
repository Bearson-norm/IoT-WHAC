#!/bin/bash
# Script untuk setup multi-sensor AS608
# Usage: ./setup_multi_sensor.sh

echo "=========================================="
echo "Setup Multi-Sensor AS608"
echo "=========================================="
echo ""

# Cek port yang tersedia
echo "1. Memeriksa port serial yang tersedia..."
echo "------------------------------------------"
if [ -e /dev/serial0 ]; then
    echo "✓ /dev/serial0 tersedia"
    REAL_SERIAL0=$(readlink -f /dev/serial0 2>/dev/null || echo "/dev/serial0")
    echo "  → Real path: $REAL_SERIAL0"
else
    echo "✗ /dev/serial0 tidak tersedia"
fi

if [ -e /dev/ttyAMA3 ]; then
    echo "✓ /dev/ttyAMA3 tersedia"
else
    echo "✗ /dev/ttyAMA3 tidak tersedia"
fi

echo ""
echo "2. Konfigurasi yang disarankan:"
echo "------------------------------------------"
echo "FINGERPRINT_PORTS=\"/dev/serial0,/dev/ttyAMA3\""
echo ""

# Tanya user
read -p "Apakah Anda ingin mengkonfigurasi multi-sensor sekarang? (y/n): " answer

if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
    echo "Setup dibatalkan."
    exit 0
fi

echo ""
echo "3. Pilih metode konfigurasi:"
echo "   1) Set environment variable (temporary)"
echo "   2) Edit config.py (permanent)"
echo "   3) Buat .env file (recommended)"
read -p "Pilihan (1/2/3): " method

case $method in
    1)
        echo ""
        echo "Untuk menjalankan dengan environment variable:"
        echo "export FINGERPRINT_PORTS=\"/dev/serial0,/dev/ttyAMA3\""
        echo "python3 fingerprint_multi_client.py"
        echo ""
        echo "Atau langsung:"
        echo "FINGERPRINT_PORTS=\"/dev/serial0,/dev/ttyAMA3\" python3 fingerprint_multi_client.py"
        ;;
    2)
        echo ""
        echo "Mengedit config.py..."
        # Backup config.py
        cp config.py config.py.backup
        echo "✓ Backup dibuat: config.py.backup"
        
        # Edit config.py
        sed -i 's|FINGERPRINT_PORTS = os.getenv("FINGERPRINT_PORTS", "").split(",") if os.getenv("FINGERPRINT_PORTS") else \[\]|FINGERPRINT_PORTS = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA3").split(",") if os.getenv("FINGERPRINT_PORTS") else ["/dev/serial0", "/dev/ttyAMA3"]|' config.py
        
        echo "✓ config.py telah diupdate"
        echo ""
        echo "Sekarang jalankan:"
        echo "python3 fingerprint_multi_client.py"
        ;;
    3)
        echo ""
        if [ -f .env ]; then
            echo "File .env sudah ada, membuat backup..."
            cp .env .env.backup
        fi
        
        # Buat atau update .env
        if ! grep -q "FINGERPRINT_PORTS" .env 2>/dev/null; then
            echo "" >> .env
            echo "# Multiple sensors configuration" >> .env
            echo "FINGERPRINT_PORTS=/dev/serial0,/dev/ttyAMA3" >> .env
            echo "✓ .env file telah diupdate"
        else
            sed -i 's|^FINGERPRINT_PORTS=.*|FINGERPRINT_PORTS=/dev/serial0,/dev/ttyAMA3|' .env
            echo "✓ FINGERPRINT_PORTS di .env telah diupdate"
        fi
        
        echo ""
        echo "Catatan: Program perlu diupdate untuk membaca .env file"
        echo "Atau gunakan: export \$(cat .env | xargs) && python3 fingerprint_multi_client.py"
        ;;
    *)
        echo "Pilihan tidak valid"
        ;;
esac

echo ""
echo "=========================================="
echo "Setup selesai!"
echo "=========================================="


