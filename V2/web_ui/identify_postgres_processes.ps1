# PowerShell script untuk identify proses PostgreSQL di port 5432

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Identifying PostgreSQL Processes on Port 5432" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Get processes listening on port 5432
Write-Host "`n[1] Processes listening on port 5432:" -ForegroundColor Yellow
$listening = netstat -ano | Select-String ":5432" | Select-String "LISTENING"
$pids = @()
foreach ($line in $listening) {
    $pid = ($line -split '\s+')[-1]
    if ($pid -and $pid -notin $pids) {
        $pids += $pid
    }
}

Write-Host "Found PIDs: $($pids -join ', ')" -ForegroundColor White

# Check each PID
Write-Host "`n[2] Checking each process:" -ForegroundColor Yellow
foreach ($pid in $pids) {
    Write-Host "`n--- PID: $pid ---" -ForegroundColor Cyan
    
    # Get process info
    try {
        $process = Get-Process -Id $pid -ErrorAction Stop
        Write-Host "Process Name: $($process.ProcessName)" -ForegroundColor White
        Write-Host "Path: $($process.Path)" -ForegroundColor Gray
        
        # Check if it's Docker
        $isDocker = $false
        if ($process.Path -like "*docker*" -or $process.ProcessName -like "*docker*") {
            $isDocker = $true
            Write-Host "Type: Docker Container" -ForegroundColor Green
        } elseif ($process.ProcessName -like "*postgres*") {
            Write-Host "Type: PostgreSQL Local Service" -ForegroundColor Yellow
        } else {
            Write-Host "Type: Unknown (check manually)" -ForegroundColor Red
        }
        
        # Check if it's a service
        try {
            $service = Get-Service | Where-Object { $_.Status -eq 'Running' -and (Get-WmiObject Win32_Service -Filter "ProcessId = $pid" -ErrorAction SilentlyContinue) }
            if ($service) {
                Write-Host "Windows Service: $($service.Name)" -ForegroundColor Magenta
                Write-Host "Display Name: $($service.DisplayName)" -ForegroundColor Magenta
                
                if (-not $isDocker) {
                    Write-Host "`n>>> This is a LOCAL PostgreSQL service that should be stopped!" -ForegroundColor Red
                    Write-Host "    Command to stop: Stop-Service -Name '$($service.Name)'" -ForegroundColor Yellow
                }
            }
        } catch {
            # Not a service or can't determine
        }
        
    } catch {
        Write-Host "Cannot get process info (may have terminated)" -ForegroundColor Red
    }
}

# Check Docker containers
Write-Host "`n[3] Checking Docker containers:" -ForegroundColor Yellow
$dockerContainers = docker ps --filter "name=postgres" --format "{{.Names}} {{.ID}}"
if ($dockerContainers) {
    Write-Host "Docker PostgreSQL containers:" -ForegroundColor Green
    $dockerContainers | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "No Docker PostgreSQL containers found" -ForegroundColor Yellow
}

# Check Windows Services
Write-Host "`n[4] Checking Windows PostgreSQL Services:" -ForegroundColor Yellow
$postgresServices = Get-Service | Where-Object { $_.Name -like "*postgres*" -or $_.DisplayName -like "*PostgreSQL*" }
if ($postgresServices) {
    Write-Host "PostgreSQL Services found:" -ForegroundColor Yellow
    foreach ($svc in $postgresServices) {
        $status = if ($svc.Status -eq 'Running') { "RUNNING" } else { "STOPPED" }
        $color = if ($svc.Status -eq 'Running') { "Red" } else { "Green" }
        Write-Host "  $($svc.Name) - $($svc.DisplayName) - Status: $status" -ForegroundColor $color
        
        if ($svc.Status -eq 'Running') {
            Write-Host "    >>> Stop with: Stop-Service -Name '$($svc.Name)'" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "No PostgreSQL Windows Services found" -ForegroundColor Green
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Recommendation:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "1. Keep Docker container running (whac-postgres)" -ForegroundColor White
Write-Host "2. Stop LOCAL PostgreSQL service if found above" -ForegroundColor White
Write-Host "3. After stopping, only Docker should listen on port 5432" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan



