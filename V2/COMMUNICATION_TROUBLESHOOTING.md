# WHAC System Communication Troubleshooting Guide

## Issue: Popup Modal Not Appearing from Incoming Fingerprint Scan Data

### Problem Overview
When a fingerprint scan is performed on the local machine, the data should flow through MQTT to both the server processor and the web UI, which should then display a popup modal for access control. If the modal doesn't appear, follow this troubleshooting guide.

---

## Root Cause Identified ✅

**MQTT Client ID Conflict**: Both the server processor (`mqtt_data_processor.py`) and the web UI (`app.py`) were connecting to the MQTT broker **without unique client IDs**. When two MQTT clients connect with the same (or no) client ID, the broker disconnects the first client when the second connects.

### Solution Applied
Added unique client IDs to both MQTT clients:
- **Server processor**: `whac_server_processor`
- **Web UI**: `whac_web_ui`

---

## Testing Steps

### 1. Restart All Components

Stop any running processes and restart the system:

```bash
# Stop all components (Ctrl+C if running)

# Start server and web UI
python start_system.py

# In a separate terminal, start the local machine client
cd local_machine/
python3 fingerprint_simple_client.py
```

### 2. Check MQTT Connections

**Server Processor Logs:**
Look for these messages in the server output:
```
✅ Server processor MQTT client connected successfully
✅ Server processor subscribed to topic: WHAC/Store001/in (QoS 1)
🔔 Server processor is now listening for scan data...
```

**Web UI Logs:**
Look for these messages in the web UI output:
```
✅ Web UI MQTT client connected successfully
✅ Web UI subscribed to topic: WHAC/Store001/in (QoS 1)
🔔 Web UI is now listening for scan notifications...
```

**Local Machine Logs:**
Look for these messages:
```
✓ MQTT broker connected successfully!
✓ Subscribed to command topics:
  - WHAC/Store001/add_user
  - WHAC/Store001/import
  - WHAC/Store001/export
  - WHAC/Store001/action
```

### 3. Test WebSocket Connection

1. Open the web UI in your browser: http://localhost:5000
2. Login with your credentials
3. Open browser console (F12)
4. Look for WebSocket connection messages:
   ```
   ✅ Connected to WebSocket server
   ```

### 4. Use Diagnostic Buttons

The web UI now has diagnostic buttons in the top navigation bar:

1. **Test Modal** - Tests if the modal popup works (bypasses MQTT/WebSocket)
2. **MQTT Status** - Checks if MQTT client is connected
3. **Simulate Scan** - Simulates a complete data flow through MQTT and WebSocket

**Test in this order:**

1. Click **"Test Modal"** → Modal should appear immediately
   - ✅ If it works: Modal and browser-side code are working
   - ❌ If it doesn't: Browser console will show errors

2. Click **"MQTT Status"** → Shows connection status
   - ✅ Should show "Connected: Yes"
   - ❌ If "Connected: No": Check web UI logs

3. Click **"Simulate Scan"** → Should trigger modal
   - ✅ If modal appears: Full pipeline is working
   - ❌ If not: Check logs below

### 5. Perform Real Fingerprint Scan

With all components running:

1. Place a registered finger on the sensor
2. Watch the logs in all three terminals

**Expected Log Flow:**

**Local Machine:**
```
✓ Match found! ID: 1, Confidence: 95
✓ Scan result sent: Match - ID: 1 (Test User)
```

**Server Processor:**
```
================================================================================
📨 Server processor received MQTT message on topic: WHAC/Store001/in
📦 Raw payload: {"store_id": "Store001", "timestamp": "...", ...}
📋 Parsed JSON payload: {...}
✓ Processed scan: scan_detected for user 1 (Test User)
================================================================================
```

