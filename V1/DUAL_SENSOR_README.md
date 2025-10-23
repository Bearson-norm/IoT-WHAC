# Dual AS608 Fingerprint Sensor System

Sistem ini memungkinkan penggunaan 2 sensor AS608 dengan fungsi yang sama seperti sistem single sensor yang sudah ada.

## Fitur

- ✅ **Dual Sensor Support**: Mendukung 2 sensor AS608 secara bersamaan
- ✅ **Same Functionality**: Semua fungsi yang ada tetap sama (scanning, enrollment, MQTT)
- ✅ **Concurrent Scanning**: Scanning dapat dilakukan secara bersamaan pada kedua sensor
- ✅ **Thread Safe**: Aman untuk digunakan dengan multiple threads
- ✅ **MQTT Integration**: Terintegrasi dengan sistem MQTT yang sudah ada
- ✅ **Database Support**: Menyimpan data user dan log scan
- ✅ **Auto Detection**: Auto-detect port sensor (jika diperlukan)

## File yang Dibuat

1. **`dual_sensor_config.py`** - Konfigurasi untuk dual sensor
2. **`dual_sensor_manager.py`** - Manager untuk mengelola 2 sensor
3. **`dual_fingerprint_mqtt_client.py`** - Client MQTT untuk dual sensor
4. **`test_dual_sensors.py`** - Script untuk testing dual sensor

## Konfigurasi Hardware

### Opsi 1: USB-to-Serial Adapters (Recommended)
```
Sensor 1: /dev/ttyUSB0
Sensor 2: /dev/ttyUSB1
```

### Opsi 2: Mixed USB/ACM Ports
```
Sensor 1: /dev/ttyUSB0
Sensor 2: /dev/ttyACM0
```

### Opsi 3: Built-in Serial Ports (dengan level shifter)
```
Sensor 1: /dev/serial0
Sensor 2: /dev/serial1
```

## Konfigurasi

Edit file `dual_sensor_config.py` sesuai dengan setup hardware Anda:

```python
SENSORS = {
    "sensor_1": {
        "port": "/dev/ttyUSB0",  # Port sensor pertama
        "baudrate": 57600,
        "device_id": "AS608_001",
        "enabled": True,
        "description": "Main Entry Sensor"
    },
    "sensor_2": {
        "port": "/dev/ttyUSB1",  # Port sensor kedua
        "baudrate": 57600,
        "device_id": "AS608_002", 
        "enabled": True,
        "description": "Secondary Entry Sensor"
    }
}
```

## Instalasi

1. **Install Dependencies**:
```bash
pip install pyserial paho-mqtt
```

2. **Test Koneksi Sensor**:
```bash
python3 test_dual_sensors.py
```

3. **Jalankan Dual Sensor Client**:
```bash
python3 dual_fingerprint_mqtt_client.py
```

## Penggunaan

### 1. Testing Sensor
```bash
python3 test_dual_sensors.py
```
Script ini akan:
- Test koneksi ke kedua sensor
- Test scanning fingerprint
- Test concurrent scanning
- Monitor status sensor

### 2. Menjalankan Dual Sensor System
```bash
python3 dual_fingerprint_mqtt_client.py
```

### 3. MQTT Commands

#### Add User
```json
{
    "fingerprint_id": 1,
    "user_name": "John Doe",
    "sensor_id": "sensor_1"
}
```

#### Import Users
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

#### Export Users
```json
{}
```

## Format Data MQTT

### Scan Result
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

## Database

Sistem menggunakan SQLite database dengan tabel:

### users
- `fingerprint_id` (INTEGER PRIMARY KEY)
- `user_name` (TEXT)
- `sensor_id` (TEXT)
- `created_at` (TIMESTAMP)
- `last_used` (TIMESTAMP)

### scan_logs
- `id` (INTEGER PRIMARY KEY)
- `sensor_id` (TEXT)
- `device_id` (TEXT)
- `fingerprint_id` (INTEGER)
- `user_name` (TEXT)
- `confidence` (INTEGER)
- `status` (TEXT)
- `timestamp` (TIMESTAMP)

## Troubleshooting

### 1. Sensor Tidak Terdeteksi
```bash
# Cek port yang tersedia
ls /dev/ttyUSB* /dev/ttyACM*

# Cek permission
sudo chmod 666 /dev/ttyUSB0 /dev/ttyUSB1
```

### 2. Permission Denied
```bash
# Tambahkan user ke group dialout
sudo usermod -a -G dialout $USER

# Atau gunakan sudo
sudo python3 dual_fingerprint_mqtt_client.py
```

### 3. Port Sudah Digunakan
```bash
# Cek proses yang menggunakan port
sudo lsof /dev/ttyUSB0

# Kill proses jika diperlukan
sudo pkill -f python3
```

### 4. Sensor Tidak Merespons
- Pastikan kabel koneksi baik
- Cek power supply sensor
- Coba restart sensor
- Cek baudrate (default: 57600)

## Perbedaan dengan Single Sensor

| Fitur | Single Sensor | Dual Sensor |
|-------|---------------|-------------|
| Jumlah Sensor | 1 | 2 |
| Port | `/dev/ttyUSB0` | `/dev/ttyUSB0`, `/dev/ttyUSB1` |
| Device ID | `AS608_001` | `AS608_001`, `AS608_002` |
| Concurrent Scanning | ❌ | ✅ |
| Sensor Selection | N/A | `sensor_id` parameter |
| Database | Single sensor | Multi sensor support |

## Kompatibilitas

- ✅ **Raspberry Pi 4**: Tested
- ✅ **Ubuntu/Debian**: Tested
- ✅ **Python 3.6+**: Required
- ✅ **AS608 Sensor**: Compatible
- ✅ **MQTT Broker**: Compatible dengan sistem existing

## Logging

Log disimpan di file `dual_fingerprint_mqtt.log` dengan level yang dapat dikonfigurasi:
- DEBUG: Detail informasi
- INFO: Informasi umum
- WARNING: Peringatan
- ERROR: Error

## Performance

- **Scanning Interval**: 2 detik (dapat dikonfigurasi)
- **Concurrent Scanning**: Mendukung scanning bersamaan
- **Thread Safe**: Aman untuk multiple threads
- **Memory Usage**: Minimal overhead untuk dual sensor

## Support

Jika mengalami masalah:
1. Jalankan `test_dual_sensors.py` untuk diagnosis
2. Cek log file untuk error details
3. Pastikan konfigurasi port benar
4. Verifikasi koneksi hardware
