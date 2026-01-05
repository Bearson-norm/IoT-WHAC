# 📦 WHAC IoT System - VPS Deployment Guide

Dokumentasi lengkap untuk deployment sistem WHAC Fingerprint ke VPS menggunakan Docker.

## 🎯 Overview

Sistem WHAC Fingerprint adalah sistem IoT untuk manajemen fingerprint dengan Web UI, database PostgreSQL, dan integrasi MQTT untuk komunikasi real-time dengan perangkat IoT (Raspberry Pi, ESP32, dll).

### Komponen Sistem

- **Web UI**: Interface web untuk monitoring dan management (Flask + SocketIO)
- **Database**: PostgreSQL untuk penyimpanan data
- **MQTT**: Komunikasi real-time dengan perangkat IoT (menggunakan broker eksternal)
- **Docker**: Containerization untuk deployment yang mudah

---

## 📋 Dokumentasi Tersedia

| File | Deskripsi | Target Audience |
|------|-----------|-----------------|
| **[QUICK_START_VPS_PORT_4545.md](QUICK_START_VPS_PORT_4545.md)** | Panduan cepat deploy (5 menit) | User yang ingin deploy cepat |
| **[PANDUAN_DEPLOY_VPS_DOCKER.md](PANDUAN_DEPLOY_VPS_DOCKER.md)** | Panduan lengkap step-by-step | User yang ingin pemahaman detail |
| **[ARSITEKTUR_VPS_DEPLOYMENT.md](ARSITEKTUR_VPS_DEPLOYMENT.md)** | Arsitektur dan flow sistem | Developer / DevOps |
| **[docker-compose.vps-external-mqtt.yml](docker-compose.vps-external-mqtt.yml)** | Docker Compose configuration | DevOps / Advanced user |
| **[vps-external-mqtt.env.example](vps-external-mqtt.env.example)** | Environment template | All users |

---

## ⚡ Quick Start

### Opsi 1: Deployment Otomatis (Recommended)

```bash
# 1. Clone repository
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY/V2

# 2. Jalankan script deployment
chmod +x deploy-vps-external-mqtt.sh
./deploy-vps-external-mqtt.sh
```

Script akan otomatis:
- ✅ Install dependencies
- ✅ Generate secure passwords
- ✅ Setup environment
- ✅ Configure firewall
- ✅ Deploy containers

### Opsi 2: Manual Deployment

```bash
# 1. Setup environment
cp vps-external-mqtt.env.example .env
nano .env  # Edit konfigurasi

# 2. Deploy
docker-compose -f docker-compose.vps-external-mqtt.yml up -d

# 3. Check logs
docker-compose -f docker-compose.vps-external-mqtt.yml logs -f
```

---

## 🔧 Prerequisites

### VPS Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2GB | 4GB |
| Storage | 10GB | 20GB |
| CPU | 1 core | 2 cores |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 |

### Software Requirements

- Docker 20.10+
- Docker Compose 1.29+
- Git
- SSH access

### Network Requirements

- Port 4545 (Web UI) - **HARUS TERBUKA**
- Port 5432 (PostgreSQL) - optional, untuk akses eksternal
- Akses ke MQTT Broker: `103.87.67.139:1883`

---

## 🏗️ Arsitektur

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ Port 4545
       │
┌──────▼────────────────────────────────────┐
│             VPS Server                    │
│  ┌────────────────────────────────────┐   │
│  │  Docker Network                    │   │
│  │                                    │   │
│  │  ┌──────────────┐  ┌────────────┐ │   │
│  │  │   Web UI     │→ │ PostgreSQL │ │   │
│  │  │  (Port 5000) │  │ (Port 5432)│ │   │
│  │  └──────┬───────┘  └────────────┘ │   │
│  │         │                          │   │
│  └─────────┼──────────────────────────┘   │
└────────────┼──────────────────────────────┘
             │
             │ MQTT (Outbound)
             │
