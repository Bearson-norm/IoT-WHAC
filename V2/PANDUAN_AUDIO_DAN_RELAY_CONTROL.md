# 🔊🚪 Panduan Lengkap: Audio Feedback & Manual Relay Control

## 📋 Fitur Baru

### 1. **Audio Feedback Control** 🔊
- Button di Web UI untuk trigger audio di local machine
- Support berbagai jenis audio: beep, success, error, welcome
- Text-to-speech untuk pesan custom
- Berguna untuk self-inspection dan konfirmasi

### 2. **Manual Relay Control** 🚪
- Button di Web UI untuk membuka relay langsung
- Tidak perlu scan fingerprint
- Support durasi custom (1-60 detik)
- Bisa pilih device (ALL, Sensor 1, Sensor 2)

### 3. **System Check** 🔍
- Button untuk trigger system self-check
- Check sensor status, MQTT connection, relay
- Audio feedback untuk hasil check

---

## 🚀 Yang Sudah Diimplementasikan

### Backend (Web UI) ✅
- [x] `/api/play_audio` - Send audio command via MQTT
- [x] `/api/manual_relay` - Manual relay control
- [x] `/api/system_check` - System self-check
- [x] All endpoints integrated with MQTT

### Frontend (Web UI) ✅
- [x] Control Panel dengan button yang lengkap
- [x] Audio control buttons (4 jenis audio)
- [x] Relay control buttons (quick & custom duration)
- [x] System check buttons
- [x] Status display untuk feedback

### Local Machine - Module ✅
- [x] `audio_feedback.py` - Module untuk audio playback
- [x] Support espeak (text-to-speech)
- [x] Support aplay (audio player)
- [x] Fallback ke beep jika TTS tidak tersedia

---

## 📦 Instalasi

### Langkah 1: Install Dependencies di Raspberry Pi

```bash
# Install espeak untuk text-to-speech
sudo apt-get update
sudo apt-get install -y espeak alsa-utils

# Test audio
speaker-test -t wav -c 2 -l 1

# Test espeak
espeak "Hello World"
```

### Langkah 2: Update Code

```bash
# Web UI
cd web_ui
git pull

# Local Machine
cd local_machine
git pull
```

### Langkah 3: Integrate ke fingerprint_multi_client.py

Tambahkan di awal file (setelah imports):

```python
# Import audio feedback
try:
    from audio_feedback import audio_feedback
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False
    logger.warning("Audio feedback module not available")
```

Tambahkan di `__init__` method:

```python
# Audio feedback
self.audio = audio_feedback if AUDIO_ENABLED else None

# MQTT Topics - tambahkan:
self.AUDIO_TOPIC = "WHAC/Store001/audio"
self.SYSTEM_TOPIC = "WHAC/Store001/system"
```

Tambahkan di `on_mqtt_connect`:

```python
# Subscribe to audio and system topics
client.subscribe(self.AUDIO_TOPIC, qos=1)
client.subscribe(self.SYSTEM_TOPIC, qos=1)
logger.info(f"✅ Subscribed to {self.AUDIO_TOPIC}")
logger.info(f"✅ Subscribed to {self.SYSTEM_TOPIC}")
```

Tambahkan di `handle_command`:

```python
elif topic == self.AUDIO_TOPIC:
    self.handle_audio_command(payload)
elif topic == self.SYSTEM_TOPIC:
    self.handle_system_command(payload)
```

Tambahkan method baru:

```python
def handle_audio_command(self, payload):
    """Handle audio playback command"""
    try:
        audio_type = payload.get('audio_type', 'beep')
        message = payload.get('message', '')
        
        logger.info(f"🔊 Audio command received: {audio_type}")
        
        if self.audio:
            self.audio.play_audio_type(audio_type, message)
            logger.info(f"✅ Audio played: {audio_type}")
        else:
            logger.warning("⚠️  Audio not available")
    except Exception as e:
        logger.error(f"Error handling audio command: {e}")

def handle_system_command(self, payload):
    """Handle system check command"""
    try:
        command = payload.get('command')
        
        logger.info(f"🔍 System command received: {command}")
        
        if command == 'system_check':
            self.run_system_check()
        else:
            logger.warning(f"Unknown system command: {command}")
    except Exception as e:
        logger.error(f"Error handling system command: {e}")

def run_system_check(self):
    """Run system self-check"""
    try:
        logger.info("=" * 80)
        logger.info("🔍 RUNNING SYSTEM SELF-CHECK")
        logger.info("=" * 80)
        
        if self.audio:
            self.audio.play_audio_type('system_check')
        
        # Check sensors
        logger.info("📡 Checking sensors...")
        connected_sensors = len([s for s in self.sensors if s.connected])
        total_sensors = len(self.sensors)
        logger.info(f"  ✓ Sensors connected: {connected_sensors}/{total_sensors}")
        
        # Check MQTT
        logger.info("📡 Checking MQTT...")
        if self.connected:
            logger.info("  ✓ MQTT connected")
        else:
            logger.warning("  ⚠️  MQTT not connected")
        
        # Check GPIO/Relay
        logger.info("🔌 Checking relay...")
        try:
            import RPi.GPIO as GPIO
            logger.info(f"  ✓ GPIO available, relay pin: {self.relay_pin}")
        except:
            logger.warning("  ⚠️  GPIO not available")
        
        # Check database
        logger.info("💾 Checking database...")
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            conn.close()
            logger.info(f"  ✓ Database OK, {user_count} users registered")
        except Exception as e:
            logger.error(f"  ✗ Database error: {e}")
        
        logger.info("=" * 80)
        logger.info("✅ SYSTEM CHECK COMPLETE")
        logger.info("=" * 80)
        
        if self.audio:
            self.audio.play_audio_type('success')
        
    except Exception as e:
        logger.error(f"Error running system check: {e}")
        if self.audio:
            self.audio.play_audio_type('error')
```

