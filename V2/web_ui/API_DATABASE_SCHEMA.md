# Dokumentasi Koneksi API dengan Database Schema

Dokumen ini menjelaskan tabel-tabel database yang digunakan oleh setiap API endpoint di Web UI.

## 📊 Database: `whac_master`

Semua API terhubung ke database PostgreSQL dengan nama `whac_master`.

---

## 🗂️ Tabel-Tabel Database

### 1. **`web_users`** - Tabel User Web UI
**Fungsi**: Menyimpan data user untuk autentikasi dan akses ke Web UI

**Kolom Utama**:
- `id` (SERIAL PRIMARY KEY)
- `username` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR) - Password ter-hash dengan bcrypt
- `full_name` (VARCHAR)
- `email` (VARCHAR)
- `role` (VARCHAR) - 'admin' atau 'viewer'
- `is_active` (BOOLEAN)
- `created_at`, `last_login`, `login_attempts`, `locked_until`

**API yang Menggunakan**:
- ✅ `POST /login` - Verifikasi login
- ✅ `GET /api/admin/web_users` - Ambil semua user web UI
- ✅ `POST /api/admin/web_users` - Buat user baru
- ✅ `PUT /api/admin/web_users/<id>` - Update user
- ✅ `DELETE /api/admin/web_users/<id>` - Hapus user
- ✅ `POST /api/admin/web_users/<id>/reset_password` - Reset password
- ✅ `POST /change_password` - Ganti password user sendiri
- ✅ `get_current_user()` - Fungsi helper untuk mendapatkan user saat ini

---

### 2. **`user_sessions`** - Tabel Session User
**Fungsi**: Menyimpan session token untuk autentikasi user

**Kolom Utama**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - Foreign key ke `web_users.id`
- `session_token` (VARCHAR, UNIQUE)
- `created_at`, `expires_at`
- `ip_address`, `user_agent`
- `is_active` (BOOLEAN)

**API yang Menggunakan**:
- ✅ `POST /login` - Membuat session baru saat login
- ✅ `GET /logout` - Menonaktifkan session saat logout
- ✅ `validate_session()` - Fungsi helper untuk validasi session

---

### 3. **`store_001`** - Tabel User Fingerprint
**Fungsi**: Menyimpan data user yang terdaftar di sistem fingerprint

**Kolom Utama**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER, UNIQUE) - ID user fingerprint
- `username` (VARCHAR) - Nama user
- `finger_template_id` (INTEGER) - ID template fingerprint
- `created_at`, `updated_at`

**API yang Menggunakan**:
- ✅ `GET /api/users` - Ambil semua user fingerprint (dengan JOIN ke `log_data`)
- ✅ `GET /api/admin/fingerprint_users` - Ambil semua user fingerprint (admin)
- ✅ `POST /api/admin/fingerprint_users` - Buat user fingerprint baru
- ✅ `PUT /api/admin/fingerprint_users/<id>` - Update user fingerprint
- ✅ `DELETE /api/admin/fingerprint_users/<id>` - Hapus user fingerprint
- ✅ `POST /api/add_user` - Tambah user baru
- ✅ `DELETE /api/delete_user/<id>` - Hapus user
- ✅ `GET /api/next_user_id` - Ambil ID user berikutnya
- ✅ `POST /api/enroll_user` - Cek apakah user_id sudah ada
- ✅ `handle_enrollment_response()` - Insert user setelah enrollment berhasil
- ✅ `get_user_info_from_fingerprint()` - Ambil info user berdasarkan fingerprint_id
- ✅ `log_manual_action()` - Ambil username untuk logging

---

### 4. **`log_data`** - Tabel Log Data Fingerprint
**Fungsi**: Menyimpan semua record scan fingerprint

**Kolom Utama**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - ID user yang melakukan scan
- `store_id` (VARCHAR) - ID store (biasanya 'Store001')
- `timestamp` (TIMESTAMP) - Waktu scan
- `finger_template_id` (INTEGER) - ID template fingerprint
- `device_id` (VARCHAR) - ID device sensor (AS608_001, AS608_002)
- `sensor_location` (VARCHAR) - Lokasi sensor ('masuk', 'keluar')
- `created_at` (TIMESTAMP)