┌────────────▼──────────────┐
│   External MQTT Broker    │
│    103.87.67.139:1883     │
└────────────┬──────────────┘
             │
┌────────────▼──────────────┐
│   IoT Devices             │
│  (Raspberry Pi, ESP32)    │
└───────────────────────────┘
```

---

## 📦 Files Structure

```
V2/
├── 📄 docker-compose.vps-external-mqtt.yml   # Docker Compose config
├── 📄 vps-external-mqtt.env.example          # Environment template
├── 📄 .env                                   # Your config (create from template)
├── 📜 deploy-vps-external-mqtt.sh            # Auto deployment script
│
├── 📁 web_ui/                                # Web UI application
│   ├── Dockerfile                            # Web UI Docker image
│   ├── Dockerfile.init                       # DB init Docker image
│   ├── app.py                                # Main Flask app
│   ├── requirements.txt                      # Python dependencies
│   ├── database_setup.sql                    # Database schema
│   ├── templates/                            # HTML templates
│   └── static/                               # CSS, JS, images
│
├── 📁 server/                                # MQTT processor (optional)
│   ├── Dockerfile
│   └── ...
│
└── 📚 Documentation/
    ├── QUICK_START_VPS_PORT_4545.md          # Quick start guide
    ├── PANDUAN_DEPLOY_VPS_DOCKER.md          # Full deployment guide
    ├── ARSITEKTUR_VPS_DEPLOYMENT.md          # Architecture doc
    └── README_DEPLOYMENT_VPS.md              # This file
```

---

## 🚀 Deployment Steps

### Step 1: Persiapan VPS

```bash
# Login ke VPS
ssh root@YOUR_VPS_IP

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Clone Repository

```bash
cd ~
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY/V2
```

### Step 3: Konfigurasi Environment

```bash
# Copy template
cp vps-external-mqtt.env.example .env

# Generate passwords
DB_PASS=$(openssl rand -base64 32)
SECRET=$(openssl rand -hex 64)

# Edit .env dan paste passwords
nano .env

# Set secure permissions
chmod 600 .env
```

### Step 4: Setup Firewall

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH (PENTING!)
sudo ufw allow 22/tcp

# Allow Web UI
sudo ufw allow 4545/tcp

# Enable firewall
sudo ufw enable
```

### Step 5: Deploy Containers

```bash
# Build and start
docker-compose -f docker-compose.vps-external-mqtt.yml up -d

# Check status
docker-compose -f docker-compose.vps-external-mqtt.yml ps

# View logs
docker-compose -f docker-compose.vps-external-mqtt.yml logs -f
```

### Step 6: Verifikasi

```bash
# Test from VPS
curl http://localhost:4545

# Test from browser
http://YOUR_VPS_IP:4545
```

**Default Login:**
- Username: `admin`
- Password: `admin123`

⚠️ **PENTING**: Ganti password default setelah login pertama kali!

---

## 🔐 Konfigurasi Penting

### Environment Variables (File .env)

```env
# Database - GANTI PASSWORD INI!
DB_PASSWORD=YourStrongPasswordHere123!

# MQTT - Broker eksternal yang sudah ada
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883

# Web UI - Port eksternal
WEB_PORT=4545

# Security - GANTI SECRET KEY INI!
SECRET_KEY=YourVeryLongRandomSecretKeyHere!
FLASK_ENV=production
```

### Generate Secure Values

```bash
# Database password
openssl rand -base64 32

# Flask secret key
openssl rand -hex 64
```

---

## 🛠️ Management Commands

### Status & Monitoring

```bash
# Check container status
docker ps

# View logs (all services)
docker-compose -f docker-compose.vps-external-mqtt.yml logs -f

# View specific service logs
docker logs whac-web-ui -f
docker logs whac-postgres -f

# Resource usage
docker stats
```

### Start/Stop/Restart

```bash
# Stop services
docker-compose -f docker-compose.vps-external-mqtt.yml stop

# Start services
docker-compose -f docker-compose.vps-external-mqtt.yml start

