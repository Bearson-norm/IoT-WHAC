# 🔄 Flow Komunikasi Dua Arah: Web UI ↔ Local Machine

## 📊 Overview

Sistem menggunakan **MQTT Protocol** untuk komunikasi dua arah antara Web UI dan Local Machine (Raspberry Pi). Semua komunikasi melalui MQTT Broker di `103.87.67.139:1883`.

```
┌─────────────┐                    ┌──────────────┐                    ┌─────────────┐
│   Web UI    │ ◄────── MQTT ─────► │ MQTT Broker │ ◄────── MQTT ─────► │Local Machine│
│  (Flask)    │                    │ (103.87...) │                    │ (Raspberry) │
└─────────────┘                    └──────────────┘                    └─────────────┘
```

---

## 📤 1. KOMUNIKASI: Web UI → Local Machine

Web UI mengirim **command/instruksi** ke Local Machine melalui beberapa MQTT topics.

### A. **Command: Enrollment User** (Add User)

**Trigger:** Admin klik "Enroll User" di Web UI

**Flow:**
```
Browser → Web UI API → MQTT Publish → Local Machine → Response
```

**1. Web UI Mengirim Command:**
- **Endpoint:** `POST /api/enroll_user`
- **Lokasi:** `web_ui/app.py` (baris 2107-2262)
- **MQTT Topic:** `WHAC/Store001/add_user`
- **Format JSON:**
```json
{
    "fingerprint_id": 123,
    "user_name": "John Doe",
    "timestamp": "2024-01-15T10:30:45.123456",
    "source": "web_ui",
    "requested_by": "admin"
}
```

**2. Local Machine Menerima:**
- **Handler:** `on_mqtt_message()` → `handle_command_wrapper()` → `handle_add_user_command()`
- **Lokasi:** `local_machine/fingerprint_simple_client.py` (baris 368-624)
- **Proses:**
  1. Extract `fingerprint_id` dan `user_name` dari payload
  2. Set flag `enrolling = True` (pause scanning)
  3. Panggil `enroll_fingerprint(fingerprint_id)` - sensor menunggu scan jari
  4. Simpan ke SQLite database lokal
  5. Kirim response ke Web UI

**3. Local Machine Mengirim Response:**
- **MQTT Topic:** `WHAC/Store001/add_user_response`
- **Format Success:**
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T10:35:20.789012",
    "command": "add_user",
    "status": "success",
    "data": {
        "fingerprint_id": 123,
        "user_name": "John Doe",
        "device_id": "AS608_001",
        "message": "User added successfully"
    },
    "device_id": "AS608_001"
}
```
- **Format Error:**
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T10:35:20.789012",
    "command": "add_user",
    "status": "error",
    "data": {
        "message": "Failed to enroll fingerprint"
    },
    "device_id": "AS608_001"
}
```

**4. Web UI Menerima Response:**
- **Handler:** `on_mqtt_message()` → `handle_enrollment_response()`
- **Lokasi:** `web_ui/app.py` (baris 300-420)
- **Proses:**
  1. Parse response payload
  2. Jika success: Simpan user ke PostgreSQL database
  3. Kirim notifikasi ke browser via WebSocket (modal popup)
  4. Update UI real-time

**Kode Sumber:**
- **Web UI (Send):** `web_ui/app.py:2216-2220`
- **Local Machine (Receive):** `local_machine/fingerprint_simple_client.py:567-624`
- **Local Machine (Response):** `local_machine/fingerprint_simple_client.py:762-780`
- **Web UI (Receive Response):** `web_ui/app.py:300-420`

---

### B. **Command: Relay Control (Grant Access)**

**Trigger:** Admin klik "Grant Access" di Web UI setelah scan fingerprint

**Flow:**
```
Browser (WebSocket) → Web UI → MQTT Publish → Local Machine → Relay ON → Response
```

**1. Web UI Mengirim Command:**
- **WebSocket Event:** `grant_access`
- **Handler:** `handle_grant_access()` → `send_relay_command()`
- **Lokasi:** `web_ui/app.py` (baris 550-598, 725-763)
- **MQTT Topic:** `WHAC/Store001/action`
- **Format JSON:**
```json
{
    "command": "grant",
    "user_id": 123,
    "action": "access_granted",
    "timestamp": "2024-01-15T10:30:45.123456",
    "source": "web_ui"
}
```

