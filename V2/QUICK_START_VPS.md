# 🚀 Quick Start: Deploy ke VPS (Port 4545)

Panduan cepat untuk deploy sistem WHAC Fingerprint ke VPS menggunakan Docker.

## ⚡ 3 Langkah Cepat

### 1️⃣ Setup Docker di VPS (5 menit)

```bash
# Login ke VPS
ssh user@your-vps-ip

# Clone repository
git clone https://github.com/your-username/IoT-WHAC.git
cd IoT-WHAC/V2

# Jalankan script setup Docker
chmod +x setup-docker-vps.sh
sudo ./setup-docker-vps.sh
```

**Script akan:**
- ✓ Install Docker & Docker Compose
- ✓ Configure firewall (port 4545, 5432, 1883)
- ✓ Setup auto-start Docker service
- ✓ Test Docker installation

---

### 2️⃣ Konfigurasi Environment (2 menit)

```bash
# Copy template environment
cp vps-env.example vps.env

# Generate password yang kuat
openssl rand -base64 32  # Untuk DB_PASSWORD
openssl rand -hex 64     # Untuk SECRET_KEY

# Edit file environment
nano vps.env
```

**Yang harus diganti:**
```env
DB_PASSWORD=PastePasswordDariGenerate
SECRET_KEY=PasteSecretKeyDariGenerate
```

**Set permission:**
```bash
chmod 600 vps.env
```

---

### 3️⃣ Deploy! (10 menit)

```bash
# Jalankan script deployment
chmod +x deploy-vps.sh
./deploy-vps.sh
```

**Script akan:**
- ✓ Check prerequisites
- ✓ Security check (password)
- ✓ Build Docker images
- ✓ Start all services
- ✓ Display access information

---

## 🎯 Akses Web UI

Setelah deployment selesai:

```
URL: http://YOUR-VPS-IP:4545
Username: admin
Password: admin123
```

**⚠️ PENTING:** Ganti password admin setelah login pertama!

---

## 📊 Monitoring

### Cek Status
```bash
docker ps
```

### Lihat Logs
```bash
# Semua services
docker-compose -f docker-compose.vps.yml logs -f

# Web UI saja
docker logs whac-web-ui -f

# Database
docker logs whac-postgres -f
```

### Resource Usage
```bash
docker stats
```

---

## 🔧 Management

### Restart Services
```bash
docker-compose -f docker-compose.vps.yml restart
```

### Stop Services
```bash
docker-compose -f docker-compose.vps.yml down
```

### Update Application
```bash
# Pull update dari Git
git pull

# Rebuild dan restart
docker-compose -f docker-compose.vps.yml up -d --build
```

---

## 💾 Backup Database

### Manual Backup
```bash
docker exec whac-postgres pg_dump -U postgres whac_master > backup_$(date +%Y%m%d).sql
```

### Auto Backup (Cron)
```bash
# Edit crontab
crontab -e

# Tambahkan line ini (backup setiap hari jam 2 pagi)
0 2 * * * docker exec whac-postgres pg_dump -U postgres whac_master > ~/backups/backup_$(date +\%Y\%m\%d).sql
```

---

## 🆘 Troubleshooting

### Web UI tidak bisa diakses

```bash
# 1. Cek container running
docker ps | grep whac-web-ui

# 2. Cek logs
docker logs whac-web-ui

# 3. Cek firewall
sudo ufw status
sudo ufw allow 4545/tcp

# 4. Restart container
docker-compose -f docker-compose.vps.yml restart web-ui
```

### Database connection error

```bash
# 1. Cek postgres running
docker ps | grep postgres

# 2. Cek logs
docker logs whac-postgres

# 3. Test connection
docker exec whac-web-ui python3 -c "import psycopg2; conn = psycopg2.connect(host='postgres', database='whac_master', user='postgres', password='YOUR_PASSWORD'); print('Connected!')"
```

### Container keeps restarting

```bash
# Lihat logs untuk error
docker logs whac-web-ui --tail 50

# Stop dan rebuild
docker-compose -f docker-compose.vps.yml down
docker-compose -f docker-compose.vps.yml up -d --build
```

---

## 📚 Dokumentasi Lengkap

Untuk panduan lengkap, lihat:
- **VPS_DEPLOYMENT_GUIDE.md** - Panduan deployment detail
- **PANDUAN_DOCKER_INDONESIA.md** - Panduan Docker lengkap

---

## 🔐 Security Checklist

- [ ] Password database sudah diganti
- [ ] Secret key Flask sudah diganti
- [ ] Password admin sudah diganti
- [ ] Firewall aktif dan dikonfigurasi
- [ ] File vps.env tidak di-commit ke Git
- [ ] SSH menggunakan key-based auth
- [ ] Auto backup database aktif

---

## 📞 Commands Cheat Sheet

| Action | Command |
|--------|---------|
| **Start** | `docker-compose -f docker-compose.vps.yml up -d` |
| **Stop** | `docker-compose -f docker-compose.vps.yml down` |
| **Restart** | `docker-compose -f docker-compose.vps.yml restart` |
| **Logs** | `docker-compose -f docker-compose.vps.yml logs -f` |
| **Status** | `docker ps` |
| **Stats** | `docker stats` |
| **Backup DB** | `docker exec whac-postgres pg_dump -U postgres whac_master > backup.sql` |
| **Update** | `git pull && docker-compose -f docker-compose.vps.yml up -d --build` |

---

**Selamat! Sistem WHAC Fingerprint sudah berjalan di VPS! 🎉**

