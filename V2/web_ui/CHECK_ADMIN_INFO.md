# Panduan Mencari Informasi User Admin

Script ini membantu Anda melihat informasi user admin dan memverifikasi password yang digunakan.

## 🚀 Cara Menggunakan

### 1. Menggunakan Script Python (Recommended)

Jalankan script untuk melihat informasi user admin:

```bash
# Cek user admin
python check_admin_info.py admin

# Atau cek user lain
python check_admin_info.py <username>
```

Script akan:
- ✅ Menampilkan semua informasi user (ID, username, email, role, dll)
- ✅ Menampilkan status akun (aktif/nonaktif, terkunci/tidak)
- ✅ Mencoba memverifikasi password umum (termasuk 'admin123')
- ✅ Memberitahu jika password cocok dengan salah satu password umum

### 2. Menggunakan DBeaver

Jika Anda sudah terhubung ke database menggunakan DBeaver, jalankan query berikut:

```sql
-- Melihat informasi lengkap user admin
SELECT 
    id,
    username,
    password_hash,
    full_name,
    email,
    role,
    is_active,
    created_at,
    last_login,
    login_attempts,
    locked_until
FROM web_users 
WHERE username = 'admin';
```

**Catatan Penting:**
- Password disimpan sebagai **hash bcrypt** - password asli **TIDAK BISA** dibaca dari hash
- Hash adalah one-way encryption untuk keamanan
- Untuk memverifikasi password, gunakan script Python di atas

### 3. Menggunakan Docker

Jika database berjalan di Docker:

```bash
# Masuk ke direktori web_ui
cd web_ui/

# Pastikan container berjalan
docker-compose ps

# Jalankan script (akan otomatis connect ke database Docker)
python check_admin_info.py admin
```

Atau langsung query via Docker:

```bash
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT id, username, full_name, email, role, is_active FROM web_users WHERE username = 'admin';"
```

## 🔐 Memverifikasi Password

Jika password sudah direset menjadi `admin123`, script akan otomatis mendeteksi dan menampilkan:

```
🎉 PASSWORD DITEMUKAN!
Username: admin
Password: admin123
```

## 🔄 Reset Password

Jika Anda lupa password atau ingin reset:

```bash
# Reset ke admin123
python reset_user_password.py admin admin123

# Atau reset dengan password custom
python reset_user_password.py admin mynewpassword
```

Untuk Docker:

```bash
python docker-reset-password.py admin admin123
```

## 📋 Informasi yang Ditampilkan

Script akan menampilkan:
- ✅ ID User
- ✅ Username
- ✅ Full Name
- ✅ Email
- ✅ Role (admin/viewer)
- ✅ Status (Aktif/Nonaktif)
- ✅ Created At
- ✅ Last Login
- ✅ Login Attempts
- ✅ Locked Until
- ✅ Password Hash (preview)
- ✅ Verifikasi password umum

## ⚠️ Troubleshooting

### Error: Connection refused
- Pastikan database PostgreSQL sedang berjalan
- Cek kredensial database di `.env` file
- Jika menggunakan Docker, pastikan container berjalan: `docker-compose ps`

### Password tidak ditemukan
- Password mungkin bukan password umum
- Reset password menggunakan script reset
- Atau coba password lain yang mungkin Anda gunakan

### User tidak ditemukan
- Script akan menampilkan daftar user yang tersedia
- Pastikan username yang Anda masukkan benar (case-sensitive)

---

**Selamat! Sekarang Anda bisa melihat informasi user admin dengan mudah.** 🎉



