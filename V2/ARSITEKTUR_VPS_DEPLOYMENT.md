# 🏗️ Arsitektur VPS Deployment - WHAC IoT System

Dokumentasi arsitektur deployment sistem WHAC Fingerprint di VPS dengan MQTT broker eksternal.

## 📐 Diagram Arsitektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INTERNET                                    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ Port 4545 (Web UI)
                                │ Port 5432 (PostgreSQL - optional)
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                         VPS SERVER                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Docker Network (whac-network)                    │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │         Web UI Container (whac-web-ui)                  │ │  │
│  │  │  - Flask Application                                    │ │  │
│  │  │  - SocketIO for real-time                              │ │  │
│  │  │  - Port: 5000 (internal) → 4545 (external)            │ │  │
│  │  │  - Connects to PostgreSQL                             │ │  │
│  │  │  - Connects to External MQTT Broker                   │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  │                            │ │ │                             │  │
│  │                            │ │ │                             │  │
│  │  ┌─────────────────────────▼─┘ │                             │  │
│  │  │   PostgreSQL Container     │                             │  │
│  │  │    (whac-postgres)         │                             │  │
│  │  │  - Database: whac_master   │                             │  │
│  │  │  - Port: 5432              │                             │  │
│  │  │  - Persistent Volume       │                             │  │
│  │  └─────────────────────────────┘                             │  │
│  │                                │                             │  │
│  │  ┌─────────────────────────────▼─────────────────────────┐  │  │
│  │  │   DB Init Container (whac-db-init)                    │  │  │
│  │  │  - Runs once on startup                               │  │  │
│  │  │  - Initializes database schema                        │  │  │
│  │  │  - Creates default admin user                         │  │  │
│  │  └───────────────────────────────────────────────────────┘  │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│                    ┌────────────────────┐                            │
│                    │  UFW Firewall      │                            │
│                    │  - Allow: 22 (SSH) │                            │
│                    │  - Allow: 4545     │                            │
│                    └────────────────────┘                            │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │ MQTT Connection
                               │ (Outbound to 103.87.67.139:1883)
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                  External MQTT Broker                                │
│                    103.87.67.139:1883                                │
│                                                                      │
│  Topics:                                                             │
│  - WHAC/Store001/in          (scan data from devices)               │
│  - WHAC/Store001/action      (commands to devices)                  │
│  - WHAC/Store001/voice_command                                      │
│  - WHAC/Store001/voice_response                                     │
│  - WHAC/Store001/audio                                              │
│  - WHAC/Store001/gpio_log                                           │
│  - WHAC/Store001/alarm                                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │ MQTT Connection
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│              Local Devices (Raspberry Pi / ESP32)                    │
│  - Fingerprint scanners                                              │
│  - Audio modules                                                     │
│  - GPIO controllers                                                  │
│  - Connects to MQTT broker                                           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Network Flow

### 1. User Access (Web UI)

```
User Browser → Internet → VPS:4545 → Docker:whac-web-ui:5000
                                           │
                                           ├─→ PostgreSQL (data)
                                           └─→ External MQTT (real-time updates)
```

### 2. Device Communication

```
Raspberry Pi → Internet → External MQTT Broker:1883
                                │
                                ├─→ Web UI (receives updates)
                                └─→ Other devices (commands)
```

### 3. Real-time Updates (WebSocket)

```
Device → MQTT Broker → Web UI Backend → SocketIO → User Browser
```

---

## 🐳 Docker Containers

### Container Details

| Container Name | Image | Port Mapping | Purpose |
|---------------|-------|--------------|---------|
| whac-web-ui | Custom (Python 3.9) | 4545:5000 | Web interface & API |
| whac-postgres | postgres:13-alpine | 5432:5432 | Database storage |
| whac-db-init | Custom (Python 3.9) | - | Database initialization |

### Resource Allocation

```yaml
whac-web-ui:
  Memory: 512MB - 1GB
  CPU: 0.5 - 1.0 cores

whac-postgres:
  Memory: 512MB - 1GB
  CPU: 0.5 - 1.0 cores
```

### Volumes (Persistent Data)

- `postgres_data`: Database files
- `./web_ui/logs`: Application logs
- `./web_ui/static`: Static assets
- `./web_ui/templates`: HTML templates

---

## 🔐 Security Layers

### 1. Network Security

```
┌─────────────────────────────────────┐
│     UFW Firewall (VPS Level)       │
│  - SSH (22): Restricted to admin IP │
│  - Web UI (4545): Public            │
│  - Database (5432): Blocked         │
└─────────────────────────────────────┘
```

### 2. Docker Network Isolation

```
Docker Bridge Network (172.25.0.0/16)
- Containers isolated from host
- Only exposed ports accessible
- Internal DNS resolution
```

### 3. Application Security

- Environment variables (secrets in .env)
- Flask SECRET_KEY for sessions
- bcrypt password hashing
- PostgreSQL authentication
- Non-root user in containers

### 4. MQTT Security (External)

- Controlled by external MQTT broker
- Topic-based access control
- Firewall rules on broker side

---

## 📦 Deployment Components

### Required Files on VPS

```
V2/
├── .env                                    # Environment configuration (CRITICAL)
├── docker-compose.vps-external-mqtt.yml    # Docker orchestration
├── web_ui/
│   ├── Dockerfile                         # Web UI image build
│   ├── Dockerfile.init                    # DB init image build
│   ├── app.py                             # Main application
│   ├── requirements.txt                   # Python dependencies
│   ├── database_setup.sql                 # Database schema
│   ├── templates/                         # HTML templates
│   └── static/                            # CSS, JS, images
└── deploy-vps-external-mqtt.sh            # Deployment automation
```

