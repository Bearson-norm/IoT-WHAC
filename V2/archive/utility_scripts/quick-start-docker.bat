@echo off
REM Quick Start Script for WHAC Fingerprint System Docker Deployment
REM This script helps you deploy the system components individually

echo 🚀 WHAC Fingerprint System - Docker Quick Start
echo ==============================================

if "%1"=="local" goto deploy_local
if "%1"=="web" goto deploy_web
if "%1"=="server" goto deploy_server
if "%1"=="all" goto deploy_all
goto usage

:usage
echo Usage: %0 [local^|web^|server^|all]
echo.
echo Options:
echo   local   - Deploy local machine (Raspberry Pi)
echo   web     - Deploy web UI (VPS)
echo   server  - Deploy server (VPS)
echo   all     - Deploy all components (reference only)
echo.
echo Examples:
echo   %0 local    # Deploy on Raspberry Pi
echo   %0 web      # Deploy web UI on VPS
echo   %0 server   # Deploy server on VPS
goto end

:deploy_local
echo 📱 Deploying Local Machine (Raspberry Pi)...
cd local_machine

REM Check if .env exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ⚠️  Please edit .env file with your configuration before running again
    echo    notepad .env
    exit /b 1
)

echo 🔨 Building Docker image...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

echo ✅ Local machine deployed successfully!
echo 📊 View logs: docker-compose logs -f
echo 🛑 Stop services: docker-compose down
goto end

:deploy_web
echo 🌐 Deploying Web UI (VPS)...
cd web_ui

REM Check if .env exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ⚠️  Please edit .env file with your configuration before running again
    echo    notepad .env
    exit /b 1
)

echo 🔨 Building Docker image...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

echo ✅ Web UI deployed successfully!
echo 🌐 Access at: http://localhost:5000
echo 📊 View logs: docker-compose logs -f
echo 🛑 Stop services: docker-compose down
goto end

:deploy_server
echo 🖥️  Deploying Server (VPS)...
cd server

REM Check if .env exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ⚠️  Please edit .env file with your configuration before running again
    echo    notepad .env
    exit /b 1
)

echo 🔨 Building Docker image...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

echo ✅ Server deployed successfully!
echo 📊 View logs: docker-compose logs -f
echo 🛑 Stop services: docker-compose down
goto end

:deploy_all
echo 📋 Complete System Deployment Guide
echo ==================================
echo.
echo 1. 🍓 Raspberry Pi (Local Machine):
echo    cd local_machine ^&^& .\quick-start-docker.bat local
echo.
echo 2. 🌐 VPS (Web UI + Server):
echo    cd web_ui ^&^& .\quick-start-docker.bat web
echo    cd server ^&^& .\quick-start-docker.bat server
echo.
echo 3. 📚 Configuration:
echo    - Edit .env files in each component directory
echo    - Update MQTT broker IP addresses
echo    - Configure database credentials
echo.
echo 4. 📖 Full documentation: DOCKER_DEPLOYMENT_GUIDE.md
goto end

:end

