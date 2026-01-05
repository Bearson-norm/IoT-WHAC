# 🚀 Quick Start: Deploy ke VPS Port 4545

Panduan singkat deploy WHAC IoT System ke VPS menggunakan Docker dengan MQTT broker eksternal.

## ⚡ Quick Deploy (5 Menit)

### 1. Login ke VPS

```bash
ssh root@YOUR_VPS_IP
```

### 2. Clone Repository

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/V2
```

### 3. Install Docker (Jika belum ada)

```bash
# Quick install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Enable Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### 4. Setup dan Deploy (OTOMATIS)

```bash
# Jalankan script deployment otomatis
chmod +x deploy-vps-external-mqtt.sh
./deploy-vps-external-mqtt.sh
```

Script akan otomatis:
- ✅ Check requirements
- ✅ Generate secure passwords
- ✅ Setup environment file
- ✅ Test MQTT connectivity
- ✅ Configure firewall
- ✅ Build dan start containers

### 5. Akses Web UI

```
URL: http://YOUR_VPS_IP:4545
Username: admin
Password: admin123
```

**SELESAI!** 🎉

---

## 📋 Manual Deployment (Jika ingin kontrol penuh)

### Step 1: Setup Environment

```bash
# Copy template
cp vps-external-mqtt.env.example .env

# Generate passwords
openssl rand -base64 32  # untuk DB_PASSWORD
openssl rand -hex 64     # untuk SECRET_KEY

# Edit .env file
nano .env

# Update:
# - DB_PASSWORD=paste_password_di_sini
# - SECRET_KEY=paste_secret_key_di_sini

# Set permissions
chmod 600 .env
```

### Step 2: Setup Firewall

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH (PENTING!)
sudo ufw allow 22/tcp

# Allow Web UI
sudo ufw allow 4545/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 3: Test MQTT Connectivity

```bash
# Install mosquitto client
sudo apt install -y mosquitto-clients

# Test connection
mosquitto_sub -h 103.87.67.139 -p 1883 -t "test" -v -C 1

# Jika sukses, Ctrl+C untuk keluar
```

### Step 4: Deploy Docker Containers

```bash
# Build images
docker-compose -f docker-compose.vps-external-mqtt.yml build

# Start services
docker-compose -f docker-compose.vps-external-mqtt.yml up -d

# Check status
docker-compose -f docker-compose.vps-external-mqtt.yml ps

# View logs
docker-compose -f docker-compose.vps-external-mqtt.yml logs -f
```

---

## 🔧 Management Commands

### Check Status

```bash
docker ps
docker-compose -f docker-compose.vps-external-mqtt.yml ps
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.vps-external-mqtt.yml logs -f

# Specific service
docker logs whac-web-ui -f
docker logs whac-postgres -f
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.vps-external-mqtt.yml restart

# Restart specific service
docker-compose -f docker-compose.vps-external-mqtt.yml restart web-ui
```

### Stop Services

```bash
docker-compose -f docker-compose.vps-external-mqtt.yml stop
```

### Start Services

```bash
docker-compose -f docker-compose.vps-external-mqtt.yml start
```

### Update dari Git

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.vps-external-mqtt.yml down
docker-compose -f docker-compose.vps-external-mqtt.yml build --no-cache
docker-compose -f docker-compose.vps-external-mqtt.yml up -d
```

---

## 🚨 Troubleshooting

### Web UI tidak bisa diakses

```bash
# 1. Check container status
docker ps

# 2. Check logs
docker logs whac-web-ui --tail=100

# 3. Check if port is listening
sudo netstat -tlnp | grep 4545

# 4. Check firewall
sudo ufw status

# 5. Test locally from VPS
curl http://localhost:4545
```

### Database connection error

```bash
# Check PostgreSQL container
docker logs whac-postgres --tail=50

# Test database connection
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT 1;"
```

### MQTT connection error

```bash
# Check Web UI logs for MQTT errors
docker logs whac-web-ui | grep -i mqtt

# Test MQTT from VPS
mosquitto_sub -h 103.87.67.139 -p 1883 -t "WHAC/Store001/#" -v

