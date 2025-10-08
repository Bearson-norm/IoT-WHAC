# Bridge Testing Guide
## Testing Connection Between Fingerprint Scanner and Web UI

## Architecture Overview

```
┌─────────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Fingerprint        │         │   MQTT Broker   │         │    Web UI       │
│  Scanner Client     │ ──pub──>│  103.87.67.139  │<──sub── │   (Flask)       │
│  (local_machine)    │         │  Port: 1883     │         │   + SocketIO    │
│                     │         │                 │         │                 │
│  Topic:             │         │  Topic:         │         │  Emits to:      │
│  WHAC/Store001/in   │         │  WHAC/Store001/ │         │  Browser via    │
└─────────────────────┘         │     in/action   │         │  WebSocket      │
                                └─────────────────┘         └─────────────────┘
                                                                     │
                                                                     v
                                                            ┌─────────────────┐
                                                            │   Web Browser   │
                                                            │   Modal Popup   │
                                                            └─────────────────┘
```

## Quick Diagnosis

### Step 1: Test MQTT Broker Connection
```bash
python test_mqtt_bridge.py
```

**Expected output:**
```
✅ Successfully connected to MQTT broker!
✅ Subscribed successfully
✅ Test message published successfully!
📥 Received message on topic: WHAC/Store001/in
```

**If it fails:**
- Check if MQTT broker at `103.87.67.139` is accessible
- Check firewall settings
- Try pinging the broker: `ping 103.87.67.139`

---

### Step 2: Simulate a Fingerprint Scan
Keep the web UI running, then in another terminal:

```bash
python simulate_fingerprint_scan.py
```

**Choose scenario 1** (Successful Match)

**Expected behavior:**
1. ✅ Message published in simulator terminal
2. ✅ Web UI terminal shows: "Received scan notification"
3. ✅ Web UI terminal shows: "✓ Scan notification emitted to WebSocket"
4. ✅ **Browser shows POPUP MODAL** with user info

**If modal doesn't show:**
- Open browser console (F12)
- Look for: `🔔 Received scan notification:`
- Check for JavaScript errors

---

### Step 3: Test with Real Fingerprint Scanner

#### On Raspberry Pi (or device with fingerprint scanner):

```bash
cd local_machine
python fingerprint_simple_client.py
```

**Expected startup output:**
```
✓ GPIO setup complete - Relay on pin 18
✓ Fingerprint sensor initialized
✓ Connected to MQTT broker
✓ Subscribed to WHAC/Store001/action
Waiting for finger...
```

**When you scan a finger:**
```
Found fingerprint with ID #1, confidence: 95
✓ Scan result sent: Match - ID: 1 (John Doe)
```

#### In Web UI terminal, you should see:
```
Received scan notification: {'store_id': 'Store001', ...}
✓ Scan notification emitted to WebSocket
```

#### In Browser:
- **Popup modal appears** with user information
- Grant or Deny buttons work

---

## Common Issues and Solutions

### Issue 1: "Cannot connect to MQTT broker"

**Symptoms:**
```
❌ Failed to connect to MQTT broker (rc: 3)
Error: Connection refused - server unavailable
```

**Solutions:**
1. Check if MQTT broker is running:
   ```bash
   # If broker is on same machine
   sudo systemctl status mosquitto
   ```

2. Check broker address in config files:
   - `local_machine/config.py` - line 10
   - `web_ui/app.py` - line 39

3. Test with mosquitto clients:
   ```bash
   # Subscribe
   mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/in"
   
   # Publish
   mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/in" -m "test"
   ```

---

### Issue 2: "Web UI doesn't receive messages"

**Symptoms:**
- Fingerprint client sends messages
- `test_mqtt_bridge.py` receives messages
- Web UI doesn't show any logs

**Solutions:**

1. Check if web UI MQTT client is initialized:
   Look for this in web UI startup logs:
   ```
   ✓ MQTT client connected for real-time notifications
   Subscribed to WHAC/Store001/in
   ```

2. Restart web UI:
   ```bash
   cd web_ui
   # Press Ctrl+C to stop
   python app.py
   ```

3. Check web UI app.py line 63-64:
   ```python
   mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
   mqtt_client.loop_start()
   ```

---

### Issue 3: "Modal doesn't show in browser"

**Symptoms:**
- Web UI receives MQTT message (✅ in logs)
- Web UI emits to WebSocket (✅ in logs)
- Browser doesn't show modal

**Solutions:**

1. **Check browser console (F12):**
   Look for:
   ```
   ✅ Connected to WebSocket server
   🔔 Received scan notification:
   📺 Showing modal...
   ✅ Modal shown successfully!
   ```

2. **If "WebSocket Disconnected":**
   - Refresh the page
   - Check if SocketIO is working:
     ```bash
     # In browser console
     socket.connected  // Should return: true
     ```

