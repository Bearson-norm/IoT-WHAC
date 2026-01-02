# 🔄 Handling Fallback: Auto-Detection ttyAMA Ports

## 📋 Overview

Sistem sekarang memiliki handling otomatis untuk mencoba port ttyAMA lainnya secara berurutan jika port yang dikonfigurasi (misalnya ttyAMA3) gagal connect.

## 🔧 Cara Kerja

### **1. Urutan Pencobaan Port**

Jika sensor gagal connect ke port yang dikonfigurasi, sistem akan mencoba port ttyAMA secara berurutan:

1. `/dev/ttyAMA1` (uart2)
2. `/dev/ttyAMA2` (uart3)
3. `/dev/ttyAMA3` (uart4) ⚠️ Port yang dikonfigurasi
4. `/dev/ttyAMA4` (uart5)
5. `/dev/ttyAMA5` (uart tambahan)
6. `/dev/ttyAMA0` (uart0, biasanya sudah digunakan)

**Catatan:** Sistem akan melewati port yang:
- Sudah digunakan oleh sensor lain
- Tidak ada di sistem
- Sudah dicoba dan gagal

### **2. Log Output**

Saat fallback aktif, Anda akan melihat log seperti ini:

```
[AS608_002] 🔍 Looking for alternative ttyAMA ports...
[AS608_002] Will try ttyAMA ports in order: ttyAMA1, ttyAMA2, ttyAMA3, ttyAMA4, ttyAMA5
[AS608_002] Found 4 alternative ttyAMA port(s): ['/dev/ttyAMA1', '/dev/ttyAMA2', '/dev/ttyAMA4', '/dev/ttyAMA5']
[AS608_002] [1/4] Trying alternative port: /dev/ttyAMA1
[AS608_002] ❌ Failed to connect to /dev/ttyAMA1, trying next port...
[AS608_002] [2/4] Trying alternative port: /dev/ttyAMA2
[AS608_002] ✅ Successfully connected to alternative port /dev/ttyAMA2!
[AS608_002] Port changed from /dev/ttyAMA3 to /dev/ttyAMA2
```

### **3. Final Port Assignment**

Setelah semua sensor connect (atau gagal), sistem akan menampilkan final port assignments:

```
📋 Final port assignments:
  ✓ AS608_001: /dev/serial0
  ✓ AS608_002: /dev/ttyAMA2  (changed from /dev/ttyAMA3)
```

## 🚀 Contoh Skenario

### **Skenario 1: ttyAMA3 Gagal, ttyAMA2 Berhasil**

**Konfigurasi:**
```python
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/ttyAMA3"]
```

**Hasil:**
- Sensor 1: `/dev/serial0` → ✅ Connect
- Sensor 2: `/dev/ttyAMA3` → ❌ Gagal
  - Mencoba `/dev/ttyAMA1` → ❌ Gagal
  - Mencoba `/dev/ttyAMA2` → ✅ Berhasil!
  - Final: Sensor 2 menggunakan `/dev/ttyAMA2`

### **Skenario 2: ttyAMA3 Gagal, Semua Alternatif Gagal**

**Konfigurasi:**
```python
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/ttyAMA3"]
```

**Hasil:**
- Sensor 1: `/dev/serial0` → ✅ Connect
- Sensor 2: `/dev/ttyAMA3` → ❌ Gagal
  - Mencoba semua ttyAMA ports → ❌ Semua gagal
  - Mencoba auto-detection umum → ❌ Tidak ada sensor terdeteksi
  - Final: Sensor 2 tidak connect

### **Skenario 3: Multi-Sensor dengan Fallback**

**Konfigurasi:**
```python
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/ttyAMA3", "/dev/ttyAMA4"]
```

**Hasil:**
- Sensor 1: `/dev/serial0` → ✅ Connect
- Sensor 2: `/dev/ttyAMA3` → ❌ Gagal → Fallback ke `/dev/ttyAMA2` → ✅ Berhasil
- Sensor 3: `/dev/ttyAMA4` → ❌ Gagal → Fallback ke `/dev/ttyAMA5` → ✅ Berhasil
- Final: 3 sensor connect dengan port yang berbeda dari konfigurasi

## ⚙️ Konfigurasi

### **Default Behavior**

