# Setup 2 Sensor AS608 - Pintu Masuk & Keluar

Panduan lengkap untuk setup 2 sensor AS608 fingerprint, satu di pintu masuk dan satu di pintu keluar.

## 📋 Overview

Sistem ini menggunakan **2 sensor AS608** yang terhubung ke **1 Raspberry Pi**:
- **Sensor 1 (AS608_001)**: Pintu Masuk
- **Sensor 2 (AS608_002)**: Pintu Keluar

Kedua sensor mengirim data ke **MQTT topic yang sama** (`WHAC/Store001/in`) dengan `device_id` yang berbeda untuk identifikasi.

## 🔧 Hardware Setup

### **Opsi 1: Menggunakan GPIO UART (Recommended untuk Raspberry Pi)**

#### **Konfigurasi Raspberry Pi:**

1. Edit `/boot/config.txt`:
```bash
sudo nano /boot/config.txt
```

2. Tambahkan untuk mengaktifkan UART tambahan:
```bash
# Aktifkan UART2 untuk sensor kedua
dtoverlay=uart2
```

3. Reboot:
```bash
sudo reboot
```

#### **Wiring:**

**Sensor AS608 #1 (Pintu Masuk):**
```
- VCC → 5V (Pin 2)
- GND → GND (Pin 6)
- TX  → GPIO 15 (Pin 10) - RX dari Pi
- RX  → GPIO 14 (Pin 8)  - TX dari Pi
Port: /dev/serial0
```

**Sensor AS608 #2 (Pintu Keluar):**
```
- VCC → 5V (Pin 2) - bisa share dengan sensor 1
- GND → GND (Pin 6) - bisa share dengan sensor 1
- TX  → GPIO 5 (Pin 29) - RX dari Pi
- RX  → GPIO 4 (Pin 7)  - TX dari Pi
Port: /dev/ttyAMA2
```

### **Opsi 2: Menggunakan USB-to-Serial Adapter (Paling Mudah)**

Gunakan 2 adapter USB-to-Serial:
- **Sensor 1 (Pintu Masuk)** → Adapter 1 → USB Port → `/dev/ttyUSB0`
- **Sensor 2 (Pintu Keluar)** → Adapter 2 → USB Port → `/dev/ttyUSB1`

## 💻 Software Setup

### **1. Install Dependencies**

```bash
cd local_machine
pip3 install -r requirements.txt
```

### **2. Set Permissions**

```bash
# Untuk GPIO UART
sudo chmod 666 /dev/serial0
sudo chmod 666 /dev/ttyAMA2

# Atau untuk USB
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyUSB1

# Tambahkan user ke group dialout
sudo usermod -a -G dialout $USER
```

### **3. Konfigurasi Environment**

Copy dan edit `env.example`:
```bash
cd local_machine
cp env.example .env
nano .env
```

**Untuk GPIO UART:**
```bash
STORE_ID=Store001
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store001/in
FINGERPRINT_PORTS=/dev/serial0,/dev/ttyAMA2
BAUD_RATE=57600
CONFIDENCE_THRESHOLD=50
SCAN_INTERVAL=5
```

**Untuk USB Adapters:**
```bash
STORE_ID=Store001
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store001/in
FINGERPRINT_PORTS=/dev/ttyUSB0,/dev/ttyUSB1
BAUD_RATE=57600
CONFIDENCE_THRESHOLD=50
SCAN_INTERVAL=5
```

### **4. Jalankan Program**

```bash
cd local_machine
python3 fingerprint_multi_client.py
```

## 📡 Format Data MQTT

Kedua sensor mengirim data ke topic `WHAC/Store001/in` dengan format yang sama, hanya berbeda pada `device_id`:

**Dari Sensor 1 (Pintu Masuk - AS608_001):**
```json
{
  "store_id": "Store001",
  "timestamp": "2024-01-15T10:30:45.123456",
  "status": "Match",
  "fingerprint_id": 5,
  "device_id": "AS608_001",
  "username": "John Doe",
  "confidence": 85
}
```

