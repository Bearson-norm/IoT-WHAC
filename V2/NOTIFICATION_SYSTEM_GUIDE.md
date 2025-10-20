# WHAC Notification System Guide

This guide explains how to set up and use the system-wide notification system that interrupts operator activity when users scan in the warehouse.

## 🎯 **Notification Types Available**

### 1. **Desktop Notifications** (Most Intrusive)
- **File**: `web_ui/desktop_notification_system.py`
- **Features**: Full-screen popup that covers the entire desktop
- **Use Case**: Critical alerts that require immediate attention
- **Behavior**: Blocks all other activities until acknowledged

### 2. **System Tray Notifications** (Least Intrusive)
- **File**: `web_ui/system_tray_notification.py`
- **Features**: Small notifications in the system tray
- **Use Case**: Regular alerts that don't interrupt workflow
- **Behavior**: Appears in system tray, doesn't block other activities

### 3. **Browser Popup Notifications** (Web-based)
- **File**: `web_ui/notification_launcher.py` + `web_ui/templates/notification_popup.html`
- **Features**: Browser-based popup with full functionality
- **Use Case**: When you want web-based notifications with action buttons
- **Behavior**: Opens in browser, can be minimized or closed

## 🚀 **Quick Setup**

### **Option 1: Automated Setup**
```bash
cd web_ui
chmod +x setup_notifications.sh
./setup_notifications.sh
```

### **Option 2: Manual Setup**
```bash
# Install dependencies
pip3 install pystray pillow

# Install system dependencies
sudo apt install -y python3-tk python3-pil python3-pil.imagetk

# Start notification launcher
python3 notification_launcher.py
```

## 🎮 **Usage Examples**

### **Start Desktop Notifications (Most Intrusive)**
```bash
python3 desktop_notification_system.py
```
- Creates full-screen popups
- Blocks all other activities
- Requires acknowledgment
- Best for critical security alerts

### **Start System Tray Notifications (Least Intrusive)**
```bash
python3 system_tray_notification.py
```
- Shows small notifications in system tray
- Doesn't interrupt other activities
- Good for regular monitoring
- Requires pystray library

### **Start Browser Popup Notifications (Web-based)**
```bash
python3 notification_launcher.py
```
- Opens notifications in browser
- Full web-based interface
- Action buttons for user commands
- Works on any system with a browser

## 🔧 **Configuration**

### **Notification Settings**
Edit the notification files to customize:

```python
# In notification_launcher.py
self.auto_close_delay = 30  # seconds
self.notification_url = "http://localhost:5000/notification_popup.html"
```

### **MQTT Topics**
The system listens to these MQTT topics:
- `WHAC/Store001/in` - Fingerprint scan data
- `WHAC/Store001/notification` - General notifications

### **Customization Options**
- **Auto-close delay**: How long before notification auto-closes
- **Sound alerts**: Enable/disable audio notifications
- **Visual effects**: Blinking, pulsing, colors
- **Action buttons**: Customize available actions

## 📱 **Notification Features**

### **Visual Elements**
- 🚨 **Alert Icon**: Blinking warning icon
- 📊 **User Details**: ID, username, timestamp, confidence
- 🎨 **Color Coding**: Red for alerts, blue for info, green for success
- ⏰ **Countdown Timer**: Shows time until auto-close

### **Action Buttons**
- 🔍 **Open Dashboard**: Opens web dashboard
- ✅ **Acknowledge**: Marks notification as seen
- 🔄 **Turn Around**: Sends command to user
- 🤲 **Stretch Arms**: Sends command to user
- ❌ **Dismiss**: Closes notification

### **Audio Alerts**
- 🔊 **System Beep**: Plays when notification appears
- 🔁 **Repeating Sound**: Plays every 5 seconds
- 🎵 **Custom Sounds**: Can be configured for different alert types

## 🧪 **Testing the System**

### **Test All Notification Types**
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

# Send test violation
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/notification" -m '{"type":"violation","message":"Test violation detected"}'
```

## 🔄 **Integration with Main System**

### **With WHAC Integrated System**
```bash
# Start main system
python3 whac_integrated_system.py

# In another terminal, start notifications
python3 notification_launcher.py
```

### **With Web Dashboard**
1. Start web dashboard: `python3 app.py`
2. Start notification launcher: `python3 notification_launcher.py`
3. Notifications will appear when users scan

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Desktop Notifications Not Appearing**
```bash
# Check if tkinter is installed
python3 -c "import tkinter; print('tkinter OK')"

# Check display settings
echo $DISPLAY
```

#### **System Tray Not Working**
```bash
# Install pystray
pip3 install pystray

# Check if system tray is available
python3 -c "import pystray; print('pystray OK')"
```

#### **Browser Popup Not Opening**
```bash
# Check if web server is running
curl http://localhost:5000/notification_popup.html

# Check browser availability
which firefox || which chrome || which chromium
```

### **Debug Mode**
```bash
# Run with debug logging
PYTHONPATH=. python3 -u notification_launcher.py
```

## 📊 **Performance Considerations**

### **Resource Usage**
- **CPU**: Minimal (only when notifications appear)
- **Memory**: ~10-20MB per notification type
- **Network**: Only MQTT communication
- **Disk**: Minimal (just log files)

### **Optimization Tips**
- Use only one notification type at a time
- Close unused notification windows
- Monitor system resources with `htop`
- Use system tray notifications for less critical alerts

## 🔒 **Security Considerations**

### **Access Control**
- Notifications run with user permissions
- MQTT credentials should be secured
- Web notifications require authentication

### **Privacy**
- Notifications may be visible to others
- Consider using system tray for sensitive environments
- Log files may contain user information

## 🎯 **Best Practices**

### **For Production**
1. Use system tray notifications for regular monitoring
2. Use desktop notifications only for critical alerts
3. Set up proper logging and monitoring
4. Test notifications thoroughly before deployment

### **For Development**
1. Use browser popup notifications for testing
2. Enable debug logging
3. Test with different user scenarios
4. Verify MQTT connectivity

## 📞 **Support**

If you encounter issues:

1. **Check logs**: Look at the notification system logs
2. **Test MQTT**: Verify MQTT broker connectivity
3. **Check dependencies**: Ensure all required libraries are installed
4. **Verify permissions**: Make sure the user has proper permissions

## 🎉 **Success Indicators**

The notification system is working correctly when:
- ✅ Notifications appear when users scan
- ✅ Action buttons work properly
- ✅ Audio alerts play
- ✅ Notifications auto-close after timeout
- ✅ MQTT messages are received
- ✅ No error messages in logs

---

**Note**: The notification system is designed to be flexible and can be customized based on your specific requirements. Choose the notification type that best fits your operational needs!



