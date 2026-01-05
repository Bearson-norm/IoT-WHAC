# 🎯 VPS Deployment Cheatsheet - WHAC IoT

Quick reference untuk deployment dan management WHAC IoT di VPS.

## 🚀 Quick Deploy (One-Liner)

```bash
# Deployment otomatis
git clone YOUR_REPO && cd YOUR_REPO/V2 && chmod +x deploy-vps-external-mqtt.sh && ./deploy-vps-external-mqtt.sh
```

---

## 📦 Initial Setup

### Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Setup Environment

```bash
cp vps-external-mqtt.env.example .env
nano .env  # Edit passwords
chmod 600 .env
```

### Generate Passwords

```bash
openssl rand -base64 32  # DB Password
openssl rand -hex 64     # Secret Key
```

### Setup Firewall

```bash
sudo apt install -y ufw
sudo ufw allow 22/tcp && sudo ufw allow 4545/tcp
sudo ufw enable
```

---

## 🐳 Docker Commands

### Deploy

```bash
# Start all services
docker-compose -f docker-compose.vps-external-mqtt.yml up -d

# Build without cache
docker-compose -f docker-compose.vps-external-mqtt.yml build --no-cache

# Pull latest images
docker-compose -f docker-compose.vps-external-mqtt.yml pull
```

### Status & Logs

```bash
# Check status
docker ps
docker-compose -f docker-compose.vps-external-mqtt.yml ps

# View all logs (follow)
docker-compose -f docker-compose.vps-external-mqtt.yml logs -f

# View specific service
docker logs whac-web-ui -f
docker logs whac-postgres -f

# Last 100 lines
docker logs whac-web-ui --tail=100
```

### Control Services

```bash
# Stop
docker-compose -f docker-compose.vps-external-mqtt.yml stop

# Start
docker-compose -f docker-compose.vps-external-mqtt.yml start

# Restart
docker-compose -f docker-compose.vps-external-mqtt.yml restart

# Restart specific
docker-compose -f docker-compose.vps-external-mqtt.yml restart web-ui

# Stop and remove
docker-compose -f docker-compose.vps-external-mqtt.yml down

# Stop and remove including volumes (⚠️ DATA LOSS!)
docker-compose -f docker-compose.vps-external-mqtt.yml down -v
```

---

## 🔧 Database Commands

### Backup & Restore

```bash
# Backup
docker exec whac-postgres pg_dump -U postgres whac_master > backup_$(date +%Y%m%d_%H%M%S).sql
gzip backup_*.sql

# Restore
gunzip backup_20240101_120000.sql.gz
cat backup_20240101_120000.sql | docker exec -i whac-postgres psql -U postgres whac_master
```

### Database Access

```bash
# Connect to database
docker exec -it whac-postgres psql -U postgres -d whac_master

# Inside psql:
\dt                                    # List tables
\d+ users                              # Describe table
SELECT * FROM users;                   # Query
\q                                     # Exit
```

### Database Maintenance

```bash
# Check database size
docker exec whac-postgres psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('whac_master'));"

# Vacuum
docker exec whac-postgres psql -U postgres -d whac_master -c "VACUUM ANALYZE;"
```

---

## 🔍 Monitoring & Health

### Container Health

```bash
# Status summary
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Resource usage
docker stats --no-stream

# Real-time stats
docker stats

# Disk usage
docker system df
```

### Service Health

```bash
# Web UI health
curl -I http://localhost:4545

# Database health
docker exec whac-postgres pg_isready -U postgres

# Test database connection
docker exec whac-postgres psql -U postgres -c "SELECT 1;"
```

### MQTT Testing

```bash
# Install mosquitto clients
sudo apt install -y mosquitto-clients

# Subscribe to all topics
mosquitto_sub -h 103.87.67.139 -p 1883 -t "WHAC/#" -v

# Subscribe to specific topic
mosquitto_sub -h 103.87.67.139 -p 1883 -t "WHAC/Store001/in" -v

# Publish test message
mosquitto_pub -h 103.87.67.139 -p 1883 -t "WHAC/Store001/test" -m "Hello from VPS"

# Test connectivity
telnet 103.87.67.139 1883
```

---

## 🔄 Update & Maintenance

### Update from Git

```bash
# Full update procedure
docker-compose -f docker-compose.vps-external-mqtt.yml down
git pull origin main
docker-compose -f docker-compose.vps-external-mqtt.yml build --no-cache
docker-compose -f docker-compose.vps-external-mqtt.yml up -d
```

### Clean Docker

```bash
# Remove unused containers, images, networks
docker system prune -a

# Remove unused volumes
docker volume prune

# Clean everything (⚠️ CAREFUL!)
docker system prune -a --volumes
```

### View Disk Usage

```bash
df -h                    # System disk usage
docker system df         # Docker disk usage
du -sh /var/lib/docker   # Docker directory size
```

---

## 🚨 Troubleshooting

### Quick Diagnostics

```bash
# 1. Check if containers running
docker ps

# 2. Check logs for errors
docker logs whac-web-ui --tail=50 | grep -i error
docker logs whac-postgres --tail=50 | grep -i error

# 3. Check ports
sudo netstat -tlnp | grep -E '4545|5432'

# 4. Check firewall
sudo ufw status

# 5. Test locally
curl http://localhost:4545
```

### Fix Common Issues

```bash
# Web UI not accessible
docker restart whac-web-ui
docker logs whac-web-ui

# Database connection error
docker restart whac-postgres
docker exec whac-postgres pg_isready

# Out of memory
docker stats --no-stream
free -h

# Out of disk space
docker system prune -a
```

