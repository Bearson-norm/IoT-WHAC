# 🚀 Deployment Guide - Windows (Docker)

## ✅ Status Konfigurasi

**GOOD NEWS!** Semua fix yang dibuat hari ini **SUDAH ADA** di `database_setup.sql`, jadi:

### ✅ Fresh Deployment (Komputer Baru)
**Tidak perlu migration!** File `web_ui/database_setup.sql` sudah include:
- ✅ `device_id VARCHAR(50)` columns
- ✅ `sensor_location VARCHAR(20)` columns
- ✅ All required indexes
- ✅ Proper schema untuk multi-sensor support

### ⚠️ Existing Deployment (Database Sudah Ada)
**Perlu migration!** Jika database sudah dibuat sebelum Nov 19, 2025, gunakan `migrate_add_device_id.sql`.

---

## 📋 Prerequisites

### 1. Software Requirements
```
✅ Docker Desktop for Windows
✅ Git (optional, untuk clone repository)
✅ Text Editor (VS Code, Notepad++, dll)
```

### 2. Hardware Requirements
```
✅ RAM: Minimum 4GB (Recommended 8GB+)
✅ Storage: Minimum 10GB free space
✅ Network: Internet connection untuk pull Docker images
```

---

## 🚀 Fresh Deployment Steps

### Step 1: Prepare Files

**Option A: Clone dari Git (Recommended)**
```powershell
cd C:\Projects
git clone <your-repo-url> IoT-WHAC
cd IoT-WHAC\V2
```

**Option B: Copy Files Manual**
1. Copy seluruh folder project ke komputer baru
2. Pastikan struktur folder intact:
   ```
   IoT-WHAC\V2\
   ├── web_ui\
   ├── local_machine\
   ├── server\
   └── docker-compose.yml
   ```

### Step 2: Configure Environment Variables

**Web UI Configuration:**
```powershell
cd web_ui
cp env.example .env
```

Edit `.env` file dengan Notepad atau VS Code:
```env
# Database Configuration
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
DB_PORT=5432

# MQTT Configuration
MQTT_BROKER=103.87.67.139  # Your VPS IP
MQTT_PORT=1883
MQTT_ACTION_TOPIC=WHAC/Store001/action
MQTT_SCAN_TOPIC=WHAC/Store001/in

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-this
```

**⚠️ PENTING:** Ganti `SECRET_KEY` dengan random string untuk security!

**Generate Secret Key (PowerShell):**
```powershell
# Method 1: Random bytes
$bytes = New-Object byte[] 32
(New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
[Convert]::ToBase64String($bytes)

# Method 2: Simple random string
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

### Step 3: Start Docker Containers

**Start Web UI + PostgreSQL:**
```powershell
cd web_ui
docker-compose up -d
```

**Expected output:**
```
Creating network "web_ui_whac-network" with driver "bridge"
Creating volume "web_ui_postgres_data" with default driver
Creating whac-postgres ... done
Creating whac-db-init  ... done
Creating whac-web-ui   ... done
```

### Step 4: Verify Deployment

**Check containers are running:**
```powershell
docker ps
```

**Expected containers:**
```
CONTAINER ID   IMAGE              STATUS         PORTS                    NAMES
xxxxxxxxxxxx   web_ui-web-ui      Up 2 minutes   0.0.0.0:5000->5000/tcp  whac-web-ui
xxxxxxxxxxxx   postgres:13        Up 2 minutes   0.0.0.0:5432->5432/tcp  whac-postgres
```

**Check logs for errors:**
```powershell
# Web UI logs
docker logs whac-web-ui

# PostgreSQL logs
docker logs whac-postgres
```

**No errors? ✅ You're good!**

### Step 5: Access Web UI

**Open browser:**
```
http://localhost:5000
```

**Default login:**
- Username: `admin`
- Password: `admin123`

**⚠️ IMPORTANT:** Change admin password after first login!

### Step 6: Configure Local Machine (Raspberry Pi)

**See:** `local_machine/README.md` for Raspberry Pi setup instructions.

**Key points:**
1. Copy `local_machine/` folder to Raspberry Pi
2. Configure `.env` with MQTT broker IP
3. Run `setup_multi_sensor.sh` for multi-sensor setup
4. Start service: `sudo systemctl start fingerprint-client`

---

## 🔄 Existing Deployment Migration

**If database already exists (created before Nov 19, 2025):**

### Check if Migration Needed

```powershell
# Connect to database
docker exec -it whac-postgres psql -U postgres -d whac_master

# Check if columns exist
\d log_data
\d log_action

