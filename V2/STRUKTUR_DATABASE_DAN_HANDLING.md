# 📊 Struktur Database dan Handling Sistem IoT-WHAC

## 🎯 Ringkasan

Dokumen ini menjelaskan struktur database yang digunakan dalam sistem IoT-WHAC (Fingerprint Access Control) dan bagaimana database tersebut di-handle oleh aplikasi.

---

## 🗄️ Arsitektur Database

Sistem ini menggunakan **2 jenis database**:

1. **PostgreSQL** (`whac_master`) - Database utama untuk Web UI dan data terpusat
2. **SQLite** (lokal) - Database lokal di setiap client untuk cache dan backup

---

## 📁 Database PostgreSQL: `whac_master`

Database PostgreSQL adalah database utama yang menyimpan semua data sistem, diakses oleh Web UI dan client melalui MQTT.

### 🔧 Konfigurasi Koneksi

```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'whac_master',
    'user': 'postgres',
    'password': 'Admin123',
    'port': 5432
}
```

**File Setup**: `web_ui/database_setup.sql`

---

## 📋 Tabel-Tabel Database PostgreSQL

### 1. **`web_users`** - User Web UI

**Fungsi**: Menyimpan data user untuk autentikasi dan akses ke Web UI

**Struktur**:
```sql
CREATE TABLE web_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    full_name VARCHAR(100),
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'admin',      -- 'admin' atau 'viewer'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);
```

**Handling**:
- **Insert**: Saat admin membuat user baru via Web UI
- **Update**: Saat user login (update `last_login`), ganti password, atau lock/unlock account
- **Delete**: Saat admin menghapus user (dengan cascade ke `user_sessions`)
- **Query**: Digunakan untuk autentikasi login, manajemen user

**File yang Handle**: `web_ui/app.py` (endpoints: `/login`, `/api/admin/web_users`, dll)

---

### 2. **`user_sessions`** - Session Management

**Fungsi**: Menyimpan session token untuk autentikasi user Web UI

**Struktur**:
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES web_users(id) ON DELETE CASCADE,  -- ✅ FK ada
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);
```

**Handling**:
- **Insert**: Saat user berhasil login (`POST /login`)
- **Update**: Saat logout (`is_active = FALSE`)
- **Delete**: Cascade saat `web_users` dihapus, atau saat session expired
- **Query**: Validasi session untuk protected routes

**File yang Handle**: `web_ui/app.py` (fungsi `validate_session()`, `get_current_user()`)

---

### 3. **`store_001`** - User Fingerprint (Master Data)

**Fungsi**: Menyimpan data user yang terdaftar di sistem fingerprint

**Struktur**:
```sql
CREATE TABLE store_001 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,           -- ID user fingerprint
    username VARCHAR(100) NOT NULL,            -- Nama user
    finger_template_id INTEGER NOT NULL,       -- ID template fingerprint di sensor
    device_id VARCHAR(50),                     -- AS608_001, AS608_002, dll
    sensor_location VARCHAR(20),                -- 'masuk', 'keluar', dll
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Handling**:
- **Insert**: 
  - Saat enrollment fingerprint via MQTT (`handle_enrollment_response()`)
  - Saat admin tambah user manual via Web UI
- **Update**: Saat update user info atau re-enrollment
- **Delete**: Saat admin hapus user fingerprint
- **Query**: 
  - Lookup user berdasarkan `user_id` atau `finger_template_id`
  - Join dengan `log_data`, `log_action` untuk menampilkan username

**File yang Handle**: 
- `web_ui/app.py` (endpoints: `/api/users`, `/api/admin/fingerprint_users`, dll)
- `local_machine/postgresql_integration.py` (fungsi `add_user()`, `get_user_info()`)

**Catatan Penting**:
- ✅ Tabel ini adalah **master data** untuk user fingerprint
- ⚠️ Tidak ada Foreign Key constraint ke tabel lain (tabel master)
- ⚠️ Support multi-sensor: satu user bisa punya multiple `finger_template_id` untuk device berbeda

---

### 4. **`user_sensor_1`** dan **`user_sensor_2`** - User per Sensor

**Fungsi**: Menyimpan data user untuk sensor spesifik (untuk sistem multi-sensor)

