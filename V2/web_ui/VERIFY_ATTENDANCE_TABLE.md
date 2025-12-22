# Panduan Verifikasi dan Membuat Tabel Attendance

Jika Anda tidak menemukan tabel `attendance` di DBeaver, ikuti langkah-langkah berikut:

## 🔍 Langkah 1: Verifikasi Tabel Attendance

Jalankan query berikut di DBeaver untuk memeriksa apakah tabel sudah ada:

```sql
-- Cek apakah tabel attendance ada
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'attendance';
```

**Hasil yang diharapkan:**
- Jika tabel **ADA**: Akan muncul 1 baris dengan `table_name = 'attendance'` dan `table_type = 'BASE TABLE'`
- Jika tabel **TIDAK ADA**: Query tidak mengembalikan hasil (0 rows)

---

## 🛠️ Langkah 2: Buat Tabel Attendance

Jika tabel tidak ada, jalankan script `create_attendance_table.sql`:

### Cara 1: Menggunakan DBeaver

1. **Buka file `create_attendance_table.sql`** di DBeaver
   - File location: `web_ui/create_attendance_table.sql`

2. **Pastikan Anda terhubung ke database yang benar:**
   - Database: `whac_master`
   - Schema: `public`
   - User: `postgres`

3. **Jalankan script:**
   - Klik kanan pada file SQL → **Execute SQL Script**
   - Atau tekan `Ctrl+Alt+X` (Windows) / `Cmd+Alt+X` (Mac)
   - Atau copy-paste isi script ke SQL Editor dan tekan `Ctrl+Enter`

4. **Verifikasi hasil:**
   - Script akan membuat tabel `attendance` dan view `attendance_summary`
   - Jika berhasil, tidak ada error message

### Cara 2: Menggunakan psql Command Line

```bash
# Masuk ke psql
psql -U postgres -d whac_master

# Jalankan script
\i web_ui/create_attendance_table.sql

# Atau copy-paste isi script langsung
```

---

## ✅ Langkah 3: Verifikasi Setelah Pembuatan

Setelah menjalankan script, verifikasi dengan query berikut:

### 3.1. Cek Tabel Attendance

```sql
-- Cek struktur tabel attendance
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'attendance'
ORDER BY ordinal_position;
```

**Hasil yang diharapkan:** 14 kolom dengan struktur:
- `id` (integer, NOT NULL)
- `user_id` (integer, NOT NULL)
- `username` (character varying)
- `attendance_date` (date, NOT NULL)
- `clock_in` (timestamp without time zone)
- `clock_out` (timestamp without time zone)
- `first_granted` (timestamp without time zone, NOT NULL)
- `last_granted` (timestamp without time zone, NOT NULL)
- `total_granted` (integer, default 1)
- `device_id_in` (character varying)
- `device_id_out` (character varying)
- `sensor_location_in` (character varying)
- `sensor_location_out` (character varying)
- `created_at` (timestamp without time zone)
- `updated_at` (timestamp without time zone)

### 3.2. Cek View Attendance Summary

```sql
-- Cek apakah view attendance_summary ada
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'attendance_summary';
```

**Hasil yang diharapkan:** 1 baris dengan `table_type = 'VIEW'`

### 3.3. Test Query View

```sql
-- Test query view attendance_summary
SELECT * FROM attendance_summary LIMIT 5;
```

**Hasil yang diharapkan:** 
- Jika tabel kosong: 0 rows (tidak ada error)
- Jika ada data: Menampilkan 5 baris pertama

### 3.4. Cek Index

```sql
-- Cek index pada tabel attendance
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public' 
AND tablename = 'attendance';
```

**Hasil yang diharapkan:** 4 index:
- `attendance_pkey` (PRIMARY KEY)
- `idx_attendance_user_id`
- `idx_attendance_date`
- `idx_attendance_user_date`

---

## 🔄 Langkah 4: Refresh DBeaver

Setelah membuat tabel, **refresh koneksi database** di DBeaver:

1. **Klik kanan** pada database `whac_master` di Database Navigator
2. Pilih **Refresh** atau tekan `F5`
3. Tabel `attendance` seharusnya muncul di folder **Tables**
4. View `attendance_summary` seharusnya muncul di folder **Views**

---

## 🐛 Troubleshooting

### Masalah 1: "relation attendance already exists"

**Penyebab:** Tabel sudah ada tapi tidak terlihat di DBeaver

**Solusi:**
```sql
-- Cek apakah tabel benar-benar ada
SELECT * FROM attendance LIMIT 1;

-- Jika query berhasil, berarti tabel ada
-- Coba refresh DBeaver (F5)
```

### Masalah 2: "permission denied"

**Penyebab:** User tidak punya permission untuk create table

**Solusi:**
```sql
-- Berikan permission (jalankan sebagai superuser)
GRANT ALL PRIVILEGES ON TABLE attendance TO postgres;
GRANT ALL PRIVILEGES ON SEQUENCE attendance_id_seq TO postgres;
```

### Masalah 3: "schema public does not exist"

**Penyebab:** Schema public belum dibuat

**Solusi:**
```sql
-- Buat schema public (jalankan sebagai superuser)
CREATE SCHEMA IF NOT EXISTS public;
GRANT ALL ON SCHEMA public TO postgres;
```

### Masalah 4: Tabel ada tapi view tidak muncul

**Solusi:**
```sql
-- Hapus dan buat ulang view
DROP VIEW IF EXISTS attendance_summary CASCADE;

-- Lalu jalankan bagian CREATE VIEW dari script create_attendance_table.sql
```

---

## 📋 Checklist Verifikasi

Setelah mengikuti langkah-langkah di atas, pastikan:

- [ ] Tabel `attendance` muncul di DBeaver (folder Tables)
- [ ] View `attendance_summary` muncul di DBeaver (folder Views)
- [ ] Query `SELECT * FROM attendance LIMIT 1` berhasil (tidak error)
- [ ] Query `SELECT * FROM attendance_summary LIMIT 1` berhasil (tidak error)
- [ ] Struktur tabel sesuai dengan dokumentasi (14 kolom)

---

## 📞 Bantuan Tambahan

Jika masih mengalami masalah:

1. **Cek log error** di DBeaver (View → Error Log)
2. **Cek koneksi database** - pastikan terhubung ke `whac_master`
3. **Cek user permissions** - pastikan user `postgres` punya akses
4. **Cek database setup** - pastikan `database_setup.sql` sudah dijalankan sebelumnya

---

## 📝 Catatan Penting

- Tabel `attendance` diisi oleh **proses background** (bukan langsung dari API Web UI)
- API Web UI hanya **membaca** data dari view `attendance_summary`
- Jika tabel kosong, itu normal - data akan terisi saat ada aktivitas fingerprint scan



