### Nuclear Option (Full Reset)

```bash
# ⚠️ WARNING: This will delete ALL data!
docker-compose -f docker-compose.vps-external-mqtt.yml down -v
docker system prune -a -f --volumes
docker-compose -f docker-compose.vps-external-mqtt.yml up -d
```

---

## 🔐 Security

### Firewall

```bash
# Check status
sudo ufw status verbose

# Allow port
sudo ufw allow 4545/tcp

# Deny port
sudo ufw deny 4545/tcp

# Delete rule
sudo ufw delete allow 4545/tcp

# Reset firewall
sudo ufw reset
```

### Check Exposed Ports

```bash
sudo netstat -tlnp
sudo ss -tulpn
```

### File Permissions

```bash
# Secure .env file
chmod 600 .env

# Check permissions
ls -la .env
```

---

## 📊 Useful One-Liners

### Status Check

```bash
# Quick status
docker ps && echo "---" && docker stats --no-stream

# Health check all
curl -I http://localhost:4545 && docker exec whac-postgres pg_isready

# Logs summary
docker logs whac-web-ui --tail=20 && echo "---" && docker logs whac-postgres --tail=20
```

### Auto Backup

```bash
# Daily backup script
echo "0 2 * * * docker exec whac-postgres pg_dump -U postgres whac_master | gzip > /backups/db_\$(date +\%Y\%m\%d).sql.gz" | crontab -
```

### Watch Logs

```bash
# Watch Web UI logs
watch -n 2 'docker logs whac-web-ui --tail=20'

# Follow multiple logs
docker logs whac-web-ui -f 2>&1 | grep -E 'ERROR|WARNING' &
docker logs whac-postgres -f 2>&1 | grep -E 'ERROR|FATAL' &
```

---

## 🌐 Network

### Check Connectivity

```bash
# Internet connectivity
ping -c 3 8.8.8.8

# MQTT broker
ping -c 3 103.87.67.139
telnet 103.87.67.139 1883

# DNS resolution
nslookup google.com
```

### Docker Network

```bash
# List networks
docker network ls

# Inspect network
docker network inspect whac-network

# Check container IP
docker inspect whac-web-ui | grep IPAddress
```

---

## 🎯 Access Information

### Web UI

```
URL: http://YOUR_VPS_IP:4545
Default User: admin
Default Pass: admin123
```

### Database

```bash
# From VPS
docker exec -it whac-postgres psql -U postgres -d whac_master

# From external (if port exposed)
psql -h YOUR_VPS_IP -U postgres -d whac_master
```

### MQTT Broker (External)

```
Host: 103.87.67.139
Port: 1883
Protocol: MQTT
```

---

## 📝 Environment Variables

### Critical Variables

```env
DB_PASSWORD=<change-this>
SECRET_KEY=<change-this>
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
WEB_PORT=4545
FLASK_ENV=production
```

### View Current Config

```bash
# Show environment variables (safe parts)
docker exec whac-web-ui env | grep -E 'MQTT|WEB_PORT|FLASK_ENV'

# Check .env file
cat .env | grep -v PASSWORD | grep -v SECRET_KEY
```

---

## 🆘 Emergency Commands

### Service Down

```bash
# Quick restart
docker-compose -f docker-compose.vps-external-mqtt.yml restart

# Force recreate
docker-compose -f docker-compose.vps-external-mqtt.yml up -d --force-recreate
```

### High CPU/Memory

```bash
# Check usage
docker stats --no-stream

# Restart specific service
docker restart whac-web-ui

# Restart all
docker-compose -f docker-compose.vps-external-mqtt.yml restart
```

### Cannot Connect to Database

```bash
# Restart database
docker restart whac-postgres

# Wait and check
sleep 10
docker exec whac-postgres pg_isready
```

### Logs Too Large

```bash
# Truncate logs
docker logs whac-web-ui > /dev/null 2>&1

# Configure log rotation (add to /etc/docker/daemon.json)
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Restart Docker
sudo systemctl restart docker
```

---

## 📚 Quick Links

| File | Purpose |
|------|---------|
| `QUICK_START_VPS_PORT_4545.md` | Quick start guide |
| `PANDUAN_DEPLOY_VPS_DOCKER.md` | Full documentation |
| `ARSITEKTUR_VPS_DEPLOYMENT.md` | Architecture details |
| `README_DEPLOYMENT_VPS.md` | Deployment overview |
| `docker-compose.vps-external-mqtt.yml` | Docker config |
| `vps-external-mqtt.env.example` | Environment template |
| `deploy-vps-external-mqtt.sh` | Auto-deploy script |

---

## 💡 Tips & Tricks

### Aliases for Convenience

```bash
# Add to ~/.bashrc or ~/.bash_aliases
alias dc='docker-compose -f docker-compose.vps-external-mqtt.yml'
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dlogs='docker-compose -f docker-compose.vps-external-mqtt.yml logs -f'
alias dstats='docker stats --no-stream'

# Usage after: source ~/.bashrc
dc up -d
dc logs -f
dps
```

### Watch Service Status

```bash
# Auto-refresh status every 2 seconds
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'
```

### Grep Logs for Errors

```bash
# Find errors in logs
docker logs whac-web-ui 2>&1 | grep -i error
docker logs whac-postgres 2>&1 | grep -i "error\|fatal"
```

---

**Quick Reference Card for WHAC IoT VPS Deployment**  
Keep this handy for daily operations! 📋

---

Last Updated: January 2025