**Struktur**:
```sql
-- Sensor 1 (AS608_001 - Pintu Masuk)
CREATE TABLE user_sensor_1 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    finger_template_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sensor 2 (AS608_002 - Pintu Keluar)
CREATE TABLE user_sensor_2 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    finger_template_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Handling**:
- **Insert**: Saat enrollment user ke sensor spesifik
- **Update**: Saat update user info
- **Delete**: Saat hapus user dari sensor
- **Query**: Lookup user berdasarkan sensor dan `user_id`

**File yang Handle**: `web_ui/app.py` (fungsi `get_sensor_table()`, `get_username_from_sensor()`)

**Catatan**:
- ⚠️ Tabel ini **redundan** dengan `store_001` (duplikasi data)
- ⚠️ Digunakan untuk backward compatibility dengan sistem multi-sensor lama
- 💡 **Rekomendasi**: Migrasi ke `store_001` dengan `device_id` untuk menghindari duplikasi

---

### 5. **`log_data`** - Log Scan Fingerprint

**Fungsi**: Menyimpan semua record scan fingerprint

**Struktur**:
```sql
CREATE TABLE log_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,                           -- ID user (bisa NULL jika unknown)
    store_id VARCHAR(50) NOT NULL,             -- 'Store001'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finger_template_id INTEGER,                -- ID template yang di-scan
    device_id VARCHAR(50),                     -- AS608_001, AS608_002
    sensor_location VARCHAR(20),                -- 'masuk', 'keluar'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
- `idx_log_data_timestamp` - Untuk query berdasarkan waktu
- `idx_log_data_user_id` - Untuk query berdasarkan user
- `idx_log_data_device_id` - Untuk query berdasarkan device
- `idx_log_data_sensor_location` - Untuk query berdasarkan lokasi

**Handling**:
- **Insert**: 
  - Saat sensor mengirim scan via MQTT (`process_incoming_scan()` → `log_scan_to_database()`)
  - Setiap scan fingerprint otomatis di-log
- **Query**: 
  - Dashboard stats (total scans hari ini)
  - Chart statistics (daily stats)
  - Log viewer (via view `fingerprint_logs`)

**File yang Handle**: 
- `web_ui/app.py` (fungsi `log_scan_to_database()`, `process_incoming_scan()`)
- `local_machine/postgresql_integration.py` (fungsi `log_fingerprint_scan()`)

**Catatan**:
- ⚠️ **Tidak ada Foreign Key** ke `store_001.user_id` (hanya relasi logis)
- ⚠️ `user_id` bisa NULL jika fingerprint tidak terdaftar
- ✅ Data ini adalah **audit trail** lengkap untuk semua scan

---

### 6. **`log_action`** - Log Aksi Akses

**Fungsi**: Menyimpan log semua aksi akses (granted/denied)

