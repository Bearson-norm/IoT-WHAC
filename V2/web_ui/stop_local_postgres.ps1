# PowerShell script untuk stop PostgreSQL lokal service

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Stopping Local PostgreSQL Service" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check service status
Write-Host "`n[1] Checking PostgreSQL services..." -ForegroundColor Yellow
$postgresServices = Get-Service | Where-Object { 
    ($_.Name -like "*postgres*" -or $_.DisplayName -like "*PostgreSQL*") -and 
    $_.Status -eq 'Running'
}

if (-not $postgresServices) {
    Write-Host "[OK] No running PostgreSQL services found" -ForegroundColor Green
    Write-Host "Docker container should be the only one using port 5432" -ForegroundColor Gray
    exit 0
}

Write-Host "Found running PostgreSQL services:" -ForegroundColor Yellow
foreach ($svc in $postgresServices) {
    Write-Host "  - $($svc.Name) ($($svc.DisplayName))" -ForegroundColor White
}

# Stop services
Write-Host "`n[2] Stopping PostgreSQL services..." -ForegroundColor Yellow
foreach ($svc in $postgresServices) {
    try {
        Write-Host "Stopping: $($svc.Name)..." -ForegroundColor Yellow
        Stop-Service -Name $svc.Name -Force
        Start-Sleep -Seconds 2
        
        # Verify
        $svc.Refresh()
        if ($svc.Status -eq 'Stopped') {
            Write-Host "[OK] Service $($svc.Name) stopped successfully" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Service $($svc.Name) status: $($svc.Status)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] Failed to stop $($svc.Name): $_" -ForegroundColor Red
    }
}

# Verify port 5432
Write-Host "`n[3] Verifying port 5432..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$listening = netstat -ano | Select-String ":5432" | Select-String "LISTENING"
$count = ($listening | Measure-Object).Count

if ($count -eq 1) {
    Write-Host "[OK] Only 1 process listening on port 5432 (should be Docker)" -ForegroundColor Green
} elseif ($count -eq 0) {
    Write-Host "[WARNING] No process listening on port 5432" -ForegroundColor Yellow
    Write-Host "Make sure Docker container is running!" -ForegroundColor Yellow
} else {
    Write-Host "[WARNING] Still $count processes listening on port 5432" -ForegroundColor Yellow
    Write-Host "You may need to restart Docker container" -ForegroundColor Yellow
}

# Check Docker container
Write-Host "`n[4] Checking Docker container..." -ForegroundColor Yellow
$dockerContainer = docker ps --filter "name=whac-postgres" --format "{{.Names}}"
if ($dockerContainer) {
    Write-Host "[OK] Docker container is running: $dockerContainer" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Docker container whac-postgres is not running!" -ForegroundColor Yellow
    Write-Host "Start it with: docker-compose up -d postgres" -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Local PostgreSQL services stopped" -ForegroundColor White
Write-Host "DBeaver should now connect to Docker database only" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan



