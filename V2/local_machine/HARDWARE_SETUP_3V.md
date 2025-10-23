# Hardware Setup untuk AS608 3.3V

## 🔌 **Koneksi Hardware AS608 3.3V**

### **Pin AS608 Sensor:**
```
AS608 Pinout:
┌─────────────────┐
│ 1. VCC (3.3V)   │ ← Power Supply
│ 2. GND          │ ← Ground
│ 3. TX           │ ← Data Out (ke Pi RX)
│ 4. RX           │ ← Data In (dari Pi TX)
│ 5. WAK          │ ← Wake Up (optional)
│ 6. RST          │ ← Reset (optional)
└─────────────────┘
```

## 🔧 **Opsi 1: USB-to-Serial Adapters (RECOMMENDED)**

### **Hardware yang Dibutuhkan:**
- 2x AS608 Fingerprint Sensor (3.3V)
- 2x USB-to-Serial TTL Converter (CP2102, CH340, atau FT232)
- Kabel jumper
- Raspberry Pi 4

### **Koneksi:**
```
AS608 Sensor 1:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ AS608 (3.3V)    │    │ USB-to-Serial   │    │ Raspberry Pi    │
│                 │    │ TTL Converter   │    │                 │
│ VCC → 3.3V      │◄──►│ 3.3V            │    │                 │
│ GND → GND       │◄──►│ GND              │    │                 │
│ TX  → RX        │◄──►│ RX               │    │                 │
│ RX  → TX        │◄──►│ TX               │    │                 │
└─────────────────┘    └─────────────────┘    │ USB Port 1      │
                                              │ → /dev/ttyUSB0  │
                                              └─────────────────┘

AS608 Sensor 2:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ AS608 (3.3V)    │    │ USB-to-Serial   │    │ Raspberry Pi    │
│                 │    │ TTL Converter   │    │                 │
│ VCC → 3.3V      │◄──►│ 3.3V            │    │                 │
│ GND → GND       │◄──►│ GND              │    │                 │
│ TX  → RX        │◄──►│ RX               │    │                 │
│ RX  → TX        │◄──►│ TX               │    │                 │
└─────────────────┘    └─────────────────┘    │ USB Port 2      │
                                              │ → /dev/ttyUSB1  │
                                              └─────────────────┘
```

### **Keunggulan USB-to-Serial:**
- ✅ Tidak menggunakan GPIO Pi
- ✅ Plug and play
- ✅ Tidak perlu level shifter
- ✅ Mudah troubleshooting
- ✅ Port terdeteksi otomatis

## 🔧 **Opsi 2: Direct GPIO Connection**

### **Hardware yang Dibutuhkan:**
- 2x AS608 Fingerprint Sensor (3.3V)
- Kabel jumper
- Raspberry Pi 4

### **Koneksi GPIO:**
```
Raspberry Pi GPIO Layout:
┌─────────────────────────────────────────┐
│ 3.3V  │ 5V   │ GPIO2 │ 5V   │ GPIO3 │ GND │ GPIO4 │ GPIO14 │ GND │ GPIO15 │ GPIO17 │ GPIO18 │ GND │ GPIO27 │ GPIO22 │ 3.3V │ GPIO23 │ GPIO24 │ GND │ GPIO25 │ GPIO8  │ GPIO7  │ GPIO1 │ GND │ GPIO12 │ GND │ GPIO16 │ GPIO20 │ GPIO21 │ GND │ GPIO26 │ GPIO19 │ GPIO13 │ GND │ GPIO6  │ GPIO5  │ GND │ GPIO11 │ GPIO10 │ GPIO9  │ GND │ GPIO0  │ GPIO1  │ GPIO2  │ 3.3V │ GPIO3  │ GPIO4  │ GND │ GPIO5  │
└─────────────────────────────────────────┘

Sensor 1 (Hardware UART):
AS608 VCC → Pi 3.3V
AS608 GND → Pi GND
AS608 TX  → Pi GPIO15 (RXD)
AS608 RX  → Pi GPIO14 (TXD)

Sensor 2 (Software UART):
AS608 VCC → Pi 3.3V
AS608 GND → Pi GND
AS608 TX  → Pi GPIO19 (Software RX)
AS608 RX  → Pi GPIO18 (Software TX)
```

### **Konfigurasi GPIO:**
```bash
# Enable UART
sudo raspi-config
# Navigate to: Interfacing Options → Serial
# Enable: Would you like a login shell to be accessible over serial? → No
# Enable: Would you like the serial port hardware to be enabled? → Yes

# Edit /boot/config.txt
sudo nano /boot/config.txt
# Add or uncomment:
enable_uart=1
dtoverlay=uart1

# Reboot
sudo reboot
```

## ⚡ **Power Requirements**