**Struktur**:
```sql
CREATE TABLE log_action (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,                           -- ID user
    store_id VARCHAR(50) NOT NULL,
    username VARCHAR(100),                     -- ⚠️ Redundansi (juga ada di store_001)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50) NOT NULL,               -- 'access_granted', 'access_denied', 'scan_detected'
    granted_denied VARCHAR(20) NOT NULL,       -- 'granted', 'denied', 'pending'
    device_id VARCHAR(50),                     -- AS608_001, AS608_002
    sensor_location VARCHAR(20),                -- 'masuk', 'keluar'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
- `idx_log_action_timestamp` - Untuk query berdasarkan waktu
- `idx_log_action_user_id` - Untuk query berdasarkan user
- `idx_log_action_device_id` - Untuk query berdasarkan device
- `idx_log_action_sensor_location` - Untuk query berdasarkan lokasi

**Handling**:
- **Insert**: 
  - Saat scan fingerprint (otomatis via `log_scan_to_database()`)
  - Saat admin grant/deny access manual (`log_manual_action()`)
- **Query**: 
  - Dashboard stats (successful/denied access hari ini)
  - Chart statistics
  - Action logs viewer (via view `action_logs`)

**File yang Handle**: 
- `web_ui/app.py` (fungsi `log_scan_to_database()`, `log_manual_action()`)
- `local_machine/postgresql_integration.py` (fungsi `log_action()`)

**Catatan**:
- ⚠️ **Tidak ada Foreign Key** ke `store_001.user_id`
- ⚠️ **Redundansi**: Kolom `username` seharusnya bisa di-join dari `store_001`
- ✅ Data ini untuk tracking **hasil akses** (granted/denied)

---

### 7. **`attendance`** - Data Kehadiran

**Fungsi**: Menyimpan data kehadiran user (clock in/out)

**Struktur**:
```sql
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username VARCHAR(100),                     -- ⚠️ Redundansi
    attendance_date DATE NOT NULL,
    clock_in TIMESTAMP,                        -- Waktu masuk pertama
    clock_out TIMESTAMP,                       -- Waktu keluar terakhir
    first_granted TIMESTAMP NOT NULL,          -- Waktu akses pertama
    last_granted TIMESTAMP NOT NULL,           -- Waktu akses terakhir
    total_granted INTEGER DEFAULT 1,          -- Total akses dalam sehari
    device_id_in VARCHAR(50),                 -- Device untuk masuk
    device_id_out VARCHAR(50),                -- Device untuk keluar
    sensor_location_in VARCHAR(20),
    sensor_location_out VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, attendance_date)         -- ✅ Constraint: satu record per user per hari
);
```

**Indexes**:
- `idx_attendance_user_id` - Untuk query berdasarkan user
- `idx_attendance_date` - Untuk query berdasarkan tanggal
- `idx_attendance_user_date` - Composite index untuk query user + date

**Handling**:
- **Insert/Update**: 
  - ⚠️ **Tidak jelas** - Tidak ada kode yang terlihat mengisi tabel ini secara langsung
  - Kemungkinan: Background process/cron job yang belum diimplementasi
- **Query**: 
  - Attendance report (`GET /api/attendance`)
  - Export CSV report (`GET /api/attendance/report`)

**File yang Handle**: 
- `web_ui/app.py` (endpoints: `/api/attendance`, `/api/attendance/report`)

**Catatan**:
- ⚠️ **Tidak ada Foreign Key** ke `store_001.user_id`
- ⚠️ **Redundansi**: Kolom `username`
- ⚠️ **Tidak jelas sumber data** - Perlu implementasi background job untuk generate attendance dari `log_action`

---

## 👁️ Views (Database Views)

Views adalah query yang sudah di-predefine untuk memudahkan akses data.

### 1. **`fingerprint_logs`** - View Log Fingerprint

**Fungsi**: Menggabungkan `log_data` dengan `user_sensor_1` dan `user_sensor_2` untuk menampilkan log dengan username

**Query**:
```sql
CREATE VIEW fingerprint_logs AS
SELECT 
    ld.id,
    ld.user_id,
    ld.store_id,
    ld.timestamp,
    ld.finger_template_id,
    ld.device_id,
    ld.sensor_location,
    COALESCE(s1.username, s2.username) as username,
    CASE 
        WHEN ld.user_id IS NULL THEN 'Unknown User'
        ELSE COALESCE(s1.username, s2.username)
    END as display_name,
    CASE
        WHEN ld.device_id = 'AS608_001' THEN 'Pintu Masuk'
        WHEN ld.device_id = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(ld.sensor_location, 'Unknown')
    END as location_display
FROM log_data ld
LEFT JOIN user_sensor_1 s1 ON ld.user_id = s1.user_id AND ld.device_id = 'AS608_001'
LEFT JOIN user_sensor_2 s2 ON ld.user_id = s2.user_id AND ld.device_id = 'AS608_002'
ORDER BY ld.timestamp DESC;
```

**Penggunaan**: 
- `GET /api/logs` - Menampilkan log fingerprint dengan username
- Dashboard recent activity

---

### 2. **`action_logs`** - View Log Aksi

**Fungsi**: Menampilkan `log_action` dengan status class dan location display

**Query**:
```sql
CREATE VIEW action_logs AS
SELECT 
    la.id,
    la.user_id,
    la.store_id,
    la.username,
    la.timestamp,
    la.action,
    la.granted_denied,
    la.device_id,
    la.sensor_location,
    CASE 
        WHEN la.granted_denied = 'granted' THEN 'success'
        WHEN la.granted_denied = 'denied' THEN 'danger'
        ELSE 'warning'
    END as status_class,
    CASE
        WHEN la.device_id = 'AS608_001' THEN 'Pintu Masuk'
        WHEN la.device_id = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(la.sensor_location, 'Unknown')
    END as location_display
