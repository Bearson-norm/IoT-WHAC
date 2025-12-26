# 📚 Panduan Launcher Sistem Local Machine

Panduan untuk menjalankan `fingerprint_multi_client.py` dan `relay_controller_advanced.py` secara bersamaan tanpa konflik.

---

## 🎯 Overview

Launcher ini dirancang untuk:
- ✅ Menjalankan kedua program secara bersamaan
- ✅ Mencegah konflik GPIO dan port serial
- ✅ Monitoring proses dan auto-restart jika crash
- ✅ Graceful shutdown dengan Ctrl+C
- ✅ Logging terpisah untuk setiap program

---

## 🚀 Cara Menggunakan

### Opsi 1: Python Launcher (Recommended) ⭐

**Linux/Raspberry Pi:**
```bash
cd local_machine
python3 start_local_system.py
```

**Windows:**
```powershell
cd local_machine
python start_local_system.py
```

**Keuntungan:**
- ✅ Monitoring proses otomatis
- ✅ Auto-restart jika salah satu program crash
- ✅ Logging terpusat
- ✅ Graceful shutdown

---

### Opsi 2: Shell Script (Linux/Raspberry Pi)

```bash
cd local_machine
chmod +x start_local_system.sh
./start_local_system.sh
```

**Atau:**
```bash
bash start_local_system.sh
```

---

### Opsi 3: Batch Script (Windows)

```powershell
cd local_machine
start_local_system.bat
```

---

### Opsi 4: Manual (Tidak Disarankan)

Jika ingin menjalankan manual di terminal terpisah:

**Terminal 1:**
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

**Terminal 2:**
```bash
cd local_machine
python3 relay_controller_advanced.py
```

**⚠️ Catatan:** Metode manual tidak memiliki monitoring dan auto-restart.

---

## 📊 Fitur Launcher

### 1. Process Monitoring
- Monitor status kedua proses setiap 2 detik
- Deteksi jika salah satu proses crash
- Logging status ke console dan file

### 2. Auto-Restart
- Otomatis restart program yang crash
- Delay 5 detik sebelum restart
- Maksimal restart count tracking

### 3. Graceful Shutdown
- Tekan `Ctrl+C` untuk stop semua proses
- Terminate proses dengan SIGTERM terlebih dahulu
- Force kill jika tidak merespons dalam 5 detik

### 4. Logging
- Log terpisah untuk setiap program:
  - `fingerprint_multi_client.log`
  - `relay_controller_advanced.log`
- Log launcher: `local_system.log`

---

## 🔧 Konfigurasi

### Environment Variables

Launcher menggunakan konfigurasi dari:
1. File `config.py` (untuk fingerprint client)
2. Environment variables (untuk relay controller)

**Relay Controller GPIO Pins:**
```bash
# Set di environment atau .env
export RELAY_GPIO_PIN=23      # Default: 23 (bukan 18!)
export INPUT_GPIO_PIN=24      # Default: 24
export OUTPUT_GPIO_PIN=25     # Default: 25
```

**Atau edit di `relay_controller_advanced.py`:**
```python
self.relay_pin = relay_pin or int(os.getenv('RELAY_GPIO_PIN', '23'))  # Ubah default ke 23
```

---

## 🛡️ Pencegahan Konflik

Launcher sudah dirancang untuk mencegah konflik:

### 1. GPIO Conflict Prevention
- `fingerprint_multi_client.py`: Relay control **DISABLED** (menggunakan `relay_controller_advanced.py`)
- `relay_controller_advanced.py`: Menggunakan GPIO 23, 24, 25 (bukan GPIO 18)

### 2. Port Serial Conflict Prevention
- Setiap sensor menggunakan port lock file
- Auto-detection port untuk menghindari konflik
- PID file untuk mencegah multiple instances

### 3. MQTT Client ID
- Setiap program menggunakan unique client ID
- Format: `whac_multi_fingerprint_client_{PID}_{timestamp}`

---

## 📝 Log Files

### Launcher Log
- **File**: `local_system.log`
- **Isi**: Status launcher, start/stop events, restart events

### Fingerprint Client Log
- **File**: `fingerprint_multi_client.log`
- **Isi**: Scan results, MQTT messages, enrollment events

### Relay Controller Log
- **File**: `relay_controller_advanced.log`
- **Isi**: GPIO control events, MQTT commands, door sensor status

---

## 🐛 Troubleshooting

### Masalah: Program tidak start

**Cek:**
1. Python terinstall dan di PATH
2. Dependencies terinstall: `pip install -r requirements.txt`
3. Script files ada di direktori yang benar
4. Permission untuk execute (Linux): `chmod +x start_local_system.sh`

