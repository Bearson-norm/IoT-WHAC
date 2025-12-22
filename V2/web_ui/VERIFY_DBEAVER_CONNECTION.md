# Verifikasi Koneksi DBeaver ke Database Docker

## 📋 Konfigurasi Database Docker (dari docker-compose.yml)

Berdasarkan `docker-compose.yml`:

```yaml
postgres:
  image: postgres:13
  container_name: whac-postgres
  ports:
    - "5432:5432"  # Host:Container
  environment:
    - POSTGRES_DB=whac_master
    - POSTGRES_USER=postgres
    - POSTGRES_PASSWORD=Admin123
```

**Artinya:**
- Port `5432` di host machine di-map ke port `5432` di container
- Database name: `whac_master`
- Username: `postgres`
- Password: `Admin123`

## ✅ Konfigurasi DBeaver yang Benar

Karena port sudah di-expose, DBeaver **seharusnya** bisa connect ke database Docker menggunakan:

- **Host**: `localhost` atau `127.0.0.1`
- **Port**: `5432`
- **Database**: `whac_master`
- **Username**: `postgres`
- **Password**: `Admin123`

## 🔍 Verifikasi Koneksi

### Step 1: Pastikan Container Docker Berjalan

```powershell
docker ps | Select-String postgres
```

Harusnya muncul:
```
whac-postgres    postgres:13    ...    0.0.0.0:5432->5432/tcp
```

### Step 2: Cek Port 5432

```powershell
netstat -ano | findstr :5432
```

**Expected:** Harusnya hanya ada 1 proses yang listen di port 5432 (Docker container)

**Jika ada 2 proses:**
- Satu dari Docker container
- Satu dari PostgreSQL lokal → **Ini yang menyebabkan masalah!**

### Step 3: Test Koneksi dari Command Line

```powershell
# Test connect ke database Docker
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT version();"
```

Jika berhasil, berarti database Docker berjalan dengan baik.

### Step 4: Test Koneksi dari Host (seperti DBeaver)

```powershell
# Install psql client jika belum ada, atau gunakan Docker
docker run --rm -it --network host postgres:13 psql -h localhost -U postgres -d whac_master
# Password: Admin123
```

Atau jika punya psql lokal:

```powershell
$env:PGPASSWORD = "Admin123"
psql -h localhost -U postgres -d whac_master -c "SELECT current_database(), current_user;"
```

**Expected output:**
```
 current_database | current_user 
------------------+--------------
 whac_master      | postgres
```

### Step 5: Verifikasi di DBeaver

1. **Buka DBeaver**
2. **Test Connection** dengan konfigurasi:
   - Host: `localhost`
   - Port: `5432`
   - Database: `whac_master`
   - Username: `postgres`
   - Password: `Admin123`

3. **Jika berhasil**, jalankan query:
   ```sql
   SELECT current_database(), current_user, inet_server_addr(), inet_server_port();
   ```

   **Expected:**
   - `current_database`: `whac_master`
   - `current_user`: `postgres`
   - `inet_server_addr`: IP container (misalnya `172.x.x.x`)
   - `inet_server_port`: `5432`

## 🐛 Troubleshooting

### Masalah: Port 5432 sudah digunakan

**Gejala:** DBeaver connect tapi ke database yang salah

**Solusi:**

1. **Cek proses yang menggunakan port 5432:**
   ```powershell
   netstat -ano | findstr :5432
   ```

2. **Jika ada PostgreSQL lokal, stop service:**
   ```powershell
   # Cek service PostgreSQL
   Get-Service | Select-String postgres
   
   # Stop service (ganti nama service sesuai yang ada)
   Stop-Service postgresql-x64-13
   # atau
   Stop-Service postgresql-x64-14
   ```

3. **Atau ubah port Docker** (tidak recommended):
   ```yaml
   # Di docker-compose.yml
   ports:
     - "5433:5432"  # Gunakan port 5433 di host
   ```
   
   Lalu di DBeaver, gunakan port `5433`.

### Masalah: Connection refused

**Gejala:** DBeaver tidak bisa connect

