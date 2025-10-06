# Fingerprint MQTT Client for Raspberry Pi 4

This Python application integrates an AS608 fingerprint sensor with MQTT communication to send fingerprint data to a remote server.

## Features

- **AS608 Fingerprint Sensor Integration**: Captures and processes fingerprint data
- **MQTT Communication**: Sends data to MQTT broker at 103.87.67.139
- **JSON Payload**: Sends structured data with store_id, finger_id, and timestamp
- **Error Handling**: Comprehensive logging and error management
- **Real-time Monitoring**: Continuous fingerprint scanning

## Hardware Requirements

- Raspberry Pi 4
- AS608 Fingerprint Sensor Module
- USB connection (or UART connection)

## Software Requirements

- Python 3.7+
- Required Python packages (see requirements.txt)

## Installation

### Option 1: Automated Setup
```bash
# Run the setup script
python3 setup.py
```

### Option 2: Manual Setup
```bash
# Update system packages
sudo apt update
sudo apt install -y python3-pip python3-serial python3-dev build-essential

# Install Python dependencies
pip3 install -r requirements.txt

# Add user to dialout group for serial access
sudo usermod -a -G dialout $USER

# Reboot to apply group changes
sudo reboot
```

## Configuration

1. **Check your fingerprint sensor connection**:
   ```bash
   ls /dev/tty*
   ```
   Look for `/dev/ttyUSB0` or `/dev/ttyACM0`

2. **Update configuration** (if needed):
   Edit `config.py` to modify:
   - Store ID
   - MQTT broker settings
   - Fingerprint sensor port
   - Other parameters

## Usage

### Basic Usage
```bash
python3 fingerprint_mqtt_client.py
```

### Running as a Service (Optional)
Create a systemd service file for automatic startup:

```bash
sudo nano /etc/systemd/system/fingerprint-mqtt.service
```

Add the following content:
```ini
[Unit]
Description=Fingerprint MQTT Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/your/project
ExecStart=/usr/bin/python3 fingerprint_mqtt_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable fingerprint-mqtt.service
sudo systemctl start fingerprint-mqtt.service
```

## MQTT Message Format

The application sends JSON messages to the topic `WHAC/Store001/in`:

```json
{
    "store_id": "Store001",
    "finger_id": 123,
    "Timestamp": "2024-01-15T10:30:45.123456"
}
```

## Troubleshooting

### Common Issues

1. **Permission denied for /dev/ttyUSB0**:
   - Make sure your user is in the dialout group
   - Run: `sudo usermod -a -G dialout $USER` and reboot

2. **Fingerprint sensor not found**:
   - Check USB connection
   - Verify the device path in config.py
   - Try different baud rates (9600, 57600, 115200)

3. **MQTT connection failed**:
   - Check network connectivity
   - Verify MQTT broker address and port
   - Check firewall settings

4. **No fingerprints recognized**:
   - Ensure fingerprints are enrolled in the sensor
   - Adjust confidence threshold in config.py
   - Clean the sensor surface

### Logs

Check the log file `fingerprint_mqtt.log` for detailed information about:
- Sensor initialization
- MQTT connections
- Fingerprint scans
- Error messages

## Development

### Adding New Features

1. Modify `fingerprint_mqtt_client.py` for new functionality
2. Update `config.py` for new configuration options
3. Test thoroughly before deployment

### Testing MQTT Connection

You can test the MQTT connection using mosquitto tools:
```bash
# Install mosquitto client
sudo apt install mosquitto-clients

# Subscribe to messages
mosquitto_sub -h 103.87.67.139 -t "WHAC/Store001/in"

# Publish test message
mosquitto_pub -h 103.87.67.139 -t "WHAC/Store001/test" -m "Hello World"
```

## License

This project is open source. Feel free to modify and distribute.

## Support

For issues and questions:
1. Check the logs in `fingerprint_mqtt.log`
2. Verify hardware connections
3. Test MQTT connectivity separately
4. Check sensor functionality with manufacturer tools
