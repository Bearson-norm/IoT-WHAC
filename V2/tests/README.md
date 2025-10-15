# Test Programs

This directory contains all test and utility programs for the IoT-WHAC fingerprint system.

## Test Categories

### System Tests
- `check_system_status.py` - Check overall system status
- `check_web_ui_mqtt.py` - Test web UI MQTT connectivity
- `start_system.py` - System startup utility

### Database Tests
- `test_database.py` - Database connection and operations testing
- `test_enrollment_debug.py` - Debug enrollment process
- `test_enrollment_manual.py` - Manual enrollment testing

### MQTT Tests
- `test_mqtt_bridge.py` - Test MQTT bridge functionality
- `test_mqtt_connection.py` - Test MQTT connection
- `test_mqtt_status.py` - Check MQTT status
- `test_mqtt_subscription.py` - Test MQTT subscriptions

### Hardware Tests
- `debug_fingerprint_connection.py` - Debug fingerprint sensor connection
- `simulate_fingerprint_scan.py` - Simulate fingerprint scanning
- `test_sensor_connection.py` - Test sensor connections

### Relay Tests
- `test_relay_fix.py` - Test relay fixes
- `test_relay_mqtt.py` - Test relay MQTT commands

### Web UI Tests
- `test_web_ui_api.py` - Test web UI API endpoints

### Verification Tests
- `verify_enrollment_bridge.py` - Verify enrollment bridge functionality

### Quick Tests
- `quick_test.py` - Quick system test utility

## Usage

Run individual tests from the project root:
```bash
python tests/test_database.py
python tests/test_mqtt_connection.py
```

Or run from within the tests directory:
```bash
cd tests
python test_database.py
```

