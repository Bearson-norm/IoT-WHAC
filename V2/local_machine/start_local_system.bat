@echo off
REM Batch script untuk menjalankan sistem local machine di Windows
REM Menjalankan fingerprint_multi_client.py dan relay_controller_advanced.py secara bersamaan

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo IoT-WHAC Local System Launcher
echo ============================================================
echo Starting fingerprint_multi_client.py and relay_controller_advanced.py
echo ============================================================

REM Cek apakah Python tersedia
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan!
    echo Silakan install Python 3.7+ dari https://www.python.org/
    pause
    exit /b 1
)

REM Cek apakah script ada
if not exist "fingerprint_multi_client.py" (
    echo [ERROR] fingerprint_multi_client.py tidak ditemukan!
    pause
    exit /b 1
)

if not exist "relay_controller_advanced.py" (
    echo [ERROR] relay_controller_advanced.py tidak ditemukan!
    pause
    exit /b 1
)

REM Jalankan menggunakan Python launcher (recommended)
if exist "start_local_system.py" (
    echo [OK] Using Python launcher (recommended)...
    python start_local_system.py
    goto :end
)

REM Fallback: jalankan langsung dengan start command
echo [WARNING] Python launcher tidak ditemukan, menggunakan fallback method...
echo [INFO] Disarankan menggunakan start_local_system.py untuk monitoring yang lebih baik
echo.

REM Start fingerprint client
echo [OK] Starting fingerprint_multi_client.py...
start "Fingerprint Client" /MIN python fingerprint_multi_client.py
if errorlevel 1 (
    echo [ERROR] Gagal start fingerprint_multi_client.py
    pause
    exit /b 1
)

REM Tunggu sebentar
timeout /t 3 /nobreak >nul

REM Start relay controller
echo [OK] Starting relay_controller_advanced.py...
start "Relay Controller" /MIN python relay_controller_advanced.py
if errorlevel 1 (
    echo [ERROR] Gagal start relay_controller_advanced.py
    echo [INFO] Menghentikan fingerprint client...
    taskkill /FI "WINDOWTITLE eq Fingerprint Client*" /F >nul 2>&1
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [OK] All components started!
echo ============================================================
echo [INFO] Kedua program berjalan di window terpisah
echo [INFO] Tutup window atau tekan Ctrl+C untuk stop
echo ============================================================
echo.
echo [INFO] Untuk melihat log, cek:
echo    - fingerprint_multi_client.log
echo    - relay_controller_advanced.log
echo.
echo [INFO] Untuk stop semua proses:
echo    taskkill /FI "WINDOWTITLE eq Fingerprint Client*" /F
echo    taskkill /FI "WINDOWTITLE eq Relay Controller*" /F
echo.
pause

:end
endlocal

