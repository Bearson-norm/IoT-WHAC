# 🔧 Troubleshooting Dashboard Stats Not Updating

## 📋 Problem Description
Dashboard statistics (Total Users, Scans Today, Access Granted, Access Denied) tidak ter-update meskipun sudah ada scan dan grant/deny access.

## 🔍 Step-by-Step Diagnosis

### 1️⃣ Check Browser Console
**Buka browser console** (F12 → Console tab) dan refresh halaman.

**Expected logs:**
```
📊 Loading dashboard stats...
📦 Stats data: {total_users: X, total_scans_today: Y, ...}
✅ Dashboard stats updated
```

**If you see:**
```
❌ Stats API error: 401 Unauthorized
```
→ **Solution:** Login ulang ke Web UI

**If you see:**
```
❌ Stats API error: 500
```
→ **Solution:** Check backend logs untuk error detail

**If you see NO logs at all:**
→ **Solution:** Function `loadDashboardStats()` tidak dipanggil, cek script errors

### 2️⃣ Check Backend Logs
Monitor log dari Web UI server:

**For Docker:**
```bash
cd web_ui
docker-compose logs -f web_ui
```

**For Direct Python:**
```bash
cd web_ui
# Check console output
```

**Expected logs when dashboard loads:**
```
INFO - 📊 Dashboard stats requested
INFO -   Total users: 2
INFO -   Checking data for date: 2025-11-19
INFO -   Scans today: 5
INFO -   Access granted today: 3
INFO -   Access denied today: 2
INFO - ✅ Dashboard stats returned: {...}
```

**If you see:**
```
ERROR - ❌ Database connection failed for dashboard stats
```
→ **Solution:** Check database connection settings

**If you see:**
```
ERROR - ❌ Error getting dashboard stats: ...
```
→ **Solution:** Check error detail dan database schema

### 3️⃣ Test API Directly
Run test script untuk test API endpoint:

```bash
cd web_ui
python test_dashboard_stats.py
```

Script ini akan:
- ✅ Test login
- ✅ Fetch dashboard stats via API
- ✅ Query database langsung untuk verify data
- ✅ Show sample data dari log_data dan log_action

**Expected output:**
```
🧪 Testing Dashboard Stats API
1️⃣  Logging in...
   ✅ Login successful
2️⃣  Fetching dashboard stats...
   Status Code: 200
   📊 Dashboard Stats:
      Total Users: 2
      Scans Today: 5
      Access Granted: 3
      Access Denied: 2
   ✅ Stats fetched successfully
3️⃣  Checking database directly...
   Total users in DB: 2
   Scans today in DB: 5
   ✅ Database check complete
```

### 4️⃣ Check Database Data
Verify data memang ada di database:

**Connect to database:**
```bash
# For Docker
docker exec -it web_ui_postgres psql -U postgres -d fingerprint_db

# For local PostgreSQL
psql -U postgres -d fingerprint_db
```

**Run queries:**
```sql
-- Check total users
SELECT COUNT(*) FROM store_001;

-- Check today's scans
SELECT COUNT(*) FROM log_data WHERE DATE(timestamp) = CURRENT_DATE;

-- Check today's access (granted)
SELECT COUNT(*) FROM log_action 
WHERE DATE(timestamp) = CURRENT_DATE AND granted_denied = 'granted';

-- Check today's access (denied)
SELECT COUNT(*) FROM log_action 
WHERE DATE(timestamp) = CURRENT_DATE AND granted_denied = 'denied';

-- Show recent log_data
SELECT * FROM log_data ORDER BY timestamp DESC LIMIT 10;

-- Show recent log_action
SELECT * FROM log_action ORDER BY timestamp DESC LIMIT 10;
```

### 5️⃣ Check HTML Elements
Verify element IDs ada di HTML:

**In browser console:**
```javascript
// Check if elements exist
console.log('Total Users:', document.getElementById('total-users'));
console.log('Scans Today:', document.getElementById('total-scans-today'));
console.log('Granted:', document.getElementById('successful-access-today'));
console.log('Denied:', document.getElementById('denied-access-today'));

// Should all return <h4> elements, not null
```

**If returns `null`:**
→ **Solution:** Element ID salah atau tidak ada di HTML

### 6️⃣ Manual Update Test
Test update element secara manual:

**In browser console:**
```javascript
// Try manual update
document.getElementById('total-users').textContent = '999';
document.getElementById('total-scans-today').textContent = '888';
document.getElementById('successful-access-today').textContent = '777';
document.getElementById('denied-access-today').textContent = '666';
```

**If numbers appear:**
→ Element IDs benar, problem ada di API call atau data response

