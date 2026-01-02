# 🔄 Fitur Auto Fallback Port untuk Multi-Sensor

## ✅ Fitur Baru

Program `fingerprint_multi_client.py` sekarang memiliki **automatic fallback mechanism** yang akan secara otomatis mencari port alternatif jika port yang dikonfigurasi gagal terhubung.

## 🎯 Cara Kerja

### **1. Koneksi Normal**

Program akan mencoba connect ke port yang dikonfigurasi di `config.py`:
- Sensor 1: `/dev/serial0`
- Sensor 2: `/dev/ttyAMA3`

### **2. Jika Port Gagal**

Jika port yang dikonfigurasi gagal terhubung (misalnya `ttyAMA3` tidak ada atau sensor tidak merespons), program akan:

1. **Untuk port ttyAMA yang gagal:**
   - Otomatis mencari port ttyAMA alternatif yang tersedia
   - Prioritas: `ttyAMA2` → `ttyAMA3` → `ttyAMA4` → `ttyAMA5` → `ttyAMA1` → `ttyAMA0`
   - Mencoba connect ke setiap port alternatif sampai berhasil
   - Jika semua ttyAMA gagal, akan mencoba auto-detect umum

2. **Untuk port non-ttyAMA yang gagal:**
   - Mencoba auto-detect umum untuk mencari sensor AS608 di port manapun

### **3. Logging**

Program akan menampilkan log detail tentang:
- Port yang dicoba
- Port alternatif yang ditemukan
- Port yang berhasil digunakan
- Final port assignment untuk setiap sensor

## 📋 Contoh Skenario

### **Skenario 1: ttyAMA3 Tidak Ada**

**Konfigurasi:**
```python
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/ttyAMA3"]
```

**Jika ttyAMA3 tidak ada:**
```
[AS608_002] Failed to connect to /dev/ttyAMA3
🔄 Attempting to find alternative ports for 1 failed sensor(s)...
[AS608_002] 🔍 Looking for alternative ttyAMA ports...
[AS608_002] Found 4 alternative ttyAMA port(s): ['/dev/ttyAMA2', '/dev/ttyAMA4', '/dev/ttyAMA5', '/dev/ttyAMA1']
[AS608_002] Trying alternative port: /dev/ttyAMA2
[AS608_002] ✅ Successfully connected to alternative port /dev/ttyAMA2!
✅ 2/2 sensors connected successfully
📋 Final port assignments:
  ✓ AS608_001: /dev/serial0
  ✓ AS608_002: /dev/ttyAMA2
```

### **Skenario 2: ttyAMA3 Ada Tapi Sensor Tidak Merespons**

**Konfigurasi:**
```python
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/ttyAMA3"]
```

**Jika sensor di ttyAMA3 tidak merespons:**
```
[AS608_002] Failed to connect to /dev/ttyAMA3
🔄 Attempting to find alternative ports for 1 failed sensor(s)...
[AS608_002] 🔍 Looking for alternative ttyAMA ports...
[AS608_002] Found 4 alternative ttyAMA port(s): ['/dev/ttyAMA2', '/dev/ttyAMA4', '/dev/ttyAMA5', '/dev/ttyAMA1']
[AS608_002] Trying alternative port: /dev/ttyAMA2
[AS608_002] ✅ Successfully connected to alternative port /dev/ttyAMA2!
✅ 2/2 sensors connected successfully
```

### **Skenario 3: Semua ttyAMA Gagal**

**Jika semua port ttyAMA gagal:**
```
[AS608_002] All ttyAMA alternatives failed, trying general auto-detection...
[AS608_002] 🔍 Auto-detecting fingerprint sensor port...
[AS608_002] Testing 6 available ports...
[AS608_002] ✅ AS608 found on /dev/ttyUSB0!
[AS608_002] ✅ Auto-detected alternative port: /dev/ttyUSB0
✅ 2/2 sensors connected successfully
```

## 🔧 Konfigurasi

### **Default Configuration**

File `config.py` sudah dikonfigurasi untuk 2 sensor:
```python
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA3")
```

### **Cara Kerja Fallback**

