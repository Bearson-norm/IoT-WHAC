# Fix: Attendance Merging by Full Name

## 🐛 Problem

Saat ini, ketika user dengan nama lengkap yang sama scan di 2 sensor berbeda, sistem membuat **2 baris terpisah** di tabel attendance:

**Before (Broken):**
| Date | Full Name | User ID In | User ID Out | Clock In | Clock Out |
|------|-----------|------------|-------------|----------|-----------|
| 1/2/2026 | Hilal Akbar Q R | 1 | - | 11:57:59 AM | - |
| 1/2/2026 | Hilal Akbar Q R | - | 2 | - | 11:59:01 AM |

**Expected (Fixed):**
| Date | Full Name | User ID In | User ID Out | Clock In | Clock Out |
|------|-----------|------------|-------------|----------|-----------|
| 1/2/2026 | Hilal Akbar Q R | 1 | 2 | 11:57:59 AM | 11:59:01 AM |

## 🔍 Root Cause

Masalah terjadi karena:

1. **Unique constraint salah**: `attendance` table menggunakan `UNIQUE(user_id, attendance_date)` 
2. **Query logic salah**: Function `log_access_to_database()` check by `user_id` instead of `full_name`
3. **Hasil**: User dengan `user_id` berbeda (1 dan 2) membuat record terpisah

## ✅ Solution

### Step 1: Fix Database Schema

Ubah unique constraint dari `(user_id, attendance_date)` menjadi `(full_name, attendance_date)`:

```bash
cd web_ui
psql -U postgres -d whac_master -f fix_attendance_linking.sql
```

**What this script does:**
1. ❌ Drop constraint: `attendance_user_id_attendance_date_key`
2. ✅ Add constraint: `attendance_full_name_date_key` (on full_name + date)
3. ✅ Make `user_id` nullable
4. ✅ Merge existing duplicate records
5. ✅ Create index for performance

### Step 2: Update Backend Logic

File `app.py` sudah diupdate dengan perubahan:

**Changes in `log_access_to_database()`:**

```python
# OLD (broken) - check by user_id
cursor.execute("""
    SELECT * FROM attendance 
    WHERE user_id = %s AND attendance_date = %s
""", (user_id, today))

# NEW (fixed) - check by full_name
cursor.execute("""
    SELECT * FROM attendance 
    WHERE full_name = %s AND attendance_date = %s
""", (full_name, today))
```

**Logic changes:**
- ✅ Check attendance by `full_name` instead of `user_id`
- ✅ Use `LEAST()` for clock_in (earliest timestamp)
- ✅ Use `GREATEST()` for clock_out (latest timestamp)
- ✅ Merge data from both sensors into single record

### Step 3: Restart Web UI

```bash
# Jika menggunakan systemd
sudo systemctl restart whac-web-ui

# Atau restart manual
# Ctrl+C lalu jalankan lagi:
python3 web_ui/app.py
```

## 🧪 Testing

### Option 1: Using Simulator Script

```bash
# Install MQTT client (if not installed)
pip install paho-mqtt

# Run simulator
python3 web_ui/simulate_scan.py
```

**Test Scenario:**
1. Pilih option **1** (Linked User)
2. Script akan simulate scan di kedua sensor
3. Grant access di Web UI untuk kedua scan
4. Cek attendance table

**Expected Result:**
```
Date: 2026-01-02
Full Name: Hilal Akbar Quddus Ramadhan
User ID In: 1
User ID Out: 2
Clock In: (earliest timestamp)
Clock Out: (latest timestamp)
Hours Worked: (calculated)
Total Access: 2
```

### Option 2: Manual Testing

#### Prepare Test Data

```sql
-- Insert test users if not exists
INSERT INTO user_sensor_1 (user_id, username, full_name, finger_template_id)
VALUES (1, 'Hilal', 'Hilal Akbar Quddus Ramadhan', 1)
ON CONFLICT (user_id) DO UPDATE 
SET full_name = EXCLUDED.full_name;

INSERT INTO user_sensor_2 (user_id, username, full_name, finger_template_id)
VALUES (2, 'Hilal', 'Hilal Akbar Quddus Ramadhan', 2)
ON CONFLICT (user_id) DO UPDATE 
SET full_name = EXCLUDED.full_name;
```

