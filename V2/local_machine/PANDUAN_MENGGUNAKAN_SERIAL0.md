# 📖 Panduan: Menggunakan Serial0 untuk Sensor Fingerprint

## ✅ Status

Konfigurasi sudah di-update untuk menggunakan `/dev/serial0` sebagai default, sesuai dengan koneksi hardware Anda yang sudah terhubung via RX/TX.

## 🔧 Konfigurasi

### **1. Default Configuration (Sudah Diperbarui)**

File `config.py` sudah di-update dengan default:
```python
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/serial0")
```

Ini berarti program akan menggunakan `/dev/serial0` secara default.

### **2. Verifikasi Port**

Cek apakah `/dev/serial0` menunjuk ke port yang benar:
```bash
ls -la /dev/serial0
# Output: lrwxrwxrwx 1 root root 5 ... /dev/serial0 -> ttyS0
```

Dari hasil diagnosis sebelumnya:
- `/dev/serial0` → `ttyS0` (mini UART)

### **3. Test Port**

Test apakah port bisa digunakan:
```bash
cd local_machine
python3 test_uart_ports.py /dev/serial0
```

## 🚀 Menjalankan Program

### **Single Sensor (Default)**

Karena default sudah `/dev/serial0`, Anda bisa langsung menjalankan:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

### **Multi-Sensor (Jika Ada Sensor Tambahan)**

Jika Anda punya sensor tambahan di port lain (misalnya ttyAMA2), set environment variable:
```bash
export FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA2"
python3 fingerprint_multi_client.py
```

Atau edit `config.py`:
```python
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA2")
```

## ⚠️ Troubleshooting

### **Error: "Failed to read data from sensor"**

Jika sensor tidak merespons, cek:

1. **Koneksi Hardware:**
   - Pastikan sensor AS608 terhubung dengan benar
   - TX sensor → RX Pi (GPIO 15 / Pin 10)
   - RX sensor → TX Pi (GPIO 14 / Pin 8)
   - VCC → 5V
   - GND → GND

2. **Baudrate:**
   - Default: 57600
   - Pastikan sensor dikonfigurasi dengan baudrate yang sama
   - Cek di `config.py`: `BAUD_RATE = 57600`

3. **Power Supply:**
   - Pastikan sensor mendapat power yang cukup (5V)
   - Cek LED sensor apakah menyala

4. **Port yang Benar:**
   - Verifikasi `/dev/serial0` benar-benar terhubung ke sensor
   - Coba test dengan: `python3 test_uart_ports.py /dev/serial0`

5. **Permission:**
   ```bash
   sudo usermod -a -G dialout $USER
   newgrp dialout
   ```

### **Error: "Permission denied"**

```bash
# Tambahkan user ke group dialout
sudo usermod -a -G dialout $USER

# Atau logout dan login lagi
# Atau gunakan:
newgrp dialout
```

### **Port Tidak Terdeteksi**

Jika `/dev/serial0` tidak ada:
```bash
# Cek symlink
ls -la /dev/serial*

# Cek port yang tersedia
ls -la /dev/tty*
```

## 📝 Catatan Penting

1. **Serial0 vs ttyAMA0:**
   - `/dev/serial0` adalah symlink yang bisa menunjuk ke:
     - `ttyAMA0` (PL011 UART) - untuk Pi 3 dan sebelumnya
     - `ttyS0` (mini UART) - untuk Pi 4 dengan konfigurasi tertentu
   
   Dari diagnosis Anda, `/dev/serial0` → `ttyS0` (mini UART).

2. **Koneksi Hardware:**
   - Sensor terhubung ke GPIO pins untuk serial0
   - GPIO 14 (TX) dan GPIO 15 (RX) untuk PL011 UART
   - Atau GPIO 14 (TX) dan GPIO 15 (RX) untuk mini UART

3. **Baudrate:**
   - Default: 57600
   - Pastikan sensor AS608 dikonfigurasi dengan baudrate yang sama

## ✅ Checklist

- [x] Config.py sudah di-update ke `/dev/serial0`
- [ ] Port `/dev/serial0` bisa dibuka (test dengan `test_uart_ports.py`)
- [ ] Sensor AS608 terhubung dengan benar (TX/RX, VCC, GND)
- [ ] Permission sudah benar (user di group `dialout`)
- [ ] Sensor mendapat power (LED menyala)
- [ ] Baudrate sensor sesuai (57600)
- [ ] Program berjalan tanpa error

## 🔍 Debugging

Jika masih ada masalah, jalankan dengan log level DEBUG:
```bash
export LOG_LEVEL=DEBUG
python3 fingerprint_multi_client.py
```

Atau test koneksi langsung:
```python
import serial
import time

ser = serial.Serial('/dev/serial0', baudrate=57600, timeout=2)
time.sleep(0.5)
print("Port opened!")
# Try to read
data = ser.read(10)
print(f"Data: {data}")
ser.close()
```

---

**Selamat! Konfigurasi sudah di-update untuk menggunakan serial0 sesuai koneksi hardware Anda.** 🎉

