# Cara Memeriksa Port Serial di Raspberry Pi

## 1. Menggunakan Command Line

### Cek apakah `/dev/serial0` ada:
```bash
ls -l /dev/serial0
```

**Output jika ada:**
```
lrwxrwxrwx 1 root root 5 Nov 17 19:17 /dev/serial0 -> ttyAMA0
```

**Output jika tidak ada:**
```
ls: cannot access '/dev/serial0': No such file or directory
```

### Cek dengan test command:
```bash
test -e /dev/serial0 && echo "ADA" || echo "TIDAK ADA"
```

Atau:
```bash
[ -e /dev/serial0 ] && echo "ADA" || echo "TIDAK ADA"
```

### Cek apakah itu symlink dan kemana:
```bash
readlink -f /dev/serial0
```

### List semua port serial yang tersedia:
```bash
ls -l /dev/tty* | grep -E 'tty(USB|ACM|AMA|S|serial)'
```

Atau lebih spesifik:
```bash
ls -l /dev/ttyAMA* /dev/serial* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

## 2. Menggunakan Python

### Program yang sudah dibuat:
```bash
python3 check_serial_ports.py
```

Program ini akan menampilkan:
- Status `/dev/serial0` dan `/dev/serial1`
- Semua port serial yang tersedia
- Informasi symlink (jika ada)
- Permission dan grup user

### Script Python sederhana:
```python
import os

port = "/dev/serial0"
if os.path.exists(port):
    print(f"✓ {port} ADA")
    if os.path.islink(port):
        real_path = os.readlink(port)
        print(f"  → Symlink ke: {real_path}")
else:
    print(f"✗ {port} TIDAK ADA")
```

## 3. Menggunakan Python Serial Tools

```python
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"Port: {port.device}, Description: {port.description}")
```

## 4. Memahami `/dev/serial0` dan `/dev/serial1`

Di Raspberry Pi:
- `/dev/serial0` biasanya adalah **symlink** ke `/dev/ttyAMA0` (UART utama)
- `/dev/serial1` biasanya adalah **symlink** ke `/dev/ttyAMA1` (UART sekunder)

### Cek symlink:
```bash
ls -la /dev/serial*
```

### Cek kemana symlink mengarah:
```bash
readlink /dev/serial0
readlink /dev/serial1
```

## 5. Troubleshooting

### Jika `/dev/serial0` tidak ada:

1. **Cek apakah UART diaktifkan:**
   ```bash
   sudo raspi-config
   ```
   Pilih: `Interface Options` → `Serial Port` → Enable

2. **Cek konfigurasi boot:**
   ```bash
   cat /boot/config.txt | grep -i uart
   ```

3. **Cek apakah device tree overlay aktif:**
   ```bash
   dtoverlay -l
   ```

4. **Cek port ttyAMA langsung:**
   ```bash
   ls -l /dev/ttyAMA*
   ```

### Jika port ada tapi tidak bisa diakses:

1. **Cek permission:**
   ```bash
   ls -l /dev/serial0
   ```

2. **Tambahkan user ke grup dialout:**
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   Lalu **logout dan login lagi**

3. **Atau gunakan sudo:**
   ```bash
   sudo python3 your_program.py
   ```

## 6. Contoh Output

### Jika port ada:
```bash
$ ls -l /dev/serial0
lrwxrwxrwx 1 root root 5 Nov 17 19:17 /dev/serial0 -> ttyAMA0
```

### Jika port tidak ada:
```bash
$ ls -l /dev/serial0
ls: cannot access '/dev/serial0': No such file or directory
```

### Menggunakan program Python:
```bash
$ python3 check_serial_ports.py
============================================================
PEMERIKSAAN PORT SERIAL
============================================================

1. Pemeriksaan /dev/serial0:
------------------------------------------------------------
✓ /dev/serial0 ADA
  → Ini adalah symlink ke: ttyAMA0
  → Path absolut: /dev/ttyAMA0

2. Pemeriksaan /dev/serial1:
------------------------------------------------------------
✓ /dev/serial1 ADA
  → Ini adalah symlink ke: ttyAMA1
  → Path absolut: /dev/ttyAMA1

3. Semua Port Serial yang Tersedia:
------------------------------------------------------------
✓ Ditemukan 4 port serial:
  • /dev/serial0 → ttyAMA0
  • /dev/serial1 → ttyAMA1
  • /dev/ttyAMA0
  • /dev/ttyAMA3
```

## 7. Quick Check Script

Buat file `cek_serial.sh`:
```bash
#!/bin/bash
echo "Cek /dev/serial0:"
if [ -e /dev/serial0 ]; then
    echo "  ✓ ADA"
    if [ -L /dev/serial0 ]; then
        echo "  → Symlink ke: $(readlink /dev/serial0)"
    fi
else
    echo "  ✗ TIDAK ADA"
fi

echo ""
echo "Cek /dev/serial1:"
if [ -e /dev/serial1 ]; then
    echo "  ✓ ADA"
    if [ -L /dev/serial1 ]; then
        echo "  → Symlink ke: $(readlink /dev/serial1)"
    fi
else
    echo "  ✗ TIDAK ADA"
fi

echo ""
echo "Port ttyAMA yang tersedia:"
ls -1 /dev/ttyAMA* 2>/dev/null || echo "  Tidak ada"
```

Jalankan:
```bash
chmod +x cek_serial.sh
./cek_serial.sh
```


