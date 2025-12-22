# 📋 Implementasi Sistem Verifikasi dan GPIO Control

## 🎯 Ringkasan

Dokumen ini menjelaskan implementasi sistem verifikasi user fingerprint dengan modal popup dan kontrol GPIO untuk membuka pintu.

---

## 📊 Arsitektur Sistem

### Flow Diagram

```
Local Machine (2 Device Sensor)
  ↓
MQTT Topic: WHAC/Store001/in
  ↓
Web UI Backend (app.py)
  ↓
Verifikasi User (check_user_in_user_machine)
  ↓
┌─────────────────┬─────────────────┐
│   VERIFIED      │   UNVERIFIED    │
│   (Terdaftar)   │ (Tidak Terdaftar)│
└─────────────────┴─────────────────┘
  ↓                    ↓
Modal: Grant/Deny   Modal: Daftar/Tidak
  ↓                    ↓
Access Log          Access Log / Enroll
  ↓                    ↓
GPIO Control        GPIO Control (jika grant)
```

---

## 🗄️ Database Schema

### 1. Tabel `user_machine`

**Fungsi**: Menyimpan user yang terdaftar di local machine dengan device identifier

**Struktur**:
```sql
CREATE TABLE user_machine (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,                    -- ID user fingerprint
    nama VARCHAR(100) NOT NULL,                   -- Nama user
    device_id VARCHAR(50) NOT NULL,               -- Device identifier (AS608_001, AS608_002)
    posisi VARCHAR(50),                           -- Posisi/jabatan
    finger_template_id INTEGER NOT NULL,         -- ID template fingerprint
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, device_id)                    -- Satu user bisa punya multiple device
);
```

**File**: `web_ui/database_schema_user_machine.sql`

---

### 2. Tabel `access_log`

**Fungsi**: Menyimpan log akses (grant/deny) dari modal popup

