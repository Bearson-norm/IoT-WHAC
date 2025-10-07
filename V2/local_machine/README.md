# Local Machine (Raspberry Pi) Files

This folder contains all the files that run on your **Raspberry Pi 4** with the AS608 fingerprint sensor.

## 🎯 Main Program (Recommended)

### **`fingerprint_simple_client.py`** ⭐
**This is the main program you should use!**

- ✅ **Standby fingerprint scanning**
- ✅ **Simple JSON format** as requested
- ✅ **MQTT command handling** (add/import/export users)
- ✅ **Template transfer support**
- ✅ **Thread-safe command interruption**
- ✅ **Auto-detect sensor port** (no manual configuration needed)
- ✅ **Relay control integration**

**Usage:**
```bash
python3 fingerprint_simple_client.py
```

## 🔍 Auto-Detection Features

### **Automatic Port Detection:**
- ✅ **Scans all available ports** automatically
- ✅ **Tests each port** for AS608 fingerprint sensor
- ✅ **No manual configuration** required
- ✅ **Cross-platform support** (Linux, Windows, macOS)
- ✅ **Fallback to config** if auto-detection fails

### **Supported Ports:**
- **Linux/Unix**: `/dev/ttyUSB*`, `/dev/ttyACM*`, `/dev/ttyS*`
- **Windows**: `COM1-COM8` and detected USB serial ports
- **macOS**: `/dev/tty.usbserial*`, `/dev/tty.usbmodem*`

### **Detection Process:**
1. **Scans system** for available serial ports
2. **Tests each port** with AS608 communication
3. **Validates sensor** by reading templates
4. **Uses first valid** AS608 sensor found
5. **Falls back** to configured port if needed

## 📁 Other Programs

### **`fingerprint_hybrid_client.py`**
- Advanced version with local SQLite database
- Comprehensive logging and user management
- More complex but feature-rich

### **`fingerprint_raw_client.py`**
- Sends raw fingerprint data or compact hashes
- Multiple data modes (raw_image, hash, checksum, template)
- For special use cases

### **`fingerprint_manager.py`**
- Standalone fingerprint management tool
- Backup/restore functionality
- Template management

### **`user_manager.py`**
- User profile management utility
- View logs, statistics, export data
- Interactive menu system

### **`auto_backup.py`**
- Automatic backup/restore on startup
- Systemd service integration
- Ensures data persistence

## ⚙️ Configuration Files

### **`config.py`**
**Main configuration file** - Edit this for your setup:
```python
STORE_ID = "Store001"
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"
FINGERPRINT_PORT = "/dev/ttyUSB0"
CONFIDENCE_THRESHOLD = 50
```

### **`config_raw.py`**
Configuration for raw data client

### **`requirements.txt`**
Python dependencies:
```bash
pip3 install -r requirements.txt
```

## 🔧 Setup Files

### **`existing.py`**
Original fingerprint enrollment tool with interactive menu

### **`fingerprint-backup.service`**
Systemd service file for automatic backup on startup

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Edit configuration:**
   ```bash
   nano config.py
   ```

3. **Run main program:**
   ```bash
   python3 fingerprint_simple_client.py
   ```

## 📡 MQTT Topics Used

- **`WHAC/Store001/in`** - Send scan results
- **`WHAC/Store001/add_user`** - Add new user
- **`WHAC/Store001/import`** - Import users
- **`WHAC/Store001/export`** - Export users

## 🎯 What This Does

1. **Connects to AS608 sensor** via serial port
2. **Connects to MQTT broker** for communication
3. **Scans fingerprints continuously** in standby mode
4. **Sends scan results** in simple JSON format
5. **Handles MQTT commands** for user management
6. **Supports template transfer** between sensors

## 📊 JSON Format Sent

```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T10:30:45.123456",
    "status": "Match",
    "fingerprint_id": 1,
    "device_id": "AS608_001",
    "username": "John Doe",
    "confidence": 85
}
```

This is the **local machine side** of your fingerprint system!
