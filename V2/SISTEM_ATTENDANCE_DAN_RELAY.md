# Sistem Attendance dan Relay Control - Dokumentasi Lengkap

## 📋 Ringkasan

Sistem ini menambahkan fitur:
1. **Relay Control** - Kontrol relay otomatis saat granted access dari kedua sensor
2. **Attendance Tracking** - Tracking clock in/out otomatis berdasarkan sensor
3. **Report System** - Generate laporan attendance per user

---

## 🔧 Fitur yang Ditambahkan

### 1. **Relay Control untuk Multi-Sensor**

**Cara Kerja:**
- Ketika user scan di sensor **AS608_001** (serial0) atau **AS608_002** (ttyAMA3)
- Web UI menerima data dengan `device_id` yang berbeda
- Saat admin klik "Grant Access", relay command dikirim dengan `device_id`
- Relay di local_machine menerima command dan mengaktifkan relay

**Format MQTT Command:**
```json
{
  "command": "grant",
  "user_id": 1,
  "action": "access_granted",
  "timestamp": "2024-01-15T10:30:00",
  "source": "web_ui",
  "device_id": "AS608_001"  // atau "AS608_002"
}
```

**Topic:** `WHAC/Store001/action`

---

### 2. **Attendance Tracking (Clock In/Out)**

**Logika Clock In/Out:**
- **Clock In**: Grant access pertama kali di hari itu dari sensor **AS608_001** (masuk)
- **Clock Out**: Grant access terakhir di hari itu dari sensor **AS608_002** (keluar)

**Database Schema:**
```sql
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username VARCHAR(100),
    attendance_date DATE NOT NULL,
    clock_in TIMESTAMP,           -- Jam pertama granted dari sensor masuk
    clock_out TIMESTAMP,          -- Jam terakhir granted dari sensor keluar
    first_granted TIMESTAMP,      -- Grant pertama hari itu
    last_granted TIMESTAMP,       -- Grant terakhir hari itu
    total_granted INTEGER,        -- Total berapa kali granted hari itu
    device_id_in VARCHAR(50),     -- Device ID untuk clock in
    device_id_out VARCHAR(50),    -- Device ID untuk clock out
    sensor_location_in VARCHAR(20),
    sensor_location_out VARCHAR(20),
    UNIQUE(user_id, attendance_date)
);
```

**View untuk Query:**
```sql
CREATE VIEW attendance_summary AS
SELECT 
    *,
    CASE
        WHEN clock_in IS NOT NULL AND clock_out IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600
        ELSE NULL
    END as hours_worked
FROM attendance;
```

---

### 3. **Report System**

**API Endpoints:**

1. **Get Attendance Records:**
   ```
   GET /api/attendance?user_id=1&start_date=2024-01-01&end_date=2024-01-31&page=1&per_page=20
   ```

2. **Get Attendance Report (Summary):**
   ```
   GET /api/attendance/report?user_id=1&start_date=2024-01-01&end_date=2024-01-31
   ```
   
   Response:
   ```json
   {
     "report": [
       {
         "user_id": 1,
         "username": "John Doe",
         "days_present": 20,
         "first_date": "2024-01-01",
         "last_date": "2024-01-31",
         "clock_in_count": 20,
         "clock_out_count": 18,
         "avg_hours_worked": 8.5,
         "total_access_granted": 45
       }
     ],
     "start_date": "2024-01-01",
     "end_date": "2024-01-31",
     "generated_at": "2024-01-31T10:00:00"
   }
   ```

3. **Get User Attendance:**
   ```
   GET /api/attendance/user/1?start_date=2024-01-01&end_date=2024-01-31
   ```

---

## 🖥️ UI Features

### **Attendance Tab**

**Lokasi:** Dashboard → Tab "Attendance"

**Fitur:**
- Tabel attendance dengan kolom:
  - Date
  - User ID
  - Username
  - Clock In
  - Clock Out
  - Hours Worked
  - Total Access
  - Location In
  - Location Out

- Filter berdasarkan tanggal (start_date dan end_date)
- Pagination
- Generate Report (download CSV)

**Cara Menggunakan:**
1. Buka tab "Attendance"
2. Pilih tanggal start dan end (default: bulan ini)
3. Klik "Refresh" untuk load data
4. Klik "Generate Report" untuk download CSV

---

## 🐳 Docker Deployment

### **Konfigurasi Docker**

**File:** `web_ui/docker-compose.yml`

**Services:**
1. **postgres** - Database PostgreSQL
2. **db-init** - Database initialization
3. **web-ui** - Flask web application

**Environment Variables:**
```yaml
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
DB_PORT=5432
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_ACTION_TOPIC=WHAC/Store001/action
MQTT_SCAN_TOPIC=WHAC/Store001/in
```

### **Cara Menjalankan di Docker:**

1. **Build dan Start:**
   ```bash
   cd web_ui
   docker-compose up -d --build
   ```

2. **Cek Status:**
   ```bash
   docker-compose ps
   ```

3. **Cek Logs:**
   ```bash
   docker-compose logs -f web-ui
   ```

4. **Stop:**
   ```bash
   docker-compose down
   ```

5. **Reset Database (Hati-hati!):**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### **Database Migration:**

Database akan otomatis di-initialize saat container pertama kali dijalankan melalui:
- `db-init` service yang menjalankan `database_setup.sql`
- Tabel `attendance` akan dibuat otomatis

**Jika perlu update schema:**
1. Update `database_setup.sql`
2. Rebuild container:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

---

## 🔄 Alur Lengkap Sistem

