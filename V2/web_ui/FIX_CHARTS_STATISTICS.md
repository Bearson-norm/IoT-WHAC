# 🔧 Fix: Grafik dan Statistik Tidak Muncul di Web UI

## 🐛 Masalah

Dashboard Web UI tidak menampilkan:
- ❌ Grafik Daily Scans (7 hari terakhir)
- ❌ Grafik Access Status (Granted/Denied)
- ❌ Statistik harian

## 🔍 Root Cause

Endpoint `/api/charts/daily_stats` memiliki 3 masalah:

### 1. **SQL INTERVAL Syntax Error** ❌
```python
# SALAH - Parameter %s di dalam string INTERVAL
WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'

# BENAR - Multiply INTERVAL dengan parameter
WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day' * %s
```

PostgreSQL tidak bisa melakukan string interpolation di dalam INTERVAL literal. Harus menggunakan operasi matematika.

### 2. **Date Serialization Error** ❌
```python
# SALAH - Date objects tidak bisa di-serialize ke JSON
return jsonify({
    'daily_scans': [dict(row) for row in daily_scans]  # date object error
})

# BENAR - Convert date to ISO string
for row in daily_scans:
    row_dict = dict(row)
    if row_dict.get('date'):
        row_dict['date'] = row_dict['date'].isoformat()  # Convert to string
```

PostgreSQL mengembalikan `date` objects yang tidak bisa langsung di-convert ke JSON. Harus dikonversi ke string terlebih dahulu.

### 3. **Missing Login Protection** ⚠️
```python
# SALAH - Endpoint tanpa proteksi
@app.route('/api/charts/daily_stats')
def daily_stats_chart():
    ...

# BENAR - Dengan login protection
@app.route('/api/charts/daily_stats')
@login_required
def daily_stats_chart():
    ...
```

## ✅ Solusi

Sudah diperbaiki di `web_ui/app.py` line 1852-1916:

1. ✅ SQL INTERVAL syntax menggunakan `INTERVAL '1 day' * %s`
2. ✅ Date serialization dengan `.isoformat()`
3. ✅ Login protection dengan `@login_required` decorator
4. ✅ Enhanced logging untuk debugging

## 🚀 Deployment

### Docker:
```bash
cd web_ui
docker-compose restart web-ui
docker-compose logs -f web-ui
```

### Manual:
```bash
cd web_ui
# Restart Flask app
pkill -f "python.*app.py"
python3 app.py
```

## 🧪 Testing

### 1. Test Endpoint Langsung

```bash
# Login dulu untuk get session cookie
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -c cookies.txt

# Test daily stats endpoint
curl http://localhost:5000/api/charts/daily_stats?days=7 \
  -b cookies.txt
```

Expected response:
```json
{
  "daily_scans": [
    {"date": "2025-11-19", "scan_count": 15},
    {"date": "2025-11-20", "scan_count": 23}
  ],
  "daily_access": [
    {"date": "2025-11-19", "granted_denied": "granted", "count": 10},
    {"date": "2025-11-19", "granted_denied": "denied", "count": 5}
  ]
}
```

### 2. Test di Web UI

1. Login ke Web UI
2. Dashboard akan auto-load grafik
3. Cek grafik:
   - **Daily Scans Chart** (Line chart)
   - **Access Status Chart** (Doughnut chart)

### 3. Check Browser Console

Buka Developer Tools (F12) → Console tab:

```javascript
// Harus tidak ada error
// Harus ada log seperti:
// "Charts loaded successfully"
```

### 4. Check Backend Logs

```bash
# Docker
docker logs whac-web-ui | grep "daily stats"

# Manual
tail -f logs/app.log | grep "daily stats"
```

Expected logs:
```
INFO - Fetching daily stats for last 7 days
INFO - Found 7 days of scan data
INFO - Found 14 days of access data
```

## 🔍 Troubleshooting

### Q: Grafik masih tidak muncul?
**A:** Check browser console untuk error:
```javascript
// F12 → Console
// Lihat error apa yang muncul
```

### Q: Error "Database connection failed"?
**A:** Check PostgreSQL connection:
```bash
# Test connection
docker exec whac-postgres psql -U postgres -d whac_master -c "SELECT NOW()"
```

### Q: Error "Unauthorized" / redirect ke login?
**A:** Clear browser cache/cookies dan login ulang

### Q: Data kosong tapi no error?
**A:** Mungkin belum ada data. Cek database:
```sql
-- Check if there's data
SELECT DATE(timestamp) as date, COUNT(*) 
FROM log_data 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp);
```

### Q: Error SQL syntax?
**A:** Check PostgreSQL version:
```bash
docker exec whac-postgres psql -U postgres -c "SELECT version()"
```

Pastikan menggunakan PostgreSQL 9.0+

## 📊 Chart Types

### 1. Daily Scans Chart (Line Chart)
- X-axis: Tanggal (7 hari terakhir)
- Y-axis: Jumlah scan
- Data dari: `log_data` table

### 2. Access Status Chart (Doughnut Chart)
- Segments: Granted vs Denied
- Data dari: `log_action` table
- Aggregate 7 hari terakhir

## 🔐 Security Note

Endpoint ini **HARUS** dilindungi dengan `@login_required` karena:
- Mengakses data sensitive (user activity)
- Bisa digunakan untuk reconnaissance
- Expose pattern aktivitas sistem

## 📝 Related Files

- `web_ui/app.py` - Line 1852-1916 (Backend endpoint)
- `web_ui/templates/index.html` - Line 1191-1240 (Frontend chart rendering)
- `web_ui/static/js/chart.js` - Chart.js library

## ✅ Status

**FIXED** ✅

Grafik dan statistik sekarang berfungsi dengan baik!

---

**Date:** 2025-11-19
**Impact:** High - Dashboard visualization
**Tested:** ✅ Yes




















