# Troubleshooting: Simulator Tidak Terkoneksi ke Web UI

## 🐛 Problem: Web UI tidak menerima scan dari simulator

### Penyebab Umum:

1. ❌ **MQTT Topic Salah** (FIXED!)
2. ❌ **MQTT Broker tidak running**
3. ❌ **IP/Port broker salah**
4. ❌ **Web UI tidak subscribe ke topic**
5. ❌ **Firewall blocking**

---

## ✅ Solution: Update Simulator (v1.1)

### Yang Sudah Diperbaiki:

#### 1. Topic Configuration
```python
# ❌ OLD (Wrong topic)
MQTT_TOPIC = "whac/fingerprint/scan"

# ✅ NEW (Correct topic)
MQTT_SCAN_TOPIC = "WHAC/Store001/in"
```

#### 2. MQTT Broker Configuration
```python
# ✅ Updated to match Web UI
MQTT_BROKER = "103.87.67.139"  # Remote broker (default)
# Or use "localhost" if running locally
```

#### 3. Better Error Handling
- ✅ Connection testing before scan
- ✅ Better error messages
- ✅ Callback functions for debugging
- ✅ QoS = 1 for reliable delivery

---

## 🚀 Quick Fix Steps

### Step 1: Update Simulator (Already Done)

Script sudah diupdate dengan konfigurasi yang benar.

### Step 2: Check MQTT Broker

#### Option A: Using Local Broker (Recommended for Testing)

```bash
# Install Mosquitto (if not installed)
sudo apt-get install mosquitto mosquitto-clients

# Start Mosquitto
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Test broker
mosquitto_pub -h localhost -t test -m "hello"
```

#### Option B: Using Remote Broker (Production)

Remote broker sudah configured di Web UI: `103.87.67.139:1883`

Update simulator jika perlu:
```python
# Edit simulate_scan.py line 13
MQTT_BROKER = "103.87.67.139"  # Remote broker
# Or
MQTT_BROKER = "localhost"  # Local broker
```

### Step 3: Verify Web UI MQTT Connection

Check di Web UI logs:

```bash
# Jika running manual
# Lihat console output untuk MQTT connection messages

# Jika using systemd
sudo journalctl -u whac-web-ui -f | grep MQTT
```

Expected output:
```
✅ MQTT client setup complete
✅ Connected to MQTT broker
✅ Subscribed to WHAC/Store001/in
```

### Step 4: Test Simulator

```bash
python3 web_ui/simulate_scan.py
```

Expected output:
```
✅ Connected to MQTT broker successfully!
✅ Message 1 published successfully!
💡 Check Web UI dashboard - modal should pop up!
```

---

## 🧪 Manual Testing

### Test 1: Verify MQTT Topic

```bash
# Terminal 1: Subscribe to topic
mosquitto_sub -h localhost -t "WHAC/Store001/in" -v

# Terminal 2: Publish test message
mosquitto_pub -h localhost -t "WHAC/Store001/in" -m '{"user_id": 1, "device_id": "AS608_001", "status": "Match"}'

# Terminal 1 should show the message
```

### Test 2: Check Web UI Subscription

```bash
# In Web UI code, verify subscription
grep -n "subscribe" web_ui/app.py

# Should show:
# mqtt_client.subscribe(MQTT_SCAN_TOPIC)
```

### Test 3: Test with Mosquitto Clients

```bash
# Publish a scan manually
mosquitto_pub -h localhost -t "WHAC/Store001/in" -m '{
  "store_id": "Store001",
  "timestamp": "2025-01-02T12:00:00",
  "status": "Match",
  "fingerprint_id": 1,
  "user_id": 1,
  "device_id": "AS608_001",
  "confidence": 95,
  "sensor_location": "masuk"
}'
```

If this works but simulator doesn't, it's a Python MQTT client issue.

---

## 🔍 Diagnostic Commands

### Check MQTT Broker Status

```bash
# Check if Mosquitto is running
sudo systemctl status mosquitto

# Check port 1883 is listening
sudo netstat -tulpn | grep 1883

# Check Mosquitto logs
sudo tail -f /var/log/mosquitto/mosquitto.log
```

### Test Network Connectivity

```bash
# Test if broker is reachable
telnet localhost 1883
# Or
nc -zv localhost 1883

# Test remote broker
telnet 103.87.67.139 1883
```

### Check Firewall

```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 1883/tcp

# CentOS/RHEL
sudo firewall-cmd --list-all
sudo firewall-cmd --add-port=1883/tcp --permanent
sudo firewall-cmd --reload
```

---

## 🛠️ Configuration Guide

### If Using Local Broker

**File: `simulate_scan.py`**
```python
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_SCAN_TOPIC = "WHAC/Store001/in"
```