FROM log_action la
ORDER BY la.timestamp DESC;
```

**Penggunaan**: 
- `GET /api/action_logs` - Menampilkan log aksi dengan format lengkap

---

### 3. **`attendance_summary`** - View Summary Attendance

**Fungsi**: Menampilkan summary attendance dengan perhitungan hours_worked

**Query**:
```sql
CREATE VIEW attendance_summary AS
SELECT 
    a.id,
    a.user_id,
    a.username,
    a.attendance_date,
    a.clock_in,
    a.clock_out,
    a.first_granted as first_access,
    a.last_granted as last_access,
    a.total_granted,
    a.device_id_in,
    a.device_id_out,
    a.sensor_location_in,
    a.sensor_location_out,
    CASE
        WHEN a.clock_in IS NOT NULL AND a.clock_out IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (a.clock_out - a.clock_in)) / 3600
        ELSE NULL
    END as hours_worked,
    CASE
        WHEN a.device_id_in = 'AS608_001' THEN 'Pintu Masuk'
        WHEN a.device_id_in = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(a.sensor_location_in, 'Unknown')
    END as location_in_display,
    CASE
        WHEN a.device_id_out = 'AS608_001' THEN 'Pintu Masuk'
        WHEN a.device_id_out = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(a.sensor_location_out, 'Unknown')
    END as location_out_display
FROM attendance a
ORDER BY a.attendance_date DESC, a.user_id;
```

**Penggunaan**: 
- `GET /api/attendance` - Menampilkan summary attendance
- `GET /api/attendance/report` - Generate laporan attendance

---

## 💾 Database SQLite (Lokal)

Selain PostgreSQL, sistem juga menggunakan **SQLite** untuk database lokal di setiap client.

### Database Files

1. **`fingerprints_simple.db`** - Untuk `fingerprint_simple_client.py`
2. **`fingerprints_multi.db`** - Untuk `fingerprint_multi_client.py`
3. **`fingerprints.db`** - Untuk `fingerprint_manager.py` (backup/restore)
4. **`fingerprint_log.db`** - Untuk `fingerprint_hybrid_client.py` (verification logs)

### Struktur SQLite (Contoh: `fingerprints_multi.db`)

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    fingerprint_id INTEGER NOT NULL,
    device_id TEXT DEFAULT 'AS608_001',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Fungsi**:
- **Cache lokal** - Menyimpan data user untuk akses cepat tanpa query ke PostgreSQL
- **Backup** - Backup template fingerprint dari sensor
- **Offline support** - Bisa beroperasi tanpa koneksi ke PostgreSQL

**Handling**:
- **Insert**: Saat enrollment user atau backup dari sensor
- **Query**: Lookup user lokal sebelum query ke PostgreSQL
- **Timeout**: 10 detik untuk handle concurrent access

**File yang Handle**: 
- `local_machine/fingerprint_multi_client.py`
- `local_machine/fingerprint_simple_client.py`
- `local_machine/fingerprint_manager.py`

---

## 🔄 Alur Data (Data Flow)

### 1. **Enrollment User Fingerprint**

```
Sensor AS608 
  → MQTT Topic: WHAC/Store001/add_user_response
  → web_ui/app.py::handle_enrollment_response()
  → INSERT INTO store_001 (user_id, username, finger_template_id, device_id)
  → INSERT INTO user_sensor_1 atau user_sensor_2 (jika multi-sensor)
  → INSERT INTO SQLite lokal (cache)
```

### 2. **Scan Fingerprint**

```
Sensor AS608 
  → MQTT Topic: WHAC/Store001/in
  → web_ui/app.py::on_mqtt_message()
  → process_incoming_scan()
  → log_scan_to_database()
  → INSERT INTO log_data (user_id, store_id, timestamp, finger_template_id, device_id)
  → INSERT INTO log_action (user_id, action, granted_denied, device_id)
  → SocketIO emit ke Web UI (real-time update)
```

### 3. **Manual Grant/Deny Access**

```
Web UI Admin
  → web_ui/app.py::log_manual_action()
  → INSERT INTO log_action (user_id, action, granted_denied)
  → MQTT publish ke sensor (jika perlu trigger relay)
```

### 4. **User Web UI Management**

```
Web UI Admin
  → web_ui/app.py (various endpoints)
  → INSERT/UPDATE/DELETE web_users
  → INSERT/UPDATE/DELETE user_sessions (untuk login/logout)