**Web UI:**
```
================================================================================
📨 Web UI received MQTT message on topic: WHAC/Store001/in
📦 Raw payload: {"store_id": "Store001", "timestamp": "...", ...}
📋 Parsed JSON payload: {...}
🔄 Formatted scan data for WebSocket: {...}
🚀 Attempting to emit 'scan_notification' event to all WebSocket clients...
✅ SUCCESS: Scan notification emitted to WebSocket!
================================================================================
```

**Browser Console:**
```
🔔 Received scan notification: {user_id: 1, status: "Match", ...}
📊 Data type: object
📊 Data keys: (7) ['user_id', 'status', 'username', ...]
🔔 showScanNotification called with data: {...}
👤 User info: Test User (ID: 1)
📺 Showing modal...
✅ Modal shown successfully!
```

---

## Common Issues & Solutions

### Issue 1: MQTT Client Not Connected

**Symptoms:**
- "MQTT Status" shows "Connected: No"
- No MQTT messages in logs

**Solutions:**
1. Check MQTT broker is running:
   ```bash
   # On the MQTT broker server
   sudo systemctl status mosquitto
   ```

2. Check firewall settings:
   ```bash
   # Allow MQTT port
   sudo ufw allow 1883/tcp
   ```

3. Verify MQTT broker IP in config:
   ```python
   # local_machine/config.py
   MQTT_BROKER = "103.87.67.139"  # Should be accessible
   ```

4. Test MQTT connection manually:
   ```bash
   # Install mosquitto clients
   sudo apt-get install mosquitto-clients
   
   # Subscribe to topic
   mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/in" -v
   
   # In another terminal, publish test message
   mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/in" -m '{"test": "message"}'
   ```

### Issue 2: WebSocket Not Connecting

**Symptoms:**
- Browser console shows "WebSocket disconnected"
- No scan notifications reaching browser

**Solutions:**
1. Check Flask-SocketIO is installed:
   ```bash
   pip install flask-socketio python-socketio
   ```

2. Verify SocketIO is running:
   - Look for this in web UI startup logs:
   ```
   * Restarting with stat
   * Debugger is active!
   * Running on http://0.0.0.0:5000
   ```

3. Check browser console for errors:
   - Press F12 → Console tab
   - Look for connection errors

4. Try different SocketIO transport:
   ```javascript
   // In index.html, modify socket initialization
   socket = io({transports: ['polling', 'websocket']});
   ```

### Issue 3: Modal Not Appearing

**Symptoms:**
- Data reaches browser (console logs show it)
- But modal doesn't pop up

**Solutions:**
1. Check browser console for JavaScript errors

2. Verify Bootstrap is loaded:
   ```javascript
   // In browser console
   typeof bootstrap !== 'undefined'  // Should return true
   ```

3. Check if modal HTML exists:
   ```javascript
   // In browser console
   document.getElementById('scanNotificationModal')  // Should return element
   ```

4. Try manual modal test:
   ```javascript
   // In browser console
   testScanNotification()
   ```

### Issue 4: Data Not Leaving Local Machine

**Symptoms:**
- Local machine shows "Match found"
- But no data in server or web UI logs

**Solutions:**
1. Check local machine MQTT connection:
   - Look for "✓ MQTT broker connected successfully!"

2. Verify scan is being sent:
   - Look for "✓ Scan result sent: Match - ID: X"

3. Check topic name matches:
   ```python
   # local_machine/config.py
   MQTT_TOPIC = "WHAC/Store001/in"  # Must match server/web UI
   ```

4. Increase log level for debugging:
   ```python
   # local_machine/config.py
   LOG_LEVEL = "DEBUG"
   ```

### Issue 5: Both Server and Web UI Not Receiving

**Symptoms:**
- Local machine sends data
- Neither server nor web UI receives it

**Solutions:**
1. Check if multiple clients with same ID exist:
   ```bash
   # On MQTT broker server, check connected clients
   mosquitto_sub -h localhost -t '$SYS/broker/clients/connected' -v
   ```

2. Verify QoS settings:
   ```python
   # Should be 1 or 2 for reliability
   MQTT_QOS = 1
   ```

