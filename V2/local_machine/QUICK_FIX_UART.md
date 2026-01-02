# ⚡ Quick Fix: UART ttyAMA2 dan ttyAMA3 Tidak Muncul

## 🎯 Masalah Utama

**Mapping UART yang BENAR:**
- `uart3` → `/dev/ttyAMA2` ⚠️ **Bukan ttyAMA3!**
- `uart4` → `/dev/ttyAMA3` ✅

Jadi jika Anda butuh `ttyAMA2` dan `ttyAMA3`, Anda perlu mengaktifkan **uart3** dan **uart4**.

## ✅ Solusi Cepat (3 Langkah)

### **Langkah 1: Edit `/boot/config.txt`**

```bash
sudo nano /boot/config.txt
```

**Tambahkan atau perbaiki:**
```ini
enable_uart=1
dtoverlay=uart3,pins_4_5
dtoverlay=uart4,pins_8_9
```

**PENTING:** 
- `uart3` akan membuat `/dev/ttyAMA2`
- `uart4` akan membuat `/dev/ttyAMA3`
- Parameter `pins_4_5` dan `pins_8_9` menentukan GPIO pins yang digunakan

### **Langkah 2: Reboot**

```bash
sudo reboot
```

### **Langkah 3: Verifikasi**

Setelah reboot, jalankan:
```bash
cd local_machine
chmod +x check_uart_ports.sh
./check_uart_ports.sh
```

Atau cek manual:
```bash
ls -la /dev/ttyAMA*
```

Seharusnya muncul:
- `/dev/ttyAMA0` (uart0 - default)
- `/dev/ttyAMA1` (jika uart2 aktif)
- `/dev/ttyAMA2` (uart3) ✅
- `/dev/ttyAMA3` (uart4) ✅

## 🔧 Jika Masih Tidak Muncul

### **Opsi 1: Coba GPIO Pins Lain**

Edit `/boot/config.txt`:
```ini
enable_uart=1
dtoverlay=uart3,ctsrts
dtoverlay=uart4,ctsrts
```

### **Opsi 2: Cek Konflik Serial Console**

```bash
cat /boot/cmdline.txt
```

Jika ada `console=serial0` atau `console=ttyAMA0`, **HAPUS** bagian tersebut.

### **Opsi 3: Gunakan USB-to-Serial (Paling Mudah)**

Jika UART GPIO bermasalah, gunakan USB-to-Serial adapter:
- Port: `/dev/ttyUSB0`, `/dev/ttyUSB1`, dll
- Tidak perlu konfigurasi GPIO
- Edit `config.py`:
  ```python
  env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/ttyUSB0,/dev/ttyUSB1")
  ```

## 📝 Update config.py

Setelah port muncul, pastikan `config.py` menggunakan port yang benar:

```python
# Untuk 2 sensor dengan uart0 dan uart4
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/serial0,/dev/ttyAMA3")

# Atau untuk uart3 dan uart4
env_ports = os.getenv("FINGERPRINT_PORTS", "/dev/ttyAMA2,/dev/ttyAMA3")
```

## 📚 Mapping Lengkap

| UART | Device | GPIO Pins (contoh) | Keterangan |
|------|--------|-------------------|------------|
| uart0 | `/dev/ttyAMA0`<br>`/dev/serial0` | GPIO 14-15 | Default UART |
| uart1 | `/dev/ttyS0`<br>`/dev/serial1` | GPIO 14-15 | Mini UART (Bluetooth) |
| uart2 | `/dev/ttyAMA1` | GPIO 0-1 atau 2-3 | Perlu dtoverlay |
| uart3 | `/dev/ttyAMA2` ⚠️ | GPIO 4-5 atau 8-9 | Perlu dtoverlay |
| uart4 | `/dev/ttyAMA3` ✅ | GPIO 8-9 atau 12-13 | Perlu dtoverlay |
| uart5 | `/dev/ttyAMA4` | GPIO 12-13 atau 14-15 | Perlu dtoverlay |

## 🚀 Test

Setelah konfigurasi, test dengan:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

Script akan otomatis mendeteksi port yang tersedia jika port di config tidak ada.

## 📖 Dokumentasi Lengkap

Lihat `SOLUSI_UART_TIDAK_MUNCUL.md` untuk troubleshooting detail.


