# Cross-Platform Setup Guide for WHAC Notifications

This guide provides setup instructions for the WHAC notification system across different operating systems.

## 🖥️ **Supported Operating Systems**

- ✅ **Windows 10/11** - PowerShell and Batch scripts
- ✅ **Linux** (Ubuntu, Debian, CentOS, Arch, openSUSE) - Bash script
- ✅ **macOS** - Bash script with Homebrew support
- ✅ **Raspberry Pi OS** - Optimized for ARM architecture

## 🚀 **Quick Setup by OS**

### **Windows 10/11**

#### **Option 1: PowerShell (Recommended)**
```powershell
# Run PowerShell as Administrator
cd web_ui
powershell -ExecutionPolicy Bypass -File setup_notifications.ps1
```

#### **Option 2: Batch File**
```cmd
# Run Command Prompt as Administrator
cd web_ui
setup_notifications.bat
```

**Features:**
- ✅ Desktop shortcut creation
- ✅ Start Menu entry
- ✅ Windows Service creation
- ✅ Task Scheduler integration
- ✅ Windows notification configuration

### **Linux (Ubuntu/Debian)**
```bash
cd web_ui
chmod +x setup_notifications.sh
./setup_notifications.sh
```

**Features:**
- ✅ Desktop entry creation
- ✅ Systemd service
- ✅ GNOME/KDE notification configuration
- ✅ Package manager integration (apt, yum, pacman, zypper)

### **macOS**
```bash
cd web_ui
chmod +x setup_notifications.sh
./setup_notifications.sh
```

**Features:**
- ✅ Application bundle creation
- ✅ LaunchAgent service
- ✅ Homebrew integration
- ✅ macOS notification configuration

### **Raspberry Pi OS**
```bash
cd web_ui
chmod +x setup_notifications.sh
./setup_notifications.sh
```

**Features:**
- ✅ Optimized for ARM architecture
- ✅ GPIO support
- ✅ Audio system integration
- ✅ Lightweight dependencies

## 📋 **Manual Setup Instructions**

If the automated scripts don't work, follow these manual steps:

### **Windows Manual Setup**

1. **Install Python Dependencies**
   ```cmd
   pip install pystray pillow
   ```

2. **Create Desktop Shortcut**
   - Right-click on desktop
   - New → Shortcut
   - Target: `python "C:\path\to\notification_launcher.py"`
   - Name: "WHAC Notifications"

3. **Create Windows Service**
   ```cmd
   sc create WHACNotifications binPath= "python \"C:\path\to\notification_launcher.py\"" start= auto
   sc start WHACNotifications
   ```

### **Linux Manual Setup**

1. **Install Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-tk python3-pil python3-pil.imagetk
   pip3 install pystray pillow
   
   # CentOS/RHEL
   sudo yum install tkinter python3-pillow
   pip3 install pystray pillow
   
   # Arch Linux
   sudo pacman -S tk python-pillow
   pip3 install pystray pillow
   ```

2. **Create Desktop Entry**
   ```bash
   cat > ~/.local/share/applications/whac-notifications.desktop << EOF
   [Desktop Entry]
   Version=1.0
   Type=Application
   Name=WHAC Notifications
   Exec=python3 /path/to/notification_launcher.py
   Icon=applications-system
   Terminal=false
   Categories=System;Security;
   EOF
   ```

3. **Create Systemd Service**
   ```bash
   sudo tee /etc/systemd/system/whac-notifications.service > /dev/null << EOF
   [Unit]
   Description=WHAC Notification System
   After=network.target
   
   [Service]
   Type=simple
   User=$USER
   ExecStart=python3 /path/to/notification_launcher.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   sudo systemctl enable whac-notifications.service
   sudo systemctl start whac-notifications.service
   ```

### **macOS Manual Setup**

1. **Install Dependencies**
   ```bash
   # Install Homebrew if not installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install dependencies
   brew install python-tk
   pip3 install pystray pillow
   ```

2. **Create Application Bundle**
   ```bash
   mkdir -p ~/Applications/WHAC\ Notifications.app/Contents/MacOS
   # Copy the Info.plist and executable from the setup script
   ```

3. **Create LaunchAgent**
   ```bash
   cat > ~/Library/LaunchAgents/com.whac.notifications.plist << EOF
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.whac.notifications</string>
       <key>ProgramArguments</key>
       <array>
           <string>python3</string>
           <string>/path/to/notification_launcher.py</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
   </dict>
   </plist>
   EOF
   
   launchctl load ~/Library/LaunchAgents/com.whac.notifications.plist
   ```

## 🧪 **Testing the Setup**

### **Test Notification System**
```bash
# Test desktop notifications
python3 desktop_notification_system.py

