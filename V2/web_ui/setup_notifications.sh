#!/bin/bash
"""
Setup script for WHAC Notification System
Installs dependencies and configures system-wide notifications
Compatible with Linux, macOS, and Unix-like systems
"""

echo "🔔 Setting up WHAC Notification System..."

# Detect operating system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
    echo "⚠️  Windows detected. Please use setup_notifications.bat or setup_notifications.ps1 instead."
    exit 1
else
    OS="unknown"
    echo "⚠️  Unknown operating system: $OSTYPE"
fi

echo "🖥️  Detected OS: $OS"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install pystray pillow

# Install system dependencies based on OS
echo "📦 Installing system dependencies..."
if [[ "$OS" == "linux" ]]; then
    # Detect Linux distribution
    if command -v apt &> /dev/null; then
        # Debian/Ubuntu
        sudo apt update
        sudo apt install -y python3-tk python3-pil python3-pil.imagetk
    elif command -v yum &> /dev/null; then
        # Red Hat/CentOS
        sudo yum install -y tkinter python3-pillow
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -S --noconfirm tk python-pillow
    elif command -v zypper &> /dev/null; then
        # openSUSE
        sudo zypper install -y python3-tk python3-Pillow
    else
        echo "⚠️  Unknown Linux distribution. Please install python3-tk and python3-pil manually."
    fi
elif [[ "$OS" == "macos" ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install python-tk
        pip3 install pillow
    else
        echo "⚠️  Homebrew not found. Please install python3-tk and pillow manually."
    fi
fi

# Set up desktop notification permissions
echo "🔐 Setting up notification permissions..."

if [[ "$OS" == "linux" ]]; then
    # For Ubuntu/Debian systems
    if command -v gsettings &> /dev/null; then
        echo "Configuring desktop notifications..."
        gsettings set org.gnome.desktop.notifications show-banners true
        gsettings set org.gnome.desktop.notifications show-in-lock-screen true
    fi
    
    # For KDE systems
    if command -v kwriteconfig5 &> /dev/null; then
        echo "Configuring KDE notifications..."
        kwriteconfig5 --file kwinrc --group Effect-Blur --key BlurStrength 5
    fi
elif [[ "$OS" == "macos" ]]; then
    echo "Configuring macOS notifications..."
    # macOS notifications are enabled by default
    echo "✅ macOS notifications should work by default"
fi

# Create desktop entry for notification launcher
echo "🖥️ Creating desktop entry..."
if [[ "$OS" == "linux" ]]; then
    # Linux desktop entry
    mkdir -p ~/.local/share/applications
    cat > ~/.local/share/applications/whac-notifications.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=WHAC Notifications
Comment=WHAC Fingerprint System Notifications
Exec=python3 $(pwd)/notification_launcher.py
Icon=applications-system
Terminal=false
StartupNotify=true
Categories=System;Security;
EOF
    chmod +x ~/.local/share/applications/whac-notifications.desktop
elif [[ "$OS" == "macos" ]]; then
    # macOS application bundle (simplified)
    echo "Creating macOS application..."
    mkdir -p ~/Applications/WHAC\ Notifications.app/Contents/MacOS
    cat > ~/Applications/WHAC\ Notifications.app/Contents/Info.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>whac-notifications</string>
    <key>CFBundleIdentifier</key>
    <string>com.whac.notifications</string>
    <key>CFBundleName</key>
    <string>WHAC Notifications</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>
EOF
    cat > ~/Applications/WHAC\ Notifications.app/Contents/MacOS/whac-notifications << EOF
#!/bin/bash
cd "$(dirname "$0")/../../../../.."
python3 notification_launcher.py
EOF
    chmod +x ~/Applications/WHAC\ Notifications.app/Contents/MacOS/whac-notifications
fi

# Create auto-start service
echo "⚙️ Creating auto-start service..."
if [[ "$OS" == "linux" ]]; then
    # Linux systemd service
    sudo tee /etc/systemd/system/whac-notifications.service > /dev/null << EOF
[Unit]
Description=WHAC Notification System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=python3 $(pwd)/notification_launcher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable whac-notifications.service
elif [[ "$OS" == "macos" ]]; then
    # macOS launchd service
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
        <string>$(pwd)/notification_launcher.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
    launchctl load ~/Library/LaunchAgents/com.whac.notifications.plist
fi

echo "🎉 WHAC Notification System setup complete!"
echo ""
echo "📋 Available notification types:"
echo "   1. Desktop Notifications (system-wide popup)"
echo "   2. System Tray Notifications (less intrusive)"
echo "   3. Browser Popup Notifications (web-based)"
echo ""
echo "🚀 To start notifications:"
echo "   python3 notification_launcher.py"
echo ""
echo "🔄 To start as service:"
echo "   sudo systemctl start whac-notifications.service"
echo ""
echo "📊 To check service status:"
echo "   sudo systemctl status whac-notifications.service"
