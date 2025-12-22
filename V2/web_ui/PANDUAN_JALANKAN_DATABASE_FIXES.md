# 📋 Panduan Menjalankan Database Fixes

Panduan lengkap untuk menjalankan script SQL untuk memperbaiki database `whac_master`.

## 🎯 Script yang Akan Dijalankan

1. **`fix_database_foreign_keys.sql`**
   - Menambahkan Foreign Key constraints
   - Memastikan referential integrity antar tabel
   - Membersihkan data yang tidak valid

2. **`remove_username_redundancy.sql`**
   - Menghapus kolom `username` dari `log_action` dan `attendance`
   - Mengupdate views untuk menggunakan JOIN ke `store_001`

---

## 🚀 Cara Menjalankan (Otomatis - Recommended)

### **Windows PowerShell**

1. **Buka PowerShell** di folder `web_ui`
2. **Jalankan script:**
   ```powershell
   .\run_database_fixes.ps1
   ```

Script akan:
- ✅ Backup database otomatis
- ✅ Menjalankan kedua script SQL secara berurutan
- ✅ Memberikan konfirmasi sebelum setiap perubahan
- ✅ Menampilkan progress dan hasil

---

## 🔧 Cara Menjalankan (Manual)

### **Step 1: Backup Database**

**Windows PowerShell:**
```powershell
# Buat folder backup jika belum ada
New-Item -ItemType Directory -Path .\backups -Force

# Backup database
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker exec whac-postgres pg_dump -U postgres whac_master > ".\backups\backup_$timestamp.sql"
```

**Linux/Mac:**
```bash
# Buat folder backup jika belum ada
mkdir -p backups

# Backup database
timestamp=$(date +%Y%m%d_%H%M%S)
docker exec whac-postgres pg_dump -U postgres whac_master > "backups/backup_$timestamp.sql"
```

**Verifikasi backup:**
```bash
# Cek ukuran file backup (harus > 0 KB)
ls -lh backups/backup_*.sql
```

---

### **Step 2: Jalankan Foreign Keys Fix**

**Windows PowerShell:**
```powershell
Get-Content .\fix_database_foreign_keys.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

**Linux/Mac:**
```bash
cat fix_database_foreign_keys.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

**Atau menggunakan file:**
```bash
docker exec -i whac-postgres psql -U postgres -d whac_master < fix_database_foreign_keys.sql
```

**Verifikasi:**
```bash
# Cek Foreign Key constraints yang sudah dibuat
docker exec whac-postgres psql -U postgres -d whac_master -c "
SELECT 
    tc.table_name, 
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('log_data', 'log_action', 'attendance')
ORDER BY tc.table_name;
"
```

**Expected Output:**
```
 table_name  |      constraint_name       | column_name | foreign_table_name
-------------+----------------------------+-------------+-------------------
 log_action  | fk_log_action_user_id     | user_id     | store_001
 log_data    | fk_log_data_user_id       | user_id     | store_001
 attendance  | fk_attendance_user_id     | user_id     | store_001
```

---

### **Step 3: Jalankan Username Redundancy Fix**

**⚠️ PERINGATAN:** Script ini akan menghapus kolom `username` dari tabel `log_action` dan `attendance`. Pastikan:
- ✅ Backup sudah dibuat
- ✅ Application code sudah di-update untuk menggunakan JOIN ke `store_001`
- ✅ Views sudah di-update (script akan otomatis update views)

**Windows PowerShell:**
```powershell
Get-Content .\remove_username_redundancy.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

**Linux/Mac:**
```bash
cat remove_username_redundancy.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

**Atau menggunakan file:**
```bash
docker exec -i whac-postgres psql -U postgres -d whac_master < remove_username_redundancy.sql
```

**Verifikasi:**
```bash
# Cek apakah kolom username sudah dihapus
docker exec whac-postgres psql -U postgres -d whac_master -c "
SELECT 
    table_name,
    column_name
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name IN ('log_action', 'attendance', 'store_001')
    AND column_name = 'username'
ORDER BY table_name;
"
```

**Expected Output:**
```
 table_name | column_name
------------+-------------
 store_001  | username
```

(Kolom `username` hanya ada di `store_001`, tidak ada di `log_action` dan `attendance`)

---

## ✅ Verifikasi Setelah Fix

### **1. Cek Foreign Key Constraints**

```sql
SELECT 
    tc.table_name, 
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('log_data', 'log_action', 'attendance')
ORDER BY tc.table_name;
```

### **2. Cek Struktur Tabel**

```sql
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name IN ('log_action', 'attendance', 'store_001')
ORDER BY table_name, ordinal_position;
```

