# 🔧 Fix: Full Name Tidak Tersimpan Saat Enrollment

## 🐛 Masalah

Saat pertama kali setup (database kosong, sensor kosong):
1. ✅ User enroll di sensor masuk (in) - form muncul, input nama lengkap "Hilal Akbar Quddus Ramadhan"
2. ❌ **Tidak muncul di attendance** - full_name tidak tersimpan
3. ❌ **Saat scan di sensor keluar (out), nama lengkap tidak muncul di dropdown** - full_name tidak tersimpan di database

## 🔍 Root Cause

1. **Frontend tidak mengirim full_name** saat enrollment untuk unverified scan
   - Di `enrollNewUser()`, saat `isUnverifiedScan = true`, full_name tidak dikirim ke `/api/enroll_user`

2. **Backend tidak menyimpan full_name** saat enrollment response diterima
   - Di `handle_enrollment_response()`, full_name tidak disimpan ke database
   - Hanya `user_name` dan `fingerprint_id` yang disimpan

3. **Attendance tracking skip** jika full_name tidak ada
   - Di `log_access_to_database()`, ada check: jika `full_name` NULL, attendance tracking di-skip

## ✅ Solusi

### 1. Frontend: Kirim full_name ke Backend

**File:** `web_ui/templates/index.html`

**Perubahan:**
```javascript
// SEBELUM (SALAH):
body: JSON.stringify({
    user_id: userIdInt,
    username: nama,
    target_sensor: deviceId
})

// SESUDAH (BENAR):
body: JSON.stringify({
    user_id: userIdInt,
    username: nama,
    full_name: fullName,  // ← TAMBAHAN!
    posisi: posisi,        // ← TAMBAHAN!
    target_sensor: deviceId
})
```

### 2. Backend: Simpan full_name ke Enrollment Manager

**File:** `web_ui/app.py` - `enroll_user()`

**Perubahan:**
```python
# Get full_name and posisi from request
full_name = data.get('full_name', '')
posisi = data.get('posisi', '')

# Store in enrollment data
if enrollment_id:
    enrollment_manager.enrollments[enrollment_id]['full_name'] = full_name
    enrollment_manager.enrollments[enrollment_id]['posisi'] = posisi

# Include in enrollment command
enrollment_command = {
    'fingerprint_id': int(user_id),
    'user_name': str(username),
    'full_name': full_name,  # ← TAMBAHAN!
    'posisi': posisi,        # ← TAMBAHAN!
    ...
}
```

### 3. Backend: Simpan full_name ke Database

**File:** `web_ui/app.py` - `handle_enrollment_response()`

**Perubahan:**
```python
# Get full_name from enrollment data or payload
full_name = None
posisi = ''
if enrollment_id and active_enrollment:
    full_name = active_enrollment.get('full_name') or data.get('full_name')
    posisi = active_enrollment.get('posisi') or data.get('posisi', '')
else:
    full_name = data.get('full_name')
    posisi = data.get('posisi', '')

# Insert with full_name
cursor.execute(f"""
    INSERT INTO {table_name} (user_id, username, full_name, finger_template_id)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (user_id) DO UPDATE SET
        username = EXCLUDED.username,
        full_name = COALESCE(EXCLUDED.full_name, {table_name}.full_name),
        finger_template_id = EXCLUDED.finger_template_id,
        updated_at = CURRENT_TIMESTAMP
""", (fingerprint_id, user_name, full_name, fingerprint_id))
```

## 🔄 Flow Setelah Fix

```
1. User scan di sensor masuk (unverified)
   ↓
2. Modal muncul, user isi form:
   - User ID: 1
   - Nama: Hilal
   - Full Name: Hilal Akbar Quddus Ramadhan
   ↓
3. Frontend kirim ke /api/enroll_user:
   {
     user_id: 1,
     username: "Hilal",
     full_name: "Hilal Akbar Quddus Ramadhan",  ← DIKIRIM!
     posisi: "Maintenance"
   }
   ↓
4. Backend simpan full_name ke enrollment_manager
   ↓
5. Enrollment command dikirim ke local machine via MQTT
   ↓
6. Local machine enroll fingerprint di sensor
   ↓
7. Enrollment response diterima
   ↓
8. Backend ambil full_name dari enrollment_manager
   ↓
9. Backend simpan ke database:
   - user_sensor_1: full_name = "Hilal Akbar Quddus Ramadhan"  ← TERSIMPAN!
   - user_machine: posisi = "Maintenance"
   ↓
10. Attendance tracking bekerja:
    - full_name tersedia
    - Attendance record dibuat dengan full_name
   ↓
11. Saat scan di sensor keluar:
    - API /api/full_names mengembalikan "Hilal Akbar Quddus Ramadhan"
    - Dropdown menampilkan nama lengkap
```

