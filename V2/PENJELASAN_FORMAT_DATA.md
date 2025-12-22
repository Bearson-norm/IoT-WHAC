# 📊 Penjelasan Format Data dari Local Machine ke Web UI

## 🔄 Alur Komunikasi

```
Local Machine (Raspberry Pi) 
    ↓ (MQTT Protocol)
MQTT Broker (103.87.67.139:1883)
    ↓ (Subscribe)
Web UI (Flask + SocketIO)
    ↓ (WebSocket)
Browser Client (Real-time UI)
```

---

## 📤 1. DATA YANG DIKIRIM DARI LOCAL MACHINE

Local machine mengirim **3 jenis data utama** melalui MQTT:

### A. **Data Hasil Scan Fingerprint** (Paling Sering)

**Topic MQTT:** `WHAC/Store001/in`

**Format JSON:**
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T10:30:45.123456",
    "status": "Match",                    // atau "Not Match"
    "fingerprint_id": 123,                // ID user yang terdeteksi
    "device_id": "AS608_001",             // atau "AS608_002" untuk sensor kedua
    "username": "John Doe",              // (opsional, jika tersedia)
    "confidence": 85                      // (opsional, tingkat kepercayaan match)
}
```

**Contoh Real:**
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T14:23:12.456789",
    "status": "Match",
    "fingerprint_id": 5,
    "device_id": "AS608_001",
    "username": "Ahmad Rizki",
    "confidence": 92
}
```

**Kode Sumber:** `local_machine/fingerprint_simple_client.py` (baris 493-533)

---

### B. **Data Response Enrollment** (Setelah Enroll User)

**Topic MQTT:** `WHAC/Store001/add_user_response`

**Format JSON:**
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T10:30:45.123456",
    "command": "add_user",
    "status": "success",                  // atau "error"
    "data": {
        "fingerprint_id": 123,
        "user_name": "John Doe",
        "device_id": "AS608_001",
        "message": "User enrolled successfully"
    },
    "device_id": "AS608_001"
}
```

**Contoh Success:**
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T14:25:30.789012",
    "command": "add_user",
    "status": "success",
    "data": {
        "fingerprint_id": 10,
        "user_name": "Budi Santoso",
        "device_id": "AS608_001",
        "message": "User enrolled successfully"
    },
    "device_id": "AS608_001"
}
```

**Contoh Error:**
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T14:25:30.789012",
    "command": "add_user",
    "status": "error",
    "data": {
        "message": "Fingerprint already exists"
    },
    "device_id": "AS608_001"
}
```

**Kode Sumber:** `local_machine/fingerprint_simple_client.py` (baris 762-780)

---

### C. **Data Status Relay** (Setelah Relay Aktif/Nonaktif)

**Topic MQTT:** `WHAC/Store001/status`

**Format JSON:**
```json
{
    "command": "relay_on",                // atau "relay_off"
    "user_id": 123,
    "action": "granted",                  // atau "denied"
    "source": "MQTT",                     // atau "local"
    "timestamp": "2024-01-15T10:30:45.123456",
    "relay_pin": 18,
    "device_id": "AS608_001",
    "status": "completed"
}
```

**Kode Sumber:** `local_machine/fingerprint_simple_client.py` (baris 463-491)

---

## 📥 2. HANDLING DATA DI WEB UI

Web UI menerima dan memproses data melalui beberapa tahap:

### A. **Penerimaan MQTT Message**

**Lokasi:** `web_ui/app.py` (baris 242-268)

**Fungsi:** `on_mqtt_message(client, userdata, msg)`

```python
def on_mqtt_message(client, userdata, msg):
    """Handle incoming MQTT messages"""
    # 1. Decode payload dari bytes ke string
    raw_payload = msg.payload.decode()
    
    # 2. Parse JSON string menjadi Python dictionary
    payload = json.loads(raw_payload)
    
    # 3. Route ke handler berdasarkan topic
    if msg.topic == "WHAC/Store001/in":
        handle_scan_message(payload)  # Handle scan data
    elif msg.topic == "WHAC/Store001/add_user_response":
        handle_enrollment_response(payload)  # Handle enrollment
```

**Proses:**
1. ✅ Menerima raw bytes dari MQTT broker
2. ✅ Decode ke string UTF-8
3. ✅ Parse JSON menjadi Python dictionary
4. ✅ Route ke handler sesuai topic

---

### B. **Processing Scan Data**

**Lokasi:** `web_ui/app.py` (baris 270-298 dan 422-470)

#### **Step 1: Handle Scan Message**
```python
def handle_scan_message(payload):
    # 1. Process dan simpan ke database
    process_incoming_scan(payload)
    
    # 2. Format data untuk WebSocket
    scan_data = {
        'user_id': payload.get('fingerprint_id'),
        'status': payload.get('status'),
        'username': payload.get('username'),
        'confidence': payload.get('confidence'),
        'timestamp': payload.get('timestamp'),
        'store_id': payload.get('store_id'),
        'device_id': payload.get('device_id')
    }
    
    # 3. Kirim ke browser via WebSocket (background task)
    socketio.start_background_task(emit_scan_notification_task, scan_data)
