# Instalasi Fitur Full Name Linking

## 📋 Prerequisites

- PostgreSQL database `whac_master` sudah terinstall dan running
- Web UI sudah berjalan
- Akses ke database dengan user `postgres`

## 🔧 Step-by-Step Installation

### Step 1: Backup Database (Recommended)

Sebelum melakukan perubahan, backup database terlebih dahulu:

```bash
pg_dump -U postgres -d whac_master > backup_before_full_name_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Jalankan Migration Script

Jalankan migration script untuk menambahkan kolom baru:

```bash
cd web_ui
psql -U postgres -d whac_master -f migration_add_full_name.sql
```

**Output yang diharapkan:**
```
ALTER TABLE
ALTER TABLE
ALTER TABLE
UPDATE 0
DROP VIEW
CREATE VIEW
CREATE INDEX
CREATE INDEX
CREATE INDEX
                       result                        
----------------------------------------------------
 Migration completed successfully! full_name columns added.
(1 row)
```

### Step 3: Restart Web UI

Restart aplikasi web UI agar perubahan diterapkan:

```bash
# Jika menggunakan systemd
sudo systemctl restart whac-web-ui

# Atau jika menjalankan manual
# Ctrl+C untuk stop, lalu jalankan lagi:
python3 app.py
```

### Step 4: Verifikasi Instalasi

#### A. Cek Database Schema

```sql
-- Cek kolom full_name di user_sensor_1
\d user_sensor_1

-- Cek kolom full_name di user_sensor_2
\d user_sensor_2

-- Cek kolom baru di attendance
\d attendance

-- Cek view attendance_summary
\d+ attendance_summary
```

#### B. Test API Endpoints

```bash
# Test get full names
curl -X GET http://localhost:5000/api/full_names \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Expected response:
# {"full_names": []}
```

#### C. Test Modal UI

1. Login ke Web UI
2. Buka halaman Dashboard
3. Simulasi scan dari Sensor 1 (AS608_001)
4. Modal harus menampilkan form "Nama Lengkap"
5. Simulasi scan dari Sensor 2 (AS608_002)
6. Modal harus menampilkan dropdown + form "Nama Lengkap"

## 🎯 Quick Test Scenario

### Test 1: Daftar User Baru di Sensor 1

1. Scan fingerprint baru di Sensor 1
2. Modal muncul dengan form:
   - User ID: (auto-filled)
   - Nama: Masukkan "John"
   - Posisi: Masukkan "Staff"
   - **Nama Lengkap: Masukkan "John Doe"**
3. Klik "Daftar"
4. Verifikasi di database:

```sql
SELECT user_id, username, full_name FROM user_sensor_1 WHERE username = 'John';
```

Expected:
```
 user_id | username | full_name 
---------+----------+-----------
       5 | John     | John Doe
```

### Test 2: Daftar User yang Sama di Sensor 2

1. Scan fingerprint baru di Sensor 2
2. Modal muncul dengan dropdown yang menampilkan "John Doe (1 user)"
3. Pilih "John Doe" dari dropdown
4. Masukkan nama: "John"
5. Klik "Daftar"
6. Verifikasi di database:

```sql
SELECT user_id, username, full_name FROM user_sensor_2 WHERE username = 'John';
```

Expected:
```
 user_id | username | full_name 
---------+----------+-----------
      12 | John     | John Doe
```

### Test 3: Grant Access dan Cek Attendance

1. Scan user di Sensor 1 → Grant Access
2. Scan user di Sensor 2 → Grant Access
3. Cek attendance:

```sql
SELECT 
    full_name, 
    user_id_in, 
    user_id_out, 
    clock_in, 
    clock_out 
FROM attendance 
WHERE attendance_date = CURRENT_DATE;
```

Expected:
```
 full_name | user_id_in | user_id_out |       clock_in       |       clock_out      
-----------+------------+-------------+----------------------+----------------------
 John Doe  |          5 |          12 | 2025-01-02 08:00:00 | 2025-01-02 17:00:00
