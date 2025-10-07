# Server-Side Fingerprint Template Management

## Overview

This system provides **centralized fingerprint template management** with automatic ID reassignment when transferring users between sensors.

## Your Use Case - Perfectly Handled! ✅

**Scenario:**
```
Sensor A: User Joe (ID 1) → Export → Server Database → Import to Sensor B (ID 2)
```

**What happens:**
1. ✅ **Sensor A** detects User Joe with ID 1
2. ✅ **Export** User Joe's template to server
3. ✅ **Server** stores template in central database
4. ✅ **Server** sends template to Sensor B with **new ID 2**
5. ✅ **User Joe** can now use Sensor B with ID 2

## System Architecture

```
┌─────────────┐    Export    ┌─────────────┐    Import    ┌─────────────┐
│  Sensor A   │ ──────────→  │   Server    │ ──────────→  │  Sensor B   │
│ User Joe    │              │  Database   │              │ User Joe    │
│ ID: 1       │              │ Templates   │              │ ID: 2       │
└─────────────┘              └─────────────┘              └─────────────┘
```

## Database Schema

### Central Users Table
```sql
users (
    user_id TEXT PRIMARY KEY,           -- Unique: "Store001_1_Joe"
    user_name TEXT NOT NULL,            -- "Joe"
    template_data BLOB NOT NULL,        -- Binary template data
    created_at TIMESTAMP,               -- When first created
    last_updated TIMESTAMP,             -- Last modification
    is_active BOOLEAN                   -- Active status
)
```

### Sensor Assignments Table
```sql
sensor_assignments (
    user_id TEXT,                       -- Reference to users
    store_id TEXT,                      -- "Store001", "Store002"
    sensor_fingerprint_id INTEGER,      -- ID on that sensor (1, 2, 3...)
    assigned_at TIMESTAMP,              -- When assigned
    is_active BOOLEAN                   -- Current assignment
)
```

## MQTT Topics

### Sensor → Server
- `WHAC/Store001/export` - Export templates from sensor
- `WHAC/Store001/add_user` - Add new user from sensor

### Server → Sensor
- `WHAC/Store001/import` - Import templates to sensor
- `WHAC/Store002/import` - Import templates to different sensor

### Server Management
- `WHAC/server/command` - Server management commands
- `WHAC/server/response` - Server responses

## Usage Examples

### 1. Export from Sensor A
```bash
# Sensor A exports all users
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/export" -m '{"request": "export_all"}'
```

**Server receives:**
```json
{
    "data": {
        "users": [
            {
                "fingerprint_id": 1,
                "user_name": "Joe",
                "template_data": "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyAhIiMkJSYnKCkqKywtLi8wMTIzNDU2Nzg5Ojs8PT4/QEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaW1xdXl9gYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CBgoOEhYaHiImKi4yNjo+QkZKTlJWWl5iZmpucnZ6foKGio6SlpqeoqaqrrK2ur7CxsrO0tba3uLm6u7y9vr/AwcLDxMXGx8jJysvMzc7P0NHS09TV1tfY2drb3N3e3+Dh4uPk5ebn6Onq6+zt7u/w8fLz9PX29/j5+vv8/f7/"
            }
        ]
    }
}
```

**Server stores:**
- `user_id`: "Store001_1_Joe"
- `user_name`: "Joe"
- `template_data`: Binary template
- `store_id`: "Store001"
- `sensor_fingerprint_id`: 1

### 2. Import to Sensor B
```bash
# Server sends to Sensor B with new ID
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store002/import" -m '{
    "users": [
        {
            "fingerprint_id": 2,
            "user_name": "Joe",
            "template_data": "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyAhIiMkJSYnKCkqKywtLi8wMTIzNDU2Nzg5Ojs8PT4/QEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaW1xdXl9gYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CBgoOEhYaHiImKi4yNjo+QkZKTlJWWl5iZmpucnZ6foKGio6SlpqeoqaqrrK2ur7CxsrO0tba3uLm6u7y9vr/AwcLDxMXGx8jJysvMzc7P0NHS09TV1tfY2drb3N3e3+Dh4uPk5ebn6Onq6+zt7u/w8fLz9PX29/j5+vv8/f7/"
        }
    ]
}'
```

**Result:**
- ✅ **User Joe** now works on Sensor B with **ID 2**
- ✅ **Same template** - identical verification
- ✅ **Server tracks** both assignments

### 3. Server Management Commands

#### List All Users
```bash
mosquitto_pub -h 103.87.67.139 -t "WHAC/server/command" -m '{
    "command": "list_users"
}'
```

**Response:**
```json
{
    "command": "list_users",
    "status": "success",
    "data": {
        "users": [
            {
                "user_id": "Store001_1_Joe",
                "user_name": "Joe",
                "current_store": "Store002",
                "current_sensor_id": 2,
                "assigned_at": "2024-01-15T10:30:45"
            }
        ],
        "total_count": 1
    }
}
```

#### Transfer User
```bash
mosquitto_pub -h 103.87.67.139 -t "WHAC/server/command" -m '{
    "command": "transfer_user",
    "user_id": "Store001_1_Joe",
    "to_store_id": "Store003"
}'
```

## Key Features

### ✅ Automatic ID Reassignment
- **Sensor A**: User Joe = ID 1
- **Sensor B**: User Joe = ID 2 (automatically assigned)
- **Sensor C**: User Joe = ID 1 (if ID 2 is taken)

### ✅ Central Template Storage
- **One template** per user in central database
- **Multiple assignments** to different sensors
- **Transfer history** tracking

### ✅ Flexible Management
- **Export all users** from any sensor
- **Import to any sensor** with new IDs
- **Transfer individual users** between sensors
- **List all users** and their locations

### ✅ Data Integrity
- **Same template** used across all sensors
- **Consistent verification** results
- **No data loss** during transfers

## Running the System

### 1. Start Server
```bash
python3 server_template_manager.py
```

### 2. Start Sensors
```bash
# On Sensor A (Store001)
python3 fingerprint_simple_client.py

# On Sensor B (Store002) 
python3 fingerprint_simple_client.py
```

### 3. Export from Sensor A
```bash
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/export" -m '{"request": "export_all"}'
```

### 4. Import to Sensor B
```bash
mosquitto_pub -h 103.87.67.139 -t "WHAC/server/command" -m '{
    "command": "transfer_user",
    "user_id": "Store001_1_Joe",
    "to_store_id": "Store002"
}'
```

## Benefits

1. **✅ Centralized Management** - All templates in one place
2. **✅ ID Flexibility** - Different IDs on different sensors
3. **✅ Easy Transfers** - Move users between locations
4. **✅ Data Consistency** - Same template everywhere
5. **✅ Scalable** - Add new sensors easily
6. **✅ Trackable** - Full transfer history

This system perfectly handles your use case: **User Joe detected on Sensor A (ID 1) → Exported to server → Imported to Sensor B (ID 2)** with full management capabilities!
