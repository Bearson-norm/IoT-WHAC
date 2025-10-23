# Dual AS608 Sensor Setup Guide

## Problem yang Ditemukan

Error yang terjadi saat menjalankan `test_dual_sensors.py`:
```
Test failed with error: cannot access local variable 'serial' where it is not associated with a value
```

## Solusi

### 1. Install Dependencies
```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

### 2. Fix Permissions
```bash
chmod +x fix_permissions.sh
./fix_permissions.sh
```

**IMPORTANT**: Log out dan log back in untuk group changes to take effect!

### 3. Test Sensor Connection
```bash
python3 test_sensors_simple.py
```

### 4. Run Dual Sensor System
```bash
chmod +x run_dual_sensors.sh
./run_dual_sensors.sh
```

## Hardware Setup

### Koneksi AS608 (3.3V)
```
AS608 VCC → USB-to-Serial 3.3V
AS608 GND → USB-to-Serial GND
AS608 TX  → USB-to-Serial RX
AS608 RX  → USB-to-Serial TX
```

### Port yang Akan Terdeteksi
- Sensor 1: `/dev/ttyUSB0`
- Sensor 2: `/dev/ttyUSB1`

## Troubleshooting

### 1. Permission Denied
```bash
sudo chmod 666 /dev/ttyUSB* /dev/ttyACM* /dev/serial*
sudo usermod -a -G dialout $USER
# Log out and log back in
```

### 2. Port Tidak Terdeteksi
```bash
# Check available ports
ls /dev/ttyUSB* /dev/ttyACM* /dev/serial*

# Test port access
python3 -c "import serial; print(serial.Serial('/dev/ttyUSB0', 57600))"
```

### 3. Import Error
```bash
pip3 install pyserial paho-mqtt adafruit-circuitpython-fingerprint RPi.GPIO
```

### 4. Sensor Tidak Merespons
- Pastikan kabel koneksi baik
- Cek power supply 3.3V untuk AS608
- Coba restart sensor
- Cek baudrate (default: 57600)
- Pastikan AS608 menggunakan 3.3V (bukan 5V)

## Keunggulan 3.3V AS608

✅ **Tidak Perlu Level Shifter** - Langsung koneksi ke Raspberry Pi  
✅ **Power Efficient** - Konsumsi daya lebih rendah  
✅ **Stable Operation** - Operasi lebih stabil  
✅ **Direct GPIO Connection** - Koneksi langsung ke GPIO Pi  

## Format Data MQTT

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

## MQTT Commands

### Add User
```json
{
    "fingerprint_id": 1,
    "user_name": "John Doe",
    "sensor_id": "sensor_1"
}
```

### Import Users
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

## Performance

- **Scanning Interval**: 5 detik (dapat dikonfigurasi)
- **Concurrent Scanning**: Mendukung scanning bersamaan
- **Thread Safe**: Aman untuk multiple threads
- **Memory Usage**: Minimal overhead untuk dual sensor
- **Power Consumption**: Lebih efisien dengan 3.3V

## Quick Start

1. **Connect Hardware**: AS608 (3.3V) → USB-to-Serial → Pi
2. **Install Dependencies**: `./install_dependencies.sh`
3. **Fix Permissions**: `./fix_permissions.sh`
4. **Log out and log back in**
5. **Test Setup**: `python3 test_sensors_simple.py`
6. **Run System**: `./run_dual_sensors.sh`

Sistem dual sensor 3.3V siap digunakan dengan performa optimal dan tidak memerlukan level shifter!