**If numbers don't appear:**
→ CSS issue atau element tidak visible

## 🐛 Common Issues & Solutions

### Issue 1: Stats Show "0" but Data Exists
**Cause:** Date/timezone mismatch antara backend dan database

**Solution:**
```python
# In app.py, check timezone
from datetime import datetime
import pytz

# Use local timezone
tz = pytz.timezone('Asia/Jakarta')  # Adjust to your timezone
today = datetime.now(tz).date()
```

### Issue 2: Stats Don't Update After New Scan
**Cause:** Auto-refresh interval belum sampai (30 detik)

**Solution:**
- Wait 30 detik untuk auto-refresh
- Or manual refresh page (F5)
- Or call `loadDashboardStats()` di console

### Issue 3: Stats Show "-" (Not Updated)
**Cause:** API call failed atau tidak dipanggil

**Check:**
1. Browser console untuk errors
2. Backend logs untuk API errors
3. Network tab (F12) untuk API response

### Issue 4: Login Required Error
**Cause:** Session expired atau not logged in

**Solution:**
1. Login ulang
2. Check `@login_required` decorator ada di endpoint
3. Check session cookie di browser

## 🔄 Complete Reset Flow

If semua troubleshooting gagal, lakukan complete reset:

### 1. Stop Services
```bash
# Docker
cd web_ui
docker-compose down

# Local service
sudo systemctl stop fingerprint-web
```

### 2. Clear Browser Cache
```
Ctrl + Shift + Delete → Clear cache and cookies
```

### 3. Restart Database (if needed)
```bash
# Docker
docker-compose restart postgres

# Local
sudo systemctl restart postgresql
```

### 4. Start Services
```bash
# Docker
docker-compose up -d

# Local
sudo systemctl start fingerprint-web
```

### 5. Test Again
```bash
python test_dashboard_stats.py
```

## 📊 Debugging Checklist

Use this checklist untuk systematic debugging:

- [ ] Browser console shows `loadDashboardStats()` being called
- [ ] Browser console shows API response received (status 200)
- [ ] Browser console shows data object with correct values
- [ ] Backend logs show "Dashboard stats requested"
- [ ] Backend logs show correct counts for each stat
- [ ] Backend logs show "Dashboard stats returned"
- [ ] Database has actual data in `log_data` and `log_action` tables
- [ ] Database timestamps are today's date
- [ ] HTML elements with correct IDs exist in DOM
- [ ] CSS doesn't hide the stat cards
- [ ] No JavaScript errors in console
- [ ] Network tab shows successful API call (200 OK)

## 🆘 Still Not Working?

If masalah masih persist after all steps:

1. **Export logs:**
   ```bash
   # Backend logs
   docker-compose logs web_ui > web_ui_logs.txt
   
   # Browser console
   # Copy all console output
   ```

2. **Export database data:**
   ```bash
   docker exec -it web_ui_postgres psql -U postgres -d fingerprint_db \
     -c "SELECT COUNT(*) FROM log_data WHERE DATE(timestamp) = CURRENT_DATE" \
     -c "SELECT COUNT(*) FROM log_action WHERE DATE(timestamp) = CURRENT_DATE"
   ```

3. **Take screenshots:**
   - Browser console (F12)
   - Network tab showing API response
   - Dashboard showing stats cards

4. **Report issue with:**
   - Logs export
   - Database export
   - Screenshots
   - Steps you've tried

## 🎯 Quick Test Commands

**Test everything in one go:**
```bash
# 1. Check if web UI is running
curl http://localhost:5000

# 2. Test dashboard stats API (after login)
python web_ui/test_dashboard_stats.py

# 3. Check backend logs
docker-compose logs --tail=50 web_ui

# 4. Check database
docker exec -it web_ui_postgres psql -U postgres -d fingerprint_db \
  -c "SELECT COUNT(*) as total_users FROM store_001;" \
  -c "SELECT COUNT(*) as scans_today FROM log_data WHERE DATE(timestamp) = CURRENT_DATE;" \
  -c "SELECT COUNT(*) as granted FROM log_action WHERE DATE(timestamp) = CURRENT_DATE AND granted_denied = 'granted';" \
  -c "SELECT COUNT(*) as denied FROM log_action WHERE DATE(timestamp) = CURRENT_DATE AND granted_denied = 'denied';"
```

---

**Remember:** The issue is likely either:
1. 🔴 API not being called (frontend issue)
2. 🟡 API failing (backend issue)
3. 🔵 Data not in database (data pipeline issue)

Use systematic approach untuk identify which one! 🎯




