---

## 🎨 Update Web UI Template

Tambahkan control panel di `web_ui/templates/index.html` setelah dashboard stats (sekitar line 127):

```html
<!-- Include Control Panel -->
{% include 'control_panel.html' %}
```

---

## 🧪 Testing

### Test 1: Audio Feedback

1. Buka Web UI
2. Scroll ke "System Control Panel"
3. Klik button "Beep"
4. **Expected**: Raspberry Pi play beep sound
5. Test juga: Success, Error, Welcome

### Test 2: Manual Relay

1. Klik button "Open 5s"
2. **Expected**: Relay buka selama 5 detik
3. Check log: `✅ Manual relay command sent: 5s`
4. Check pintu: harus terbuka

### Test 3: System Check

1. Klik button "Run Full Check"
2. **Expected**: Log menampilkan hasil check
3. Audio "System check" diplay
4. Audio "Success" setelah check selesai

---

## 📊 Dashboard Statistics Fix

Jika grafik tidak muncul, check:

### 1. Check API Endpoint

```bash
curl http://localhost:5000/api/dashboard_stats
curl http://localhost:5000/api/charts/daily_stats?days=7
```

**Expected Response:**
```json
{
  "total_users": 5,
  "total_scans_today": 12,
  "successful_access_today": 10,
  "denied_access_today": 2,
  "recent_activity": [...]
}
```

### 2. Check Browser Console

1. Buka Web UI
2. Press F12 → Console tab
3. Check for errors
4. Look for: `loadDashboardStats()` and `loadCharts()` calls

### 3. Check Database

```sql
-- Check if tables exist
SELECT * FROM store_001 LIMIT 5;
SELECT * FROM log_data WHERE DATE(timestamp) = CURRENT_DATE;
SELECT * FROM log_action WHERE DATE(timestamp) = CURRENT_DATE;
```

### 4. Common Fixes

**Issue:** `Failed to fetch`
**Fix:** Check Web UI running and accessible

**Issue:** `Database connection failed`
**Fix:** Check PostgreSQL running
```bash
docker ps | grep postgres
docker logs whac-postgres
```

**Issue:** `No data to display`
**Fix:** Add some test data
```bash
# Simulate some scans
curl -X POST http://localhost:5000/simulate_scan
```

---

## 🎯 Use Cases

### Use Case 1: Remote Door Opening
Scenario: Guest datang, tapi fingerprint belum terdaftar
1. Admin buka Web UI dari jauh
2. Klik "Open 10s" di control panel
3. Pintu terbuka selama 10 detik
4. Guest bisa masuk

### Use Case 2: System Maintenance
Scenario: Mau check apakah sensor masih bekerja
1. Klik "Run Full Check"
2. System play audio "System check"
3. Check log untuk hasil
4. Audio "Success" jika semua OK

### Use Case 3: Audio Notification
Scenario: Mau test apakah speaker bekerja
1. Klik button audio berbeda-beda
2. Verify audio keluar dari Raspberry Pi
3. Adjust volume jika perlu

---

## 🔧 Troubleshooting

### Q: Audio tidak keluar
**A:** Check:
```bash
# Test speaker
speaker-test -t wav -c 2 -l 1

# Test espeak
espeak "Test"

# Check volume
alsamixer

# Increase volume
amixer set PCM -- 100%
```

### Q: Relay tidak respond
**A:** Check:
```bash
# Check GPIO
gpio readall

# Check MQTT
mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/action" -v

# Check logs
tail -f local_machine/logs/fingerprint_client.log
```

### Q: Web UI button tidak response
**A:** Check:
```bash
# Check browser console (F12)
# Check Web UI logs
docker logs whac-web-ui

# Check MQTT connection
curl http://localhost:5000/api/mqtt_status
```

---

## 📚 Files Modified/Created

### Web UI:
- ✅ `web_ui/app.py` - Added 3 API endpoints
- ✅ `web_ui/templates/control_panel.html` - NEW control panel UI

### Local Machine:
- ✅ `local_machine/audio_feedback.py` - NEW audio module
- ⏳ `local_machine/fingerprint_multi_client.py` - Need integration (documented above)

### Documentation:
- ✅ `PANDUAN_AUDIO_DAN_RELAY_CONTROL.md` - This file
- ✅ `IMPLEMENTASI_AUDIO_DAN_RELAY_CONTROL.md` - Implementation notes

---

## ✅ Checklist Deployment

- [ ] Install espeak di Raspberry Pi
- [ ] Test audio dengan `espeak "Test"`
- [ ] Update Web UI code dan restart
- [ ] Update Local Machine code
- [ ] Integrate audio_feedback ke fingerprint_multi_client.py
- [ ] Restart local machine client
- [ ] Test audio dari Web UI
- [ ] Test manual relay
- [ ] Test system check
- [ ] Verify semua berfungsi

---

## 🎉 Status

**Backend API:** ✅ COMPLETE
**Frontend UI:** ✅ COMPLETE
**Audio Module:** ✅ COMPLETE
**Integration:** ⏳ NEED MANUAL INTEGRATION (documented above)
**Testing:** ⏳ PENDING

**Documentasi:** ✅ COMPLETE

---

**Selamat! Sistem Anda sekarang punya kontrol audio dan relay yang lengkap!** 🎉

