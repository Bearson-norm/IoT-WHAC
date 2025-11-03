# Panduan Penggunaan Multi-Sensor AS608

## 📋 Ringkasan

Program `fingerprint_multi_client.py` adalah versi multi-sensor dari `fingerprint_simple_client.py` yang mendukung **beberapa sensor AS608 secara simultan** dengan protokol pengiriman MQTT yang **sama persis**, hanya berbeda pada atribut `device_id` untuk mengidentifikasi sensor mana yang mendeteksi sidik jari.

---

## ✅ Fitur

- ✅ **Multi-Sensor Support**: Mendukung 2 atau lebih sensor AS608 secara bersamaan
- ✅ **Threading**: Scanning dari semua sensor berjalan secara parallel (tidak saling blocking)
- ✅ **Protokol Sama**: Format JSON MQTT identik dengan single sensor version
- ✅ **Device ID Unik**: Setiap sensor memiliki `device_id` unik (AS608_001, AS608_002, dll)
- ✅ **Auto-Detection**: Otomatis mendeteksi port sensor jika tidak dikonfigurasi
- ✅ **Thread-Safe**: Operasi scanning thread-safe untuk menghindari konflik
- ✅ **MQTT Commands**: Mendukung command add_user, import, export, relay control

---

## 🔧 Konfigurasi

### **1. Konfigurasi Hardware**

#### **Opsi A: Menggunakan GPIO UART (Raspberry Pi 4)**

Edit `/boot/config.txt`:
```bash
sudo nano /boot/config.txt
```

Tambahkan untuk mengaktifkan UART tambahan:
```bash
# Aktifkan UART2 untuk sensor kedua
dtoverlay=uart2
```

Reboot:
```bash
sudo reboot
```

**Wiring:**
```
Sensor AS608 #1:
- VCC → 5V (Pin 2)
- GND → GND (Pin 6)
- TX  → GPIO 15 (Pin 10) - RX dari Pi
- RX  → GPIO 14 (Pin 8)  - TX dari Pi
Port: /dev/serial0

Sensor AS608 #2:
- VCC → 5V (Pin 2) - bisa share
- GND → GND (Pin 6) - bisa share
- TX  → GPIO 5 (Pin 29) - RX dari Pi
- RX  → GPIO 4 (Pin 7)  - TX dari Pi
Port: /dev/ttyAMA2
```

#### **Opsi B: Menggunakan USB-to-Serial Adapter (Paling Mudah)**

Gunakan 2 adapter USB-to-Serial:
- Sensor 1 → Adapter 1 → USB Port → `/dev/ttyUSB0`
- Sensor 2 → Adapter 2 → USB Port → `/dev/ttyUSB1`

---

### **2. Konfigurasi Software**

#### **Opsi A: Environment Variable (Recommended)**

Edit file `.env` atau set environment variable:

```bash
# Untuk 2 sensor menggunakan GPIO UART
export FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA2"

# Atau untuk USB adapters
export FINGERPRINT_PORTS="/dev/ttyUSB0,/dev/ttyUSB1"

# Atau kombinasi
export FINGERPRINT_PORTS="/dev/serial0,/dev/ttyUSB0"
```

#### **Opsi B: Edit config.py**

Edit `local_machine/config.py`:

```python
# Untuk 2 sensor
FINGERPRINT_PORTS = ["/dev/serial0", "/dev/ttyAMA2"]
```

---

## 🚀 Menjalankan Program

### **1. Install Dependencies**

```bash
cd local_machine
pip3 install -r requirements.txt
```

### **2. Set Permissions**

```bash
# Set permissions untuk serial ports
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
cp env.example .env
nano .env
```

Set `FINGERPRINT_PORTS`:
```bash
FINGERPRINT_PORTS=/dev/serial0,/dev/ttyAMA2
```

### **4. Jalankan Program**

```bash
python3 fingerprint_multi_client.py
```

---

## 📡 Format MQTT Data

### **Format JSON (Sama dengan Single Sensor)**

Ketika sensor mendeteksi sidik jari, data dikirim ke topic `WHAC/Store001/in` dengan format:

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

**Perbedaan dengan Single Sensor:**
- ✅ Format JSON **identik sama**
- ✅ **`device_id`** berbeda untuk mengidentifikasi sensor:
  - Sensor pertama: `"device_id": "AS608_001"`
  - Sensor kedua: `"device_id": "AS608_002"`
  - Sensor ketiga: `"device_id": "AS608_003"`, dst.

### **Contoh Output**

**Dari Sensor 1:**
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

**Dari Sensor 2 (deteksi bersamaan atau berbeda waktu):**
```json
{
  "store_id": "Store001",
  "timestamp": "2024-01-15T10:30:47.234567",
  "status": "Match",
  "fingerprint_id": 5,
  "device_id": "AS608_002",
  "username": "John Doe",
  "confidence": 88
}
```