### **AS608 3.3V Power Consumption:**
- **Voltage**: 3.3V ± 0.3V
- **Current**: 120mA (typical), 150mA (max)
- **Power**: 396mW (typical), 495mW (max)

### **Total Power untuk 2 Sensor:**
- **Current**: 240mA (typical), 300mA (max)
- **Power**: 792mW (typical), 990mW (max)

### **Raspberry Pi Power Supply:**
- **Recommended**: 5V 2A (10W)
- **Sufficient for**: Pi + 2x AS608 + relay + other peripherals

## 🔍 **Troubleshooting Hardware**

### **1. Sensor Tidak Terdeteksi**
```bash
# Cek koneksi power
# AS608 VCC harus 3.3V (bukan 5V!)

# Cek koneksi data
# AS608 TX → Pi RX
# AS608 RX → Pi TX

# Cek port
ls /dev/ttyUSB* /dev/ttyACM* /dev/serial*
```

### **2. Sensor Tidak Merespons**
- Pastikan AS608 menggunakan 3.3V (bukan 5V)
- Cek koneksi kabel
- Cek baudrate (default: 57600)
- Restart sensor

### **3. Permission Denied**
```bash
# Set permission
sudo chmod 666 /dev/ttyUSB0 /dev/ttyUSB1

# Add user to dialout group
sudo usermod -a -G dialout $USER
# Logout and login again
```

### **4. Port Sudah Digunakan**
```bash
# Cek proses
sudo lsof /dev/ttyUSB0

# Kill proses
sudo pkill -f python3
```

## 📊 **Voltage Level Compatibility**

### **3.3V AS608 (Recommended):**
```
AS608 Logic Levels:
- VCC: 3.3V
- VIL: 0.8V (max)
- VIH: 2.0V (min)
- VOL: 0.4V (max)
- VOH: 2.4V (min)

Raspberry Pi GPIO Levels:
- VCC: 3.3V
- VIL: 0.8V (max)
- VIH: 1.3V (min)
- VOL: 0.4V (max)
- VOH: 2.4V (min)

✅ COMPATIBLE - No level shifter needed!
```

### **5V AS608 (Not Recommended):**
```
AS608 Logic Levels:
- VCC: 5V
- VIL: 1.5V (max)
- VIH: 3.5V (min)
- VOL: 0.4V (max)
- VOH: 4.0V (min)

❌ INCOMPATIBLE - Level shifter required!
```

## 🛠️ **Tools untuk Testing**

### **1. Test Serial Connection:**
```bash
# Test port availability
python3 -c "import serial; print(serial.Serial('/dev/ttyUSB0', 57600))"

# Test communication
python3 -c "
import serial
import time
ser = serial.Serial('/dev/ttyUSB0', 57600, timeout=1)
time.sleep(0.5)
print('Port opened:', ser.is_open)
ser.close()
"
```

### **2. Test AS608 Sensor:**
```bash
# Run test script
python3 test_dual_sensors.py

# Check sensor response
python3 -c "
import serial
import adafruit_fingerprint
uart = serial.Serial('/dev/ttyUSB0', 57600, timeout=2)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
print('Templates:', finger.template_count)
uart.close()
"
```

## 📋 **Checklist Hardware Setup**

### **Pre-Installation:**
- [ ] AS608 sensors configured for 3.3V
- [ ] USB-to-Serial adapters (if using USB method)
- [ ] Kabel jumper
- [ ] Raspberry Pi 4
- [ ] Power supply 5V 2A

### **Installation:**
- [ ] Connect AS608 VCC to 3.3V (not 5V!)
- [ ] Connect AS608 GND to GND
- [ ] Connect AS608 TX to converter RX
- [ ] Connect AS608 RX to converter TX
- [ ] Connect converter to Pi USB port
- [ ] Power on all devices

### **Testing:**
- [ ] Check port detection: `ls /dev/ttyUSB*`
- [ ] Test connection: `python3 test_dual_sensors.py`
- [ ] Verify sensor response
- [ ] Check template count
- [ ] Test fingerprint scanning

### **Final Setup:**
- [ ] Configure ports in `dual_sensor_config.py`
- [ ] Run dual sensor client
- [ ] Test MQTT communication
- [ ] Verify database logging
- [ ] Test user enrollment

## 🎯 **Best Practices**

1. **Always use 3.3V AS608** - No level shifter needed
2. **Use USB-to-Serial adapters** - Easier setup and troubleshooting
3. **Check power supply** - Ensure stable 3.3V for AS608
4. **Use quality cables** - Avoid loose connections
5. **Test incrementally** - Test one sensor at a time
6. **Keep logs** - Monitor system logs for issues
7. **Backup database** - Regular backup of fingerprint data

Dengan setup 3.3V ini, sistem dual sensor akan berjalan dengan optimal tanpa memerlukan level shifter!