1. Program mencoba connect ke port yang dikonfigurasi
2. Jika gagal, program akan:
   - Untuk ttyAMA: mencari ttyAMA alternatif (ttyAMA2, ttyAMA4, ttyAMA5, dll)
   - Untuk non-ttyAMA: melakukan auto-detect umum
3. Program akan mencoba setiap alternatif sampai berhasil atau semua gagal
4. Final port assignment akan ditampilkan di log

## 📊 Prioritas Port Alternatif

Untuk port ttyAMA yang gagal, prioritas alternatif:
1. `/dev/ttyAMA2` (uart3)
2. `/dev/ttyAMA3` (uart4) - biasanya yang dikonfigurasi
3. `/dev/ttyAMA4` (uart5)
4. `/dev/ttyAMA5` (jika ada)
5. `/dev/ttyAMA1` (uart2)
6. `/dev/ttyAMA0` (uart0, biasanya digunakan untuk serial0)

## ⚠️ Catatan Penting

1. **Port Lock:**
   - Program akan otomatis release port lock pada port yang gagal
   - Port lock baru akan dibuat untuk port alternatif yang berhasil

2. **Port yang Sudah Digunakan:**
   - Program tidak akan mencoba port yang sudah digunakan oleh sensor lain
   - Setiap sensor akan mendapat port yang unik

3. **Auto-Detection:**
   - Auto-detection akan test setiap port untuk mencari sensor AS608
   - Hanya port yang benar-benar memiliki sensor AS608 yang akan digunakan

4. **Logging:**
   - Semua proses fallback akan di-log dengan detail
   - Final port assignment akan ditampilkan di akhir

## 🚀 Manfaat

1. **Fleksibilitas:**
   - Tidak perlu mengubah config jika port tertentu tidak tersedia
   - Program akan otomatis mencari alternatif

2. **Robustness:**
   - Program tetap bisa berjalan meskipun ada port yang gagal
   - Tidak perlu manual intervention

3. **User-Friendly:**
   - User tidak perlu tahu port mana yang tersedia
   - Program akan otomatis menemukan port yang bekerja

## 📝 Contoh Log Lengkap

```
🔧 Configuring 2 sensors from FINGERPRINT_PORTS
📌 Sensor 1: AS608_001 -> /dev/serial0
📌 Sensor 2: AS608_002 -> /dev/ttyAMA3
[AS608_001] Connecting to sensor on /dev/serial0 (attempt 1)
[AS608_001] ✓ Sensor connected! Templates: 5
[AS608_002] Connecting to sensor on /dev/ttyAMA3 (attempt 1)
[AS608_002] Connection attempt 1 failed: Failed to read data from sensor
[AS608_002] Connecting to sensor on /dev/ttyAMA3 (attempt 2)
[AS608_002] Connection attempt 2 failed: Failed to read data from sensor
[AS608_002] Connecting to sensor on /dev/ttyAMA3 (attempt 3)
[AS608_002] Connection attempt 3 failed: Failed to read data from sensor
[AS608_002] Failed to connect to /dev/ttyAMA3
🔄 Attempting to find alternative ports for 1 failed sensor(s)...
[AS608_002] 🔍 Looking for alternative ttyAMA ports...
[AS608_002] Found 4 alternative ttyAMA port(s): ['/dev/ttyAMA2', '/dev/ttyAMA4', '/dev/ttyAMA5', '/dev/ttyAMA1']
[AS608_002] Trying alternative port: /dev/ttyAMA2
[AS608_002] Connecting to sensor on /dev/ttyAMA2 (attempt 1)
[AS608_002] ✓ Sensor connected! Templates: 3
[AS608_002] ✅ Successfully connected to alternative port /dev/ttyAMA2!
✅ 2/2 sensors connected successfully
📋 Final port assignments:
  ✓ AS608_001: /dev/serial0
  ✓ AS608_002: /dev/ttyAMA2
```

## ✅ Checklist

- [x] Fitur auto fallback sudah diimplementasi
- [x] Support untuk ttyAMA alternatif
- [x] Support untuk auto-detect umum
- [x] Port lock handling
- [x] Detailed logging
- [x] Final port assignment display

---

**Fitur ini membuat program lebih robust dan user-friendly. Program akan otomatis mencari port alternatif jika port yang dikonfigurasi gagal!** 🎉

