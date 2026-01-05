# Docker Setup Guide - IoT-WHAC V2

## 📦 Docker Setup Options

### Option 1: Fresh Install dengan Docker Compose (Recommended)

Untuk fresh install, database akan otomatis disetup dengan schema terbaru (sudah include full_name).

#### Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: whac-postgres
    environment:
      POSTGRES_DB: whac_master
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: Admin123
    volumes:
      # Mount init script untuk fresh database
      - ./web_ui/database_setup.sql:/docker-entrypoint-initdb.d/01-init.sql
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - whac-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  web-ui:
    build:
      context: ./web_ui
      dockerfile: Dockerfile
    container_name: whac-web-ui
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=whac_master
      - DB_USER=postgres
      - DB_PASSWORD=Admin123
      - MQTT_BROKER=mosquitto
      - MQTT_PORT=1883
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - whac-network
    restart: unless-stopped

  mosquitto:
    image: eclipse-mosquitto:2
    container_name: whac-mosquitto
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - mosquitto_data:/mosquitto/data
      - mosquitto_logs:/mosquitto/log
    ports:
      - "1883:1883"
      - "9001:9001"
    networks:
      - whac-network
    restart: unless-stopped

volumes:
  postgres_data:
  mosquitto_data:
  mosquitto_logs:

networks:
  whac-network:
    driver: bridge
```

#### Jalankan Docker Compose:

```bash
# Build dan start semua services
docker-compose up -d

# Cek logs
docker-compose logs -f

# Verify database initialized
docker exec -it whac-postgres psql -U postgres -d whac_master -c "\d user_sensor_1"
```

**✅ Database sudah include full_name columns - TIDAK perlu migration!**

---

### Option 2: Existing Database dalam Docker (Upgrade)

Jika Anda sudah punya database running di Docker dan ingin upgrade:

#### Step 1: Backup Database

```bash
# Backup dari container
docker exec whac-postgres pg_dump -U postgres whac_master > backup_$(date +%Y%m%d).sql
```

#### Step 2: Run Migration di Container

```bash
# Copy migration script ke container
docker cp web_ui/migration_add_full_name.sql whac-postgres:/tmp/

# Execute migration
docker exec -it whac-postgres psql -U postgres -d whac_master -f /tmp/migration_add_full_name.sql
```

#### Step 3: Verify

```bash
docker exec -it whac-postgres psql -U postgres -d whac_master -c "
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'user_sensor_1' AND column_name = 'full_name';
"
```

**✅ Migration hanya dilakukan SEKALI - tidak perlu run lagi!**

---

### Option 3: Docker Init Script untuk Conditional Migration

Jika ingin setup yang lebih sophisticated (auto-detect perlu migration atau tidak):

#### Create `docker-init.sh`:

```bash
#!/bin/bash
# File: web_ui/docker-init.sh

set -e

echo "🔍 Checking database state..."

# Check if full_name column exists
if psql -U postgres -d whac_master -c "\d user_sensor_1" | grep -q "full_name"; then
    echo "✅ Database already up-to-date (full_name exists)"
else
    echo "⚠️  Database needs migration (full_name not found)"
    echo "🔄 Running migration..."
    psql -U postgres -d whac_master -f /docker-entrypoint-initdb.d/02-migration.sql
    echo "✅ Migration completed"
fi

echo "🎉 Database setup complete!"
```

#### Update `docker-compose.yml`:

```yaml
services:
  postgres:
    # ... other config ...
    volumes:
      # Fresh install
      - ./web_ui/database_setup.sql:/docker-entrypoint-initdb.d/01-init.sql
      # Migration (only runs if needed)
      - ./web_ui/migration_add_full_name.sql:/docker-entrypoint-initdb.d/02-migration.sql
      # Init script
      - ./web_ui/docker-init.sh:/docker-entrypoint-initdb.d/03-init.sh
      - postgres_data:/var/lib/postgresql/data
```

**✅ Auto-detect dan run migration jika diperlukan!**

---

## 🔄 Development Workflow

### Scenario 1: Fresh Development Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd IoT-WHAC/V2

# 2. Start Docker
docker-compose up -d

# 3. Database otomatis initialized dengan schema terbaru
# ✅ TIDAK PERLU migration script!

# 4. Verify
docker exec -it whac-postgres psql -U postgres -d whac_master -c "\d user_sensor_1"
```

### Scenario 2: Pull Update (dengan perubahan schema)

```bash
# 1. Pull latest code
git pull origin main

# 2. Check if migration needed (lihat CHANGELOG atau release notes)
cat CHANGELOG_FULL_NAME_LINKING.md

# 3. Jika perlu migration:
docker cp web_ui/migration_add_full_name.sql whac-postgres:/tmp/
docker exec -it whac-postgres psql -U postgres -d whac_master -f /tmp/migration_add_full_name.sql

# 4. Restart web-ui
docker-compose restart web-ui
```

### Scenario 3: Rebuild from Scratch

```bash
# 1. Stop dan hapus containers & volumes
docker-compose down -v

# 2. Start ulang (fresh install)
docker-compose up -d

# ✅ Database setup dari awal dengan schema terbaru
# ✅ TIDAK PERLU migration!
```

---

## 🎯 Best Practices

### 1. **Version Control untuk Database State**

Tambahkan file tracking untuk database version:

