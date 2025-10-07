# Server Files

This folder contains all the files that run on your **server** for centralized fingerprint template management.

## 🎯 Main Program

### **`server_template_manager.py`** ⭐
**This is the main server program!**

- ✅ **Central template database** management
- ✅ **Automatic ID reassignment** when transferring between sensors
- ✅ **MQTT communication** with all sensors
- ✅ **User transfer** between different stores/sensors
- ✅ **Template storage** and retrieval

**Usage:**
```bash
python3 server_template_manager.py
```

## 📁 Documentation

### **`SERVER_MANAGEMENT_GUIDE.md`**
Complete guide for server-side management:
- Database schema
- MQTT topics
- Usage examples
- Transfer workflows

### **`TEMPLATE_TRANSFER.md`**
Technical documentation for template transfer:
- Data types comparison
- Template format details
- Security considerations

## 🏗️ System Architecture

```
┌─────────────┐    Export    ┌─────────────┐    Import    ┌─────────────┐
│  Sensor A   │ ──────────→  │   Server    │ ──────────→  │  Sensor B   │
│ User Joe    │              │  Database   │              │ User Joe    │
│ ID: 1       │              │ Templates   │              │ ID: 2       │
└─────────────┘              └─────────────┘              └─────────────┘
```

## 🎯 Your Use Case - Perfectly Handled!

**Scenario:**
```
Sensor A: User Joe (ID 1) → Export → Server → Import to Sensor B (ID 2)
```

**What happens:**
1. ✅ **Sensor A** detects User Joe with ID 1
2. ✅ **Exports** Joe's template to server
3. ✅ **Server** stores template in central database
4. ✅ **Server** sends template to Sensor B with **new ID 2**
5. ✅ **User Joe** can now use Sensor B with ID 2

## 📊 Database Schema

### Central Users Table
```sql
users (
    user_id TEXT PRIMARY KEY,           -- "Store001_1_Joe"
    user_name TEXT NOT NULL,            -- "Joe"
    template_data BLOB NOT NULL,        -- Binary template
    created_at TIMESTAMP,
    last_updated TIMESTAMP,
    is_active BOOLEAN
)
```

### Sensor Assignments Table
```sql
sensor_assignments (
    user_id TEXT,                       -- Reference to users
    store_id TEXT,                      -- "Store001", "Store002"
    sensor_fingerprint_id INTEGER,      -- ID on that sensor
    assigned_at TIMESTAMP,
    is_active BOOLEAN
)
```

## 📡 MQTT Topics

### Server Listens To:
- **`WHAC/+/export`** - Export from any sensor
- **`WHAC/+/add_user`** - Add user from any sensor
- **`WHAC/server/command`** - Server management commands

### Server Sends To:
- **`WHAC/Store001/import`** - Import to specific sensor
- **`WHAC/Store002/import`** - Import to different sensor
- **`WHAC/server/response`** - Server responses

## 🚀 Usage Examples

### 1. Start Server
```bash
python3 server_template_manager.py
```

### 2. Export from Sensor A
```bash
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/export" -m '{"request": "export_all"}'
```

### 3. Transfer User to Sensor B
```bash
mosquitto_pub -h 103.87.67.139 -t "WHAC/server/command" -m '{
    "command": "transfer_user",
    "user_id": "Store001_1_Joe",
    "to_store_id": "Store002"
}'
```

### 4. List All Users
```bash
mosquitto_pub -h 103.87.67.139 -t "WHAC/server/command" -m '{
    "command": "list_users"
}'
```

## 🔧 Server Commands

### List All Users
```json
{
    "command": "list_users"
}
```

### Transfer User
```json
{
    "command": "transfer_user",
    "user_id": "Store001_1_Joe",
    "to_store_id": "Store002"
}
```

### Get User Info
```json
{
    "command": "get_user_info",
    "user_id": "Store001_1_Joe"
}
```

## ✅ Key Features

1. **✅ Centralized Management** - All templates in one database
2. **✅ ID Reassignment** - Different IDs on different sensors
3. **✅ Easy Transfers** - Move users between locations
4. **✅ Data Consistency** - Same template everywhere
5. **✅ Scalable** - Add new sensors easily
6. **✅ Trackable** - Full transfer history

## 🎯 Perfect for Your Needs

- **Server manages everything** - Central database
- **ID reassignment** - Different IDs on different sensors
- **Template consistency** - Same template, different IDs
- **Easy transfers** - Move users between locations
- **Scalable** - Add new sensors easily
- **Trackable** - Full transfer history

This is the **server side** of your fingerprint management system!
