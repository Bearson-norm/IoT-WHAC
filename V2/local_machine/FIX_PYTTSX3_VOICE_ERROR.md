# 🔧 Fix: pyttsx3 Voice Setting Error

## 🐛 Masalah

pyttsx3 gagal initialize dengan error:
```
⚠️  pyttsx3 initialization failed: SetVoiceByName failed with unknown return code -1 for voice: gmw/en
```

**Penyebab:**
- pyttsx3 mencoba set voice yang tidak tersedia di sistem
- Voice setting gagal, menyebabkan initialization error
- Sistem fallback ke espeak, padahal pyttsx3 sebenarnya bisa digunakan dengan default voice

## ✅ Solusi

Diperbaiki initialization pyttsx3 agar:
1. **Tidak crash** jika voice setting gagal
2. **Tetap menggunakan pyttsx3** dengan default voice jika Indonesian voice tidak tersedia
3. **Graceful degradation** - hanya fallback ke espeak jika pyttsx3 benar-benar tidak bisa initialize

### Perubahan:

1. **Better Voice Handling**
   - Try-catch untuk setiap voice operation
   - Tidak crash jika voice tidak ditemukan
   - Gunakan default voice jika Indonesian voice tidak ada

2. **Property Setting dengan Error Handling**
   - Set rate, volume dengan try-catch
   - Continue meskipun beberapa property gagal

3. **Smart Fallback**
   - Hanya fallback ke espeak jika pyttsx3 benar-benar gagal init
   - Jika pyttsx3 init berhasil tapi voice gagal, tetap gunakan pyttsx3 dengan default

## 🔄 Flow Baru

```
1. Try pyttsx3.init()
   ↓
2. If success:
   ├─ Try set Indonesian voice
   │  ├─ If success → Use Indonesian voice ✅
   │  └─ If failed → Use default voice ✅
   ├─ Set rate & volume (with error handling)
   └─ Continue with pyttsx3 ✅
   ↓
3. If pyttsx3.init() completely failed:
   └─ Fallback to espeak direct
```

## 📊 Perbandingan

| Scenario | Before | After |
|----------|--------|-------|
| **Voice not found** | ❌ Crash, fallback to espeak | ✅ Use default voice, continue with pyttsx3 |
| **Voice setting failed** | ❌ Crash, fallback to espeak | ✅ Use default voice, continue with pyttsx3 |
| **pyttsx3 init failed** | ❌ Fallback to espeak | ✅ Fallback to espeak (same) |
| **Property setting failed** | ❌ Crash | ✅ Continue with defaults |

## 🧪 Testing

### Test 1: pyttsx3 dengan Default Voice
```bash
python3 fingerprint_multi_client.py
# Expected: "✅ TTS engine initialized (pyttsx3) with default settings"
# Expected: NO fallback to espeak
```

### Test 2: Voice Command
```bash
# Klik "Instruksi" → "Berputar 360°"
# Expected: Audio berbicara via pyttsx3 (bukan espeak)
# Expected log: "🔊 Speaking: ..." (bukan "🔊 Speaking (espeak): ...")
```

### Test 3: Verify pyttsx3 Used
```bash
# Check logs
grep "TTS engine initialized" logs/*.log
# Expected: "✅ TTS engine initialized (pyttsx3)"
# NOT: "✅ Using espeak direct (fallback)"
```

## ✅ Expected Behavior Setelah Fix

### Log Output:
```
✅ Pygame mixer initialized
✅ TTS engine initialized (pyttsx3)  ← SUDAH TIDAK ERROR!
✅ Audio playback thread started
✅ AudioController initialized
```

**ATAU jika voice setting gagal tapi engine OK:**
```
✅ Pygame mixer initialized
⚠️  Some TTS properties failed to set: SetVoiceByName failed...
ℹ️  Continuing with default TTS settings
✅ TTS engine initialized (pyttsx3) with default settings  ← MASIH PAKAI PYTTSX3!
✅ AudioController initialized
```

### Saat Voice Command:
```
🔊 Voice command received: spin_around
🎵 Playing audio: voice_command - spin_around
🔊 Speaking: Silakan berputar tiga ratus enam puluh derajat...  ← PYTTSX3!
✅ TTS playback completed
✅ Voice command playback completed: spin_around
```

## 🔍 Troubleshooting

### Issue: Masih Fallback ke espeak

**Check:**
```bash
# 1. Cek pyttsx3 terinstall
python3 -c "import pyttsx3; print('OK')"

# 2. Test pyttsx3 init
python3 -c "import pyttsx3; engine = pyttsx3.init(); print('Init OK')"

# 3. Check available voices
python3 -c "import pyttsx3; engine = pyttsx3.init(); voices = engine.getProperty('voices'); print([v.name for v in voices])"
```

**Solution:**
- Jika pyttsx3 benar-benar tidak bisa init, fallback ke espeak adalah expected behavior
- Jika pyttsx3 bisa init tapi masih fallback, check logs untuk error details

### Issue: Voice Tidak Berbicara

**Check:**
```bash
# 1. Test pyttsx3 langsung
python3 -c "import pyttsx3; engine = pyttsx3.init(); engine.say('Test'); engine.runAndWait()"

# 2. Check audio output
speaker-test -t wav -c 2

# 3. Check logs untuk error
grep "Error in TTS playback" logs/*.log
```

## 📝 Code Changes

### File: `local_machine/audio_controller.py`

**Improved:**
- Better error handling untuk voice setting
- Try-catch untuk setiap property setting
- Continue dengan default jika voice setting gagal
- Hanya fallback jika pyttsx3 benar-benar tidak bisa init

**Key Changes:**
1. Voice iteration dengan error handling
2. Property setting dengan individual try-catch
3. Graceful degradation (tidak crash)
4. Better logging untuk debugging

## 🎯 Benefits

1. ✅ **pyttsx3 tetap digunakan** meskipun voice setting gagal
2. ✅ **Lebih reliable** - tidak crash karena voice error
3. ✅ **Better user experience** - tetap bisa berbicara
4. ✅ **Smart fallback** - hanya fallback jika benar-benar perlu
5. ✅ **Better logging** - lebih informatif untuk debugging

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
- Check logs untuk "✅ TTS engine initialized (pyttsx3)"
- Test voice command dari Web UI
- Verify audio berbicara via pyttsx3 (bukan espeak)

## ✅ Success Indicators

- ✅ Log: "✅ TTS engine initialized (pyttsx3)" (tidak ada fallback warning)
- ✅ Voice command berbicara via pyttsx3
- ✅ No errors di logs terkait voice setting
- ✅ Audio output di speaker

## 📚 Referensi

- pyttsx3 docs: https://pyttsx3.readthedocs.io/
- Voice setting: https://pyttsx3.readthedocs.io/en/latest/engine.html#pyttsx3.engine.Engine.setProperty
- Error handling best practices: https://docs.python.org/3/tutorial/errors.html

---

**Status:** ✅ Fixed  
**Date:** 5 Januari 2026  
**Version:** 2.2

