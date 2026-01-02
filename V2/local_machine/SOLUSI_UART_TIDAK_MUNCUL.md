# 🔧 Solusi: UART ttyAMA2 dan ttyAMA3 Tidak Muncul

## 📋 Masalah
Setelah menambahkan `dtoverlay=uart1-uart5` di `/boot/config.txt` dan reboot, device `/dev/ttyAMA2` dan `/dev/ttyAMA3` tidak muncul.

## 🔍 Diagnosis

### 1. Jalankan Script Diagnostik
```bash
cd local_machine
python3 diagnose_uart.py
```

Script ini akan mengecek:
- ✅ Konfigurasi `/boot/config.txt`
- ✅ Device tree overlays yang ter-load
- ✅ Port serial yang tersedia
- ✅ Kernel messages (dmesg)
- ✅ Mapping UART ke device
- ✅ Konflik serial console

### 2. Cek Manual

#### A. Cek Port yang Tersedia
```bash
ls -la /dev/ttyAMA*
ls -la /dev/ttyS*
ls -la /dev/serial*
```

#### B. Cek Device Tree
```bash
ls /proc/device-tree/soc/ | grep serial
```

#### C. Cek Kernel Messages
```bash
dmesg | grep -i uart
dmesg | grep -i tty
```

#### D. Cek Model Raspberry Pi
```bash
cat /proc/device-tree/model
```

## ✅ Solusi

### **Solusi 1: Tambahkan Parameter GPIO Pins**

UART tambahan di Raspberry Pi memerlukan spesifikasi GPIO pins. Edit `/boot/config.txt`:

```bash
sudo nano /boot/config.txt
```

**Untuk Raspberry Pi 4:**
```ini
# Enable UART
enable_uart=1

# UART default (uart0) - sudah ada
# dtoverlay=uart0  # Tidak perlu, sudah default

# UART 1 (mini UART) - biasanya untuk Bluetooth
# dtoverlay=uart1  # Biasanya sudah aktif

# UART 2-5 dengan GPIO pins spesifik
dtoverlay=uart2,pins_2_3
dtoverlay=uart3,pins_4_5
dtoverlay=uart4,pins_8_9
dtoverlay=uart5,pins_12_13
```

**Atau gunakan GPIO alternatif (jika pins di atas konflik):**
```ini
dtoverlay=uart2,ctsrts
dtoverlay=uart3,ctsrts
dtoverlay=uart4,ctsrts
dtoverlay=uart5,ctsrts
```

**Mapping GPIO ke UART:**
- **uart2**: GPIO 0-1 (pins 27-28) atau GPIO 2-3 (pins 3-5)
- **uart3**: GPIO 4-5 (pins 7-29) atau GPIO 8-9 (pins 24-21)
- **uart4**: GPIO 8-9 (pins 24-21) atau GPIO 12-13 (pins 32-33)
- **uart5**: GPIO 12-13 (pins 32-33) atau GPIO 14-15 (pins 8-10)

### **Solusi 2: Gunakan Mapping yang Benar**

Setelah overlay aktif, mapping UART ke device adalah:
- `uart0` → `/dev/ttyAMA0` atau `/dev/serial0`
- `uart1` → `/dev/ttyS0` atau `/dev/serial1`
- `uart2` → `/dev/ttyAMA1`
- `uart3` → `/dev/ttyAMA2` ⚠️ **Bukan ttyAMA3!**
- `uart4` → `/dev/ttyAMA3` ✅
- `uart5` → `/dev/ttyAMA4`

**Jadi jika Anda butuh ttyAMA2 dan ttyAMA3:**
- `ttyAMA2` = `uart3`
- `ttyAMA3` = `uart4`

**Edit config.py:**
```python
# Untuk 2 sensor dengan uart3 dan uart4
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA2,/dev/ttyAMA3")
```

### **Solusi 3: Verifikasi Konfigurasi**

Setelah edit `/boot/config.txt`, pastikan:

1. **Reboot Raspberry Pi:**
   ```bash
   sudo reboot
   ```

