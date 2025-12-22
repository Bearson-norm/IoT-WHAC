# Panduan Reset Password Web UI

## 🔐 Cara Reset Password

### Method 1: Reset Password Admin (Paling Mudah)

Jika Anda lupa password untuk user **admin**:

**Menggunakan Docker (Recommended):**

```powershell
cd web_ui/
python docker-reset-password.py admin admin123
```

Atau dengan password custom:

```powershell
python docker-reset-password.py admin passwordbaru123
```

**Menggunakan Script Lokal:**

```powershell
cd web_ui/
python reset_user_password.py admin admin123
```

### Method 2: Cari Password yang Mungkin Digunakan

Jika Anda ingin mencoba password yang mungkin digunakan:

```powershell
cd web_ui/
python find_or_reset_password.py admin
```

Script ini akan:
- Mencoba password umum (admin123, admin, password123, dll)
- Memberitahu jika password cocok
- Jika tidak cocok, bisa langsung reset

### Method 3: Reset Password User Lain

Jika lupa password untuk user selain admin:

```powershell
# Ganti <username> dengan username yang ingin direset
python docker-reset-password.py <username> passwordbaru123

# Contoh:
python docker-reset-password.py Greyoungter passwordbaru123
python docker-reset-password.py Iman passwordbaru123
```

### Method 4: Menggunakan DBeaver (Manual)

1. Buka DBeaver dan connect ke database
2. Jalankan query berikut (ganti `<username>` dan `<new_password>`):

```sql
-- Reset password untuk user tertentu
-- Perlu generate password hash dulu menggunakan Python

-- Atau gunakan hash yang sudah diketahui untuk 'admin123':
UPDATE web_users 
SET password_hash = '$2b$12$7cD0.neGPVGRNL3X9nzY6uc5G1Ek8OB/PBhYDvcjKvZ0mcYK9yOyS',
    is_active = TRUE,
    login_attempts = 0,
    locked_until = NULL
WHERE username = 'admin';
```

**Catatan:** Untuk password lain, perlu generate hash menggunakan Python.

## 📋 Langkah-langkah Reset Password

### Step 1: Tentukan Username

Jika tidak ingat username, cek di database:

```powershell
# Via Docker
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT username, full_name, email, role FROM web_users ORDER BY username;"

# Atau via script
cd web_ui/
python check_admin_info.py admin
```

### Step 2: Reset Password

Pilih salah satu method di atas. Paling mudah:

```powershell
cd web_ui/
python docker-reset-password.py admin admin123
```

### Step 3: Login dengan Password Baru

Setelah reset, login dengan:
- **Username**: `admin` (atau username yang direset)
- **Password**: `admin123` (atau password baru yang Anda set)

## 🔍 Cek User yang Tersedia

Jika tidak ingat username apa saja yang ada:

```powershell
# Via Docker
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT id, username, full_name, email, role, is_active FROM web_users ORDER BY username;"
```

Atau gunakan script:

```powershell
cd web_ui/
python check_admin_info.py admin
```

## ⚠️ Troubleshooting

### Error: Container tidak ditemukan

```powershell
# Cek container
docker ps | Select-String postgres

# Jika tidak ada, start container
cd web_ui/
docker-compose up -d postgres
```

### Error: User tidak ditemukan

```powershell
# Cek user yang tersedia
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT username FROM web_users;"
```

### Error: Database connection failed

Pastikan:
1. Container PostgreSQL berjalan
2. Port 5432 tidak conflict
3. Password database benar (Admin123)

## ✅ Setelah Reset

1. **Login dengan password baru**
2. **Ubah password setelah login** (jika ada fitur change password)
3. **Simpan password di tempat yang aman**

## 🎯 Quick Reset (Copy-Paste)

Jika ingin langsung reset password admin ke `admin123`:

```powershell
cd web_ui/
python docker-reset-password.py admin admin123
```

Setelah itu login dengan:
- Username: `admin`
- Password: `admin123`

---

**File yang tersedia:**
- `docker-reset-password.py` - Reset password di Docker (Recommended)
- `reset_user_password.py` - Reset password lokal
- `find_or_reset_password.py` - Cari atau reset password
- `check_admin_info.py` - Cek info user dan verifikasi password