3. Check retained messages:
   ```bash
   # Clear retained messages on topic
   mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/in" -r -n
   ```

---

## Verification Checklist

Before considering the issue resolved, verify:

- [ ] Local machine can scan fingerprints
- [ ] MQTT messages are published by local machine
- [ ] Server processor receives and logs MQTT messages
- [ ] Web UI receives MQTT messages
- [ ] WebSocket emits scan notification
- [ ] Browser receives WebSocket event
- [ ] Modal popup appears in browser
- [ ] Grant/Deny buttons work
- [ ] Actions are logged to database

---

## Additional Diagnostic Commands

### Check All Processes Running
```bash
# List Python processes
ps aux | grep python

# Should see:
# - mqtt_data_processor.py
# - app.py
# - fingerprint_simple_client.py
```

### Monitor MQTT Traffic
```bash
# Subscribe to all WHAC topics
mosquitto_sub -h 103.87.67.139 -t "WHAC/#" -v

# Should show messages on:
# - WHAC/Store001/in (scan data)
# - WHAC/Store001/action (relay commands)
# - WHAC/Store001/relay_status (relay status)
```

### Check Network Connectivity
```bash
# From local machine to MQTT broker
ping 103.87.67.139

# Test MQTT port
telnet 103.87.67.139 1883

# Should connect successfully
```

### Database Verification
```bash
# Connect to PostgreSQL
psql -U postgres -d whac_master

# Check recent scan logs
SELECT * FROM log_data ORDER BY timestamp DESC LIMIT 10;

# Check recent action logs
SELECT * FROM log_action ORDER BY timestamp DESC LIMIT 10;
```

---

## Success Indicators

When everything is working correctly:

1. **Local Machine**: Scans are detected and published
2. **Server Processor**: Receives, processes, and logs to database
3. **Web UI**: Receives data and emits to WebSocket
4. **Browser**: Modal appears for each scan
5. **Database**: All scans and actions are logged

---

## Getting Help

If issues persist:

1. **Collect Logs**: Save output from all three components
2. **Check Browser Console**: Save any error messages
3. **Network Trace**: Use Wireshark to capture MQTT traffic
4. **Test Components Individually**: Isolate which component is failing

**Log Files to Check:**
- Local machine: `local_machine/fingerprint_mqtt.log`
- Server processor: Terminal output
- Web UI: Terminal output
- Browser: Console (F12)

---

## Recent Fixes Applied

### Fix #1: Unique MQTT Client IDs ✅
**File**: `server/mqtt_data_processor.py`
```python
# Before:
self.mqtt_client = mqtt.Client()

# After:
self.mqtt_client = mqtt.Client(client_id="whac_server_processor", clean_session=True)
```

**File**: `web_ui/app.py`
```python
# Before:
mqtt_client = mqtt.Client()

# After:
mqtt_client = mqtt.Client(client_id="whac_web_ui", clean_session=True)
```

### Fix #2: Enhanced Logging ✅
Added detailed logging throughout the data flow:
- MQTT connection status
- Message reception
- WebSocket emission
- Browser event handling

### Fix #3: QoS Settings ✅
Changed subscription QoS from 0 to 1 for guaranteed delivery:
```python
client.subscribe(MQTT_SCAN_TOPIC, qos=1)
```

### Fix #4: Diagnostic Tools ✅
Added test buttons and API endpoints:
- `/test_websocket` - Test WebSocket emission
- `/simulate_scan` - Simulate complete flow
- `/api/mqtt_status` - Check MQTT connection
- UI buttons for easy testing

---

## Next Steps

1. **Restart all components** with the fixes applied
2. **Run diagnostic tests** using the UI buttons
3. **Perform a real scan** and watch the logs
4. **Verify modal appears** in the browser
5. **Test grant/deny actions** work correctly

If you still don't see the modal after following this guide, check the browser console for JavaScript errors and the server logs for any exceptions.

