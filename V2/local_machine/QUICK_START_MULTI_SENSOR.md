# Quick Start - Multi-Sensor AS608

## 🚀 Setup Cepat untuk 2 Sensor AS608

### **Langkah 1: Hardware Setup**

#### **Opsi A: GPIO UART (Raspberry Pi 4)**

1. Edit `/boot/config.txt`:
   ```bash
   sudo nano /boot/config.txt
   ```

2. Tambahkan:
   ```bash
   dtoverlay=uart2
   ```

3. Reboot:
   ```bash
   sudo reboot
   ```

4. Wiring:
   - **Sensor 1**: GPIO 14 (TX) / GPIO 15 (RX) → `/dev/serial0`
   - **Sensor 2**: GPIO 4 (TX) / GPIO 5 (RX) → `/dev/ttyAMA2`

#### **Opsi B: USB-to-Serial (Paling Mudah)**

- Sensor 1 → Adapter 1 → USB → `/dev/ttyUSB0`
- Sensor 2 → Adapter 2 → USB → `/dev/ttyUSB1`

---

### **Langkah 2: Software Configuration**

1. **Set Environment Variable:**
   ```bash
   # Untuk GPIO UART
   export FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA2"
   
   # Atau untuk USB
   export FINGERPRINT_PORTS="/dev/ttyUSB0,/dev/ttyUSB1"
   ```

2. **Atau edit `.env` file:**
   ```bash
   cp env.example .env
   nano .env
   ```
   
   Tambahkan:
   ```bash
   FINGERPRINT_PORTS=/dev/serial0,/dev/ttyAMA2
   ```

---

### **Langkah 3: Set Permissions**

```bash
sudo chmod 666 /dev/serial0
sudo chmod 666 /dev/ttyAMA2
# atau
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyUSB1

sudo usermod -a -G dialout $USER
```

---

### **Langkah 4: Run Program**

```bash
python3 fingerprint_multi_client.py
```

---

## ✅ Verifikasi

Program akan menampilkan:
```
[AS608_001] ✓ Sensor connected! Templates: X
[AS608_002] ✓ Sensor connected! Templates: Y
✅ 2/2 sensors connected successfully
✓ MQTT broker connected successfully!
```

---

## 📡 Test Scanning

1. Tempelkan jari di **Sensor 1** → Cek MQTT topic `WHAC/Store001/in`
   - Data akan memiliki `"device_id": "AS608_001"`

2. Tempelkan jari di **Sensor 2** → Cek MQTT topic `WHAC/Store001/in`
   - Data akan memiliki `"device_id": "AS608_002"`

---

## 📋 Format MQTT Data

Kedua sensor mengirim format **sama persis**, hanya berbeda `device_id`:

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

**Dari Sensor 2:**
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

## 🐛 Troubleshooting

**Sensor tidak terdeteksi?**
```bash
# Test koneksi
cd tests
python3 debug_fingerprint_connection.py
```

**Port conflict?**
```bash
sudo lsof /dev/serial0
sudo pkill -f python3
```

---

**Lihat dokumentasi lengkap:** [MULTI_SENSOR_USAGE.md](./MULTI_SENSOR_USAGE.md)


