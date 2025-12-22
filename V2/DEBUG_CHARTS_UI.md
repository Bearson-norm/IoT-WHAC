# 🔍 Debug: Grafik Tidak Muncul di UI

## 🎯 Langkah-Langkah Debug

Saya sudah menambahkan **enhanced logging** di frontend. Ikuti langkah ini:

### Langkah 1: Restart Web UI Docker

```bash
cd web_ui
docker-compose restart web-ui
```

### Langkah 2: Buka Web UI dan Login

```
http://your-vps-ip:5000
```

Login dengan credentials admin Anda.

### Langkah 3: Buka Browser Console

**Tekan F12** atau klik kanan → **Inspect** → Tab **Console**

### Langkah 4: Refresh Page (F5)

Anda akan melihat **detailed logs** seperti ini:

#### ✅ **Jika Berhasil:**
```javascript
📊 Loading charts...
✅ Chart.js is loaded
📡 Response status: 200
📦 Chart data received: {daily_scans: Array(1), daily_access: Array(0)}
  - Daily scans: 1 days
  - Daily access: 0 records
⚠️ No daily_access data available
  Date item: 2025-11-18
  Scan count: 7
📈 Creating daily scans chart...
✅ Daily scans chart created
📊 Access stats - Granted: 0 Denied: 0
📉 Creating access status chart...
✅ Access status chart created
🎉 All charts loaded successfully!
```

#### ❌ **Jika Ada Error:**

**Error 1: Chart.js Not Loaded**
```javascript
❌ Chart.js is not loaded!
```
**Solusi:** Check internet connection atau CDN blocked.

**Error 2: API Error**
```javascript
📡 Response status: 401
❌ API error: 401 Unauthorized
```
**Solusi:** Login dulu atau check session expired.

**Error 3: Canvas Not Found**
```javascript
❌ dailyScansChart canvas not found!
```
**Solusi:** HTML template issue.

**Error 4: Empty Data**
```javascript
⚠️ No daily_scans data available
⚠️ No daily_access data available
```
**Solusi:** Belum ada data di database.

---

## 🧪 Test Endpoint Manual

### Test 1: Check API Response

```bash
# Login dan save cookie
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -c cookies.txt

# Test endpoint
curl http://localhost:5000/api/charts/daily_stats?days=7 \
  -b cookies.txt \
  -v
```

**Expected Response:**
```json
{
  "daily_scans": [
    {"date": "2025-11-18", "scan_count": 7}
  ],
  "daily_access": []
}
```

### Test 2: Check Backend Logs

```bash
# Docker
docker logs whac-web-ui --tail 50 | grep "daily stats"

# Expected output:
INFO - Fetching daily stats for last 7 days
INFO - Found 1 days of scan data
INFO - Found 0 days of access data
```

---

## 🔧 Common Issues & Solutions

### Issue 1: Response 401 Unauthorized

**Symptoms:**
- Browser console: `Response status: 401`
- Redirect to login page

**Cause:**
- Session expired
- Not logged in

**Solution:**
```bash
# Clear cookies
# Login again
# Refresh page (F5)
```

### Issue 2: Chart.js Not Loading

**Symptoms:**
- Console: `Chart.js is not loaded!`
- Charts area empty

**Cause:**
- CDN blocked
- Internet connection issue
- Adblocker

**Solution:**
```html
<!-- Check if this line exists in HTML head -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- Or download Chart.js locally -->
```

**Test CDN:**
```bash
curl -I https://cdn.jsdelivr.net/npm/chart.js
# Should return 200 OK
```

### Issue 3: Canvas Element Not Found

**Symptoms:**
- Console: `dailyScansChart canvas not found!`

**Cause:**
- HTML template missing canvas element

**Solution:**
Check HTML has:
```html
<canvas id="dailyScansChart"></canvas>
<canvas id="accessStatusChart"></canvas>
```

### Issue 4: Data Empty But No Error

**Symptoms:**
- Console: `No daily_scans data available`
- Empty charts

