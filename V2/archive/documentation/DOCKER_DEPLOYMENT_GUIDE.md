# Docker Deployment Guide - WHAC Fingerprint System

This guide explains how to deploy the WHAC Fingerprint System using Docker containers across different devices.

## 🏗️ Architecture Overview

```
┌─────────────────┐    MQTT     ┌─────────────────┐    Database    ┌─────────────────┐
│   Raspberry Pi  │ ──────────► │      VPS        │ ─────────────► │   PostgreSQL    │
│  (Local Machine)│             │  (Web UI +      │               │   Database      │
│                 │             │   Server)       │               │                 │
└─────────────────┘             └─────────────────┘               └─────────────────┘
```

## 📦 Components

1. **Local Machine** (Raspberry Pi) - Fingerprint scanner
2. **Web UI** (VPS) - Web dashboard
3. **Server** (VPS) - MQTT data processor
4. **PostgreSQL** (VPS) - Database
5. **MQTT Broker** (VPS) - Message broker

## 🚀 Deployment Instructions

### 1. Raspberry Pi (Local Machine)

#### Prerequisites
- Raspberry Pi OS
- Docker and Docker Compose installed
- AS608 fingerprint sensor connected

#### Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd IoT-WHAC/V2/local_machine

# Copy environment file
cp env.example .env

# Edit configuration
nano .env

# Build and run
docker-compose up -d
```

#### Configuration
Edit `.env` file:
```env
STORE_ID=Store001
MQTT_BROKER=your-vps-ip
MQTT_PORT=1883
FINGERPRINT_PORT=/dev/serial0
CONFIDENCE_THRESHOLD=50
```

### 2. VPS (Web UI + Server)

#### Prerequisites
- Ubuntu/Debian server
- Docker and Docker Compose installed
- Open ports: 5000 (Web UI), 1883 (MQTT), 5432 (PostgreSQL)

#### Setup Web UI
```bash
# Navigate to web_ui directory
cd web_ui

# Copy environment file
cp env.example .env

# Edit configuration
nano .env

# Build and run
docker-compose up -d
```

#### Setup Server
```bash
# Navigate to server directory
cd server

# Copy environment file
cp env.example .env

# Edit configuration
nano .env

# Build and run
docker-compose up -d
```

#### Configuration
Edit `.env` files for both web_ui and server:
```env
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
MQTT_BROKER=103.87.67.139
```

## 🔧 Individual Component Deployment

### Local Machine Only (Raspberry Pi)
```bash
cd local_machine
docker-compose up -d
```

### Web UI Only (VPS)
```bash
cd web_ui
docker-compose up -d
```

### Server Only (VPS)
```bash
cd server
docker-compose up -d
```

## 📋 Environment Variables

### Local Machine (.env)
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

### Web UI (.env)
```env
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
DB_PORT=5432
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
FLASK_ENV=production
SECRET_KEY=whac_fingerprint_secret_key
```

### Server (.env)
```env
MQTT_BROKER=103.87.67.139
MQTT_PORT=1883
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
DB_PORT=5432
```

## 🔍 Monitoring and Logs

### View Logs
```bash
# Local Machine
docker-compose -f local_machine/docker-compose.yml logs -f

# Web UI
docker-compose -f web_ui/docker-compose.yml logs -f

# Server
docker-compose -f server/docker-compose.yml logs -f
```

### Health Checks
```bash
# Check container status
docker ps

# Check health status
docker inspect <container_name> | grep Health
```

## 🛠️ Troubleshooting

### Common Issues

1. **Serial Port Access Denied**
   - Ensure user is in `dialout` group
   - Check device permissions: `ls -la /dev/tty*`

2. **MQTT Connection Failed**
   - Verify MQTT broker is running
   - Check firewall settings
   - Verify IP addresses and ports

3. **Database Connection Failed**
   - Ensure PostgreSQL is running
   - Check database credentials
   - Verify network connectivity

4. **GPIO Access Denied**
   - Run with `privileged: true`
   - Use `network_mode: host`

### Debug Commands
```bash
# Check container logs
docker logs <container_name>

# Enter container
docker exec -it <container_name> /bin/bash

# Check network connectivity
docker exec -it <container_name> ping <target_ip>

# Check MQTT connection
docker exec -it <container_name> mosquitto_pub -h <broker_ip> -t test -m "test"
```

## 🔒 Security Considerations

1. **Change default passwords** in production
2. **Use environment variables** for sensitive data
3. **Enable MQTT authentication** if needed
4. **Use HTTPS** for web UI in production
5. **Regular security updates** for base images

## 📊 Performance Optimization

1. **Resource limits** for containers
2. **Volume optimization** for database
3. **Network optimization** for MQTT
4. **Log rotation** configuration

## 🚀 Production Deployment

### Using Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml whac-system
```

### Using Kubernetes
- Create Kubernetes manifests
- Use ConfigMaps for configuration
- Use Secrets for sensitive data
- Use PersistentVolumes for data

## 📝 Maintenance

### Updates
```bash
# Pull latest images
docker-compose pull

# Rebuild containers
docker-compose up -d --build

# Clean up old images
docker image prune
```

### Backups
```bash
# Backup database
docker exec postgres pg_dump -U postgres whac_master > backup.sql

# Backup volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

This deployment guide provides everything needed to run the WHAC Fingerprint System using Docker containers across different devices!

