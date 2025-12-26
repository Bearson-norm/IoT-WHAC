@echo off
REM Quick Setup Script for Local Machine - Windows
REM Note: GPIO control hanya bekerja di Raspberry Pi, tidak di Windows

echo ========================================
echo IoT-WHAC Local Machine Setup
echo ========================================
echo.
echo [INFO] Script ini untuk setup di Windows
echo [INFO] GPIO control hanya bekerja di Raspberry Pi
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
cd local_machine
if not exist requirements.txt (
    echo [ERROR] File requirements.txt tidak ditemukan!
    echo Pastikan Anda berada di direktori project yang benar.
    pause
    exit /b 1
)

echo Menginstall dependencies...
echo [INFO] Beberapa library (RPi.GPIO) mungkin error di Windows - ini normal
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Ada error saat install dependencies
    echo [INFO] Error RPi.GPIO normal di Windows (hanya untuk Raspberry Pi)
    echo Lanjutkan manual jika perlu: pip install -r requirements.txt
)

echo.
echo ========================================
echo Step 2: Setup Configuration
echo ========================================
if not exist .env (
    if exist env.example (
        echo Membuat file .env dari env.example...
        copy env.example .env
        echo [OK] File .env sudah dibuat
        echo [INFO] Edit .env jika perlu mengubah konfigurasi
    ) else (
        echo [INFO] File env.example tidak ditemukan, skip...
    )
) else (
    echo [INFO] File .env sudah ada
)

echo.
echo ========================================
echo Step 3: Check Serial Ports
echo ========================================
echo.
echo [INFO] Untuk cek port serial sensor fingerprint:
echo   python check_serial_ports.py
echo.
set /p check_port="Cek port serial sekarang? (y/n): "
if /i "%check_port%"=="y" (
    if exist check_serial_ports.py (
        python check_serial_ports.py
    ) else (
        echo [INFO] File check_serial_ports.py tidak ditemukan
    )
)

echo.
echo ========================================
echo Step 4: Ready to Run
echo ========================================
echo.
echo Setup selesai! Untuk menjalankan:
echo.
echo Terminal 1 - Fingerprint Scanner:
echo   cd local_machine
echo   python fingerprint_multi_client.py
echo.
echo Terminal 2 - Relay Controller (jika digunakan):
echo   cd local_machine
echo   python relay_controller_advanced.py
echo.
echo [CATATAN]
echo - GPIO control hanya bekerja di Raspberry Pi
echo - Di Windows, program akan tetap berjalan untuk testing
echo - Pastikan sensor fingerprint terhubung dan terdeteksi
echo.
pause

