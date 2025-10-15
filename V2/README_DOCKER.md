# Docker Setup for WHAC Fingerprint System

This document provides a complete Docker setup for the WHAC Fingerprint System, allowing you to deploy each component individually on different devices.

## 🏗️ Architecture

```
┌─────────────────┐    MQTT     ┌─────────────────┐    Database    ┌─────────────────┐
│   Raspberry Pi  │ ──────────► │      VPS        │ ─────────────► │   PostgreSQL    │
│  (Local Machine)│             │  (Web UI +      │               │   Database      │
│                 │             │   Server)       │               │                 │
└─────────────────┘             └─────────────────┘               └─────────────────┘
```

## 📦 Components

### 1. Local Machine (Raspberry Pi)
- **Location**: Raspberry Pi with AS608 fingerprint sensor
- **Purpose**: Fingerprint scanning and MQTT communication
- **Files**: `local_machine/Dockerfile`, `local_machine/docker-compose.yml`

### 2. Web UI (VPS)
- **Location**: VPS server
- **Purpose**: Web dashboard and user interface
- **Files**: `web_ui/Dockerfile`, `web_ui/docker-compose.yml`

### 3. Server (VPS)
- **Location**: VPS server
- **Purpose**: MQTT data processing and database integration
- **Files**: `server/Dockerfile`, `server/docker-compose.yml`

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- AS608 fingerprint sensor (for Raspberry Pi)
- VPS with public IP (for web UI and server)

### 1. Deploy Local Machine (Raspberry Pi)

```bash
# Navigate to local machine directory
cd local_machine

# Copy environment template
cp env.example .env

# Edit configuration
nano .env

# Deploy
docker-compose up -d
```

### 2. Deploy Web UI (VPS)

```bash
# Navigate to web UI directory
cd web_ui

# Copy environment template
cp env.example .env

# Edit configuration
nano .env

# Deploy
docker-compose up -d
```

### 3. Deploy Server (VPS)

```bash
# Navigate to server directory
cd server

# Copy environment template
cp env.example .env

# Edit configuration
nano .env

# Deploy
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

Each component has its own `.env` file with the following variables:

#### Local Machine (.env)
```env
STORE_ID=Store001
MQTT_BROKER=your-vps-ip
MQTT_PORT=1883
FINGERPRINT_PORT=/dev/serial0
CONFIDENCE_THRESHOLD=50
```

#### Web UI (.env)
```env
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
MQTT_BROKER=103.87.67.139
```

#### Server (.env)
```env
MQTT_BROKER=103.87.67.139
DB_HOST=postgres
DB_NAME=whac_master
DB_USER=postgres
DB_PASSWORD=Admin123
```

## 📋 Quick Start Scripts

### Linux/macOS
```bash
# Make executable
chmod +x quick-start-docker.sh

# Deploy components
./quick-start-docker.sh local    # Raspberry Pi
./quick-start-docker.sh web      # VPS Web UI
./quick-start-docker.sh server   # VPS Server
```

### Windows
```cmd
# Deploy components
quick-start-docker.bat local     # Raspberry Pi
quick-start-docker.bat web       # VPS Web UI
quick-start-docker.bat server    # VPS Server
```

## 🔍 Monitoring

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

### Debug Commands
```bash
# Check container logs
docker logs <container_name>

# Enter container
docker exec -it <container_name> /bin/bash

# Check network connectivity
docker exec -it <container_name> ping <target_ip>
```

## 📚 Additional Documentation

- **Complete Guide**: `DOCKER_DEPLOYMENT_GUIDE.md`
- **Component READMEs**: 
  - `local_machine/README.md`
  - `web_ui/README.md`
  - `server/README.md`

## 🔒 Security Notes

1. **Change default passwords** in production
2. **Use environment variables** for sensitive data
3. **Enable MQTT authentication** if needed
4. **Use HTTPS** for web UI in production
5. **Regular security updates** for base images

## 🚀 Production Deployment

For production deployment, consider:
- Using Docker Swarm or Kubernetes
- Implementing proper secrets management
- Setting up monitoring and logging
- Configuring backup strategies
- Implementing security best practices

This Docker setup provides a complete, scalable solution for the WHAC Fingerprint System!