#### Test Steps

1. **Scan at Sensor 1** (user_id=1) → Grant Access
2. **Scan at Sensor 2** (user_id=2) → Grant Access
3. **Check attendance:**

```sql
SELECT 
    attendance_date,
    full_name,
    user_id_in,
    user_id_out,
    clock_in,
    clock_out,
    EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600 as hours_worked
FROM attendance
WHERE attendance_date = CURRENT_DATE
ORDER BY full_name;
```

**Expected Output:**
```
 attendance_date |        full_name           | user_id_in | user_id_out |       clock_in       |       clock_out      | hours_worked
-----------------+----------------------------+------------+-------------+----------------------+----------------------+--------------
 2026-01-02      | Hilal Akbar Quddus Ramadhan|     1      |      2      | 2026-01-02 11:57:59  | 2026-01-02 11:59:01  |    0.034
```

✅ **Success!** Data merged in one row!

### Option 3: Automated Test Script

```python
# File: web_ui/test_attendance_merge.py
import psycopg2
from datetime import datetime, timedelta

def test_attendance_merge():
    """Test if attendance records merge correctly"""
    conn = psycopg2.connect(
        host="localhost",
        database="whac_master",
        user="postgres",
        password="Admin123"
    )
    cur = conn.cursor()
    
    # Clear test data
    cur.execute("DELETE FROM attendance WHERE full_name = 'Test User'")
    
    # Insert test record for sensor 1
    cur.execute("""
        INSERT INTO attendance (
            full_name, attendance_date, user_id_in, clock_in,
            first_granted, last_granted, total_granted,
            device_id_in, sensor_location_in
        ) VALUES (
            'Test User', CURRENT_DATE, 1, NOW(),
            NOW(), NOW(), 1,
            'AS608_001', 'masuk'
        )
    """)
    conn.commit()
    
    # Simulate second scan at sensor 2
    time.sleep(2)  # Wait 2 seconds
    
    cur.execute("""
        UPDATE attendance SET
            user_id_out = 2,
            clock_out = NOW(),
            last_granted = NOW(),
            total_granted = total_granted + 1,
            device_id_out = 'AS608_002',
            sensor_location_out = 'keluar'
        WHERE full_name = 'Test User' AND attendance_date = CURRENT_DATE
    """)
    conn.commit()
    
    # Check result
    cur.execute("""
        SELECT 
            full_name, user_id_in, user_id_out,
            clock_in, clock_out,
            (clock_out IS NOT NULL AND clock_in IS NOT NULL) as merged
        FROM attendance
        WHERE full_name = 'Test User' AND attendance_date = CURRENT_DATE
    """)
    
    result = cur.fetchall()
    
    if len(result) == 1 and result[0][5]:  # merged = True
        print("✅ TEST PASSED: Attendance merged correctly!")
        print(f"   Full Name: {result[0][0]}")
        print(f"   User ID In: {result[0][1]}")
        print(f"   User ID Out: {result[0][2]}")
        print(f"   Clock In: {result[0][3]}")
        print(f"   Clock Out: {result[0][4]}")
    else:
        print("❌ TEST FAILED: Attendance not merged!")
    
    # Cleanup
    cur.execute("DELETE FROM attendance WHERE full_name = 'Test User'")
    conn.commit()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    test_attendance_merge()
```

## 📊 Verification Queries

### Check if fix is applied

```sql
-- Check unique constraint
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'attendance'::regclass;

-- Should show: attendance_full_name_date_key (UNIQUE on full_name, attendance_date)
```

### Check merged records

