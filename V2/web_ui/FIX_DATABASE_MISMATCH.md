# Fix: Data Tidak Sinkron Antara Web UI dan DBeaver

## 🔍 Masalah

- User "Iman" muncul di Web UI tapi **TIDAK ada** di database DBeaver
- User "testuser" ada di database DBeaver tapi **TIDAK muncul** di Web UI

## 🔎 Penyebab

**Web UI dan DBeaver menggunakan database yang berbeda!**

- **Web UI (Docker)**: Menggunakan `DB_HOST=postgres` → Connect ke database **di dalam Docker container**
- **DBeaver**: Menggunakan `localhost:5432` → Connect ke database **di host machine** (atau database lokal)

Meskipun port sudah di-expose (`5432:5432`), jika ada PostgreSQL lokal yang juga berjalan di port 5432, DBeaver mungkin connect ke database lokal, bukan database Docker.

## 🔧 Solusi

### Step 1: Verifikasi Database yang Digunakan

Jalankan script untuk membandingkan kedua database:

```bash
cd web_ui/
python check_database_mismatch.py
```

Script ini akan:
- Cek users di database Docker
- Cek users di database localhost
- Bandingkan dan tunjukkan perbedaan

### Step 2: Tentukan Database yang Benar

**Pertanyaan:**
- Database mana yang seharusnya digunakan? (Docker atau localhost?)
- Data mana yang lebih lengkap/benar?

### Step 3: Sync Data

#### Opsi A: Sync dari Docker ke Localhost

Jika data yang benar ada di Docker:

```powershell
# Export dari Docker
docker exec whac-postgres pg_dump -U postgres -d whac_master -t web_users --data-only --column-inserts > docker_users.sql

# Import ke localhost
$env:PGPASSWORD = "Admin123"
psql -h localhost -U postgres -d whac_master -f docker_users.sql
```

#### Opsi B: Sync dari Localhost ke Docker

Jika data yang benar ada di localhost:

```powershell
# Export dari localhost
$env:PGPASSWORD = "Admin123"
pg_dump -h localhost -U postgres -d whac_master -t web_users --data-only --column-inserts > localhost_users.sql

# Import ke Docker
Get-Content localhost_users.sql | docker exec -i whac-postgres psql -U postgres -d whac_master
```

#### Opsi C: Gunakan Script Sync

```powershell
cd web_ui/
.\sync_users_simple.ps1
```

### Step 4: Pastikan Menggunakan Database yang Sama

**Untuk Web UI:**
- Pastikan environment variable `DB_HOST=postgres` (untuk Docker)
- Atau `DB_HOST=localhost` (jika ingin menggunakan database lokal)

**Untuk DBeaver:**
- Jika ingin connect ke Docker: `localhost:5432` (port sudah di-expose)
- Pastikan tidak ada PostgreSQL lokal yang berjalan di port 5432
- Atau gunakan port berbeda untuk PostgreSQL lokal

### Step 5: Verifikasi Setelah Sync

```sql
-- Di DBeaver, jalankan:
SELECT id, username, full_name, email, role, created_at 
FROM web_users 
ORDER BY created_at DESC;
```

Harusnya sama dengan yang muncul di Web UI.

## 🔍 Cek Database yang Aktif

### Cek Port 5432

```powershell
# Cek apakah ada proses yang menggunakan port 5432
netstat -ano | findstr :5432
```

Jika ada 2 proses, berarti ada 2 database instance:
- Satu di Docker
- Satu di localhost

### Cek Container Docker

```powershell
docker ps | Select-String postgres
```

Pastikan container `whac-postgres` sedang berjalan.

### Cek Environment Variables Web UI

```powershell
docker exec whac-web-ui env | Select-String DB_
```

Pastikan `DB_HOST=postgres` (untuk Docker) atau `DB_HOST=localhost` (untuk lokal).

## 💡 Rekomendasi

### Solusi Terbaik: Gunakan Database Docker Saja

1. **Stop PostgreSQL lokal** (jika ada):
   ```powershell
   # Windows Service
   Stop-Service postgresql-x64-13
   ```

2. **Pastikan hanya Docker yang berjalan**:
   ```powershell
   docker ps | Select-String postgres
   ```

3. **DBeaver connect ke Docker**:
   - Host: `localhost`
   - Port: `5432`
   - Database: `whac_master`
   - User: `postgres`
   - Password: `Admin123`

4. **Web UI tetap menggunakan Docker**:
   - `DB_HOST=postgres` (di dalam Docker network)

Dengan ini, Web UI dan DBeaver akan menggunakan **database yang sama** (Docker).

## 🐛 Troubleshooting

### Masalah: Port 5432 sudah digunakan

**Solusi:**
- Stop PostgreSQL lokal
- Atau ubah port Docker di `docker-compose.yml`:
  ```yaml
  ports:
    - "5433:5432"  # Gunakan port 5433 di host
  ```
- DBeaver connect ke `localhost:5433`

### Masalah: Data masih tidak sinkron setelah sync

**Solusi:**
1. Pastikan sync berhasil (cek jumlah user)
2. Refresh DBeaver connection
3. Restart Web UI container: `docker-compose restart web-ui`
4. Clear browser cache dan hard refresh (Ctrl+F5)

### Masalah: User hilang setelah sync

**Solusi:**
- Backup dulu sebelum sync
- Gunakan `ON CONFLICT DO UPDATE` saat import
- Atau hapus semua user dulu, baru import

## ✅ Checklist

- [ ] Script `check_database_mismatch.py` sudah dijalankan
- [ ] Database yang benar sudah ditentukan
- [ ] Data sudah di-sync
- [ ] DBeaver connect ke database yang benar
- [ ] Web UI menggunakan database yang sama
- [ ] Data sudah diverifikasi (sama di kedua tempat)

---

**File yang dibuat:**
- `check_database_mismatch.py` - Script untuk compare kedua database
- `FIX_DATABASE_MISMATCH.md` - Dokumentasi ini