## 🧪 Testing

### Test 1: Enrollment di Sensor Masuk
```bash
# 1. Scan fingerprint yang tidak terdaftar di sensor masuk
# 2. Isi form:
#    - User ID: 1
#    - Nama: Hilal
#    - Full Name: Hilal Akbar Quddus Ramadhan
#    - Posisi: Maintenance
# 3. Klik "Enroll"
# 4. Complete enrollment di sensor
```

**Expected:**
- ✅ Enrollment berhasil
- ✅ Full name tersimpan di database
- ✅ Attendance record dibuat dengan full_name
- ✅ Attendance muncul di tabel attendance

### Test 2: Check Database
```sql
-- Check user_sensor_1
SELECT user_id, username, full_name FROM user_sensor_1 WHERE user_id = 1;
-- Expected: full_name = "Hilal Akbar Quddus Ramadhan"

-- Check attendance
SELECT full_name, user_id_in, clock_in FROM attendance WHERE full_name = 'Hilal Akbar Quddus Ramadhan';
-- Expected: Record dengan full_name
```

### Test 3: Scan di Sensor Keluar
```bash
# 1. Scan fingerprint yang tidak terdaftar di sensor keluar
# 2. Modal muncul
# 3. Check dropdown "Nama Lengkap"
```

**Expected:**
- ✅ Dropdown menampilkan "Hilal Akbar Quddus Ramadhan"
- ✅ Bisa pilih nama lengkap yang sudah ada
- ✅ Atau input nama lengkap baru

### Test 4: API Full Names
```bash
curl -X GET http://localhost:5000/api/full_names \
  -H "Cookie: session=..."
```

**Expected:**
```json
{
  "full_names": [
    {
      "full_name": "Hilal Akbar Quddus Ramadhan",
      "sample_user_id": 1,
      "user_count": 1
    }
  ]
}
```

## ✅ Success Indicators

1. ✅ **Enrollment berhasil** - No errors di logs
2. ✅ **Full name tersimpan** - Check database: `SELECT full_name FROM user_sensor_1 WHERE user_id = 1;`
3. ✅ **Attendance muncul** - Check attendance table dengan full_name
4. ✅ **Dropdown berfungsi** - Saat scan di sensor keluar, nama lengkap muncul di dropdown
5. ✅ **API full_names bekerja** - `/api/full_names` mengembalikan data

## 📝 Files Modified

1. ✅ `web_ui/app.py`
   - `enroll_user()` - Tambah full_name ke enrollment command
   - `handle_enrollment_response()` - Simpan full_name ke database

2. ✅ `web_ui/templates/index.html`
   - `enrollNewUser()` - Kirim full_name dan posisi ke backend

## 🔍 Troubleshooting

### Issue: Full name masih tidak tersimpan

**Check:**
```sql
-- Check apakah full_name NULL
SELECT user_id, username, full_name FROM user_sensor_1 WHERE user_id = 1;

-- Check enrollment data
SELECT * FROM access_log WHERE user_id = 1 ORDER BY timestamp DESC LIMIT 5;
```

**Solution:**
- Pastikan form diisi dengan benar (full_name tidak kosong)
- Check browser console untuk error
- Check backend logs untuk enrollment response

### Issue: Attendance tidak muncul

**Check:**
```sql
-- Check attendance dengan full_name
SELECT * FROM attendance WHERE full_name = 'Hilal Akbar Quddus Ramadhan';

-- Check apakah full_name NULL di attendance
SELECT * FROM attendance WHERE full_name IS NULL;
```

**Solution:**
- Pastikan full_name tersimpan di user_sensor_1/user_sensor_2
- Check logs untuk "No full_name for user_id" warning
- Pastikan scan dilakukan setelah enrollment selesai

### Issue: Dropdown tidak menampilkan nama

**Check:**
```bash
# Test API
curl -X GET http://localhost:5000/api/full_names
```

**Solution:**
- Pastikan API mengembalikan data
- Check browser console untuk error
- Pastikan full_name tersimpan di database (bukan NULL)

## 🚀 Deployment

### Step 1: Update Code
```bash
cd ~/IoT-WHAC/V2/web_ui
git pull  # atau copy file baru
```

### Step 2: Restart Web UI
```bash
python3 app.py
```

### Step 3: Test
- Test enrollment di sensor masuk
- Check database untuk full_name
- Test scan di sensor keluar
- Check dropdown nama lengkap

---

**Status:** ✅ Fixed  
**Date:** 5 Januari 2026  
**Version:** 2.4

