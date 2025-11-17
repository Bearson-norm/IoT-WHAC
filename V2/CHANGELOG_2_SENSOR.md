# Changelog - Support 2 Sensor (Pintu Masuk & Keluar)

## 📋 Ringkasan Perubahan

Sistem telah diupdate untuk mendukung **2 sensor AS608 fingerprint** - satu di pintu masuk dan satu di pintu keluar.

## ✅ Perubahan yang Dilakukan

### 1. **Hapus Komponen Redundant**
- ❌ **Dihapus**: `server/mqtt_data_processor.py`
  - **Alasan**: Redundant karena Web UI sudah langsung subscribe ke MQTT dan menyimpan ke database
  - **Dampak**: Tidak ada, Web UI sudah menangani semua fungsi ini

### 2. **Update Database Schema**
- ✅ **Ditambahkan kolom** `device_id` dan `sensor_location` ke tabel:
  - `log_data`
  - `log_action`
- ✅ **Ditambahkan index** untuk performa query
- ✅ **Update views** untuk menampilkan lokasi sensor (Pintu Masuk / Pintu Keluar)

### 3. **Update Web UI**
- ✅ **Auto-detect** lokasi sensor berdasarkan `device_id`:
  - `AS608_001` → Pintu Masuk
  - `AS608_002` → Pintu Keluar
- ✅ **Simpan** `device_id` dan `sensor_location` ke database
- ✅ **Tampilkan** lokasi sensor di dashboard dan logs

### 4. **Update Dokumentasi**
- ✅ **Update** `server/README.md` - Hapus referensi `mqtt_data_processor.py`
- ✅ **Buat** `server/SETUP_2_SENSOR.md` - Panduan lengkap setup 2 sensor
- ✅ **Buat** `web_ui/database_migration_2_sensor.sql` - Script migrasi database

## 🔄 Arsitektur Baru

### **Sebelum:**
```
Local Machine → MQTT → mqtt_data_processor.py → PostgreSQL → Web UI
```

### **Sesudah:**
```
Local Machine (2 Sensor) → MQTT → Web UI (Direct)
                              ↓
                        PostgreSQL
```

**Keuntungan:**
- ✅ Lebih sederhana - tidak perlu komponen server tambahan
- ✅ Lebih cepat - langsung dari MQTT ke Web UI
- ✅ Lebih efisien - mengurangi overhead processing

## 📊 Format Data MQTT

Kedua sensor mengirim ke topic yang sama (`WHAC/Store001/in`) dengan `device_id` berbeda:

**Sensor 1 (Pintu Masuk):**
```json
{
  "device_id": "AS608_001",
  "store_id": "Store001",
  "fingerprint_id": 5,
  ...
}
```

**Sensor 2 (Pintu Keluar):**
```json
{
  "device_id": "AS608_002",
  "store_id": "Store001",
  "fingerprint_id": 5,
  ...
}
```

## 🗄️ Database Changes

### **Tabel `log_data`:**
```sql
- device_id VARCHAR(50)        -- AS608_001, AS608_002
- sensor_location VARCHAR(20)  -- masuk, keluar
```

### **Tabel `log_action`:**
```sql
- device_id VARCHAR(50)        -- AS608_001, AS608_002
- sensor_location VARCHAR(20)  -- masuk, keluar
```

### **View `fingerprint_logs`:**
- Menambahkan kolom `location_display` yang menampilkan "Pintu Masuk" atau "Pintu Keluar"

### **View `action_logs`:**
- Menambahkan kolom `location_display` yang menampilkan "Pintu Masuk" atau "Pintu Keluar"

## 🚀 Cara Update Database yang Sudah Ada

Jika Anda sudah punya database yang berjalan:

```bash
# 1. Backup database dulu
pg_dump -U postgres whac_master > backup_before_migration.sql

# 2. Run migration script
psql -U postgres -d whac_master -f web_ui/database_migration_2_sensor.sql

# 3. Verify
psql -U postgres -d whac_master -c "\d log_data"
psql -U postgres -d whac_master -c "\d log_action"
```

## 📝 Setup 2 Sensor

Ikuti panduan lengkap di: `server/SETUP_2_SENSOR.md`

**Quick Start:**
1. Setup hardware (2 sensor AS608)
2. Konfigurasi `FINGERPRINT_PORTS` di `.env`
3. Jalankan `fingerprint_multi_client.py`
4. Web UI otomatis mendeteksi dan menampilkan lokasi sensor

## ⚠️ Breaking Changes

**Tidak ada breaking changes!**
- Semua perubahan backward compatible
- Database migration script tersedia
- Web UI tetap berfungsi dengan sensor tunggal

## 🎯 Next Steps

1. ✅ Update database (jika sudah ada)
2. ✅ Setup 2 sensor sesuai panduan
3. ✅ Test scan di kedua sensor
4. ✅ Verify lokasi sensor muncul di Web UI

## 📚 Dokumentasi Terkait

- `server/SETUP_2_SENSOR.md` - Panduan setup 2 sensor
- `server/README.md` - Dokumentasi server components
- `web_ui/database_setup.sql` - Schema database lengkap
- `web_ui/database_migration_2_sensor.sql` - Script migrasi

---

**Update Date**: 2024-01-15  
**Version**: 2.0.0