**Dari Sensor 2 (Pintu Keluar - AS608_002):**
```json
{
  "store_id": "Store001",
  "timestamp": "2024-01-15T10:31:20.123456",
  "status": "Match",
  "fingerprint_id": 5,
  "device_id": "AS608_002",
  "username": "John Doe",
  "confidence": 85
}
```

## 🗄️ Database Tracking

Web UI secara otomatis:
- ✅ **Mendeteksi** `device_id` dari setiap scan
- ✅ **Menentukan lokasi** sensor (masuk/keluar) berdasarkan `device_id`
- ✅ **Menyimpan** `device_id` dan `sensor_location` ke database
- ✅ **Menampilkan** lokasi sensor di dashboard dan logs

**Mapping:**
- `AS608_001` → `sensor_location = 'masuk'` → Display: "Pintu Masuk"
- `AS608_002` → `sensor_location = 'keluar'` → Display: "Pintu Keluar"

## 🎯 Testing

### **1. Test Sensor 1 (Pintu Masuk):**
```bash
# Tempelkan jari di Sensor 1
# Cek MQTT topic
mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/in" -v
```

**Expected output:**
```json
{
  "device_id": "AS608_001",
  ...
}
```

### **2. Test Sensor 2 (Pintu Keluar):**
```bash
# Tempelkan jari di Sensor 2
# Cek MQTT topic (sama)
mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/in" -v
```

**Expected output:**
```json
{
  "device_id": "AS608_002",
  ...
}
```

### **3. Test Web UI:**
1. Buka Web UI di browser
2. Login sebagai admin
3. Scan fingerprint di Sensor 1 → Harus muncul "Pintu Masuk"
4. Scan fingerprint di Sensor 2 → Harus muncul "Pintu Keluar"

## 🔍 Troubleshooting

### **Sensor tidak terdeteksi:**
```bash
# Cek port yang tersedia
ls -l /dev/tty* | grep -E "USB|AMA|serial"

# Test koneksi serial
python3 -c "import serial; s=serial.Serial('/dev/serial0', 57600); print('OK')"
```

### **Permission denied:**
```bash
sudo chmod 666 /dev/serial0
sudo chmod 666 /dev/ttyAMA2
# atau
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyUSB1
```

### **Device ID tidak sesuai:**
- Pastikan urutan port di `FINGERPRINT_PORTS` sesuai dengan urutan fisik
- Port pertama = AS608_001 (Pintu Masuk)
- Port kedua = AS608_002 (Pintu Keluar)

## 📊 Monitoring

### **Logs:**
Program akan menampilkan log untuk setiap sensor:
```
📌 Sensor 1: AS608_001 -> /dev/serial0
📌 Sensor 2: AS608_002 -> /dev/ttyAMA2
✅ Sensor AS608_001 connected
✅ Sensor AS608_002 connected
```

### **Web UI Dashboard:**
- Lihat semua scan dengan lokasi sensor
- Filter berdasarkan sensor (masuk/keluar)
- Statistik per sensor

## ✅ Checklist Setup

- [ ] Hardware terhubung dengan benar
- [ ] UART2 diaktifkan (jika menggunakan GPIO)
- [ ] Permissions diatur
- [ ] Environment variables dikonfigurasi
- [ ] Program berjalan tanpa error
- [ ] Sensor 1 terdeteksi sebagai AS608_001
- [ ] Sensor 2 terdeteksi sebagai AS608_002
- [ ] Data muncul di MQTT topic
- [ ] Web UI menampilkan lokasi sensor dengan benar

## 🎉 Selesai!

Sistem 2 sensor sudah siap digunakan. Kedua sensor akan mengirim data ke Web UI secara real-time dengan identifikasi lokasi yang jelas (Pintu Masuk / Pintu Keluar).


