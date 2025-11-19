# 🐳 Panduan Penggunaan Docker - Sistem WHAC Fingerprint

Panduan lengkap untuk menggunakan sistem WHAC Fingerprint dengan Docker.

## 📋 Daftar Isi

1. [Persiapan](#persiapan)
2. [Instalasi Docker](#instalasi-docker)
3. [Deploy Web UI (VPS)](#deploy-web-ui-vps)
4. [Deploy Local Machine (Raspberry Pi)](#deploy-local-machine-raspberry-pi)
5. [Deploy Server (VPS) - Opsional](#deploy-server-vps---opsional)
6. [Monitoring dan Troubleshooting](#monitoring-dan-troubleshooting)
7. [Perintah Penting](#perintah-penting)

---

## 🛠️ Persiapan

### Persyaratan Sistem

**Untuk VPS (Web UI + Database):**
- Ubuntu/Debian server
- Docker dan Docker Compose terpasang
- Port terbuka: 5000 (Web UI), 5432 (PostgreSQL)
- Minimum 2GB RAM, 10GB storage

**Untuk Raspberry Pi (Local Machine):**
- Raspberry Pi OS
- Docker dan Docker Compose terpasang
- AS608 fingerprint sensor terhubung
- Port serial tersedia (`/dev/serial0` atau `/dev/ttyUSB0`)

---

## 📦 Instalasi Docker

### Di Ubuntu/Debian (VPS)

```bash
# Update sistem
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Tambahkan user ke grup docker (opsional, untuk tidak perlu sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verifikasi instalasi
docker --version
docker-compose --version
```

### Di Raspberry Pi

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Tambahkan user ke grup docker
sudo usermod -aG docker $USER
sudo usermod -aG dialout $USER  # Untuk akses serial port
newgrp docker

# Verifikasi
docker --version
docker-compose --version
```

---

## 🌐 Deploy Web UI (VPS)

### Langkah 1: Clone Repository

```bash
# Clone repository (atau copy file ke VPS)
git clone <repository-url>
cd IoT-WHAC/V2/web_ui
```

### Langkah 2: Konfigurasi Environment

```bash
# Copy file environment template
cp env.example .env

# Edit konfigurasi
nano .env
```

**Isi file `.env`:**

```env
# Database Configuration
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
DB_PORT=5432

# MQTT Configuration
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_ACTION_TOPIC=WHAC/Store001/action
MQTT_SCAN_TOPIC=WHAC/Store001/in

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=whac_fingerprint_secret_key
```

**⚠️ PENTING:** Ganti `DB_PASSWORD` dan `SECRET_KEY` dengan password yang kuat untuk production!

### Langkah 3: Build dan Jalankan

```bash
# Build dan jalankan container
docker-compose up -d

# Cek status container
docker-compose ps

# Lihat logs
docker-compose logs -f
```

### Langkah 4: Verifikasi

```bash
# Cek apakah Web UI berjalan
curl http://localhost:5000

# Atau buka di browser
# http://your-vps-ip:5000
```

**Default Login:**
- Username: `admin`
- Password: `admin123` (atau sesuai yang di-setup di database)

---

## 🔌 Deploy Local Machine (Raspberry Pi)

### Langkah 1: Persiapan

```bash
# Masuk ke direktori local_machine
cd IoT-WHAC/V2/local_machine

# Pastikan sensor terhubung
ls -la /dev/tty* | grep -E "ttyUSB|serial|ACM"
```

### Langkah 2: Konfigurasi Environment

```bash
# Copy file environment template
cp env.example .env

# Edit konfigurasi
nano .env
```

**Isi file `.env`:**

```env
STORE_ID=Store001
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
MQTT_TOPIC=WHAC/Store001/in
FINGERPRINT_PORT=/dev/serial0
BAUD_RATE=57600
CONFIDENCE_THRESHOLD=50
SCAN_INTERVAL=5
LOG_LEVEL=INFO
```

**⚠️ PENTING:** 
- Ganti `FINGERPRINT_PORT` sesuai port sensor Anda
- Ganti `MQTT_BROKER` dengan IP VPS Anda

### Langkah 3: Set Permission Serial Port

```bash
# Tambahkan user ke grup dialout
sudo usermod -aG dialout $USER
newgrp dialout

# Set permission untuk serial port
sudo chmod 666 /dev/serial0
# atau
sudo chmod 666 /dev/ttyUSB0
```

### Langkah 4: Build dan Jalankan

```bash
# Build dan jalankan container
docker-compose up -d

# Cek status
docker-compose ps

# Lihat logs
docker-compose logs -f fingerprint-scanner
```

### Langkah 5: Verifikasi

```bash
# Cek koneksi MQTT
docker logs whac-fingerprint-scanner | grep -i "mqtt\|connected"

# Test scan fingerprint (jika sensor terhubung)
# Logs akan menampilkan hasil scan
```

---

## 🖥️ Deploy Server (VPS) - Opsional

Server ini untuk memproses data MQTT dan menyimpan ke database. Jika Web UI sudah menangani ini, server ini opsional.

### Langkah 1: Konfigurasi

```bash
cd IoT-WHAC/V2/server
cp env.example .env
nano .env
```

**Isi file `.env`:**

```env
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
DB_PORT=5432
SCAN_TOPIC=WHAC/Store001/in
ACTION_TOPIC=WHAC/Store001/action
STATUS_TOPIC=WHAC/Store001/status
```

### Langkah 2: Jalankan

```bash
docker-compose up -d
docker-compose logs -f
```

---

## 📊 Monitoring dan Troubleshooting

### Melihat Logs

```bash
# Web UI
cd web_ui
docker-compose logs -f web-ui

# Local Machine
cd local_machine
docker-compose logs -f fingerprint-scanner

# Server
cd server
docker-compose logs -f mqtt-processor

# Database
docker-compose logs -f postgres
```

### Cek Status Container

```bash
# Semua container
docker ps

# Container tertentu
docker ps | grep whac

# Detail container
docker inspect whac-web-ui
```

### Masuk ke Container

```bash
# Masuk ke container Web UI
docker exec -it whac-web-ui /bin/bash

# Masuk ke container Local Machine
docker exec -it whac-fingerprint-scanner /bin/bash

# Masuk ke database
docker exec -it whac-postgres psql -U postgres -d whac_master
```

### Troubleshooting Umum

#### 1. Container Tidak Bisa Start

```bash
# Cek logs error
docker-compose logs

# Cek resource
docker stats

# Restart container
docker-compose restart
```

#### 2. Database Connection Error

```bash
# Cek apakah database running
docker ps | grep postgres

# Cek koneksi dari Web UI
docker exec -it whac-web-ui python3 -c "import psycopg2; psycopg2.connect(host='postgres', dbname='whac_master', user='postgres', password='Admin123')"

# Cek logs database
docker logs whac-postgres
```

#### 3. MQTT Connection Error

```bash
# Test koneksi MQTT dari container
docker exec -it whac-fingerprint-scanner python3 -c "
import paho.mqtt.client as mqtt
client = mqtt.Client()
client.connect('103.87.67.139', 1883, 60)
print('MQTT Connected!')
"

# Cek firewall
sudo ufw status
sudo ufw allow 1883/tcp
```

#### 4. Serial Port Tidak Terdeteksi

```bash
# Cek device
ls -la /dev/tty* | grep -E "USB|serial|ACM"

# Set permission
sudo chmod 666 /dev/serial0

# Cek dari container
docker exec -it whac-fingerprint-scanner ls -la /dev/tty*
```

#### 5. Web UI Tidak Bisa Diakses

```bash
# Cek port terbuka
sudo netstat -tulpn | grep 5000

# Cek firewall
sudo ufw allow 5000/tcp

# Cek logs
docker logs whac-web-ui

# Restart container
docker-compose restart web-ui
```

---

## 🎯 Perintah Penting

### Management Container

```bash
# Start semua service
docker-compose up -d

# Stop semua service
docker-compose down

# Restart service tertentu
docker-compose restart web-ui

# Rebuild container
docker-compose up -d --build

# Hapus container dan volume (HATI-HATI!)
docker-compose down -v
```

### Database Management

```bash
# Backup database
docker exec whac-postgres pg_dump -U postgres whac_master > backup.sql

# Restore database
docker exec -i whac-postgres psql -U postgres whac_master < backup.sql

# Masuk ke database
docker exec -it whac-postgres psql -U postgres -d whac_master

# Cek tabel
docker exec -it whac-postgres psql -U postgres -d whac_master -c "\dt"
```

### Update dan Maintenance

```bash
# Pull update terbaru
git pull

# Rebuild container dengan update
docker-compose up -d --build

# Clean up old images
docker image prune -a

# Clean up unused volumes (HATI-HATI!)
docker volume prune
```

### Monitoring Resources

```bash
# Monitor resource usage
docker stats

# Disk usage
docker system df

# Inspect network
docker network inspect whac-network
```

---

## 🔐 Security Best Practices

1. **Ganti Password Default**
   ```bash
   # Edit .env file
   nano web_ui/.env
   # Ganti DB_PASSWORD dan SECRET_KEY
   ```

2. **Firewall Configuration**
   ```bash
   sudo ufw allow 5000/tcp  # Web UI
   sudo ufw allow 5432/tcp  # PostgreSQL (hanya internal)
   sudo ufw allow 1883/tcp  # MQTT
   sudo ufw enable
   ```

3. **Regular Updates**
   ```bash
   # Update sistem
   sudo apt update && sudo apt upgrade -y
   
   # Update Docker images
   docker-compose pull
   docker-compose up -d
   ```

4. **Backup Regular**
   ```bash
   # Buat script backup
   #!/bin/bash
   docker exec whac-postgres pg_dump -U postgres whac_master > backup_$(date +%Y%m%d).sql
   ```

---

## 📝 Checklist Deployment

### Web UI (VPS)
- [ ] Docker dan Docker Compose terpasang
- [ ] File `.env` dikonfigurasi
- [ ] Port 5000 terbuka
- [ ] Container berjalan (`docker ps`)
- [ ] Web UI bisa diakses di browser
- [ ] Database terhubung

### Local Machine (Raspberry Pi)
- [ ] Docker dan Docker Compose terpasang
- [ ] Sensor AS608 terhubung
- [ ] Serial port terdeteksi
- [ ] File `.env` dikonfigurasi
- [ ] Permission serial port OK
- [ ] Container berjalan
- [ ] MQTT terhubung ke broker

### Verifikasi Sistem
- [ ] Web UI bisa login
- [ ] Fingerprint scan terdeteksi di Web UI
- [ ] Data tersimpan di database
- [ ] MQTT messages terkirim dan diterima

---

## 🆘 Bantuan

Jika mengalami masalah:

1. **Cek Logs**: `docker-compose logs -f`
2. **Cek Status**: `docker ps`
3. **Cek Network**: `docker network inspect whac-network`
4. **Cek Resource**: `docker stats`

Untuk bantuan lebih lanjut, lihat:
- `README_DOCKER.md`
- `DOCKER_DEPLOYMENT_GUIDE.md`
- Dokumentasi di setiap folder komponen

---

**Selamat menggunakan Sistem WHAC Fingerprint dengan Docker! 🎉**

