# Fitur Full Name Linking untuk Attendance System

## 📋 Overview

Fitur ini memungkinkan penghubungan data user dari 2 sensor berbeda (Sensor 1 - Pintu Masuk dan Sensor 2 - Pintu Keluar) menggunakan **Nama Lengkap** sebagai identifier umum. Hal ini berguna untuk reporting attendance yang menggabungkan data clock-in dan clock-out dari user yang sama meskipun memiliki `user_id` berbeda di masing-masing sensor.

## 🎯 Use Case

**Skenario:**
1. User A melakukan scan fingerprint di **Sensor 1 (Pintu Masuk)** → Terdaftar sebagai `user_id = 5` dengan nama lengkap "John Doe"
2. User A melakukan scan fingerprint di **Sensor 2 (Pintu Keluar)** → Terdaftar sebagai `user_id = 12` dengan nama lengkap "John Doe"
3. Sistem akan mengenali bahwa kedua `user_id` tersebut adalah orang yang sama berdasarkan **Nama Lengkap**
4. Attendance report akan menampilkan:
   - **Full Name**: John Doe
   - **User ID In**: 5
   - **User ID Out**: 12
   - **Clock In**: 08:00 (dari Sensor 1)
   - **Clock Out**: 17:00 (dari Sensor 2)

## 🗄️ Database Schema Changes

### 1. Tabel `user_sensor_1` dan `user_sensor_2`
Ditambahkan kolom `full_name`:
```sql
ALTER TABLE user_sensor_1 ADD COLUMN full_name VARCHAR(200);
ALTER TABLE user_sensor_2 ADD COLUMN full_name VARCHAR(200);
```

### 2. Tabel `attendance`
Ditambahkan kolom untuk tracking:
```sql
ALTER TABLE attendance 
ADD COLUMN full_name VARCHAR(200),
ADD COLUMN user_id_in INTEGER,
ADD COLUMN user_id_out INTEGER;
```

- `full_name`: Nama lengkap yang menghubungkan data dari kedua sensor
- `user_id_in`: User ID dari sensor masuk (Sensor 1)
- `user_id_out`: User ID dari sensor keluar (Sensor 2)

### 3. View `attendance_summary`
Diupdate untuk include kolom baru:
```sql
CREATE VIEW attendance_summary AS
SELECT 
    a.id,
    a.user_id,
    a.username,
    a.full_name,
    a.user_id_in,
    a.user_id_out,
    -- ... kolom lainnya
FROM attendance a;
```

## 🔧 API Endpoints Baru

### 1. Get All Full Names
```
GET /api/full_names
```
**Response:**
```json
{
  "full_names": [
    {
      "full_name": "John Doe",
      "sample_user_id": 5,
      "user_count": 2
    },
    {
      "full_name": "Jane Smith",
      "sample_user_id": 3,
      "user_count": 1
    }
  ]
}
```

### 2. Assign Full Name to User
```
POST /api/assign_full_name
```
**Request Body:**
```json
{
  "user_id": 5,
  "full_name": "John Doe",
  "device_id": "AS608_001"
}
```
**Response:**
```json
{
  "status": "success",
  "message": "Full name \"John Doe\" assigned to user 5",
  "user_id": 5,
  "full_name": "John Doe",
  "device_id": "AS608_001"
}
```

### 3. Link Two Users
```
POST /api/link_users
```
**Request Body:**
```json
{
  "user_id_sensor1": 5,
  "user_id_sensor2": 12,
  "full_name": "John Doe"
}
```
**Response:**
```json
{
  "status": "success",
  "message": "Users linked with full name \"John Doe\"",
  "user_id_sensor1": 5,
  "user_id_sensor2": 12,
  "full_name": "John Doe"
}
```

## 🖥️ UI/UX Changes

### Modal Pop-up untuk Unknown User

#### Sensor 1 (Pintu Masuk)
Ketika scan baru di Sensor 1, modal akan menampilkan:
- **Form Input Nama Lengkap** (required)
- User harus mengisi nama lengkap baru
- Nama ini akan digunakan untuk linking dengan data di Sensor 2

**Screenshot:**
```
┌─────────────────────────────────────────┐
│ ⚠️  User Tidak Terdaftar                │
│     Pendaftaran User Baru - Pintu Masuk │
├─────────────────────────────────────────┤
│ 📍 Sensor: Pintu Masuk (Sensor 1)      │
│                                          │
│ User ID: [5]                            │
│ Nama: [John]                            │
│ Posisi: [Staff]                         │
│                                          │
│ Nama Lengkap: *                         │
│ [John Doe________________]              │
│ ℹ️  Digunakan untuk menghubungkan data  │
│    dari sensor masuk dan keluar         │
│                                          │
│ [Daftar]  [Tidak]                       │
└─────────────────────────────────────────┘
```

#### Sensor 2 (Pintu Keluar)
Ketika scan baru di Sensor 2, modal akan menampilkan:
- **Dropdown untuk memilih nama lengkap yang sudah ada** (dari Sensor 1)
- **ATAU Form Input untuk nama lengkap baru**
- User bisa memilih nama yang sama untuk linking, atau buat baru

