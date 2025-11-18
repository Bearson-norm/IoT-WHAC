# Panduan Menghubungkan DBeaver ke Database Web UI

Panduan lengkap untuk menghubungkan DBeaver ke database PostgreSQL Web UI.

## 📋 Informasi Koneksi Database

Berdasarkan konfigurasi default:

- **Database Type**: PostgreSQL
- **Host**: `localhost` (atau `127.0.0.1`)
- **Port**: `5432`
- **Database Name**: `whac_master`
- **Username**: `postgres`
- **Password**: `Admin123`

> **Catatan Penting**: 
> - Jika database berjalan di Docker, port `5432` sudah di-expose ke localhost di `docker-compose.yml`
> - Ketika Anda connect ke `localhost:5432` menggunakan DBeaver, Anda akan terhubung ke **database Docker**
> - Ini adalah database yang sama yang digunakan oleh Web UI container
> - Jika Anda punya PostgreSQL lokal yang juga menggunakan port 5432, pastikan Docker container sudah berjalan dan port tidak conflict

## 🚀 Langkah-langkah Menghubungkan DBeaver

### 1. Pastikan Database Docker Berjalan

Sebelum menghubungkan, pastikan container PostgreSQL berjalan:

**Windows PowerShell:**
```powershell
# Cek status container
docker ps | Select-String postgres

# Atau jika menggunakan docker-compose
cd web_ui/
docker-compose ps
```

**Linux/Mac:**
```bash
# Cek status container
docker ps | grep postgres

# Atau jika menggunakan docker-compose
cd web_ui/
docker-compose ps
```

Jika belum berjalan, jalankan:

```bash
cd web_ui/
docker-compose up -d postgres
```

> **Penting**: Pastikan container `whac-postgres` sedang berjalan. Jika tidak, DBeaver tidak bisa connect.

### 2. Buka DBeaver