**File: `web_ui/app.py`** (check existing config)
```python
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_SCAN_TOPIC = os.getenv('MQTT_SCAN_TOPIC', 'WHAC/Store001/in')
```

### If Using Remote Broker

**File: `simulate_scan.py`**
```python
MQTT_BROKER = "103.87.67.139"  # Your remote broker IP
MQTT_PORT = 1883
MQTT_SCAN_TOPIC = "WHAC/Store001/in"
```

### Using Environment Variables (Recommended)

Create `.env` file in `web_ui/` folder:
```bash
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_SCAN_TOPIC=WHAC/Store001/in
```

Then update simulator to read from env:
```python
import os
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_SCAN_TOPIC = os.getenv('MQTT_SCAN_TOPIC', 'WHAC/Store001/in')
```

---

## 📊 Verification Checklist

- [ ] Mosquitto service running
- [ ] Port 1883 listening
- [ ] Web UI connected to MQTT broker
- [ ] Simulator using correct topic: `WHAC/Store001/in`
- [ ] Simulator using correct broker IP
- [ ] Firewall allows port 1883
- [ ] Test with `mosquitto_pub` works
- [ ] Simulator connection test passes
- [ ] Web UI logs show incoming messages

---

## 🔧 Common Issues & Solutions

### Issue 1: "Connection Refused"

**Cause:** MQTT broker not running

**Solution:**
```bash
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### Issue 2: "Connection Timeout"

**Cause:** Wrong IP or firewall blocking

**Solution:**
```bash
# Test connectivity
ping <MQTT_BROKER_IP>
telnet <MQTT_BROKER_IP> 1883

# Allow in firewall
sudo ufw allow from <YOUR_IP> to any port 1883
```

### Issue 3: "Message Published but Web UI No Response"

**Cause:** Topic mismatch

**Solution:**
```bash
# Check Web UI subscribed topics
grep "subscribe" web_ui/app.py

# Check simulator publish topic
grep "MQTT_SCAN_TOPIC" web_ui/simulate_scan.py

# Should be: WHAC/Store001/in
```

### Issue 4: "Cannot Import paho.mqtt"

**Cause:** Library not installed

**Solution:**
```bash
pip install paho-mqtt
# Or
pip3 install paho-mqtt
```

---

## 📱 Quick Test Script

Save as `test_mqtt.py`:

```python
#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time

BROKER = "localhost"
PORT = 1883
TOPIC = "WHAC/Store001/in"

def on_connect(client, userdata, flags, rc):
    print(f"Connected: {rc}")
    client.subscribe(TOPIC)
    print(f"Subscribed to: {TOPIC}")

def on_message(client, userdata, msg):
    print(f"Received: {msg.topic} -> {msg.payload.decode()}")

# Subscriber
sub = mqtt.Client("subscriber")
sub.on_connect = on_connect
sub.on_message = on_message
sub.connect(BROKER, PORT)
sub.loop_start()

time.sleep(1)

# Publisher
pub = mqtt.Client("publisher")
pub.connect(BROKER, PORT)
pub.publish(TOPIC, "TEST MESSAGE")
print(f"Published to: {TOPIC}")
pub.disconnect()

time.sleep(2)
sub.loop_stop()
sub.disconnect()
```

Run:
```bash
python3 test_mqtt.py
```

Expected output:
```
Connected: 0
Subscribed to: WHAC/Store001/in
Published to: WHAC/Store001/in
Received: WHAC/Store001/in -> TEST MESSAGE
```

---

## 💡 Best Practices

1. **Use Local Broker for Development**
   - Faster
   - No network issues
   - Easier debugging

2. **Use Environment Variables**
   - Easy to switch between local/remote
   - No code changes needed
   - Secure credentials

3. **Test Connection Before Publishing**
   - Simulator now does this automatically
   - Prevents silent failures

4. **Check Logs**
   - Web UI logs: `tail -f app.log`
   - Mosquitto logs: `tail -f /var/log/mosquitto/mosquitto.log`
   - Simulator output: Already verbose

---

## 📞 Still Not Working?

### Debug Mode

Enable verbose logging in simulator (already enabled in v1.1):
- Connection callbacks
- Publish status
- Payload display

### Capture MQTT Traffic

```bash
# Monitor all MQTT messages
mosquitto_sub -h localhost -t "#" -v

# Monitor specific topic
mosquitto_sub -h localhost -t "WHAC/Store001/in" -v
```

### Check Web UI Code

Verify MQTT subscription in `app.py`:
```python
# Search for subscription code
grep -A 10 "mqtt_client.subscribe" web_ui/app.py
```

### Contact Support

Provide this information:
1. Simulator output (full)
2. Web UI logs
3. MQTT broker logs
4. Network topology (local/remote)
5. Firewall status

---

**Updated:** 2025-01-02  
**Version:** 1.1  
**Status:** ✅ Fixed and Tested



