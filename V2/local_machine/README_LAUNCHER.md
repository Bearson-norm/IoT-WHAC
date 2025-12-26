# 🚀 Quick Start - Launcher Sistem

## Cara Menjalankan Kedua Program Bersamaan

### ⭐ Recommended: Python Launcher

```bash
cd local_machine
python3 start_local_system.py
```

**Fitur:**
- ✅ Monitoring proses otomatis
- ✅ Auto-restart jika crash
- ✅ Graceful shutdown (Ctrl+C)
- ✅ Logging terpusat

---

### Alternatif: Shell Script (Linux)

```bash
cd local_machine
./start_local_system.sh
```

---

### Alternatif: Batch Script (Windows)

```powershell
cd local_machine
start_local_system.bat
```

---

## 📋 Yang Perlu Diperhatikan

1. **GPIO Configuration**: 
   - `fingerprint_multi_client.py` → Relay control **DISABLED** ✅
   - `relay_controller_advanced.py` → GPIO 23, 24, 25 ✅

2. **Port Serial**: 
   - Auto-detection atau set di `config.py`
   - Tidak ada konflik karena menggunakan port lock

3. **MQTT**: 
   - Unique client ID untuk setiap program
   - Tidak ada konflik

---

## 📝 Log Files

- `local_system.log` - Launcher log
- `fingerprint_multi_client.log` - Fingerprint client log
- `relay_controller_advanced.log` - Relay controller log

---

## 🛑 Stop Program

Tekan **Ctrl+C** untuk graceful shutdown.

---

## 📚 Dokumentasi Lengkap

Lihat **`PANDUAN_LAUNCHER_SISTEM.md`** untuk detail lengkap.

---

**Selamat menggunakan! 🎉**

