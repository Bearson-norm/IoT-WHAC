# 📋 Panduan Auto-Cleanup Logs dan Device Identifier

Panduan lengkap untuk setup auto-cleanup logs lebih dari 3 bulan dan update views dengan device identifier.

---

## 🎯 Fitur yang Ditambahkan

### 1. **Auto-Cleanup Logs (Lebih dari 3 Bulan)**
- Function untuk menghapus data `log_data`, `log_action`, dan `attendance` lebih dari 3 bulan
- Support custom retention period
- Preview function untuk dry run sebelum cleanup

### 2. **Device In/Out Identifier di Views**
- Update `fingerprint_logs` view dengan identifier device masuk/keluar
- Update `action_logs` view dengan identifier device masuk/keluar
- Kolom baru: `is_device_in`, `is_device_out`, `device_direction`, `device_direction_display`

---

## 🚀 Cara Setup

### **Step 1: Backup Database**

```powershell
# Windows PowerShell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker exec whac-postgres pg_dump -U postgres whac_master > "backups\backup_before_cleanup_$timestamp.sql"
```

```bash
# Linux/Mac
timestamp=$(date +%Y%m%d_%H%M%S)
docker exec whac-postgres pg_dump -U postgres whac_master > "backups/backup_before_cleanup_$timestamp.sql"
```

---

### **Step 2: Jalankan Script Auto-Cleanup**

```powershell
# Windows PowerShell
Get-Content auto_cleanup_logs.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

```bash
# Linux/Mac
cat auto_cleanup_logs.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

**Fungsi yang dibuat:**
- `cleanup_old_log_data()` - Cleanup default (3 bulan)
- `cleanup_old_logs_custom(months)` - Cleanup dengan custom retention period
- `preview_old_logs(months)` - Preview data yang akan dihapus

---

### **Step 3: Update Views dengan Device Identifier**

```powershell
# Windows PowerShell
Get-Content update_views_device_identifier.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

```bash
# Linux/Mac
cat update_views_device_identifier.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

**Views yang di-update:**
- `fingerprint_logs` - Tambah kolom device identifier
- `action_logs` - Tambah kolom device identifier

---

### **Step 4: Setup Auto-Cleanup Schedule**

#### **Windows (PowerShell):**

```powershell
# Jalankan script setup
.\setup_auto_cleanup_cron.ps1
```

Script akan membuat Windows Scheduled Task yang menjalankan cleanup setiap hari jam 2 pagi.

#### **Linux/Mac (Bash):**

```bash
# Jalankan script setup
chmod +x setup_auto_cleanup_cron.sh
./setup_auto_cleanup_cron.sh
```

Script akan membuat cron job yang menjalankan cleanup setiap hari jam 2 pagi.

---

## 📊 Kolom Baru di Views

### **fingerprint_logs dan action_logs**

| Kolom | Tipe | Deskripsi |
|-------|------|-----------|
| `is_device_in` | BOOLEAN | `TRUE` jika device masuk (AS608_001 atau sensor_location='masuk') |
| `is_device_out` | BOOLEAN | `TRUE` jika device keluar (AS608_002 atau sensor_location='keluar') |
| `device_direction` | VARCHAR | 'IN', 'OUT', atau 'UNKNOWN' |
| `device_direction_display` | VARCHAR | 'Masuk', 'Keluar', atau lokasi lain |

---

## 🔧 Cara Menggunakan

### **1. Preview Data yang Akan Dihapus (Dry Run)**

```sql
-- Preview data lebih dari 3 bulan
SELECT * FROM preview_old_logs(3);

-- Preview data lebih dari 6 bulan
SELECT * FROM preview_old_logs(6);
```

**Output:**
```
 table_name  | record_count | oldest_timestamp | newest_timestamp
-------------+--------------+------------------+------------------
 log_data    | 1250        | 2024-08-01       | 2024-11-01
 log_action  | 1180        | 2024-08-01       | 2024-11-01
 attendance  | 45          | 2024-08-01       | 2024-11-01
```

---

### **2. Manual Cleanup**

```sql
-- Cleanup default (3 bulan)
SELECT * FROM cleanup_old_log_data();

-- Cleanup dengan custom retention (6 bulan)
SELECT * FROM cleanup_old_logs_custom(6);
```

**Output:**
```
 deleted_log_data_count | deleted_log_action_count | deleted_attendance_count
------------------------+--------------------------+-------------------------
                   1250 |                     1180 |                       45
```

