# 🔧 Cara Nonaktifkan Relay Built-in di fingerprint_multi_client.py

## 📋 Ringkasan

Jika Anda menggunakan `relay_controller_advanced.py` untuk kontrol GPIO, sebaiknya nonaktifkan relay control built-in di `fingerprint_multi_client.py` untuk menghindari konflik GPIO.

---

## ✅ Status

**Relay control sudah dinonaktifkan** di `fingerprint_multi_client.py` (baris 214-217).

---

## 🔧 Konfigurasi Saat Ini

### **fingerprint_multi_client.py**

```python
# Relay control
# DISABLED: Relay control di-nonaktifkan karena menggunakan relay_controller_advanced.py
# Jika ingin menggunakan relay built-in, uncomment baris di bawah dan comment relay_controller_advanced.py
# self.relay_pin = 18  # GPIO pin for relay
# self.setup_gpio()
self.relay_pin = None  # Disabled - using relay_controller_advanced.py instead
```

**Status**: ✅ **Sudah dinonaktifkan**

---

### **relay_controller_advanced.py**

```python
# GPIO 18 untuk relay (share dengan fingerprint_multi_client.py - perlu nonaktifkan relay di fingerprint_multi_client.py)
self.relay_pin = relay_pin or int(os.getenv('RELAY_GPIO_PIN', '18'))
self.input_pin = input_pin or int(os.getenv('INPUT_GPIO_PIN', '24'))
self.output_pin = output_pin or int(os.getenv('OUTPUT_GPIO_PIN', '25'))
```

**Status**: ✅ **Menggunakan GPIO 18**

---

## 🔄 Jika Ingin Mengaktifkan Kembali Relay Built-in

Jika suatu saat ingin menggunakan relay built-in di `fingerprint_multi_client.py`:

### **1. Aktifkan di fingerprint_multi_client.py**

Edit `local_machine/fingerprint_multi_client.py`:

```python
# Relay control
self.relay_pin = 18  # GPIO pin for relay
self.setup_gpio()
# self.relay_pin = None  # Comment baris ini
```

### **2. Nonaktifkan relay_controller_advanced.py**

Jangan jalankan `relay_controller_advanced.py` atau ubah GPIO pin-nya ke pin lain.

---

## ✅ Verifikasi

### **Cek Log fingerprint_multi_client.py**

Saat program start, seharusnya **TIDAK** ada log:
```
✓ GPIO setup complete - Relay on pin 18
```

Jika ada log tersebut, berarti relay masih aktif.

### **Cek Log relay_controller_advanced.py**

Saat program start, seharusnya ada log:
```
✓ GPIO(18) setup - Relay control (OUTPUT)
✓ GPIO(24) setup - Digital input (INPUT)
✓ GPIO(25) setup - Output control (OUTPUT)
```

---

## 🐛 Troubleshooting

### **Error: GPIO pin 18 is already in use**

**Penyebab**: Relay masih aktif di `fingerprint_multi_client.py`

**Solusi**:
1. Pastikan `self.relay_pin = None` di `fingerprint_multi_client.py`
2. Restart `fingerprint_multi_client.py`
3. Cek tidak ada proses lain yang menggunakan GPIO 18

### **Relay Tidak Berfungsi**

**Cek**:
1. `relay_controller_advanced.py` berjalan?
2. GPIO 18 terhubung dengan benar?
3. MQTT connection aktif?
4. Command grant diterima dari Web UI?

---

## 📚 File Terkait

- `local_machine/fingerprint_multi_client.py` - Relay built-in (disabled)
- `local_machine/relay_controller_advanced.py` - Relay control (active, GPIO 18)
- `local_machine/GPIO_ALLOCATION_DAN_PROGRAM.md` - Dokumentasi GPIO

---

*Dokumen ini menjelaskan cara nonaktifkan relay built-in di fingerprint_multi_client.py.*





