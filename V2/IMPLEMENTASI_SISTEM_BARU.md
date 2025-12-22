# 🚀 Implementasi Sistem Baru - Unified Database dengan Modal Popup

## 📋 Ringkasan

Dokumen ini menjelaskan implementasi sistem baru yang mengintegrasikan:
1. **Unified Database** - Satu tabel untuk kedua sensor dengan `device_id` sebagai identifier
2. **Modal Popup** - Verifikasi user dan enrollment dari Web UI
3. **GPIO Control** - Kontrol pintu dengan GPIO(1), GPIO(2), dan GPIO(3)

---

## 🗄️ Database Schema Baru

### 1. Tabel `user_machine`

Tabel unified untuk menyimpan user dari kedua sensor dengan `device_id` sebagai identifier unik.

**Struktur**:
```sql
CREATE TABLE user_machine (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,                    -- ID user fingerprint dari sensor
    nama VARCHAR(100) NOT NULL,                 -- Nama user
    device_id VARCHAR(50) NOT NULL,              -- AS608_001, AS608_002 (unique identifier)
    posisi VARCHAR(100),                          -- Posisi/jabatan user
    finger_template_id INTEGER NOT NULL,         -- ID template fingerprint di sensor
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, device_id)                   -- Satu user bisa punya fingerprint di multiple device
);
```

**File**: `web_ui/database_schema_new.sql`

---

### 2. Tabel `access_log`

Tabel untuk menyimpan log akses (grant/deny) dengan format: ID, Nama, Nama Device, Status, timestamp.

**Struktur**:
```sql
CREATE TABLE access_log (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,                 -- Nama user
    device_id VARCHAR(50) NOT NULL,              -- Nama Device (AS608_001, AS608_002)
    status VARCHAR(20) NOT NULL,                 -- 'granted' atau 'denied'
    user_id INTEGER,                             -- ID user jika terdaftar (NULL jika tidak terdaftar)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50),                     -- 'scan_verified', 'scan_unverified', 'manual'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3. Tabel `gpio_log`

Tabel untuk menyimpan log status GPIO (relay control, door sensor, output control).

**Struktur**:
```sql
CREATE TABLE gpio_log (
    id SERIAL PRIMARY KEY,
    gpio_pin INTEGER NOT NULL,                   -- GPIO pin number (1, 2, 3)
    gpio_state VARCHAR(10) NOT NULL,             -- 'HIGH' atau 'LOW'
    event_type VARCHAR(50),                      -- 'relay_control', 'door_sensor', 'output_control'
    user_id INTEGER,                              -- ID user terkait (jika ada)
    device_id VARCHAR(50),                        -- Device ID terkait
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT                              -- Deskripsi event
);
```

---

## 🔄 Flow Sistem Baru

### 1. **Scan Fingerprint dari Sensor**

```
Sensor AS608 (Device 1 atau 2)
  ↓
MQTT Topic: WHAC/Store001/in
  ↓
web_ui/app.py::handle_scan_message()
  ↓
check_user_in_user_machine(fingerprint_id, device_id)
  ↓
[User Terdaftar?]
  ├─ YES → Modal Popup: Grant/Deny
  └─ NO  → Modal Popup: Daftar/Tidak
```

---

### 2. **User Terverifikasi (Terdaftar)**

**Kondisi**: User sudah terdaftar di `user_machine` dengan `device_id` yang sesuai.

**Modal Popup**:
- Menampilkan informasi user (nama, device, timestamp)
- Pilihan: **Grant** atau **Deny**

**Jika Grant**:
1. Log ke `access_log`: ID, Nama, Nama Device, Status (granted), timestamp
2. Kirim MQTT command ke `relay_controller_advanced.py`
3. GPIO(1) HIGH → wait 5s → GPIO(1) LOW
4. Monitor GPIO(2) setelah 5 detik GPIO(1) LOW
5. Log GPIO status ke `gpio_log`

**Jika Deny**:
1. Log ke `access_log`: ID, Nama, Nama Device, Status (denied), timestamp
2. Tidak ada aksi GPIO

---

### 3. **User Tidak Terverifikasi (Tidak Terdaftar)**

**Kondisi**: User tidak terdaftar di `user_machine`.

**Modal Popup**:
- Menampilkan informasi: "User tidak terdaftar"
- Pilihan: **Daftar** atau **Tidak**

**Jika Daftar**:
1. Modal form muncul dengan field:
   - Nama
   - Posisi
2. Submit → `POST /api/enroll_user_from_modal`
3. Insert ke `user_machine`: user_id, nama, device_id, posisi, finger_template_id
4. Log ke `access_log`: Status (granted) - karena user baru didaftarkan

**Jika Tidak**:
1. Log ke `access_log`: ID, Nama, Nama Device, Status (denied), timestamp
2. Tidak ada aksi GPIO

---

## 🔌 GPIO Control Logic

### GPIO Pin Configuration

- **GPIO(1)**: Relay control (OUTPUT)
  - HIGH → Aktifkan relay (buka pintu)
  - LOW → Nonaktifkan relay (tutup pintu)
  - Timing: HIGH → wait 5s → LOW

- **GPIO(2)**: Digital input (INPUT)
  - Membaca status dari sensor pintu eksternal
  - LOW = Pintu terbuka
  - HIGH = Pintu tertutup
  - Monitoring kontinyu dalam background thread

- **GPIO(3)**: Output control (OUTPUT)
  - HIGH saat GPIO(2) LOW (pintu terbuka)
  - LOW saat GPIO(2) HIGH (pintu tertutup)
  - Kontrol otomatis berdasarkan GPIO(2)

### Flow GPIO Control

```
Grant Access
  ↓
