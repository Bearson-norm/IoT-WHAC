# Fix Admin Login Issue in Docker

Jika Anda mengalami masalah login admin di Docker, ikuti langkah berikut:

## Solusi 1: Rebuild Container (Recommended)

Script `init_db.py` sudah diperbaiki untuk memastikan admin user dibuat dengan password yang benar:

```bash
cd web_ui
docker-compose down -v  # Hapus volume juga untuk fresh start
docker-compose up -d --build
```

## Solusi 2: Fix Manual dengan Script Python

Jalankan script untuk fix password admin di database Docker:

```bash
python web_ui/docker-fix-admin.py
```

Atau jika menggunakan bash:

```bash
bash web_ui/docker-fix-admin.sh
```

## Solusi 3: Fix Manual dengan Docker Exec

Connect langsung ke database container:

```bash
docker exec -it whac-postgres psql -U postgres -d whac_master
```

Kemudian jalankan SQL:

```sql
UPDATE web_users 
SET password_hash = '$2b$12$7cD0.neGPVGRNL3X9nzY6uc5G1Ek8OB/PBhYDvcjKvZ0mcYK9yOyS',
    is_active = TRUE,
    login_attempts = 0,
    locked_until = NULL
WHERE username = 'admin';

-- Jika admin tidak ada, buat baru:
INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, login_attempts, locked_until)
SELECT 'admin', '$2b$12$7cD0.neGPVGRNL3X9nzY6uc5G1Ek8OB/PBhYDvcjKvZ0mcYK9yOyS', 'System Administrator', 'admin@whac.com', 'admin', TRUE, 0, NULL
WHERE NOT EXISTS (SELECT 1 FROM web_users WHERE username = 'admin');
```

## Kredensial Login

Setelah fix, gunakan kredensial berikut:

- **Username**: `admin`
- **Password**: `admin123`

## Troubleshooting

### Cek apakah container db-init berjalan
```bash
docker logs whac-db-init
```

### Cek logs web-ui
```bash
docker logs whac-web-ui
```

### Cek apakah database sudah terinisialisasi
```bash
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT username, is_active, login_attempts, locked_until FROM web_users WHERE username = 'admin';"
```

### Verifikasi password hash
```bash
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT password_hash FROM web_users WHERE username = 'admin';"
```

Hash yang benar harus dimulai dengan: `$2b$12$7cD0.neGPVGRNL3X9nzY6uc5G1Ek8OB/PBhYDvcjKvZ0mcYK9yOyS`




