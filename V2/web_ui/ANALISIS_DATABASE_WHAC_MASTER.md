# 📊 Analisis Database `whac_master` - Struktur dan Sumber Data

## 🎯 Ringkasan

Dokumen ini menjelaskan struktur database `whac_master`, dari mana sumber datanya, dan masalah-masalah yang ditemukan terkait hubungan antar tabel dan informasi yang kurang.

---

## 📁 Struktur Database `whac_master`

Database `whac_master` adalah database PostgreSQL yang digunakan untuk menyimpan semua data sistem WHAC (Fingerprint Access Control). Database ini dibuat melalui file `web_ui/database_setup.sql` dan diinisialisasi oleh `web_ui/init_db.py`.

### 📋 Tabel-Tabel Utama

#### 1. **`web_users`** - User Web UI
**Fungsi**: Menyimpan data user untuk autentikasi dan akses ke Web UI

**Kolom**:
- `id` (SERIAL PRIMARY KEY)
- `username` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR)
- `full_name`, `email`, `role`, `is_active`
- `created_at`, `last_login`, `login_attempts`, `locked_until`

**Sumber Data**:
- Dibuat melalui Web UI (form create user)
- Default admin user dibuat saat inisialisasi database

---

#### 2. **`user_sessions`** - Session User Web UI
**Fungsi**: Menyimpan session token untuk autentikasi user Web UI

**Kolom**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - **Foreign Key ke `web_users.id`** ✅
- `session_token` (VARCHAR, UNIQUE)
- `created_at`, `expires_at`, `ip_address`, `user_agent`, `is_active`

**Sumber Data**:
- Dibuat saat user login ke Web UI
- Dihapus saat logout

**Relasi**: ✅ **Memiliki Foreign Key** ke `web_users.id`

---

#### 3. **`store_001`** - User Fingerprint
**Fungsi**: Menyimpan data user yang terdaftar di sistem fingerprint

**Kolom**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER, UNIQUE) - ID user fingerprint (sama dengan finger_template_id)
- `username` (VARCHAR) - Nama user
- `finger_template_id` (INTEGER) - ID template fingerprint di sensor
- `created_at`, `updated_at`

**Sumber Data**:
1. **Enrollment via MQTT**: Saat user melakukan enrollment fingerprint di sensor, data dikirim via MQTT topic `WHAC/Store001/add_user_response` dan disimpan oleh `handle_enrollment_response()` di `web_ui/app.py`
2. **Manual via Web UI**: Admin dapat menambah user melalui form di Web UI
3. **Import dari sensor**: Data dapat di-import dari sensor fingerprint

**Relasi**: ❌ **TIDAK memiliki Foreign Key** ke tabel lain (tabel master untuk user fingerprint)

---

#### 4. **`log_data`** - Log Scan Fingerprint
**Fungsi**: Menyimpan semua record scan fingerprint

**Kolom**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - ID user yang melakukan scan
- `store_id` (VARCHAR) - ID store (biasanya 'Store001')
- `timestamp` (TIMESTAMP) - Waktu scan
- `finger_template_id` (INTEGER) - ID template fingerprint
- `device_id` (VARCHAR) - ID device sensor (AS608_001, AS608_002)
- `sensor_location` (VARCHAR) - Lokasi sensor ('masuk', 'keluar')
- `created_at` (TIMESTAMP)

**Sumber Data**:
1. **MQTT dari Sensor**: 
   - Sensor fingerprint (AS608) mengirim data scan via MQTT topic `WHAC/Store001/in`
   - Diterima oleh `on_mqtt_message()` di `web_ui/app.py`
   - Diproses oleh `process_incoming_scan()` → `log_scan_to_database()`
2. **File**: `local_machine/fingerprint_multi_client.py`, `fingerprint_simple_client.py`, dll mengirim data ke MQTT

**Relasi**: ❌ **TIDAK memiliki Foreign Key** ke `store_001.user_id` (hanya relasi logis)

