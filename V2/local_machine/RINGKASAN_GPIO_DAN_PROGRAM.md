# 📋 Ringkasan GPIO dan Program yang Perlu Dijalankan

## 🔌 GPIO yang Digunakan di Local Machine

### **GPIO yang Sudah Digunakan**

| Program | GPIO Pin | Fungsi | Status |
|---------|----------|--------|--------|
| `fingerprint_multi_client.py` | **18** | Relay control (built-in) | ⚠️ **DISABLED** |
| `door_sensor.py` | **24** | Door sensor input | ✅ Digunakan |
| `relay_controller_advanced.py` | **18** | Relay control | ✅ **AKTIF** |
| `relay_controller_advanced.py` | **24** | Digital input (door sensor) | ✅ **AKTIF** |
| `relay_controller_advanced.py` | **25** | Output control | ✅ **AKTIF** |

**Catatan**: 
- GPIO 1, 2, 3 **TIDAK DISARANKAN** (GPIO sistem Raspberry Pi)
- GPIO 18 bisa konflik jika `fingerprint_multi_client.py` dan `relay_controller_advanced.py` sama-sama menggunakan relay
- **Solusi**: `relay_controller_advanced.py` sekarang menggunakan GPIO 23, 24, 25 (default)

---

## ✅ Rekomendasi GPIO untuk relay_controller_advanced.py

### **Default (Sudah Diupdate di Code)** ✅ **DITERAPKAN**

```python
relay_pin = 18      # GPIO 18 - Relay control (OUTPUT)
input_pin = 24      # GPIO 24 - Digital input (INPUT) - Door sensor
output_pin = 25     # GPIO 25 - Output control (OUTPUT)
```

**Keuntungan**:
- ✅ Tidak konflik dengan GPIO sistem (1, 2, 3)
- ✅ Relay built-in di fingerprint_multi_client.py sudah dinonaktifkan
- ✅ GPIO 24 bisa share dengan door_sensor.py (jika digunakan)
- ✅ GPIO yang aman dan stabil
- ✅ Menggunakan GPIO 18 yang sudah familiar

### **Custom GPIO via Environment Variable**

Jika ingin menggunakan GPIO berbeda, set environment variable:

```bash
export RELAY_GPIO_PIN=23
export INPUT_GPIO_PIN=24
export OUTPUT_GPIO_PIN=25
```

---

## 🚀 Program yang Perlu Dijalankan

### **Untuk Sistem Lengkap dengan Verifikasi dan GPIO Control**

Anda perlu menjalankan **2 program**:

#### **1. fingerprint_multi_client.py** ✅ **WAJIB**

**Fungsi**:
- Scan fingerprint dari 2 sensor (AS608_001, AS608_002)
- Kirim data scan ke MQTT topic `WHAC/Store001/in`
- Handle enrollment via MQTT
- Handle MQTT commands (add_user, import, export)

**Cara Menjalankan**:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

**Konfigurasi**:
- Edit `config.py` atau set environment variable:
  ```bash
  export FINGERPRINT_PORTS="/dev/ttyUSB0,/dev/ttyUSB1"
  # atau
  export FINGERPRINT_PORTS="/dev/serial0,/dev/ttyAMA3"
  ```

**Catatan**: 
- Relay control built-in (GPIO 18) bisa tetap aktif
- Atau nonaktifkan jika menggunakan `relay_controller_advanced.py`

---

#### **2. relay_controller_advanced.py** ✅ **WAJIB**

**Fungsi**:
- Menerima command grant/deny dari Web UI via MQTT topic `WHAC/Store001/action`
- Kontrol GPIO untuk membuka pintu:
  - GPIO(23) HIGH → Wait 5 detik → GPIO(23) LOW
- Monitor status pintu:
  - GPIO(24) membaca status pintu (LOW/HIGH)
  - GPIO(25) dikontrol berdasarkan GPIO(24)
- Log GPIO status ke database `gpio_log` table

**Cara Menjalankan**:
```bash
cd local_machine
python3 relay_controller_advanced.py
```

**Konfigurasi**:
- GPIO pin sudah default (23, 24, 25)
- Atau set environment variable untuk custom GPIO
- Pastikan database connection sudah benar

---

### **Program Opsional**

#### **3. door_sensor.py** ⚠️ **OPSIONAL**

**Fungsi**:
- Monitoring status pintu secara real-time
- Kirim status ke MQTT topic `WHAC/Store001/door_status`

**Cara Menjalankan**:
```bash
cd local_machine
python3 door_sensor.py
```

