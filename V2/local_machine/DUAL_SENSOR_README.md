# Dual AS608 Fingerprint Sensor System (3.3V)

Sistem dual sensor AS608 yang kompatibel dengan 3.3V dan mengikuti struktur sistem existing yang sudah ada.

## ✅ **Keunggulan 3.3V AS608**

- **Tidak Perlu Level Shifter** - Langsung koneksi ke Raspberry Pi
- **Power Efficient** - Konsumsi daya lebih rendah
- **Stable Operation** - Operasi lebih stabil
- **Direct GPIO Connection** - Koneksi langsung ke GPIO Pi

## 🔧 **Hardware Setup untuk 3.3V**

### **Opsi 1: USB-to-Serial Adapters (RECOMMENDED)**

**Koneksi:**
```
AS608 (3.3V) → USB-to-Serial TTL → USB Port Pi
```

**Pin Mapping:**
```
AS608 VCC → USB-to-Serial 3.3V
AS608 GND → USB-to-Serial GND  
AS608 TX  → USB-to-Serial RX
AS608 RX  → USB-to-Serial TX
```

**Port yang akan terdeteksi:**
- Sensor 1: `/dev/ttyUSB0`
- Sensor 2: `/dev/ttyUSB1`

### **Opsi 2: Direct GPIO Connection**

**Pin GPIO Raspberry Pi:**
```
Sensor 1 (Hardware UART):
- GPIO 14 (TXD) → AS608 RX
- GPIO 15 (RXD) → AS608 TX

Sensor 2 (Software UART):
- GPIO 18 (TXD) → AS608 RX  
- GPIO 19 (RXD) → AS608 TX
```

## 📁 **File yang Dibuat**

1. **`dual_sensor_config.py`** - Konfigurasi untuk dual sensor 3.3V
2. **`dual_sensor_manager.py`** - Manager untuk mengelola 2 sensor
3. **`dual_fingerprint_simple_client.py`** - Client MQTT untuk dual sensor
4. **`test_dual_sensors.py`** - Script testing untuk dual sensor

## ⚙️ **Konfigurasi**

Edit file `dual_sensor_config.py`:

```python
# Untuk USB-to-Serial adapters (RECOMMENDED)
SENSORS = {
    "sensor_1": {
        "port": "/dev/ttyUSB0",  # Port sensor pertama
        "baudrate": 57600,
        "device_id": "AS608_001",
        "enabled": True,
        "description": "Main Entry Sensor",
        "voltage": "3.3V"  # AS608 running on 3.3V
    },
    "sensor_2": {
        "port": "/dev/ttyUSB1",  # Port sensor kedua
        "baudrate": 57600,
        "device_id": "AS608_002", 
        "enabled": True,
        "description": "Secondary Entry Sensor",
        "voltage": "3.3V"  # AS608 running on 3.3V
    }
}
```

## 🚀 **Instalasi**

### **1. Install Dependencies**
```bash
# Install Python packages
pip3 install pyserial paho-mqtt adafruit-circuitpython-fingerprint

# Install system packages
sudo apt update
sudo apt install -y python3-pip python3-serial
```

### **2. Set Permission**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Set permission for serial ports
sudo chmod 666 /dev/ttyUSB* /dev/ttyACM* /dev/serial*

# Logout and login again for group changes to take effect
```

### **3. Test Koneksi**
```bash
# Test dual sensor setup
python3 test_dual_sensors.py
```

### **4. Jalankan Dual Sensor System**
```bash
# Run dual sensor client
python3 dual_fingerprint_simple_client.py
```

## 📊 **Format Data MQTT**

Data yang dikirim ke MQTT broker sama dengan sistem existing, ditambah informasi sensor:

```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-01T12:00:00",
    "status": "Match",
    "fingerprint_id": 1,
    "device_id": "AS608_001",
    "sensor_id": "sensor_1",
    "sensor_description": "Main Entry Sensor",
    "username": "John Doe",
    "confidence": 85
}
```

## 🎛️ **MQTT Commands**

### **Add User**
```json
{
    "fingerprint_id": 1,
    "user_name": "John Doe",
    "sensor_id": "sensor_1"
}
```

### **Import Users**
```json
{
    "users": [
        {
            "fingerprint_id": 1,
            "user_name": "User 1",
            "sensor_id": "sensor_1",
            "template_data": "base64_encoded_template"
        }
    ]
}
```

### **Export Users**
```json
{}
```

## 🗄️ **Database**

Sistem menggunakan SQLite database dengan tabel yang sama seperti sistem existing:

### **users table**
- `fingerprint_id` (INTEGER PRIMARY KEY)
- `user_name` (TEXT)
- `sensor_id` (TEXT) - **NEW: untuk dual sensor**
- `created_at` (TIMESTAMP)
- `last_used` (TIMESTAMP)

### **scan_logs table**
- `id` (INTEGER PRIMARY KEY)
- `sensor_id` (TEXT) - **NEW: untuk dual sensor**
- `device_id` (TEXT)
- `fingerprint_id` (INTEGER)
- `user_name` (TEXT)
- `confidence` (INTEGER)
- `status` (TEXT)
- `timestamp` (TIMESTAMP)

## 🔌 **Power Requirements untuk 3.3V**

### **AS608 Power Consumption:**
- **Voltage**: 3.3V
- **Current**: 120mA (typical)
- **Total for 2 sensors**: 240mA

### **Raspberry Pi Power:**
- **Recommended**: 5V 2A power supply
- **Sufficient for**: Pi + 2x AS608 + relay + other peripherals

## 🛠️ **Troubleshooting**

### **1. Sensor Tidak Terdeteksi**
```bash
# Cek port yang tersedia
ls /dev/ttyUSB* /dev/ttyACM* /dev/serial*