### **3. Test Views**

```sql
-- Test action_logs view
SELECT * FROM action_logs LIMIT 5;

-- Test attendance_summary view
SELECT * FROM attendance_summary LIMIT 5;
```

---

## 🔄 Restore dari Backup (Jika Ada Masalah)

Jika terjadi masalah dan perlu restore dari backup:

**Windows PowerShell:**
```powershell
# Cari file backup terbaru
$backupFile = Get-ChildItem .\backups\backup_*.sql | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Restore
Get-Content $backupFile | docker exec -i whac-postgres psql -U postgres -d whac_master
```

**Linux/Mac:**
```bash
# Cari file backup terbaru
backup_file=$(ls -t backups/backup_*.sql | head -1)

# Restore
cat "$backup_file" | docker exec -i whac-postgres psql -U postgres -d whac_master
```

---

## ⚠️ Troubleshooting

### **Error: "constraint already exists"**

**Penyebab:** Foreign Key constraint sudah ada sebelumnya.

**Solusi:**
- Script sudah menggunakan `DROP CONSTRAINT IF EXISTS`, jadi seharusnya tidak terjadi
- Jika masih error, jalankan manual:
  ```sql
  ALTER TABLE log_data DROP CONSTRAINT IF EXISTS fk_log_data_user_id;
  ALTER TABLE log_action DROP CONSTRAINT IF EXISTS fk_log_action_user_id;
  ALTER TABLE attendance DROP CONSTRAINT IF EXISTS fk_attendance_user_id;
  ```
- Lalu jalankan script lagi

---

### **Error: "column does not exist"**

**Penyebab:** Kolom `username` sudah tidak ada di tabel.

**Solusi:**
- Script sudah menggunakan `DROP COLUMN IF EXISTS`, jadi seharusnya tidak terjadi
- Jika masih error, berarti kolom sudah dihapus sebelumnya
- Skip script `remove_username_redundancy.sql` jika kolom sudah tidak ada

---

### **Error: "violates foreign key constraint"**

**Penyebab:** Ada data di `log_data`, `log_action`, atau `attendance` dengan `user_id` yang tidak ada di `store_001`.

**Solusi:**
- Script sudah membersihkan data yang tidak valid di awal
- Jika masih error, cek data manual:
  ```sql
  -- Cek data yang tidak valid
  SELECT DISTINCT user_id FROM log_data 
  WHERE user_id IS NOT NULL 
  AND user_id NOT IN (SELECT user_id FROM store_001);
  ```
- Hapus atau update data yang tidak valid sebelum menjalankan script

---

### **Error: "cannot drop view because other objects depend on it"**

**Penyebab:** Ada object lain yang depend pada view.

**Solusi:**
- Script sudah menggunakan `DROP VIEW IF EXISTS ... CASCADE`, jadi seharusnya tidak terjadi
- Jika masih error, hapus manual dengan CASCADE:
  ```sql
  DROP VIEW IF EXISTS action_logs CASCADE;
  DROP VIEW IF EXISTS attendance_summary CASCADE;
  ```

---

## 📝 Catatan Penting

1. **Backup Selalu Dulu!** Jangan skip backup, terutama untuk production database.

2. **Test di Development** - Test script di development environment dulu sebelum production.

3. **Update Application Code** - Setelah menjalankan `remove_username_redundancy.sql`, pastikan semua query di application code sudah di-update untuk menggunakan JOIN ke `store_001` atau menggunakan views yang sudah di-update.

4. **Restart Web UI** - Setelah menjalankan fixes, restart Web UI:
   ```bash
   cd web_ui
   docker-compose restart
   ```

5. **Monitor Logs** - Setelah restart, monitor logs untuk memastikan tidak ada error:
   ```bash
   docker-compose logs -f web-ui
   ```

---

## 🎯 Checklist

Sebelum menjalankan fixes:
- [ ] Backup database sudah dibuat
- [ ] Container `whac-postgres` sedang berjalan
- [ ] Test connection ke database berhasil
- [ ] Sudah membaca dokumentasi ini

Setelah menjalankan fixes:
- [ ] Foreign Key constraints sudah dibuat (verifikasi)
- [ ] Kolom `username` sudah dihapus dari `log_action` dan `attendance` (verifikasi)
- [ ] Views sudah di-update (test query)
- [ ] Web UI sudah di-restart
- [ ] Application berjalan normal (test fitur)

---

## 📞 Bantuan

Jika ada masalah atau pertanyaan:
1. Cek log error di output script
2. Cek dokumentasi di file SQL (ada komentar di dalamnya)
3. Restore dari backup jika perlu
4. Cek troubleshooting section di atas












