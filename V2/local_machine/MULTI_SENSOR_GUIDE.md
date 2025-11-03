# Panduan Multi-Sensor AS608

## ⚠️ **PENTING: Dua Sensor TIDAK BISA Berbagi Satu UART**

**Jawaban Singkat:** Tidak memungkinkan menghubungkan 2 sensor AS608 ke satu UART yang sama di Raspberry Pi 4.

### **Alasan Teknis:**
1. **UART adalah Point-to-Point Protocol** - Bukan bus seperti I2C atau SPI
2. **Tidak Ada Address Selection** - AS608 tidak memiliki mekanisme alamat seperti I2C
3. **Data Collision** - Jika dua sensor menerima data di waktu yang sama, akan terjadi konflik
4. **Master-Slave Only** - Satu master (Pi) ke satu slave (sensor) pada satu waktu

---

## ✅ **Solusi yang Memungkinkan:**

### **1. Menggunakan UART Berbeda (Raspberry Pi 4)**

Raspberry Pi 4 memiliki beberapa UART yang bisa digunakan:

#### **Option A: Hardware UART + Software UART**
- **Hardware UART (Primary):** `/dev/serial0` atau `/dev/ttyAMA0` (GPIO 14/15)
- **Secondary UART:** `/dev/serial1` atau `/dev/ttyAMA1` (jika tersedia)
- **Software UART:** Konfigurasi melalui `config.txt` untuk GPIO lain

**Konfigurasi `config.txt`:**
```bash
# Enable additional UART
dtoverlay=uart2
dtoverlay=uart3
dtoverlay=uart4
dtoverlay=uart5
```

Setelah reboot, Anda akan memiliki:
- `/dev/ttyAMA0` - Primary UART
- `/dev/ttyAMA1` - Secondary UART
- `/dev/ttyAMA2` - Tertiary UART (jika enabled)
- dll.

#### **Option B: USB-to-Serial Adapter (Paling Mudah) ⭐**
Ini adalah solusi **paling mudah dan reliable**:

1. Beli 2 USB-to-Serial adapter (CP2102, CH340, FT232RL)
2. Hubungkan setiap sensor AS608 ke adapter
3. Sambungkan adapter ke port USB Raspberry Pi
4. Sistem akan mendeteksi sebagai `/dev/ttyUSB0` dan `/dev/ttyUSB1`

**Keuntungan:**
- ✅ Tidak perlu konfigurasi GPIO
- ✅ Plug & Play
- ✅ Lebih mudah troubleshooting
- ✅ Tidak mengganggu UART internal Pi

**Contoh Koneksi:**
```
Sensor AS608 #1 → USB-to-Serial Adapter #1 → USB Port Pi → /dev/ttyUSB0
Sensor AS608 #2 → USB-to-Serial Adapter #2 → USB Port Pi → /dev/ttyUSB1
```

---

### **2. Koneksi Hardware**

#### **Untuk AS608 ke USB-to-Serial Adapter:**
```
AS608 Sensor          USB-to-Serial Adapter
───────────          ──────────────────────
VCC (Red)    →       5V
GND (Black)  →       GND
TX           →       RX
RX           →       TX
```

#### **Untuk AS608 ke Raspberry Pi GPIO (UART):**
```
AS608 Sensor          Raspberry Pi GPIO
───────────          ──────────────────
VCC (Red)    →       5V (Pin 2 atau 4)
GND (Black)  →       GND (Pin 6, 9, 14, 20, atau 25)
TX           →       RX (GPIO 15 / Pin 10) - untuk /dev/serial0
RX           →       TX (GPIO 14 / Pin 8)  - untuk /dev/serial0
```

**Untuk UART kedua (/dev/serial1):**
- Aktifkan di `config.txt`: `dtoverlay=uart1`
- Gunakan GPIO yang berbeda sesuai dokumentasi

---

### **3. Konfigurasi Software**

#### **Mengatur Port di `config.py` atau Environment Variable:**

**Untuk USB Adapters:**
```python
# Single sensor (existing)
FINGERPRINT_PORT = "/dev/ttyUSB0"

# Multiple sensors (new support)
FINGERPRINT_PORTS = ["/dev/ttyUSB0", "/dev/ttyUSB1"]
```

**Atau via Environment Variable:**
```bash
export FINGERPRINT_PORTS="/dev/ttyUSB0,/dev/ttyUSB1"
```

**Untuk GPIO UART:**
```python
# Hardware UART + Secondary UART
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/serial1"]
```

#### **Cek Port yang Tersedia:**
```bash
# List semua serial port
ls -l /dev/tty*

# Cek USB serial devices
lsusb

# Cek UART status
dmesg | grep tty
```

---

### **4. Testing Koneksi**

Gunakan script test untuk memastikan kedua sensor terdeteksi:

```bash
cd tests
python3 debug_fingerprint_connection.py
```

Script ini akan:
- ✅ Scan semua port yang tersedia
- ✅ Test koneksi ke setiap port
- ✅ Identifikasi sensor AS608
- ✅ Tampilkan jumlah template di setiap sensor

---

### **5. Modifikasi Kode untuk Multi-Sensor**

Jika menggunakan kode multi-sensor yang sudah dimodifikasi:

```python
from fingerprint_multi_client import MultiFingerprintClient

# Inisialisasi dengan multiple ports
client = MultiFingerprintClient(
    ports=["/dev/ttyUSB0", "/dev/ttyUSB1"],
    device_ids=["AS608_001", "AS608_002"]
)

# Start scanning dari semua sensor
client.start()
```

---

## 📋 **Troubleshooting**

### **Sensor Tidak Terdeteksi:**

1. **Cek Koneksi Hardware:**
   ```bash
   lsusb  # Harus terlihat USB-to-Serial adapter
   ls -l /dev/ttyUSB*  # Harus ada device file
   ```

2. **Cek Permissions:**
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   sudo chmod 666 /dev/ttyUSB1
   ```

3. **Cek Baud Rate:**
   - Default AS608: 57600 bps
   - Pastikan semua sensor menggunakan baud rate yang sama

4. **Test Manual:**
   ```bash
   python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0', 57600); print('OK')"
   ```

### **Port Conflict:**

Jika port sudah digunakan:
```bash
# Cek process yang menggunakan port
sudo lsof /dev/ttyUSB0

# Kill process jika perlu
sudo pkill -f fingerprint
```

---

## 🎯 **Rekomendasi**

**Solusi Terbaik untuk 2 Sensor AS608:**

1. ⭐ **Gunakan 2x USB-to-Serial Adapter** (paling mudah dan reliable)
2. Gunakan Hardware UART + Secondary UART (jika USB port terbatas)
3. Gunakan Software UART (jika benar-benar diperlukan)

**Keuntungan USB-to-Serial:**
- ✅ Tidak perlu konfigurasi GPIO
- ✅ Plug & Play
- ✅ Portabel (mudah dipindah)
- ✅ Tidak mengganggu fungsi lain Pi
- ✅ Support hingga banyak sensor (tergantung USB port)

---

## 📚 **Referensi**

- [Raspberry Pi UART Documentation](https://www.raspberrypi.com/documentation/computers/configuration.html#uart)
- [AS608 Datasheet](https://github.com/adafruit/Adafruit_CircuitPython_Fingerprint)
- [PySerial Documentation](https://pyserial.readthedocs.io/)

---

**Pertanyaan?** Buat issue atau hubungi developer untuk support lebih lanjut.


