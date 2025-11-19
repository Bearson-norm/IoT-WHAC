# Troubleshooting: Port Serial Konflik / Tidak Bisa Dibaca

## Masalah
Sensor di `/dev/ttyAMA3` tidak bisa dibaca dengan error:
```
✗ Error: Failed to read data from sensor
```

Padahal sebelumnya bisa, dan sekarang ada 2 sensor yang terhubung.

## Penyebab Umum

### 1. **Port Sedang Digunakan oleh Program Lain** (Paling Sering)

Jika `fingerprint_multi_client.py` masih berjalan, port akan terkunci dan tidak bisa digunakan program lain.

**Cek apakah port sedang digunakan:**
```bash
lsof /dev/ttyAMA3
```

**Atau gunakan program helper:**
```bash
python3 check_port_usage.py
```

**Solusi:**
```bash
# Hentikan semua program fingerprint
sudo pkill -f fingerprint_multi_client
sudo pkill -f fingerprint

# Atau kill semua python3
sudo killall python3

# Atau cari PID spesifik dan kill
lsof /dev/ttyAMA3
sudo kill <PID>
```

### 2. **Multiple Program Menggunakan Port yang Sama**

Tidak bisa 2 program menggunakan port serial yang sama secara bersamaan.

**Solusi:**
- Hentikan program lain sebelum menjalankan program baru
- Pastikan hanya 1 program yang menggunakan port pada satu waktu

### 3. **Kabel/Koneksi Bermasalah**

**Cek:**
- Kabel TX/RX tidak terbalik
- Koneksi VCC dan GND benar
- Sensor menyala (LED menyala)

**Test:**
```bash
# Cek apakah port bisa dibuka
python3 -c "import serial; s=serial.Serial('/dev/ttyAMA3', 57600, timeout=1); print('OK'); s.close()"
```

### 4. **Baud Rate Tidak Sesuai**

Default baud rate AS608 adalah 57600. Pastikan semua program menggunakan baud rate yang sama.

**Cek di config.py:**
```python
BAUD_RATE = 57600
```

### 5. **Permission Issue**

**Cek permission:**
```bash
ls -l /dev/ttyAMA3
```

**Output seharusnya:**
```
crw-rw---- 1 root dialout 204, 67 Nov 18 19:16 /dev/ttyAMA3
```

**Jika permission denied:**
```bash
# Tambahkan user ke grup dialout
sudo usermod -a -G dialout $USER

# Logout dan login lagi, atau:
newgrp dialout

# Atau jalankan dengan sudo
sudo python3 read_as608_sensor.py
```

## Langkah Troubleshooting

### Step 1: Cek Port Usage
```bash
python3 check_port_usage.py
```

### Step 2: Hentikan Program yang Menggunakan Port
```bash
# Cek proses
ps aux | grep fingerprint

# Kill proses
sudo pkill -f fingerprint_multi_client
```

### Step 3: Cek Port Tersedia
```bash
ls -l /dev/ttyAMA3
```

### Step 4: Test Koneksi
```bash
python3 read_as608_sensor.py
```

### Step 5: Jika Masih Error, Cek Sensor
```bash
# Cek apakah sensor benar-benar terhubung
# Coba dengan port lain atau sensor lain
```

## Best Practices

### 1. **Selalu Hentikan Program Sebelum Menjalankan Program Baru**

```bash
# Sebelum menjalankan fingerprint_multi_client.py
sudo pkill -f fingerprint

# Tunggu beberapa detik
sleep 2

# Baru jalankan program baru
python3 fingerprint_multi_client.py
```

### 2. **Gunakan Script untuk Memastikan Port Bebas**

Buat file `ensure_port_free.sh`:
```bash
#!/bin/bash
echo "Menghentikan proses yang menggunakan port serial..."
sudo pkill -f fingerprint_multi_client
sleep 2
echo "Port seharusnya sudah bebas"
```

### 3. **Cek Port Sebelum Menjalankan Program**

Tambahkan di awal program untuk cek apakah port sedang digunakan.

## Contoh Workflow yang Benar

### Menjalankan Multi-Sensor Client:
```bash
# 1. Pastikan tidak ada program lain yang berjalan
sudo pkill -f fingerprint

# 2. Tunggu beberapa detik
sleep 2

# 3. Jalankan multi-sensor client
python3 fingerprint_multi_client.py
```

### Test Sensor Individual:
```bash
# 1. Hentikan multi-sensor client (Ctrl+C atau pkill)
sudo pkill -f fingerprint_multi_client

# 2. Tunggu beberapa detik
sleep 2

# 3. Test sensor individual
python3 read_as608_sensor.py
```

## Script Helper

Gunakan `check_port_usage.py` untuk cek status port:
```bash
python3 check_port_usage.py
```

Program ini akan:
- Cek apakah port sedang digunakan
- Tampilkan proses yang menggunakan port
- Berikan solusi untuk menghentikan proses

## Catatan Penting

1. **Serial port adalah exclusive resource** - hanya 1 program bisa menggunakan port pada satu waktu
2. **Jika `fingerprint_multi_client.py` berjalan**, port akan terkunci untuk program lain
3. **Selalu hentikan program lama sebelum menjalankan program baru**
4. **Gunakan `check_port_usage.py` untuk troubleshooting**


