# ⚡ Quick Start Setup - IoT-WHAC

Panduan cepat untuk menjalankan sistem IoT-WHAC.

---

## 🎯 Setup Cepat (5 Menit)

### 1️⃣ Setup Web UI (Komputer/Server)

```powershell
# 1. Install dependencies
cd web_ui
pip install -r requirements.txt

# 2. Setup database (jika belum ada)
# Install PostgreSQL, lalu:
psql -U postgres
CREATE DATABASE whac_master;
\q

# 3. Setup schema database
psql -U postgres -d whac_master -f database_setup.sql

# 4. Konfigurasi (opsional - edit .env jika perlu)
cp env.example .env
# Edit .env jika perlu mengubah default settings

# 5. Jalankan Web UI
python app.py
```

**Akses**: `http://localhost:5000`  
**Login**: `admin` / `admin123`

---

### 2️⃣ Setup Local Machine (Raspberry Pi)

```bash
# 1. Install dependencies
cd local_machine
pip3 install -r requirements.txt

# 2. Konfigurasi (opsional - edit config.py jika perlu)
# Default sudah OK untuk testing

# 3. Cek port sensor
python3 check_serial_ports.py

# 4. Jalankan program
# Terminal 1 - Fingerprint Scanner
python3 fingerprint_multi_client.py

# Terminal 2 - Relay Controller (jika digunakan)
python3 relay_controller_advanced.py
```

---

## 📋 Checklist Minimal

### Web UI
- [ ] PostgreSQL installed
- [ ] Database `whac_master` created
- [ ] Schema database setup (`database_setup.sql`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Web UI running (`python app.py`)
- [ ] Bisa login di `http://localhost:5000`

### Local Machine
- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] Sensor terdeteksi (cek port serial)
- [ ] Program fingerprint scanner running
- [ ] Koneksi MQTT berhasil

---

## 🔧 Konfigurasi Default

### Web UI (app.py)
- **Database**: `localhost:5432/whac_master`
- **User**: `postgres` / `Admin123`
- **Port**: `5000`
- **MQTT**: `103.87.67.139:1883`

### Local Machine (config.py)
- **Store ID**: `Store001`
- **MQTT**: `103.87.67.139:1883`
- **Port Sensor**: Auto-detect atau `/dev/ttyUSB0`
- **Baud Rate**: `57600`

---

## 🚀 Menjalankan Sistem

### Urutan:
1. **PostgreSQL** → Pastikan service running
2. **Web UI** → `cd web_ui && python app.py`
3. **Local Machine** → `cd local_machine && python3 fingerprint_multi_client.py`

### Test:
1. Buka `http://localhost:5000` → Login
2. Scan fingerprint di sensor
3. Data muncul di Web UI
4. Klik Grant/Deny → Relay control bekerja

---

## ❓ Masalah Umum

### Database Error?
```bash
# Cek PostgreSQL running
# Windows: Services → PostgreSQL
# Linux: sudo systemctl status postgresql
```

### Sensor Tidak Terdeteksi?
```bash
# Cek port
python3 check_serial_ports.py

# Linux: Permission
sudo chmod 666 /dev/ttyUSB0
```

### MQTT Connection Failed?
- Cek internet connection
- Cek firewall (port 1883)
- Test: `python3 tests/test_mqtt_connection.py`

---

## 📚 Dokumentasi Lengkap

Lihat **`PANDUAN_SETUP_SISTEM.md`** untuk panduan detail.

---

**Selamat! Sistem siap digunakan! 🎉**