```
┌─────────────────┐
│  Sensor 1       │
│  /dev/serial0   │──┐
│  AS608_001      │  │
│  (Pintu Masuk)  │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │     ┌──────────────┐     ┌──────────────┐
│  Sensor 2       │  │     │              │     │              │
│  /dev/ttyAMA3   │──┼────▶│  MQTT Broker │────▶│   Web UI     │
│  AS608_002      │  │     │              │     │   (app.py)   │
│  (Pintu Keluar) │  │     │  103.87.67.  │     │              │
└─────────────────┘  │     │  139:1883    │     │  PostgreSQL  │
                     │     │              │     │              │
local_machine/       │     └──────────────┘     └──────────────┘
fingerprint_multi_   │            │                     │
client.py            │            │                     │
                     │            │                     │
Topic: WHAC/Store001/in           │                     │
                     │            │                     │
                     │            ▼                     │
                     │     ┌──────────────┐             │
                     │     │              │             │
                     └────▶│  Relay       │             │
                           │  Control     │             │
                           │  (GPIO 18)   │             │
                           └──────────────┘             │
                                                         │
                                                         ▼
                                                ┌──────────────┐
                                                │  Attendance  │
                                                │  Tracking    │
                                                │  (Database)  │
                                                └──────────────┘
```

**Alur Detail:**

1. **User scan di Sensor 1 (AS608_001):**
   - Data dikirim ke MQTT topic `WHAC/Store001/in` dengan `device_id: "AS608_001"`
   - Web UI menerima dan menampilkan modal
   - Admin klik "Grant Access"
   - Relay command dikirim ke `WHAC/Store001/action` dengan `device_id: "AS608_001"`
   - Relay di local_machine aktif
   - Attendance record dibuat/update dengan `clock_in` = waktu sekarang

2. **User scan di Sensor 2 (AS608_002):**
   - Data dikirim dengan `device_id: "AS608_002"`
   - Admin klik "Grant Access"
   - Relay command dikirim dengan `device_id: "AS608_002"`
   - Relay aktif
   - Attendance record di-update dengan `clock_out` = waktu sekarang

---

## 📊 Contoh Data Attendance

**Record di Database:**
```
user_id: 1
username: "John Doe"
attendance_date: 2024-01-15
clock_in: 2024-01-15 08:00:00  (dari AS608_001)
clock_out: 2024-01-15 17:30:00 (dari AS608_002)
first_granted: 2024-01-15 08:00:00
last_granted: 2024-01-15 17:30:00
total_granted: 2
device_id_in: "AS608_001"
device_id_out: "AS608_002"
sensor_location_in: "masuk"
sensor_location_out: "keluar"
hours_worked: 9.5
```

---

## ✅ Testing

### **Test Relay Control:**

1. Scan fingerprint di sensor 1
2. Klik "Grant Access" di web UI
3. Cek log di local_machine:
   ```
   [AS608_001] ✓ Relay command received: grant
   🔓 Granting access - Relay ON for 10 seconds
   ```

### **Test Attendance:**

1. Scan di sensor 1 (masuk) → Grant Access
2. Cek database:
   ```sql
   SELECT * FROM attendance WHERE user_id = 1 AND attendance_date = CURRENT_DATE;
   ```
   - `clock_in` harus terisi
   - `device_id_in` = "AS608_001"

3. Scan di sensor 2 (keluar) → Grant Access
4. Cek database lagi:
   - `clock_out` harus terisi
   - `device_id_out` = "AS608_002"
   - `hours_worked` terhitung

### **Test Report:**

1. Buka tab "Attendance" di web UI
2. Pilih tanggal range
3. Klik "Refresh"
4. Data harus muncul di tabel
5. Klik "Generate Report"
6. File CSV harus terdownload

---

## 🐛 Troubleshooting

### **Relay tidak aktif:**
1. Cek MQTT connection:
   ```bash
   docker-compose logs web-ui | grep MQTT
   ```
2. Cek apakah device_id dikirim:
   ```bash
   docker-compose logs web-ui | grep device_id
   ```
3. Test MQTT manual:
   ```bash
   mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/action" -m '{"command":"grant","user_id":1,"device_id":"AS608_001"}'
   ```

### **Attendance tidak ter-record:**
1. Cek database:
   ```sql
   SELECT * FROM attendance ORDER BY id DESC LIMIT 10;
   ```
2. Cek log:
   ```bash
   docker-compose logs web-ui | grep attendance
   ```
3. Pastikan `update_attendance()` dipanggil saat grant access

### **Report tidak muncul:**
1. Cek API endpoint:
   ```bash
   curl http://localhost:5000/api/attendance?page=1
   ```
2. Cek browser console untuk error JavaScript
3. Pastikan database sudah ada data attendance

---

## 📝 Catatan Penting

1. **Clock In/Out Logic:**
   - Clock In hanya di-set saat grant access dari sensor masuk (AS608_001)
   - Clock Out selalu di-update saat grant access dari sensor keluar (AS608_002)
   - Jika user hanya scan di satu sensor, hanya clock_in atau clock_out yang terisi

2. **Relay Control:**
   - Relay command dikirim ke topic yang sama untuk semua sensor
   - Perbedaan hanya di field `device_id`
   - Local machine harus subscribe ke `WHAC/Store001/action`

3. **Database:**
   - Tabel `attendance` dibuat otomatis saat docker-compose up
   - View `attendance_summary` untuk query yang lebih mudah
   - Index sudah dibuat untuk performa optimal

---

## 🚀 Next Steps (Opsional)

1. **Email Notification** - Kirim email saat user clock in/out
2. **Overtime Calculation** - Hitung overtime otomatis
3. **Dashboard Widget** - Tampilkan statistik attendance di dashboard
4. **Export PDF** - Generate report dalam format PDF
5. **Mobile App** - Aplikasi mobile untuk melihat attendance

---

**Dokumentasi dibuat:** 2024-01-15
**Versi:** 1.0.0






