1. Buka aplikasi DBeaver di komputer Anda
2. Jika belum terinstall, download dari [dbeaver.io](https://dbeaver.io/)

### 3. Buat Koneksi Baru

1. **Klik ikon "New Database Connection"** (ikon kabel/konektor di toolbar atas)
   - Atau: **File → New → Database Connection**
   - Atau: Tekan **Ctrl+Shift+N** (Windows/Linux) atau **Cmd+Shift+N** (Mac)

2. **Pilih PostgreSQL** dari daftar database
   - Cari "PostgreSQL" di kotak pencarian
   - Klik untuk memilih, lalu klik **Next**

### 4. Konfigurasi Koneksi

Di jendela **Edit Connection**, isi form berikut:

#### Tab Main

- **Host**: `localhost` (atau `127.0.0.1`)
- **Port**: `5432`
- **Database**: `whac_master`
- **Username**: `postgres`
- **Password**: `Admin123`
  - ✅ Centang **Save password** jika ingin DBeaver menyimpan password

#### Tab Driver Properties (Opsional)

Tidak perlu diubah jika menggunakan default.

#### Tab SSH (Tidak Perlu)

Skip tab ini kecuali Anda menghubungkan ke server remote via SSH.

### 5. Test Koneksi

1. Klik tombol **Test Connection** di bagian bawah jendela
2. DBeaver akan meminta download driver PostgreSQL jika belum ada:
   - Klik **Download** dan tunggu hingga selesai
3. Jika berhasil, akan muncul pesan: **"Connected"** atau **"Connected successfully"**
4. Jika gagal, periksa:
   - Apakah container PostgreSQL sedang berjalan?
   - Apakah port 5432 sudah digunakan oleh aplikasi lain?
   - Apakah kredensial (username/password) sudah benar?

### 6. Simpan Koneksi

1. Klik **Finish** untuk menyimpan koneksi
2. Beri nama untuk koneksi (contoh: "WHAC Web UI Database")
3. Koneksi akan muncul di **Database Navigator** panel sebelah kiri

### 7. Eksplorasi Database

Setelah terhubung, Anda bisa melihat:

- 📁 **Schemas** → `public`
  - 📋 **Tables**:
    - `web_users` - Tabel user untuk autentikasi web UI
    - `user_sessions` - Tabel session user
    - `log_data` - Data log fingerprint scan
    - `log_action` - Log aksi akses (granted/denied)
    - `store_001` - Data user untuk store 001
  - 👁️ **Views**:
    - `fingerprint_logs` - View untuk melihat log fingerprint
    - `action_logs` - View untuk melihat log aksi

## 🔍 Query Contoh

Setelah terhubung, Anda bisa menjalankan query SQL:

### Melihat Semua User

```sql
SELECT * FROM web_users;
```

### Melihat Log Fingerprint

```sql
SELECT * FROM fingerprint_logs 
ORDER BY timestamp DESC 
LIMIT 100;
```

### Melihat Log Aksi

```sql
SELECT * FROM action_logs 
WHERE granted_denied = 'granted'
ORDER BY timestamp DESC;
```

### Melihat Data Store 001

```sql
SELECT * FROM store_001;
```

### Memeriksa Database Docker

Ketika Anda connect ke `localhost:5432`, Anda akan terhubung ke **database Docker**. Untuk memverifikasi:

```sql
-- Cek jumlah user di database
SELECT COUNT(*) as total_users FROM web_users;

-- Lihat semua user
SELECT id, username, full_name, email, role, is_active, created_at, last_login 
FROM web_users 
ORDER BY created_at DESC;
```

**Tips:**
- Jika hanya melihat 1 user (admin), berarti database Docker belum ter-sync dengan data lengkap
- Gunakan script `check_docker_db.py` untuk membandingkan dengan database lokal
- Jika perlu sync data, gunakan script `sync_users_simple.ps1` (Windows) atau `sync_users_simple.sh` (Linux/Mac)

### Melihat Informasi User Admin

Untuk melihat informasi lengkap user admin (termasuk password hash):

```sql
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

Atau untuk melihat semua user:

```sql
SELECT 
    id,
    username,
    full_name,
    email,
    role,
    is_active,
    created_at,
    last_login
FROM web_users 
ORDER BY username;
```

**Catatan Penting tentang Password:**
- Password disimpan sebagai **hash bcrypt** di kolom `password_hash`
- Password asli **TIDAK BISA** dibaca dari hash (one-way encryption)
- Untuk memverifikasi password, gunakan script Python: `python check_admin_info.py admin`
- Untuk reset password, gunakan: `python reset_user_password.py admin admin123`

## 🔧 Troubleshooting

### Error: Connection refused

**Penyebab**: PostgreSQL tidak berjalan atau port tidak accessible

**Solusi**:
```bash
# Cek apakah container berjalan
docker ps | grep whac-postgres

# Jika tidak berjalan, start container
cd web_ui/
docker-compose up -d postgres

# Cek logs jika ada masalah
docker-compose logs postgres
```

### Error: Password authentication failed

**Penyebab**: Username atau password salah

**Solusi**:
- Pastikan username: `postgres`
- Pastikan password: `Admin123`
- Jika Anda mengubah password di `.env` file, gunakan password tersebut

### Error: Database does not exist

**Penyebab**: Database `whac_master` belum dibuat

**Solusi**:
```bash
# Database seharusnya dibuat otomatis oleh docker-compose
# Tapi jika tidak, jalankan init container
cd web_ui/
docker-compose up db-init
```

### Port 5432 already in use

**Penyebab**: Port 5432 sudah digunakan aplikasi lain

**Solusi 1**: Hentikan aplikasi lain yang menggunakan port 5432

**Solusi 2**: Ubah port di `docker-compose.yml`:
```yaml
postgres:
  ports:
    - "5433:5432"  # Ubah dari 5432:5432 ke 5433:5432
```
Kemudian di DBeaver, gunakan port `5433` sebagai Host port (tapi internal tetap 5432).

### Koneksi lambat atau timeout

**Penyebab**: Resource Docker terbatas

**Solusi**:
- Pastikan Docker memiliki cukup memory (minimal 2GB)
- Restart container: `docker-compose restart postgres`

## 📝 Catatan Penting

1. **Password Default**: Password default adalah `Admin123`. Untuk production, sebaiknya ubah password yang lebih kuat.

2. **Backup Database**: Sebelum melakukan perubahan besar, selalu backup database:
   ```bash
   docker exec whac-postgres pg_dump -U postgres whac_master > backup.sql
   ```

3. **Data Persistence**: Data disimpan di Docker volume `postgres_data`. Volume ini tidak akan terhapus meskipun container dihapus.

4. **Restore Database**:
   ```bash
   cat backup.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
   ```

## 🎯 Tips DBeaver

- **Dark Mode**: Preferences → Appearance → Theme
- **Query Shortcuts**: Ctrl+Enter untuk menjalankan query
- **Auto-complete**: Tekan Ctrl+Space untuk autocomplete
- **Format SQL**: Tekan Ctrl+Shift+F untuk format SQL code
- **Export Data**: Klik kanan tabel → Export Data → Pilih format (CSV, Excel, dll)

## 📚 Referensi

- [DBeaver Documentation](https://dbeaver.com/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Selamat! Database Anda sekarang sudah terhubung ke DBeaver.** 🎉





