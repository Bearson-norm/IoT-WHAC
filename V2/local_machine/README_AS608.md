# Program Pembaca Sensor AS608

Program sederhana untuk membaca sensor fingerprint AS608 yang terhubung ke Raspberry Pi melalui `/dev/ttyAMA3`.

## Instalasi

Pastikan library yang diperlukan sudah terinstall:

```bash
pip3 install adafruit-circuitpython-fingerprint pyserial
```

Atau install dari requirements.txt:
```bash
pip3 install -r requirements.txt
```

## Penggunaan

### 1. Pastikan port tersedia

Cek apakah port `/dev/ttyAMA3` ada:
```bash
ls -l /dev/ttyAMA3
```

Jika port tidak ada, cek port yang tersedia:
```bash
ls -l /dev/ttyAMA*
```

### 2. Pastikan user memiliki akses

Jika mendapat error permission denied, tambahkan user ke grup dialout:
```bash
sudo usermod -a -G dialout $USER
```

Atau jalankan dengan sudo:
```bash
sudo python3 read_as608_sensor.py
```

### 3. Jalankan program

```bash
python3 read_as608_sensor.py
```

## Fitur

Program ini memiliki 3 mode:

1. **Scan Sekali (Single Scan)**: Scan satu kali dan cari match
2. **Scan Kontinyu (Continuous Scan)**: Scan terus menerus sampai dihentikan (Ctrl+C)
3. **Info Sensor**: Menampilkan informasi sensor (jumlah template, parameter sistem, dll)

## Contoh Output

```
==================================================
PROGRAM PEMBACA SENSOR AS608
Port: /dev/ttyAMA3
==================================================
Menghubungkan ke sensor pada /dev/ttyAMA3 (percobaan 1/3)...
✓ Sensor terhubung dengan sukses!
  Jumlah template tersimpan: 5

==================================================
INFORMASI SENSOR
==================================================
Jumlah template tersimpan: 5
Status register: 0
System ID: 1
Library size: 256
Security level: 3
Device address: 0xFFFFFFFF
Packet size: 128
Baud rate: 6
==================================================

Pilih mode:
  1. Scan sekali (single scan)
  2. Scan kontinyu (continuous scan)
  3. Hanya tampilkan info sensor
```

## Troubleshooting

### Port tidak ditemukan
- Pastikan sensor terhubung dengan benar
- Cek koneksi kabel
- Cek apakah port benar dengan: `ls -l /dev/ttyAMA*`

### Permission denied
- Jalankan dengan sudo: `sudo python3 read_as608_sensor.py`
- Atau tambahkan user ke grup dialout: `sudo usermod -a -G dialout $USER`

### Sensor tidak merespon
- Pastikan sensor sudah menyala (LED menyala)
- Cek koneksi kabel (TX, RX, VCC, GND)
- Cek baud rate (default: 57600)
- Coba restart sensor atau Raspberry Pi

### Tidak ada match ditemukan
- Pastikan sudah ada template yang tersimpan di sensor
- Coba scan dengan jari yang sudah terdaftar
- Pastikan jari ditempatkan dengan benar di sensor

## Mengubah Port

Jika sensor terhubung ke port lain, edit file `read_as608_sensor.py` dan ubah:

```python
SENSOR_PORT = "/dev/ttyAMA3"  # Ganti dengan port Anda
```

Port umum:
- `/dev/ttyAMA0` - UART0 (GPIO 14/15)
- `/dev/ttyAMA1` - UART1 (GPIO 0/1)
- `/dev/ttyAMA2` - UART2 (GPIO 4/5)
- `/dev/ttyAMA3` - UART3 (GPIO 8/9)
- `/dev/ttyUSB0` - USB to Serial adapter
- `/dev/serial0` - Alias untuk UART0



