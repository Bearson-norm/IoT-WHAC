# Perbaikan Overlapping Handling

## Masalah yang Diperbaiki

Program utama di folder `local_machine` memiliki beberapa masalah overlapping yang dapat menyebabkan konflik ketika beberapa program berjalan bersamaan. Berikut adalah perbaikan yang telah dilakukan:

### 1. ✅ Port Conflict Detection (Konflik Serial Port)

**Masalah:**
- Beberapa program dapat mencoba menggunakan serial port yang sama secara bersamaan
- Tidak ada mekanisme locking yang mencegah konflik

**Solusi:**
- Menambahkan file-based locking untuk setiap serial port
- Lock file disimpan di `/tmp/serial_port_{port_name}.lock`
- Program akan mengecek apakah port sudah digunakan oleh proses lain
- Jika proses lain sudah tidak berjalan, lock file lama akan dihapus otomatis

**File yang diperbaiki:**
- `fingerprint_simple_client.py` - Method `acquire_port_lock()` dan `release_port_lock()`
- `fingerprint_multi_client.py` - Method `acquire_port_lock()` di class `SensorConnection`

### 2. ✅ MQTT Client ID Conflicts (Konflik ID Klien MQTT)

**Masalah:**
- Client ID MQTT tidak unik, dapat menyebabkan konflik jika beberapa instance berjalan
- Client ID statis: `"whac_fingerprint_client"` dan `"whac_multi_fingerprint_client"`

**Solusi:**
- Client ID dibuat unik dengan menambahkan PID proses dan timestamp
- Format: `whac_fingerprint_client_{PID}_{timestamp}`
- Setiap instance program akan memiliki client ID yang berbeda

**File yang diperbaiki:**
- `fingerprint_simple_client.py` - Method `connect_mqtt()`
- `fingerprint_multi_client.py` - Method `connect_mqtt()`

### 3. ✅ GPIO Pin Conflict (Konflik Pin GPIO)

**Masalah:**
- Beberapa program mencoba mengontrol GPIO pin 18 (relay) secara bersamaan
- Tidak ada pengecekan apakah GPIO sudah digunakan oleh proses lain

**Solusi:**
- Menambahkan file-based locking untuk GPIO pin
- Lock file disimpan di `/tmp/gpio_pin_{pin_number}.lock`
- Program akan mengecek dan menolak jika GPIO sudah digunakan
- Lock file akan dihapus saat program selesai

**File yang diperbaiki:**
- `fingerprint_simple_client.py` - Method `setup_gpio()`
- `fingerprint_multi_client.py` - Method `setup_gpio()`

### 4. ✅ Database File Conflicts (Konflik File Database)

**Masalah:**
- `fingerprint_simple_client.py` dan `fingerprint_multi_client.py` menggunakan database file yang sama: `fingerprints.db`
- Dapat menyebabkan SQLite locking issues jika kedua program berjalan bersamaan

**Solusi:**
- Menggunakan database file terpisah untuk setiap program:
  - `fingerprint_simple_client.py` → `fingerprints_simple.db`
  - `fingerprint_multi_client.py` → `fingerprints_multi.db`
- Menambahkan timeout pada semua koneksi SQLite (10 detik) untuk menangani concurrent access dengan lebih baik

**File yang diperbaiki:**
- `fingerprint_simple_client.py` - Semua `sqlite3.connect()` calls
- `fingerprint_multi_client.py` - Semua `sqlite3.connect()` calls

### 5. ✅ Instance Detection (Deteksi Instance Ganda)

**Masalah:**
- Tidak ada mekanisme untuk mencegah beberapa instance dari program yang sama berjalan bersamaan
- Dapat menyebabkan resource conflicts dan behavior yang tidak terduga

**Solusi:**
- Menambahkan PID file untuk setiap program:
  - `fingerprint_simple_client.py` → `/tmp/fingerprint_simple_client.pid`
  - `fingerprint_multi_client.py` → `/tmp/fingerprint_multi_client.pid`
- Program akan mengecek apakah instance lain sudah berjalan
- Jika instance lain masih aktif, program akan menolak untuk start dan memberikan pesan error
- PID file akan dihapus otomatis saat program selesai

