# Modal Popup Debugging Guide

## Issue Fixed
The popup modal wasn't showing because multiple Bootstrap Modal instances were being created, causing conflicts.

## What Was Changed

### 1. Global Modal Instance
- Added `scanModal` as a global variable to store a single modal instance
- The modal is now initialized once when the page loads in `DOMContentLoaded`

### 2. Consistent Modal Usage
- `showScanNotification()` - Now uses the global `scanModal` instance
- `grantAccess()` - Now uses the global `scanModal` instance
- `denyAccess()` - Now uses the global `scanModal` instance
- `action_result` handler - Now uses the global `scanModal` instance

### 3. Better Logging
- Added console logs to track modal initialization and display
- Added emoji indicators for easier debugging in console

### 4. Test Button
- Added a "Test Modal" button in the navbar for easy testing

## How to Test

### Method 1: Test Button (Easiest)
1. Open the dashboard in your browser
2. Click the yellow "Test Modal" button in the top navbar
3. The modal should pop up immediately with test data

### Method 2: Browser Console
Open the browser console (F12) and run:
```javascript
testScanNotification()
```

### Method 3: WebSocket Test
Open the browser console (F12) and run:
```javascript
testWebSocketConnection()
```

### Method 4: Backend Simulation
Visit these URLs while logged in:
- `http://localhost:5000/test_websocket` - Test WebSocket emission
- `http://localhost:5000/simulate_scan` - Simulate a real fingerprint scan

## Console Logs to Watch For

When the modal works correctly, you should see:
```
✅ Scan notification modal initialized
🔔 showScanNotification called with data: {...}
👤 User info: Test User (ID: 1)
📺 Showing modal...
✅ Modal shown successfully!
```

## Troubleshooting

### Modal Still Not Showing?
1. **Check Console for Errors**
   - Open browser console (F12)
   - Look for red error messages
   - Check if modal initialization succeeded

2. **Verify Bootstrap is Loaded**
   - In console, type: `typeof bootstrap`
   - Should return: `"object"`
   - If `"undefined"`, Bootstrap failed to load

3. **Check Modal Element Exists**
   - In console, type: `document.getElementById('scanNotificationModal')`
   - Should return the modal DOM element
   - If `null`, modal HTML is missing

4. **Test Global Modal Variable**
   - In console, type: `scanModal`
   - Should return a Bootstrap Modal instance object
   - If `null`, initialization failed

5. **Clear Browser Cache**
   - Press Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
   - Clear cached files
   - Reload the page (Ctrl+F5 or Cmd+Shift+R)

### WebSocket Not Receiving Events?
1. **Check WebSocket Connection**
   - Look for: "✅ Connected to WebSocket server" in console
   - Look for green connection indicator in top-right corner

2. **Check MQTT Broker Connection**
   - Check server logs: `python web_ui/app.py`
   - Look for: "✓ MQTT client connected"

3. **Test Manual Emission**
   - Visit: `http://localhost:5000/simulate_scan`
   - This bypasses MQTT and directly emits to WebSocket

## Common Issues and Solutions

### Issue: Modal shows but doesn't close
**Solution**: Make sure you're using the Grant or Deny buttons, not clicking outside the modal (it's configured as static backdrop)

### Issue: Multiple modals stack on top of each other
**Solution**: This was the original problem - now fixed by using a single global instance

### Issue: Modal backdrop remains after closing
**Solution**: Restart the web server to clear any stuck states

### Issue: Test button doesn't work
**Solution**: Check browser console for JavaScript errors

## Files Modified
- `web_ui/templates/index.html` - Fixed modal instantiation and usage

## Testing Checklist
- [ ] Test Modal button shows the modal
- [ ] Modal displays user information correctly
- [ ] Grant Access button closes the modal
- [ ] Deny Access button closes the modal
- [ ] Modal shows when receiving real MQTT scan
- [ ] Console shows success messages
- [ ] No JavaScript errors in console
- [ ] WebSocket connection indicator shows green


