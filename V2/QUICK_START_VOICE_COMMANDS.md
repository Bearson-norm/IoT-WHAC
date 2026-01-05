# 🚀 Quick Start: Voice Commands

## ⚡ 3-Step Quick Start

### Step 1: Restart Services (1 menit)

```bash
# Restart Web UI
cd web_ui
python3 app.py

# Restart Local Machine (terminal lain)
cd local_machine
python3 fingerprint_multi_client.py
```

**Expected Output (Local Machine):**
```
✅ Audio controller initialized
✓ Subscribed to command topics (including audio and voice commands)
```

**Expected Output (Web UI):**
```
✅ Web UI subscribed to topic: WHAC/Store001/voice_response (QoS 1)
🔔 Web UI is now listening for scan notifications, enrollment responses, voice commands, and GPIO logs...
```

### Step 2: Buka Web UI (30 detik)

```bash
# Buka browser
http://localhost:5000

# Login dengan kredensial admin
```

### Step 3: Test Voice Commands (30 detik)

1. **Lihat Navbar** - Tombol baru akan muncul:
   - ⚠️ **Instruksi** (dropdown kuning)
   - 🔴 **Peringatan** (dropdown merah)

2. **Klik Instruksi** → Pilih "Berputar 360°"
3. **Dengarkan Audio** di speaker Raspberry Pi
4. **Lihat Notifikasi** sukses di Web UI

---

## 🎯 Apa yang Berubah?

### ❌ Dihapus:
- Status Pintu (card di dashboard)
- Door status MQTT handler

### ✅ Ditambahkan:
- **15 Perintah Suara** dalam Bahasa Indonesia
- **2 Dropdown Menu** (Instruksi & Peringatan)
- **MQTT Topics Baru** untuk voice commands
- **API Endpoint Baru** `/api/voice_command`

---

## 📱 Cara Menggunakan

### Mengirim Instruksi Self-Inspection:

```
1. Klik "Instruksi" ⚠️
2. Pilih perintah:
   • Berputar 360°
   • Angkat Tangan
   • Rentangkan Tangan
   • Tunjukkan Saku
   • Buka Tas
   • Lepas Jaket
   • Maju Selangkah
   • Mundur
   • Tunggu Sebentar
3. Audio akan diputar otomatis
```

### Mengirim Peringatan:

```
1. Klik "Peringatan" 🔴
2. Pilih peringatan:
   • Barang Terlarang
   • Benda Berbahaya
   • Akses Ditolak
   • Perilaku Mencurigakan
   • Stop Segera
3. Audio peringatan akan diputar
```

---

## 🧪 Testing Cepat

### Test 1: Instruksi
```bash
# 1. Buka Web UI
# 2. Klik "Instruksi" → "Berputar 360°"
# 3. Expected: Audio "Silakan berputar..." diputar di speaker
```

### Test 2: Peringatan
```bash
# 1. Klik "Peringatan" → "Barang Terlarang"
# 2. Expected: Audio peringatan diputar dengan volume tinggi
```

### Test 3: Multiple Commands
```bash
# 1. Klik "Instruksi" → "Angkat Tangan"
# 2. Tunggu selesai
# 3. Klik "Instruksi" → "Rentangkan Tangan"
# Expected: Audio diputar berurutan (queue system bekerja)
```

---

## ⚠️ Troubleshooting 1-Minute Fix

### Issue: Tombol Tidak Muncul

```bash
# Clear browser cache
Ctrl + F5 (Windows/Linux)
Cmd + Shift + R (Mac)
```

### Issue: Audio Tidak Diputar

```bash
# Cek speaker connected
speaker-test -t wav -c 2

# Cek audio controller
cd local_machine
grep "Audio controller initialized" <(python3 fingerprint_multi_client.py)
```

### Issue: MQTT Error

```bash
# Restart MQTT broker
sudo systemctl restart mosquitto

# Test MQTT
mosquitto_pub -h localhost -t "test" -m "hello"
```

---

## 📊 Expected Behavior

### ✅ Success Indicators:

1. **Web UI:**
   - ✅ Tombol "Instruksi" dan "Peringatan" muncul
   - ✅ Dropdown menu berfungsi
   - ✅ Notifikasi sukses muncul setelah klik
   - ✅ No errors di browser console (F12)

