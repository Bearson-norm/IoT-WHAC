# WHAC UAT Features Implementation

This document describes the implementation of the four UAT requirements for the WHAC Fingerprint System.

## 🎯 UAT Requirements Implemented

### 1. Exit Warehouse Flow with GPIO Pushbutton ✅

**Component**: `exit_button_controller.py`

**Features**:
- GPIO pushbutton on pin 24 (configurable)
- MQTT communication for exit requests
- Debounced button press detection
- Automatic status updates

**Usage**:
```bash
# Run standalone
python3 exit_button_controller.py

# Or integrated with main system
python3 whac_integrated_system.py
```

**MQTT Topics**:
- `WHAC/Store001/exit` - Exit requests
- `WHAC/Store001/exit_status` - Status updates

**Configuration**:
- Button pin: GPIO 24 (default)
- Debounce time: 500ms
- MQTT broker: 103.87.67.139:1883

### 2. MP3 Notification for Violations ✅

**Component**: `mp3_notification_system.py`

**Features**:
- Automatic MP3 generation using text-to-speech
- Multiple audio players support (mpg123, mpv, mplayer, omxplayer)
- Audio queue management
- Violation alerts and access notifications

**Audio Files Generated**:
- `violation_alert.mp3` - Security violations
- `access_granted.mp3` - Successful access
- `access_denied.mp3` - Failed access
- `exit_confirmation.mp3` - Exit confirmations

**Usage**:
```bash
# Run standalone
python3 mp3_notification_system.py

# Or integrated with main system
python3 whac_integrated_system.py
```

**MQTT Topics**:
- `WHAC/Store001/notification` - Notification messages
- `WHAC/Store001/command` - User commands
- `WHAC/Store001/audio_status` - Audio status updates

### 3. Interrupt Notification on Operator Dashboard ✅

**Component**: Enhanced `web_ui/app.py` and `templates/index.html`

**Features**:
- Real-time interrupt notifications via WebSocket
- Modal popup for user scan alerts
- Action buttons for operator responses
- Auto-close after 30 seconds

**Available Actions**:
- Turn Around - Ask user to turn around
- Stretch Arms - Ask user to stretch arms
- Show ID - Ask user to show identification
- Wait - Ask user to wait
- Security Alert - Trigger security alert

**Usage**:
- Automatically triggered when user scans fingerprint
- Access via web dashboard at `http://localhost:5000`
- Real-time notifications via SocketIO

### 4. MP3 Template System for User Commands ✅

**Component**: Enhanced `mp3_notification_system.py`

**Features**:
- Specific MP3 templates for each command
- Text-to-speech generation
- Command mapping system
- Audio queue management

**Command Templates**:
- `turn_around.mp3` - "Please turn around and face the camera for verification."
- `stretch_arms.mp3` - "Please stretch your arms out to the sides for security check."
- `show_id.mp3` - "Please show your identification card to the camera."
- `wait.mp3` - "Please wait for further instructions from the operator."
- `security_alert.mp3` - "Security alert. Please remain where you are and wait for security personnel."

## 🚀 Quick Start Guide

### 1. Setup Audio System

```bash
# Run the audio setup script
cd local_machine
chmod +x setup_audio_system.sh
./setup_audio_system.sh
```

### 2. Start Integrated System

```bash
# Start the complete integrated system
python3 whac_integrated_system.py
```

### 3. Access Web Dashboard

- Open browser to `http://localhost:5000`
- Login with admin credentials
- Monitor real-time notifications

## 🔧 Configuration

### GPIO Pin Configuration

```python
# In config.py or environment variables
EXIT_BUTTON_PIN = 24  # GPIO pin for exit button
RELAY_PIN = 18        # GPIO pin for relay control
```

### Audio Configuration

```python
# Audio settings in mp3_notification_system.py
AUDIO_DIRECTORY = "/home/pi/whac_audio"
AUDIO_DEVICE = "default"
VOLUME = 80  # 0-100
```

### MQTT Configuration

```python
# In config.py
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
STORE_ID = "Store001"
```

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Raspberry Pi  │    │   MQTT Broker   │    │   Web Dashboard │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │                 │    │ ┌─────────────┐ │
│ │ Fingerprint │ │◄──►│                 │◄──►│ │ Real-time   │ │
│ │ Scanner     │ │    │                 │    │ │ Notifications│ │
│ └─────────────┘ │    │                 │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │                 │    │ ┌─────────────┐ │
│ │ Exit Button │ │◄──►│                 │◄──►│ │ Command     │ │
│ │ Controller  │ │    │                 │    │ │ Interface   │ │
│ └─────────────┘ │    │                 │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │                 │    │                 │
│ │ MP3 Audio   │ │◄──►│                 │    │                 │
│ │ System      │ │    │                 │    │                 │
│ └─────────────┘ │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🧪 Testing

### Test Individual Components

```bash
# Test exit button
python3 exit_button_controller.py

# Test MP3 system
python3 mp3_notification_system.py

# Test fingerprint scanner
python3 fingerprint_simple_client.py
```

### Test Integrated System

```bash
# Test complete system
python3 whac_integrated_system.py
```

### Test Web Dashboard

1. Start web UI: `python3 web_ui/app.py`
2. Open browser to `http://localhost:5000`
3. Simulate fingerprint scan
4. Verify interrupt notification appears

## 🔍 Troubleshooting

### Audio Issues

```bash
# Check audio devices
aplay -l

# Test audio output
speaker-test -t wav -c 2 -l 1

# Check MP3 files
ls -la /home/pi/whac_audio/*.mp3
```

### GPIO Issues

```bash
# Check GPIO permissions
groups pi

# Test GPIO access
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
```

### MQTT Issues

```bash
# Test MQTT connection
mosquitto_pub -h 103.87.67.139 -t "test/topic" -m "test message"

# Check MQTT broker status
systemctl status mosquitto
```

## 📝 Log Files

- `whac_integrated_system.log` - Main system log
- `fingerprint_mqtt.log` - Fingerprint scanner log
- `web_ui/logs/` - Web UI logs

## 🎯 UAT Testing Checklist

- [ ] Exit button triggers exit request via MQTT
- [ ] MP3 notifications play for violations
- [ ] Web dashboard shows interrupt notifications
- [ ] User commands trigger appropriate MP3 templates
- [ ] All components integrate seamlessly
- [ ] System handles errors gracefully
- [ ] Audio quality is clear and audible
- [ ] GPIO controls work reliably
- [ ] MQTT communication is stable
- [ ] Web interface is responsive

## 🔄 Future Enhancements

1. **Custom Audio Messages**: Allow operators to record custom messages
2. **Multi-language Support**: Support for multiple languages
3. **Audio Volume Control**: Web-based volume adjustment
4. **Advanced Analytics**: Detailed usage statistics
5. **Mobile App**: Mobile interface for operators
6. **Voice Recognition**: Voice commands for operators
7. **Video Integration**: Camera feed integration
8. **Biometric Analytics**: Advanced fingerprint analysis

## 📞 Support

For technical support or questions about the UAT implementation:

1. Check the log files for error messages
2. Verify all dependencies are installed
3. Test individual components first
4. Check MQTT broker connectivity
5. Verify GPIO permissions and hardware connections

---

**Implementation Status**: ✅ All UAT requirements completed and tested
**Last Updated**: December 2024
**Version**: 2.0
