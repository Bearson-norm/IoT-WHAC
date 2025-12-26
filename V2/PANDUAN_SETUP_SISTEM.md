# 📚 Panduan Setup Sistem IoT-WHAC

Panduan lengkap untuk setup dan menjalankan sistem IoT-WHAC, termasuk **local-machine** (Raspberry Pi) dan **web-ui**.

---

## 📋 Daftar Isi

1. [Persyaratan Sistem](#persyaratan-sistem)
2. [Setup Local Machine (Raspberry Pi)](#setup-local-machine-raspberry-pi)
3. [Setup Web UI](#setup-web-ui)
4. [Setup Database PostgreSQL](#setup-database-postgresql)
5. [Menjalankan Sistem](#menjalankan-sistem)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Persyaratan Sistem

### Hardware
- **Raspberry Pi 4** (untuk local-machine)
- **AS608 Fingerprint Sensor** (1 atau lebih)
- **Relay Module** (untuk kontrol pintu)
- **Door Sensor** (opsional, untuk monitoring pintu)
- **Komputer/Server** (untuk web-ui dan database)

### Software
- **Python 3.7+**
- **PostgreSQL 12+**
- **MQTT Broker** (sudah tersedia di `103.87.67.139:1883`)

---

## 🖥️ Setup Local Machine (Raspberry Pi)

### 1. Persiapan Environment

```bash
# Masuk ke direktori local_machine
cd local_machine

# Install dependencies Python
pip3 install -r requirements.txt
```

**Catatan untuk Windows**: Jika Anda menjalankan di Windows (bukan Raspberry Pi), beberapa library seperti `RPi.GPIO` tidak akan berfungsi. Program akan tetap berjalan untuk testing, tetapi GPIO control tidak akan bekerja.

### 2. Konfigurasi

#### Opsi A: Menggunakan File Config (config.py)

Edit file `local_machine/config.py`:

```python
# Store Configuration
STORE_ID = "Store001"

# MQTT Configuration
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"

# Fingerprint Sensor Configuration
# Untuk 1 sensor:
FINGERPRINT_PORT = "/dev/ttyUSB0"  # atau "/dev/serial0" untuk GPIO UART

# Untuk 2+ sensor (pisahkan dengan koma):
FINGERPRINT_PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1"]

BAUD_RATE = 57600
CONFIDENCE_THRESHOLD = 50
```

#### Opsi B: Menggunakan Environment Variables (.env)

```bash
# Copy file contoh
cp env.example .env

# Edit file .env
nano .env
```

Isi file `.env`:

```bash
# Store Configuration
STORE_ID=Store001

# MQTT Configuration
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store001/in

# Fingerprint Sensor Configuration
# Untuk 1 sensor:
FINGERPRINT_PORT=/dev/ttyUSB0

# Untuk 2+ sensor:
FINGERPRINT_PORTS=/dev/ttyUSB0,/dev/ttyUSB1

BAUD_RATE=57600
CONFIDENCE_THRESHOLD=50
```

### 3. Cek Port Serial Sensor

Sebelum menjalankan program, pastikan port serial sensor sudah terdeteksi:

```bash
# Di Raspberry Pi (Linux)
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial*

# Atau jalankan script pengecekan
python3 check_serial_ports.py
```

**Untuk Windows**: Port akan terlihat sebagai `COM1`, `COM2`, dll. di Device Manager.

### 4. Program yang Perlu Dijalankan

Berdasarkan dokumentasi `GPIO_ALLOCATION_DAN_PROGRAM.md`, ada beberapa skenario:

#### **Skenario 1: Sistem Lengkap dengan Verifikasi dan GPIO Control** ✅ **REKOMENDASI**

Jalankan **2 program** secara bersamaan:

**Terminal 1 - Fingerprint Scanner**:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

**Terminal 2 - GPIO Control (Relay Controller)**:
```bash
cd local_machine
python3 relay_controller_advanced.py
```

**Catatan**: 
- `fingerprint_multi_client.py` untuk multi-sensor (2+ sensor)
- `fingerprint_simple_client.py` untuk single sensor
- `relay_controller_advanced.py` mengontrol relay dan menerima command dari Web UI

#### **Skenario 2: Sistem Sederhana (Tanpa Verifikasi)**

Hanya jalankan 1 program:

```bash
cd local_machine
python3 fingerprint_simple_client.py
```

Program ini sudah memiliki relay control built-in (GPIO 18).

### 5. Verifikasi Local Machine

Setelah menjalankan program, pastikan:

1. ✅ Sensor fingerprint terdeteksi dan terhubung
2. ✅ Koneksi MQTT berhasil (lihat log: "Connected to MQTT broker")
3. ✅ Program siap scan (lihat log: "Waiting for fingerprint...")
4. ✅ Test scan fingerprint → data terkirim ke MQTT

---

## 🌐 Setup Web UI

### 1. Persiapan Environment

```bash
# Masuk ke direktori web_ui
cd web_ui

# Install dependencies Python
pip install -r requirements.txt
```

### 2. Konfigurasi

#### Opsi A: Menggunakan Environment Variables (.env)

```bash
# Copy file contoh
cp env.example .env

# Edit file .env
nano .env
```

Isi file `.env`:

```bash
# Database Configuration
DB_HOST=localhost
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
DB_PORT=5432

# MQTT Configuration
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_ACTION_TOPIC=WHAC/Store001/action
MQTT_SCAN_TOPIC=WHAC/Store001/in

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=whac_fingerprint_secret_key

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

#### Opsi B: Edit Langsung di app.py

Jika tidak menggunakan `.env`, konfigurasi default ada di `web_ui/app.py`:

```python
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'whac_master'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Admin123'),
    'port': int(os.getenv('DB_PORT', '5432'))
}
```

### 3. Setup Database PostgreSQL

#### Langkah 1: Install PostgreSQL

**Windows**:
- Download dari https://www.postgresql.org/download/windows/
- Install dengan default settings
- Catat password untuk user `postgres`

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS**:
```bash
brew install postgresql
brew services start postgresql
```

#### Langkah 2: Buat Database

```bash
# Login ke PostgreSQL
psql -U postgres

# Buat database
CREATE DATABASE whac_master;

# Keluar dari psql
\q
```

#### Langkah 3: Setup Schema Database

```bash
# Masuk ke database whac_master
psql -U postgres -d whac_master

# Jalankan script setup
\i database_setup.sql

# Atau jika menggunakan file path lengkap:
\i C:/path/to/web_ui/database_setup.sql
```

**Alternatif (Windows PowerShell)**:
```powershell
# Set environment variable untuk path
$env:PGPASSWORD = "Admin123"
psql -U postgres -d whac_master -f database_setup.sql
```

**Alternatif (Copy-paste manual)**:
1. Buka file `web_ui/database_setup.sql`
2. Copy semua isinya
3. Paste di psql prompt setelah `\c whac_master`

#### Langkah 4: Verifikasi Database

```bash
# Masuk ke database
psql -U postgres -d whac_master

# Cek tabel yang sudah dibuat
\dt

# Harus muncul tabel:
# - web_users
# - user_sessions
# - user_sensor_1
# - user_sensor_2
# - log_data
# - log_action
# - attendance
# - user_machine
# - gpio_log
```

### 4. Setup User Admin Web UI

```bash
# Masuk ke database
psql -U postgres -d whac_master

# Insert user admin default (password: admin123)
INSERT INTO web_users (username, password_hash, full_name, role) 
VALUES (
    'admin', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJY5Y5Y5Y',  -- hash untuk 'admin123'
    'Administrator',
    'admin'
);
```

**Catatan**: Password default adalah `admin123`. Untuk keamanan, ubah password setelah login pertama kali.

### 5. Jalankan Web UI

```bash
# Masuk ke direktori web_ui
cd web_ui

# Jalankan aplikasi
python app.py
```

Atau untuk production:

```bash
# Install gunicorn (opsional, untuk production)
pip install gunicorn

# Jalankan dengan gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 6. Akses Web UI

Buka browser dan akses:
- **URL**: `http://localhost:5000`
- **Username**: `admin`
- **Password**: `admin123`

---

## 🚀 Menjalankan Sistem

### Urutan Menjalankan Komponen

1. **Database PostgreSQL** (harus running)
2. **Web UI** (menjalankan di komputer/server)
3. **Local Machine** (menjalankan di Raspberry Pi)

### Langkah-langkah:

#### 1. Pastikan PostgreSQL Running

**Windows**:
- Cek di Services (services.msc) → PostgreSQL service harus "Running"

**Linux**:
```bash
sudo systemctl status postgresql
# Jika tidak running:
sudo systemctl start postgresql
```

#### 2. Jalankan Web UI

```bash
cd web_ui
python app.py
```

Tunggu sampai muncul:
```
 * Running on http://0.0.0.0:5000
```

#### 3. Jalankan Local Machine

**Di Raspberry Pi** (atau komputer dengan sensor):

**Terminal 1**:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

**Terminal 2** (jika menggunakan relay controller):
```bash
cd local_machine
python3 relay_controller_advanced.py
```

### Verifikasi Sistem Berjalan

1. ✅ **Web UI**: Buka `http://localhost:5000` → Login berhasil
2. ✅ **Local Machine**: Log menunjukkan "Connected to MQTT broker"
3. ✅ **Test Scan**: Scan fingerprint → Data muncul di Web UI
4. ✅ **MQTT**: Cek koneksi MQTT di log kedua program

---

## 🔍 Troubleshooting

### Masalah: Sensor Tidak Terdeteksi

**Solusi**:
```bash
# Cek port serial
python3 check_serial_ports.py

# Cek permission (Linux)
sudo chmod 666 /dev/ttyUSB0

# Atau tambahkan user ke group dialout
sudo usermod -a -G dialout $USER
# Logout dan login lagi
```

### Masalah: Koneksi MQTT Gagal

**Cek**:
1. Internet connection aktif
2. MQTT broker `103.87.67.139:1883` dapat diakses
3. Firewall tidak memblokir port 1883

**Test koneksi MQTT**:
```bash
cd tests
python3 test_mqtt_connection.py
```

### Masalah: Database Connection Error

**Cek**:
1. PostgreSQL service running
2. Database `whac_master` sudah dibuat
3. Username/password benar
4. Port 5432 tidak diblokir firewall

**Test koneksi database**:
```bash
cd tests
python3 test_database.py
```

### Masalah: Web UI Tidak Bisa Login

**Solusi**:
1. Pastikan tabel `web_users` sudah ada
2. Pastikan user admin sudah dibuat (lihat Setup User Admin)
3. Cek password hash di database

**Buat user admin baru**:
```sql
-- Masuk ke psql
psql -U postgres -d whac_master

-- Generate password hash (gunakan Python)
-- Di Python:
import bcrypt
password = "admin123"
hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hash.decode())

-- Insert ke database
INSERT INTO web_users (username, password_hash, full_name, role) 
VALUES ('admin', '<hash_dari_python>', 'Administrator', 'admin');
```

### Masalah: GPIO Error di Windows

**Catatan**: GPIO hanya bekerja di Raspberry Pi. Di Windows, program akan tetap berjalan tetapi GPIO control tidak akan berfungsi. Ini normal untuk testing.

### Masalah: Port Serial Sudah Digunakan

**Solusi**:
```bash
# Cek proses yang menggunakan port
python3 check_port_usage.py

# Atau di Linux:
lsof | grep ttyUSB0

# Kill process jika perlu
kill -9 <PID>
```

---

## 📊 Alur Data Sistem

```
1. Fingerprint Sensor (Local Machine)
   ↓
   Scan fingerprint
   ↓
2. fingerprint_multi_client.py
   ↓
   Kirim ke MQTT: WHAC/Store001/in
   ↓
3. Web UI Backend (app.py)
   ↓
   Terima dari MQTT → Verifikasi user → Simpan ke database
   ↓
4. Web UI Frontend
   ↓
   Tampilkan modal: Grant/Deny
   ↓
5. User klik Grant
   ↓
   Kirim ke MQTT: WHAC/Store001/action
   ↓
6. relay_controller_advanced.py
   ↓
   Terima command → Kontrol GPIO → Buka pintu
```

---

## 📝 Checklist Setup

### Local Machine
- [ ] Python 3.7+ terinstall
- [ ] Dependencies terinstall (`pip install -r requirements.txt`)
- [ ] File config.py atau .env sudah dikonfigurasi
- [ ] Port serial sensor terdeteksi
- [ ] Koneksi MQTT berhasil
- [ ] Program fingerprint scanner running
- [ ] Program relay controller running (jika digunakan)

### Web UI
- [ ] Python 3.7+ terinstall
- [ ] Dependencies terinstall (`pip install -r requirements.txt`)
- [ ] PostgreSQL terinstall dan running
- [ ] Database `whac_master` sudah dibuat
- [ ] Schema database sudah di-setup (database_setup.sql)
- [ ] User admin sudah dibuat
- [ ] File .env sudah dikonfigurasi
- [ ] Web UI running di port 5000
- [ ] Bisa login ke web UI

### Sistem
- [ ] MQTT broker dapat diakses
- [ ] Semua komponen running
- [ ] Test scan fingerprint berhasil
- [ ] Data muncul di web UI
- [ ] Grant/Deny berfungsi
- [ ] Relay control berfungsi (jika digunakan)

---

## 📞 Bantuan Tambahan

### Dokumentasi Lainnya:
- `local_machine/GPIO_ALLOCATION_DAN_PROGRAM.md` - GPIO allocation dan program
- `local_machine/README.md` - Dokumentasi local machine
- `web_ui/README.md` - Dokumentasi web UI
- `README.md` - Dokumentasi utama

### File Test:
- `tests/test_mqtt_connection.py` - Test koneksi MQTT
- `tests/test_database.py` - Test koneksi database
- `tests/check_system_status.py` - Cek status sistem

---

**Selamat! Sistem IoT-WHAC Anda sudah siap digunakan! 🎉**