# Check connectivity
ping 103.87.67.139
telnet 103.87.67.139 1883
```

### Container tidak start

```bash
# Check detailed logs
docker-compose -f docker-compose.vps-external-mqtt.yml logs

# Rebuild from scratch
docker-compose -f docker-compose.vps-external-mqtt.yml down -v
docker-compose -f docker-compose.vps-external-mqtt.yml build --no-cache
docker-compose -f docker-compose.vps-external-mqtt.yml up -d
```

---

## 📊 Health Check

### Check all services

```bash
# Container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Resource usage
docker stats --no-stream

# Disk usage
docker system df
```

### Test Web UI

```bash
# From VPS
curl -I http://localhost:4545

# From outside
curl -I http://YOUR_VPS_IP:4545
```

### Test Database

```bash
# Connect to database
docker exec -it whac-postgres psql -U postgres -d whac_master

# Check tables
\dt

# Check users
SELECT username, role FROM users;

# Exit
\q
```

---

## 🔐 Security Checklist

- [ ] Changed DB_PASSWORD di .env
- [ ] Changed SECRET_KEY di .env
- [ ] Set permission .env (chmod 600)
- [ ] Firewall enabled dan configured
- [ ] Port 4545 hanya terbuka untuk IP yang diperlukan
- [ ] Default admin password sudah diganti
- [ ] SSL/HTTPS configured (optional, lihat panduan lengkap)
- [ ] Regular backup database

---

## 📚 File Structure

```
V2/
├── docker-compose.vps-external-mqtt.yml  # Docker Compose config
├── vps-external-mqtt.env.example         # Environment template
├── .env                                  # Your environment (don't commit!)
├── deploy-vps-external-mqtt.sh           # Deployment script
├── PANDUAN_DEPLOY_VPS_DOCKER.md          # Full documentation
└── QUICK_START_VPS_PORT_4545.md          # This file
```

---

## 🎯 Environment Variables

File `.env` yang penting:

```env
# Database
DB_PASSWORD=your_strong_password_here

# MQTT (External Broker)
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883

# Web UI
WEB_PORT=4545
SECRET_KEY=your_secret_key_here
FLASK_ENV=production
```

---

## 🔄 Backup & Restore

### Backup Database

```bash
# Create backup
docker exec whac-postgres pg_dump -U postgres whac_master > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_*.sql
```

### Restore Database

```bash
# Stop web-ui first
docker-compose -f docker-compose.vps-external-mqtt.yml stop web-ui

# Restore
gunzip backup_20240101_120000.sql.gz
cat backup_20240101_120000.sql | docker exec -i whac-postgres psql -U postgres whac_master

# Restart web-ui
docker-compose -f docker-compose.vps-external-mqtt.yml start web-ui
```

---

## 📞 Getting Help

1. **Check logs first:** `docker-compose -f docker-compose.vps-external-mqtt.yml logs -f`
2. **Check container status:** `docker ps -a`
3. **Review full documentation:** `PANDUAN_DEPLOY_VPS_DOCKER.md`
4. **Test connectivity:** Check network, firewall, dan MQTT broker

---

## ⚡ One-Liner Commands

```bash
# Deploy everything
git clone YOUR_REPO && cd YOUR_REPO/V2 && chmod +x deploy-vps-external-mqtt.sh && ./deploy-vps-external-mqtt.sh

# Quick restart
docker-compose -f docker-compose.vps-external-mqtt.yml restart

# Quick logs
docker-compose -f docker-compose.vps-external-mqtt.yml logs -f --tail=100

# Quick status
docker-compose -f docker-compose.vps-external-mqtt.yml ps && docker stats --no-stream

# Full rebuild
docker-compose -f docker-compose.vps-external-mqtt.yml down && docker-compose -f docker-compose.vps-external-mqtt.yml build --no-cache && docker-compose -f docker-compose.vps-external-mqtt.yml up -d
```

---

**Happy Deploying! 🚀**

Untuk panduan lengkap dengan penjelasan detail, lihat: `PANDUAN_DEPLOY_VPS_DOCKER.md`


