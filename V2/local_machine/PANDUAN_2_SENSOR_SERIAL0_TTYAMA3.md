# 📖 Panduan: Menggunakan 2 Sensor dengan Serial0 dan ttyAMA3

## ✅ Konfigurasi

Konfigurasi sudah di-update untuk menggunakan 2 sensor:
- **Sensor 1**: `/dev/serial0` (sudah terhubung via RX/TX)
- **Sensor 2**: `/dev/ttyAMA3` (uart4, sudah tersedia)

## 🔧 Setup Hardware

### **Sensor 1 - Serial0 (Sudah Terhubung)**
- Terhubung ke GPIO pins untuk serial0
- TX sensor → RX Pi (GPIO 15 / Pin 10)
- RX sensor → TX Pi (GPIO 14 / Pin 8)
- VCC → 5V
- GND → GND

### **Sensor 2 - ttyAMA3 (UART4)**
Untuk menggunakan ttyAMA3, pastikan UART4 sudah aktif di `/boot/config.txt`:

```ini
enable_uart=1
dtoverlay=uart4,pins_8_9
```

**Koneksi Hardware untuk Sensor 2:**
- TX sensor → RX Pi (sesuai GPIO untuk uart4)
- RX sensor → TX Pi (sesuai GPIO untuk uart4)
- VCC → 5V
- GND → GND

**GPIO Pins untuk UART4 (ttyAMA3):**
- TX: GPIO 8 (Pin 24)
- RX: GPIO 9 (Pin 21)

Atau alternatif:
- TX: GPIO 12 (Pin 32)
- RX: GPIO 13 (Pin 33)

## 📝 Konfigurasi Software

### **1. File config.py (Sudah Diupdate)**

Default sudah menggunakan 2 sensor:
```python
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA3")
```

### **2. Via Environment Variable (Opsional)**

Jika ingin override, set environment variable:
```bash
export FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA3"
```

### **3. Verifikasi Port**

Test kedua port sebelum digunakan:
```bash
cd local_machine
python3 test_uart_ports.py /dev/serial0 /dev/ttyAMA3
```

Output yang diharapkan:
```
✓ /dev/serial0: READY
✓ /dev/ttyAMA3: READY
```

## 🚀 Menjalankan Program

### **1. Pastikan Permission Benar**

```bash
sudo usermod -a -G dialout $USER
newgrp dialout
```

### **2. Jalankan Program**

```bash
cd local_machine
python3 fingerprint_multi_client.py
```

Program akan:
- ✅ Connect ke Sensor 1 di `/dev/serial0` (AS608_001)
- ✅ Connect ke Sensor 2 di `/dev/ttyAMA3` (AS608_002)
- ✅ Menampilkan status setiap sensor
- ✅ Scanning dari kedua sensor secara parallel

### **3. Output yang Diharapkan**

```
🔧 Configuring 2 sensors from FINGERPRINT_PORTS
📌 Sensor 1: AS608_001 -> /dev/serial0
📌 Sensor 2: AS608_002 -> /dev/ttyAMA3
[AS608_001] Connecting to sensor on /dev/serial0 (attempt 1)
[AS608_001] ✓ Sensor connected! Templates: X
[AS608_002] Connecting to sensor on /dev/ttyAMA3 (attempt 1)
[AS608_002] ✓ Sensor connected! Templates: Y
✅ 2/2 sensors connected successfully
```

## ⚠️ Troubleshooting

### **Sensor 1 (serial0) Tidak Connect**

1. **Cek koneksi hardware:**
   - Pastikan TX/RX terhubung dengan benar (cross connection)
   - Pastikan power supply (5V dan GND)

2. **Cek port:**
   ```bash
   ls -la /dev/serial0
   python3 test_uart_ports.py /dev/serial0
   ```

3. **Cek baudrate:**
   - Default: 57600
   - Pastikan sensor dikonfigurasi dengan baudrate yang sama

### **Sensor 2 (ttyAMA3) Tidak Connect**

1. **Cek apakah port ada:**
   ```bash
   ls -la /dev/ttyAMA3
   ```

2. **Cek konfigurasi UART4:**
   ```bash
   # Cek apakah uart4 aktif
   dmesg | grep ttyAMA3
   
   # Cek config.txt
   grep uart4 /boot/config.txt
   ```

