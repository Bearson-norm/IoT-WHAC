# Server Components

This folder contains server-side components for the WHAC Fingerprint System.

## 🎯 Main Components

### **`mqtt_data_processor.py`** ⭐
**This is the main server component that bridges local machines and web UI!**

- ✅ **Receives fingerprint scan data** from local machines via MQTT
- ✅ **Processes and logs data** to PostgreSQL database
- ✅ **Real-time data processing** for web UI
- ✅ **User information lookup** and validation
- ✅ **Status updates** via MQTT

**Usage:**
```bash
python3 mqtt_data_processor.py
```

### **`server_template_manager.py`**
- Central template management system
- User ID reassignment between sensors
- Template transfer coordination
- Multi-sensor management

### **`central_fingerprints.db`**
- SQLite database for template management
- User profile storage
- Template metadata

## 🔄 Data Flow

```
Local Machine → MQTT → Server → PostgreSQL → Web UI
```

1. **Local Machine** scans fingerprint and sends to MQTT
2. **Server** receives data via `mqtt_data_processor.py`
3. **Server** processes and logs to PostgreSQL
4. **Web UI** displays data and sends real-time notifications

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

### **2. Setup Database:**
```bash
# Make sure PostgreSQL is running
# Run the database setup from web_ui folder
cd ../web_ui/
psql -U postgres -d whac_master -f database_setup.sql
```

### **3. Run Server:**
```bash
cd server/
python3 mqtt_data_processor.py
```

## 📈 Monitoring

### **Logs:**
- **MQTT connection** status
- **Data processing** events
- **Database operations** results
- **Error handling** and recovery

### **Status Indicators:**
- **Connected** to MQTT broker
- **Subscribed** to scan topics
- **Database** connectivity
- **Processing** statistics

## 🔧 Integration

### **With Local Machine:**
- Receives scan data from `fingerprint_simple_client.py`
- Processes JSON format data
- Logs to PostgreSQL database

### **With Web UI:**
- Provides real-time data for dashboard
- Enables popup notifications
- Supports admin management

## 🎯 What This Solves

### **Missing Communication:**
- ✅ **Bridges** local machine and web UI
- ✅ **Processes** MQTT data in real-time
- ✅ **Logs** all scan data to database
- ✅ **Enables** real-time notifications

### **Data Flow:**
- ✅ **Local Machine** → MQTT → **Server** → PostgreSQL → **Web UI**
- ✅ **Complete integration** between all components
- ✅ **Real-time processing** and notifications
- ✅ **Persistent data storage** and retrieval

This is the **missing link** that connects your local machine fingerprint scanner to the web UI dashboard! 🎉