GPIO(1) = HIGH (relay aktif)
  ↓
Wait 5 seconds
  ↓
GPIO(1) = LOW (relay nonaktif)
  ↓
[Background Thread]
  ↓
Check GPIO(2) status
  ↓
Log GPIO(2) status ke database
  ↓
[Monitoring Thread - Kontinyu]
  ↓
GPIO(2) changed?
  ├─ LOW → GPIO(3) = HIGH
  └─ HIGH → GPIO(3) = LOW
```

---

## 📝 Code Changes

### 1. **web_ui/app.py**

#### Fungsi Baru:
- `check_user_in_user_machine(fingerprint_id, device_id)` - Cek apakah user terdaftar
- `log_access_to_database(nama, device_id, status, user_id, action_type)` - Log ke access_log

#### Fungsi yang Diupdate:
- `handle_scan_message()` - Sekarang check verifikasi dan emit modal
- `handle_grant_access()` - Log ke access_log dan kirim GPIO command
- `handle_deny_access()` - Log ke access_log
- `send_relay_command()` - Tambah parameter device_id dan GPIO config

#### Endpoint Baru:
- `POST /api/enroll_user_from_modal` - Enrollment user dari modal popup

---

### 2. **local_machine/relay_controller_advanced.py**

File baru untuk advanced GPIO control dengan:
- GPIO(1) control dengan timing 5 detik
- GPIO(2) monitoring kontinyu
- GPIO(3) control otomatis berdasarkan GPIO(2)
- Logging ke database PostgreSQL

**Fitur**:
- Background thread untuk monitoring GPIO(2) dan GPIO(3)
- Thread terpisah untuk check GPIO(2) setelah 5 detik GPIO(1) LOW
- Logging semua GPIO events ke `gpio_log` table

---

## 🚀 Cara Setup

### 1. Setup Database

Jalankan SQL script untuk membuat tabel baru:

```bash
psql -U postgres -d whac_master -f web_ui/database_schema_new.sql
```

Atau via Docker:
```bash
docker exec -i whac-postgres psql -U postgres -d whac_master < web_ui/database_schema_new.sql
```

### 2. Update Web UI

Tidak perlu restart, perubahan di `app.py` akan otomatis ter-load jika menggunakan auto-reload.

### 3. Setup Relay Controller

Jalankan advanced relay controller di Raspberry Pi:

```bash
cd local_machine
python3 relay_controller_advanced.py
```

Atau sebagai service:
```bash
sudo systemctl enable relay-controller-advanced.service
sudo systemctl start relay-controller-advanced.service
```

---

## 📊 Testing

### 1. Test Verifikasi User

1. Scan fingerprint dari sensor yang sudah terdaftar
2. Modal popup harus muncul dengan pilihan Grant/Deny
3. Pilih Grant → Cek `access_log` dan `gpio_log`

### 2. Test Enrollment

1. Scan fingerprint dari sensor yang belum terdaftar
2. Modal popup harus muncul dengan pilihan Daftar/Tidak
3. Pilih Daftar → Isi form → Submit
4. Cek `user_machine` dan `access_log`

### 3. Test GPIO Control

1. Grant access dari Web UI
2. Monitor GPIO(1) → harus HIGH selama 5 detik, lalu LOW
3. Monitor GPIO(2) → harus ter-log setelah 5 detik GPIO(1) LOW
4. Monitor GPIO(3) → harus HIGH saat GPIO(2) LOW, LOW saat GPIO(2) HIGH

---

## 🔍 Monitoring & Logging

### 1. Access Log

Query untuk melihat log akses:
```sql
SELECT * FROM access_log_detail 
ORDER BY timestamp DESC 
LIMIT 50;
```

### 2. GPIO Log

Query untuk melihat log GPIO:
```sql
SELECT * FROM gpio_log_detail 
ORDER BY timestamp DESC 
LIMIT 50;
```

### 3. User Machine

Query untuk melihat user terdaftar:
```sql
SELECT * FROM user_machine 
ORDER BY created_at DESC;
```

---

## ⚠️ Catatan Penting

1. **GPIO Pin Numbers**: 
   - Pastikan GPIO pin sesuai dengan hardware (GPIO 1, 2, 3 di BCM numbering)
   - GPIO(2) harus menggunakan pull-up resistor (PUD_UP)

2. **Database Connection**:
   - `relay_controller_advanced.py` perlu koneksi ke PostgreSQL
   - Pastikan database credentials benar di environment variables

3. **MQTT Connection**:
   - Pastikan MQTT broker accessible dari Raspberry Pi
   - Check firewall rules jika perlu

4. **Threading**:
   - Monitoring thread berjalan kontinyu
   - Pastikan cleanup dilakukan saat shutdown

---

## 📚 File-File Terkait

- `web_ui/database_schema_new.sql` - Database schema baru
- `web_ui/app.py` - Web UI dengan flow baru
- `local_machine/relay_controller_advanced.py` - Advanced GPIO controller
- `STRUKTUR_DATABASE_DAN_HANDLING.md` - Dokumentasi struktur database

---

## ✅ Checklist Implementasi

- [x] Database schema baru (user_machine, access_log, gpio_log)
- [x] Fungsi verifikasi user di app.py
- [x] Update handle_scan_message untuk emit modal
- [x] Endpoint enrollment dari modal
- [x] Update grant/deny untuk log ke access_log
- [x] Advanced relay controller dengan GPIO(1), GPIO(2), GPIO(3)
- [x] GPIO monitoring dan logging
- [ ] Frontend modal popup (perlu update di index.html)
- [ ] Testing end-to-end

---

*Dokumen ini dibuat untuk menjelaskan implementasi sistem baru dengan unified database dan modal popup.*



