# 🔌 GPIO Allocation dan Program yang Perlu Dijalankan

## 📊 GPIO yang Digunakan di Local Machine

### **1. GPIO yang Sudah Digunakan**

#### **A. fingerprint_multi_client.py**
- **GPIO 18** → Relay control (OUTPUT)
  - Digunakan untuk kontrol relay sederhana
  - **Status**: ✅ Sudah digunakan
  - **Fungsi**: Membuka pintu saat fingerprint match

#### **B. fingerprint_simple_client.py**
- **GPIO 18** → Relay control (OUTPUT)
  - **Status**: ✅ Sudah digunakan (sama dengan multi_client)
  - **Catatan**: Jangan jalankan kedua program bersamaan (akan konflik)

#### **C. door_sensor.py**
- **GPIO 24** → Door sensor input (INPUT)
  - **Status**: ✅ Sudah digunakan
  - **Fungsi**: Membaca status pintu (terbuka/tertutup)

#### **D. relay_controller_advanced.py** (Saat Ini)
- **GPIO 1** → Relay control (OUTPUT) ⚠️ **TIDAK DISARANKAN**
- **GPIO 2** → Digital input (INPUT) ⚠️ **TIDAK DISARANKAN**
- **GPIO 3** → Output control (OUTPUT) ⚠️ **TIDAK DISARANKAN**

**Masalah**: GPIO 1, 2, 3 adalah GPIO sistem yang bisa konflik dengan fungsi lain di Raspberry Pi.

---

## ✅ Rekomendasi GPIO untuk relay_controller_advanced.py

### **Rekomendasi 1: GPIO yang Aman (Recommended)** ✅ **SUDAH DITERAPKAN**

```python
relay_pin = 18      # GPIO 18 - Relay control (OUTPUT)
input_pin = 24      # GPIO 24 - Digital input (INPUT) - Door sensor
output_pin = 25     # GPIO 25 - Output control (OUTPUT)
```

**Status**: 
- ✅ GPIO 18 digunakan oleh `relay_controller_advanced.py`
- ✅ Relay control di `fingerprint_multi_client.py` **sudah dinonaktifkan**
- ✅ Tidak ada konflik GPIO

### **Rekomendasi 2: GPIO Terpisah (Jika Ingin Keduanya Berjalan)**

```python
relay_pin = 23      # GPIO 23 - Relay control (OUTPUT)
input_pin = 24      # GPIO 24 - Digital input (INPUT) - Door sensor
output_pin = 25     # GPIO 25 - Output control (OUTPUT)
```

**Keuntungan**: 
- GPIO 18 tetap untuk `fingerprint_multi_client.py`
- GPIO 23 untuk `relay_controller_advanced.py`
- Tidak ada konflik

### **Rekomendasi 3: GPIO Alternatif (Jika GPIO 24 Sudah Digunakan)**

```python
relay_pin = 23      # GPIO 23 - Relay control (OUTPUT)
input_pin = 22      # GPIO 22 - Digital input (INPUT) - Door sensor
output_pin = 27     # GPIO 27 - Output control (OUTPUT)
```

---

## 🔧 Cara Mengubah GPIO di relay_controller_advanced.py

### **Opsi 1: Ubah di Constructor (Recommended)**

Edit `local_machine/relay_controller_advanced.py`:

```python
class AdvancedRelayController:
    def __init__(self, 
                 relay_pin=23,        # ✅ Ubah dari 1 ke 23
                 input_pin=24,        # ✅ Ubah dari 2 ke 24 (atau 22)
                 output_pin=25,       # ✅ Ubah dari 3 ke 25
                 mqtt_broker="103.87.67.139", 
                 mqtt_port=1883,
                 db_config=None):
```

### **Opsi 2: Via Environment Variable**

Tambahkan di `local_machine/.env` atau environment:

```bash
RELAY_GPIO_PIN=23
INPUT_GPIO_PIN=24
OUTPUT_GPIO_PIN=25
```

Lalu update constructor:

```python
relay_pin = int(os.getenv('RELAY_GPIO_PIN', '23'))
input_pin = int(os.getenv('INPUT_GPIO_PIN', '24'))
output_pin = int(os.getenv('OUTPUT_GPIO_PIN', '25'))
```

---

## 📋 Program yang Perlu Dijalankan

### **Skenario 1: Sistem Lengkap dengan Verifikasi dan GPIO Control**

Untuk memfungsikan keseluruhan sistem dengan verifikasi user dan GPIO control, Anda perlu menjalankan **2 program**:

#### **1. fingerprint_multi_client.py** ✅ **WAJIB**
**Fungsi**:
- Scan fingerprint dari 2 sensor
- Kirim data ke MQTT
- Handle enrollment
- **Catatan**: Nonaktifkan relay control di program ini jika menggunakan `relay_controller_advanced.py`

**Cara Menjalankan**:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

**Konfigurasi**:
- Edit `config.py` atau set environment variable:
  ```bash
  export FINGERPRINT_PORTS="/dev/ttyUSB0,/dev/ttyUSB1"
  ```

#### **2. relay_controller_advanced.py** ✅ **WAJIB**
**Fungsi**:
- Menerima command grant/deny dari Web UI via MQTT
- Kontrol GPIO untuk membuka pintu
- Monitor status pintu (GPIO 2/24)
- Log GPIO status ke database

**Cara Menjalankan**:
```bash
cd local_machine
python3 relay_controller_advanced.py
```

**Konfigurasi**:
- Pastikan GPIO pin sudah diubah (lihat rekomendasi di atas)
- Pastikan database connection sudah benar

---

### **Skenario 2: Sistem Sederhana (Tanpa Verifikasi)**

Jika hanya ingin sistem sederhana tanpa verifikasi dan GPIO control advanced:

#### **1. fingerprint_multi_client.py** ✅ **WAJIB**
- Relay control sudah built-in (GPIO 18)
- Tidak perlu `relay_controller_advanced.py`

**Cara Menjalankan**:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

---

### **Skenario 3: Sistem dengan Door Sensor Monitoring**

Jika ingin monitoring status pintu secara real-time:

#### **1. fingerprint_multi_client.py** ✅ **WAJIB**
#### **2. relay_controller_advanced.py** ✅ **WAJIB**
#### **3. door_sensor.py** ⚠️ **OPSIONAL**

**Cara Menjalankan**:
```bash
# Terminal 1
cd local_machine
python3 fingerprint_multi_client.py

# Terminal 2
cd local_machine
python3 relay_controller_advanced.py

# Terminal 3 (Optional)
cd local_machine
python3 door_sensor.py
```

---

## 🔄 Alur Program yang Berjalan

### **Flow Lengkap dengan Verifikasi**:

```
1. fingerprint_multi_client.py
   ↓
   Scan fingerprint dari sensor 1 & 2
   ↓
   Kirim ke MQTT: WHAC/Store001/in
   ↓
2. Web UI Backend (app.py)
   ↓
   Verifikasi user di user_machine table
   ↓
   Kirim ke WebSocket: scan_notification dengan is_verified
   ↓
3. Web UI Frontend
   ↓
   Tampilkan modal: Grant/Deny atau Daftar/Tidak
   ↓
   User klik Grant → Kirim ke MQTT: WHAC/Store001/action
   ↓
4. relay_controller_advanced.py
   ↓
   Terima command 'grant' dari MQTT
   ↓
   GPIO(23) HIGH → Wait 5s → GPIO(23) LOW
   ↓
   Monitor GPIO(24) → Control GPIO(25)
   ↓
   Log ke gpio_log table
```

---

## ⚙️ Konfigurasi fingerprint_multi_client.py

### **Nonaktifkan Relay Control di fingerprint_multi_client.py**