---

## 🔍 Testing

### **1. Test Koneksi Sensor**

```bash
# Test apakah sensor terdeteksi
cd tests
python3 debug_fingerprint_connection.py
```

### **2. Test Multi-Sensor**

Jalankan program dan cek log:
```bash
python3 fingerprint_multi_client.py
```

Output yang diharapkan:
```
[AS608_001] ✓ Sensor connected! Templates: 10
[AS608_002] ✓ Sensor connected! Templates: 10
✅ 2/2 sensors connected successfully
✓ MQTT broker connected successfully!
[AS608_001] Starting standby scanning on /dev/serial0...
[AS608_002] Starting standby scanning on /dev/ttyAMA2...
```

### **3. Test Scanning**

1. Tempelkan jari di sensor pertama → Cek MQTT topic
2. Tempelkan jari di sensor kedua → Cek MQTT topic
3. Keduanya harus mengirim data dengan `device_id` yang berbeda

---

## 📊 Monitoring

### **Cek Log**

```bash
tail -f fingerprint_mqtt.log
```

### **Cek MQTT Topic**

Gunakan MQTT client untuk subscribe ke topic:
```
WHAC/Store001/in
```

Anda akan melihat data dari semua sensor dengan `device_id` yang berbeda.

---

## 🎯 Use Cases

### **1. Dua Pintu Masuk Berbeda**

- **Sensor 1** (`AS608_001`): Pintu masuk utama
- **Sensor 2** (`AS608_002`): Pintu masuk belakang

Server bisa membedakan pintu mana yang digunakan berdasarkan `device_id`.

### **2. Antrian Ganda**

- **Sensor 1** (`AS608_001`): Counter 1
- **Sensor 2** (`AS608_002`): Counter 2

Kedua sensor bisa scan bersamaan tanpa blocking.

### **3. Redundancy/Backup**

- **Sensor 1** (`AS608_001`): Primary
- **Sensor 2** (`AS608_002`): Backup

Jika satu sensor mati, sensor lain tetap berfungsi.

---

## 🐛 Troubleshooting

### **Sensor Tidak Terdeteksi**

1. **Cek Port:**
   ```bash
   ls -l /dev/tty*
   ```

2. **Cek Permissions:**
   ```bash
   sudo chmod 666 /dev/serial0
   sudo chmod 666 /dev/ttyAMA2
   ```

3. **Cek Koneksi Hardware:**
   - Pastikan kabel terhubung dengan benar
   - Pastikan sensor mendapat power (LED menyala)
   - Cek wiring TX/RX (harus cross: TX sensor ke RX Pi)

### **Port Conflict**

```bash
# Cek process yang menggunakan port
sudo lsof /dev/serial0
sudo lsof /dev/ttyAMA2

# Kill process jika perlu
sudo pkill -f python3
```

### **Satu Sensor Tidak Scan**

- Cek log untuk error spesifik
- Pastikan sensor terhubung dengan benar
- Coba restart program

### **MQTT Tidak Terkirim**

- Cek koneksi ke MQTT broker
- Cek topic configuration
- Cek network connectivity

---

## 📝 Perbedaan dengan Single Sensor Version

| Aspek | Single Sensor | Multi Sensor |
|-------|---------------|--------------|
| File | `fingerprint_simple_client.py` | `fingerprint_multi_client.py` |
| Sensor Support | 1 sensor | 2+ sensors |
| Threading | Single thread | Multi-thread (1 per sensor) |
| Device ID | Fixed: `AS608_001` | Dynamic: `AS608_001`, `AS608_002`, etc. |
| Config | `FINGERPRINT_PORT` | `FINGERPRINT_PORTS` (comma-separated) |
| Protokol MQTT | ✅ Sama | ✅ Sama |

---

## 🔄 Migrasi dari Single Sensor

Jika sebelumnya menggunakan `fingerprint_simple_client.py`:

1. **Backup config:**
   ```bash
   cp config.py config.py.backup
   ```

2. **Update config:**
   - Set `FINGERPRINT_PORTS` dengan port sensor yang ada
   - Atau tambahkan sensor kedua ke `FINGERPRINT_PORTS`

3. **Jalankan multi-sensor version:**
   ```bash
   python3 fingerprint_multi_client.py
   ```

4. **Verifikasi:**
   - Pastikan semua sensor terdeteksi
   - Test scanning dari setiap sensor
   - Cek MQTT topic untuk memastikan data terkirim dengan `device_id` yang benar

---

## 📚 Referensi

- [Raspberry Pi UART Configuration](./MULTI_SENSOR_GUIDE.md)
- [Single Sensor Documentation](./README.md)
- [Troubleshooting Guide](./README.md#troubleshooting)

---

**Pertanyaan atau Issue?** Silakan buat issue di repository atau hubungi developer.


