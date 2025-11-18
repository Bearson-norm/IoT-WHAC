# PowerShell script untuk test koneksi DBeaver ke database Docker

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Test Koneksi DBeaver ke Database Docker" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Cek container
Write-Host "`n[1] Checking Docker container..." -ForegroundColor Yellow
$container = docker ps --filter "name=whac-postgres" --format "{{.Names}}"
if ($container) {
    Write-Host "[OK] Container found: $container" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Container whac-postgres is not running!" -ForegroundColor Red
    Write-Host "   Start it with: docker-compose up -d postgres" -ForegroundColor Yellow
    exit 1
}

# Step 2: Cek port
Write-Host "`n[2] Checking port 5432..." -ForegroundColor Yellow
$portCheck = netstat -ano | Select-String ":5432" | Select-String "LISTENING"
if ($portCheck) {
    Write-Host "[OK] Port 5432 is listening" -ForegroundColor Green
    Write-Host "   Processes:" -ForegroundColor Gray
    $portCheck | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "[WARNING] Port 5432 is not listening" -ForegroundColor Yellow
}

# Step 3: Test connection dari container
Write-Host "`n[3] Testing connection from container..." -ForegroundColor Yellow
try {
    $result = docker exec whac-postgres psql -U postgres -d whac_master -t -c "SELECT current_database(), current_user;"
    if ($result) {
        Write-Host "[OK] Container database is accessible" -ForegroundColor Green
        Write-Host "   $result" -ForegroundColor Gray
    }
} catch {
    Write-Host "[ERROR] Cannot connect from container" -ForegroundColor Red
}

# Step 4: Test connection dari host (seperti DBeaver)
Write-Host "`n[4] Testing connection from host (like DBeaver)..." -ForegroundColor Yellow

# Check if psql is available
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if ($psqlPath) {
    $env:PGPASSWORD = "Admin123"
    try {
        $result = psql -h localhost -U postgres -d whac_master -t -c "SELECT current_database(), current_user, inet_server_addr();" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Connection from host successful!" -ForegroundColor Green
            Write-Host "   $result" -ForegroundColor Gray
        } else {
            Write-Host "[ERROR] Connection failed" -ForegroundColor Red
            Write-Host "   Error: $result" -ForegroundColor Red
        }
    } catch {
        Write-Host "[ERROR] Error: $_" -ForegroundColor Red
    }
} else {
    Write-Host "[WARNING] psql not found locally, using Docker..." -ForegroundColor Yellow
    try {
        $result = docker run --rm --network host postgres:13 psql -h localhost -U postgres -d whac_master -t -c "SELECT current_database(), current_user;" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Connection from host successful (via Docker)!" -ForegroundColor Green
            Write-Host "   $result" -ForegroundColor Gray
        } else {
            Write-Host "[ERROR] Connection failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "[ERROR] Error: $_" -ForegroundColor Red
    }
}

# Step 5: Cek data
Write-Host "`n[5] Checking data in database..." -ForegroundColor Yellow
try {
    $userCount = docker exec whac-postgres psql -U postgres -d whac_master -t -c "SELECT COUNT(*) FROM web_users;"
    if ($userCount) {
        Write-Host "[OK] Found $($userCount.Trim()) users in database" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] Cannot check data" -ForegroundColor Yellow
}

# Step 6: Summary
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "DBeaver Configuration" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Host: localhost" -ForegroundColor White
Write-Host "Port: 5432" -ForegroundColor White
Write-Host "Database: whac_master" -ForegroundColor White
Write-Host "Username: postgres" -ForegroundColor White
Write-Host "Password: Admin123" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nTips:" -ForegroundColor Yellow
Write-Host "1. Pastikan container berjalan: docker ps | Select-String postgres" -ForegroundColor Gray
Write-Host "2. Jika ada PostgreSQL lokal, stop service terlebih dahulu" -ForegroundColor Gray
Write-Host "3. Test connection di DBeaver dengan konfigurasi di atas" -ForegroundColor Gray
Write-Host "4. Jika masih tidak bisa, cek firewall atau network settings" -ForegroundColor Gray