**2. Local Machine Menerima:**
- **Handler:** `on_mqtt_message()` → `handle_command_wrapper()` → `handle_relay_command()`
- **Lokasi:** `local_machine/fingerprint_simple_client.py` (baris 444-461)
- **Proses:**
  1. Extract `command`, `user_id`, `action` dari payload
  2. Panggil `control_relay(command, duration=10)` - Aktifkan relay GPIO pin 18
  3. Relay ON selama 10 detik
  4. Kirim status update ke Web UI

**3. Local Machine Mengirim Status:**
- **MQTT Topic:** `WHAC/Store001/status`
- **Format:**
```json
{
    "command": "grant",
    "user_id": 123,
    "action": "access_granted",
    "source": "web_ui",
    "timestamp": "2024-01-15T10:30:50.456789",
    "relay_pin": 18,
    "device_id": "AS608_001",
    "status": "completed"
}
```

**Kode Sumber:**
- **Web UI (Send):** `web_ui/app.py:725-763`
- **Local Machine (Receive):** `local_machine/fingerprint_simple_client.py:444-461`
- **Local Machine (Response):** `local_machine/fingerprint_simple_client.py:463-491`

---

### C. **Command: Relay Control (Deny Access)**

**Trigger:** Admin klik "Deny Access" di Web UI setelah scan fingerprint

**Flow:** Sama seperti Grant Access, tapi command berbeda

**1. Web UI Mengirim Command:**
- **WebSocket Event:** `deny_access`
- **Handler:** `handle_deny_access()` → `send_relay_command()`
- **Lokasi:** `web_ui/app.py` (baris 688-723)
- **MQTT Topic:** `WHAC/Store001/action`
- **Format JSON:**
```json
{
    "command": "deny",
    "user_id": 123,
    "action": "access_denied",
    "timestamp": "2024-01-15T10:30:45.123456",
    "source": "web_ui"
}
```

**2. Local Machine Menerima:**
- Handler sama seperti Grant Access
- Relay tetap OFF (tidak diaktifkan)

**Kode Sumber:**
- **Web UI (Send):** `web_ui/app.py:688-723`
- **Local Machine (Receive):** `local_machine/fingerprint_simple_client.py:444-461`

---

### D. **Command: Audio Self-Inspection**

**Trigger:** Admin klik tombol "Self Inspection" di Web UI

**Flow:**
```
Browser → Web UI API → MQTT Publish → Local Machine → Play Audio
```

**1. Web UI Mengirim Command:**
- **Endpoint:** `POST /api/audio/self_inspection`
- **Lokasi:** `web_ui/app.py` (baris 2263-2353)
- **MQTT Topic:** `WHAC/Store001/audio`
- **Format JSON:**
```json
{
    "command": "self_inspection",
    "timestamp": "2024-01-15T10:30:45.123456",
    "source": "web_ui",
    "requested_by": "admin"
}
```

**2. Local Machine Menerima:**
- **Handler:** `on_mqtt_message()` → `handle_command_wrapper()` → `handle_audio_command()`
- **Lokasi:** `local_machine/fingerprint_multi_client.py` (untuk multi-sensor)
- **Proses:**
  1. Extract command dari payload
  2. Panggil audio controller untuk play self-inspection audio
  3. Kirim response (opsional)

**Kode Sumber:**
- **Web UI (Send):** `web_ui/app.py:2314-2318`
- **Local Machine (Receive):** `local_machine/fingerprint_multi_client.py` (audio handler)

---

## 📥 2. KOMUNIKASI: Local Machine → Web UI

Local Machine mengirim **data/notifikasi** ke Web UI melalui beberapa MQTT topics.

### A. **Data: Hasil Scan Fingerprint**

**Trigger:** User scan jari di sensor fingerprint

**Flow:**
```
Sensor → Local Machine → MQTT Publish → Web UI → Database → Browser (WebSocket)
```

**1. Local Machine Mengirim Data:**
- **Handler:** `scan_fingerprint()` → `send_scan_result()`
- **Lokasi:** `local_machine/fingerprint_simple_client.py` (baris 493-533)
- **MQTT Topic:** `WHAC/Store001/in`
- **Format JSON:**
```json
{
    "store_id": "Store001",
    "timestamp": "2024-01-15T10:30:45.123456",
    "status": "Match",  // atau "Not Match"
    "fingerprint_id": 123,
    "device_id": "AS608_001",
    "username": "John Doe",  // opsional
    "confidence": 85  // opsional
}
```

**2. Web UI Menerima:**
- **Handler:** `on_mqtt_message()` → `handle_scan_message()`
- **Lokasi:** `web_ui/app.py` (baris 242-298)
- **Proses:**
  1. Parse payload JSON
  2. Panggil `process_incoming_scan(payload)`:
     - Validasi data
     - Tentukan `sensor_location` dari `device_id`
     - Simpan ke PostgreSQL database (tabel `store_001`)
  3. Format data untuk WebSocket
  4. Kirim ke browser via SocketIO (`emit_scan_notification_task`)

