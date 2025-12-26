@echo off
REM Quick Setup Script for Web UI - Windows
REM This script helps setup the Web UI component

echo ========================================
echo IoT-WHAC Web UI Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak terinstall!
    echo Silakan install Python 3.7+ dari https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python terdeteksi
python --version

echo.
echo ========================================
echo Step 1: Install Dependencies
echo ========================================
cd web_ui
if not exist requirements.txt (
    echo [ERROR] File requirements.txt tidak ditemukan!
    echo Pastikan Anda berada di direktori project yang benar.
    pause
    exit /b 1
)

echo Menginstall dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Ada error saat install dependencies
    echo Lanjutkan manual: pip install -r requirements.txt
)

echo.
echo ========================================
echo Step 2: Setup Environment File
echo ========================================
if not exist .env (
    if exist env.example (
        echo Membuat file .env dari env.example...
        copy env.example .env
        echo [OK] File .env sudah dibuat
        echo [INFO] Edit .env jika perlu mengubah konfigurasi default
    ) else (
        echo [INFO] File env.example tidak ditemukan, skip...
    )
) else (
    echo [INFO] File .env sudah ada
)

echo.
echo ========================================
echo Step 3: Database Setup
echo ========================================
echo.
echo [INFO] Pastikan PostgreSQL sudah terinstall dan running
echo [INFO] Database 'whac_master' harus sudah dibuat
echo.
echo Untuk setup database:
echo   1. Install PostgreSQL
echo   2. Buat database: CREATE DATABASE whac_master;
echo   3. Jalankan schema: psql -U postgres -d whac_master -f database_setup.sql
echo.
set /p setup_db="Apakah database sudah di-setup? (y/n): "
if /i "%setup_db%"=="y" (
    echo [OK] Database setup sudah selesai
) else (
    echo [INFO] Silakan setup database terlebih dahulu
    echo Lihat PANDUAN_SETUP_SISTEM.md untuk detail
)

echo.
echo ========================================
echo Step 4: Ready to Run
echo ========================================
echo.
echo Setup selesai! Untuk menjalankan Web UI:
echo.
echo   cd web_ui
echo   python app.py
echo.
echo Akses di browser: http://localhost:5000
echo Login: admin / admin123
echo.
pause