```

#### **Step 2: Process Incoming Scan (Database)**
```python
def process_incoming_scan(data):
    # 1. Extract data dari payload
    store_id = data.get('store_id')
    timestamp = data.get('timestamp')
    status = data.get('status')  # "Match" atau "Not Match"
    fingerprint_id = data.get('fingerprint_id')
    device_id = data.get('device_id')
    username = data.get('username')
    confidence = data.get('confidence')
    
    # 2. Validasi data lengkap
    if not all([store_id, timestamp, status, fingerprint_id is not None, device_id]):
        logger.warning("Incomplete scan data")
        return
    
    # 3. Tentukan sensor location berdasarkan device_id
    sensor_location = None
    if device_id == 'AS608_001':
        sensor_location = 'masuk'  # Pintu Masuk
    elif device_id == 'AS608_002':
        sensor_location = 'keluar'  # Pintu Keluar
    
    # 4. Parse timestamp
    scan_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    # 5. Tentukan action berdasarkan status
    if status == "Match":
        action = "scan_detected"
        granted_denied = "pending"  # Menunggu keputusan admin
    else:
        action = "no_match"
        granted_denied = "denied"
    
    # 6. Ambil username dari database jika tidak ada di payload
    if not username:
        user_info = get_user_info_from_fingerprint(fingerprint_id)
        username = user_info.get('username') if user_info else None
    
    # 7. Simpan ke database PostgreSQL
    log_scan_to_database(
        store_id, 
        fingerprint_id, 
        scan_time, 
        action, 
        username, 
        granted_denied, 
        device_id, 
        sensor_location
    )
```

**Hasil:**
- ✅ Data tersimpan di tabel `store_001` (PostgreSQL)
- ✅ Data dikirim ke browser via WebSocket untuk real-time update

---

### C. **Processing Enrollment Response**

**Lokasi:** `web_ui/app.py` (baris 300-420)

```python
def handle_enrollment_response(payload):
    # 1. Extract data
    status = payload.get('status')  # "success" atau "error"
    data = payload.get('data', {})
    fingerprint_id = data.get('fingerprint_id')
    user_name = data.get('user_name')
    device_id = data.get('device_id', 'AS608_001')
    
    # 2. Tentukan sensor location
    sensor_location = None
    if device_id == 'AS608_001':
        sensor_location = 'masuk'
    elif device_id == 'AS608_002':
        sensor_location = 'keluar'
    
    # 3. Jika success, simpan ke database
    if status == 'success' and fingerprint_id and user_name:
        # Insert ke PostgreSQL dengan composite key (user_id, device_id)
        cursor.execute("""
            INSERT INTO store_001 (user_id, username, finger_template_id, device_id, sensor_location)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, device_id) DO UPDATE SET
                username = EXCLUDED.username,
                finger_template_id = EXCLUDED.finger_template_id,
                sensor_location = EXCLUDED.sensor_location,
                updated_at = CURRENT_TIMESTAMP
        """, (fingerprint_id, user_name, fingerprint_id, device_id, sensor_location))
        
        conn.commit()
    
    # 4. Kirim notifikasi ke browser
    notification_data = {
        'type': 'enrollment_success',  // atau 'enrollment_error'
        'message': f'User {user_name} enrolled successfully!',
        'user_id': fingerprint_id,
        'username': user_name,
        'device_id': device_id,
        'sensor_location': sensor_location,
        'timestamp': datetime.now().isoformat()
    }
    
    socketio.start_background_task(emit_notification_task, notification_data)
```

**Hasil:**
- ✅ User tersimpan di database `store_001`
- ✅ Notifikasi muncul di browser (modal popup)

---

## 🔄 3. FLOW LENGKAP DATA

### **Scenario: User Scan Fingerprint**

```
1. User scan jari di sensor AS608_001
   ↓
2. Local Machine detect fingerprint (ID: 5, Confidence: 92)
   ↓
3. Local Machine kirim via MQTT:
   Topic: WHAC/Store001/in
   Payload: {
       "store_id": "Store001",
       "timestamp": "2024-01-15T14:23:12.456789",
       "status": "Match",
       "fingerprint_id": 5,
       "device_id": "AS608_001",
       "username": "Ahmad Rizki",
       "confidence": 92
   }
   ↓