# Look for: device_id and sensor_location columns
# If missing, proceed with migration
```

### Run Migration

**Option 1: Run SQL script**
```powershell
docker exec -i whac-postgres psql -U postgres -d whac_master < web_ui/migrate_add_device_id.sql
```

**Option 2: Execute commands directly**
```powershell
# Add device_id and sensor_location
docker exec whac-postgres psql -U postgres -d whac_master -c "ALTER TABLE log_data ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001'; ALTER TABLE log_data ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20) DEFAULT 'unknown';"

docker exec whac-postgres psql -U postgres -d whac_master -c "ALTER TABLE log_action ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001'; ALTER TABLE log_action ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20) DEFAULT 'unknown';"

# Create indexes
docker exec whac-postgres psql -U postgres -d whac_master -c "CREATE INDEX IF NOT EXISTS idx_log_data_device_id ON log_data(device_id); CREATE INDEX IF NOT EXISTS idx_log_data_sensor_location ON log_data(sensor_location); CREATE INDEX IF NOT EXISTS idx_log_action_device_id ON log_action(device_id); CREATE INDEX IF NOT EXISTS idx_log_action_sensor_location ON log_action(sensor_location);"
```

### Verify Migration
```powershell
docker exec whac-postgres psql -U postgres -d whac_master -c "\d log_data"
docker exec whac-postgres psql -U postgres -d whac_master -c "\d log_action"
```

**Should show:** `device_id` and `sensor_location` columns in both tables.

---

## 🧪 Testing Deployment

### 1. Test Web UI
- ✅ Login successful
- ✅ Dashboard loads
- ✅ Charts render (Daily Scans, Access Status)
- ✅ User management works

### 2. Test Database Connection
```powershell
cd web_ui
python test_dashboard_stats.py
```

Expected output:
```
🧪 Testing Dashboard Stats API
1️⃣  Logging in...
   ✅ Login successful
2️⃣  Fetching dashboard stats...
   ✅ Stats fetched successfully
3️⃣  Checking database directly...
   ✅ Database check complete
```

### 3. Test MQTT Connection
- Check if Web UI can connect to MQTT broker
- See logs: `docker logs whac-web-ui | Select-String "MQTT"`

Expected:
```
✅ Web UI MQTT client connected successfully
✅ Web UI subscribed to topic: WHAC/Store001/in
```

### 4. Test Fingerprint Scan
1. Ensure Raspberry Pi is running
2. Scan fingerprint on sensor
3. Check Web UI dashboard:
   - ✅ Notification modal appears
   - ✅ Stats increment (Scans Today, Access Granted/Denied)
   - ✅ Logs show new entries

---

## 📊 Database Schema Reference

### Current Schema (After All Fixes)

**log_data table:**
```sql
id                 SERIAL PRIMARY KEY
user_id            INTEGER
store_id           VARCHAR(50) NOT NULL
timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
finger_template_id INTEGER
device_id          VARCHAR(50)           -- Multi-sensor support
sensor_location    VARCHAR(20)           -- masuk/keluar tracking
created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**log_action table:**
```sql
id             SERIAL PRIMARY KEY
user_id        INTEGER
store_id       VARCHAR(50) NOT NULL
username       VARCHAR(100)
timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
action         VARCHAR(50) NOT NULL
granted_denied VARCHAR(20) NOT NULL
device_id      VARCHAR(50)           -- Multi-sensor support
sensor_location VARCHAR(20)          -- masuk/keluar tracking
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Indexes:**
```sql
-- Performance indexes
idx_log_data_user_id
idx_log_data_store_id
idx_log_data_timestamp
idx_log_data_device_id
idx_log_data_sensor_location