**3. Browser Menerima (Real-time):**
- **WebSocket Event:** `scan_notification`
- **Data Format:**
```json
{
    "user_id": 123,
    "status": "Match",
    "username": "John Doe",
    "confidence": 85,
    "timestamp": "2024-01-15T10:30:45.123456",
    "store_id": "Store001",
    "device_id": "AS608_001"
}
```
- **UI Update:**
  - Tampilkan notifikasi popup
  - Update tabel attendance
  - Update chart/statistik
  - Tampilkan tombol Grant/Deny (jika Match)

**Kode Sumber:**
- **Local Machine (Send):** `local_machine/fingerprint_simple_client.py:493-533`
- **Web UI (Receive):** `web_ui/app.py:242-298`
- **Web UI (Process):** `web_ui/app.py:422-470`
- **Web UI (WebSocket):** `web_ui/app.py:226-240`

---

### B. **Data: Response Enrollment**

**Trigger:** Setelah Local Machine selesai enroll user

**Flow:**
```
Local Machine (Enroll Complete) → MQTT Publish → Web UI → Database → Browser (Modal)
```

**1. Local Machine Mengirim Response:**
- **Handler:** `handle_add_user_command()` → `send_command_response()`
- **Lokasi:** `local_machine/fingerprint_simple_client.py` (baris 604-608, 762-780)
- **MQTT Topic:** `WHAC/Store001/add_user_response`
- **Format:** (Sudah dijelaskan di bagian A. Enrollment User)

**2. Web UI Menerima:**
- **Handler:** `on_mqtt_message()` → `handle_enrollment_response()`
- **Lokasi:** `web_ui/app.py` (baris 300-420)
- **Proses:**
  1. Parse response payload
  2. Jika `status == "success"`:
     - Simpan user ke PostgreSQL database
     - Tentukan `sensor_location` dari `device_id`
  3. Format notifikasi untuk WebSocket
  4. Kirim ke browser via SocketIO (`emit_notification_task`)

**3. Browser Menerima (Real-time):**
- **WebSocket Event:** `notification`
- **Data Format:**
```json
{
    "type": "enrollment_success",
    "message": "User John Doe enrolled successfully on AS608_001 (masuk)!",
    "user_id": 123,
    "username": "John Doe",
    "fingerprint_id": 123,
    "device_id": "AS608_001",
    "sensor_location": "masuk",
    "timestamp": "2024-01-15T10:35:20.789012"
}
```
- **UI Update:**
  - Tampilkan modal popup dengan pesan sukses
  - Update daftar user di UI
  - Refresh tabel jika perlu

**Kode Sumber:**
- **Local Machine (Send):** `local_machine/fingerprint_simple_client.py:762-780`
- **Web UI (Receive):** `web_ui/app.py:300-420`

---

### C. **Data: Relay Status Update**

**Trigger:** Setelah Local Machine mengaktifkan/menonaktifkan relay

**Flow:**
```
Local Machine (Relay Action) → MQTT Publish → Web UI → Log Database
```

**1. Local Machine Mengirim Status:**
- **Handler:** `handle_relay_command()` → `send_relay_status()`
- **Lokasi:** `local_machine/fingerprint_simple_client.py` (baris 463-491)
- **MQTT Topic:** `WHAC/Store001/status`
- **Format:** (Sudah dijelaskan di bagian B. Relay Control)

**2. Web UI Menerima:**
- **Handler:** `on_mqtt_message()` (bisa ditambahkan handler khusus)
- **Proses:**
  - Log status ke database (opsional)
  - Update UI jika perlu

**Kode Sumber:**
- **Local Machine (Send):** `local_machine/fingerprint_simple_client.py:463-491`
- **Web UI (Receive):** `web_ui/app.py:242-268` (bisa ditambahkan handler khusus)

---

## 🔄 3. DIAGRAM FLOW LENGKAP

### **Scenario 1: User Scan Fingerprint → Admin Grant Access**

