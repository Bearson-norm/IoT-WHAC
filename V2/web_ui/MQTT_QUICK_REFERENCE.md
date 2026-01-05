# Quick Reference: MQTT Configuration

## 🎯 Configuration Summary

| Component | Setting | Value |
|-----------|---------|-------|
| **MQTT Broker** | IP Address | `103.87.67.139` (remote) or `localhost` (local) |
| **MQTT Port** | Port | `1883` |
| **Scan Topic** | Topic | `WHAC/Store001/in` |
| **Action Topic** | Topic | `WHAC/Store001/action` |

---

## ⚙️ Simulator Configuration (Fixed!)

**Before (Wrong):**
```python
MQTT_BROKER = "localhost"
MQTT_TOPIC = "whac/fingerprint/scan"  # ❌ Wrong!
```

**After (Correct):**
```python
MQTT_BROKER = "103.87.67.139"  # Or "localhost"
MQTT_SCAN_TOPIC = "WHAC/Store001/in"  # ✅ Correct!
```

---

## 🚀 Quick Commands

### Start Simulator
```bash
cd web_ui
python3 simulate_scan.py
```

### Test MQTT Connection
```bash
# Subscribe to topic
mosquitto_sub -h localhost -t "WHAC/Store001/in" -v

# Publish test message
mosquitto_pub -h localhost -t "WHAC/Store001/in" -m "test"
```

### Check Services
```bash
# MQTT Broker
sudo systemctl status mosquitto

# Web UI (if using systemd)
sudo systemctl status whac-web-ui
```

---

## 🔍 Troubleshooting Quick Checks

```bash
# 1. Is broker running?
sudo systemctl status mosquitto

# 2. Is port listening?
sudo netstat -tulpn | grep 1883

# 3. Can reach broker?
telnet localhost 1883

# 4. Test with mosquitto client?
mosquitto_pub -h localhost -t test -m hello
```

---

## 📋 Expected Flow

```
Simulator → MQTT Broker → Web UI → Modal Popup

1. Simulator publishes to "WHAC/Store001/in"
2. MQTT Broker receives message
3. Web UI (subscribed) receives message
4. Web UI emits SocketIO event
5. Browser shows modal popup
```

---

## ✅ Verification

After running simulator, you should see:

### In Simulator:
```
✅ Connected to MQTT broker successfully!
✅ Message published successfully!
💡 Check Web UI dashboard - modal should pop up!
```

### In Web UI (console/logs):
```
📡 Received scan from MQTT
👤 User ID: 1
📍 Device: AS608_001
```

### In Browser:
```
🎉 Modal popup appears with scan details
```

---

## 📞 Need Help?

See full documentation:
- `TROUBLESHOOTING_SIMULATOR.md` - Complete troubleshooting guide
- `FITUR_FULL_NAME_LINKING.md` - Feature documentation
- `QUICK_START_FIX.md` - Quick start guide

---

**Last Updated:** 2025-01-02 v1.1