Sistem akan otomatis mencoba fallback jika:
1. Port yang dikonfigurasi tidak ada
2. Port yang dikonfigurasi gagal connect setelah 3 retry
3. Sensor tidak merespons di port yang dikonfigurasi

### **Mengubah Urutan Pencobaan**

Jika ingin mengubah urutan, edit fungsi `find_alternative_ttyama_ports` di `fingerprint_multi_client.py`:

```python
# Urutan default: ttyAMA1, ttyAMA2, ttyAMA3, ttyAMA4, ttyAMA5
preferred_order = ['/dev/ttyAMA1', '/dev/ttyAMA2', '/dev/ttyAMA3', '/dev/ttyAMA4', '/dev/ttyAMA5', '/dev/ttyAMA0']
```

### **Mengubah Start Port**

Untuk mulai dari port tertentu (misalnya ttyAMA2), edit di `connect_all_sensors`:

```python
alternative_ports = self.find_alternative_ttyama_ports(
    exclude_ports=connected_ports,
    start_from='/dev/ttyAMA2'  # Start from ttyAMA2 instead of ttyAMA1
)
```

## 📊 Monitoring

### **Cek Status Fallback**

Saat program berjalan, perhatikan log untuk:
- `🔍 Looking for alternative ttyAMA ports...` - Fallback dimulai
- `[X/Y] Trying alternative port: ...` - Mencoba port ke-X dari Y alternatif
- `✅ Successfully connected to alternative port` - Fallback berhasil
- `⚠️ All X ttyAMA alternative ports failed` - Semua alternatif gagal

### **Final Status**

Di akhir koneksi, cek:
```
📋 Final port assignments:
  ✓ AS608_001: /dev/serial0
  ✓ AS608_002: /dev/ttyAMA2  (mungkin berbeda dari konfigurasi)
```

## 🔍 Troubleshooting

### **Semua Port Gagal**

Jika semua port ttyAMA gagal:

1. **Cek apakah port ada:**
   ```bash
   ls -la /dev/ttyAMA*
   ```

2. **Cek apakah UART aktif:**
   ```bash
   dmesg | grep ttyAMA
   ```

3. **Cek konfigurasi `/boot/config.txt`:**
   ```bash
   grep uart /boot/config.txt
   ```

4. **Test port manual:**
   ```bash
   python3 test_uart_ports.py /dev/ttyAMA1 /dev/ttyAMA2 /dev/ttyAMA3
   ```

### **Port Terdeteksi Tapi Sensor Tidak Connect**

Jika port ada tapi sensor tidak connect:

1. **Cek koneksi hardware:**
   - Pastikan TX/RX terhubung dengan benar
   - Pastikan power supply (5V dan GND)

2. **Cek baudrate:**
   - Default: 57600
   - Pastikan sensor dikonfigurasi dengan baudrate yang sama

3. **Cek apakah port sedang digunakan:**
   ```bash
   sudo lsof /dev/ttyAMA2
   ```

### **Port Berubah Setiap Kali**

Jika port berubah setiap kali program dijalankan:

1. **Ini normal** jika sensor fisik terhubung ke port yang berbeda
2. **Untuk konsistensi**, pastikan hardware terhubung ke port yang sama
3. **Atau** update konfigurasi setelah mengetahui port yang benar

## ✅ Best Practices

1. **Setelah mengetahui port yang benar**, update konfigurasi:
   ```python
   # Di config.py
   env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA2")
   ```

2. **Monitor log** untuk melihat port yang digunakan:
   - Jika port selalu berubah, kemungkinan ada masalah hardware

3. **Test port sebelum digunakan**:
   ```bash
   python3 test_uart_ports.py /dev/ttyAMA1 /dev/ttyAMA2 /dev/ttyAMA3
   ```

4. **Pastikan UART aktif** di `/boot/config.txt` untuk port yang ingin digunakan

## 📝 Catatan

- Fallback hanya aktif untuk port ttyAMA yang gagal
- Port yang sudah connect tidak akan diubah
- Sistem akan melewati port yang sudah digunakan oleh sensor lain
- Urutan pencobaan: ttyAMA1 → ttyAMA2 → ttyAMA3 → ttyAMA4 → ttyAMA5

---

**Sistem sekarang memiliki handling otomatis untuk mencoba port alternatif jika port yang dikonfigurasi gagal!** 🎉