### Masalah: GPIO Conflict

**Solusi:**
1. Pastikan `fingerprint_multi_client.py` relay control **DISABLED**:
   ```python
   # Di fingerprint_multi_client.py line 214-218
   # self.relay_pin = 18  # DISABLED
   self.relay_pin = None  # Disabled - using relay_controller_advanced.py instead
   ```

2. Pastikan `relay_controller_advanced.py` menggunakan GPIO 23 (bukan 18):
   ```python
   # Di relay_controller_advanced.py line 48
   self.relay_pin = relay_pin or int(os.getenv('RELAY_GPIO_PIN', '23'))  # Default: 23
   ```

### Masalah: Port Serial Conflict

**Solusi:**
1. Hentikan semua proses yang menggunakan port:
   ```bash
   pkill -f fingerprint_multi_client
   pkill -f relay_controller_advanced
   ```

2. Hapus lock files:
   ```bash
   rm /tmp/serial_port_*.lock
   rm /tmp/fingerprint_multi_client.pid
   ```

3. Cek port tersedia:
   ```bash
   python3 check_serial_ports.py
   ```

### Masalah: Program Crash dan Restart Loop

**Cek:**
1. Lihat log file untuk error details
2. Cek konfigurasi (config.py, environment variables)
3. Cek hardware connection (sensor, GPIO wiring)
4. Disable auto-restart sementara untuk debugging:
   ```python
   # Di start_local_system.py
   self.restart_enabled = False  # Disable auto-restart
   ```

### Masalah: Tidak Bisa Stop dengan Ctrl+C

**Solusi:**
1. Force kill processes:
   ```bash
   # Linux
   pkill -9 -f fingerprint_multi_client
   pkill -9 -f relay_controller_advanced
   
   # Windows
   taskkill /F /FI "WINDOWTITLE eq Fingerprint Client*"
   taskkill /F /FI "WINDOWTITLE eq Relay Controller*"
   ```

2. Hapus PID files:
   ```bash
   rm /tmp/fingerprint_multi_client.pid
   rm /tmp/relay_controller_advanced.pid
   ```

---

## ✅ Verifikasi Sistem Berjalan

### 1. Cek Proses
```bash
# Linux
ps aux | grep -E "fingerprint_multi_client|relay_controller_advanced"

# Windows
tasklist | findstr "python"
```

### 2. Cek Log Files
```bash
# Lihat log launcher
tail -f local_system.log

# Lihat log fingerprint client
tail -f fingerprint_multi_client.log

# Lihat log relay controller
tail -f relay_controller_advanced.log
```

### 3. Test Functionality
1. **Fingerprint Scan**: Scan fingerprint → Data muncul di Web UI
2. **Relay Control**: Klik Grant di Web UI → Relay aktif (GPIO 23 HIGH)
3. **Door Sensor**: Monitor GPIO 24 status di log

---

## 📋 Checklist Setup

Sebelum menjalankan launcher, pastikan:

- [ ] Python 3.7+ terinstall
- [ ] Dependencies terinstall (`pip install -r requirements.txt`)
- [ ] File `config.py` sudah dikonfigurasi
- [ ] Sensor fingerprint terhubung dan terdeteksi
- [ ] GPIO wiring sudah benar (relay, door sensor)
- [ ] MQTT broker dapat diakses
- [ ] Database PostgreSQL running (untuk relay controller logging)
- [ ] Tidak ada proses lain yang menggunakan GPIO/port yang sama

---

## 🔄 Alur Kerja

```
1. Launcher Start
   ↓
2. Check Existing Instances
   ↓
3. Start Fingerprint Client
   ↓
4. Wait 3 seconds
   ↓
5. Start Relay Controller
   ↓
6. Monitor Both Processes
   ↓
7. If Crash → Auto Restart (if enabled)
   ↓
8. On Ctrl+C → Graceful Shutdown
```

---

## 💡 Tips

1. **Gunakan Python Launcher**: Lebih robust dengan monitoring dan auto-restart
2. **Cek Log Files**: Selalu cek log jika ada masalah
3. **Test Satu Program Dulu**: Test `fingerprint_multi_client.py` dulu sebelum menjalankan launcher
4. **Monitor Resource**: Cek CPU dan memory usage jika sistem lambat
5. **Backup Config**: Backup `config.py` sebelum mengubah konfigurasi

---

## 📞 Bantuan

Jika masih ada masalah:
1. Cek dokumentasi di `GPIO_ALLOCATION_DAN_PROGRAM.md`
2. Cek troubleshooting di file ini
3. Lihat log files untuk error details
4. Test program secara individual untuk isolasi masalah

---

**Selamat menggunakan sistem IoT-WHAC! 🎉**