---

#### 5. **`log_action`** - Log Aksi Akses
**Fungsi**: Menyimpan log semua aksi akses (granted/denied)

**Kolom**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - ID user
- `store_id` (VARCHAR) - ID store
- `username` (VARCHAR) - **Redundansi**: Nama user (juga ada di `store_001`)
- `timestamp` (TIMESTAMP) - Waktu aksi
- `action` (VARCHAR) - Jenis aksi (access_granted, access_denied, scan_detected, dll)
- `granted_denied` (VARCHAR) - Status: 'granted', 'denied', atau 'pending'
- `device_id` (VARCHAR) - ID device sensor
- `sensor_location` (VARCHAR) - Lokasi sensor
- `created_at` (TIMESTAMP)

**Sumber Data**:
1. **MQTT dari Sensor**: Saat scan fingerprint, data dikirim ke MQTT dan diproses oleh `process_incoming_scan()` → `log_scan_to_database()`
2. **Manual dari Web UI**: Admin dapat grant/deny access manual melalui `log_manual_action()`

**Relasi**: ❌ **TIDAK memiliki Foreign Key** ke `store_001.user_id` (hanya relasi logis)

**Masalah**: 
- ❌ Redundansi data `username` (seharusnya bisa di-join dari `store_001`)
- ❌ Tidak ada constraint untuk memastikan `user_id` valid

---

#### 6. **`attendance`** - Data Kehadiran
**Fungsi**: Menyimpan data kehadiran user (clock in/out)

**Kolom**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - ID user
- `username` (VARCHAR) - **Redundansi**: Nama user
- `attendance_date` (DATE) - Tanggal kehadiran
- `clock_in` (TIMESTAMP) - Waktu masuk pertama
- `clock_out` (TIMESTAMP) - Waktu keluar terakhir
- `first_granted` (TIMESTAMP) - Waktu akses pertama kali
- `last_granted` (TIMESTAMP) - Waktu akses terakhir kali
- `total_granted` (INTEGER) - Total akses dalam sehari
- `device_id_in`, `device_id_out` - Device ID untuk masuk/keluar
- `sensor_location_in`, `sensor_location_out` - Lokasi sensor
- `created_at`, `updated_at`
- `UNIQUE(user_id, attendance_date)` - Constraint untuk mencegah duplikasi

**Sumber Data**:
- **Background Process**: Diisi oleh proses background yang menganalisis `log_action` untuk membuat summary attendance per hari
- **Catatan**: Tidak ada kode yang terlihat mengisi tabel ini secara langsung di codebase saat ini

**Relasi**: ❌ **TIDAK memiliki Foreign Key** ke `store_001.user_id` (hanya relasi logis)

**Masalah**:
- ❌ Redundansi data `username`
- ❌ Tidak ada constraint untuk memastikan `user_id` valid
- ⚠️ **Tidak jelas siapa yang mengisi tabel ini** (tidak ada kode yang terlihat)

---

## 🔄 Alur Data (Data Flow)

### 1. **Enrollment User Fingerprint**
```
Sensor AS608 → MQTT (WHAC/Store001/add_user_response) 
→ web_ui/app.py::handle_enrollment_response() 
→ INSERT INTO store_001
```

### 2. **Scan Fingerprint**
```
Sensor AS608 → MQTT (WHAC/Store001/in) 
→ web_ui/app.py::on_mqtt_message() 
→ process_incoming_scan() 
→ log_scan_to_database() 
→ INSERT INTO log_data + log_action
```

### 3. **Manual Grant/Deny Access**
```
Web UI → web_ui/app.py::log_manual_action() 
→ INSERT INTO log_action
```

### 4. **User Web UI Management**
```
Web UI → web_ui/app.py (various endpoints) 
→ INSERT/UPDATE/DELETE web_users + user_sessions
```

---

## ❌ Masalah yang Ditemukan

### 1. **Tidak Ada Foreign Key Constraints**

