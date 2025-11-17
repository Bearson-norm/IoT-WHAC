# Server Components

This folder contains server-side components for the WHAC Fingerprint System.

## 🎯 Main Components

### **`server_template_manager.py`** ⭐
**Central template management system for multi-sensor deployments**

- ✅ **Central template management** - Stores fingerprint templates in central database
- ✅ **User ID reassignment** - Automatically assigns new IDs when transferring between sensors
- ✅ **Template transfer coordination** - Manages template transfers between sensors
- ✅ **Multi-sensor management** - Tracks which users are assigned to which sensors

**Usage:**
```bash
python3 server_template_manager.py
```

### **`central_fingerprints.db`**
- SQLite database for template management
- User profile storage
- Template metadata
- Sensor assignment tracking

## 🔄 Data Flow

```
Local Machine → MQTT → Web UI (Direct)
                ↓
         (Optional) Server Template Manager
                ↓
         Central Template Database
```

**Note:** For single or dual sensor setups (e.g., entrance/exit), the Web UI directly subscribes to MQTT topics and processes data. The `server_template_manager.py` is only needed for advanced multi-sensor deployments with template transfer requirements.

## 📊 MQTT Topics

### **Incoming (from Local Machine):**
- **`WHAC/Store001/in`** - Fingerprint scan data

### **Outgoing (to Local Machine):**
- **`WHAC/Store001/action`** - Relay control commands
- **`WHAC/Store001/status`** - Status updates

## 🗄️ Database Integration

### **PostgreSQL Tables:**
- **`log_data`** - Raw scan data
- **`log_action`** - Action logs with user info
- **`store_001`** - User profiles and template mapping

### **Data Processing:**
- **User lookup** by fingerprint ID
- **Action logging** with timestamps
- **Status tracking** and updates
- **Real-time notifications** to web UI

## ⚙️ Configuration

### **MQTT Settings:**
- **Broker**: `103.87.67.139:1883`
- **Topics**: `WHAC/Store001/*`
- **QoS**: 1 (at least once delivery)

### **Database Settings:**
- **Host**: localhost
- **Database**: whac_master
- **User**: postgres
- **Password**: Admin123

## 🚀 Setup Instructions

### **1. Install Dependencies:**
```bash
cd server/
pip install -r requirements.txt
```

### **2. Run Server Template Manager (Optional):**
```bash
cd server/
python3 server_template_manager.py
```

**Note:** Only needed if you require:
- Template transfer between multiple sensors
- Central template management
- User ID reassignment across sensors

For simple dual-sensor setups (entrance/exit), this is **not required**.

## 📈 Monitoring

### **Logs:**
- **MQTT connection** status
- **Template management** operations
- **Transfer history** tracking
- **Error handling** and recovery

### **Status Indicators:**
- **Connected** to MQTT broker
- **Subscribed** to export/import topics
- **Database** connectivity
- **Template operations** statistics

## 🔧 Integration

### **With Local Machine:**
- Receives export requests from sensors
- Stores templates in central database
- Sends import commands to sensors with new IDs

### **With Web UI:**
- Web UI directly subscribes to MQTT scan topics
- No server component needed for basic operation
- Server only needed for advanced template management

## 🎯 Use Cases

### **When to Use Server Template Manager:**
- ✅ **Multi-location deployments** - Transfer users between different locations
- ✅ **Template backup** - Central storage of all templates
- ✅ **ID management** - Automatic ID reassignment when moving users
- ✅ **Audit trail** - Track all template transfers

### **When NOT Needed:**
- ❌ **Single sensor** - Web UI handles everything directly
- ❌ **Dual sensor (entrance/exit)** - Web UI handles everything directly
- ❌ **Simple deployments** - Direct MQTT to Web UI is sufficient