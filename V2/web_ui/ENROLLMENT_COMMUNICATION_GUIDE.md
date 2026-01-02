# Panduan Komunikasi Enrollment antara Web-UI dan Local Machine

## Overview

Sistem komunikasi enrollment menggunakan MQTT untuk komunikasi real-time antara Web-UI dan Local Machine dengan fitur:

1. **Status Tracking** - Melacak status enrollment dari awal sampai selesai
2. **Progress Updates** - Update progress real-time selama enrollment
3. **Timeout Handling** - Auto-timeout jika enrollment tidak selesai dalam 2 menit
4. **Error Handling** - Penanganan error yang lebih baik
5. **Retry Support** - Support untuk retry enrollment

## Flow Komunikasi

### 1. Web-UI → Local Machine (Request Enrollment)

**Endpoint:** `POST /api/enroll_user`

**Request Body:**
```json
{
  "user_id": 1,
  "username": "John Doe",
  "target_sensor": "AS608_001"  // Optional
}
```

**MQTT Topic:** `WHAC/Store001/add_user`

**MQTT Payload:**
```json
{
  "fingerprint_id": 1,
  "user_name": "John Doe",
  "timestamp": "2026-01-02T10:00:00",
  "source": "web_ui",
  "requested_by": "admin",
  "enrollment_id": "enroll_1_1704182400000",
  "target_sensor": "AS608_001"  // Optional
}
```

**Response:**
```json
{
  "message": "Enrollment command sent...",
  "user_id": 1,
  "username": "John Doe",
  "status": "enrollment_started",
  "enrollment_id": "enroll_1_1704182400000"
}
```

### 2. Local Machine → Web-UI (Progress Updates)

**MQTT Topic:** `WHAC/Store001/add_user_response`

**Progress Update Payload:**
```json
{
  "store_id": "Store001",
  "timestamp": "2026-01-02T10:00:05",
  "command": "add_user",
  "status": "progress",
  "data": {
    "enrollment_id": "enroll_1_1704182400000",
    "fingerprint_id": 1,
    "user_name": "John Doe",
    "device_id": "AS608_001",
    "progress": 40,
    "progress_message": "Starting enrollment on AS608_001...",
    "status": "in_progress"
  },
  "device_id": "MULTI_SENSOR"
}
```

### 3. Local Machine → Web-UI (Success Response)

**MQTT Topic:** `WHAC/Store001/add_user_response`

**Success Payload:**
```json
{
  "store_id": "Store001",
  "timestamp": "2026-01-02T10:00:30",
  "command": "add_user",
  "status": "success",
  "data": {
    "fingerprint_id": 1,
    "user_name": "John Doe",
    "device_id": "AS608_001",
    "enrolled_sensors": ["AS608_001"],
    "remaining_sensors": ["AS608_002"],
    "message": "User enrolled successfully on AS608_001",
    "enrollment_id": "enroll_1_1704182400000",
    "progress": 100,
    "progress_message": "Enrollment completed successfully"
  },
  "device_id": "MULTI_SENSOR"
}
```

### 4. Local Machine → Web-UI (Error Response)

**MQTT Topic:** `WHAC/Store001/add_user_response`

**Error Payload:**
```json
{
  "store_id": "Store001",
  "timestamp": "2026-01-02T10:00:15",
  "command": "add_user",
  "status": "error",
  "data": {
    "message": "Failed to enroll fingerprint on any sensor",
    "fingerprint_id": 1,
    "user_name": "John Doe",
    "enrollment_id": "enroll_1_1704182400000",
    "progress": 0,
    "progress_message": "Enrollment failed on all sensors"
  },
  "device_id": "MULTI_SENSOR"
}
```

## Status Tracking API

### Get Enrollment Status

**Endpoint:** `GET /api/enrollment_status/<enrollment_id>`

**Response:**
```json
{
  "enrollment_id": "enroll_1_1704182400000",
  "user_id": 1,
  "username": "John Doe",
  "status": "in_progress",
  "progress": 40,
  "progress_message": "Starting enrollment on AS608_001...",
  "started_at": "2026-01-02T10:00:00",
  "device_id": "AS608_001",
  "sensor_location": "masuk"
}
```

