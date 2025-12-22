# 🚪 Panduan Sensor Pintu (Door Sensor)

## 📋 Deskripsi

Program `door_sensor.py` digunakan untuk mendeteksi status pintu (tertutup/terbuka) menggunakan sensor magnetik yang terhubung ke GPIO Raspberry Pi 4. Status pintu dikirim secara real-time ke Web UI melalui MQTT.

## 🔌 Koneksi Hardware

### Sensor Pintu Magnetik (Magnetic Door Sensor)

Sensor pintu magnetik biasanya memiliki 3 terminal:
- **NC (Normally Closed)**: Terminal yang terhubung saat pintu tertutup
- **COM (Common)**: Terminal common/ground
- **NO (Normally Open)**: Terminal yang terhubung saat pintu terbuka

### Wiring ke Raspberry Pi 4

```
Sensor Pintu          Raspberry Pi 4
-----------          ----------------
COM (Common)    →     GND (Ground)
NC/NO          →     GPIO Pin (default: GPIO 24)
                      + Pull-down resistor (internal)
```

**Catatan:**
- GPIO 24 adalah default, dapat diubah melalui environment variable `DOOR_SENSOR_PIN`
- Raspberry Pi menggunakan 3.3V logic level
- Sensor harus memberikan output 3.3V saat aktif

### Konfigurasi Sensor

Program mendukung 2 jenis konfigurasi sensor:

1. **NC (Normally Closed)** - Default
   - Pintu tertutup: GPIO membaca HIGH (3.3V)
   - Pintu terbuka: GPIO membaca LOW (0V)

2. **NO (Normally Open)**
   - Pintu tertutup: GPIO membaca LOW (0V)
   - Pintu terbuka: GPIO membaca HIGH (3.3V)

## ⚙️ Konfigurasi

### Environment Variables

Tambahkan ke file `.env` atau set sebelum menjalankan program:

```bash
# GPIO Pin untuk sensor pintu (default: 24)
DOOR_SENSOR_PIN=24

# Tipe sensor: NC atau NO (default: NC)
DOOR_SENSOR_TYPE=NC

# MQTT Configuration (dari config.py)
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
STORE_ID=Store001
```

### File Config

Konfigurasi MQTT menggunakan file `config.py` yang sama dengan fingerprint client.

## 🚀 Cara Menjalankan

### 1. Install Dependencies

```bash
cd local_machine
pip3 install -r requirements.txt
```

### 2. Jalankan Program

```bash
python3 door_sensor.py
```

### 3. Jalankan sebagai Service (Opsional)

Buat file service `/etc/systemd/system/door-sensor.service`:

```ini
[Unit]
Description=WHAC Door Sensor Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/local_machine
ExecStart=/usr/bin/python3 /path/to/local_machine/door_sensor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Aktifkan service:
```bash
sudo systemctl enable door-sensor.service
sudo systemctl start door-sensor.service
sudo systemctl status door-sensor.service
```

## 📡 MQTT Topics

### Published Topics

**Topic:** `WHAC/Store001/door_status`

**Format JSON:**
```json
{
    "store_id": "Store001",
    "door_status": "closed",
    "is_closed": true,
    "timestamp": "2024-01-15T10:30:45.123456",
    "sensor_pin": 24,
    "sensor_type": "NC"
}
```

**Status Values:**
- `door_status`: `"closed"` atau `"open"`
- `is_closed`: `true` atau `false`

### Update Frequency

- Status dikirim saat ada perubahan (dengan debounce 100ms)
- Heartbeat dikirim setiap 30 detik untuk memastikan koneksi aktif

## 🖥️ Integrasi dengan Web UI

Web UI secara otomatis:
1. Subscribe ke topic `WHAC/Store001/door_status`
2. Menampilkan status pintu di dashboard
3. Update real-time melalui WebSocket (SocketIO)

### Tampilan di Dashboard

Status pintu ditampilkan sebagai card di dashboard dengan:
- **Icon**: 🚪 (tertutup) atau 🚪 (terbuka)
- **Status Text**: "Tertutup" atau "Terbuka"
- **Warna**: Hijau (tertutup) atau Merah (terbuka)
- **Timestamp**: Waktu update terakhir

## 🔍 Troubleshooting

### 1. GPIO tidak terdeteksi

**Error:** `GPIO setup error`

**Solusi:**
- Pastikan RPi.GPIO terinstall: `pip3 install RPi.GPIO`
- Pastikan program dijalankan di Raspberry Pi (bukan di Windows/Mac)
- Cek permission: `sudo usermod -a -G gpio $USER`

### 2. Status tidak berubah

**Gejala:** Status pintu tidak berubah di Web UI

**Solusi:**
- Cek koneksi MQTT: `mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/door_status"`
- Cek log: `tail -f door_sensor.log`
- Verifikasi wiring sensor
- Test GPIO manual: `gpio readall` atau `raspi-gpio get 24`

### 3. Status terbalik

**Gejala:** Status tertutup/terbuka terbalik

**Solusi:**
- Ubah `DOOR_SENSOR_TYPE` dari `NC` ke `NO` atau sebaliknya
- Atau tukar koneksi NC/NO di sensor

### 4. MQTT tidak terhubung

**Error:** `Failed to connect to MQTT broker`

**Solusi:**
- Cek koneksi internet
- Verifikasi MQTT broker IP dan port
- Cek firewall settings
- Test koneksi: `mosquitto_pub -h 103.87.67.139 -t "test" -m "test"`

## 📝 Log Files

Log disimpan di: `local_machine/door_sensor.log`

Format log:
```
2024-01-15 10:30:45 - INFO - ✓ GPIO setup complete - Door sensor on pin 24
2024-01-15 10:30:45 - INFO - ✓ MQTT client connected
2024-01-15 10:30:46 - INFO - 🚪 Door state changed: CLOSED
2024-01-15 10:30:46 - INFO - ✓ Door status sent: CLOSED
```

## 🔧 Testing

### Test Manual GPIO

```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
    state = GPIO.input(24)
    print(f"GPIO 24: {'HIGH' if state else 'LOW'}")
    time.sleep(0.5)
```

### Test MQTT Publishing

```bash
# Subscribe ke topic
mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/door_status" -v

# Program akan publish status setiap kali pintu berubah
```

## 📚 Referensi

- [RPi.GPIO Documentation](https://sourceforge.net/projects/raspberry-gpio-python/)
- [MQTT Protocol](https://mqtt.org/)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)

## ⚠️ Catatan Penting

1. **Voltage Level**: Pastikan sensor menggunakan 3.3V, bukan 5V (bisa merusak GPIO)
2. **Pull Resistor**: Program menggunakan internal pull-down resistor
3. **Debounce**: Program menggunakan debounce 100ms untuk mencegah false trigger
4. **Thread Safety**: Monitoring berjalan di background thread untuk tidak blocking

## 📞 Support

Jika ada masalah, cek:
1. Log file: `door_sensor.log`
2. MQTT connection status
3. GPIO wiring dan sensor
4. Web UI console untuk error messages




