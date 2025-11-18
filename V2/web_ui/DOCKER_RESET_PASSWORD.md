# Reset Password di Docker Container

Panduan untuk mereset password user di sistem Docker.

## ⚠️ PENTING: Password Tidak Bisa Ditemukan

Password asli **TIDAK BISA** ditemukan dari hash bcrypt. Hash adalah enkripsi satu arah (one-way encryption) untuk keamanan. Satu-satunya cara adalah **mereset password** ke nilai baru.

## Cara Reset Password di Docker

### Opsi 1: Menggunakan Script Python (Recommended)

Script ini bisa dijalankan dari **host machine** (tidak perlu masuk ke container):

```bash
# Reset password admin (default: password123)
python web_ui/docker-reset-password.py admin

# Reset dengan password custom
python web_ui/docker-reset-password.py admin mynewpassword

# Reset password user lain
python web_ui/docker-reset-password.py Mamat
python web_ui/docker-reset-password.py Greyoungter newpass123
```

**Keuntungan:**
- Bisa dijalankan dari host
- Otomatis mencari container PostgreSQL
- Menampilkan info user sebelum reset
- Support untuk semua user, bukan hanya admin

### Opsi 2: Menggunakan Script Bash

```bash
# Reset password admin (default: password123)
bash web_ui/docker-reset-password.sh admin

# Reset dengan password custom
bash web_ui/docker-reset-password.sh admin mynewpassword

# Reset password user lain
bash web_ui/docker-reset-password.sh Mamat
```

### Opsi 3: Reset Admin Saja (Script Lama)

Jika hanya perlu reset admin:

```bash
# Reset admin ke 'admin123'
python web_ui/docker-fix-admin.py

# Atau menggunakan bash
bash web_ui/docker-fix-admin.sh
```

### Opsi 4: Manual dengan Docker Exec

Jika script tidak bekerja, bisa langsung akses database:

```bash
# 1. Masuk ke container PostgreSQL
docker exec -it whac-postgres psql -U postgres -d whac_master

# 2. Di dalam psql, jalankan SQL (ganti <username> dan <new_password>)
#    Tapi perlu generate hash dulu dengan Python
```

Atau generate hash dulu, lalu update:

```bash
# Generate hash untuk password baru
docker exec whac-web-ui python3 -c "import bcrypt; print(bcrypt.hashpw('mynewpassword'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))"

# Copy hash yang dihasilkan, lalu update di database
docker exec -it whac-postgres psql -U postgres -d whac_master -c "UPDATE web_users SET password_hash = '<hash_yang_dihasilkan>', is_active = TRUE, locked_until = NULL, login_attempts = 0 WHERE username = 'admin';"
```

## Contoh Penggunaan

### Reset Password Admin

```bash
cd web_ui
python docker-reset-password.py admin
```

Output:
```
============================================================
🔐 Reset Password di Docker Container
============================================================
✓ Menggunakan container: whac-postgres

[*] Mengecek user 'admin'...
✓ User ditemukan:
   ID: 1
   Username: admin
   Full Name: System Administrator
   Email: admin@whac.com
   Role: admin

[*] Membuat password hash untuk 'password123'...
✓ Password hash dibuat

[*] Mereset password...
============================================================
✅ Password berhasil direset!
============================================================
Login Credentials:
   Username: admin
   Password: password123
============================================================
⚠️  Silakan ubah password setelah login!
============================================================
```

### Reset Password User Lain

```bash
python docker-reset-password.py Mamat mynewpass123
```

## Troubleshooting

### Container Tidak Ditemukan

Jika script tidak menemukan container:

```bash
# Cek container yang berjalan
docker ps

# Cek nama container PostgreSQL
docker ps --format '{{.Names}}' | grep postgres
```

### Error: Docker Command Not Found

Pastikan Docker sudah terinstall dan ada di PATH:

```bash
# Test Docker
docker --version

# Test Docker Compose
docker-compose --version
```

### Error: Permission Denied

Pastikan script bisa dijalankan:

```bash
# Linux/Mac
chmod +x web_ui/docker-reset-password.py
chmod +x web_ui/docker-reset-password.sh

# Windows (PowerShell)
# Tidak perlu chmod, langsung jalankan dengan python
```

### Error: Python/bcrypt Tidak Tersedia

Script akan otomatis mencari Python di berbagai container. Jika masih error:

1. Pastikan container web-ui berjalan (mengandung Python + bcrypt)
2. Atau install bcrypt di host: `pip install bcrypt`

## Setelah Reset Password

1. **Login** dengan username dan password baru
2. **Ubah password** melalui menu "Change Password" di web UI
3. **Jangan lupa** password baru yang Anda buat!

## Catatan Keamanan

- Password hash adalah one-way encryption - tidak bisa dibalik
- Setelah reset, password lama tidak bisa digunakan lagi
- Disarankan untuk mengubah password setelah login pertama kali
- Jangan share password reset script dengan user non-admin

