# 🔧 Fix: Database Schema Missing device_id Column

## 📋 Problem Description

Dashboard statistics (Scans Today, Access Granted, Access Denied) tidak ter-update meskipun fingerprint scan berhasil.

### Error Logs
```
ERROR: column "device_id" of relation "log_data" does not exist
ERROR: column "device_id" of relation "log_action" does not exist
```

## 🔍 Root Cause

Backend app.py sudah di-update untuk support multi-sensor system dengan `device_id` field, tapi database schema belum di-update. Database yang running dibuat sebelum `device_id` column ditambahkan ke `database_setup.sql`.

**Impact:**
- Scan data tidak masuk ke database
- Action logs (grant/deny) tidak tersimpan
- Dashboard stats selalu menunjukkan 0

## ✅ Solution Applied

### 1. Add device_id Column to Tables

**For log_data table:**
```sql
ALTER TABLE log_data 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001';
```

**For log_action table:**
```sql
ALTER TABLE log_action 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001';
```

### 2. Create Indexes for Performance

```sql
CREATE INDEX IF NOT EXISTS idx_log_data_device_id ON log_data(device_id);
CREATE INDEX IF NOT EXISTS idx_log_action_device_id ON log_action(device_id);
```

## 🚀 Deployment Instructions

### Option 1: Docker PostgreSQL (Recommended)

```bash
# Run migration script
docker exec whac-postgres psql -U postgres -d whac_master -f /docker-entrypoint-initdb.d/migrate_add_device_id.sql
```

Or execute commands directly:

```bash
# Add columns
docker exec whac-postgres psql -U postgres -d whac_master -c "ALTER TABLE log_data ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001';"

docker exec whac-postgres psql -U postgres -d whac_master -c "ALTER TABLE log_action ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001';"

# Create indexes
docker exec whac-postgres psql -U postgres -d whac_master -c "CREATE INDEX IF NOT EXISTS idx_log_data_device_id ON log_data(device_id);"

docker exec whac-postgres psql -U postgres -d whac_master -c "CREATE INDEX IF NOT EXISTS idx_log_action_device_id ON log_action(device_id);"
```

### Option 2: Local PostgreSQL

```bash
# Connect to database
psql -U postgres -d whac_master

# Run migration
\i web_ui/migrate_add_device_id.sql
```

Or use migration script:

```bash
psql -U postgres -d whac_master -f web_ui/migrate_add_device_id.sql
```

### Option 3: Using DBeaver or pgAdmin

1. Connect to your PostgreSQL database
2. Open SQL editor
3. Copy and paste contents from `web_ui/migrate_add_device_id.sql`
4. Execute

## ✅ Verification

### 1. Check Schema

**Verify columns exist:**
```bash
docker exec whac-postgres psql -U postgres -d whac_master -c "\d log_data"
docker exec whac-postgres psql -U postgres -d whac_master -c "\d log_action"
```

**Expected output:** Both tables should show `device_id VARCHAR(50)` column.

### 2. Test Scan

1. **Scan fingerprint** on sensor
2. **Check backend logs** (should be NO errors):
   ```bash
   docker logs whac-web-ui --tail=50
   ```
3. **Verify data in database:**
   ```bash
   docker exec whac-postgres psql -U postgres -d whac_master -c "SELECT * FROM log_data WHERE DATE(timestamp) = CURRENT_DATE ORDER BY timestamp DESC LIMIT 5;"
   ```

### 3. Check Dashboard

1. **Refresh browser** (Ctrl + F5)
2. **Check stats cards:**
   - ✅ Scans Today: Should increment
   - ✅ Access Granted: Should increment after grant
   - ✅ Access Denied: Should increment after deny

## 📊 Expected Behavior After Fix

### Before Fix:
```
ERROR: column "device_id" of relation "log_data" does not exist
❌ Scans Today: 0 (even after scanning)
❌ Access Granted: 0 (even after granting)
❌ Database: No new records in log_data/log_action
```

### After Fix:
```
✅ Scan notification received
✅ Data inserted to log_data with device_id='AS608_002'
✅ Action logged to log_action with device_id='AS608_002'
✅ Scans Today: 1 (incremented)
✅ Access Granted: 1 (incremented)
```

## 🐛 Troubleshooting

### Issue 1: Migration Already Applied
**Symptom:** `ALTER TABLE` returns immediately without error

**Solution:** This is normal! `IF NOT EXISTS` clause prevents duplicate columns. Verify with `\d log_data`.

### Issue 2: Permission Denied
**Symptom:** `ERROR: permission denied for table log_data`

**Solution:** Run as postgres superuser:
```bash
docker exec -u postgres whac-postgres psql -d whac_master -c "ALTER TABLE log_data ADD COLUMN IF NOT EXISTS device_id VARCHAR(50);"
```

### Issue 3: Stats Still Not Updating
**Check:**
1. ✅ Columns added to database
2. ✅ Web UI container restarted (optional, but recommended)
3. ✅ MQTT broker connection working
4. ✅ Local machine sending scans

**Debug:**
```bash
# Check recent logs
docker logs whac-web-ui --tail=100 | grep -i "error\|device_id"

# Check database data
docker exec whac-postgres psql -U postgres -d whac_master -c "SELECT COUNT(*) FROM log_data WHERE DATE(timestamp) = CURRENT_DATE;"
```

## 📝 Files Modified/Created

1. ✅ **Database (live):** 
   - Added `device_id` column to `log_data` table
   - Added `device_id` column to `log_action` table
   - Created indexes on `device_id` columns

2. ✅ **web_ui/migrate_add_device_id.sql** (NEW):
   - Migration script for future deployments

3. ℹ️ **web_ui/database_setup.sql** (Already correct):
   - Already contains `device_id` columns
   - No changes needed

## 🔄 For Future Deployments

New deployments using `database_setup.sql` will automatically have `device_id` columns. This migration is only needed for **existing databases** created before Nov 19, 2025.

### When to Apply This Migration:
- ✅ Existing production databases
- ✅ Existing development databases
- ❌ New deployments (already in database_setup.sql)

## 📚 Related Issues

- **Issue:** Dashboard stats not updating
- **Related Fix:** Timezone fix (Asia/Jakarta) in `web_ui/app.py`
- **Multi-sensor Support:** `device_id` tracks which sensor (AS608_001, AS608_002) generated each log

## 🎯 Summary

**Problem:** Database schema missing `device_id` column for multi-sensor support.

**Solution:** Add `device_id VARCHAR(50)` column to `log_data` and `log_action` tables.

**Status:** ✅ FIXED - Data now properly logged to database with device identification.

---

**Date Fixed:** November 19, 2025  
**Applied To:** whac_master database  
**Compatible With:** All versions after multi-sensor support implementation




















