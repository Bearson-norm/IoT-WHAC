# Quick Start: Fix Attendance Merging

## 🚀 3-Step Quick Fix

### Step 1: Run Fix Script (2 minutes)

```bash
cd web_ui
psql -U postgres -d whac_master -f fix_attendance_linking.sql
```

**Expected Output:**
```
ALTER TABLE
ALTER TABLE
ALTER TABLE
UPDATE 0
DROP VIEW
CREATE VIEW
CREATE INDEX
                       result                        
----------------------------------------------------
 Attendance linking fixed! Records with same full_name are now merged.
```

### Step 2: Restart Web UI (30 seconds)

```bash
# Option A: Systemd
sudo systemctl restart whac-web-ui

# Option B: Manual
# Ctrl+C to stop, then:
python3 app.py

# Option C: Docker
docker-compose restart web-ui
```

### Step 3: Test (2 minutes)

```bash
# Install dependency (if needed)
pip install paho-mqtt

# Run test
python3 simulate_scan.py
```

Select option **1** (Linked User Test), then:
1. Grant access for first scan (Sensor 1)
2. Grant access for second scan (Sensor 2)
3. Check attendance table

**Expected Result:**
```
✅ 1 row with both User ID In and User ID Out filled
✅ Clock In = earliest timestamp
✅ Clock Out = latest timestamp
```

---

## 📊 Before & After

### Before (Broken):
```
Date        | Full Name  | User ID In | User ID Out | Clock In  | Clock Out
------------|------------|------------|-------------|-----------|----------
2026-01-02  | Hilal A Q  | 1          | -           | 11:57:59  | -
2026-01-02  | Hilal A Q  | -          | 2           | -         | 11:59:01
```
❌ **2 rows** for same person!

### After (Fixed):
```
Date        | Full Name  | User ID In | User ID Out | Clock In  | Clock Out
------------|------------|------------|-------------|-----------|----------
2026-01-02  | Hilal A Q  | 1          | 2           | 11:57:59  | 11:59:01
```
✅ **1 row** merged correctly!

---

## 🧪 Quick Test Commands

### Verify Fix Applied:

```sql
-- Check constraint exists
\d attendance

-- Should show: attendance_full_name_date_key UNIQUE (full_name, attendance_date)
```

### Test Merge:

```bash
# Run simulator
python3 web_ui/simulate_scan.py

# Choose option 1
# Grant access for both scans in Web UI
```

### Check Result:

```sql
SELECT 
    full_name,
    user_id_in,
    user_id_out,
    clock_in,
    clock_out
FROM attendance
WHERE attendance_date = CURRENT_DATE;
```

---

## ⚠️ Troubleshooting

### "psql: command not found"
```bash
# Install PostgreSQL client
sudo apt-get install postgresql-client
```

### "Connection refused"
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if needed
sudo systemctl start postgresql
```

### "Permission denied"
```bash
# Use sudo
sudo -u postgres psql -d whac_master -f fix_attendance_linking.sql
```

### Attendance still showing 2 rows
```bash
# Hard refresh browser
Ctrl + F5 (Windows/Linux)
Cmd + Shift + R (Mac)

# Or clear browser cache
```

---

## 📱 Mobile Quick Steps

### For Windows:

```cmd
cd C:\path\to\IoT-WHAC\V2\web_ui
psql -U postgres -d whac_master -f fix_attendance_linking.sql
python app.py
python simulate_scan.py
```

### For Linux/Mac:

```bash
cd ~/IoT-WHAC/V2/web_ui
psql -U postgres -d whac_master -f fix_attendance_linking.sql
python3 app.py
python3 simulate_scan.py
```

### For Docker:

```bash
# Copy script to container
docker cp fix_attendance_linking.sql whac-postgres:/tmp/

# Run in container
docker exec -it whac-postgres psql -U postgres -d whac_master -f /tmp/fix_attendance_linking.sql

# Restart web UI
docker-compose restart web-ui

# Run simulator on host
python3 simulate_scan.py
```

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ SQL script runs without errors
2. ✅ Web UI restarts successfully
3. ✅ Simulator publishes scans
4. ✅ Attendance shows **1 row per person per day**
5. ✅ Clock In = earliest time, Clock Out = latest time
6. ✅ Both User ID In and User ID Out are filled

---

## 🎯 What Changed?

| Component | Before | After |
|-----------|--------|-------|
| Unique Key | `(user_id, date)` | `(full_name, date)` |
| Record Count | 2 rows per person | 1 row per person |
| Matching By | user_id | full_name |
| Clock In | From sensor record | Earliest timestamp |
| Clock Out | From sensor record | Latest timestamp |

---

## 📞 Need Help?

- 📖 Full docs: `FIX_ATTENDANCE_MERGING.md`
- 🔧 Feature docs: `FITUR_FULL_NAME_LINKING.md`
- 🐳 Docker guide: `DOCKER_SETUP_GUIDE.md`
- 💾 Installation: `INSTALASI_FITUR_FULL_NAME.md`

---

**Last Updated:** 2025-01-02  
**Version:** 1.0  
**Estimated Time:** 5 minutes total







