# 🚀 Panduan Deploy WHAC IoT ke VPS dengan Docker

Panduan lengkap untuk deploy sistem WHAC Fingerprint ke VPS menggunakan Docker dan Git.

## 📋 Prerequisites

1. **VPS dengan spesifikasi minimal:**
   - RAM: 2GB (recommended 4GB)
   - Storage: 10GB free space
   - OS: Ubuntu 20.04/22.04 atau Debian 11/12
   - Port terbuka: 4545 (Web UI), 5432 (PostgreSQL - optional jika ingin akses eksternal)

2. **Software yang dibutuhkan:**
   - Docker & Docker Compose
   - Git
   - SSH access ke VPS

3. **MQTT Broker Eksternal:**
   - Sudah tersedia di: `103.87.67.139:1883`
   - Pastikan VPS bisa akses ke broker ini

---

## 🔧 LANGKAH 1: Setup Awal VPS

### 1.1 Login ke VPS via SSH

```bash
ssh root@YOUR_VPS_IP
# atau
ssh your_username@YOUR_VPS_IP
```

### 1.2 Update sistem

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3 Install Docker

```bash
# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Verify Docker installation
sudo docker --version
```

### 1.4 Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### 1.5 Add user ke Docker group (optional, untuk non-root user)

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 1.6 Enable Docker service

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

---

## 📦 LANGKAH 2: Clone Repository dari Git

### 2.1 Install Git (jika belum ada)

```bash
sudo apt install -y git
```

### 2.2 Clone repository Anda

```bash
# Pindah ke direktori home atau direktori pilihan Anda
cd ~

# Clone repository (ganti dengan URL repository Anda)
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

# Masuk ke direktori project
cd YOUR_REPOSITORY/V2

# Atau jika structure berbeda, sesuaikan path-nya
```

**Catatan:** Ganti `YOUR_USERNAME/YOUR_REPOSITORY` dengan URL Git repository Anda yang sebenarnya.

### 2.3 Verify files

```bash
# Check apakah semua file penting ada
ls -la

# Harus ada:
# - docker-compose.vps.yml
# - vps-env.example
# - web_ui/
# - server/ (optional)
```

---

## ⚙️ LANGKAH 3: Konfigurasi Environment Variables

### 3.1 Copy template environment file

```bash
cp vps-env.example .env
```

### 3.2 Edit file .env

```bash
nano .env
# atau gunakan vim/vi
```

### 3.3 Konfigurasi yang WAJIB diubah:

```env
# ============================================
# DATABASE CONFIGURATION
# ============================================
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
# GANTI PASSWORD INI! Gunakan password yang kuat
DB_PASSWORD=YourStrongPasswordHere123!
DB_PORT=5432

# ============================================
# MQTT BROKER CONFIGURATION (EKSTERNAL)
# ============================================
# Gunakan IP broker MQTT yang sudah ada
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883

# MQTT Topics (sesuaikan dengan konfigurasi Anda)
MQTT_ACTION_TOPIC=WHAC/Store001/action
MQTT_SCAN_TOPIC=WHAC/Store001/in
MQTT_VOICE_COMMAND_TOPIC=WHAC/Store001/voice_command
MQTT_VOICE_RESPONSE_TOPIC=WHAC/Store001/voice_response
MQTT_AUDIO_TOPIC=WHAC/Store001/audio
MQTT_AUDIO_RESPONSE_TOPIC=WHAC/Store001/audio_response
MQTT_GPIO_LOG_TOPIC=WHAC/Store001/gpio_log
MQTT_ALARM_TOPIC=WHAC/Store001/alarm

# ============================================
# WEB UI CONFIGURATION
# ============================================
# Port untuk akses Web UI dari luar
WEB_PORT=4545

# Flask Environment
FLASK_ENV=production

# GANTI SECRET KEY INI! Generate random string
# Gunakan: openssl rand -hex 64
SECRET_KEY=YourVeryLongRandomSecretKeyHere123456789abcdef

# ============================================
# STORE/DEVICE CONFIGURATION
# ============================================
STORE_ID=Store001

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
```

### 3.4 Generate secure passwords dan keys:

```bash
# Generate DB Password
openssl rand -base64 32

# Generate SECRET_KEY
openssl rand -hex 64
```

Copy hasil generate di atas ke file `.env` Anda.

### 3.5 Set permission untuk keamanan

```bash
chmod 600 .env
```