```

### Test 4: Cek Attendance Report di UI

1. Buka halaman "Attendance"
2. Tabel harus menampilkan:
   - **Full Name**: John Doe (bold)
   - **User ID In**: 5
   - **User ID Out**: 12
   - **Clock In**: 08:00
   - **Clock Out**: 17:00
   - **Hours Worked**: 9.00

## 🐛 Troubleshooting

### Error: "column full_name does not exist"

**Cause:** Migration belum dijalankan atau gagal

**Solution:**
```bash
# Cek apakah kolom sudah ada
psql -U postgres -d whac_master -c "\d user_sensor_1"

# Jika belum ada, jalankan migration lagi
psql -U postgres -d whac_master -f migration_add_full_name.sql
```

### Error: "view attendance_summary does not exist"

**Cause:** View gagal dibuat

**Solution:**
```sql
-- Drop dan recreate view
DROP VIEW IF EXISTS attendance_summary CASCADE;

-- Copy-paste CREATE VIEW dari migration_add_full_name.sql
```

### Modal tidak menampilkan form full_name

**Cause:** Cache browser atau JavaScript belum reload

**Solution:**
1. Hard refresh browser (Ctrl+F5 atau Cmd+Shift+R)
2. Clear browser cache
3. Restart web UI

### Dropdown tidak menampilkan nama lengkap

**Cause:** Belum ada user dengan full_name di database

**Solution:**
1. Daftar user baru di Sensor 1 dengan full_name
2. Atau update user existing:

```sql
UPDATE user_sensor_1 
SET full_name = 'John Doe' 
WHERE user_id = 5;
```

### Attendance tidak ter-link

**Cause:** Full name tidak sama persis (case-sensitive)

**Solution:**
```sql
-- Cek full_name di kedua sensor
SELECT user_id, username, full_name FROM user_sensor_1 WHERE user_id = 5;
SELECT user_id, username, full_name FROM user_sensor_2 WHERE user_id = 12;

-- Update jika berbeda
UPDATE user_sensor_2 
SET full_name = 'John Doe' 
WHERE user_id = 12;
```

## 🔄 Rollback (Jika Diperlukan)

Jika terjadi masalah dan ingin rollback:

```sql
-- Restore dari backup
psql -U postgres -d whac_master < backup_before_full_name_YYYYMMDD_HHMMSS.sql
```

Atau hapus kolom secara manual:

```sql
-- Hapus kolom dari user_sensor_1
ALTER TABLE user_sensor_1 DROP COLUMN IF EXISTS full_name;

-- Hapus kolom dari user_sensor_2
ALTER TABLE user_sensor_2 DROP COLUMN IF EXISTS full_name;

-- Hapus kolom dari attendance
ALTER TABLE attendance DROP COLUMN IF EXISTS full_name;
ALTER TABLE attendance DROP COLUMN IF EXISTS user_id_in;
ALTER TABLE attendance DROP COLUMN IF EXISTS user_id_out;

-- Recreate view lama
-- (Copy dari database_setup.sql versi lama)
```

## 📊 Monitoring

Setelah instalasi, monitor hal berikut:

### 1. Database Performance

```sql
-- Cek index usage
SELECT 
    schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename IN ('user_sensor_1', 'user_sensor_2', 'attendance');
```

### 2. API Response Time

```bash
# Test response time
time curl -X GET http://localhost:5000/api/full_names \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### 3. Log Errors

```bash
# Monitor web UI logs
tail -f /var/log/whac-web-ui/app.log

# Atau jika running di terminal
# Lihat output console
```

## ✅ Post-Installation Checklist

- [ ] Migration script berhasil dijalankan
- [ ] Database schema sudah terupdate (kolom full_name ada)
- [ ] View attendance_summary sudah terupdate
- [ ] Web UI sudah direstart
- [ ] API `/api/full_names` bisa diakses
- [ ] Modal di Sensor 1 menampilkan form full_name
- [ ] Modal di Sensor 2 menampilkan dropdown + form
- [ ] Attendance record tersimpan dengan full_name
- [ ] Attendance report menampilkan kolom baru
- [ ] Test scenario berhasil dijalankan

## 📞 Support

Jika mengalami masalah:

1. Cek log error di console/log file
2. Verifikasi database schema dengan `\d` command
3. Test API endpoint dengan curl
4. Cek dokumentasi di `FITUR_FULL_NAME_LINKING.md`

---

**Last Updated:** 2025-01-02  
**Version:** 1.0







