# 🔧 Cara Menjalankan SQL Script di PowerShell

## ❌ Error yang Sering Terjadi

### **Error: "The '<' operator is reserved for future use"**

**Penyebab:** PowerShell tidak mendukung redirect operator `<` seperti di bash/Linux.

**Salah:**
```powershell
docker exec -i whac-postgres psql -U postgres -d whac_master < script.sql
```

**Benar:**
```powershell
Get-Content script.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

---

## ✅ Cara yang Benar untuk PowerShell

### **Method 1: Menggunakan Get-Content dengan Pipe (Recommended)**

```powershell
# Single script
Get-Content fix_database_foreign_keys.sql | docker exec -i whac-postgres psql -U postgres -d whac_master

# Dengan output ke file
Get-Content script.sql | docker exec -i whac-postgres psql -U postgres -d whac_master > output.txt
```

### **Method 2: Menggunakan Here-String**

```powershell
$sql = @"
ALTER TABLE store_001 ADD COLUMN device_id VARCHAR(50);
"@

$sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

### **Method 3: Menggunakan -Command dengan psql**

```powershell
docker exec whac-postgres psql -U postgres -d whac_master -c "SELECT * FROM store_001 LIMIT 5;"
```

---

## 📋 Contoh Lengkap: Menjalankan Database Fixes

### **Step 1: Backup Database**

```powershell
# Buat folder backup
if (-not (Test-Path "backups")) { New-Item -ItemType Directory -Path "backups" }

# Backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker exec whac-postgres pg_dump -U postgres whac_master > "backups\backup_$timestamp.sql"
```

### **Step 2: Jalankan Script SQL**

```powershell
# Script 1: Foreign Keys
Get-Content fix_database_foreign_keys.sql | docker exec -i whac-postgres psql -U postgres -d whac_master

# Script 2: Username Redundancy
Get-Content remove_username_redundancy.sql | docker exec -i whac-postgres psql -U postgres -d whac_master

# Script 3: Multi-Sensor
Get-Content fix_multi_sensor_fingerprint.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

### **Step 3: Verifikasi**

```powershell
# Cek Foreign Keys
docker exec whac-postgres psql -U postgres -d whac_master -c "SELECT constraint_name, table_name FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY';"

# Cek struktur tabel
docker exec whac-postgres psql -U postgres -d whac_master -c "\d store_001"
```

---

## 🚀 Script Otomatis (PowerShell)

Gunakan script `run_database_fixes.ps1` yang sudah dibuat:

```powershell
.\run_database_fixes.ps1
```

Script ini akan:
- ✅ Backup database otomatis
- ✅ Menjalankan semua script SQL
- ✅ Memberikan konfirmasi sebelum perubahan
- ✅ Menampilkan progress dan hasil

---

## 📝 Perbandingan: PowerShell vs Bash

| Operasi | PowerShell | Bash/Linux |
|---------|-----------|------------|
| Redirect input | `Get-Content file.sql \| docker exec -i ...` | `docker exec -i ... < file.sql` |
| Redirect output | `> output.txt` | `> output.txt` |
| Pipe | `\|` | `\|` |
| Here-string | `@"..."@` | `<<EOF ... EOF` |

---

## ⚠️ Catatan Penting

1. **Encoding:** Pastikan file SQL menggunakan encoding UTF-8
2. **Path:** Gunakan path relatif atau absolut yang benar
3. **Error Handling:** Cek `$LASTEXITCODE` setelah menjalankan command:
   ```powershell
   Get-Content script.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
   if ($LASTEXITCODE -ne 0) {
       Write-Host "Error occurred!" -ForegroundColor Red
   }
   ```

---

## 🔍 Troubleshooting

### **Error: "Cannot find path"**

**Penyebab:** Path file tidak benar atau tidak ada.

**Solusi:**
```powershell
# Cek path
Get-Location
Test-Path "fix_database_foreign_keys.sql"

# Gunakan path absolut jika perlu
Get-Content "C:\full\path\to\script.sql" | docker exec -i whac-postgres psql -U postgres -d whac_master
```

### **Error: "Container not found"**

**Penyebab:** Container Docker tidak berjalan.

**Solusi:**
```powershell
# Cek container
docker ps --filter "name=whac-postgres"

# Start container jika tidak berjalan
docker-compose up -d postgres
```

### **Error: "Permission denied"**

**Penyebab:** Tidak punya akses ke file atau container.

**Solusi:**
```powershell
# Jalankan PowerShell sebagai Administrator
# Atau cek permission file
Get-Acl "script.sql"
```

---

## 📚 Referensi

- [PowerShell Redirection](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_redirection)
- [Docker Exec Documentation](https://docs.docker.com/engine/reference/commandline/exec/)
- [PostgreSQL psql Documentation](https://www.postgresql.org/docs/current/app-psql.html)












