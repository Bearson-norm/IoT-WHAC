# 🚀 Cara Mulai - IoT-WHAC System

Panduan singkat untuk memulai sistem IoT-WHAC.

---

## 📖 Pilih Panduan Sesuai Kebutuhan

### 🎯 **Panduan Lengkap** (Recommended untuk pertama kali)
📄 **`PANDUAN_SETUP_SISTEM.md`**
- Panduan detail step-by-step
- Setup database, web-ui, dan local-machine
- Troubleshooting lengkap
- **Baca ini jika setup pertama kali!**

### ⚡ **Quick Start** (Untuk yang sudah familiar)
📄 **`QUICK_START_SETUP.md`**
- Panduan cepat 5 menit
- Checklist minimal
- Konfigurasi default
- **Baca ini jika ingin cepat setup!**

---

## 🖥️ Setup Web UI (Komputer/Server)

### Opsi 1: Menggunakan Script (Windows)
```powershell
# Jalankan script setup
.\setup_web_ui.bat
```

### Opsi 2: Manual Setup
```powershell
# 1. Install dependencies
cd web_ui
pip install -r requirements.txt

# 2. Setup database PostgreSQL
# - Install PostgreSQL
# - Buat database: CREATE DATABASE whac_master;
# - Setup schema: psql -U postgres -d whac_master -f database_setup.sql

# 3. Jalankan Web UI
python app.py
```

**Akses**: `http://localhost:5000`  
**Login**: `admin` / `admin123`

---

## 🖥️ Setup Local Machine (Raspberry Pi)

### Opsi 1: Menggunakan Script (Windows - untuk testing)
```powershell
# Jalankan script setup
.\setup_local_machine.bat
```

### Opsi 2: Manual Setup
```bash
# 1. Install dependencies
cd local_machine
pip3 install -r requirements.txt

# 2. Cek port sensor
python3 check_serial_ports.py

# 3. Jalankan program
# Terminal 1
python3 fingerprint_multi_client.py

# Terminal 2 (jika menggunakan relay controller)
python3 relay_controller_advanced.py
```

---

## 📋 Urutan Menjalankan

1. ✅ **PostgreSQL** → Pastikan service running
2. ✅ **Web UI** → `cd web_ui && python app.py`
3. ✅ **Local Machine** → `cd local_machine && python3 fingerprint_multi_client.py`

---

## ✅ Verifikasi Sistem

1. **Web UI**: Buka `http://localhost:5000` → Login berhasil ✅
2. **Local Machine**: Log menunjukkan "Connected to MQTT broker" ✅
3. **Test Scan**: Scan fingerprint → Data muncul di Web UI ✅
4. **Grant/Deny**: Klik Grant → Relay control bekerja ✅

---

## 📚 Dokumentasi Lainnya

- **`local_machine/GPIO_ALLOCATION_DAN_PROGRAM.md`** - GPIO allocation dan program
- **`local_machine/README.md`** - Dokumentasi local machine
- **`web_ui/README.md`** - Dokumentasi web UI
- **`README.md`** - Dokumentasi utama project

---

## 🆘 Butuh Bantuan?

1. Baca **`PANDUAN_SETUP_SISTEM.md`** bagian Troubleshooting
2. Cek file test di folder `tests/`
3. Lihat dokumentasi di masing-masing folder

---

**Selamat menggunakan sistem IoT-WHAC! 🎉**