**Struktur**:
```sql
CREATE TABLE access_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,                              -- ID user (bisa NULL jika tidak terdaftar)
    nama VARCHAR(100),                             -- Nama user
    device_id VARCHAR(50) NOT NULL,                -- Device identifier
    status VARCHAR(20) NOT NULL,                   -- 'granted' atau 'denied'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_source VARCHAR(50) DEFAULT 'modal',     -- 'modal', 'automatic', 'manual'
    finger_template_id INTEGER,                    -- ID template fingerprint
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3. Tabel `gpio_log`

**Fungsi**: Menyimpan log GPIO status untuk monitoring

**Struktur**:
```sql
CREATE TABLE gpio_log (
    id SERIAL PRIMARY KEY,
    gpio_pin INTEGER NOT NULL,                    -- GPIO pin number (1, 2, 3)
    gpio_state VARCHAR(10) NOT NULL,              -- 'HIGH' atau 'LOW'
    event_type VARCHAR(50),                        -- 'relay_control', 'door_sensor', 'output_control'
    user_id INTEGER,                               -- ID user terkait
    device_id VARCHAR(50),                          -- Device identifier
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                              -- Deskripsi event
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔄 Flow Proses

### 1. **Scan Fingerprint dari Local Machine**

**Lokasi**: `local_machine/fingerprint_multi_client.py` atau `fingerprint_simple_client.py`

**Proses**:
1. Sensor membaca fingerprint
2. Mencari match di database lokal
3. Mengirim data ke MQTT topic `WHAC/Store001/in`

**Format Data MQTT**:
```json
{
    "fingerprint_id": 1,
    "device_id": "AS608_001",
    "status": "Match",
    "confidence": 85,
    "timestamp": "2025-01-15T10:30:00",
    "store_id": "Store001",
    "username": "John Doe"
}
```

---

### 2. **Web UI Backend Menerima Data**

**Lokasi**: `web_ui/app.py::handle_scan_message()`

**Proses**:
1. Menerima data dari MQTT
2. Memanggil `check_user_in_user_machine(fingerprint_id, device_id)`
3. Memproses data scan dan log ke database
4. Mengirim data ke WebSocket dengan status verifikasi

**Fungsi Verifikasi**:
```python
def check_user_in_user_machine(fingerprint_id, device_id):
    """Check if user exists in user_machine table"""
    cursor.execute("""
        SELECT id, user_id, nama, device_id, posisi, finger_template_id
        FROM user_machine
        WHERE user_id = %s AND device_id = %s
        LIMIT 1
    """, (fingerprint_id, device_id))
    return dict(result) if result else None
```

**Data yang Dikirim ke WebSocket**:
```json
{
    "user_id": 1,
    "status": "Match",
    "username": "John Doe",
    "confidence": 85,
    "timestamp": "2025-01-15T10:30:00",
    "store_id": "Store001",
    "device_id": "AS608_001",
    "is_verified": true,              // ✅ Baru: Status verifikasi
    "user_info": {                    // ✅ Baru: Info user jika terdaftar
        "id": 1,
        "user_id": 1,
        "nama": "John Doe",
        "device_id": "AS608_001",
        "posisi": "Manager",
        "finger_template_id": 1
    }
}
```

---

### 3. **Modal Popup di Web UI**

**Lokasi**: `web_ui/templates/index.html`

#### **Kondisi 1: User Terverifikasi (is_verified = true)**

**Modal Menampilkan**:
- Nama user
- Posisi
- User ID
- Device ID
- Status scan

**Pilihan**:
- **Grant Access** → Log ke `access_log` dengan status `granted` → GPIO Control
- **Deny Access** → Log ke `access_log` dengan status `denied`

**JavaScript Function**:
```javascript
function showVerifiedUserView(data) {
    // Tampilkan view untuk user terverifikasi
    // Tampilkan tombol Grant/Deny
}

function grantAccess() {
    socket.emit('grant_access', {
        user_id: currentScanData.user_id,
        nama: nama,
        device_id: currentScanData.device_id,
        finger_template_id: currentScanData.user_id
    });
}

function denyAccess() {
    socket.emit('deny_access', {
        user_id: currentScanData.user_id,
        nama: nama,
        device_id: currentScanData.device_id,
        finger_template_id: currentScanData.user_id
    });
}
```

---

#### **Kondisi 2: User Tidak Terverifikasi (is_verified = false)**

**Modal Menampilkan**:
- Pesan: "User tidak terdaftar"
- Form enrollment dengan field:
  - User ID (auto-fill dari fingerprint_id)
  - Nama (required)
  - Posisi (optional)

**Pilihan**:
- **Daftar** → Form enrollment → Insert ke `user_machine` → Log `granted` → GPIO Control
- **Tidak** → Log ke `access_log` dengan status `denied`

**JavaScript Function**:
```javascript
function showUnverifiedUserView(data) {
    // Tampilkan view untuk user tidak terverifikasi
    // Tampilkan form enrollment
    // Tampilkan tombol Daftar/Tidak
}

async function enrollNewUser() {
    const response = await fetch('/api/enroll_user_from_modal', {
        method: 'POST',
        body: JSON.stringify({
            user_id: userIdInt,
            nama: nama,
            posisi: posisi,
            device_id: deviceId,
            finger_template_id: fingerprintId
        })
    });
    
    // Setelah berhasil, log sebagai granted
    socket.emit('grant_access', {...});
}

function dismissUnknownUser() {
    // Log sebagai denied
    socket.emit('deny_access', {...});
}
```

---

### 4. **Backend Handler Grant/Deny**

**Lokasi**: `web_ui/app.py`

#### **Grant Access Handler**

```python
@socketio.on('grant_access')
def handle_grant_access(data):
    user_id = data.get('user_id')
    nama = data.get('nama', 'Unknown')
    device_id = data.get('device_id', 'AS608_001')
    finger_template_id = data.get('finger_template_id', user_id)
    
    # Log ke access_log
    log_access_to_database(nama, device_id, 'granted', user_id, 'modal', finger_template_id)
    
    # Send MQTT command ke relay controller
    success = send_relay_command('grant', user_id, 'access_granted', device_id)
    
    if success:
        # Log ke log_action (legacy)
        log_manual_action(user_id, 'access_granted', 'granted', device_id, None)
        
        emit('action_result', {
            'status': 'success',
            'message': f'Access granted for {nama}',
            'action': 'granted'
        })
```

#### **Deny Access Handler**

```python
@socketio.on('deny_access')
def handle_deny_access(data):
    user_id = data.get('user_id')
    nama = data.get('nama', 'Unknown')
    device_id = data.get('device_id', 'AS608_001')
    finger_template_id = data.get('finger_template_id', user_id)
    
    # Log ke access_log
    log_access_to_database(nama, device_id, 'denied', user_id, 'modal', finger_template_id)
    
    # Send MQTT command (relay tetap OFF)
    success = send_relay_command('deny', user_id, 'access_denied', device_id)
    
    if success:
        emit('action_result', {
            'status': 'success',
            'message': f'Access denied for {nama}',
            'action': 'denied'
        })
```

---

### 5. **GPIO Control (Raspberry Pi 4)**

**Lokasi**: `local_machine/relay_controller_advanced.py`

**GPIO Configuration**:
- **GPIO(1)**: Relay control (OUTPUT) - Membuka pintu
- **GPIO(2)**: Digital input (INPUT) - Sensor pintu dari luar
- **GPIO(3)**: Output control (OUTPUT) - Kontrol berdasarkan GPIO(2)

**Flow GPIO Control**:

```
Grant Access
  ↓
MQTT Command: 'grant'
  ↓
GPIO(1) = HIGH (relay aktif, pintu terbuka)
  ↓
Wait 5 seconds
  ↓
GPIO(1) = LOW (relay nonaktif, pintu tertutup)
  ↓
[Background Thread - Check GPIO(2) setelah 5 detik]
  ↓
GPIO(2) status → Log ke gpio_log
  ↓
[Monitoring Thread - Kontinyu]
  ↓
GPIO(2) changed?
  ├─ LOW → GPIO(3) = HIGH
  └─ HIGH → GPIO(3) = LOW
```

**Implementation**:

```python
def grant_access(self, user_id, action, device_id):
    """Grant access by activating relay (GPIO 1)"""
    # Activate GPIO(1) - Relay control (HIGH)
    GPIO.output(self.relay_pin, GPIO.HIGH)
    self.log_gpio_status(self.relay_pin, 'HIGH', 'relay_control', ...)
    
    # Wait 5 seconds
    time.sleep(5)
    
    # Deactivate GPIO(1) - Relay control (LOW)
    GPIO.output(self.relay_pin, GPIO.LOW)
    self.log_gpio_status(self.relay_pin, 'LOW', 'relay_control', ...)
    
    # Check GPIO(2) after 5 seconds delay (in background thread)
    check_thread = threading.Thread(target=self.check_gpio_2_after_delay, daemon=True)
    check_thread.start()

def check_gpio_2_after_delay(self):
    """Check GPIO(2) status after 5 seconds GPIO(1) LOW"""
    time.sleep(5)  # Wait 5 seconds
    
    if not self.gpio_1_active:
        gpio_2_state = GPIO.input(self.input_pin)
        state_str = 'HIGH' if gpio_2_state == GPIO.HIGH else 'LOW'
        
        # Log to database
        self.log_gpio_status(self.input_pin, state_str, 'door_sensor',
                            f'GPIO({self.input_pin}) read {state_str} after 5 seconds GPIO({self.relay_pin}) LOW')

def monitor_gpio_2_and_3(self):
    """Monitor GPIO(2) and control GPIO(3) accordingly"""
    while self.monitoring:
        current_state = GPIO.input(self.input_pin)
        
        if current_state != self.gpio_2_last_state:
            self.gpio_2_last_state = current_state
            
            if current_state == GPIO.LOW:
                # GPIO(2) is LOW → Set GPIO(3) HIGH
                GPIO.output(self.output_pin, GPIO.HIGH)
                self.log_gpio_status(self.output_pin, 'HIGH', 'output_control', ...)
            else:
                # GPIO(2) is HIGH → Set GPIO(3) LOW
                GPIO.output(self.output_pin, GPIO.LOW)
                self.log_gpio_status(self.output_pin, 'LOW', 'output_control', ...)
        
        time.sleep(0.1)  # Check every 100ms
```

---

## 📝 API Endpoints

### 1. **Enroll User dari Modal**

**Endpoint**: `POST /api/enroll_user_from_modal`

**Request Body**:
```json
{
    "user_id": 1,
    "nama": "John Doe",
    "posisi": "Manager",
    "device_id": "AS608_001",
    "finger_template_id": 1
}
```

**Response**:
```json
{
    "status": "success",
    "message": "User John Doe berhasil didaftarkan",
    "user_id": 1,
    "nama": "John Doe",
    "device_id": "AS608_001"
}
```

**Lokasi**: `web_ui/app.py::enroll_user_from_modal()`

---

### 2. **WebSocket Events**

#### **Grant Access**
```javascript
socket.emit('grant_access', {
    user_id: 1,
    nama: 'John Doe',
    device_id: 'AS608_001',
    finger_template_id: 1
});
```

#### **Deny Access**
```javascript
socket.emit('deny_access', {
    user_id: 1,
    nama: 'John Doe',
    device_id: 'AS608_001',
    finger_template_id: 1
});
```

---

## 🔧 Setup dan Konfigurasi

### 1. **Setup Database**

Jalankan SQL script untuk membuat tabel:
```bash
psql -U postgres -d whac_master -f web_ui/database_schema_user_machine.sql
```

Atau via Docker:
```bash
docker exec -i whac-postgres psql -U postgres -d whac_master < web_ui/database_schema_user_machine.sql
```

---

### 2. **Setup GPIO di Raspberry Pi**

Pastikan `relay_controller_advanced.py` berjalan di Raspberry Pi:

```bash
cd local_machine
python3 relay_controller_advanced.py
```

**GPIO Pin Configuration** (dalam code):
- `relay_pin = 1` (GPIO 1)
- `input_pin = 2` (GPIO 2)
- `output_pin = 3` (GPIO 3)

**Catatan**: Pastikan GPIO pin sesuai dengan wiring di Raspberry Pi.

---

### 3. **MQTT Topics**

- **Scan Data**: `WHAC/Store001/in`
- **Action Command**: `WHAC/Store001/action`
- **Relay Status**: `WHAC/Store001/relay_status`
- **GPIO Log**: `WHAC/Store001/gpio_log`

---

## ✅ Testing

### 1. **Test Verifikasi User Terdaftar**

1. Pastikan user sudah terdaftar di `user_machine`:
```sql
INSERT INTO user_machine (user_id, nama, device_id, posisi, finger_template_id)
VALUES (1, 'John Doe', 'AS608_001', 'Manager', 1);
```

2. Scan fingerprint di sensor
3. Modal harus muncul dengan pilihan Grant/Deny
4. Klik Grant → GPIO(1) harus HIGH selama 5 detik → LOW
5. Cek `access_log` dan `gpio_log` di database

---

### 2. **Test User Tidak Terdaftar**

1. Scan fingerprint yang tidak terdaftar
2. Modal harus muncul dengan form enrollment
3. Isi form (Nama, Posisi)
4. Klik Daftar → User harus terdaftar di `user_machine`
5. Cek `access_log` dengan status `granted`

---

### 3. **Test GPIO Control**

1. Grant access dari modal
2. Monitor GPIO di Raspberry Pi:
```bash
# Di terminal lain
watch -n 0.1 gpio readall
```

3. Verifikasi:
   - GPIO(1) HIGH → Wait 5s → GPIO(1) LOW
   - GPIO(2) status ter-log setelah 5 detik GPIO(1) LOW
   - GPIO(3) mengikuti GPIO(2) (LOW → HIGH, HIGH → LOW)

---

## 📊 Monitoring dan Logging

### 1. **Access Log**

Query untuk melihat log akses:
```sql
SELECT * FROM access_log 
ORDER BY timestamp DESC 
LIMIT 10;
```

### 2. **GPIO Log**

Query untuk melihat log GPIO:
```sql
SELECT * FROM gpio_log 
ORDER BY timestamp DESC 
LIMIT 10;
```

### 3. **User Machine**

Query untuk melihat user terdaftar:
```sql
SELECT * FROM user_machine 
ORDER BY created_at DESC;
```

---

## 🐛 Troubleshooting

### 1. **Modal Tidak Muncul**

- Cek WebSocket connection di browser console
- Cek log di `web_ui/app.py` untuk error
- Pastikan `scanModal` sudah di-initialize

### 2. **GPIO Tidak Berfungsi**

- Cek MQTT connection antara Web UI dan Raspberry Pi
- Cek `relay_controller_advanced.py` berjalan di Raspberry Pi
- Cek GPIO pin configuration sesuai wiring
- Cek log di `gpio_log` table

### 3. **User Tidak Terverifikasi**

- Cek data di `user_machine` table
- Pastikan `user_id` dan `device_id` sesuai
- Cek log di `web_ui/app.py` untuk error verifikasi

---

## 📚 File-File Terkait

- **Database Schema**: `web_ui/database_schema_user_machine.sql`
- **Backend Handler**: `web_ui/app.py`
- **Frontend Modal**: `web_ui/templates/index.html`
- **GPIO Control**: `local_machine/relay_controller_advanced.py`
- **Fingerprint Client**: `local_machine/fingerprint_multi_client.py`

---

*Dokumen ini menjelaskan implementasi lengkap sistem verifikasi dan GPIO control untuk IoT-WHAC.*

