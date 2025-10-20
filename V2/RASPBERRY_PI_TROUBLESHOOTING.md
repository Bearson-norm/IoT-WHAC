# Raspberry Pi Troubleshooting Guide

This guide helps resolve common issues when running the WHAC system on Raspberry Pi.

## 🚨 Common Issues and Solutions

### 1. Permission Denied Errors

**Error**: `[Errno 13] Permission denied: '/home/pi'`

**Solution**:
```bash
# Use current directory instead of /home/pi
cd /path/to/your/project
python3 whac_simple_system.py
```

### 2. GPIO Edge Detection Errors

**Error**: `GPIO setup error: Failed to add edge detection`

**Solution**: The system now automatically falls back to polling mode. This is normal and the system will still work.

### 3. Fingerprint Sensor Not Found

**Error**: `'NoneType' object has no attribute 'get_image'`

**Solutions**:
```bash
# Check if fingerprint sensor is connected
ls -la /dev/serial*
ls -la /dev/tty*

# Enable UART if needed
sudo raspi-config
# Navigate to: Interfacing Options > Serial
# Enable serial port hardware

# Check permissions
sudo usermod -a -G dialout $USER
```

### 4. Audio System Issues

**Error**: `Audio test failed - MP3 files not found`

**Solution**:
```bash
# Run the quick setup script
chmod +x quick_setup_pi.sh
./quick_setup_pi.sh
```

### 5. MQTT Connection Issues

**Error**: `MQTT client disconnected (code: 7)`

**Solutions**:
```bash
# Check internet connection
ping 103.87.67.139

# Check MQTT broker status
mosquitto_pub -h 103.87.67.139 -t "test/topic" -m "test message"

# If using local MQTT broker
sudo systemctl status mosquitto
sudo systemctl start mosquitto
```

## 🧪 Testing Steps

### Step 1: Run System Tests
```bash
python3 test_system.py
```

This will test:
- GPIO functionality
- Audio system
- Fingerprint sensor
- MQTT connection
- Audio file generation

### Step 2: Run Simple System
```bash
python3 whac_simple_system.py
```

This runs a simplified version that handles errors gracefully.

### Step 3: Run Full System
```bash
python3 whac_integrated_system.py
```

This runs the complete integrated system.

## 🔧 Manual Setup

If the automated setup fails, follow these manual steps:

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install -y espeak espeak-data ffmpeg mpg123 alsa-utils
pip3 install pygame
```

### 2. Create Audio Directory
```bash
mkdir -p whac_audio
cd whac_audio
```

### 3. Generate Audio Files
```bash
# Generate WAV files
espeak -s 150 -v en -w access_granted.wav "Access granted. Welcome to the warehouse."
espeak -s 150 -v en -w access_denied.wav "Access denied. Please contact your supervisor."
espeak -s 150 -v en -w violation_alert.wav "Security violation detected. Please contact supervisor immediately."

# Convert to MP3
ffmpeg -i access_granted.wav -acodec mp3 -ab 128k -y access_granted.mp3
ffmpeg -i access_denied.wav -acodec mp3 -ab 128k -y access_denied.mp3
ffmpeg -i violation_alert.wav -acodec mp3 -ab 128k -y violation_alert.mp3

# Clean up WAV files
rm *.wav
```

### 4. Set Permissions
```bash
chmod -R 755 whac_audio
```

## 🎯 UAT Testing Without Hardware

If you don't have the fingerprint sensor or GPIO button connected, you can still test the system:

### 1. Test MP3 Notifications
```bash
# Send test notification via MQTT
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/notification" -m '{"type":"violation","message":"Test violation","user_id":"test_user"}'
```

### 2. Test Exit Button (Simulated)
```bash
# Send test exit request via MQTT
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/exit" -m '{"action":"exit_request","timestamp":"2025-01-01T00:00:00","source":"test","store_id":"Store001"}'
```

### 3. Test User Commands
```bash
# Send test user command via MQTT
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/command" -m '{"user_id":"test_user","command_type":"user_instruction","instruction":"turn_around","timestamp":"2025-01-01T00:00:00"}'
```

## 📊 System Status Check

### Check Running Processes
```bash
ps aux | grep python
```

### Check Log Files
```bash
tail -f whac_simple_system.log
tail -f whac_integrated_system.log
```

### Check Audio Files
```bash
ls -la whac_audio/
```

### Check GPIO Status
```bash
# Check if GPIO is accessible
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
```

## 🔄 Restart Services

If the system becomes unresponsive:

```bash
# Kill all Python processes
sudo pkill -f python

# Restart MQTT broker (if using local)
sudo systemctl restart mosquitto

# Restart the system
python3 whac_simple_system.py
```

## 📞 Getting Help

If you're still having issues:

1. **Check the logs**: Look at the log files for specific error messages
2. **Run tests**: Use `python3 test_system.py` to identify which components are failing
3. **Check hardware**: Ensure all hardware connections are secure
4. **Verify permissions**: Make sure the user has proper permissions for GPIO and audio

## 🎉 Success Indicators

The system is working correctly when you see:

- ✅ All components initialized successfully
- ✅ MQTT connections established
- ✅ Audio files generated and playable
- ✅ No repeated error messages in logs
- ✅ System status shows all components as "Active"

---

**Note**: The system is designed to be resilient and will continue working even if some components fail. The most important components for UAT are the MP3 notification system and MQTT communication.