---

## 🔥 LANGKAH 4: Setup Firewall (UFW)

### 4.1 Install UFW (jika belum ada)

```bash
sudo apt install -y ufw
```

### 4.2 Konfigurasi firewall

```bash
# Allow SSH (PENTING! Jangan lupa ini!)
sudo ufw allow 22/tcp

# Allow Web UI port
sudo ufw allow 4545/tcp

# Allow PostgreSQL (optional, hanya jika ingin akses dari luar)
# sudo ufw allow 5432/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## 🐳 LANGKAH 5: Deploy dengan Docker Compose

### 5.1 Buat file docker-compose khusus VPS (sudah ada: docker-compose.vps.yml)

File `docker-compose.vps.yml` sudah dikonfigurasi untuk deployment VPS dengan:
- PostgreSQL database
- Web UI pada port 4545
- Koneksi ke MQTT broker eksternal (103.87.67.139)
- MQTT processor (optional)

### 5.2 Build dan jalankan containers

```bash
# Pull images dan build
docker-compose -f docker-compose.vps.yml pull
docker-compose -f docker-compose.vps.yml build

# Start services
docker-compose -f docker-compose.vps.yml up -d

# Monitor logs
docker-compose -f docker-compose.vps.yml logs -f
```

### 5.3 Tunggu semua service running

```bash
# Check status
docker-compose -f docker-compose.vps.yml ps

# Harus menunjukkan semua service UP:
# - whac-postgres (healthy)
# - whac-db-init (exited/completed)
# - whac-web-ui (healthy)
# - whac-mqtt-processor (optional)
```

---

## ✅ LANGKAH 6: Verifikasi Deployment

### 6.1 Check containers

```bash
docker ps
```

Output harus menunjukkan containers yang running.

### 6.2 Check logs

```bash
# Check Web UI logs
docker logs whac-web-ui

# Check database logs
docker logs whac-postgres

# Check specific service
docker-compose -f docker-compose.vps.yml logs web-ui
```

### 6.3 Test akses Web UI

```bash
# Dari VPS
curl http://localhost:4545

# Atau dari browser:
http://YOUR_VPS_IP:4545
```

### 6.4 Test koneksi MQTT

```bash
# Install mosquitto clients
sudo apt install -y mosquitto-clients

# Test subscribe
mosquitto_sub -h 103.87.67.139 -p 1883 -t "WHAC/Store001/#" -v

# Test publish (dari terminal lain)
mosquitto_pub -h 103.87.67.139 -p 1883 -t "WHAC/Store001/test" -m "Hello from VPS"
```

### 6.5 Check database

```bash
# Connect ke database container
docker exec -it whac-postgres psql -U postgres -d whac_master

# List tables
\dt

# Check users table
SELECT username, role FROM users;

# Exit
\q
```

---

## 🔄 LANGKAH 7: Management Commands

### 7.1 Stop services

```bash
docker-compose -f docker-compose.vps.yml stop
```

### 7.2 Start services

```bash
docker-compose -f docker-compose.vps.yml start
```

### 7.3 Restart services

```bash
docker-compose -f docker-compose.vps.yml restart
```

### 7.4 Stop dan remove containers

```bash
docker-compose -f docker-compose.vps.yml down
```

### 7.5 Stop dan remove dengan volumes (HATI-HATI: akan hapus data!)

```bash
docker-compose -f docker-compose.vps.yml down -v
```

### 7.6 View logs

```bash
# All services
docker-compose -f docker-compose.vps.yml logs -f

# Specific service
docker-compose -f docker-compose.vps.yml logs -f web-ui

# Last 100 lines
docker-compose -f docker-compose.vps.yml logs --tail=100
```

### 7.7 Update dari Git

```bash
# Stop services
docker-compose -f docker-compose.vps.yml stop

# Pull latest changes
git pull origin main  # atau branch Anda

# Rebuild (jika ada perubahan code)
docker-compose -f docker-compose.vps.yml build

# Start services
docker-compose -f docker-compose.vps.yml up -d
```

---

## 🔐 LANGKAH 8: Setup SSL/HTTPS dengan Nginx (Optional tapi Recommended)

### 8.1 Install Nginx

```bash
sudo apt install -y nginx
```

### 8.2 Install Certbot untuk SSL gratis

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 8.3 Konfigurasi Nginx reverse proxy

```bash
sudo nano /etc/nginx/sites-available/whac
```

Isi dengan:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Ganti dengan domain Anda

    location / {
        proxy_pass http://localhost:4545;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support untuk SocketIO
    location /socket.io {
        proxy_pass http://localhost:4545;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
    }

    client_max_body_size 10M;
}
```

