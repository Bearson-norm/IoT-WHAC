# ⚡ Quick Start Docker - Sistem WHAC Fingerprint

Panduan cepat untuk menjalankan sistem WHAC Fingerprint dengan Docker dalam 5 menit!

## 🚀 Quick Start (3 Langkah)

### 1️⃣ Deploy Web UI di VPS

```bash
cd web_ui
cp env.example .env
nano .env  # Edit konfigurasi jika perlu
docker-compose up -d
```

**Akses:** `http://your-vps-ip:5000`

### 2️⃣ Deploy Local Machine di Raspberry Pi

```bash
cd local_machine
cp env.example .env
nano .env  # Edit MQTT_BROKER dengan IP VPS Anda
docker-compose up -d
```

### 3️⃣ Verifikasi

```bash
# Cek Web UI
curl http://localhost:5000

# Cek logs Local Machine
docker-compose logs -f
```

---

## 📝 Menggunakan Quick Start Script

### Linux/macOS

```bash
# Web UI (VPS)
./quick-start-docker.sh web

# Local Machine (Raspberry Pi)
./quick-start-docker.sh local
```

### Windows

```cmd
REM Web UI (VPS)
quick-start-docker.bat web

REM Local Machine (Raspberry Pi)
quick-start-docker.bat local
```

---

## ⚙️ Konfigurasi Minimal

### Web UI (.env)

```env
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
MQTT_BROKER=103.87.67.139
```

### Local Machine (.env)

```env
MQTT_BROKER=103.87.67.139  # IP VPS Anda
FINGERPRINT_PORT=/dev/serial0
```

---

## 🔍 Perintah Penting

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild
docker-compose up -d --build
```

---

## 📚 Dokumentasi Lengkap

Untuk panduan detail, lihat:
- **PANDUAN_DOCKER_INDONESIA.md** - Panduan lengkap dalam Bahasa Indonesia
- **README_DOCKER.md** - Dokumentasi umum
- **DOCKER_DEPLOYMENT_GUIDE.md** - Panduan deployment detail

---

**Selamat! Sistem Anda sudah berjalan! 🎉**