---

### **3. Query dengan Device Identifier**

```sql
-- Filter hanya device masuk
SELECT * FROM fingerprint_logs 
WHERE is_device_in = TRUE 
ORDER BY timestamp DESC 
LIMIT 10;

-- Filter hanya device keluar
SELECT * FROM fingerprint_logs 
WHERE is_device_out = TRUE 
ORDER BY timestamp DESC 
LIMIT 10;

-- Count per direction
SELECT 
    device_direction,
    device_direction_display,
    COUNT(*) as total
FROM fingerprint_logs
GROUP BY device_direction, device_direction_display;

-- Summary per hari per direction
SELECT 
    DATE(timestamp) as date,
    device_direction_display,
    COUNT(*) as total_scans
FROM fingerprint_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp), device_direction_display
ORDER BY date DESC, device_direction_display;
```

---

## ⚙️ Konfigurasi Auto-Cleanup

### **Windows Scheduled Task**

**Cek task:**
```powershell
Get-ScheduledTask -TaskName "WHAC_AutoCleanup_Logs"
```

**Jalankan manual:**
```powershell
Start-ScheduledTask -TaskName "WHAC_AutoCleanup_Logs"
```

**Hapus task:**
```powershell
Unregister-ScheduledTask -TaskName "WHAC_AutoCleanup_Logs" -Confirm:$false
```

---

### **Linux Cron Job**

**Cek cron job:**
```bash
crontab -l | grep cleanup
```

**Edit cron job:**
```bash
crontab -e
```

**Hapus cron job:**
```bash
crontab -l | grep -v cleanup | crontab -
```

---

## 📝 Log Cleanup

### **Windows:**
Log disimpan di: `C:\logs\whac_cleanup.log`

### **Linux/Mac:**
Log disimpan di: `/var/log/whac_cleanup.log`

**Cek log:**
```bash
# Windows PowerShell
Get-Content C:\logs\whac_cleanup.log -Tail 20

# Linux/Mac
tail -20 /var/log/whac_cleanup.log
```

---

## ⚠️ Catatan Penting

1. **Backup Selalu Dulu!** Jangan skip backup sebelum cleanup
2. **Test dengan Preview** - Selalu preview data yang akan dihapus sebelum cleanup
3. **Retention Period** - Default 3 bulan, bisa diubah sesuai kebutuhan
4. **Schedule Time** - Default jam 2 pagi, bisa diubah di script setup
5. **Monitor Logs** - Cek log setelah cleanup untuk memastikan berjalan dengan baik

---

## 🔍 Troubleshooting

### **Error: "function does not exist"**

**Penyebab:** Function cleanup belum dibuat.

**Solusi:**
```sql
-- Jalankan script auto_cleanup_logs.sql
\i auto_cleanup_logs.sql
```

---

### **Error: "view does not exist"**

**Penyebab:** Views belum di-update.

**Solusi:**
```sql
-- Jalankan script update_views_device_identifier.sql
\i update_views_device_identifier.sql
```

---

### **Scheduled Task Tidak Berjalan**

**Windows:**
```powershell
# Cek task status
Get-ScheduledTask -TaskName "WHAC_AutoCleanup_Logs" | Select-Object State, LastRunTime

# Test manual
Start-ScheduledTask -TaskName "WHAC_AutoCleanup_Logs"
```

**Linux:**
```bash
# Cek cron service
systemctl status cron

# Test manual
docker exec whac-postgres psql -U postgres -d whac_master -c "SELECT * FROM cleanup_old_log_data();"
```

---

## 📚 File yang Dibuat

1. ✅ `auto_cleanup_logs.sql` - Function untuk cleanup
2. ✅ `update_views_device_identifier.sql` - Update views dengan device identifier
3. ✅ `setup_auto_cleanup_cron.sh` - Script setup cron job (Linux/Mac)
4. ✅ `setup_auto_cleanup_cron.ps1` - Script setup scheduled task (Windows)
5. ✅ `PANDUAN_AUTO_CLEANUP.md` - Dokumentasi ini

---

## 🎯 Kesimpulan

Dengan setup ini:
- ✅ Data logs akan otomatis dihapus setelah lebih dari 3 bulan
- ✅ Views memiliki identifier device masuk/keluar yang jelas
- ✅ Bisa query berdasarkan device direction dengan mudah
- ✅ Database tetap bersih dan performa terjaga












