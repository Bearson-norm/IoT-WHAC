@echo off
REM Batch script for setting up WHAC Notification System on Windows
REM Run with: setup_notifications.bat

echo 🔔 Setting up WHAC Notification System on Windows...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running with administrator privileges
    set IS_ADMIN=1
) else (
    echo ⚠️  Not running as administrator. Some features may not work.
    set IS_ADMIN=0
)

REM Install Python dependencies
echo 🐍 Installing Python dependencies...
pip install pystray pillow
if %errorLevel% == 0 (
    echo ✅ Python dependencies installed successfully
) else (
    echo ❌ Failed to install Python dependencies
    echo Please install manually: pip install pystray pillow
    pause
)

REM Get current directory
set CURRENT_DIR=%CD%

REM Create desktop shortcut
echo 🖥️ Creating desktop shortcut...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\WHAC Notifications.lnk
set TARGET_PATH=%CURRENT_DIR%\notification_launcher.py

REM Create VBScript to create shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%SHORTCUT_PATH%" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "python" >> CreateShortcut.vbs
echo oLink.Arguments = ""%TARGET_PATH%"" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "WHAC Fingerprint System Notifications" >> CreateShortcut.vbs
echo oLink.IconLocation = "shell32.dll,1" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript CreateShortcut.vbs >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Desktop shortcut created
) else (
    echo ❌ Failed to create desktop shortcut
)
del CreateShortcut.vbs

REM Create Start Menu entry
echo 📋 Creating Start Menu entry...
set START_MENU_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\WHAC Notifications.lnk

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateStartMenu.vbs
echo sLinkFile = "%START_MENU_PATH%" >> CreateStartMenu.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateStartMenu.vbs
echo oLink.TargetPath = "python" >> CreateStartMenu.vbs
echo oLink.Arguments = ""%TARGET_PATH%"" >> CreateStartMenu.vbs
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> CreateStartMenu.vbs
echo oLink.Description = "WHAC Fingerprint System Notifications" >> CreateStartMenu.vbs
echo oLink.IconLocation = "shell32.dll,1" >> CreateStartMenu.vbs
echo oLink.Save >> CreateStartMenu.vbs

cscript CreateStartMenu.vbs >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Start Menu entry created
) else (
    echo ❌ Failed to create Start Menu entry
)
del CreateStartMenu.vbs

REM Create Windows Service (requires admin privileges)
if %IS_ADMIN% == 1 (
    echo ⚙️ Creating Windows Service...
    set SERVICE_NAME=WHACNotifications
    set SERVICE_DISPLAY_NAME=WHAC Notification System
    set SERVICE_DESCRIPTION=WHAC Fingerprint System Notification Service
    
    REM Check if service already exists
    sc query %SERVICE_NAME% >nul 2>&1
    if %errorLevel% == 0 (
        echo ⚠️  Service %SERVICE_NAME% already exists. Stopping and removing...
        sc stop %SERVICE_NAME% >nul 2>&1
        sc delete %SERVICE_NAME% >nul 2>&1
        timeout /t 2 >nul
    )
    
    REM Create the service
    sc create %SERVICE_NAME% binPath= "python \"%TARGET_PATH%\"" DisplayName= "%SERVICE_DISPLAY_NAME%" start= auto >nul 2>&1
    if %errorLevel% == 0 (
        sc description %SERVICE_NAME% "%SERVICE_DESCRIPTION%" >nul 2>&1
        echo ✅ Windows Service created: %SERVICE_NAME%
        echo To start the service: sc start %SERVICE_NAME%
        echo To stop the service: sc stop %SERVICE_NAME%
    ) else (
        echo ❌ Failed to create Windows Service
        echo You can still run the notification system manually
    )
) else (
    echo ⚠️  Skipping Windows Service creation (requires administrator privileges)
)

REM Create Windows Task Scheduler task
echo ⏰ Creating Task Scheduler task...
set TASK_NAME=WHACNotifications
set TASK_DESCRIPTION=WHAC Fingerprint System Notifications

REM Remove existing task if it exists
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create new task
schtasks /create /tn "%TASK_NAME%" /tr "python \"%TARGET_PATH%\"" /sc onstart /ru "%USERNAME%" /f >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Task Scheduler task created: %TASK_NAME%
    echo The notification system will start automatically when you log in
) else (
    echo ❌ Failed to create Task Scheduler task
)

REM Configure Windows notifications
echo 🔔 Configuring Windows notifications...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings" /v "NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK" /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings" /v "NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK" /t REG_DWORD /d 1 /f >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Windows notifications configured
) else (
    echo ⚠️  Could not configure Windows notifications
)

REM Test notification system
echo 🧪 Testing notification system...
echo Starting notification launcher for testing...
start /min python "%TARGET_PATH%"
timeout /t 3 >nul
echo ✅ Notification system test started
echo Check for notification popups or system tray icon

echo.
echo 🎉 WHAC Notification System setup complete!
echo.
echo 📋 Available notification types:
echo    1. Desktop Notifications (system-wide popup)
echo    2. System Tray Notifications (less intrusive)
echo    3. Browser Popup Notifications (web-based)
echo.
echo 🚀 To start notifications manually:
echo    python notification_launcher.py
echo.
echo 🔄 To start as Windows Service (if created):
echo    sc start WHACNotifications
echo.
echo 📊 To check service status:
echo    sc query WHACNotifications
echo.
echo 🖥️ Desktop shortcut created on your desktop
echo 📋 Start Menu entry created in Programs
echo ⏰ Task Scheduler task created for auto-start

pause