2. **Local Machine:**
   - ✅ Log: "Voice command received: ..."
   - ✅ Log: "Voice command ... queued successfully"
   - ✅ Audio diputar di speaker

3. **Audio Output:**
   - ✅ Audio file diputar (jika ada di folder `audio/`)
   - ✅ TTS diputar (jika audio file tidak ada)
   - ✅ Tidak ada overlapping audio

---

## 🔧 Optional: Custom Audio Files

### Tambahkan Audio Kustom (5 menit):

```bash
cd local_machine
mkdir -p audio

# Copy audio files (format: MP3, WAV, OGG)
cp /path/to/spin_around.mp3 audio/
cp /path/to/raise_hands.mp3 audio/
cp /path/to/prohibited_warning.mp3 audio/

# Restart local machine
python3 fingerprint_multi_client.py
```

**Nama File yang Didukung:**
- `spin_around.mp3`
- `raise_hands.mp3`
- `spread_arms.mp3`
- `show_pockets.mp3`
- `open_bag.mp3`
- `remove_jacket.mp3`
- `turn_around_slowly.mp3`
- `prohibited_warning.mp3`
- `weapon_warning.mp3`
- `unauthorized_entry.mp3`
- `suspicious_behavior.mp3`
- `stop_immediately.mp3`
- `step_forward.mp3`
- `step_back.mp3`
- `wait_moment.mp3`

---

## 📸 Screenshot Preview

### Navbar Sebelum (Before):
```
[MQTT Status] [Simulate Scan] [Self-Inspection] [Aktifkan Alarm]
```

### Navbar Setelah (After):
```
[MQTT Status] [Simulate Scan] [Self-Inspection] [⚠️ Instruksi ▼] [🔴 Peringatan ▼] [Aktifkan Alarm]
```

---

## 🎯 Use Cases

### 1. Security Check Point
```
Scenario: Pengunjung masuk area terbatas
Actions:
1. Scan fingerprint
2. Klik "Instruksi" → "Berputar 360°"
3. Klik "Instruksi" → "Tunjukkan Saku"
4. Klik "Instruksi" → "Buka Tas"
```

### 2. Emergency Warning
```
Scenario: Deteksi barang mencurigakan
Actions:
1. Klik "Peringatan" → "Stop Segera"
2. Klik "Peringatan" → "Perilaku Mencurigakan"
3. Call security team
```

### 3. Routine Inspection
```
Scenario: Pemeriksaan rutin
Actions:
1. Klik "Instruksi" → "Maju Selangkah"
2. Klik "Instruksi" → "Angkat Tangan"
3. Klik "Instruksi" → "Rentangkan Tangan"
```

---

## 📚 Full Documentation

Untuk dokumentasi lengkap, lihat:
- **PANDUAN_PERINTAH_SUARA.md** - Panduan lengkap (Indonesia)
- **VOICE_COMMANDS_CHANGELOG.md** - Technical changelog (English)
- **AUDIO_SELF_INSPECTION_GUIDE.md** - Audio system guide

---

## ✅ Checklist

Sebelum deploy ke production:

- [ ] Web UI restart successful
- [ ] Local machine restart successful
- [ ] Tombol "Instruksi" muncul di navbar
- [ ] Tombol "Peringatan" muncul di navbar
- [ ] Test 1 instruksi command → audio diputar
- [ ] Test 1 peringatan command → audio diputar
- [ ] Test multiple commands → queue system bekerja
- [ ] No errors di logs
- [ ] Status pintu card hilang dari dashboard

---

**Status:** ✅ Ready to Use  
**Waktu Total:** 5 menit  
**Difficulty:** Mudah (Easy)  
**Tanggal:** 4 Januari 2026

---

## 💡 Tips

1. **Audio Files:** Gunakan MP3 format untuk best compatibility
2. **Volume Control:** Adjust volume di Raspberry Pi: `alsamixer`
3. **Queue System:** Tidak perlu tunggu audio selesai, klik beberapa perintah sekaligus
4. **Testing:** Gunakan TTS untuk testing cepat tanpa audio files
5. **Security:** Only logged-in users can send voice commands

---

**Need Help?** 
- 📖 Baca: `PANDUAN_PERINTAH_SUARA.md`
- 🔧 Troubleshoot: Check logs di `web_ui/logs/` dan `local_machine/logs/`
- 🐛 Report bugs: Create issue di repository

---

**Selamat Menggunakan! 🎉**