# Test system tray notifications
python3 system_tray_notification.py

# Test browser popup notifications
python3 notification_launcher.py
```

### **Test with MQTT**
```bash
# Send test scan data
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/in" -m '{"status":"Match","fingerprint_id":"123","username":"Test User","confidence":95}'
```

## 🔧 **Troubleshooting by OS**

### **Windows Issues**

#### **PowerShell Execution Policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **Service Creation Failed**
- Run Command Prompt as Administrator
- Check if Python is in PATH
- Verify file paths are correct

#### **Desktop Shortcut Not Working**
- Check if Python is installed
- Verify file paths
- Try running manually first

### **Linux Issues**

#### **Permission Denied**
```bash
chmod +x setup_notifications.sh
sudo chown $USER:$USER /path/to/files
```

#### **Package Manager Not Found**
- Install the appropriate package manager for your distribution
- Use manual installation steps

#### **Systemd Service Failed**
```bash
sudo systemctl status whac-notifications.service
sudo journalctl -u whac-notifications.service
```

### **macOS Issues**

#### **Homebrew Not Found**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### **LaunchAgent Not Loading**
```bash
launchctl list | grep whac
launchctl unload ~/Library/LaunchAgents/com.whac.notifications.plist
launchctl load ~/Library/LaunchAgents/com.whac.notifications.plist
```

#### **Application Bundle Not Working**
- Check file permissions
- Verify Python path
- Test executable manually

## 📊 **Platform-Specific Features**

### **Windows Features**
- Windows Service integration
- Task Scheduler support
- Windows notification system
- Desktop shortcuts
- Start Menu integration

### **Linux Features**
- Systemd service
- Desktop environment integration
- Package manager support
- Multiple distribution support
- GNOME/KDE notification configuration

### **macOS Features**
- LaunchAgent service
- Application bundle creation
- Homebrew integration
- macOS notification system
- Native app integration

### **Raspberry Pi Features**
- ARM architecture optimization
- GPIO support
- Audio system integration
- Lightweight dependencies
- Low resource usage

## 🎯 **Best Practices by Platform**

### **Windows**
1. Run setup scripts as Administrator
2. Use PowerShell for better error handling
3. Test services before enabling auto-start
4. Check Windows Defender exclusions

### **Linux**
1. Use appropriate package manager
2. Check systemd service status
3. Verify desktop environment compatibility
4. Test notification permissions

### **macOS**
1. Install Homebrew first
2. Check LaunchAgent permissions
3. Test application bundle
4. Verify notification settings

### **Raspberry Pi**
1. Use optimized scripts
2. Check GPIO permissions
3. Test audio system
4. Monitor resource usage

## 📞 **Getting Help**

### **Common Issues**
1. **Python not found**: Install Python 3.7+
2. **Permission denied**: Run with appropriate privileges
3. **Dependencies missing**: Install required packages
4. **Service not starting**: Check logs and configuration

### **Debug Commands**
```bash
# Check Python version
python3 --version

# Check installed packages
pip3 list | grep -E "(pystray|pillow)"

# Check service status (Linux)
sudo systemctl status whac-notifications.service

# Check service status (Windows)
sc query WHACNotifications

# Check LaunchAgent status (macOS)
launchctl list | grep whac
```

---

**Note**: The setup scripts are designed to be robust and handle most common scenarios. If you encounter issues, try the manual setup steps or check the troubleshooting section for your specific operating system.

