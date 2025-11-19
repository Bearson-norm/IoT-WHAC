# ⚡ Quick Start: Audio & Relay Control

## 🎯 Yang Sudah Dibuat

### ✅ Web UI (Backend API)
- `/api/play_audio` - Trigger audio di local machine
- `/api/manual_relay` - Buka relay manual
- `/api/system_check` - System self-check

### ✅ Web UI (Frontend)
- Control panel dengan button lengkap
- Audio: Beep, Success, Error, Welcome
- Relay: 5s, 10s, 30s, Custom
- System Check: Full check, sensors, MQTT, relay

### ✅ Local Machine
- `audio_feedback.py` - Module audio lengkap
- Support text-to-speech (espeak)
- Fallback ke beep jika TTS tidak ada

---

## 🚀 Deploy (3 Langkah)

### 1️⃣ Install Audio di Raspberry Pi

```bash
sudo apt-get update
sudo apt-get install -y espeak alsa-utils

# Test
espeak "Hello"
```

### 2️⃣ Update Code

```bash
# Web UI
cd web_ui
git pull
docker-compose restart

# Local Machine  
cd local_machine
git pull
```

### 3️⃣ Add Control Panel ke Web UI

Edit `web_ui/templates/index.html`, tambahkan setelah dashboard stats (line ~127):

```html
<!-- Include Control Panel -->
{% include 'control_panel.html' %}
```

---

## 📝 Integration ke Local Machine

Karena file `fingerprint_multi_client.py` sangat panjang, follow panduan di:
**`PANDUAN_AUDIO_DAN_RELAY_CONTROL.md`** (section "Langkah 3")

**TL;DR:**
1. Import audio_feedback
2. Subscribe ke MQTT topics (audio & system)
3. Add handler methods
4. Restart client

---

## 🧪 Test

### Audio Test:
```bash
python3 local_machine/audio_feedback.py
```

### Web UI Test:
1. Buka http://your-ip:5000
2. Scroll ke "System Control Panel"
3. Klik button "Beep"
4. ✅ Harus keluar suara dari Raspberry Pi

### Relay Test:
1. Klik "Open 5s"
2. ✅ Relay harus buka 5 detik

---

## 📚 Dokumentasi Lengkap

- **Complete Guide:** `PANDUAN_AUDIO_DAN_RELAY_CONTROL.md`
- **Implementation:** `IMPLEMENTASI_AUDIO_DAN_RELAY_CONTROL.md`

---

**Status:** ✅ READY TO DEPLOY!

