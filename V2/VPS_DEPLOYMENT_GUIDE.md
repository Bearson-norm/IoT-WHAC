# 🚀 Panduan Deploy ke VPS - Port 4545

Panduan lengkap untuk deploy sistem WHAC Fingerprint ke VPS menggunakan Docker dan Git.

## 📋 Daftar Isi

1. [Persiapan VPS](#persiapan-vps)
2. [Instalasi Docker di VPS](#instalasi-docker-di-vps)
3. [Clone Repository dari Git](#clone-repository-dari-git)
4. [Konfigurasi Environment](#konfigurasi-environment)
5. [Deploy dengan Docker](#deploy-dengan-docker)
6. [Verifikasi Deployment](#verifikasi-deployment)
7. [Maintenance dan Monitoring](#maintenance-dan-monitoring)
8. [Troubleshooting](#troubleshooting)

---

## 🖥️ Persiapan VPS

### Persyaratan Sistem

- **OS**: Ubuntu 20.04/22.04 atau Debian 11/12
- **RAM**: Minimum 2GB (Rekomendasi 4GB)
- **Storage**: Minimum 20GB
- **Akses**: SSH dengan user yang memiliki sudo privileges

### Port yang Dibutuhkan

```bash
4545  # Web UI (Flask)
5432  # PostgreSQL Database
1883  # MQTT Broker (internal)
```

### Firewall Configuration

```bash
# Allow SSH (jika belum)
sudo ufw allow 22/tcp

# Allow Web UI port
sudo ufw allow 4545/tcp

# Allow PostgreSQL (hanya jika butuh akses eksternal)
sudo ufw allow 5432/tcp

# Allow MQTT (hanya jika butuh akses eksternal)
sudo ufw allow 1883/tcp

# Enable firewall
sudo ufw enable

# Cek status
sudo ufw status
```

---

## 🐳 Instalasi Docker di VPS

### Langkah 1: Update Sistem

```bash
# Login ke VPS via SSH
ssh user@your-vps-ip

# Update sistem
sudo apt update && sudo apt upgrade -y
```

### Langkah 2: Install Docker

```bash
# Install dependencies
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Tambahkan Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Tambahkan Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package database
sudo apt update

# Install Docker Engine
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Verifikasi instalasi
docker --version
```

**Expected Output:**
```
Docker version 24.0.x, build xxxxx
```

### Langkah 3: Install Docker Compose

```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Set executable permissions
sudo chmod +x /usr/local/bin/docker-compose

# Verifikasi instalasi
docker-compose --version
```

**Expected Output:**
```
Docker Compose version v2.x.x
```

### Langkah 4: Configure Docker untuk User

```bash
# Tambahkan user ke grup docker
sudo usermod -aG docker $USER

# Apply grup changes (atau logout dan login kembali)
newgrp docker

# Test docker tanpa sudo
docker run hello-world
```

**Expected Output:**
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

### Langkah 5: Enable Docker Auto-Start

```bash
# Enable Docker service
sudo systemctl enable docker

# Start Docker service
sudo systemctl start docker

# Cek status
sudo systemctl status docker
```

---

## 📥 Clone Repository dari Git

### Langkah 1: Install Git (jika belum ada)

```bash
# Install Git
sudo apt install -y git

# Verifikasi
git --version
```

### Langkah 2: Clone Repository

```bash
# Pindah ke home directory
cd ~

# Clone repository (ganti dengan URL repository Anda)
git clone https://github.com/your-username/IoT-WHAC.git

# Masuk ke direktori proyek
cd IoT-WHAC/V2
```

**Jika repository private:**

```bash
# Clone dengan authentication
git clone https://username:token@github.com/your-username/IoT-WHAC.git

# Atau setup SSH key (lebih aman)
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
# Copy public key ke GitHub Settings > SSH Keys
```

### Langkah 3: Verifikasi File

```bash
# Cek struktur direktori
ls -la

# Pastikan file-file penting ada
ls -la web_ui/
ls -la server/
```

---

## ⚙️ Konfigurasi Environment

### Langkah 1: Setup Environment untuk Web UI

```bash
# Masuk ke direktori VPS config
cd ~/IoT-WHAC/V2

# Copy environment template
cp vps-env.example vps.env

# Edit konfigurasi
nano vps.env
```

**Edit file `vps.env`:**

```env
# Database Configuration
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=GantiPasswordIniDenganYangKuat123!
DB_PORT=5432

# MQTT Configuration
# Gunakan IP VPS Anda atau localhost jika MQTT internal
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_ACTION_TOPIC=WHAC/Store001/action
MQTT_SCAN_TOPIC=WHAC/Store001/in
MQTT_VOICE_COMMAND_TOPIC=WHAC/Store001/voice_command
MQTT_VOICE_RESPONSE_TOPIC=WHAC/Store001/voice_response

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=GantiSecretKeyIniDenganStringRandomYangPanjang456!

# Web UI Port (custom port 4545)
WEB_PORT=4545
```

**⚠️ PENTING - Security:**

1. **Ganti `DB_PASSWORD`** dengan password yang kuat
2. **Ganti `SECRET_KEY`** dengan random string panjang
3. **Jangan commit file `.env` ke Git!**

### Langkah 2: Generate Strong Passwords

```bash
# Generate random password untuk database
openssl rand -base64 32

# Generate random secret key
openssl rand -hex 64
```

Copy hasil generate ke dalam file `vps.env`.

### Langkah 3: Set Environment File Permissions

```bash
# Set permission agar hanya owner yang bisa read
chmod 600 vps.env

# Verifikasi
ls -la vps.env
```

---

## 🚀 Deploy dengan Docker

### Langkah 1: Verifikasi Docker Compose File

```bash
# Cek apakah file ada
ls -la docker-compose.vps.yml

# Preview konfigurasi
cat docker-compose.vps.yml
```

### Langkah 2: Build Docker Images

```bash
# Build images (ini akan memakan waktu 5-10 menit)
docker-compose -f docker-compose.vps.yml --env-file vps.env build

# Cek images yang sudah dibuild
docker images
```

### Langkah 3: Start Services

```bash
# Start semua services dalam background
docker-compose -f docker-compose.vps.yml --env-file vps.env up -d

# Tunggu beberapa saat (30-60 detik) untuk inisialisasi
sleep 60
```

**Expected Output:**
```
Creating network "v2_whac-network" ... done
Creating whac-postgres ... done
Creating whac-db-init ... done
Creating whac-web-ui ... done
Creating whac-mqtt-broker ... done
```

### Langkah 4: Cek Status Services

```bash
# Cek status semua container
docker-compose -f docker-compose.vps.yml ps

# Atau
docker ps
```

**Expected Output:**
```
NAME              STATUS          PORTS
whac-web-ui       Up 1 minute     0.0.0.0:4545->5000/tcp
whac-postgres     Up 2 minutes    0.0.0.0:5432->5432/tcp
whac-mqtt-broker  Up 2 minutes    0.0.0.0:1883->1883/tcp
```

### Langkah 5: View Logs

```bash
# Lihat logs semua services
docker-compose -f docker-compose.vps.yml logs

# Lihat logs specific service dengan follow
docker-compose -f docker-compose.vps.yml logs -f web-ui

# Lihat logs database
docker-compose -f docker-compose.vps.yml logs -f postgres

# Cek logs untuk errors
docker-compose -f docker-compose.vps.yml logs | grep -i error
```

---

## ✅ Verifikasi Deployment

### Langkah 1: Test Web UI dari VPS

```bash
# Test dari dalam VPS
curl http://localhost:4545

# Test health endpoint
curl http://localhost:4545/api/dashboard_stats
```

**Expected Response:**
```html
<!DOCTYPE html>
<html>
...Login page HTML...
</html>
```

### Langkah 2: Test dari Browser External

```bash
# Dapatkan IP VPS Anda
curl ifconfig.me
```

Buka browser dan akses:
```
http://YOUR-VPS-IP:4545
```

**Anda harus melihat login page!**

### Langkah 3: Test Database Connection

```bash
# Masuk ke container postgres
docker exec -it whac-postgres psql -U postgres -d whac_master

# Di dalam psql, jalankan:
\dt  # List semua tables
\q   # Exit
```

**Expected Output:**
```
                List of relations
 Schema |           Name            | Type  |  Owner   
--------+---------------------------+-------+----------
 public | attendance                | table | postgres
 public | employees                 | table | postgres
 public | users                     | table | postgres
...
```

### Langkah 4: Login ke Web UI

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

**⚠️ PENTING:** Segera ganti password admin setelah login pertama kali!

### Langkah 5: Cek Resource Usage

```bash
# Monitor resource usage
docker stats

# Atau untuk snapshot
docker stats --no-stream
```

---

## 🔧 Maintenance dan Monitoring

### Daily Operations

#### View Logs

```bash
# Real-time logs
docker-compose -f docker-compose.vps.yml logs -f

# Logs 100 baris terakhir
docker-compose -f docker-compose.vps.yml logs --tail=100

# Logs dari waktu tertentu
docker-compose -f docker-compose.vps.yml logs --since 2024-01-01T10:00:00
```

#### Restart Services

```bash
# Restart semua services
docker-compose -f docker-compose.vps.yml restart

# Restart service tertentu
docker-compose -f docker-compose.vps.yml restart web-ui

# Stop services
docker-compose -f docker-compose.vps.yml stop

# Start services
docker-compose -f docker-compose.vps.yml start
```

### Database Backup

```bash
# Buat directory untuk backup
mkdir -p ~/backups

# Backup database
docker exec whac-postgres pg_dump -U postgres whac_master > ~/backups/whac_backup_$(date +%Y%m%d_%H%M%S).sql

# Verifikasi backup
ls -lh ~/backups/

# Compress backup untuk save space
gzip ~/backups/whac_backup_*.sql
```

#### Automated Backup Script

Buat file `~/backup_database.sh`:

```bash
#!/bin/bash
# Database backup script

BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/whac_backup_$DATE.sql"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Backup database
docker exec whac-postgres pg_dump -U postgres whac_master > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days backups
find $BACKUP_DIR -name "whac_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

Set executable dan jalankan:

```bash
chmod +x ~/backup_database.sh
./backup_database.sh
```

#### Setup Cron for Auto Backup

```bash
# Edit crontab
crontab -e

# Tambahkan line ini untuk backup setiap hari jam 2 pagi
0 2 * * * /home/$USER/backup_database.sh >> /home/$USER/backup.log 2>&1
```

### Update Application

```bash
# Masuk ke direktori proyek
cd ~/IoT-WHAC/V2

# Pull update terbaru dari Git
git pull origin main

# Rebuild dan restart services
docker-compose -f docker-compose.vps.yml --env-file vps.env up -d --build

# Cek logs untuk pastikan update berhasil
docker-compose -f docker-compose.vps.yml logs -f
```

### System Monitoring

```bash
# Cek disk usage
df -h

# Cek Docker disk usage
docker system df

# Cek memory usage
free -h

# Cek running processes
top
# Atau gunakan htop (lebih user-friendly)
sudo apt install htop
htop
```

### Clean Up Docker

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (HATI-HATI!)
docker volume prune

# Remove unused networks
docker network prune

# Remove everything unused (VERY CAREFUL!)
docker system prune -a --volumes
```

---

## 🔍 Troubleshooting

### Problem 1: Port 4545 Already in Use

**Symptoms:**
```
Error: Bind for 0.0.0.0:4545 failed: port is already allocated
```

**Solution:**
```bash
# Cek process yang menggunakan port 4545
sudo lsof -i :4545

# Atau
sudo netstat -tulpn | grep 4545

# Kill process jika perlu
sudo kill -9 <PID>

# Atau ganti port di vps.env dan docker-compose.vps.yml
```

### Problem 2: Cannot Connect to Web UI

**Symptoms:** Browser tidak bisa akses `http://VPS-IP:4545`

**Solution:**
```bash
# 1. Cek apakah container berjalan
docker ps | grep whac-web-ui

# 2. Cek logs untuk error
docker logs whac-web-ui

# 3. Cek firewall
sudo ufw status
sudo ufw allow 4545/tcp

# 4. Cek apakah service listening
sudo netstat -tulpn | grep 4545

# 5. Test dari dalam VPS
curl http://localhost:4545

# 6. Restart container
docker-compose -f docker-compose.vps.yml restart web-ui
```

### Problem 3: Database Connection Error

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
```bash
# 1. Cek apakah postgres running
docker ps | grep postgres

# 2. Cek logs postgres
docker logs whac-postgres

# 3. Test koneksi dari web-ui container
docker exec whac-web-ui python3 -c "import psycopg2; conn = psycopg2.connect(host='postgres', database='whac_master', user='postgres', password='YOUR_PASSWORD'); print('Connected!')"

# 4. Restart postgres
docker-compose -f docker-compose.vps.yml restart postgres

# 5. Wait untuk postgres ready (bisa 10-30 detik)
docker logs whac-postgres | grep "ready to accept connections"
```

### Problem 4: Container Keeps Restarting

**Symptoms:** Container status shows "Restarting"

**Solution:**
```bash
# 1. Cek logs untuk error
docker logs whac-web-ui --tail 50

# 2. Cek resource usage
docker stats --no-stream

# 3. Cek health check
docker inspect whac-web-ui | grep -A 10 Health

# 4. Stop dan remove container
docker-compose -f docker-compose.vps.yml down

# 5. Start ulang
docker-compose -f docker-compose.vps.yml up -d

# 6. Monitor logs
docker-compose -f docker-compose.vps.yml logs -f
```

### Problem 5: Out of Disk Space

**Symptoms:**
```
no space left on device
```

**Solution:**
```bash
# 1. Cek disk usage
df -h

# 2. Cek Docker disk usage
docker system df

# 3. Clean Docker
docker system prune -a

# 4. Remove old logs
find ~/IoT-WHAC/V2 -name "*.log" -mtime +7 -delete

# 5. Remove old backups
find ~/backups -name "*.sql.gz" -mtime +30 -delete

# 6. Clean apt cache
sudo apt clean
```

### Problem 6: SSL/HTTPS Setup

Jika ingin menggunakan HTTPS dengan domain:

```bash
# Install Nginx
sudo apt install nginx

# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Setup SSL certificate
sudo certbot --nginx -d yourdomain.com

# Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/whac
```

Tambahkan konfigurasi:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:4545;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/whac /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## 📝 Quick Command Reference

### Start/Stop Services

```bash
# Start
docker-compose -f docker-compose.vps.yml --env-file vps.env up -d

# Stop
docker-compose -f docker-compose.vps.yml down

# Restart
docker-compose -f docker-compose.vps.yml restart

# Rebuild
docker-compose -f docker-compose.vps.yml up -d --build
```

### Logs

```bash
# All services
docker-compose -f docker-compose.vps.yml logs -f

# Specific service
docker logs whac-web-ui -f

# Last 100 lines
docker logs whac-web-ui --tail 100
```

### Database

```bash
# Backup
docker exec whac-postgres pg_dump -U postgres whac_master > backup.sql

# Restore
docker exec -i whac-postgres psql -U postgres whac_master < backup.sql

# Access psql
docker exec -it whac-postgres psql -U postgres -d whac_master
```

### Monitoring

```bash
# Container status
docker ps

# Resource usage
docker stats

# Disk usage
docker system df

# Logs
docker-compose -f docker-compose.vps.yml logs
```

---

## 🎉 Deployment Checklist

### Pre-Deployment
- [ ] VPS ready dengan Ubuntu/Debian
- [ ] Docker dan Docker Compose terinstall
- [ ] Firewall dikonfigurasi (port 4545, 5432, 1883)
- [ ] Repository di-clone dari Git
- [ ] File `vps.env` sudah dikonfigurasi
- [ ] Password database dan secret key sudah diganti

### Deployment
- [ ] Docker images berhasil di-build
- [ ] Services berjalan (docker ps)
- [ ] Database initialized
- [ ] Web UI bisa diakses dari browser
- [ ] Login berhasil dengan credentials

### Post-Deployment
- [ ] Password admin sudah diganti
- [ ] Backup database sudah disetup
- [ ] Cron job untuk auto backup aktif
- [ ] Monitoring tools terinstall (htop, dll)
- [ ] SSL/HTTPS disetup (opsional)
- [ ] Domain dikonfigurasi (opsional)

---

## 🔐 Security Checklist

- [ ] Ganti password database default
- [ ] Ganti secret key Flask
- [ ] Ganti password admin default
- [ ] Firewall aktif dan dikonfigurasi
- [ ] File .env tidak di-commit ke Git
- [ ] SSH menggunakan key-based authentication
- [ ] Regular security updates (apt update && apt upgrade)
- [ ] Database backup terenkripsi
- [ ] HTTPS/SSL aktif untuk production
- [ ] Disable root login SSH
- [ ] Change default SSH port (opsional)

---

## 📞 Support

Jika mengalami masalah:

1. Cek logs: `docker-compose -f docker-compose.vps.yml logs`
2. Cek status: `docker ps -a`
3. Cek resource: `docker stats`
4. Lihat troubleshooting section di atas

Dokumentasi terkait:
- `PANDUAN_DOCKER_INDONESIA.md`
- `README_DOCKER.md`
- `DOCKER_DEPLOYMENT_GUIDE.md`

---

**Selamat! Sistem WHAC Fingerprint Anda sudah berjalan di VPS! 🎉**

**URL Akses:** `http://YOUR-VPS-IP:4545`

