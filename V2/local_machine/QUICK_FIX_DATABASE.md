# 🔧 Quick Fix: Database Schema Error

## Error yang Anda alami:
```
ERROR - [AS608_001] Enrollment error: table users has no column named username
```

## ⚡ Solusi Cepat (3 Langkah)

### 1️⃣ Stop Service
```bash
# Jika pakai systemd
sudo systemctl stop whac-fingerprint

# Jika run manual
# Tekan Ctrl+C untuk stop process

# Jika pakai Docker
docker-compose down
```

### 2️⃣ Fix Database
```bash
cd local_machine

# Jalankan script fix
python3 fix_database_schema.py
```

### 3️⃣ Restart Service
```bash
# Jika pakai systemd
sudo systemctl start whac-fingerprint

# Jika run manual
python3 fingerprint_multi_client.py

# Jika pakai Docker
docker-compose up -d
```

---

## 📝 Alternatif: Hapus Database Lama

Jika fix script tidak bekerja, Anda bisa hapus database lama:

```bash
cd local_machine

# Backup dulu (opsional tapi disarankan)
cp fingerprints.db fingerprints.db.backup

# Hapus database lama
rm fingerprints.db

# Database baru akan dibuat otomatis dengan schema yang benar
# saat Anda run client lagi
```

⚠️ **WARNING:** Ini akan menghapus semua user yang sudah enrolled!

---

## ✅ Verifikasi

Setelah fix, coba enrollment lagi dan Anda harus lihat log seperti ini:

```
📝 Adding user 'jari manis hilal' (ID: 11) to all sensors...
⏸️  Pausing fingerprint scanning during enrollment...
[AS608_001] Starting enrollment for jari manis hilal...
[AS608_001] Place finger on sensor for first scan...
[AS608_001] ✓ First image captured!
...
[AS608_001] ✅ Fingerprint enrolled successfully at location 11!
[AS608_001] ✓ User enrolled successfully: jari manis hilal (ID: 11)
✅ Enrollment completed successfully on AS608_001
▶️  Resuming fingerprint scanning...
```

✅ Tidak ada error `table users has no column named username`

---

## 💡 Penjelasan Masalah

Database SQLite lokal memiliki 2 masalah:
1. **Column name lama:** `username` (salah)
2. **Column name baru:** `user_name` (benar)

Script fix akan:
- Backup database lama
- Migrate data ke schema baru
- Tambah kolom `device_id` untuk multi-sensor support

---

## 📚 Dokumentasi Lengkap

Untuk penjelasan detail, lihat:
- `FIX_ENROLLMENT_MULTI_SENSOR.md` - Penjelasan lengkap fix
- `fix_database_schema.py` - Source code fix script

---

**Need Help?** Check logs dengan: `tail -f logs/fingerprint_client.log`




