# Restart services
docker-compose -f docker-compose.vps-external-mqtt.yml restart

# Stop and remove containers
docker-compose -f docker-compose.vps-external-mqtt.yml down
```

### Update & Maintenance

```bash
# Pull latest code from Git
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.vps-external-mqtt.yml down
docker-compose -f docker-compose.vps-external-mqtt.yml build --no-cache
docker-compose -f docker-compose.vps-external-mqtt.yml up -d
```

### Backup Database

```bash
# Create backup
docker exec whac-postgres pg_dump -U postgres whac_master > backup_$(date +%Y%m%d).sql

# Compress backup
gzip backup_*.sql

# Restore from backup
gunzip backup_20240101.sql.gz
cat backup_20240101.sql | docker exec -i whac-postgres psql -U postgres whac_master
```

---

## 🚨 Troubleshooting

### Web UI tidak bisa diakses

```bash
# 1. Check container
docker ps | grep whac-web-ui

# 2. Check logs
docker logs whac-web-ui --tail=100

# 3. Check port
sudo netstat -tlnp | grep 4545

# 4. Check firewall
sudo ufw status

# 5. Test locally
curl http://localhost:4545
```

### Database connection error

```bash
# Check PostgreSQL
docker logs whac-postgres

# Test connection
docker exec -it whac-postgres psql -U postgres -d whac_master -c "SELECT 1;"

# Check if healthy
docker exec whac-postgres pg_isready -U postgres
```

### MQTT connection error

```bash
# Check Web UI logs
docker logs whac-web-ui | grep -i mqtt

# Test MQTT from VPS
sudo apt install -y mosquitto-clients
mosquitto_sub -h 103.87.67.139 -p 1883 -t "WHAC/#" -v

# Test connectivity
ping 103.87.67.139
telnet 103.87.67.139 1883
```

### Container tidak start

```bash
# Check all logs
docker-compose -f docker-compose.vps-external-mqtt.yml logs

# Rebuild from scratch
docker-compose -f docker-compose.vps-external-mqtt.yml down -v
docker system prune -a
docker-compose -f docker-compose.vps-external-mqtt.yml build --no-cache
docker-compose -f docker-compose.vps-external-mqtt.yml up -d
```

### Out of disk space

```bash
# Clean Docker
docker system prune -a -f
docker volume prune -f

# Check disk usage
df -h
docker system df
```

---

## 📊 Monitoring & Health Check

### Health Check Commands

```bash
# 1. Web UI health
curl -I http://localhost:4545

# 2. Database health
docker exec whac-postgres pg_isready -U postgres

# 3. MQTT connectivity
mosquitto_pub -h 103.87.67.139 -p 1883 -t "test" -m "hello"

# 4. Container health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Performance Monitoring

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Network connections
docker exec whac-web-ui netstat -an | grep ESTABLISHED
```

---

## 🔄 Update Procedure

### Update dari Git

```bash
# 1. Backup database
docker exec whac-postgres pg_dump -U postgres whac_master > backup_before_update.sql

# 2. Stop services
docker-compose -f docker-compose.vps-external-mqtt.yml stop

# 3. Pull latest code
git pull origin main

# 4. Rebuild
docker-compose -f docker-compose.vps-external-mqtt.yml build

# 5. Start services
docker-compose -f docker-compose.vps-external-mqtt.yml up -d

# 6. Check logs
docker-compose -f docker-compose.vps-external-mqtt.yml logs -f
```

---

## 🔐 Security Best Practices

### ✅ Checklist Keamanan

- [ ] Password DB_PASSWORD sudah diganti
- [ ] SECRET_KEY sudah diganti
- [ ] File .env permission: 600
- [ ] File .env tidak di-commit ke Git
- [ ] Firewall (UFW) sudah aktif
- [ ] Port 22 (SSH) restricted to admin IP
- [ ] Default admin password sudah diganti
- [ ] Regular database backup
- [ ] SSL/HTTPS configured (recommended)
- [ ] Docker containers running as non-root
- [ ] Regular security updates

### Security Enhancements (Optional)

```bash
# 1. Install fail2ban (protect SSH)
sudo apt install -y fail2ban