2. **Setelah reboot, cek port:**
   ```bash
   ls -la /dev/ttyAMA*
   ```

3. **Cek apakah overlay ter-load:**
   ```bash
   dmesg | grep -i uart
   ```

4. **Test koneksi ke port:**
   ```bash
   python3 -c "import serial; s=serial.Serial('/dev/ttyAMA2', 57600); print('OK')"
   ```

### **Solusi 4: Alternatif - Gunakan USB-to-Serial Adapter**

Jika UART GPIO bermasalah, gunakan USB-to-Serial adapter yang lebih mudah:

1. **Sambungkan AS608 ke USB-to-Serial adapter**
2. **Port akan muncul sebagai `/dev/ttyUSB0`, `/dev/ttyUSB1`, dll**
3. **Tidak perlu konfigurasi GPIO**

**Edit config.py:**
```python
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/ttyUSB0,/dev/ttyUSB1")
```

### **Solusi 5: Cek Konflik Serial Console**

Serial console bisa mengkonflik dengan UART. Cek `/boot/cmdline.txt`:

```bash
cat /boot/cmdline.txt
```

Jika ada `console=serial0` atau `console=ttyAMA0`, **HAPUS** atau **COMMENT**:
```bash
sudo nano /boot/cmdline.txt
```

Hapus bagian `console=serial0,115200` atau `console=ttyAMA0,115200`

## 📝 Contoh Konfigurasi Lengkap

### **Untuk 2 Sensor dengan UART GPIO:**

**1. Edit `/boot/config.txt`:**
```ini
enable_uart=1
dtoverlay=uart3,pins_4_5
dtoverlay=uart4,pins_8_9
```

**2. Reboot:**
```bash
sudo reboot
```

**3. Edit `config.py`:**
```python
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA2")
```

Atau jika ingin menggunakan uart3 dan uart4:
```python
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/ttyAMA2,/dev/ttyAMA3")
```

**4. Test:**
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

## 🐛 Troubleshooting

### **Masalah: Port masih tidak muncul setelah reboot**

1. **Cek apakah overlay benar-benar ter-load:**
   ```bash
   vcgencmd get_config int | grep uart
   ```

2. **Cek dmesg untuk error:**
   ```bash
   dmesg | grep -i error
   dmesg | tail -50
   ```

3. **Cek apakah GPIO pins tidak konflik:**
   ```bash
   gpio readall  # Jika wiringpi terinstall
   ```

4. **Coba dengan parameter berbeda:**
   ```ini
   dtoverlay=uart3,ctsrts
   dtoverlay=uart4,ctsrts
   ```

### **Masalah: Permission denied saat akses port**

Tambahkan user ke group dialout:
```bash
sudo usermod -a -G dialout $USER
# Logout dan login lagi
```

Atau gunakan sudo:
```bash
sudo python3 fingerprint_multi_client.py
```

### **Masalah: Port muncul tapi tidak bisa connect**

1. **Cek apakah port benar-benar UART (bukan device lain):**
   ```bash
   ls -la /dev/ttyAMA2
   ```

2. **Cek apakah ada proses lain yang menggunakan port:**
   ```bash
   sudo lsof /dev/ttyAMA2
   ```

3. **Test dengan baudrate yang benar:**
   ```python
   import serial
   s = serial.Serial('/dev/ttyAMA2', 57600, timeout=2)
   print("Connected!")
   s.close()
   ```

## 📚 Referensi

- [Raspberry Pi UART Documentation](https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts)
- [Device Tree Overlays](https://github.com/raspberrypi/firmware/blob/master/boot/overlays/README)
- GPIO Pinout: https://pinout.xyz

## ✅ Checklist

- [ ] `/boot/config.txt` sudah di-edit dengan benar
- [ ] Sudah reboot setelah edit config.txt
- [ ] Port muncul di `/dev/ttyAMA*`
- [ ] Tidak ada konflik serial console
- [ ] User sudah ditambahkan ke group `dialout`
- [ ] `config.py` sudah di-update dengan port yang benar
- [ ] Test koneksi berhasil