3. **Test WebSocket directly:**
   Visit: `http://localhost:5000/simulate_scan`
   
   This bypasses MQTT and directly emits to WebSocket.

4. **Use Test Button:**
   Click the yellow "Test Modal" button in navbar

5. **Clear browser cache:**
   - Ctrl+Shift+Delete (Windows/Linux)
   - Cmd+Shift+Delete (Mac)
   - Select "Cached files"
   - Hard refresh: Ctrl+F5 or Cmd+Shift+R

---

### Issue 4: "Fingerprint scanner not detected"

**Symptoms:**
```
❌ Fingerprint sensor not found
```

**Solutions:**

1. Check if sensor is connected:
   ```bash
   ls /dev/ttyUSB* /dev/serial*
   ```

2. Check permissions:
   ```bash
   sudo usermod -a -G dialout $USER
   sudo chmod 666 /dev/ttyUSB0  # or your port
   ```

3. Test sensor with simple script:
   ```bash
   cd local_machine
   python -c "import serial; s = serial.Serial('/dev/ttyUSB0', 57600); print('OK')"
   ```

---

## Testing Checklist

### Pre-requisites
- [ ] MQTT broker is accessible at 103.87.67.139:1883
- [ ] Web UI is running (`python web_ui/app.py`)
- [ ] Browser has web UI open at http://localhost:5000
- [ ] Browser console is open (F12)

### Basic Tests
- [ ] `test_mqtt_bridge.py` connects successfully
- [ ] `simulate_fingerprint_scan.py` publishes successfully
- [ ] Web UI logs show "Received scan notification"
- [ ] Browser console shows "Received scan notification"
- [ ] **Modal popup appears in browser**

### Integration Tests
- [ ] Fingerprint client connects to MQTT
- [ ] Scan a fingerprint
- [ ] Web UI receives the scan
- [ ] Modal appears with correct user info
- [ ] "Grant Access" button works
- [ ] "Deny Access" button works
- [ ] Relay activates (if connected)

### Advanced Tests
- [ ] Multiple scans in quick succession
- [ ] Unknown fingerprint (no match)
- [ ] Browser refresh keeps WebSocket connected
- [ ] Multiple browsers show modal simultaneously

---

## Debug Logs to Collect

If issues persist, collect these logs:

### 1. Fingerprint Client Logs
```bash
cd local_machine
python fingerprint_simple_client.py 2>&1 | tee fingerprint_debug.log
# Scan a finger, then Ctrl+C
cat fingerprint_debug.log
```

### 2. Web UI Logs
```bash
cd web_ui
python app.py 2>&1 | tee webui_debug.log
# Scan a finger or simulate, then Ctrl+C
cat webui_debug.log
```

### 3. Browser Console Logs
1. Open browser console (F12)
2. Go to Console tab
3. Scan a finger or simulate
4. Right-click in console → "Save as..."

### 4. MQTT Diagnostic Logs
```bash
python test_mqtt_bridge.py 2>&1 | tee mqtt_debug.log
# Let it run for 30 seconds
# In another terminal, simulate a scan
# Ctrl+C
cat mqtt_debug.log
```

---

## Configuration Files to Check

### 1. `local_machine/config.py`
```python
MQTT_BROKER = "103.87.67.139"  # Should match web UI
MQTT_PORT = 1883
MQTT_TOPIC = "WHAC/Store001/in"  # Should match web UI
```

### 2. `web_ui/app.py` (lines 39-42)
```python
MQTT_BROKER = "103.87.67.139"  # Should match fingerprint client
MQTT_PORT = 1883
MQTT_ACTION_TOPIC = "WHAC/Store001/action"
MQTT_SCAN_TOPIC = "WHAC/Store001/in"  # Should match fingerprint client
```

### 3. Both should use same broker and topics!

---

## Quick Fix Commands

### Restart Everything
```bash
# Terminal 1: Web UI
cd web_ui
python app.py

# Terminal 2: Fingerprint Client (on Pi)
cd local_machine
python fingerprint_simple_client.py

# Terminal 3: Test
python simulate_fingerprint_scan.py
```

### Test End-to-End in 30 Seconds
```bash
# 1. Start web UI
cd web_ui && python app.py &

# 2. Wait 3 seconds
sleep 3

# 3. Open browser
# Go to http://localhost:5000
# Login if needed

# 4. Simulate scan
python simulate_fingerprint_scan.py
# Choose option 1

# Expected: Modal pops up! ✅
```

---

## Need More Help?

Run the diagnostic tool and share the output:
```bash
python test_mqtt_bridge.py > diagnostic_output.txt 2>&1
```

Check these files for errors:
- `local_machine/fingerprint_mqtt.log`
- `web_ui/` (check terminal output)
- Browser console (F12 → Console tab)