### Get Active Enrollments

**Endpoint:** `GET /api/enrollment_status?user_id=1`

**Response:**
```json
{
  "enrollment_id": "enroll_1_1704182400000",
  "user_id": 1,
  "username": "John Doe",
  "status": "in_progress",
  "progress": 40,
  "progress_message": "Starting enrollment on AS608_001...",
  "started_at": "2026-01-02T10:00:00"
}
```

## Status Values

- `pending` - Enrollment request dibuat, menunggu diproses
- `in_progress` - Enrollment sedang berlangsung
- `success` - Enrollment berhasil
- `error` - Enrollment gagal
- `timeout` - Enrollment timeout (lebih dari 2 menit)

## Progress Values

- `0-10%` - Request dikirim ke local machine
- `20-30%` - Menunggu scan sidik jari pertama
- `40-50%` - Scan sidik jari pertama selesai, menunggu scan kedua
- `60-70%` - Scan sidik jari kedua selesai, membuat model
- `80-90%` - Model dibuat, menyimpan ke sensor
- `100%` - Enrollment selesai, menyimpan ke database

## WebSocket Notifications

Web-UI mengirim notifikasi real-time via WebSocket:

### Enrollment Progress
```javascript
{
  type: 'enrollment_progress',
  enrollment_id: 'enroll_1_1704182400000',
  progress: 40,
  progress_message: 'Starting enrollment on AS608_001...',
  status: 'in_progress',
  device_id: 'AS608_001',
  timestamp: '2026-01-02T10:00:05'
}
```

### Enrollment Success
```javascript
{
  type: 'enrollment_success',
  message: 'User John Doe enrolled successfully on AS608_001 (masuk)!',
  user_id: 1,
  username: 'John Doe',
  fingerprint_id: 1,
  device_id: 'AS608_001',
  sensor_location: 'masuk',
  timestamp: '2026-01-02T10:00:30'
}
```

### Enrollment Error
```javascript
{
  type: 'enrollment_error',
  message: 'Enrollment failed: Failed to enroll fingerprint on any sensor',
  error: 'Failed to enroll fingerprint on any sensor',
  enrollment_id: 'enroll_1_1704182400000',
  user_id: 1,
  username: 'John Doe',
  timestamp: '2026-01-02T10:00:15'
}
```

## Timeout Handling

- Default timeout: **120 detik (2 menit)**
- Jika enrollment tidak selesai dalam 2 menit, status otomatis menjadi `timeout`
- Enrollment yang timeout akan di-cleanup setelah 1 jam

## Error Handling

### Common Errors

1. **MQTT Connection Error**
   - Error: `MQTT client not connected to broker`
   - Solution: Check MQTT broker status

2. **Sensor Not Available**
   - Error: `Target sensor AS608_001 not available`
   - Solution: Check sensor connection

3. **Enrollment Timeout**
   - Error: `Enrollment timed out after 120 seconds`
   - Solution: Retry enrollment

4. **Database Error**
   - Error: `Database connection failed`
   - Solution: Check database connection

## Best Practices

1. **Polling Status** - Gunakan polling untuk check status enrollment setiap 2-3 detik
2. **WebSocket Listen** - Listen untuk WebSocket notifications untuk real-time updates
3. **Error Handling** - Selalu handle error responses dengan baik
4. **Timeout Handling** - Handle timeout dengan memberikan opsi retry
5. **Progress Display** - Tampilkan progress bar untuk user experience yang lebih baik

## Testing

### Test Enrollment Flow

1. Start enrollment via `/api/enroll_user`
2. Check status via `/api/enrollment_status/<enrollment_id>`
3. Monitor WebSocket notifications
4. Verify user added to database after success

### Test Error Handling

1. Disconnect MQTT broker
2. Try enrollment - should get connection error
3. Reconnect MQTT broker
4. Retry enrollment - should work

### Test Timeout

1. Start enrollment
2. Don't complete fingerprint scan
3. Wait 2+ minutes
4. Check status - should be `timeout`

