# Fingerprint MQTT System

A complete fingerprint management system with AS608 sensor, MQTT communication, and server-side template management.

## 📁 Project Structure

```
├── local_machine/          # Files for Raspberry Pi 4
│   ├── fingerprint_simple_client.py  ⭐ Main program
│   ├── config.py                    # Configuration
│   ├── requirements.txt             # Dependencies
│   └── README.md                    # Local setup guide
│
├── server/                 # Files for Server
│   ├── server_template_manager.py   ⭐ Main server program
│   ├── SERVER_MANAGEMENT_GUIDE.md   # Server guide
│   └── README.md                    # Server setup guide
│
└── README.md               # This file
```

## 🎯 Your Use Case - Perfectly Handled!

**Scenario:**
```
Sensor A: User Joe (ID 1) → Export → Server → Import to Sensor B (ID 2)
```

**What happens:**
1. ✅ **Sensor A** detects User Joe with ID 1
2. ✅ **Exports** Joe's template to server via MQTT
3. ✅ **Server** stores template in central database
4. ✅ **Server** automatically assigns new ID 2 for Sensor B
5. ✅ **Sends** Joe's template to Sensor B with ID 2
6. ✅ **User Joe** can now use Sensor B with ID 2

## 🚀 Quick Start

### 1. Local Machine (Raspberry Pi 4)

```bash
cd local_machine/
pip3 install -r requirements.txt
nano config.py  # Edit your settings
python3 fingerprint_simple_client.py
```

### 2. Server

```bash
cd server/
python3 server_template_manager.py
```

## 📡 System Architecture

```
┌─────────────┐    Export    ┌─────────────┐    Import    ┌─────────────┐
│  Sensor A   │ ──────────→  │   Server    │ ──────────→  │  Sensor B   │
│ User Joe    │              │  Database   │              │ User Joe    │
│ ID: 1       │              │ Templates   │              │ ID: 2       │
└─────────────┘              └─────────────┘              └─────────────┘
```

## 🔧 Configuration

### MQTT Broker
- **IP**: 103.87.67.139
- **Port**: 1883
- **Topics**: WHAC/Store001/in, WHAC/Store001/export, etc.

### AS608 Sensor
- **Port**: /dev/ttyUSB0 (configurable)
- **Baud Rate**: 57600
- **Capacity**: 128 templates

## 📊 JSON Format

### Scan Results
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T10:30:45.123456",
    "action": "access_granted",
    "fingerprint_id": 1,
    "device_id": "AS608_001"
}
```

### Template Transfer
```json
{
    "fingerprint_id": 1,
    "user_name": "Joe",
    "template_data": "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyAhIiMkJSYnKCkqKywtLi8wMTIzNDU2Nzg5Ojs8PT4/QEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaW1xdXl9gYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CBgoOEhYaHiImKi4yNjo+QkZKTlJWWl5iZmpucnZ6foKGio6SlpqeoqaqrrK2ur7CxsrO0tba3uLm6u7y9vr/AwcLDxMXGx8jJysvMzc7P0NHS09TV1tfY2drb3N3e3+Dh4uPk5ebn6Onq6+zt7u/w8fLz9PX29/j5+vv8/f7/"
}
```

## 🎯 Key Features

### Local Machine (Raspberry Pi)
- ✅ **Standby fingerprint scanning**
- ✅ **MQTT communication**
- ✅ **Template export/import**
- ✅ **Command handling**
- ✅ **Simple JSON format**

### Server
- ✅ **Central template database**
- ✅ **Automatic ID reassignment**
- ✅ **User transfer between sensors**
- ✅ **Template management**
- ✅ **Transfer history tracking**

## 📁 File Organization

### `local_machine/` - Raspberry Pi Files
- **Main program**: `fingerprint_simple_client.py`
- **Configuration**: `config.py`
- **Dependencies**: `requirements.txt`
- **Documentation**: `README.md`

### `server/` - Server Files
- **Main program**: `server_template_manager.py`
- **Documentation**: `SERVER_MANAGEMENT_GUIDE.md`
- **Setup guide**: `README.md`

## 🔧 Setup Instructions

### For Local Machine (Raspberry Pi 4):
1. Go to `local_machine/` folder
2. Install dependencies: `pip3 install -r requirements.txt`
3. Edit `config.py` with your settings
4. Run: `python3 fingerprint_simple_client.py`

### For Server:
1. Go to `server/` folder
2. Run: `python3 server_template_manager.py`

## 📡 MQTT Topics

### Local Machine Sends:
- `WHAC/Store001/in` - Scan results
- `WHAC/Store001/export` - Export templates

### Server Sends:
- `WHAC/Store001/import` - Import templates
- `WHAC/server/response` - Server responses

### Server Listens:
- `WHAC/+/export` - Export from any sensor
- `WHAC/server/command` - Server commands

## 🎯 Perfect for Your Use Case

This system handles **exactly** what you need:
- **User Joe detected on Sensor A (ID 1)**
- **Exported to server via MQTT**
- **Stored in central database**
- **Imported to Sensor B with new ID 2**
- **User Joe can now use Sensor B with ID 2**

The separation into `local_machine/` and `server/` folders makes it clear what runs where!