Jika menggunakan `relay_controller_advanced.py`, sebaiknya nonaktifkan relay control di `fingerprint_multi_client.py` untuk menghindari konflik:

**Cara 1: Comment setup_gpio()**
```python
# Relay control
# self.relay_pin = 18  # GPIO pin for relay
# self.setup_gpio()    # Nonaktifkan jika menggunakan relay_controller_advanced.py
```

**Cara 2: Tambahkan Flag**
```python
USE_BUILTIN_RELAY = False  # Set False jika menggunakan relay_controller_advanced.py

if USE_BUILTIN_RELAY:
    self.relay_pin = 18
    self.setup_gpio()
```

---

## 📊 Ringkasan GPIO Allocation

| Program | GPIO Pin | Fungsi | Status |
|---------|----------|--------|--------|
| `fingerprint_multi_client.py` | **18** | Relay control (built-in) | ✅ Digunakan |
| `door_sensor.py` | **24** | Door sensor input | ✅ Digunakan |
| `relay_controller_advanced.py` | **23** (recommended) | Relay control | ✅ Recommended |
| `relay_controller_advanced.py` | **24** (recommended) | Door sensor input | ✅ Recommended |
| `relay_controller_advanced.py` | **25** (recommended) | Output control | ✅ Recommended |

**Catatan**: 
- GPIO 1, 2, 3 **TIDAK DISARANKAN** (GPIO sistem)
- GPIO 18 bisa konflik jika kedua program berjalan bersamaan
- **Solusi**: Gunakan GPIO 23 untuk relay_controller_advanced.py

---

## 🚀 Quick Start

### **Setup GPIO di relay_controller_advanced.py**

1. Edit `local_machine/relay_controller_advanced.py`:
   ```python
   relay_pin=23,      # Ubah dari 1
   input_pin=24,      # Ubah dari 2
   output_pin=25,     # Ubah dari 3
   ```

2. Nonaktifkan relay di `fingerprint_multi_client.py` (opsional):
   ```python
   # Comment atau hapus:
   # self.relay_pin = 18
   # self.setup_gpio()
   ```

### **Jalankan Program**

**Terminal 1 - Fingerprint Scanner**:
```bash
cd local_machine
python3 fingerprint_multi_client.py
```

**Terminal 2 - GPIO Control**:
```bash
cd local_machine
python3 relay_controller_advanced.py
```

### **Verifikasi**

1. Cek log untuk memastikan GPIO setup berhasil
2. Test scan fingerprint → Modal muncul di Web UI
3. Klik Grant → GPIO(23) harus HIGH → Wait 5s → LOW
4. Cek `gpio_log` table di database

---

## 🐛 Troubleshooting

### **GPIO Conflict Error**

**Error**: `GPIO pin X is already in use`

**Solusi**:
1. Cek program mana yang menggunakan GPIO tersebut
2. Stop program yang konflik
3. Atau ubah GPIO pin di salah satu program

### **Relay Tidak Berfungsi**

**Cek**:
1. GPIO pin sudah benar di wiring?
2. Relay module terhubung dengan benar?
3. Program `relay_controller_advanced.py` berjalan?
4. MQTT connection aktif?

### **Door Sensor Tidak Terbaca**

**Cek**:
1. GPIO 24 terhubung dengan benar?
2. Sensor menggunakan pull-up atau pull-down?
3. Program monitoring GPIO(2) berjalan?

---

## 📚 File Terkait

- `local_machine/fingerprint_multi_client.py` - Fingerprint scanner
- `local_machine/relay_controller_advanced.py` - GPIO control
- `local_machine/door_sensor.py` - Door sensor monitoring
- `local_machine/config.py` - Konfigurasi port dan MQTT

---

*Dokumen ini menjelaskan GPIO allocation dan program yang perlu dijalankan untuk sistem IoT-WHAC.*