```sql
-- File: web_ui/database_version.sql
CREATE TABLE IF NOT EXISTS _database_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert current version
INSERT INTO _database_version (version, description)
VALUES ('1.1.0', 'Added full_name linking feature')
ON CONFLICT (version) DO NOTHING;
```

Include di `database_setup.sql` dan migration script.

### 2. **Docker Health Check Script**

```bash
#!/bin/bash
# File: web_ui/healthcheck.sh

# Check database connection
psql -U postgres -d whac_master -c "SELECT 1" > /dev/null 2>&1
DB_STATUS=$?

# Check if full_name exists
psql -U postgres -d whac_master -c "\d user_sensor_1" | grep -q "full_name"
SCHEMA_STATUS=$?

if [ $DB_STATUS -eq 0 ] && [ $SCHEMA_STATUS -eq 0 ]; then
    echo "healthy"
    exit 0
else
    echo "unhealthy"
    exit 1
fi
```

### 3. **Environment-Specific Setup**

```yaml
# docker-compose.dev.yml - Development
services:
  postgres:
    volumes:
      - ./web_ui/database_setup.sql:/docker-entrypoint-initdb.d/01-init.sql
      # Include sample data for dev
      - ./web_ui/sample_data.sql:/docker-entrypoint-initdb.d/99-sample-data.sql

# docker-compose.prod.yml - Production
services:
  postgres:
    volumes:
      # Production uses persistent volume
      - /var/lib/whac/postgres:/var/lib/postgresql/data
      # Backup location
      - /var/lib/whac/backups:/backups
```

---

## 📊 Diagram: Setup Decision Tree

```
Start Docker Setup
│
├─ Is this fresh install?
│  ├─ YES → Use database_setup.sql (in docker-compose)
│  │        └─ ✅ Done! (includes full_name)
│  │
│  └─ NO → Existing database?
│     ├─ Has full_name column?
│     │  ├─ YES → ✅ Nothing to do
│     │  └─ NO → Run migration_add_full_name.sql ONCE
│     │           └─ ✅ Done!
│     │
│     └─ Rebuild from scratch?
│        └─ docker-compose down -v
│           └─ Use database_setup.sql
│              └─ ✅ Done!
```

---

## ❓ FAQ

### Q: Setiap restart Docker, apa database reset?
**A:** Tidak, jika menggunakan Docker volumes. Data persisten.

```bash
# Volume akan persist data
docker-compose down    # Container stop, data AMAN
docker-compose up -d   # Container start, data masih ada
```

### Q: Kapan harus run migration?
**A:** Hanya sekali saat upgrade dari versi lama ke versi baru.

```bash
# Migration chart:
v1.0 (no full_name) → migration → v1.1 (with full_name)
v1.1 (fresh install) → NO migration needed
```

### Q: Bagaimana jika migration sudah dijalankan tapi Docker restart?
**A:** Tidak masalah. Migration script sudah idempotent (aman dirun multiple times).

```sql
-- Migration uses IF NOT EXISTS
ALTER TABLE user_sensor_1 
ADD COLUMN IF NOT EXISTS full_name VARCHAR(200);
-- ✅ Safe to run multiple times
```

### Q: Apakah bisa automate migration di Docker?
**A:** Ya, gunakan Option 3 (docker-init.sh) di atas.

---

## 🚀 Quick Start Commands

### Fresh Install:
```bash
docker-compose up -d
# ✅ Done! Database ready dengan full_name
```

### Upgrade Existing:
```bash
docker cp web_ui/migration_add_full_name.sql whac-postgres:/tmp/
docker exec -it whac-postgres psql -U postgres -d whac_master -f /tmp/migration_add_full_name.sql
docker-compose restart web-ui
# ✅ Done! Database upgraded
```

### Reset Everything:
```bash
docker-compose down -v
docker-compose up -d
# ✅ Done! Fresh setup
```

---

## 🔧 Troubleshooting

### Migration script tidak jalan di Docker init

**Problem:** Script di `/docker-entrypoint-initdb.d/` tidak execute

**Solution:**
```bash
# Init scripts hanya jalan jika database kosong
# Jika database sudah ada, jalankan manual:
docker exec -it whac-postgres psql -U postgres -d whac_master -f /tmp/migration.sql
```

### Permission denied untuk init script

**Problem:** `docker-init.sh` tidak executable

**Solution:**
```bash
chmod +x web_ui/docker-init.sh
docker-compose down
docker-compose up -d
```

### Database tidak persist setelah restart

**Problem:** Docker volume tidak configured

**Solution:**
```yaml
volumes:
  postgres_data:  # ← Pastikan ini ada di docker-compose.yml

services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data  # ← Mount named volume
```

---

## 📝 Summary

| Scenario | Migration Needed? | Action |
|----------|------------------|--------|
| Fresh Docker setup | ❌ NO | Use `database_setup.sql` (auto via docker-compose) |
| Existing Docker DB | ✅ YES (once) | Run `migration_add_full_name.sql` in container |
| Docker restart | ❌ NO | Data persists via volumes |
| Docker rebuild | ❌ NO | Fresh setup from `database_setup.sql` |
| Pull code updates | ⚠️ Maybe | Check CHANGELOG, run migration if schema changed |

---

**Created:** 2025-01-02  
**Version:** 1.0  
**Last Updated:** 2025-01-02