```

---

## 🔗 Relasi Antar Tabel

### Relasi yang Ada (Dengan Foreign Key)

```
web_users (1) ──< (N) user_sessions
                    (user_id) [✅ FK dengan ON DELETE CASCADE]
```

### Relasi Logis (Tanpa Foreign Key)

```
store_001 (1) ──< (N) log_data
                    (user_id) [❌ FK tidak ada]

store_001 (1) ──< (N) log_action
                    (user_id) [❌ FK tidak ada]

store_001 (1) ──< (N) attendance
                    (user_id) [❌ FK tidak ada]
```

**Masalah**:
- ❌ Data `user_id` di `log_data`, `log_action`, dan `attendance` bisa merujuk ke user yang tidak ada di `store_001`
- ❌ Tidak ada referential integrity - data bisa tidak konsisten
- ❌ Tidak bisa menggunakan `ON DELETE CASCADE` untuk auto-cleanup

---

## 📝 Handling Database di Code

### 1. **Koneksi Database**

**PostgreSQL**:
```python
# web_ui/app.py
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None
```

**SQLite**:
```python
# local_machine/fingerprint_multi_client.py
conn = sqlite3.connect(self.db_file, timeout=10.0)
```

### 2. **Insert Data**

**Contoh: Log Scan Fingerprint**
```python
# web_ui/app.py::log_scan_to_database()
def log_scan_to_database(fingerprint_id, store_id, timestamp, device_id, sensor_location):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert ke log_data
    cursor.execute("""
        INSERT INTO log_data (user_id, store_id, timestamp, finger_template_id, device_id, sensor_location)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (fingerprint_id, store_id, timestamp, fingerprint_id, device_id, sensor_location))
    
    # Insert ke log_action
    cursor.execute("""
        INSERT INTO log_action (user_id, store_id, username, timestamp, action, granted_denied, device_id, sensor_location)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, store_id, username, timestamp, action, granted_denied, device_id, sensor_location))
    
    conn.commit()
    cursor.close()
    conn.close()
```

### 3. **Query Data**

**Contoh: Get Dashboard Stats**
```python
# web_ui/app.py::get_dashboard_stats()
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM store_001")
    total_users = cursor.fetchone()[0]
    
    # Total scans today
    cursor.execute("""
        SELECT COUNT(*) FROM log_data 
        WHERE DATE(timestamp) = CURRENT_DATE
    """)
    total_scans = cursor.fetchone()[0]
    
    # Successful access today
    cursor.execute("""
        SELECT COUNT(*) FROM log_action 
        WHERE granted_denied = 'granted' 
        AND DATE(timestamp) = CURRENT_DATE
    """)
    successful_access = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return {
        'total_users': total_users,
        'total_scans': total_scans,
        'successful_access': successful_access
    }
```

### 4. **Error Handling**

```python
try:
    conn = get_db_connection()
    if conn is None:
        logger.error("Database connection failed")
        return None
    
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    result = cursor.fetchall()
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return result
except psycopg2.Error as e:
    logger.error(f"Database error: {e}")
    if conn:
        conn.rollback()
    return None
