# Analisis Integrasi Multi-Sensor: serial0 dan ttyAMA3

## 📋 Status Integrasi Saat Ini

### ✅ **SUDAH TERINTEGRASI**

#### 1. **Backend (local_machine)**
- ✅ File `fingerprint_multi_client.py` sudah ada dan mendukung multi-sensor
- ✅ Konfigurasi menggunakan `FINGERPRINT_PORTS` untuk multiple sensors
- ✅ Setiap sensor memiliki `device_id` unik (AS608_001, AS608_002, dll)
- ✅ Data dikirim ke MQTT topic `WHAC/Store001/in` dengan format yang sama
- ✅ Format JSON sudah termasuk `device_id` untuk identifikasi sensor

#### 2. **Backend (web_ui/app.py)**
- ✅ Web UI sudah subscribe ke MQTT topic `WHAC/Store001/in`
- ✅ Handler `handle_scan_message()` sudah menerima `device_id` dari payload (line 277)
- ✅ Data `device_id` dikirim ke WebSocket sebagai bagian dari `scan_data`
- ✅ Database sudah bisa menyimpan data dari multiple sensors

#### 3. **Komunikasi MQTT**
- ✅ Format data konsisten antara single dan multi-sensor
- ✅ Topic yang sama: `WHAC/Store001/in`
- ✅ Perbedaan hanya pada field `device_id`

---

## ⚠️ **YANG PERLU DIPERBAIKI**

### 1. **UI Belum Menampilkan Device ID**

**Masalah:**
- Modal scan notification tidak menampilkan informasi sensor (device_id)
- Tabel logs tidak memiliki kolom untuk device_id
- User tidak bisa melihat sensor mana yang mendeteksi fingerprint

**Lokasi yang perlu diperbaiki:**
- `web_ui/templates/index.html` - Modal scan notification (line 340-344)
- `web_ui/templates/index.html` - Tabel logs (line 188-196)
- `web_ui/templates/admin.html` - Tabel logs (jika ada)

---

## 🔧 Konfigurasi untuk 2 Sensor (serial0 dan ttyAMA3)

### **Langkah 1: Konfigurasi Hardware**

Pastikan kedua sensor terhubung dengan benar:
- **Sensor 1**: `/dev/serial0` (GPIO UART primary)
- **Sensor 2**: `/dev/ttyAMA3` (GPIO UART setelah enable uart3)

**Untuk mengaktifkan ttyAMA3 di Raspberry Pi:**
```bash
sudo nano /boot/config.txt
```

Tambahkan:
```
dtoverlay=uart3
```

Reboot:
```bash
sudo reboot
```

### **Langkah 2: Konfigurasi Software**

#### **Opsi A: Environment Variable (Recommended)**

Edit file `.env` di folder `local_machine/`:
```bash
cd local_machine
cp env.example .env
nano .env
```

Tambahkan:
```bash
FINGERPRINT_PORTS=/dev/serial0,/dev/ttyAMA3
```

#### **Opsi B: Edit config.py**

Edit `local_machine/config.py`:
```python
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/ttyAMA3"]
```

### **Langkah 3: Set Permissions**

```bash
sudo chmod 666 /dev/serial0
sudo chmod 666 /dev/ttyAMA3
sudo usermod -a -G dialout $USER
```

### **Langkah 4: Jalankan Program**

```bash
cd local_machine
python3 fingerprint_multi_client.py
```

**Output yang diharapkan:**
```
[AS608_001] ✓ Sensor connected! Templates: X
[AS608_002] ✓ Sensor connected! Templates: Y
✅ 2/2 sensors connected successfully
✓ MQTT broker connected successfully!
[AS608_001] Starting standby scanning on /dev/serial0...
[AS608_002] Starting standby scanning on /dev/ttyAMA3...
```

---

## 📡 Format Data MQTT