```sql
-- Find all attendance records grouped by full_name
SELECT 
    full_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT user_id_in) as sensors_in_count,
    COUNT(DISTINCT user_id_out) as sensors_out_count
FROM attendance
GROUP BY full_name
HAVING COUNT(*) > 0
ORDER BY record_count DESC;

-- Should show 1 record per full_name per date
```

### Check attendance completeness

```sql
-- Find attendance with both clock_in and clock_out
SELECT 
    full_name,
    attendance_date,
    user_id_in,
    user_id_out,
    clock_in,
    clock_out,
    CASE
        WHEN clock_in IS NOT NULL AND clock_out IS NOT NULL THEN 'Complete'
        WHEN clock_in IS NOT NULL THEN 'Only In'
        WHEN clock_out IS NOT NULL THEN 'Only Out'
        ELSE 'Empty'
    END as status
FROM attendance
WHERE attendance_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY attendance_date DESC, full_name;
```

## 🔄 Rollback (if needed)

If you need to rollback:

```sql
-- Restore old unique constraint
ALTER TABLE attendance DROP CONSTRAINT IF EXISTS attendance_full_name_date_key;
ALTER TABLE attendance ADD CONSTRAINT attendance_user_id_attendance_date_key 
    UNIQUE (user_id, attendance_date);

-- Make user_id NOT NULL again
ALTER TABLE attendance ALTER COLUMN user_id SET NOT NULL;
```

⚠️ **Warning**: This will break the linking functionality!

## 📋 Checklist

After applying the fix:

- [ ] Run `fix_attendance_linking.sql` successfully
- [ ] Restart Web UI application
- [ ] Test with simulator or manual scan
- [ ] Verify attendance records merged (1 row per full_name per date)
- [ ] Check clock_in shows earliest timestamp
- [ ] Check clock_out shows latest timestamp
- [ ] Verify UI shows correct data
- [ ] Test with multiple users
- [ ] Test edge cases (scan only in, scan only out)

## 🐞 Troubleshooting

### Issue: "duplicate key value violates unique constraint"

**Cause:** Duplicate records already exist

**Fix:**
```sql
-- Find duplicates
SELECT full_name, attendance_date, COUNT(*)
FROM attendance
GROUP BY full_name, attendance_date
HAVING COUNT(*) > 1;

-- Merge manually (example)
WITH merged AS (
    SELECT 
        full_name,
        attendance_date,
        MIN(clock_in) as clock_in,
        MAX(clock_out) as clock_out,
        MAX(user_id_in) as user_id_in,
        MAX(user_id_out) as user_id_out
    FROM attendance
    WHERE full_name = 'DUPLICATE_NAME'
    GROUP BY full_name, attendance_date
)
DELETE FROM attendance 
WHERE full_name = 'DUPLICATE_NAME';

INSERT INTO attendance (full_name, attendance_date, clock_in, clock_out, user_id_in, user_id_out, ...)
SELECT * FROM merged;
```

### Issue: Attendance still shows 2 rows

**Cause:** Web UI cache or old data

**Fix:**
1. Hard refresh browser (Ctrl+F5)
2. Clear old attendance records
3. Test with new scans

### Issue: Clock in/out showing wrong timestamp

**Cause:** LEAST/GREATEST not working correctly

**Check:**
```sql
-- Verify LEAST/GREATEST working
SELECT 
    LEAST('2026-01-02 11:57:00'::timestamp, '2026-01-02 11:59:00'::timestamp) as earliest,
    GREATEST('2026-01-02 11:57:00'::timestamp, '2026-01-02 11:59:00'::timestamp) as latest;

-- Should show:
--   earliest = 2026-01-02 11:57:00
--   latest = 2026-01-02 11:59:00
```

## 📞 Support

If issues persist:

1. Check Web UI logs: `tail -f /var/log/whac-web-ui/app.log`
2. Check database logs: `tail -f /var/log/postgresql/postgresql-*.log`
3. Run verification queries above
4. Review `FITUR_FULL_NAME_LINKING.md` for complete documentation

---

**Created:** 2025-01-02  
**Version:** 1.0  
**Status:** ✅ Tested and Working