```
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────────┐    ┌─────────┐
│  User   │    │  Sensor │    │  Local   │    │ MQTT Broker │    │ Web UI  │
│         │    │         │    │ Machine  │    │             │    │         │
└────┬────┘    └────┬────┘    └────┬─────┘    └──────┬──────┘    └────┬────┘
     │              │               │                  │               │
     │ Scan Jari   │               │                  │               │
     ├─────────────►│               │                  │               │
     │              │               │                  │               │
     │              │ Detect Match  │                  │               │
     │              ├──────────────►│                  │               │
     │              │               │                  │               │
     │              │               │ Publish Scan     │               │
     │              │               │ Topic: /in       │               │
     │              │               ├──────────────────►│               │
     │              │               │                  │               │
     │              │               │                  │ Subscribe     │
     │              │               │                  ├──────────────►│
     │              │               │                  │               │
     │              │               │                  │               │ Process & Save DB
     │              │               │                  │               ├──────────────┐
     │              │               │                  │               │               │
     │              │               │                  │               │◄──────────────┘
     │              │               │                  │               │
     │              │               │                  │ WebSocket     │
     │              │               │                  │               ├──────────────┐
     │              │               │                  │               │               │
     │              │               │                  │               │◄──────────────┘
     │              │               │                  │               │
     │              │               │                  │               │ Browser shows
     │              │               │                  │               │ notification +
     │              │               │                  │               │ Grant/Deny btn
     │              │               │                  │               │
     │              │               │                  │               │ Admin clicks
     │              │               │                  │               │ "Grant Access"
     │              │               │                  │               │
     │              │               │                  │ Publish Action│
     │              │               │                  │◄──────────────┤
     │              │               │                  │ Topic: /action│
     │              │               │                  │               │
     │              │               │ Subscribe        │               │
     │              │               │◄─────────────────┤               │
     │              │               │                  │               │
     │              │               │ Relay ON (10s)   │               │
     │              │               ├──────────────┐   │               │
     │              │               │              │   │               │
     │              │               │◄──────────────┘   │               │
     │              │               │                  │               │
     │              │               │ Publish Status    │               │
     │              │               │ Topic: /status   │               │
     │              │               ├──────────────────►│               │
     │              │               │                  │               │
     │              │               │                  │               │ Update UI
     │              │               │                  │               │◄──────────────┐
     │              │               │                  │               │               │
     │              │               │                  │               │◄──────────────┘
```

### **Scenario 2: Admin Enroll User**

```
┌─────────┐    ┌──────────┐    ┌─────────────┐    ┌─────────────┐
│ Browser │    │  Web UI  │    │ MQTT Broker │    │Local Machine│
│         │    │          │    │             │    │             │
└────┬────┘    └────┬─────┘    └──────┬──────┘    └──────┬──────┘
     │              │                  │                  │
     │ Click Enroll │                  │                  │
     ├─────────────►│                  │                  │
     │              │                  │                  │
     │              │ Publish Add User │                  │
     │              │ Topic: /add_user│                  │
     │              ├──────────────────►│                  │
     │              │                  │                  │
     │              │                  │ Subscribe        │
     │              │                  ├──────────────────►│
     │              │                  │                  │
     │              │                  │                  │ Pause Scanning
     │              │                  │                  ├──────────────┐
     │              │                  │                  │              │
     │              │                  │                  │◄──────────────┘
     │              │                  │                  │
     │              │                  │                  │ Wait for scan
     │              │                  │                  │ (User scan jari)
     │              │                  │                  │
     │              │                  │                  │ Enroll Complete
     │              │                  │                  │
     │              │                  │ Publish Response │
     │              │                  │◄──────────────────┤
     │              │                  │ Topic: /add_user_│
     │              │                  │        response  │
     │              │                  │                  │
     │              │ Subscribe        │                  │
     │              │◄─────────────────┤                  │
     │              │                  │                  │
     │              │ Save to DB       │                  │
     │              ├──────────────┐   │                  │
     │              │              │   │                  │
     │              │◄──────────────┘   │                  │
     │              │                  │                  │
     │              │ WebSocket        │                  │
     │              │ Notification     │                  │
     │              ├──────────────┐   │                  │
     │              │              │   │                  │
     │◄──────────────┘              │   │                  │
     │              │                  │                  │
     │ Show Modal   │                  │                  │
     │ "Enrolled!"  │                  │                  │
```

---

## 📋 4. MQTT TOPICS SUMMARY

### **Topics yang di-Subscribe oleh Web UI:**
| Topic | Purpose | Handler |
|-------|---------|---------|
| `WHAC/Store001/in` | Scan results dari Local Machine | `handle_scan_message()` |
| `WHAC/Store001/add_user_response` | Response enrollment | `handle_enrollment_response()` |
| `WHAC/Store001/status` | Relay status updates | (bisa ditambahkan handler) |

