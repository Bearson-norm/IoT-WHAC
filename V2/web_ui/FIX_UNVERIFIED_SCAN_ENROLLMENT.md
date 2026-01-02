# Fix: Handling Unverified Scan Enrollment

## Masalah

Ketika scan sidik jari menghasilkan "Not Match" dengan `fingerprint_id = 0`, sistem tidak bisa:
1. Menampilkan modal enrollment dengan benar
2. Mendaftarkan user baru ke sensor fisik
3. Menyinkronkan data antara database dan sensor

## Solusi yang Diterapkan

### 1. Backend (`app.py`)

#### Perbaikan di `handle_scan_message()`:
- Deteksi scan "Not Match" dengan `fingerprint_id = 0` sebagai unverified scan
- Generate temporary scan ID untuk tracking
- Set flag `is_unverified_scan = true` untuk frontend

#### Perbaikan di `process_incoming_scan()`:
- Allow `fingerprint_id = 0` atau `None` untuk unverified scans
- Set `granted_denied = "pending"` untuk unverified scans (bukan "denied")
- Skip database lookup untuk `fingerprint_id = 0`

### 2. Frontend (`index.html`)

#### Perbaikan di `showUnverifiedUserView()`:
- Deteksi `is_unverified_scan` flag
- Auto-fetch next available user ID untuk unverified scans
- Unlock user_id field untuk unverified scans

#### Perbaikan di `enrollNewUser()`:
- Deteksi apakah ini unverified scan
- Jika unverified scan:
  - Kirim enrollment command ke sensor via `/api/enroll_user`
  - Sensor akan melakukan enrollment fisik (2x scan)
  - Tunggu response dari sensor
- Jika bukan unverified scan:
  - Gunakan `/api/enroll_user_from_modal` (hanya save ke database)

## Flow Baru untuk Unverified Scan

1. **Scan "Not Match" dengan fingerprint_id = 0**
   - Sensor mengirim: `{"status": "Not Match", "fingerprint_id": 0, "device_id": "AS608_001"}`
   - Web-UI menerima dan detect sebagai unverified scan

2. **Modal Enrollment Muncul**
   - Frontend detect `is_unverified_scan = true`
   - Auto-fetch next available user ID
   - Tampilkan form enrollment

3. **User Submit Form**
   - Frontend kirim ke `/api/enroll_user` (bukan `/api/enroll_user_from_modal`)
   - Web-UI kirim MQTT command ke sensor: `WHAC/Store001/add_user`
   - Command include: `user_id`, `user_name`, `target_sensor`

4. **Sensor Enrollment Fisik**
   - Sensor terima command
   - Pause scanning
   - Lakukan enrollment fisik (2x scan sidik jari)
   - Simpan template ke sensor
   - Kirim response success/error

5. **Web-UI Terima Response**
   - Terima response dari sensor via MQTT
   - Save ke database (user_sensor_1/2 dan user_machine)
   - Kirim notifikasi ke frontend
   - Close modal

## Testing

### Test Case 1: Unverified Scan → Enrollment
1. Scan sidik jari yang tidak terdaftar
2. Modal harus muncul dengan form enrollment
3. Isi form dan submit
4. Sensor harus melakukan enrollment fisik
5. User harus terdaftar di database dan sensor

### Test Case 2: Verified Scan → Grant/Deny
1. Scan sidik jari yang sudah terdaftar
2. Modal harus muncul dengan opsi Grant/Deny
3. Grant/Deny harus bekerja dengan benar

## Catatan Penting

- **Unverified scans** (Not Match dengan ID 0) memerlukan enrollment fisik di sensor
- **Verified scans** (Match) hanya perlu approval grant/deny
- Enrollment dari unverified scan akan trigger enrollment fisik di sensor
- Enrollment dari modal manual (bukan dari scan) hanya save ke database