**Cause:**
- No data in database for last 7 days

**Check Database:**
```bash
docker exec whac-postgres psql -U postgres -d whac_master -c "
SELECT DATE(timestamp) as date, COUNT(*) 
FROM log_data 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date;
"
```

**If empty (0 rows):**
1. Belum ada fingerprint scans
2. Data sudah lebih dari 7 hari
3. Table `log_data` kosong

**Solution:**
- Scan beberapa fingerprint
- Atau ubah days parameter: `/api/charts/daily_stats?days=30`

---

## 📊 Expected Console Output

### Skenario 1: Ada Data Scans, Tidak Ada Access Logs

```
📊 Loading charts...
✅ Chart.js is loaded
📡 Response status: 200
📦 Chart data received: {daily_scans: Array(1), daily_access: Array(0)}
  - Daily scans: 1 days
  - Daily access: 0 records
⚠️ No daily_access data available  ← NORMAL jika belum ada grant/deny action
  Date item: 2025-11-18
  Scan count: 7
📈 Creating daily scans chart...
✅ Daily scans chart created
📊 Access stats - Granted: 0 Denied: 0
📉 Creating access status chart...
✅ Access status chart created  ← Chart tetap dibuat (empty doughnut)
🎉 All charts loaded successfully!
```

**Result:**
- ✅ Line chart muncul dengan 1 data point (7 scans)
- ✅ Doughnut chart muncul kosong (no data)

### Skenario 2: Ada Data Lengkap

```
📊 Loading charts...
✅ Chart.js is loaded
📡 Response status: 200
📦 Chart data received: {daily_scans: Array(3), daily_access: Array(4)}
  - Daily scans: 3 days
  - Daily access: 4 records
  Date item: 2025-11-18
  Scan count: 7
  Date item: 2025-11-19
  Scan count: 12
  Date item: 2025-11-20
  Scan count: 8
📈 Creating daily scans chart...
✅ Daily scans chart created
📊 Access stats - Granted: 15 Denied: 3
📉 Creating access status chart...
✅ Access status chart created
🎉 All charts loaded successfully!
```

**Result:**
- ✅ Line chart dengan 3 data points
- ✅ Doughnut chart: 15 granted, 3 denied

---

## 🎯 Action Plan

### Ikuti Urutan Ini:

1. **Restart Web UI**
   ```bash
   cd web_ui
   docker-compose restart web-ui
   ```

2. **Open Browser Console (F12)**

3. **Login ke Web UI**

4. **Check Console Logs**
   - Copy semua log yang muncul
   - Kirim ke saya jika ada error

5. **Check Network Tab (F12 → Network)**
   - Look for `/api/charts/daily_stats` request
   - Check Status Code (should be 200)
   - Check Response data

6. **Report Results**
   Share:
   - Console logs
   - Network tab response
   - Backend logs: `docker logs whac-web-ui --tail 50`

---

## 📸 Screenshot Guide

Ambil screenshot ini untuk debugging:

1. **Browser Console** (F12 → Console)
2. **Network Tab** (F12 → Network → filter: `daily_stats`)
3. **Elements Tab** (F12 → Elements → search: `canvas`)
4. **Dashboard view** (full page)

---

## 🚨 Emergency Check

Jika masih tidak muncul, jalankan ini di **Browser Console:**

```javascript
// Check Chart.js
console.log('Chart.js loaded?', typeof Chart !== 'undefined');

// Check canvas elements
console.log('Daily scans canvas?', document.getElementById('dailyScansChart') !== null);
console.log('Access status canvas?', document.getElementById('accessStatusChart') !== null);

// Manual fetch
fetch('/api/charts/daily_stats?days=7')
  .then(r => r.json())
  .then(d => console.log('API Data:', d))
  .catch(e => console.error('API Error:', e));
```

Copy output dan kirim ke saya!

---

**Status:** ✅ Enhanced debugging implemented
**Next:** Share console logs untuk analysis lebih lanjut




