### **Topics yang di-Publish oleh Web UI:**
| Topic | Purpose | Trigger |
|-------|---------|---------|
| `WHAC/Store001/action` | Relay control (grant/deny) | Admin klik Grant/Deny |
| `WHAC/Store001/add_user` | Enrollment command | Admin enroll user |
| `WHAC/Store001/audio` | Audio command | Admin trigger audio |

### **Topics yang di-Subscribe oleh Local Machine:**
| Topic | Purpose | Handler |
|-------|---------|---------|
| `WHAC/Store001/add_user` | Enrollment command | `handle_add_user_command()` |
| `WHAC/Store001/import` | Import users | `handle_import_command()` |
| `WHAC/Store001/export` | Export users | `handle_export_command()` |
| `WHAC/Store001/action` | Relay control | `handle_relay_command()` |
| `WHAC/Store001/audio` | Audio commands | `handle_audio_command()` |

### **Topics yang di-Publish oleh Local Machine:**
| Topic | Purpose | Trigger |
|-------|---------|---------|
| `WHAC/Store001/in` | Scan results | User scan fingerprint |
| `WHAC/Store001/add_user_response` | Enrollment response | Enrollment complete |
| `WHAC/Store001/status` | Relay status | Relay action complete |

---

## 🔑 5. POIN PENTING

### **Format Data:**
- ✅ Semua data dalam format **JSON string**
- ✅ Encoding: **UTF-8**
- ✅ Timestamp: **ISO 8601** format
- ✅ QoS Level: **1** (at least once delivery)

### **Error Handling:**
- ✅ Web UI validasi MQTT connection sebelum publish
- ✅ Local Machine validasi payload sebelum proses
- ✅ Try-catch di setiap handler
- ✅ Response error dikirim kembali ke Web UI

### **Threading:**
- ✅ Local Machine: Command processing di background thread (non-blocking)
- ✅ Web UI: MQTT message handling di background thread
- ✅ WebSocket emission via background task

### **Database:**
- ✅ Local Machine: SQLite database lokal (`fingerprints.db`)
- ✅ Web UI: PostgreSQL database (`whac_master.store_001`)
- ✅ Sync: Enrollment response trigger save ke PostgreSQL

### **Real-time Updates:**
- ✅ Web UI → Browser: Via SocketIO WebSocket
- ✅ Local Machine → Web UI: Via MQTT
- ✅ Browser update UI tanpa refresh

---

## 📝 6. CONTOH KODE LENGKAP

### **Web UI → Local Machine (Enrollment):**
```python
# web_ui/app.py
@app.route('/api/enroll_user', methods=['POST'])
def enroll_user():
    enrollment_command = {
        'fingerprint_id': int(user_id),
        'user_name': str(username),
        'timestamp': datetime.now().isoformat(),
        'source': 'web_ui',
        'requested_by': session.get('username', 'admin')
    }
    
    result = mqtt_client.publish(
        'WHAC/Store001/add_user',
        json.dumps(enrollment_command),
        qos=1
    )
```

### **Local Machine → Web UI (Scan Result):**
```python
# local_machine/fingerprint_simple_client.py
def send_scan_result(self, status, fingerprint_id, confidence=None):
    data = {
        "store_id": "Store001",
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "fingerprint_id": fingerprint_id,
        "device_id": "AS608_001"
    }
    
    payload = json.dumps(data)
    result = self.mqtt_client.publish(
        "WHAC/Store001/in", 
        payload, 
        qos=MQTT_QOS
    )
```

### **Web UI Receive & Process:**
```python
# web_ui/app.py
def on_mqtt_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    
    if msg.topic == "WHAC/Store001/in":
        handle_scan_message(payload)

def handle_scan_message(payload):
    process_incoming_scan(payload)  # Save to DB
    
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

### **Komunikasi Web UI → Local Machine:**
1. **Enrollment:** `WHAC/Store001/add_user` → Response: `WHAC/Store001/add_user_response`
2. **Relay Control:** `WHAC/Store001/action` → Response: `WHAC/Store001/status`
3. **Audio Command:** `WHAC/Store001/audio` → Response: (opsional)

### **Komunikasi Local Machine → Web UI:**
1. **Scan Result:** `WHAC/Store001/in` → Process → Database → WebSocket → Browser
2. **Enrollment Response:** `WHAC/Store001/add_user_response` → Process → Database → WebSocket → Browser
3. **Relay Status:** `WHAC/Store001/status` → Log (opsional)

### **Real-time Flow:**
- ✅ MQTT untuk komunikasi server-to-server
- ✅ WebSocket untuk komunikasi server-to-browser
- ✅ Database sebagai persistent storage
- ✅ Threading untuk non-blocking operations