**Solusi:**

1. **Pastikan container berjalan:**
   ```powershell
   docker ps | Select-String postgres
   ```

2. **Restart container jika perlu:**
   ```powershell
   cd web_ui/
   docker-compose restart postgres
   ```

3. **Cek log container:**
   ```powershell
   docker logs whac-postgres --tail 50
   ```

### Masalah: Authentication failed

**Gejala:** Password salah atau user tidak ditemukan

**Solusi:**

1. **Verifikasi password di docker-compose.yml:**
   - Pastikan `POSTGRES_PASSWORD=Admin123`
   - Atau cek `.env` file jika ada

2. **Test dengan Docker exec:**
   ```powershell
   docker exec -it whac-postgres psql -U postgres -d whac_master
   # Jika berhasil tanpa password prompt, berarti password benar
   ```

### Masalah: Database tidak ditemukan

**Gejala:** Error "database does not exist"

**Solusi:**

1. **Cek database yang ada:**
   ```powershell
   docker exec -it whac-postgres psql -U postgres -c "\l"
   ```

2. **Pastikan database `whac_master` ada**

3. **Jika tidak ada, jalankan init:**
   ```powershell
   cd web_ui/
   docker-compose up db-init
   ```

## 🔍 Cara Memastikan DBeaver Connect ke Docker

### Method 1: Cek Container ID

Jalankan query di DBeaver:

```sql
-- Cek hostname/container info
SELECT 
    current_database(),
    current_user,
    version(),
    inet_server_addr() as server_ip,
    inet_server_port() as server_port;
```

Lalu cek IP container:

```powershell
docker inspect whac-postgres | Select-String "IPAddress"
```

Jika `server_ip` dari query sama dengan IP container, berarti connect ke Docker ✅

### Method 2: Cek Data yang Unik

1. **Buat user test di Docker:**
   ```powershell
   docker exec -it whac-postgres psql -U postgres -d whac_master -c "INSERT INTO web_users (username, password_hash, role) VALUES ('docker_test', 'test', 'viewer');"
   ```

2. **Cek di DBeaver:**
   ```sql
   SELECT * FROM web_users WHERE username = 'docker_test';
   ```

   Jika muncul, berarti connect ke Docker ✅

3. **Hapus test user:**
   ```sql
   DELETE FROM web_users WHERE username = 'docker_test';
   ```

### Method 3: Cek Process List

Jalankan query di DBeaver:

```sql
SELECT pid, usename, application_name, client_addr, state 
FROM pg_stat_activity 
WHERE datname = 'whac_master';
```

Jika `client_addr` adalah IP dari host machine (bukan container IP), berarti connect dari luar container (seperti DBeaver) ✅

## ✅ Checklist Verifikasi

- [ ] Container `whac-postgres` sedang berjalan
- [ ] Port 5432 hanya digunakan oleh Docker (tidak ada PostgreSQL lokal)
- [ ] Test connection di DBeaver berhasil
- [ ] Query `SELECT current_database()` mengembalikan `whac_master`
- [ ] Data di DBeaver sama dengan data di Web UI
- [ ] Test user di Docker muncul di DBeaver

## 💡 Tips

1. **Gunakan Connection Name yang Jelas:**
   - Di DBeaver, beri nama connection: "WHAC Docker Database"
   - Ini membantu membedakan dengan connection lain

2. **Save Password:**
   - Centang "Save password" di DBeaver
   - Ini memudahkan koneksi berikutnya

3. **Test Connection Secara Berkala:**
   - Jika data tidak sinkron, test connection lagi
   - Pastikan masih connect ke database yang benar

4. **Monitor Container:**
   ```powershell
   # Watch container status
   docker ps --filter "name=whac-postgres"
   ```

---

**Kesimpulan:** Konfigurasi DBeaver Anda (`localhost:5432`) **sudah benar** untuk connect ke database Docker, asalkan:
1. Container Docker berjalan
2. Tidak ada PostgreSQL lokal yang conflict di port 5432
3. Password dan database name sesuai dengan docker-compose.yml


























