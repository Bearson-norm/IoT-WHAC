# =====================================================
# Script PowerShell untuk Setup Auto-Cleanup dengan Task Scheduler
# Database: whac_master
# =====================================================
# 
# Script ini membuat scheduled task untuk auto-cleanup logs
# lebih dari 3 bulan setiap hari jam 2 pagi
# =====================================================

$CONTAINER_NAME = "whac-postgres"
$DB_NAME = "whac_master"
$DB_USER = "postgres"
$CLEANUP_TIME = "02:00"  # Jam 2 pagi
$TASK_NAME = "WHAC_AutoCleanup_Logs"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Auto-Cleanup Scheduled Task" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Cek apakah container berjalan
Write-Host "[1/4] Checking Docker container..." -ForegroundColor Yellow
$container = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}"
if (-not $container) {
    Write-Host "❌ Container $CONTAINER_NAME tidak berjalan!" -ForegroundColor Red
    Write-Host "   Jalankan: docker-compose up -d postgres" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Container $CONTAINER_NAME berjalan" -ForegroundColor Green
Write-Host ""

# Test koneksi database
Write-Host "[2/4] Testing database connection..." -ForegroundColor Yellow
$testResult = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT 1;" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database connection OK" -ForegroundColor Green
} else {
    Write-Host "❌ Database connection failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Cek apakah function sudah ada
Write-Host "[3/4] Checking cleanup functions..." -ForegroundColor Yellow
$functionExists = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM pg_proc WHERE proname = 'cleanup_old_log_data';" 2>&1 | ForEach-Object { $_.Trim() }

if ($functionExists -eq "0") {
    Write-Host "⚠️  Cleanup function belum ada" -ForegroundColor Yellow
    Write-Host "   Jalankan auto_cleanup_logs.sql terlebih dahulu" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Cleanup function sudah ada" -ForegroundColor Green
Write-Host ""

# Buat PowerShell script untuk cleanup
Write-Host "[4/4] Creating scheduled task..." -ForegroundColor Yellow

$cleanupScript = @"
# Auto-cleanup logs lebih dari 3 bulan
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT * FROM cleanup_old_log_data();" | Out-File -Append "C:\logs\whac_cleanup.log"
"@

$scriptPath = "$PSScriptRoot\cleanup_logs.ps1"
$cleanupScript | Out-File -FilePath $scriptPath -Encoding UTF8

Write-Host "✅ Cleanup script created: $scriptPath" -ForegroundColor Green

# Cek apakah task sudah ada
$existingTask = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "⚠️  Scheduled task sudah ada" -ForegroundColor Yellow
    $response = Read-Host "   Update task? (Y/N)"
    if ($response -eq 'Y' -or $response -eq 'y') {
        Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:$false
    } else {
        Write-Host "   Task tidak di-update" -ForegroundColor Gray
        exit 0
    }
}

# Buat scheduled task
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At $CLEANUP_TIME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest

try {
    Register-ScheduledTask -TaskName $TASK_NAME -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Auto-cleanup WHAC logs lebih dari 3 bulan" | Out-Null
    Write-Host "✅ Scheduled task created: $TASK_NAME" -ForegroundColor Green
    Write-Host "   Schedule: Daily at $CLEANUP_TIME" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Scheduled task akan menjalankan cleanup setiap hari jam $CLEANUP_TIME" -ForegroundColor Yellow
Write-Host "Log akan disimpan di: C:\logs\whac_cleanup.log" -ForegroundColor Gray
Write-Host ""
Write-Host "Untuk test manual:" -ForegroundColor Yellow
Write-Host "  docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c `"SELECT * FROM cleanup_old_log_data();`"" -ForegroundColor Gray
Write-Host ""
Write-Host "Untuk melihat scheduled task:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName $TASK_NAME" -ForegroundColor Gray
Write-Host ""