**Masalah**: Tabel `log_data`, `log_action`, dan `attendance` tidak memiliki Foreign Key constraint ke `store_001.user_id`, padahal mereka memiliki relasi logis.

**Dampak**:
- ❌ Data `user_id` di `log_data` bisa merujuk ke user yang tidak ada di `store_001`
- ❌ Tidak ada referential integrity - data bisa tidak konsisten
- ❌ Tidak bisa menggunakan `ON DELETE CASCADE` untuk auto-cleanup

**Contoh Masalah**:
```sql
-- User dengan user_id = 999 tidak ada di store_001
-- Tapi bisa ada di log_data
SELECT * FROM log_data WHERE user_id = 999;  -- Bisa return data
SELECT * FROM store_001 WHERE user_id = 999;  -- Return NULL
```

**Solusi yang Disarankan**:
```sql
-- Tambahkan Foreign Key constraints
ALTER TABLE log_data 
ADD CONSTRAINT fk_log_data_user_id 
FOREIGN KEY (user_id) REFERENCES store_001(user_id) ON DELETE SET NULL;

ALTER TABLE log_action 
ADD CONSTRAINT fk_log_action_user_id 
FOREIGN KEY (user_id) REFERENCES store_001(user_id) ON DELETE SET NULL;

ALTER TABLE attendance 
ADD CONSTRAINT fk_attendance_user_id 
FOREIGN KEY (user_id) REFERENCES store_001(user_id) ON DELETE CASCADE;
```

---

### 2. **Redundansi Data Username**

**Masalah**: Kolom `username` disimpan di:
- `store_001.username` (sumber utama)
- `log_action.username` (redundansi)
- `attendance.username` (redundansi)

**Dampak**:
- ❌ Data bisa tidak konsisten jika username di `store_001` diubah
- ❌ Wasted storage space
- ❌ Harus update multiple tabel saat username berubah

**Solusi yang Disarankan**:
- Hapus kolom `username` dari `log_action` dan `attendance`
- Gunakan JOIN ke `store_001` saat perlu menampilkan username
- Atau buat VIEW yang sudah include username

---

### 3. **Tidak Ada Index untuk Foreign Key**

**Masalah**: Meskipun ada relasi logis, tidak ada index yang optimal untuk JOIN operations.

**Status Saat Ini**:
- ✅ Ada index `idx_log_data_user_id` pada `log_data(user_id)`
- ✅ Ada index `idx_log_action_user_id` pada `log_action(user_id)`
- ✅ Ada index `idx_attendance_user_id` pada `attendance(user_id)`

**Catatan**: Index sudah ada, tapi Foreign Key constraint tetap perlu ditambahkan.

---

### 4. **Tabel `attendance` Tidak Jelas Sumbernya**

**Masalah**: Tidak ada kode yang terlihat mengisi tabel `attendance` secara langsung.

**Kemungkinan**:
- ⚠️ Proses background yang belum diimplementasi
- ⚠️ Script terpisah yang tidak ada di codebase
- ⚠️ Manual insertion (tidak ideal)

**Solusi yang Disarankan**:
- Buat background job/cron job yang menganalisis `log_action` setiap hari
- Generate `attendance` records berdasarkan `log_action` dengan `granted_denied = 'granted'`
- Atau hapus tabel jika tidak digunakan

---

### 5. **Tidak Ada Validasi Data di Application Level**

**Masalah**: Saat insert data ke `log_data` dan `log_action`, tidak ada validasi apakah `user_id` ada di `store_001`.

**Contoh di Code** (`web_ui/app.py:481-499`):
```python
# log_scan_to_database() langsung insert tanpa validasi
cursor.execute("""
    INSERT INTO log_data (user_id, store_id, timestamp, finger_template_id, device_id, sensor_location)
    VALUES (%s, %s, %s, %s, %s, %s)
""", (fingerprint_id, store_id, timestamp, fingerprint_id, device_id, sensor_location))
```