### 8.4 Enable site

```bash
sudo ln -s /etc/nginx/sites-available/whac /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8.5 Get SSL certificate

```bash
sudo certbot --nginx -d your-domain.com
```

### 8.6 Setup auto-renewal

```bash
sudo certbot renew --dry-run
```

---

## 📊 LANGKAH 9: Monitoring & Maintenance

### 9.1 Check resource usage

```bash
# Docker stats
docker stats

# Disk usage
docker system df

# Specific container
docker stats whac-web-ui
```

### 9.2 Setup log rotation

```bash
sudo nano /etc/docker/daemon.json
```

Tambahkan:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:

```bash
sudo systemctl restart docker
```

### 9.3 Backup database

```bash
# Backup
docker exec whac-postgres pg_dump -U postgres whac_master > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
cat backup_20240101_120000.sql | docker exec -i whac-postgres psql -U postgres whac_master
```

### 9.4 Auto-restart on reboot

```bash
# Docker Compose akan auto-restart containers karena setting restart: unless-stopped
# Pastikan Docker service enabled
sudo systemctl enable docker
```

---

## 🚨 Troubleshooting

### Problem: Container tidak start

```bash
# Check logs
docker-compose -f docker-compose.vps.yml logs

# Check specific service
docker logs whac-web-ui --tail=50
```

### Problem: Tidak bisa akses Web UI

```bash
# Check if port is listening
sudo netstat -tlnp | grep 4545

# Check firewall
sudo ufw status

# Check container
docker ps | grep whac-web-ui

# Check logs
docker logs whac-web-ui
```

### Problem: Database connection error

```bash
# Check PostgreSQL container
docker logs whac-postgres

# Check if database is healthy
docker exec whac-postgres pg_isready -U postgres

# Try connect manually
docker exec -it whac-postgres psql -U postgres -d whac_master
```

### Problem: MQTT connection error

```bash
# Test dari VPS
mosquitto_sub -h 103.87.67.139 -p 1883 -t "test" -v

# Check if VPS can reach MQTT broker
ping 103.87.67.139
telnet 103.87.67.139 1883

# Check container logs
docker logs whac-web-ui | grep -i mqtt
```

### Problem: Out of disk space

```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Remove old images
docker image prune -a
```

---

## 📝 Checklist Deployment

- [ ] VPS siap dengan spesifikasi minimal
- [ ] Docker & Docker Compose terinstall
- [ ] Repository di-clone dari Git
- [ ] File `.env` dikonfigurasi dengan password kuat
- [ ] Firewall dikonfigurasi (UFW)
- [ ] Port 4545 terbuka
- [ ] Containers berjalan dengan `docker-compose up -d`
- [ ] Web UI bisa diakses di `http://VPS_IP:4545`
- [ ] Koneksi ke MQTT broker eksternal berfungsi
- [ ] Database berjalan dan terisi
- [ ] SSL/HTTPS dikonfigurasi (optional)
- [ ] Backup strategy diimplementasikan

---

## 🎯 Default Login

Setelah deployment berhasil, akses Web UI:

```
URL: http://YOUR_VPS_IP:4545
Username: admin
Password: admin123
```

**PENTING:** Ganti password default setelah login pertama kali!

---

## 📞 Support

Jika mengalami masalah:

1. Check logs: `docker-compose -f docker-compose.vps.yml logs -f`
2. Check container status: `docker ps -a`
3. Check system resources: `docker stats`
4. Review troubleshooting section di atas

---

## 🔄 Update System

Untuk update sistem:

```bash
# 1. Pull latest code
git pull origin main

# 2. Backup database
docker exec whac-postgres pg_dump -U postgres whac_master > backup_before_update.sql

# 3. Stop services
docker-compose -f docker-compose.vps.yml down

# 4. Rebuild
docker-compose -f docker-compose.vps.yml build --no-cache

# 5. Start services
docker-compose -f docker-compose.vps.yml up -d

# 6. Check logs
docker-compose -f docker-compose.vps.yml logs -f
```

---

**Selamat! Sistem WHAC Fingerprint Anda sekarang sudah running di VPS! 🎉**