---

## 🔄 Data Flow

### Fingerprint Scan Flow

```
1. User places finger on scanner (Raspberry Pi)
2. Raspberry Pi publishes to MQTT: WHAC/Store001/in
3. MQTT Broker forwards to Web UI
4. Web UI receives via MQTT subscription
5. Web UI queries database for user info
6. Web UI emits to browser via SocketIO
7. Browser updates dashboard in real-time
8. Web UI logs to PostgreSQL
```

### Command Flow (Web UI → Device)

```
1. User clicks action on Web UI
2. Web UI publishes to MQTT: WHAC/Store001/action
3. MQTT Broker forwards to Raspberry Pi
4. Raspberry Pi executes command
5. Raspberry Pi publishes response
6. Web UI receives and updates dashboard
```

### Voice Command Flow

```
1. Voice detected on device
2. Device publishes to: WHAC/Store001/voice_command
3. Web UI processes command
4. Web UI publishes response to: WHAC/Store001/voice_response
5. Device plays audio response
```

---

## ⚙️ Environment Configuration

### Critical Environment Variables

```env
# Database Connection
DB_HOST=postgres               # Docker service name
DB_PORT=5432                   # Internal port
DB_NAME=whac_master           # Database name
DB_USER=postgres              # Database user
DB_PASSWORD=<strong-password>  # MUST be changed!

# MQTT Connection (External)
MQTT_BROKER=103.87.67.139     # External broker IP
MQTT_PORT=1883                # MQTT standard port

# Web UI
WEB_PORT=4545                 # External access port
SECRET_KEY=<random-string>    # Flask session key
FLASK_ENV=production          # Production mode
```

---

## 📊 Monitoring Points

### Health Checks

1. **Web UI Health**
   ```bash
   curl http://localhost:4545/api/dashboard_stats
   ```

2. **Database Health**
   ```bash
   docker exec whac-postgres pg_isready
   ```

3. **MQTT Connectivity**
   ```bash
   mosquitto_sub -h 103.87.67.139 -p 1883 -t "WHAC/#" -C 1
   ```

### Log Locations

```bash
# Docker logs
docker logs whac-web-ui
docker logs whac-postgres

# Application logs (if mounted)
./web_ui/logs/app.log

# System logs
journalctl -u docker
```

### Resource Monitoring

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Network connections
docker exec whac-web-ui netstat -an
```

---

## 🚀 Scaling Considerations

### Vertical Scaling (Current Setup)

- Increase VPS resources (RAM, CPU)
- Adjust Docker resource limits
- Optimize PostgreSQL settings

### Horizontal Scaling (Future)

- Load balancer in front of multiple Web UI instances
- PostgreSQL replication (master-slave)
- Redis for session management
- Multiple MQTT brokers (clustered)

---

## 🔄 High Availability Setup (Advanced)

```
┌──────────────────────────────────────────────────┐
│              Load Balancer (Nginx)               │
│                   Port 443 (HTTPS)               │
└────────────┬───────────────┬─────────────────────┘
             │               │
      ┌──────▼─────┐  ┌──────▼─────┐
      │  VPS 1     │  │  VPS 2     │
      │  Web UI    │  │  Web UI    │
      └──────┬─────┘  └──────┬─────┘
             │               │
             └───────┬───────┘
                     │
          ┌──────────▼──────────┐
          │  PostgreSQL Cluster │
          │  (Primary + Replica) │
          └─────────────────────┘
```

---

## 📈 Performance Optimization

### Database

- Enable connection pooling
- Index critical columns
- Regular VACUUM and ANALYZE
- Query optimization

### Application

- Enable Flask caching
- Optimize SocketIO connections
- Compress static assets
- Use CDN for static files

### Docker

- Multi-stage builds (smaller images)
- Layer caching optimization
- Resource limit tuning
- Log rotation

---

## 🔐 Backup Strategy

### What to Backup

1. **Database** (Critical)
   - Daily automated backups
   - Keep last 30 days
   - Store off-site

2. **Environment Files** (Critical)
   - .env file
   - docker-compose.yml
   - Encrypt before storing

3. **Application Logs** (Important)
   - Weekly rotation
   - Keep last 4 weeks

### Backup Script Example

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
docker exec whac-postgres pg_dump -U postgres whac_master | \
  gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Environment backup
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" .env docker-compose*.yml

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
```

---

## 📚 Related Documentation

- [PANDUAN_DEPLOY_VPS_DOCKER.md](PANDUAN_DEPLOY_VPS_DOCKER.md) - Full deployment guide
- [QUICK_START_VPS_PORT_4545.md](QUICK_START_VPS_PORT_4545.md) - Quick start guide
- [QUICK_START_VOICE_COMMANDS.md](QUICK_START_VOICE_COMMANDS.md) - Voice commands

---

## 🎯 Deployment Checklist

### Pre-deployment
- [ ] VPS provisioned (2GB+ RAM)
- [ ] Domain name configured (optional)
- [ ] SSL certificate ready (optional)
- [ ] MQTT broker accessible
- [ ] Git repository setup

### Deployment
- [ ] Docker installed
- [ ] Repository cloned
- [ ] .env configured
- [ ] Firewall configured
- [ ] Containers running
- [ ] Health checks passing

### Post-deployment
- [ ] Web UI accessible
- [ ] MQTT connection verified
- [ ] Database populated
- [ ] Default password changed
- [ ] Backup configured
- [ ] Monitoring setup
- [ ] Documentation updated

---

**Architecture Version:** 2.0  
**Last Updated:** January 2025  
**Deployment Target:** VPS with External MQTT Broker


