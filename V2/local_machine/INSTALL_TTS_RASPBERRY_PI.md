# 🔊 Install TTS (pyttsx3) di Raspberry Pi

## ⚠️ Catatan Penting

**Jangan typo!** Pastikan mengetik dengan benar:
- ✅ **`pyttsx3`** (benar - ada 's')
- ❌ **`pyttx3`** (salah - kurang 's')

## 🚀 Langkah Instalasi

### Step 1: Install Dependencies Sistem (jika belum)

```bash
# Update package list
sudo apt-get update

# Install espeak dan dependencies
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev

# Install Python development headers (diperlukan untuk beberapa package)
sudo apt-get install -y python3-dev python3-pip
```

### Step 2: Install pyttsx3

```bash
# Pastikan virtual environment aktif
source fingerprint-env/bin/activate  # atau: . fingerprint-env/bin/activate

# Install pyttsx3 (PERHATIKAN: pyttsx3 dengan 's')
pip install pyttsx3

# Atau install dari requirements.txt
pip install -r requirements.txt
```

### Step 3: Verifikasi Instalasi

```bash
# Test TTS
python3 -c "import pyttsx3; engine = pyttsx3.init(); engine.say('Test suara'); engine.runAndWait()"
```

**Expected Output:**
```
✅ TTS engine initialized
🔊 Speaking: Test suara
✅ TTS playback completed
```

## 🔍 Troubleshooting

### Issue 1: "No matching distribution found for pyttx3"

**Penyebab:** Typo - mengetik `pyttx3` bukan `pyttsx3`

**Solusi:**
```bash
# Pastikan mengetik dengan benar
pip install pyttsx3  # ← Ada 's' di sini!
```

### Issue 2: "ERROR: Could not find a version that satisfies the requirement"

**Penyebab:** Dependencies sistem belum terinstall

**Solusi:**
```bash
# Install dependencies
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev python3-dev
pip install pyttsx3
```

### Issue 3: "ImportError: No module named 'pyttsx3'"

**Penyebab:** Virtual environment tidak aktif atau install di environment yang salah

**Solusi:**
```bash
# Pastikan virtual environment aktif
source fingerprint-env/bin/activate

# Install lagi
pip install pyttsx3

# Verifikasi
python3 -c "import pyttsx3; print('OK')"
```

### Issue 4: TTS tidak berbicara (silent)

**Penyebab:** Audio output tidak dikonfigurasi

**Solusi:**
```bash
# Test speaker
speaker-test -t wav -c 2

# Set default audio output
sudo raspi-config
# Pilih: Advanced Options → Audio → Force 3.5mm jack

# Atau set via command
sudo amixer cset numid=3 1  # 3.5mm jack
sudo amixer cset numid=3 2  # HDMI
```

### Issue 5: TTS berbicara dalam bahasa Inggris

**Penyebab:** Voice Indonesia tidak tersedia

**Solusi:**
```bash
# Install Indonesian voice (jika tersedia)
sudo apt-get install -y espeak-data-id

# Atau gunakan default voice (akan tetap bekerja)
# Sistem akan otomatis mencoba mencari voice Indonesia
```

## 📋 Checklist Instalasi

- [ ] espeak terinstall: `which espeak` → `/usr/bin/espeak` ✅
- [ ] Virtual environment aktif: `source fingerprint-env/bin/activate`
- [ ] pyttsx3 terinstall: `pip list | grep pyttsx3`
- [ ] TTS test berhasil: `python3 -c "import pyttsx3; ..."`
- [ ] Audio output bekerja: `speaker-test -t wav -c 2`
- [ ] Restart local machine: `python3 fingerprint_multi_client.py`

## 🎯 Quick Install Script

```bash
#!/bin/bash
# Quick install TTS untuk Raspberry Pi

echo "🔊 Installing TTS dependencies..."

# Install system dependencies
sudo apt-get update
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev python3-dev

# Activate virtual environment
source fingerprint-env/bin/activate

# Install pyttsx3
pip install pyttsx3

# Test installation
echo "🧪 Testing TTS..."
python3 -c "import pyttsx3; engine = pyttsx3.init(); engine.say('TTS berhasil diinstall'); engine.runAndWait()"

echo "✅ TTS installation complete!"
```

## 🔄 Alternatif: Gunakan espeak Langsung (Lebih Ringan)

Jika pyttsx3 masih bermasalah, bisa gunakan espeak langsung:

```python
import subprocess

def speak_espeak(text):
    """Use espeak directly (lighter than pyttsx3)"""
    subprocess.run(['espeak', '-v', 'id', text])
```

**Keuntungan:**
- ✅ Lebih ringan (tidak perlu Python wrapper)
- ✅ Langsung menggunakan espeak
- ✅ Lebih cepat

**Kerugian:**
- ❌ Tidak ada kontrol rate/volume via Python
- ❌ Perlu subprocess call

## 📊 Resource Usage Comparison

| Method | CPU | RAM | Setup |
|--------|-----|-----|-------|
| **pyttsx3** | 5-15% | 10-15 MB | pip install |
| **espeak direct** | 3-10% | 5-10 MB | apt-get install |
| **Audio MP3** | 2-5% | 5-10 MB | Copy files |

## ✅ Verifikasi Final

Setelah install, restart local machine:

```bash
cd ~/IoT-WHAC/V2/local_machine
python3 fingerprint_multi_client.py
```

**Expected Log:**
```
✅ TTS engine initialized
✅ AudioController initialized
✓ Subscribed to command topics (including audio and voice commands)
```

## 🆘 Masih Bermasalah?

Jika masih error, coba:

1. **Update pip:**
   ```bash
   pip install --upgrade pip
   pip install pyttsx3
   ```

2. **Install dari source:**
   ```bash
   pip install git+https://github.com/nateshmbhat/pyttsx3.git
   ```

3. **Gunakan alternatif:**
   - Gunakan audio file MP3 (tidak perlu TTS)
   - Gunakan espeak langsung via subprocess

## 📚 Referensi

- pyttsx3 docs: https://pyttsx3.readthedocs.io/
- espeak docs: http://espeak.sourceforge.net/
- Raspberry Pi audio: https://www.raspberrypi.org/documentation/configuration/audio/

---

**Status:** ✅ Ready to Use  
**Last Updated:** 4 Januari 2026