# Cek permission
sudo chmod 666 /dev/ttyUSB0 /dev/ttyUSB1

# Test koneksi manual
python3 -c "import serial; print(serial.Serial('/dev/ttyUSB0', 57600))"
```

### **2. Permission Denied**
```bash
# Tambahkan user ke group dialout
sudo usermod -a -G dialout $USER

# Atau gunakan sudo
sudo python3 dual_fingerprint_simple_client.py
```

### **3. Port Sudah Digunakan**
```bash
# Cek proses yang menggunakan port
sudo lsof /dev/ttyUSB0

# Kill proses jika diperlukan
sudo pkill -f python3
```

### **4. Sensor Tidak Merespons**
- Pastikan kabel koneksi baik
- Cek power supply 3.3V untuk AS608
- Coba restart sensor
- Cek baudrate (default: 57600)
- Pastikan AS608 menggunakan 3.3V (bukan 5V)

## 📈 **Performance**

- **Scanning Interval**: 5 detik (dapat dikonfigurasi)
- **Concurrent Scanning**: Mendukung scanning bersamaan
- **Thread Safe**: Aman untuk multiple threads
- **Memory Usage**: Minimal overhead untuk dual sensor
- **Power Consumption**: Lebih efisien dengan 3.3V

## 🔄 **Kompatibilitas dengan Sistem Existing**

| Fitur | Single Sensor | Dual Sensor (3.3V) |
|-------|---------------|-------------------|
| MQTT Format | ✅ | ✅ (Enhanced) |
| Database | ✅ | ✅ (Enhanced) |
| Relay Control | ✅ | ✅ |
| MP3 Notifications | ✅ | ✅ |
| Exit Button | ✅ | ✅ |
| User Management | ✅ | ✅ |
| Template Import/Export | ✅ | ✅ |
| GPIO Control | ✅ | ✅ |
| Voltage | 3.3V/5V | 3.3V Only |
| Level Shifter | Optional | Not Needed |

## 🎯 **Keunggulan Implementasi**

- **Backward Compatible** - Sistem existing tetap berfungsi
- **3.3V Optimized** - Didesain khusus untuk 3.3V AS608
- **No Level Shifter** - Tidak perlu level shifter
- **Same Functionality** - Semua fitur existing tetap ada
- **Enhanced Features** - Ditambah fitur dual sensor
- **Easy Migration** - Mudah migrasi dari single sensor

## 📝 **Logging**

Log disimpan di file `dual_fingerprint_mqtt.log` dengan informasi:
- Sensor connection status
- Scan results dengan sensor ID
- MQTT command handling
- Error details dengan sensor context

## 🔧 **Environment Variables**

Sistem mendukung environment variables untuk Docker deployment:

```bash
# Sensor configuration
export SENSOR_1_PORT="/dev/ttyUSB0"
export SENSOR_2_PORT="/dev/ttyUSB1"
export SENSOR_1_BAUDRATE="57600"
export SENSOR_2_BAUDRATE="57600"

# MQTT configuration
export MQTT_BROKER="103.87.67.139"
export MQTT_PORT="1883"
export STORE_ID="Store001"

# Application configuration
export CONFIDENCE_THRESHOLD="50"
export SCAN_INTERVAL="5"
export LOG_LEVEL="INFO"
```

## 🚀 **Quick Start**

1. **Connect Hardware**: AS608 (3.3V) → USB-to-Serial → Pi
2. **Edit Config**: Update ports in `dual_sensor_config.py`
3. **Test Setup**: `python3 test_dual_sensors.py`
4. **Run System**: `python3 dual_fingerprint_simple_client.py`

Sistem dual sensor 3.3V siap digunakan dengan performa optimal dan tidak memerlukan level shifter!
