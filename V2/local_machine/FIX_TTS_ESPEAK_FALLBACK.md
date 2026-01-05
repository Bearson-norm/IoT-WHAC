# 🔧 Fix: TTS Fallback ke espeak Direct

## 🐛 Masalah

TTS engine (pyttsx3) gagal initialize dengan error:
```
⚠️  TTS initialization failed: SetVoiceByName failed with unknown return code -1 for voice: gmw/en
```

Akibatnya, voice commands hanya print ke log, tidak berbicara.

## ✅ Solusi

Ditambahkan **automatic fallback ke espeak langsung** jika pyttsx3 gagal.

### Perubahan:

1. **Improved TTS Initialization**
   - Handle voice error dengan lebih baik
   - Tidak crash jika voice tidak ditemukan
   - Gunakan default voice jika Indonesian voice tidak ada

2. **espeak Direct Fallback**
   - Otomatis detect espeak jika pyttsx3 gagal
   - Gunakan espeak langsung via subprocess
   - Lebih ringan dan reliable

3. **Better Error Handling**
   - Fallback otomatis saat runtime error
   - Multiple fallback layers

## 🔄 Flow Baru

```
1. Try pyttsx3 initialization
   ↓
2. If failed → Check espeak available
   ↓
3. If espeak found → Use espeak direct
   ↓
4. If espeak not found → Print to log (last resort)
```

## 📊 Perbandingan

| Method | Status | Resource |
|--------|--------|----------|
| **pyttsx3** | ✅ Preferred | 10-15 MB RAM |
| **espeak direct** | ✅ Fallback | 5-10 MB RAM |
| **Print log** | ⚠️ Last resort | Minimal |

## 🧪 Testing

### Test 1: pyttsx3 (Normal)
```bash
# Jika pyttsx3 bekerja
python3 fingerprint_multi_client.py
# Expected: "✅ TTS engine initialized (pyttsx3)"
```

### Test 2: espeak Fallback
```bash
# Jika pyttsx3 gagal, otomatis fallback
python3 fingerprint_multi_client.py
# Expected: "⚠️  pyttsx3 initialization failed: ..."
# Expected: "🔄 Falling back to espeak direct..."
# Expected: "✅ Using espeak direct (fallback)"
```

### Test 3: Voice Command
```bash
# Klik tombol "Instruksi" → "Berputar 360°"
# Expected: Audio berbicara (via pyttsx3 atau espeak)
```

## 🎯 espeak Direct Parameters

```python
espeak -v id -s 150 -a 200 "text"
```

- `-v id` = Indonesian voice
- `-s 150` = Speed (150 words/min)
- `-a 200` = Amplitude/Volume (0-200)

## ✅ Expected Behavior Setelah Fix

### Log Output:
```
✅ Pygame mixer initialized
⚠️  pyttsx3 initialization failed: SetVoiceByName failed...
🔄 Falling back to espeak direct...
✅ Using espeak direct (fallback)
✅ Audio playback thread started
✅ AudioController initialized
```

### Saat Voice Command:
```
🔊 Voice command received: spin_around
🎵 Playing audio: voice_command - spin_around
🔊 Speaking (espeak): Silakan berputar tiga ratus enam puluh derajat...
✅ espeak playback completed
✅ Voice command playback completed: spin_around
```

## 🔍 Troubleshooting

### Issue: Masih Print ke Log

**Check:**
```bash
# 1. Cek espeak terinstall
which espeak
# Expected: /usr/bin/espeak

# 2. Test espeak manual
espeak -v id "Test suara"

# 3. Cek audio output
speaker-test -t wav -c 2
```

**Solution:**
```bash
# Install espeak jika belum
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev

# Restart local machine
python3 fingerprint_multi_client.py
```

### Issue: espeak Tidak Berbicara

**Check:**
```bash
# Test espeak dengan parameter
espeak -v id -s 150 -a 200 "Test suara"

# Cek audio device
aplay -l

# Set audio output
sudo raspi-config
# Advanced Options → Audio → Force 3.5mm jack
```

## 📝 Code Changes

### File: `local_machine/audio_controller.py`

**Added:**
- `self.use_espeak_direct` flag
- `_play_espeak_direct()` method
- Improved TTS initialization error handling
- Automatic fallback detection

**Modified:**
- `_play_tts()` method dengan fallback logic
- TTS initialization dengan better error handling

## 🚀 Deployment

### Step 1: Update Code
```bash
cd ~/IoT-WHAC/V2/local_machine
git pull  # atau copy file baru
```

### Step 2: Restart
```bash
python3 fingerprint_multi_client.py
```

### Step 3: Verify
- Check logs untuk "Using espeak direct" atau "TTS engine initialized"
- Test voice command dari Web UI
- Verify audio berbicara

## ✅ Success Indicators

- ✅ Log: "✅ Using espeak direct (fallback)" ATAU "✅ TTS engine initialized (pyttsx3)"
- ✅ Voice command berbicara (tidak hanya print log)
- ✅ Audio output di speaker
- ✅ No errors di logs

## 📚 Referensi

- espeak docs: http://espeak.sourceforge.net/
- pyttsx3 docs: https://pyttsx3.readthedocs.io/
- Raspberry Pi audio: https://www.raspberrypi.org/documentation/configuration/audio/

---

**Status:** ✅ Fixed  
**Date:** 5 Januari 2026  
**Version:** 2.1

