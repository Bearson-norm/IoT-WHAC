#!/bin/bash
# Shell script untuk menjalankan sistem local machine
# Menjalankan fingerprint_multi_client.py dan relay_controller_advanced.py secara bersamaan

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "IoT-WHAC Local System Launcher"
echo "============================================================"
echo "Starting fingerprint_multi_client.py and relay_controller_advanced.py"
echo "============================================================"

# Cek apakah Python tersedia
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 tidak ditemukan!"
    exit 1
fi

# Cek apakah script ada
if [ ! -f "fingerprint_multi_client.py" ]; then
    echo "❌ fingerprint_multi_client.py tidak ditemukan!"
    exit 1
fi

if [ ! -f "relay_controller_advanced.py" ]; then
    echo "❌ relay_controller_advanced.py tidak ditemukan!"
    exit 1
fi

# Fungsi untuk cleanup saat exit
cleanup() {
    echo ""
    echo "============================================================"
    echo "🛑 Stopping all processes..."
    echo "============================================================"
    
    # Kill semua proses Python yang terkait
    pkill -f "fingerprint_multi_client.py" 2>/dev/null
    pkill -f "relay_controller_advanced.py" 2>/dev/null
    
    # Tunggu sebentar
    sleep 2
    
    # Force kill jika masih berjalan
    pkill -9 -f "fingerprint_multi_client.py" 2>/dev/null
    pkill -9 -f "relay_controller_advanced.py" 2>/dev/null
    
    echo "✅ All processes stopped"
    echo "============================================================"
    exit 0
}

# Setup signal handlers
trap cleanup SIGINT SIGTERM

# Jalankan menggunakan Python launcher (recommended)
if [ -f "start_local_system.py" ]; then
    echo "🚀 Using Python launcher (recommended)..."
    python3 start_local_system.py
else
    # Fallback: jalankan langsung dengan background processes
    echo "⚠️  Python launcher tidak ditemukan, menggunakan fallback method..."
    echo "💡 Disarankan menggunakan start_local_system.py untuk monitoring yang lebih baik"
    echo ""
    
    # Start fingerprint client
    echo "🚀 Starting fingerprint_multi_client.py..."
    python3 fingerprint_multi_client.py > fingerprint_multi_client.log 2>&1 &
    FINGERPRINT_PID=$!
    echo "✅ Fingerprint client started (PID: $FINGERPRINT_PID)"
    
    # Tunggu sebentar
    sleep 3
    
    # Start relay controller
    echo "🚀 Starting relay_controller_advanced.py..."
    python3 relay_controller_advanced.py > relay_controller_advanced.log 2>&1 &
    RELAY_PID=$!
    echo "✅ Relay controller started (PID: $RELAY_PID)"
    
    echo ""
    echo "============================================================"
    echo "🎉 All components started!"
    echo "============================================================"
    echo "Fingerprint Client PID: $FINGERPRINT_PID"
    echo "Relay Controller PID: $RELAY_PID"
    echo "============================================================"
    echo "💡 Press Ctrl+C to stop all components"
    echo "📝 Logs:"
    echo "   - fingerprint_multi_client.log"
    echo "   - relay_controller_advanced.log"
    echo "============================================================"
    
    # Wait for processes
    wait $FINGERPRINT_PID $RELAY_PID
fi

