# GPIO Pin Mapping untuk Dual AS608 dengan Relay

## ⚠️ **Konflik Pin yang Harus Dihindari**

**GPIO18 sudah digunakan untuk RELAY CONTROL!**
- GPIO18 = Relay Control (sudah digunakan)
- GPIO19 = Exit Button (jika digunakan)

## 🔌 **Pin Mapping yang Benar untuk Dual AS608**

### **Sensor 1 (Hardware UART - Primary):**
```
AS608 Pin    → Raspberry Pi 4 GPIO
VCC (3.3V)   → Pin 1 (3.3V)
GND          → Pin 6 (GND)
TX           → Pin 10 (GPIO15/RXD) - Hardware UART RX
RX           → Pin 8 (GPIO14/TXD)  - Hardware UART TX
```

### **Sensor 2 (Software UART - Secondary):**
```
AS608 Pin    → Raspberry Pi 4 GPIO
VCC (3.3V)   → Pin 1 (3.3V)
GND          → Pin 14 (GND)
TX           → Pin 38 (GPIO20) - Software UART RX
RX           → Pin 40 (GPIO21) - Software UART TX
```

## 📋 **Pin Layout Raspberry Pi 4**

```
┌─────────────────────────────────────────┐
│ 3.3V  │ 5V   │ GPIO2 │ 5V   │ GPIO3 │ GND │
│ GPIO4 │ GPIO14│ GPIO15│ GPIO17│ GPIO18│ GND │ ← GPIO18 = RELAY!
│ GPIO27│ GPIO22│ 3.3V  │ GPIO23│ GPIO24│ GND │
│ GPIO25│ GPIO8 │ GPIO7 │ GPIO1 │ GND   │ GPIO12│
│ GND   │ GPIO16│ GPIO20│ GPIO21│ GND   │ GPIO26│ ← GPIO20,21 = Sensor 2
│ GPIO19│ GPIO13│ GPIO6 │ GPIO5 │ GND   │ GPIO11│ ← GPIO19 = Exit Button
│ GPIO10│ GPIO9 │ GND   │ GPIO0 │ GPIO1 │ GPIO2 │
└─────────────────────────────────────────┘

Pin yang digunakan:
✅ GPIO14 (Pin 8)  = Sensor 1 TX (Hardware UART)
✅ GPIO15 (Pin 10) = Sensor 1 RX (Hardware UART)
❌ GPIO18 (Pin 12) = RELAY CONTROL (KONFLIK!)
❌ GPIO19 (Pin 35) = Exit Button (KONFLIK!)
✅ GPIO20 (Pin 38) = Sensor 2 TX (Software UART)
✅ GPIO21 (Pin 40) = Sensor 2 RX (Software UART)
```

## 🔧 **Konfigurasi yang Benar**

### **1. Hardware UART (Sensor 1):**
```python
# Port: /dev/serial0 (Hardware UART)
# TX: GPIO14, RX: GPIO15
# Tidak ada konflik dengan relay
```

### **2. Software UART (Sensor 2):**
```python
# Port: /dev/serial1 (Software UART)
# TX: GPIO20, RX: GPIO21
# Tidak ada konflik dengan relay (GPIO18)
```

## ⚙️ **Konfigurasi Sistem**

### **File: dual_sensor_config.py**
```python
SENSORS = {
    "sensor_1": {
        "port": "/dev/serial0",  # Hardware UART (GPIO14/15)
        "baudrate": 57600,
        "device_id": "AS608_001",
        "enabled": True,
        "description": "Main Entry Sensor",
        "voltage": "3.3V"
    },
    "sensor_2": {
        "port": "/dev/serial1",  # Software UART (GPIO20/21)
        "baudrate": 57600,
        "device_id": "AS608_002", 
        "enabled": True,
        "description": "Secondary Entry Sensor",
        "voltage": "3.3V"
    }
}

# Relay tetap menggunakan GPIO18
RELAY_CONFIG = {
    "enabled": True,
    "pin": 18,  # GPIO18 - Relay control
    "access_duration": 10
}
```

## 🚫 **Pin yang Tidak Bisa Digunakan**

### **Pin yang Sudah Digunakan:**
- **GPIO18** = Relay Control (KONFLIK!)
- **GPIO19** = Exit Button (jika digunakan)
- **GPIO14/15** = Hardware UART (Sensor 1)

### **Pin Alternatif untuk Sensor 2:**
- **GPIO20/21** = Software UART (RECOMMENDED)
- **GPIO22/23** = Alternatif lain
- **GPIO24/25** = Alternatif lain

## 🔄 **Solusi Alternatif**

### **Opsi 1: USB-to-Serial Adapters (RECOMMENDED)**
```
Sensor 1: AS608 → USB-to-Serial 1 → USB Port Pi → /dev/ttyUSB0
Sensor 2: AS608 → USB-to-Serial 2 → USB Port Pi → /dev/ttyUSB1
```
**Keunggulan:**
- ✅ Tidak menggunakan GPIO tambahan
- ✅ Tidak ada konflik dengan relay
- ✅ Plug and play
- ✅ Mudah troubleshooting

### **Opsi 2: GPIO dengan Pin Berbeda**
```
Sensor 1: GPIO14/15 (Hardware UART)
Sensor 2: GPIO20/21 (Software UART)
Relay: GPIO18 (tetap sama)
```

## 📊 **Power Distribution**

### **Pin 3.3V yang Tersedia:**
- **Pin 1** = 3.3V (untuk AS608)
- **Pin 17** = 3.3V (untuk AS608 kedua)

### **Pin GND yang Tersedia:**
- **Pin 6** = GND (untuk AS608)
- **Pin 9** = GND (untuk AS608 kedua)
- **Pin 14** = GND (untuk AS608 kedua)
- **Pin 20** = GND (untuk AS608 kedua)

## 🛠️ **Troubleshooting**

### **1. Konflik Pin:**
```bash
# Cek pin yang digunakan
gpio readall

# Cek proses yang menggunakan GPIO
sudo cat /sys/kernel/debug/gpio
```

### **2. UART Configuration:**
```bash
# Enable UART
sudo raspi-config
# Interfacing Options → Serial
# Enable serial port hardware

# Edit /boot/config.txt
sudo nano /boot/config.txt
# Add:
enable_uart=1
dtoverlay=uart1
```

### **3. Test Koneksi:**
```bash
# Test hardware UART
python3 -c "import serial; print(serial.Serial('/dev/serial0', 57600))"

# Test software UART
python3 -c "import serial; print(serial.Serial('/dev/serial1', 57600))"
```

## 🎯 **Rekomendasi Final**

**Untuk menghindari konflik dengan relay (GPIO18), gunakan:**

1. **USB-to-Serial Adapters** (PALING MUDAH)
2. **GPIO20/21 untuk Sensor 2** (jika ingin GPIO direct)
3. **Pastikan tidak ada konflik dengan pin yang sudah digunakan**

Dengan konfigurasi ini, relay tetap menggunakan GPIO18 dan sensor kedua menggunakan GPIO20/21 tanpa konflik!
