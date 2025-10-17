# PowerShell script for setting up WHAC Notification System on Windows
# Run with: powershell -ExecutionPolicy Bypass -File setup_notifications.ps1

Write-Host "🔔 Setting up WHAC Notification System on Windows..." -ForegroundColor Green

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "⚠️  This script requires administrator privileges. Please run PowerShell as Administrator." -ForegroundColor Yellow
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to continue anyway (some features may not work)"
}

# Install Python dependencies
Write-Host "🐍 Installing Python dependencies..." -ForegroundColor Cyan
try {
    pip install pystray pillow
    Write-Host "✅ Python dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install Python dependencies: $_" -ForegroundColor Red
    Write-Host "Please install manually: pip install pystray pillow" -ForegroundColor Yellow
}

# Install Windows-specific dependencies
Write-Host "📦 Installing Windows dependencies..." -ForegroundColor Cyan
try {
    # Install Windows notification support
    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Write-Host "Installing Windows notification tools via winget..." -ForegroundColor Cyan
        winget install --id=Microsoft.WindowsTerminal --silent --accept-package-agreements --accept-source-agreements
    } else {
        Write-Host "⚠️  winget not available, skipping Windows tools installation" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not install Windows dependencies: $_" -ForegroundColor Yellow
}

# Create desktop shortcut for notification launcher
Write-Host "🖥️ Creating desktop shortcut..." -ForegroundColor Cyan
try {
    $currentPath = Get-Location
    $shortcutPath = "$env:USERPROFILE\Desktop\WHAC Notifications.lnk"
    $targetPath = "$currentPath\notification_launcher.py"
    
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = "python"
    $Shortcut.Arguments = "`"$targetPath`""
    $Shortcut.WorkingDirectory = $currentPath
    $Shortcut.Description = "WHAC Fingerprint System Notifications"
    $Shortcut.IconLocation = "shell32.dll,1"
    $Shortcut.Save()
    
    Write-Host "✅ Desktop shortcut created: $shortcutPath" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create desktop shortcut: $_" -ForegroundColor Red
}

# Create Start Menu entry
Write-Host "📋 Creating Start Menu entry..." -ForegroundColor Cyan
try {
    $currentPath = Get-Location
    $startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\WHAC Notifications.lnk"
    
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($startMenuPath)
    $Shortcut.TargetPath = "python"
    $Shortcut.Arguments = "`"$currentPath\notification_launcher.py`""
    $Shortcut.WorkingDirectory = $currentPath
    $Shortcut.Description = "WHAC Fingerprint System Notifications"
    $Shortcut.IconLocation = "shell32.dll,1"
    $Shortcut.Save()
    
    Write-Host "✅ Start Menu entry created" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create Start Menu entry: $_" -ForegroundColor Red
}

# Create Windows Service (requires admin privileges)
if ($isAdmin) {
    Write-Host "⚙️ Creating Windows Service..." -ForegroundColor Cyan
    try {
        $currentPath = Get-Location
        $serviceName = "WHACNotifications"
        $serviceDisplayName = "WHAC Notification System"
        $serviceDescription = "WHAC Fingerprint System Notification Service"
        
        # Check if service already exists
        $existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($existingService) {
            Write-Host "⚠️  Service $serviceName already exists. Stopping and removing..." -ForegroundColor Yellow
            Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
            sc.exe delete $serviceName
            Start-Sleep -Seconds 2
        }
        
        # Create the service
        $servicePath = "python `"$currentPath\notification_launcher.py`""
        sc.exe create $serviceName binPath= $servicePath DisplayName= $serviceDisplayName start= auto
        sc.exe description $serviceName $serviceDescription
        
        Write-Host "✅ Windows Service created: $serviceName" -ForegroundColor Green
        Write-Host "To start the service: Start-Service -Name $serviceName" -ForegroundColor Cyan
        Write-Host "To stop the service: Stop-Service -Name $serviceName" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ Failed to create Windows Service: $_" -ForegroundColor Red
        Write-Host "You can still run the notification system manually" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Skipping Windows Service creation (requires administrator privileges)" -ForegroundColor Yellow
}

# Create Windows Task Scheduler task
Write-Host "⏰ Creating Task Scheduler task..." -ForegroundColor Cyan
try {
    $currentPath = Get-Location
    $taskName = "WHACNotifications"
    $taskDescription = "WHAC Fingerprint System Notifications"
    
    # Remove existing task if it exists
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # Create new task
    $action = New-ScheduledTaskAction -Execute "python" -Argument "`"$currentPath\notification_launcher.py`"" -WorkingDirectory $currentPath
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType InteractiveToken
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $taskDescription
    
    Write-Host "✅ Task Scheduler task created: $taskName" -ForegroundColor Green
    Write-Host "The notification system will start automatically when you log in" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Failed to create Task Scheduler task: $_" -ForegroundColor Red
}

# Configure Windows notifications
Write-Host "🔔 Configuring Windows notifications..." -ForegroundColor Cyan
try {
    # Enable Windows notifications
    Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings" -Name "NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK" -Value 1 -ErrorAction SilentlyContinue
    Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings" -Name "NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK" -Value 1 -ErrorAction SilentlyContinue
    
    Write-Host "✅ Windows notifications configured" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not configure Windows notifications: $_" -ForegroundColor Yellow
}

# Test notification system
Write-Host "🧪 Testing notification system..." -ForegroundColor Cyan
try {
    Write-Host "Starting notification launcher for testing..." -ForegroundColor Cyan
    Start-Process python -ArgumentList "`"$currentPath\notification_launcher.py`"" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    
    Write-Host "✅ Notification system test started" -ForegroundColor Green
    Write-Host "Check for notification popups or system tray icon" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Failed to test notification system: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 WHAC Notification System setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Available notification types:" -ForegroundColor Cyan
Write-Host "   1. Desktop Notifications (system-wide popup)" -ForegroundColor White
Write-Host "   2. System Tray Notifications (less intrusive)" -ForegroundColor White
Write-Host "   3. Browser Popup Notifications (web-based)" -ForegroundColor White
Write-Host ""
Write-Host "🚀 To start notifications manually:" -ForegroundColor Cyan
Write-Host "   python notification_launcher.py" -ForegroundColor White
Write-Host ""
Write-Host "🔄 To start as Windows Service (if created):" -ForegroundColor Cyan
Write-Host "   Start-Service -Name WHACNotifications" -ForegroundColor White
Write-Host ""
Write-Host "📊 To check service status:" -ForegroundColor Cyan
Write-Host "   Get-Service -Name WHACNotifications" -ForegroundColor White
Write-Host ""
Write-Host "🖥️ Desktop shortcut created on your desktop" -ForegroundColor Cyan
Write-Host "📋 Start Menu entry created in Programs" -ForegroundColor Cyan
Write-Host "⏰ Task Scheduler task created for auto-start" -ForegroundColor Cyan

Read-Host "Press Enter to exit"

