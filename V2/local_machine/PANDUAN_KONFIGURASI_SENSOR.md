# 📖 Panduan Lengkap: Mengatur Data Sensor AS608

Panduan ini menjelaskan cara mengatur semua parameter sensor AS608 untuk sistem fingerprint multi-sensor.

---

## 📋 Daftar Isi

1. [Cara Mengatur Port Sensor](#1-cara-mengatur-port-sensor)
2. [Parameter Konfigurasi Sensor](#2-parameter-konfigurasi-sensor)
3. [Metode Konfigurasi](#3-metode-konfigurasi)
4. [Contoh Konfigurasi](#4-contoh-konfigurasi)
5. [Verifikasi Konfigurasi](#5-verifikasi-konfigurasi)

---

## 1. Cara Mengatur Port Sensor

### **A. Single Sensor (1 Sensor)**

#### **Menggunakan Environment Variable (.env)**

1. Copy file `env.example` ke `.env`:
   ```bash
   cp env.example .env
   ```

2. Edit file `.env`:
   ```bash
   nano .env
   ```

3. Set port sensor:
   ```bash
   # Untuk GPIO UART (Raspberry Pi)
   FINGERPRINT_PORT=/dev/serial0
   
   # Atau untuk USB-to-Serial adapter
   FINGERPRINT_PORT=/dev/ttyUSB0
   ```

#### **Menggunakan config.py**

Edit file `config.py`:
```python
# Untuk GPIO UART
FINGERPRINT_PORT = "/dev/serial0"

# Atau untuk USB adapter
FINGERPRINT_PORT = "/dev/ttyUSB0"
```

---

### **B. Multiple Sensors (2+ Sensor)**

#### **Menggunakan Environment Variable (.env)**

Edit file `.env`:
```bash
# Untuk 2 sensor menggunakan GPIO UART
FINGERPRINT_PORTS=/dev/serial0,/dev/ttyAMA2

# Atau untuk USB adapters
FINGERPRINT_PORTS=/dev/ttyUSB0,/dev/ttyUSB1

# Atau kombinasi GPIO + USB
FINGERPRINT_PORTS=/dev/serial0,/dev/ttyUSB0

# Untuk 3 sensor
FINGERPRINT_PORTS=/dev/ttyUSB0,/dev/ttyUSB1,/dev/ttyUSB2
```

**Catatan:** Port dipisahkan dengan koma (`,`), tanpa spasi atau dengan spasi (akan otomatis di-trim).

#### **Menggunakan config.py**

Edit file `config.py`:
```python
# Untuk 2 sensor
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/ttyAMA2"]

# Atau untuk USB adapters
FINGERPRINT_PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1"]

# Untuk 3 sensor
FINGERPRINT_PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2"]
```

---

## 2. Parameter Konfigurasi Sensor

Berikut adalah semua parameter yang bisa diatur untuk sensor:

### **A. Port Configuration**

| Parameter | Deskripsi | Default | Contoh |
|-----------|-----------|---------|--------|
| `FINGERPRINT_PORT` | Port untuk single sensor | `/dev/serial0` | `/dev/ttyUSB0` |
| `FINGERPRINT_PORTS` | Port untuk multiple sensors (comma-separated) | `[]` | `/dev/ttyUSB0,/dev/ttyUSB1` |

**Port yang umum digunakan:**
- `/dev/serial0` - GPIO UART utama (Raspberry Pi)
- `/dev/ttyAMA0` - GPIO UART alternatif
- `/dev/ttyAMA1`, `/dev/ttyAMA2` - UART tambahan (setelah enable di config.txt)
- `/dev/ttyUSB0`, `/dev/ttyUSB1` - USB-to-Serial adapters

---

### **B. Communication Settings**

| Parameter | Deskripsi | Default | Range | Contoh |
|-----------|-----------|---------|-------|--------|
| `BAUD_RATE` | Kecepatan komunikasi serial | `57600` | `9600`, `19200`, `38400`, `57600`, `115200` | `57600` |

**Catatan:** AS608 biasanya menggunakan `57600` baud rate. Jangan ubah kecuali sensor Anda menggunakan baud rate berbeda.

---

### **C. Fingerprint Matching Settings**

| Parameter | Deskripsi | Default | Range | Contoh |
|-----------|-----------|---------|-------|--------|
| `CONFIDENCE_THRESHOLD` | Minimum confidence untuk match (0-255) | `50` | `0-255` | `50` |

**Penjelasan:**
- **Nilai rendah (20-40):** Lebih mudah match, tapi bisa false positive
- **Nilai sedang (50-80):** Seimbang (recommended)
- **Nilai tinggi (100+):** Lebih ketat, mengurangi false positive tapi bisa miss match

**Rekomendasi:** Gunakan `50-80` untuk keseimbangan terbaik.

---

### **D. Scanning Settings**

| Parameter | Deskripsi | Default | Range | Contoh |
|-----------|-----------|---------|-------|--------|
| `SCAN_INTERVAL` | Interval antar scan (detik) | `5` | `1-60` | `5` |

**Penjelasan:**
- **Nilai rendah (1-3):** Scan lebih cepat, tapi lebih boros CPU
- **Nilai sedang (5-10):** Seimbang (recommended)
- **Nilai tinggi (15+):** Lebih hemat CPU, tapi respons lebih lambat

**Rekomendasi:** Gunakan `5` detik untuk penggunaan normal.

---

### **E. MQTT Settings**

| Parameter | Deskripsi | Default | Contoh |
|-----------|-----------|---------|--------|
| `MQTT_BROKER` | Alamat MQTT broker | `103.87.67.139` | `192.168.1.100` |
| `MQTT_PORT` | Port MQTT broker | `1883` | `1883` |
| `MQTT_TOPIC` | Topic untuk mengirim data scan | `WHAC/Store001/in` | `WHAC/Store002/in` |
| `MQTT_USERNAME` | Username MQTT (opsional) | `""` | `admin` |
| `MQTT_PASSWORD` | Password MQTT (opsional) | `""` | `password123` |
| `MQTT_QOS` | Quality of Service (0, 1, atau 2) | `1` | `1` |
| `MQTT_KEEPALIVE` | Keepalive interval (detik) | `60` | `60` |

---

### **F. Store Configuration**

| Parameter | Deskripsi | Default | Contoh |
|-----------|-----------|---------|--------|
| `STORE_ID` | ID toko/lokasi | `Store001` | `Store002` |

---

### **G. Logging Settings**

| Parameter | Deskripsi | Default | Opsi | Contoh |
|-----------|-----------|---------|------|--------|
| `LOG_LEVEL` | Level logging | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `LOG_FILE` | Nama file log | `fingerprint_mqtt.log` | - | `fingerprint.log` |

**Penjelasan LOG_LEVEL:**
- **DEBUG:** Menampilkan semua informasi detail (untuk troubleshooting)
- **INFO:** Menampilkan informasi normal (recommended)
- **WARNING:** Hanya warning dan error
- **ERROR:** Hanya error

---

## 3. Metode Konfigurasi

Ada 3 cara untuk mengatur konfigurasi sensor:

### **Metode 1: Environment Variable (.env) - RECOMMENDED ⭐**

**Keuntungan:**
- ✅ Mudah diubah tanpa edit kode
- ✅ Aman untuk version control (bisa di-ignore)
- ✅ Support Docker deployment
- ✅ Bisa berbeda untuk setiap environment

**Cara:**
1. Copy `env.example` ke `.env`:
   ```bash
   cp env.example .env
   ```

2. Edit `.env`:
   ```bash
   nano .env
   ```

3. Set semua parameter yang diinginkan:
   ```bash
   # Sensor Configuration
   FINGERPRINT_PORTS=/dev/ttyUSB0,/dev/ttyUSB1
   BAUD_RATE=57600
   CONFIDENCE_THRESHOLD=50
   SCAN_INTERVAL=5
   
   # MQTT Configuration
   MQTT_BROKER=103.87.67.139
   MQTT_PORT=1883
   MQTT_TOPIC=WHAC/Store001/in
   
   # Store Configuration
   STORE_ID=Store001
   
   # Logging
   LOG_LEVEL=INFO
   ```

4. Load environment variables sebelum menjalankan program:
   ```bash
   # Jika menggunakan python-dotenv
   export $(cat .env | xargs)
   python3 fingerprint_multi_client.py
   
   # Atau jika program sudah support .env otomatis
   python3 fingerprint_multi_client.py
   ```

---

### **Metode 2: Langsung Edit config.py**

**Keuntungan:**
- ✅ Langsung terlihat di kode
- ✅ Tidak perlu file tambahan

**Cara:**
1. Edit file `config.py`:
   ```bash
   nano config.py
   ```

2. Ubah nilai parameter:
   ```python
   # Sensor Configuration
   FINGERPRINT_PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1"]
   BAUD_RATE = 57600
   CONFIDENCE_THRESHOLD = 50
   SCAN_INTERVAL = 5
   
   # MQTT Configuration
   MQTT_BROKER = "103.87.67.139"
   MQTT_PORT = 1883
   MQTT_TOPIC = "WHAC/Store001/in"
   ```

3. Simpan dan jalankan program:
   ```bash
   python3 fingerprint_multi_client.py
   ```

---

### **Metode 3: Export Environment Variable di Terminal**

**Keuntungan:**
- ✅ Cepat untuk testing
- ✅ Tidak perlu edit file

**Cara:**
```bash
# Set environment variables
export FINGERPRINT_PORTS="/dev/ttyUSB0,/dev/ttyUSB1"
export BAUD_RATE=57600
export CONFIDENCE_THRESHOLD=50
export SCAN_INTERVAL=5
export MQTT_BROKER="103.87.67.139"
export MQTT_PORT=1883

# Jalankan program
python3 fingerprint_multi_client.py
```

**Catatan:** Environment variable ini hanya berlaku untuk session terminal saat ini. Setelah terminal ditutup, setting akan hilang.

---

## 4. Contoh Konfigurasi

### **Contoh 1: Single Sensor dengan GPIO UART**

**File `.env`:**
```bash
# Single Sensor - GPIO UART
FINGERPRINT_PORT=/dev/serial0
BAUD_RATE=57600
CONFIDENCE_THRESHOLD=50
SCAN_INTERVAL=5
STORE_ID=Store001
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store001/in
LOG_LEVEL=INFO
```

---

### **Contoh 2: Dua Sensor dengan USB Adapters**

**File `.env`:**
```bash
# Multiple Sensors - USB Adapters
FINGERPRINT_PORTS=/dev/ttyUSB0,/dev/ttyUSB1
BAUD_RATE=57600
CONFIDENCE_THRESHOLD=60
SCAN_INTERVAL=5
STORE_ID=Store001
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store001/in
LOG_LEVEL=INFO
```

---

### **Contoh 3: Tiga Sensor (GPIO + USB)**

**File `.env`:**
```bash
# Three Sensors - Mixed
FINGERPRINT_PORTS=/dev/serial0,/dev/ttyUSB0,/dev/ttyUSB1
BAUD_RATE=57600
CONFIDENCE_THRESHOLD=70
SCAN_INTERVAL=3
STORE_ID=Store002
MQTT_BROKER=192.168.1.100
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store002/in
MQTT_USERNAME=admin
MQTT_PASSWORD=securepass123
LOG_LEVEL=DEBUG
```

---

### **Contoh 4: High Security (Ketat)**

**File `.env`:**
```bash
# High Security Configuration
FINGERPRINT_PORTS=/dev/ttyUSB0,/dev/ttyUSB1
BAUD_RATE=57600
CONFIDENCE_THRESHOLD=100  # Sangat ketat
SCAN_INTERVAL=2  # Scan cepat
STORE_ID=Store001
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store001/in
MQTT_QOS=2  # Highest quality
LOG_LEVEL=INFO
```

---

### **Contoh 5: Development/Testing**

**File `.env`:**
```bash
# Development Configuration
FINGERPRINT_PORTS=/dev/ttyUSB0
BAUD_RATE=57600
CONFIDENCE_THRESHOLD=30  # Lebih mudah match untuk testing
SCAN_INTERVAL=1  # Scan cepat untuk testing
STORE_ID=Store001
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store001/in
LOG_LEVEL=DEBUG  # Detail logging
```

---

## 5. Verifikasi Konfigurasi

### **A. Cek Port yang Tersedia**

```bash
# List semua serial port
ls -l /dev/tty*

# Cek USB serial devices
lsusb

# Cek UART status
dmesg | grep tty
```

**Output yang diharapkan:**
```
/dev/ttyUSB0
/dev/ttyUSB1
/dev/serial0
```

---

### **B. Test Koneksi Port**

```bash
# Test port (harus bisa dibuka)
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0', 57600); print('Port OK'); s.close()"
```

---

### **C. Jalankan Program dan Cek Log**

```bash
python3 fingerprint_multi_client.py
```

**Output yang diharapkan:**
```
🔧 Configuring 2 sensors from FINGERPRINT_PORTS
📌 Sensor 1: AS608_001 -> /dev/ttyUSB0
📌 Sensor 2: AS608_002 -> /dev/ttyUSB1
[AS608_001] ✓ Sensor connected! Templates: 10
[AS608_002] ✓ Sensor connected! Templates: 8
✅ 2/2 sensors connected successfully
✓ MQTT broker connected successfully!
```

---

### **D. Cek Konfigurasi yang Aktif**

Program akan menampilkan konfigurasi saat startup:
```
======================================================================
MULTI-SENSOR FINGERPRINT MQTT CLIENT - Ready!
======================================================================
Store ID: Store001
MQTT Broker: 103.87.67.139:1883
Scan Topic: WHAC/Store001/in
Total Sensors: 2
  - AS608_001: /dev/ttyUSB0 (10 templates)
  - AS608_002: /dev/ttyUSB1 (8 templates)
Confidence Threshold: 50
======================================================================
```

---

## 🔧 Tips & Best Practices

### **1. Prioritas Konfigurasi**

Jika menggunakan environment variable dan `config.py` bersamaan:
1. **Environment variable** akan diutamakan
2. **config.py** digunakan sebagai fallback/default

### **2. Port Naming**

- Gunakan port yang konsisten (jangan sering ganti)
- USB adapters bisa berubah port (`/dev/ttyUSB0` bisa jadi `/dev/ttyUSB1` setelah reboot)
- Untuk stabilitas, gunakan GPIO UART atau udev rules untuk USB

### **3. Confidence Threshold**

- Mulai dengan nilai default (`50`)
- Jika banyak false positive → naikkan threshold
- Jika banyak miss match → turunkan threshold
- Test dengan beberapa jari untuk menemukan nilai optimal

### **4. Scan Interval**

- Untuk akses kontrol cepat → gunakan `2-3` detik
- Untuk hemat CPU → gunakan `5-10` detik
- Jangan terlalu rendah (`<1` detik) karena bisa overload sensor

### **5. Logging**

- Production: gunakan `INFO` atau `WARNING`
- Development/Troubleshooting: gunakan `DEBUG`
- File log bisa membesar, pertimbangkan log rotation

---

## 🐛 Troubleshooting

### **Port Tidak Terdeteksi**

```bash
# Cek apakah port ada
ls -l /dev/ttyUSB*

# Cek permissions
sudo chmod 666 /dev/ttyUSB0

# Cek apakah port digunakan
sudo lsof /dev/ttyUSB0
```

### **Sensor Tidak Connect**

1. Cek koneksi hardware
2. Cek baud rate (harus sesuai sensor)
3. Cek power supply sensor
4. Cek wiring TX/RX (harus cross)

### **Konfigurasi Tidak Terbaca**

1. Pastikan format `.env` benar (tidak ada spasi di sekitar `=`)
2. Pastikan environment variable di-export sebelum run
3. Cek apakah `config.py` memiliki nilai default yang benar

---

## 📚 Referensi

- [MULTI_SENSOR_GUIDE.md](./MULTI_SENSOR_GUIDE.md) - Panduan hardware multi-sensor
- [MULTI_SENSOR_USAGE.md](./MULTI_SENSOR_USAGE.md) - Panduan penggunaan multi-sensor
- [README.md](./README.md) - Dokumentasi umum

---

**Pertanyaan atau Issue?** Silakan buat issue di repository atau hubungi developer.