```

---

## ⚠️ Masalah yang Ditemukan

### 1. **Tidak Ada Foreign Key Constraints**

**Masalah**: Tabel `log_data`, `log_action`, dan `attendance` tidak memiliki Foreign Key constraint ke `store_001.user_id`.

**Dampak**:
- ❌ Data `user_id` bisa merujuk ke user yang tidak ada
- ❌ Tidak ada referential integrity
- ❌ Tidak bisa auto-cleanup saat user dihapus

**Solusi**: Tambahkan Foreign Key constraints (file: `web_ui/fix_database_foreign_keys.sql`)

---

### 2. **Redundansi Data Username**

**Masalah**: Kolom `username` disimpan di:
- `store_001.username` (sumber utama) ✅
- `log_action.username` (redundansi) ❌
- `attendance.username` (redundansi) ❌

**Dampak**:
- ❌ Data bisa tidak konsisten jika username diubah
- ❌ Wasted storage space
- ❌ Harus update multiple tabel saat username berubah

**Solusi**: Hapus kolom `username` dari `log_action` dan `attendance`, gunakan JOIN (file: `web_ui/remove_username_redundancy.sql`)

---

### 3. **Tabel `attendance` Tidak Jelas Sumbernya**

**Masalah**: Tidak ada kode yang terlihat mengisi tabel `attendance` secara langsung.

**Kemungkinan**:
- ⚠️ Background process yang belum diimplementasi
- ⚠️ Script terpisah yang tidak ada di codebase

**Solusi**: Implementasi background job/cron job yang generate `attendance` dari `log_action`

---

### 4. **Duplikasi Tabel: `user_sensor_1/2` vs `store_001`**

**Masalah**: Tabel `user_sensor_1` dan `user_sensor_2` redundan dengan `store_001`.

**Dampak**:
- ❌ Data duplikat
- ❌ Harus maintain multiple tabel

**Solusi**: Migrasi ke `store_001` dengan `device_id` untuk menghindari duplikasi

---

## ✅ Best Practices yang Sudah Diterapkan

1. ✅ **Indexes** - Semua tabel memiliki index pada kolom yang sering digunakan
2. ✅ **Views** - Views untuk query yang sering digunakan (fingerprint_logs, action_logs, attendance_summary)
3. ✅ **Connection Pooling** - Setiap query membuka dan menutup koneksi dengan benar
4. ✅ **Error Handling** - Try-catch untuk semua database operations
5. ✅ **Logging** - Semua database operations di-log
6. ✅ **Timeout** - SQLite menggunakan timeout untuk handle concurrent access

---

## 📊 Ringkasan Struktur Database

### PostgreSQL (`whac_master`)

**Tabel Utama** (7 tabel):
1. `web_users` - User Web UI
2. `user_sessions` - Session management
3. `store_001` - User fingerprint (master data)
4. `user_sensor_1` - User untuk sensor 1 (redundan)
5. `user_sensor_2` - User untuk sensor 2 (redundan)
6. `log_data` - Log scan fingerprint
7. `log_action` - Log aksi akses
8. `attendance` - Data kehadiran

**Views** (3 views):
1. `fingerprint_logs` - View log dengan username
2. `action_logs` - View log aksi dengan format lengkap
3. `attendance_summary` - View summary attendance

### SQLite (Lokal)

**Database Files**:
1. `fingerprints_simple.db` - Cache untuk simple client
2. `fingerprints_multi.db` - Cache untuk multi client
3. `fingerprints.db` - Backup/restore manager
4. `fingerprint_log.db` - Verification logs

---

## 🎯 Kesimpulan

Sistem database IoT-WHAC menggunakan:

1. **PostgreSQL** sebagai database utama untuk:
   - Web UI authentication (`web_users`, `user_sessions`)
   - User fingerprint management (`store_001`, `user_sensor_1/2`)
   - Logging dan audit trail (`log_data`, `log_action`)
   - Attendance tracking (`attendance`)

2. **SQLite** sebagai database lokal untuk:
   - Cache user data untuk akses cepat
   - Backup template fingerprint
   - Offline support

**Handling**:
- ✅ Koneksi database di-handle dengan proper error handling
- ✅ Insert/Update/Delete operations menggunakan transactions
- ✅ Query menggunakan indexes untuk performa optimal
- ✅ Views untuk query yang sering digunakan

**Masalah yang Perlu Diperbaiki**:
- ❌ Tambahkan Foreign Key constraints
- ❌ Hapus redundansi username
- ❌ Implementasi background job untuk attendance
- ❌ Migrasi dari `user_sensor_1/2` ke `store_001` dengan `device_id`

---

## 📚 File-File Terkait

- **Setup Database**: `web_ui/database_setup.sql`
- **Migration Scripts**: 
  - `web_ui/migrate_add_device_id.sql`
  - `web_ui/fix_database_foreign_keys.sql`
  - `web_ui/remove_username_redundancy.sql`
- **Application Code**:
  - `web_ui/app.py` - Web UI dan database handling
  - `local_machine/postgresql_integration.py` - PostgreSQL integration
  - `local_machine/fingerprint_multi_client.py` - SQLite handling
- **Documentation**:
  - `web_ui/API_DATABASE_SCHEMA.md` - API dan database mapping
  - `web_ui/ANALISIS_DATABASE_WHAC_MASTER.md` - Analisis database

---

*Dokumen ini dibuat untuk menjelaskan struktur database dan handling yang existing di sistem IoT-WHAC.*