**File yang diperbaiki:**
- `fingerprint_simple_client.py` - Method `check_existing_instance()`
- `fingerprint_multi_client.py` - Method `check_existing_instance()`

## Cara Kerja Locking Mechanism

### Port Locking
```python
# Lock file: /tmp/serial_port_{port_name}.lock
# Isi: PID dari proses yang menggunakan port
# Pengecekan: Sebelum membuka serial port, program akan:
# 1. Cek apakah lock file ada
# 2. Jika ada, cek apakah proses masih berjalan
# 3. Jika proses sudah mati, hapus lock file lama
# 4. Buat lock file baru dengan PID saat ini
```

### GPIO Locking
```python
# Lock file: /tmp/gpio_pin_{pin_number}.lock
# Isi: PID dari proses yang menggunakan GPIO
# Pengecekan: Sebelum setup GPIO, program akan:
# 1. Cek apakah lock file ada
# 2. Jika ada dan proses masih berjalan, tolak dan exit
# 3. Jika proses sudah mati, hapus lock file lama
# 4. Buat lock file baru dengan PID saat ini
```

### PID File
```python
# PID file: /tmp/fingerprint_{program_name}.pid
# Isi: PID dari proses yang sedang berjalan
# Pengecekan: Saat program start, akan:
# 1. Cek apakah PID file ada
# 2. Jika ada, cek apakah proses masih berjalan
# 3. Jika proses masih berjalan, tolak dan exit
# 4. Jika proses sudah mati, hapus PID file lama
# 5. Buat PID file baru dengan PID saat ini
```

## Cleanup Mechanism

Semua lock files dan PID files akan dihapus otomatis saat program selesai melalui method `cleanup()`:
- Port locks akan dilepas saat sensor disconnect
- GPIO locks akan dilepas saat cleanup
- PID files akan dihapus saat cleanup

## Kompatibilitas

- **Unix/Linux (Raspberry Pi)**: ✅ Fully supported dengan file locking
- **Windows**: ⚠️ File locking tidak tersedia, tetapi program tetap berjalan (hanya tanpa protection)
- **macOS**: ✅ Fully supported dengan file locking

## Testing

Untuk menguji perbaikan ini:

1. **Test Port Conflict:**
   ```bash
   # Terminal 1
   python3 fingerprint_simple_client.py
   
   # Terminal 2 (harus ditolak)
   python3 fingerprint_simple_client.py
   # Expected: Error message tentang port sudah digunakan
   ```

2. **Test Instance Detection:**
   ```bash
   # Terminal 1
   python3 fingerprint_multi_client.py
   
   # Terminal 2 (harus ditolak)
   python3 fingerprint_multi_client.py
   # Expected: Error message tentang instance lain sudah berjalan
   ```

3. **Test GPIO Conflict:**
   ```bash
   # Terminal 1
   python3 fingerprint_simple_client.py
   
   # Terminal 2 (harus ditolak jika menggunakan GPIO yang sama)
   python3 relay_controller.py
   # Expected: Error message tentang GPIO sudah digunakan
   ```

## Catatan Penting

1. **Lock Files**: Lock files disimpan di `/tmp/` dan akan otomatis terhapus saat sistem reboot
2. **Stale Locks**: Jika program crash tanpa cleanup, lock files mungkin tertinggal. Program akan otomatis menghapus lock file jika proses yang terkait sudah tidak berjalan
3. **Manual Cleanup**: Jika perlu, lock files dapat dihapus manual:
   ```bash
   rm /tmp/serial_port_*.lock
   rm /tmp/gpio_pin_*.lock
   rm /tmp/fingerprint_*.pid
   ```

## Kesimpulan

Semua masalah overlapping handling telah diperbaiki:
- ✅ Port conflicts - DICEK dan DITOLAK
- ✅ MQTT client ID conflicts - DIBUAT UNIK
- ✅ GPIO conflicts - DICEK dan DITOLAK
- ✅ Database conflicts - DIPISAHKAN FILE
- ✅ Multiple instances - DICEK dan DITOLAK

Program sekarang aman untuk dijalankan tanpa khawatir konflik resource.