idx_log_action_user_id
idx_log_action_store_id
idx_log_action_timestamp
idx_log_action_device_id
idx_log_action_sensor_location
```

---

## 🔧 Troubleshooting

### Issue 1: Docker Desktop Not Starting
**Solution:**
1. Check Windows virtualization enabled (Hyper-V / WSL2)
2. Restart Docker Desktop
3. Check Task Manager → Docker Desktop is running

### Issue 2: Port Already in Use
**Error:** `port 5000 is already allocated`

**Solution:**
```powershell
# Check what's using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
```

### Issue 3: Database Connection Failed
**Check:**
1. PostgreSQL container is running: `docker ps`
2. Database credentials in `.env` are correct
3. Network connectivity: `docker network ls`

**Reset database:**
```powershell
cd web_ui
docker-compose down -v  # ⚠️ This deletes all data!
docker-compose up -d
```

### Issue 4: Charts Not Showing
**Solution:**
1. Hard refresh browser: `Ctrl + F5`
2. Check browser console (F12) for errors
3. Verify Chart.js loaded: `typeof Chart` should return "function"

### Issue 5: Stats Not Updating
**Solution:**
1. Verify database schema has `device_id` and `sensor_location` columns
2. Check backend logs for errors: `docker logs whac-web-ui --tail=50`
3. Scan fingerprint and check if data enters database:
   ```powershell
   docker exec whac-postgres psql -U postgres -d whac_master -c "SELECT * FROM log_data WHERE DATE(timestamp) = CURRENT_DATE ORDER BY timestamp DESC LIMIT 5;"
   ```

---

## 🔐 Security Recommendations

### Production Deployment:

1. **Change Default Passwords:**
   ```sql
   -- Change admin password via Web UI
   -- Settings → Change Password
   ```

2. **Use Strong SECRET_KEY:**
   ```env
   SECRET_KEY=<long-random-string-here>
   ```

3. **Firewall Configuration:**
   ```powershell
   # Only allow necessary ports
   # 5000 - Web UI (restrict to local network)
   # 5432 - PostgreSQL (restrict to localhost only)
   # 1883 - MQTT (allow from Raspberry Pi IP only)
   ```

4. **Use HTTPS (Production):**
   - Deploy behind Nginx reverse proxy
   - Get SSL certificate (Let's Encrypt)
   - See: `PRODUCTION_DEPLOYMENT.md` (if available)

5. **Regular Backups:**
   ```powershell
   # Backup database
   docker exec whac-postgres pg_dump -U postgres whac_master > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
   ```

---

## 📝 Maintenance

### Regular Tasks:

**1. Check Logs (Weekly):**
```powershell
docker logs whac-web-ui --tail=100
docker logs whac-postgres --tail=100
```

**2. Backup Database (Weekly):**
```powershell
# Create backup
docker exec whac-postgres pg_dump -U postgres whac_master > backups/backup_$(Get-Date -Format "yyyyMMdd").sql

# Compress backup
Compress-Archive -Path backups/backup_*.sql -DestinationPath backups/archive_$(Get-Date -Format "yyyyMM").zip
```

**3. Clean Docker (Monthly):**
```powershell
# Remove unused images
docker image prune -a

# Remove unused volumes (⚠️ Be careful!)
docker volume prune
```

**4. Update Containers:**
```powershell
cd web_ui
docker-compose pull
docker-compose up -d --build
```

---

## 📚 Additional Resources

- **Multi-Sensor Setup:** `local_machine/MULTI_SENSOR_GUIDE.md`
- **Troubleshooting:** `TROUBLESHOOT_DASHBOARD_STATS.md`
- **Database Migration:** `web_ui/migrate_add_device_id.sql`
- **Testing:** `web_ui/test_dashboard_stats.py`

---

## ✅ Deployment Checklist

### Fresh Deployment:
- [ ] Docker Desktop installed and running
- [ ] Project files copied to new computer
- [ ] `.env` file configured
- [ ] `SECRET_KEY` changed from default
- [ ] Database password changed (if needed)
- [ ] Containers started: `docker-compose up -d`
- [ ] Web UI accessible at http://localhost:5000
- [ ] Default login works (admin/admin123)
- [ ] Admin password changed
- [ ] Raspberry Pi configured and connected
- [ ] Test fingerprint scan successful
- [ ] Dashboard stats updating correctly
- [ ] Charts rendering properly
- [ ] Backup schedule configured

### Existing Deployment Migration:
- [ ] Database backup created
- [ ] Migration script prepared
- [ ] Database schema checked
- [ ] Migration executed
- [ ] Schema verified (device_id + sensor_location present)
- [ ] Indexes created
- [ ] Containers restarted
- [ ] Test scan performed
- [ ] Stats updating correctly

---

## 🎯 Summary

### ✅ For Fresh Deployment (Komputer Baru):
**Semua konfigurasi SUDAH INCLUDE di `database_setup.sql`!**
- Cukup run `docker-compose up -d`
- Database akan ter-create dengan schema yang benar
- Tidak perlu migration manual!

### ⚠️ For Existing Deployment:
**Perlu run migration script jika database dibuat sebelum Nov 19, 2025:**
- Run `migrate_add_device_id.sql`
- Verify dengan `\d log_data` dan `\d log_action`
- Restart containers

### 🎉 Result:
- Multi-sensor support (AS608_001, AS608_002)
- Location tracking (masuk/keluar)
- Real-time dashboard updates
- Proper timezone (Asia/Jakarta)
- Visible charts and statistics

---

**Status:** ✅ **PRODUCTION READY!**  
**Last Updated:** November 19, 2025  
**Version:** V2 with Multi-Sensor Support




