3. **Jika port tidak ada, aktifkan UART4:**
   ```bash
   sudo nano /boot/config.txt
   # Tambahkan:
   enable_uart=1
   dtoverlay=uart4,pins_8_9
   
   # Reboot
   sudo reboot
   ```

4. **Cek koneksi hardware:**
   - Pastikan sensor terhubung ke GPIO pins yang benar untuk uart4
   - TX sensor → RX Pi (GPIO 9 / Pin 21)
   - RX sensor → TX Pi (GPIO 8 / Pin 24)

### **Kedua Sensor Tidak Connect**

1. **Cek permission:**
   ```bash
   groups  # Harus ada 'dialout'
   sudo usermod -a -G dialout $USER
   newgrp dialout
   ```

2. **Test port satu per satu:**
   ```bash
   python3 test_uart_ports.py /dev/serial0
   python3 test_uart_ports.py /dev/ttyAMA3
   ```

3. **Cek apakah ada proses lain yang menggunakan port:**
   ```bash
   sudo lsof /dev/serial0
   sudo lsof /dev/ttyAMA3
   ```

4. **Jalankan dengan log level DEBUG:**
   ```bash
   export LOG_LEVEL=DEBUG
   python3 fingerprint_multi_client.py
   ```

## 📊 Monitoring

Program akan menampilkan:
- Status koneksi setiap sensor
- Jumlah template di setiap sensor
- Scan results dengan device_id yang berbeda:
  - `AS608_001` untuk sensor di serial0
  - `AS608_002` untuk sensor di ttyAMA3

## 🔍 Verifikasi Setelah Setup

### **1. Cek Status Sensor**

Setelah program berjalan, cek log:
```
MULTI-SENSOR FINGERPRINT MQTT CLIENT - Ready!
Total Sensors: 2
  - AS608_001: /dev/serial0 (X templates)
  - AS608_002: /dev/ttyAMA3 (Y templates)
```

### **2. Test Scanning**

Letakkan jari di salah satu sensor, program akan:
- Mendeteksi fingerprint
- Mengirim data ke MQTT dengan device_id yang sesuai
- Menampilkan log: `[AS608_001] ✓ Match found!` atau `[AS608_002] ✓ Match found!`

### **3. Test Enrollment**

Enroll fingerprint melalui MQTT atau Web UI:
- Program akan secara otomatis memilih sensor yang belum memiliki fingerprint tersebut
- Atau bisa specify target sensor

## 📝 Catatan Penting

1. **Device ID:**
   - Sensor 1: `AS608_001` (serial0)
   - Sensor 2: `AS608_002` (ttyAMA3)

2. **Baudrate:**
   - Default: 57600 (sama untuk kedua sensor)
   - Bisa diubah di `config.py`: `BAUD_RATE = 57600`

3. **Scanning:**
   - Kedua sensor scanning secara parallel
   - Setiap sensor memiliki thread sendiri
   - Scan interval: 5 detik (default, bisa diubah di `config.py`)

4. **Database:**
   - Menggunakan `fingerprints_multi.db`
   - Menyimpan mapping fingerprint_id → user_name → device_id

## ✅ Checklist

- [x] Config.py sudah di-update ke `/dev/serial0,/dev/ttyAMA3`
- [ ] Port `/dev/serial0` bisa dibuka (test dengan `test_uart_ports.py`)
- [ ] Port `/dev/ttyAMA3` bisa dibuka (test dengan `test_uart_ports.py`)
- [ ] Sensor 1 terhubung ke serial0 dengan benar
- [ ] Sensor 2 terhubung ke ttyAMA3 dengan benar (GPIO 8-9)
- [ ] UART4 aktif di `/boot/config.txt` (jika ttyAMA3 tidak ada)
- [ ] Permission sudah benar (user di group `dialout`)
- [ ] Kedua sensor mendapat power (LED menyala)
- [ ] Baudrate sensor sesuai (57600)
- [ ] Program berjalan dan kedua sensor connect

## 🎯 Quick Start

```bash
# 1. Test port
cd local_machine
python3 test_uart_ports.py /dev/serial0 /dev/ttyAMA3

# 2. Pastikan permission
sudo usermod -a -G dialout $USER
newgrp dialout

# 3. Jalankan program
python3 fingerprint_multi_client.py
```

---

**Selamat! Konfigurasi 2 sensor sudah siap. Program akan menggunakan serial0 dan ttyAMA3 secara bersamaan.** 🎉

