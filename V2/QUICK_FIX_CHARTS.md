# ⚡ Quick Fix: Grafik Tidak Muncul di Dashboard

## 🐛 Masalah
Grafik dan statistik tidak muncul di dashboard Web UI.

## ✅ Sudah Diperbaiki!
Fix sudah diimplementasikan di `web_ui/app.py`

---

## 🚀 Cara Deploy Fix

### Docker (Recommended):
```bash
cd web_ui
docker-compose restart web-ui
docker-compose logs -f web-ui
```

### Manual:
```bash
cd web_ui
# Stop old process
pkill -f "python.*app.py"

# Start new process
python3 app.py
# atau
gunicorn --bind 0.0.0.0:5000 app:app
```

---

## 🧪 Test Apakah Sudah Bekerja

### 1. Login ke Web UI
- Buka: `http://your-vps-ip:5000`
- Login dengan admin credentials

### 2. Check Dashboard
Harus muncul 2 grafik:
- ✅ **Daily Scans** (Line chart - 7 hari)
- ✅ **Access Status** (Doughnut chart - Granted/Denied)

### 3. Check Browser Console (F12)
Tidak boleh ada error seperti:
- ❌ `TypeError: Cannot read property 'date'`
- ❌ `500 Internal Server Error`
- ❌ `Failed to load resource`

### 4. Check Backend Logs
```bash
# Docker
docker logs whac-web-ui | grep "daily stats"

# Output yang benar:
INFO - Fetching daily stats for last 7 days
INFO - Found X days of scan data
```

---

## 🔍 Troubleshooting

### Grafik Masih Kosong?
```bash
# Check apakah ada data di database
docker exec whac-postgres psql -U postgres -d whac_master -c "
SELECT COUNT(*) FROM log_data 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
"
```

Jika hasil = 0, berarti belum ada data scan. Coba:
1. Scan fingerprint di sensor
2. Refresh dashboard
3. Grafik akan muncul

### Error 500 di Console?
```bash
# Check detailed error logs
docker logs whac-web-ui --tail 100
```

### Redirect ke Login terus?
```bash
# Clear cookies dan login ulang
# Atau check session:
docker logs whac-web-ui | grep "login"
```

---

## 🎯 What Was Fixed

1. ✅ SQL INTERVAL syntax error
2. ✅ Date serialization to JSON
3. ✅ Login protection restored
4. ✅ Enhanced logging

---

**Status:** ✅ FIXED
**Dokumentasi:** `web_ui/FIX_CHARTS_STATISTICS.md`




