4. Web UI terima di on_mqtt_message()
   ↓
5. Web UI parse JSON dan route ke handle_scan_message()
   ↓
6. Web UI process dengan process_incoming_scan():
   - Validasi data
   - Tentukan sensor_location = "masuk"
   - Tentukan action = "scan_detected"
   - Simpan ke database PostgreSQL (tabel store_001)
   ↓
7. Web UI format untuk WebSocket:
   {
       'user_id': 5,
       'status': 'Match',
       'username': 'Ahmad Rizki',
       'confidence': 92,
       'timestamp': '2024-01-15T14:23:12.456789',
       'store_id': 'Store001',
       'device_id': 'AS608_001'
   }
   ↓
8. Web UI kirim ke browser via SocketIO (event: 'scan_notification')
   ↓
9. Browser terima dan update UI real-time:
   - Tampilkan notifikasi
   - Update tabel attendance
   - Update chart/statistik
```

---

## 📋 4. STRUKTUR DATABASE

Data scan disimpan di tabel `store_001` dengan struktur:

```sql
CREATE TABLE store_001 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(255),
    finger_template_id INTEGER,
    device_id VARCHAR(50),
    sensor_location VARCHAR(50),  -- 'masuk' atau 'keluar'
    action VARCHAR(50),            -- 'scan_detected' atau 'no_match'
    granted_denied VARCHAR(50),    -- 'pending', 'granted', atau 'denied'
    timestamp TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, device_id)     -- Composite key untuk multi-sensor
);
```

---

## 🔑 5. POIN PENTING

### **Format Data:**
- ✅ Semua data dikirim sebagai **JSON string** via MQTT
- ✅ Encoding: **UTF-8**
- ✅ Timestamp format: **ISO 8601** (YYYY-MM-DDTHH:MM:SS.microseconds)
- ✅ QoS Level: **1** (at least once delivery)

### **Error Handling:**
- ✅ Web UI validasi data sebelum proses
- ✅ Jika data tidak lengkap, log warning dan skip
- ✅ Jika database error, log error tapi tetap kirim notifikasi ke browser
- ✅ Try-catch di setiap handler untuk prevent crash

### **Multi-Sensor Support:**
- ✅ `device_id` digunakan untuk identifikasi sensor
- ✅ `AS608_001` = Sensor Masuk
- ✅ `AS608_002` = Sensor Keluar
- ✅ Database menggunakan composite key `(user_id, device_id)` untuk support multiple fingerprint per user

### **Real-time Updates:**
- ✅ MQTT message diterima di background thread
- ✅ Data dikirim ke browser via SocketIO WebSocket
- ✅ Browser update UI tanpa refresh (real-time)

---

## 📝 6. CONTOH KODE LENGKAP

### **Local Machine (Pengirim):**
```python
# local_machine/fingerprint_simple_client.py
def send_scan_result(self, status, fingerprint_id, confidence=None):
    data = {
        "store_id": "Store001",
        "timestamp": datetime.now().isoformat(),
        "status": status,  # "Match" atau "Not Match"
        "fingerprint_id": fingerprint_id,
        "device_id": "AS608_001"
    }
    
    if username:
        data["username"] = username
    if confidence is not None:
        data["confidence"] = confidence
    
    payload = json.dumps(data)
    result = self.mqtt_client.publish("WHAC/Store001/in", payload, qos=1)
```

### **Web UI (Penerima):**
```python
# web_ui/app.py
def on_mqtt_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    
    if msg.topic == "WHAC/Store001/in":
        handle_scan_message(payload)

def handle_scan_message(payload):
    process_incoming_scan(payload)  # Simpan ke database
    
    scan_data = {
        'user_id': payload.get('fingerprint_id'),
        'status': payload.get('status'),
        'username': payload.get('username'),
        'confidence': payload.get('confidence'),
        'timestamp': payload.get('timestamp'),
        'store_id': payload.get('store_id'),
        'device_id': payload.get('device_id')
    }
    
    socketio.start_background_task(emit_scan_notification_task, scan_data)
```

---

## 🎯 KESIMPULAN

1. **Format Data:** JSON string via MQTT protocol
2. **Topik Utama:** 
   - `WHAC/Store001/in` (scan data)
   - `WHAC/Store001/add_user_response` (enrollment)
   - `WHAC/Store001/status` (relay status)
3. **Processing:** Parse JSON → Validasi → Simpan DB → Kirim WebSocket
4. **Real-time:** Data langsung muncul di browser tanpa refresh
5. **Multi-sensor:** Didukung via `device_id` dan composite key di database