**Screenshot:**
```
┌─────────────────────────────────────────┐
│ ⚠️  User Tidak Terdaftar                │
│     Pendaftaran User Baru - Pintu Keluar│
├─────────────────────────────────────────┤
│ 📍 Sensor: Pintu Keluar (Sensor 2)     │
│                                          │
│ User ID: [12]                           │
│ Nama: [John]                            │
│ Posisi: [Staff]                         │
│                                          │
│ Nama Lengkap: *                         │
│ [-- Pilih nama lengkap yang sudah ada --▼]│
│ │ John Doe (2 users)                   │ │
│ │ Jane Smith (1 user)                  │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ -- ATAU --                              │
│                                          │
│ [_____________________________]         │
│ ℹ️  Buat nama lengkap baru jika belum   │
│    ada di daftar                        │
│                                          │
│ [Daftar]  [Tidak]                       │
└─────────────────────────────────────────┘
```

### Attendance Report Table

Tabel attendance report diupdate untuk menampilkan:

| Date       | Full Name  | User ID In | User ID Out | Clock In | Clock Out | Hours | Total Access | Location In  | Location Out |
|------------|------------|------------|-------------|----------|-----------|-------|--------------|--------------|--------------|
| 2025-01-02 | **John Doe** | 5          | 12          | 08:00    | 17:00     | 9.00  | 4            | Pintu Masuk  | Pintu Keluar |
| 2025-01-02 | **Jane Smith** | 3          | -           | 08:30    | -         | -     | 1            | Pintu Masuk  | -            |

**Perubahan:**
- Kolom **Full Name** ditampilkan dengan bold
- Kolom **User ID In** dan **User ID Out** terpisah untuk tracking
- Jika user hanya scan di satu sensor, kolom lainnya akan menampilkan "-"

## 🔄 Workflow

### 1. User Baru Scan di Sensor 1
```
User Scan → Modal Muncul → Input Full Name → Daftar → Data tersimpan:
- user_sensor_1: user_id=5, username="John", full_name="John Doe"
```

### 2. User yang Sama Scan di Sensor 2
```
User Scan → Modal Muncul → Pilih "John Doe" dari dropdown → Daftar → Data tersimpan:
- user_sensor_2: user_id=12, username="John", full_name="John Doe"
```

### 3. Attendance Tracking
Ketika user grant access:
```
Grant Access (Sensor 1) → Update attendance:
- attendance: user_id=5, full_name="John Doe", user_id_in=5, clock_in=08:00

Grant Access (Sensor 2) → Update attendance:
- attendance: user_id=5, full_name="John Doe", user_id_out=12, clock_out=17:00
```

**Note:** Sistem menggunakan `full_name` sebagai key untuk menggabungkan data, bukan `user_id`.

## 📊 Reporting

### Attendance Report Query
```sql
SELECT 
    full_name,
    user_id_in,
    user_id_out,
    clock_in,
    clock_out,
    EXTRACT(EPOCH FROM (clock_out - clock_in)) / 3600 as hours_worked
FROM attendance
WHERE attendance_date = '2025-01-02'
ORDER BY full_name;
```

### Benefits:
1. **Akurat**: Data clock-in dan clock-out tergabung meski dari user_id berbeda
2. **Fleksibel**: Tidak perlu user_id sama di kedua sensor
3. **User-friendly**: Menggunakan nama lengkap yang mudah dikenali
4. **Reporting**: Laporan attendance lebih akurat dan lengkap

## 🚀 Migration

Untuk database yang sudah ada, jalankan migration script:
```bash
psql -U postgres -d whac_master -f web_ui/migration_add_full_name.sql
```

Script ini akan:
1. Menambahkan kolom `full_name` ke `user_sensor_1` dan `user_sensor_2`
2. Menambahkan kolom `full_name`, `user_id_in`, `user_id_out` ke `attendance`
3. Recreate view `attendance_summary`
4. Membuat index untuk performa query

## ⚠️ Important Notes

1. **Nama Lengkap Harus Konsisten**: Pastikan nama lengkap diisi dengan format yang sama (case-sensitive)
2. **Unique Constraint**: Tabel attendance masih menggunakan `UNIQUE(user_id, attendance_date)`, jadi satu user_id hanya bisa punya satu record per hari
3. **Linking Manual**: Admin bisa menggunakan API `/api/link_users` untuk link user yang sudah terdaftar
4. **Backward Compatibility**: User lama yang belum punya `full_name` akan tetap berfungsi normal

## 🔍 Troubleshooting

### Problem: Attendance tidak ter-link
**Solution:** Pastikan `full_name` sama persis di kedua sensor. Gunakan API `/api/assign_full_name` untuk update.

### Problem: User ID In/Out tidak muncul
**Solution:** Data hanya tersimpan saat grant access. Pastikan user sudah melakukan grant access di kedua sensor.

### Problem: Dropdown tidak menampilkan nama
**Solution:** Pastikan sudah ada user di Sensor 1 dengan `full_name` yang terisi.

## 📝 Testing Checklist

- [ ] Scan baru di Sensor 1 → Modal muncul dengan form full_name
- [ ] Input full_name di Sensor 1 → Data tersimpan ke database
- [ ] Scan baru di Sensor 2 → Modal muncul dengan dropdown + form
- [ ] Pilih nama dari dropdown → Data tersimpan dengan full_name yang sama
- [ ] Grant access di Sensor 1 → Attendance record dibuat dengan user_id_in
- [ ] Grant access di Sensor 2 → Attendance record diupdate dengan user_id_out
- [ ] Attendance report menampilkan full_name, user_id_in, user_id_out
- [ ] API `/api/full_names` mengembalikan list nama lengkap
- [ ] API `/api/assign_full_name` berhasil update full_name
- [ ] API `/api/link_users` berhasil link 2 user_id

---

**Created:** 2025-01-02  
**Version:** 1.0  
**Author:** AI Assistant