**Catatan**: 
- Bisa share GPIO 24 dengan `relay_controller_advanced.py`
- Atau gunakan GPIO berbeda jika ingin monitoring terpisah

---

## 📊 Alur Program yang Berjalan

```
┌─────────────────────────────────────┐
│  fingerprint_multi_client.py        │
│  - Scan fingerprint dari sensor     │
│  - Kirim ke MQTT: WHAC/Store001/in  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Web UI Backend (app.py)            │
│  - Terima data dari MQTT            │
│  - Verifikasi user di user_machine  │
│  - Kirim ke WebSocket                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Web UI Frontend                     │
│  - Tampilkan modal: Grant/Deny      │
│  - Atau modal: Daftar/Tidak         │
└──────────────┬──────────────────────┘
               │
               ▼ (User klik Grant)
┌─────────────────────────────────────┐
│  Web UI Backend                      │
│  - Kirim ke MQTT: WHAC/Store001/    │
│    action (command: grant)           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  relay_controller_advanced.py       │
│  - Terima command 'grant'           │
│  - GPIO(23) HIGH → Wait 5s → LOW    │
│  - Monitor GPIO(24) → Control GPIO(25)│
│  - Log ke gpio_log table            │
└─────────────────────────────────────┘
```

---

## ✅ Jawaban Singkat

### **Q: GPIO mana saja yang digunakan di local_machine sekarang?**

**A**: 
- **GPIO 18** → `fingerprint_multi_client.py` (relay control built-in)
- **GPIO 24** → `door_sensor.py` (door sensor input)
- **GPIO 23, 24, 25** → `relay_controller_advanced.py` (relay, input, output)

---

### **Q: GPIO untuk relay_controller_advanced.py baiknya dimana saja?**

**A**: 
- **GPIO 18** → Relay control (OUTPUT) ✅ **AKTIF**
- **GPIO 24** → Digital input (INPUT) - Door sensor ✅ **AKTIF**
- **GPIO 25** → Output control (OUTPUT) ✅ **AKTIF**

**Alasan**:
- GPIO 1, 2, 3 adalah GPIO sistem (tidak disarankan)
- GPIO 18 digunakan oleh relay_controller_advanced.py
- Relay built-in di fingerprint_multi_client.py sudah dinonaktifkan
- GPIO 18, 24, 25 adalah GPIO user yang aman

**Status**: ✅ Sudah diupdate di code (default: 18, 24, 25)

---

### **Q: Untuk memfungsikan keseluruhan apakah hanya perlu menjalankan program fingerprint_multi_client.py saja?**

**A**: **TIDAK**, Anda perlu menjalankan **2 program**:

1. ✅ **fingerprint_multi_client.py** - Untuk scan fingerprint dan kirim ke MQTT
2. ✅ **relay_controller_advanced.py** - Untuk kontrol GPIO (buka pintu) dari Web UI

**Alasan**:
- `fingerprint_multi_client.py` hanya scan fingerprint dan kirim data
- `relay_controller_advanced.py` yang menerima command grant/deny dari Web UI dan kontrol GPIO
- Keduanya perlu berjalan bersamaan untuk sistem lengkap

**Cara Menjalankan**:
```bash
# Terminal 1
cd local_machine
python3 fingerprint_multi_client.py

# Terminal 2
cd local_machine
python3 relay_controller_advanced.py
```

---

## 🔧 Setup Cepat

### **1. Update GPIO di relay_controller_advanced.py**

✅ **Sudah diupdate** - Default menggunakan GPIO 23, 24, 25

Jika ingin custom, set environment variable:
```bash
export RELAY_GPIO_PIN=18
export INPUT_GPIO_PIN=24
export OUTPUT_GPIO_PIN=25
```

### **2. Jalankan Program**

**Terminal 1**:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

**Terminal 2**:
```bash
cd local_machine
python3 relay_controller_advanced.py
```

### **3. Verifikasi**

1. ✅ Cek log - GPIO setup berhasil
2. ✅ Test scan fingerprint → Modal muncul di Web UI
3. ✅ Klik Grant → GPIO(23) HIGH → Wait 5s → LOW
4. ✅ Cek `gpio_log` table di database

---

## 📚 File Terkait

- `local_machine/GPIO_ALLOCATION_DAN_PROGRAM.md` - Dokumentasi lengkap
- `local_machine/relay_controller_advanced.py` - GPIO control (sudah diupdate)
- `local_machine/fingerprint_multi_client.py` - Fingerprint scanner
- `local_machine/door_sensor.py` - Door sensor monitoring (opsional)

---

*Ringkasan GPIO allocation dan program yang perlu dijalankan untuk sistem IoT-WHAC.*