**API yang Menggunakan**:
- ✅ `process_incoming_scan()` - Insert log saat ada scan baru dari MQTT
- ✅ `log_scan_to_database()` - Fungsi untuk logging scan
- ✅ `GET /api/dashboard_stats` - Hitung total scans hari ini
- ✅ `GET /api/charts/daily_stats` - Statistik harian untuk chart
- ✅ `GET /api/logs` - Ambil log fingerprint (via view `fingerprint_logs`)

---

### 5. **`log_action`** - Tabel Log Aksi Akses
**Fungsi**: Menyimpan log semua aksi akses (granted/denied)

**Kolom Utama**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - ID user
- `store_id` (VARCHAR) - ID store
- `username` (VARCHAR) - Nama user
- `timestamp` (TIMESTAMP) - Waktu aksi
- `action` (VARCHAR) - Jenis aksi (access_granted, access_denied, scan_detected, dll)
- `granted_denied` (VARCHAR) - Status: 'granted' atau 'denied'
- `device_id` (VARCHAR) - ID device sensor
- `sensor_location` (VARCHAR) - Lokasi sensor
- `created_at` (TIMESTAMP)

**API yang Menggunakan**:
- ✅ `log_scan_to_database()` - Insert log action saat scan
- ✅ `log_manual_action()` - Insert log saat admin grant/deny access manual
- ✅ `GET /api/dashboard_stats` - Hitung successful/denied access hari ini
- ✅ `GET /api/charts/daily_stats` - Statistik harian untuk chart
- ✅ `GET /api/action_logs` - Ambil log aksi (via view `action_logs`)

---

### 6. **`attendance`** - Tabel Attendance (Kehadiran)
**Fungsi**: Menyimpan data kehadiran user (clock in/out)

**Kolom Utama**:
- `id` (SERIAL PRIMARY KEY)
- `user_id` (INTEGER) - ID user
- `username` (VARCHAR) - Nama user
- `attendance_date` (DATE) - Tanggal kehadiran
- `clock_in` (TIMESTAMP) - Waktu masuk pertama
- `clock_out` (TIMESTAMP) - Waktu keluar terakhir
- `first_granted` (TIMESTAMP) - Waktu akses pertama kali
- `last_granted` (TIMESTAMP) - Waktu akses terakhir kali
- `total_granted` (INTEGER) - Total akses dalam sehari
- `device_id_in`, `device_id_out` - Device ID untuk masuk/keluar
- `sensor_location_in`, `sensor_location_out` - Lokasi sensor
- `created_at`, `updated_at`

**API yang Menggunakan**:
- ✅ `GET /api/attendance` - Ambil data attendance dengan pagination
- ✅ `GET /api/attendance/report` - Generate laporan attendance (CSV)

**Catatan**: Tabel ini diisi oleh proses background (bukan langsung dari API Web UI)

---

## 👁️ Views (View Database)

### 1. **`fingerprint_logs`** - View Log Fingerprint
**Fungsi**: View yang menggabungkan `log_data` dengan `store_001` untuk menampilkan log dengan username

**Query Dasar**:
```sql
SELECT 
    ld.*, 
    s.username,
    location_display
FROM log_data ld
LEFT JOIN store_001 s ON ld.user_id = s.user_id
```

**API yang Menggunakan**:
- ✅ `GET /api/logs` - Menampilkan log fingerprint dengan username
- ✅ `GET /api/dashboard_stats` - Recent activity (10 log terakhir)

---

### 2. **`action_logs`** - View Log Aksi
**Fungsi**: View yang menampilkan `log_action` dengan status class dan location display

**Query Dasar**:
```sql
SELECT 
    la.*,
    status_class,
    location_display
FROM log_action la
```

**API yang Menggunakan**:
- ✅ `GET /api/action_logs` - Menampilkan log aksi dengan format yang lebih lengkap

---

### 3. **`attendance_summary`** - View Summary Attendance
**Fungsi**: View yang menampilkan summary attendance dengan perhitungan hours_worked

**Query Dasar**:
```sql
SELECT 
    a.*,
    hours_worked,
    location_in_display,
    location_out_display
FROM attendance a
```

**API yang Menggunakan**:
- ✅ `GET /api/attendance` - Menampilkan summary attendance
- ✅ `GET /api/attendance/report` - Generate laporan attendance

---

## 📋 Ringkasan Koneksi API per Endpoint