### **Dari Sensor 1 (serial0):**
```json
{
  "store_id": "Store001",
  "timestamp": "2024-01-15T10:30:45.123456",
  "status": "Match",
  "fingerprint_id": 5,
  "device_id": "AS608_001",
  "username": "John Doe",
  "confidence": 85
}
```

### **Dari Sensor 2 (ttyAMA3):**
```json
{
  "store_id": "Store001",
  "timestamp": "2024-01-15T10:30:47.234567",
  "status": "Match",
  "fingerprint_id": 5,
  "device_id": "AS608_002",
  "username": "John Doe",
  "confidence": 88
}
```

**Perbedaan:** Hanya field `device_id` yang berbeda untuk mengidentifikasi sensor.

---

## 🔄 Alur Data Lengkap

```
┌─────────────────┐
│  Sensor 1       │
│  /dev/serial0   │──┐
│  device_id:     │  │
│  AS608_001      │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │     ┌──────────────┐     ┌──────────────┐
│  Sensor 2       │  │     │              │     │              │
│  /dev/ttyAMA3   │──┼────▶│  MQTT Broker  │────▶│   Web UI     │
│  device_id:     │  │     │              │     │   (app.py)   │
│  AS608_002      │  │     │  103.87.67.  │     │              │
└─────────────────┘  │     │  139:1883    │     │  PostgreSQL  │
                     │     │              │     │              │
local_machine/       │     └──────────────┘     └──────────────┘
fingerprint_multi_   │
client.py            │
                     │
Topic: WHAC/Store001/in
```

---

## ✅ Verifikasi Integrasi

### **Test 1: Cek Koneksi Sensor**
```bash
cd tests
python3 debug_fingerprint_connection.py
```

### **Test 2: Cek MQTT Messages**
```bash
# Subscribe ke MQTT topic
mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/in" -v
```

### **Test 3: Cek Web UI**
1. Buka browser: `http://localhost:5000`
2. Login ke dashboard
3. Scan fingerprint di sensor 1 → Modal harus muncul
4. Scan fingerprint di sensor 2 → Modal harus muncul
5. Cek tabel logs → Data harus masuk (tapi device_id belum ditampilkan)

---

## 🎯 Kesimpulan

### **Status: 90% Terintegrasi** ✅

**Yang Sudah Bekerja:**
- ✅ Multi-sensor support di local_machine
- ✅ MQTT communication
- ✅ Web UI menerima data dari multiple sensors
- ✅ Database menyimpan data dengan device_id

**Yang Perlu Diperbaiki:**
- ⚠️ UI belum menampilkan device_id di modal dan tabel
- ⚠️ User tidak bisa melihat sensor mana yang mendeteksi

**Rekomendasi:**
1. Tambahkan kolom "Sensor" atau "Device ID" di tabel logs
2. Tampilkan device_id di modal scan notification
3. Tambahkan filter berdasarkan sensor di dashboard

---

## 📝 Catatan Penting

1. **Port Mapping:**
   - `/dev/serial0` → AS608_001
   - `/dev/ttyAMA3` → AS608_002

2. **Device ID Format:**
   - Sensor pertama: `AS608_001`
   - Sensor kedua: `AS608_002`
   - Format: `AS608_{index+1:03d}`

3. **MQTT Topic:**
   - Sama untuk semua sensor: `WHAC/Store001/in`
   - Pembeda: field `device_id` dalam payload

4. **Threading:**
   - Setiap sensor memiliki thread scanning sendiri
   - Tidak saling blocking
   - Bisa scan bersamaan

---

## 🚀 Langkah Selanjutnya

Jika ingin menampilkan device_id di UI, perlu:
1. Update modal scan notification untuk menampilkan device_id
2. Tambahkan kolom device_id di tabel logs
3. Update query database untuk include device_id
4. Tambahkan filter berdasarkan sensor (opsional)

Apakah Anda ingin saya implementasikan perbaikan UI untuk menampilkan device_id?



