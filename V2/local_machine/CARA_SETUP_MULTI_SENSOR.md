# Cara Setup Multi-Sensor AS608

## Masalah
Program hanya mendeteksi 1 sensor karena `FINGERPRINT_PORTS` tidak dikonfigurasi. Log menunjukkan:
```
🔧 Using single sensor from FINGERPRINT_PORT
📌 Sensor 1: AS608_001 -> /dev/serial0
Total Sensors: 1
```

## Solusi: Konfigurasi Multi-Sensor

Ada 3 cara untuk menambahkan sensor kedua di `/dev/ttyAMA3`:

### **Cara 1: Environment Variable (Paling Cepat)**

Jalankan program dengan environment variable:

```bash
FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA3" python3 fingerprint_multi_client.py
```

Atau set dulu lalu jalankan:
```bash
export FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA3"
python3 fingerprint_multi_client.py
```

**Keuntungan:** Tidak perlu edit file, cepat untuk testing

### **Cara 2: Edit config.py (Permanent)**

Edit file `config.py` dan ubah baris 24-26:

**Sebelum:**
```python
FINGERPRINT_PORTS = os.getenv("FINGERPRINT_PORTS", "").split(",") if os.getenv("FINGERPRINT_PORTS") else []
# Filter out empty strings
FINGERPRINT_PORTS = [p.strip() for p in FINGERPRINT_PORTS if p.strip()]
```

**Sesudah:**
```python
FINGERPRINT_PORTS = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA3").split(",") if os.getenv("FINGERPRINT_PORTS") else ["/dev/serial0", "/dev/ttyAMA3"]
# Filter out empty strings
FINGERPRINT_PORTS = [p.strip() for p in FINGERPRINT_PORTS if p.strip()]
```

**Keuntungan:** Konfigurasi permanent, tidak perlu set env setiap kali

### **Cara 3: Menggunakan Script Helper**

Jalankan script setup:
```bash
chmod +x setup_multi_sensor.sh
./setup_multi_sensor.sh
```

Script akan:
- Memeriksa port yang tersedia
- Memberikan opsi konfigurasi
- Membantu setup otomatis

## Verifikasi Setup

Setelah konfigurasi, jalankan program dan cek log:

**Seharusnya muncul:**
```
🔧 Configuring 2 sensors from FINGERPRINT_PORTS
📌 Sensor 1: AS608_001 -> /dev/serial0
📌 Sensor 2: AS608_002 -> /dev/ttyAMA3
Total Sensors: 2
✅ 2/2 sensors connected successfully
```

## Troubleshooting

### Sensor kedua tidak terhubung

1. **Cek port tersedia:**
   ```bash
   ls -l /dev/ttyAMA3
   ```

2. **Cek permission:**
   ```bash
   ls -l /dev/ttyAMA3
   ```
   Pastikan user ada di grup `dialout`:
   ```bash
   groups
   ```
   Jika tidak ada, tambahkan:
   ```bash
   sudo usermod -a -G dialout $USER
   # Logout dan login lagi
   ```

3. **Cek apakah sensor benar-benar terhubung:**
   ```bash
   python3 read_as608_sensor.py
   ```
   (Edit port di file tersebut ke `/dev/ttyAMA3`)

4. **Cek log untuk error:**
   Program akan menampilkan warning jika port tidak ditemukan:
   ```
   ⚠️  Port /dev/ttyAMA3 does not exist for AS608_002
   ```

### Port berbeda

Jika sensor kedua menggunakan port lain (misalnya `/dev/ttyUSB0`), ubah konfigurasi:

```bash
FINGERPRINT_PORTS="/dev/serial0,/dev/ttyUSB0" python3 fingerprint_multi_client.py
```

### Hanya ingin 1 sensor

Jika hanya ingin menggunakan 1 sensor, jangan set `FINGERPRINT_PORTS` atau set ke empty string:

```bash
FINGERPRINT_PORTS="" python3 fingerprint_multi_client.py
```

## Contoh Konfigurasi Lengkap

### 2 Sensor (serial0 + ttyAMA3)
```bash
FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA3" python3 fingerprint_multi_client.py
```

### 3 Sensor
```bash
FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA1,/dev/ttyAMA3" python3 fingerprint_multi_client.py
```

### 4 Sensor
```bash
FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA1,/dev/ttyAMA2,/dev/ttyAMA3" python3 fingerprint_multi_client.py
```

## Catatan Penting

1. **Port harus dipisahkan dengan koma** (tanpa spasi atau dengan spasi, akan di-trim)
2. **Setiap sensor akan mendapat device_id unik:**
   - Sensor 1: `AS608_001`
   - Sensor 2: `AS608_002`
   - Sensor 3: `AS608_003`
   - dst.

3. **Setiap sensor akan scan secara parallel** dalam thread terpisah

4. **Data dari setiap sensor akan dikirim dengan device_id yang berbeda** ke MQTT