### 🔐 Authentication & User Management
| Endpoint | Method | Tabel Utama | Operasi |
|----------|--------|-------------|---------|
| `/login` | POST | `web_users`, `user_sessions` | SELECT, INSERT |
| `/logout` | GET | `user_sessions` | UPDATE |
| `/change_password` | POST | `web_users` | UPDATE |
| `/api/admin/web_users` | GET | `web_users` | SELECT |
| `/api/admin/web_users` | POST | `web_users` | INSERT |
| `/api/admin/web_users/<id>` | PUT | `web_users` | UPDATE |
| `/api/admin/web_users/<id>` | DELETE | `web_users`, `user_sessions` | DELETE |
| `/api/admin/web_users/<id>/reset_password` | POST | `web_users` | UPDATE |

### 👤 Fingerprint User Management
| Endpoint | Method | Tabel Utama | Operasi |
|----------|--------|-------------|---------|
| `/api/users` | GET | `store_001`, `log_data` | SELECT (JOIN) |
| `/api/admin/fingerprint_users` | GET | `store_001` | SELECT |
| `/api/admin/fingerprint_users` | POST | `store_001` | INSERT |
| `/api/admin/fingerprint_users/<id>` | PUT | `store_001` | UPDATE |
| `/api/admin/fingerprint_users/<id>` | DELETE | `store_001` | DELETE |
| `/api/add_user` | POST | `store_001` | INSERT |
| `/api/delete_user/<id>` | DELETE | `store_001` | DELETE |
| `/api/next_user_id` | GET | `store_001` | SELECT (MAX) |
| `/api/enroll_user` | POST | `store_001` | SELECT (check) |

### 📊 Dashboard & Statistics
| Endpoint | Method | Tabel Utama | Operasi |
|----------|--------|-------------|---------|
| `/api/dashboard_stats` | GET | `store_001`, `log_data`, `log_action`, `fingerprint_logs` | SELECT |
| `/api/charts/daily_stats` | GET | `log_data`, `log_action` | SELECT (GROUP BY) |

### 📝 Logs
| Endpoint | Method | Tabel/View | Operasi |
|----------|--------|------------|---------|
| `/api/logs` | GET | `fingerprint_logs` (view) | SELECT |
| `/api/action_logs` | GET | `action_logs` (view) | SELECT |

### ⏰ Attendance
| Endpoint | Method | Tabel/View | Operasi |
|----------|--------|------------|---------|
| `/api/attendance` | GET | `attendance_summary` (view) | SELECT |
| `/api/attendance/report` | GET | `attendance_summary` (view) | SELECT |

### 🔧 Background Processes (MQTT Handlers)
| Fungsi | Tabel Utama | Operasi |
|--------|-------------|---------|
| `process_incoming_scan()` | `log_data`, `log_action` | INSERT |
| `handle_enrollment_response()` | `store_001` | INSERT |
| `log_manual_action()` | `log_action`, `store_001` | INSERT, SELECT |

---

## 🔗 Relasi Antar Tabel

```
web_users (1) ──< (N) user_sessions
                    (user_id)

store_001 (1) ──< (N) log_data
                    (user_id)

store_001 (1) ──< (N) log_action
                    (user_id)

store_001 (1) ──< (N) attendance
                    (user_id)
```

---

## 📌 Catatan Penting

1. **Database Name**: Semua koneksi menggunakan database `whac_master`
2. **Schema**: Semua tabel berada di schema `public` (default PostgreSQL)
3. **Views**: `fingerprint_logs`, `action_logs`, dan `attendance_summary` adalah views, bukan tabel fisik
4. **Foreign Keys**: 
   - `user_sessions.user_id` → `web_users.id`
   - `log_data.user_id` → `store_001.user_id` (logical, tidak ada FK constraint)
   - `log_action.user_id` → `store_001.user_id` (logical, tidak ada FK constraint)
   - `attendance.user_id` → `store_001.user_id` (logical, tidak ada FK constraint)

5. **Indexes**: Semua tabel memiliki index pada kolom yang sering digunakan untuk query (timestamp, user_id, device_id, dll)

---

## 🎯 Kesimpulan

API Web UI ini terhubung ke **6 tabel utama** dan **3 views**:

**Tabel**:
1. `web_users` - User management Web UI
2. `user_sessions` - Session management
3. `store_001` - User fingerprint data
4. `log_data` - Log scan fingerprint
5. `log_action` - Log aksi akses
6. `attendance` - Data kehadiran

**Views**:
1. `fingerprint_logs` - View log dengan username
2. `action_logs` - View log aksi dengan format lengkap
3. `attendance_summary` - View summary attendance

Semua tabel berada di database PostgreSQL `whac_master` pada schema `public`.



