**Dampak**:
- ❌ Bisa insert `user_id` yang tidak valid
- ❌ Data tidak konsisten

**Solusi**:
- Tambahkan validasi di application level
- Atau tambahkan Foreign Key constraint (akan otomatis reject invalid data)

---

## ✅ Rekomendasi Perbaikan

### 1. **Tambahkan Foreign Key Constraints**
```sql
-- Pastikan semua user_id valid
ALTER TABLE log_data 
ADD CONSTRAINT fk_log_data_user_id 
FOREIGN KEY (user_id) REFERENCES store_001(user_id) ON DELETE SET NULL;

ALTER TABLE log_action 
ADD CONSTRAINT fk_log_action_user_id 
FOREIGN KEY (user_id) REFERENCES store_001(user_id) ON DELETE SET NULL;

ALTER TABLE attendance 
ADD CONSTRAINT fk_attendance_user_id 
FOREIGN KEY (user_id) REFERENCES store_001(user_id) ON DELETE CASCADE;
```

### 2. **Hapus Redundansi Username**
```sql
-- Hapus kolom username dari log_action dan attendance
-- Gunakan JOIN saat query
ALTER TABLE log_action DROP COLUMN IF EXISTS username;
ALTER TABLE attendance DROP COLUMN IF EXISTS username;
```

### 3. **Buat Views untuk Query yang Sering Digunakan**
```sql
-- View sudah ada: fingerprint_logs, action_logs, attendance_summary
-- Pastikan views ini menggunakan JOIN ke store_001 untuk username
```

### 4. **Implementasi Background Job untuk Attendance**
- Buat script/cron job yang generate `attendance` dari `log_action`
- Atau hapus tabel `attendance` jika tidak digunakan

### 5. **Tambahkan Validasi di Application Level**
- Validasi `user_id` sebelum insert ke `log_data` dan `log_action`
- Atau biarkan Foreign Key constraint handle validasi

---

## 📊 Diagram Relasi Database (Saat Ini vs Ideal)

### Saat Ini (Tanpa Foreign Key):
```
web_users (1) ──< (N) user_sessions [✅ FK ada]
                    (user_id)

store_001 (1) ──< (N) log_data [❌ FK tidak ada]
                    (user_id)

store_001 (1) ──< (N) log_action [❌ FK tidak ada]
                    (user_id)

store_001 (1) ──< (N) attendance [❌ FK tidak ada]
                    (user_id)
```

### Ideal (Dengan Foreign Key):
```
web_users (1) ──< (N) user_sessions [✅ FK]
                    (user_id) [FK]

store_001 (1) ──< (N) log_data [✅ FK]
                    (user_id) [FK]

store_001 (1) ──< (N) log_action [✅ FK]
                    (user_id) [FK]

store_001 (1) ──< (N) attendance [✅ FK]
                    (user_id) [FK]
```

---

## 📝 Kesimpulan

Database `whac_master` memiliki struktur yang baik secara logis, tetapi **kurang dalam hal referential integrity**:

1. ✅ **Relasi logis sudah benar** - Tabel-tabel sudah dirancang dengan relasi yang tepat
2. ❌ **Foreign Key constraints tidak ada** - Data bisa tidak konsisten
3. ❌ **Redundansi data** - Username disimpan di multiple tabel
4. ⚠️ **Tabel attendance tidak jelas sumbernya** - Tidak ada kode yang mengisi

**Prioritas Perbaikan**:
1. **Tinggi**: Tambahkan Foreign Key constraints
2. **Sedang**: Hapus redundansi username
3. **Rendah**: Implementasi background job untuk attendance (atau hapus jika tidak digunakan)

---

## 🔧 Script SQL untuk Perbaikan

File SQL untuk memperbaiki masalah-masalah di atas dapat dibuat di:
- `web_ui/fix_database_foreign_keys.sql`
- `web_ui/remove_username_redundancy.sql`

Apakah Anda ingin saya buatkan script SQL untuk memperbaiki masalah-masalah ini?