# 2. Restrict SSH to specific IP
sudo ufw allow from YOUR_IP_ADDRESS to any port 22

# 3. Setup SSL with Certbot
sudo apt install -y certbot nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📈 Performance Tuning

### PostgreSQL Optimization

```sql
-- Connect to database
docker exec -it whac-postgres psql -U postgres -d whac_master

-- Check database size
SELECT pg_size_pretty(pg_database_size('whac_master'));

-- Vacuum and analyze
VACUUM ANALYZE;

-- Create indexes (if needed)
CREATE INDEX idx_attendance_date ON attendance(date);
```

### Docker Optimization

```yaml
# Increase resource limits if needed
# Edit docker-compose.vps-external-mqtt.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
```

---

## 📞 Support & Documentation

### Dokumentasi Lengkap

1. **[QUICK_START_VPS_PORT_4545.md](QUICK_START_VPS_PORT_4545.md)**  
   Panduan cepat untuk deployment

2. **[PANDUAN_DEPLOY_VPS_DOCKER.md](PANDUAN_DEPLOY_VPS_DOCKER.md)**  
   Panduan lengkap step-by-step dengan penjelasan detail

3. **[ARSITEKTUR_VPS_DEPLOYMENT.md](ARSITEKTUR_VPS_DEPLOYMENT.md)**  
   Dokumentasi arsitektur sistem dan flow data

### Getting Help

1. Check logs first: `docker-compose -f docker-compose.vps-external-mqtt.yml logs -f`
2. Review troubleshooting section
3. Check documentation files
4. Verify network connectivity

---

## 🎯 Project Info

- **System**: WHAC IoT Fingerprint System
- **Version**: 2.0
- **Deployment Type**: VPS with External MQTT Broker
- **Web UI Port**: 4545
- **MQTT Broker**: 103.87.67.139:1883

---

## 📝 Notes

### Penting untuk Diingat

- File `.env` berisi informasi sensitif, **JANGAN** commit ke Git
- Ganti password default admin segera setelah deployment
- Backup database secara regular
- Monitor resource usage (RAM, CPU, disk)
- Update sistem secara berkala
- Review logs untuk detect issues

### Development vs Production

| Aspect | Development | Production (VPS) |
|--------|-------------|------------------|
| FLASK_ENV | development | production |
| Debug Mode | Enabled | Disabled |
| SECRET_KEY | Simple | Random 64+ chars |
| DB_PASSWORD | Simple | Strong password |
| Firewall | Optional | Required |
| SSL/HTTPS | Optional | Recommended |
| Backup | Optional | Required |

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] VPS ready (specs checked)
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Git installed
- [ ] Repository cloned
- [ ] MQTT broker accessible

### Deployment
- [ ] .env file created and configured
- [ ] Secure passwords generated
- [ ] Firewall configured
- [ ] Containers built
- [ ] Containers started
- [ ] Logs checked

### Post-Deployment
- [ ] Web UI accessible from browser
- [ ] Login successful
- [ ] Default password changed
- [ ] MQTT connection verified
- [ ] Database working
- [ ] Backup configured
- [ ] Monitoring setup

---

## 🎉 Success Indicators

Deployment berhasil jika:

✅ All containers running: `docker ps` shows healthy containers  
✅ Web UI accessible: `http://YOUR_VPS_IP:4545`  
✅ Login successful: Can login with admin credentials  
✅ MQTT connected: Real-time updates working  
✅ Database working: Can view data and create records  
✅ No errors in logs: `docker logs whac-web-ui` clean  

---

**Happy Deploying! 🚀**

Untuk pertanyaan atau issue, review dokumentasi lengkap atau check logs untuk troubleshooting.

---

**Last Updated**: January 2025  
**Maintainer**: WHAC IoT Team  
**License**: Sesuai dengan license repository


