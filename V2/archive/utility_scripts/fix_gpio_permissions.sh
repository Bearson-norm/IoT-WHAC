#!/bin/bash
# Fix GPIO permissions and edge detection issues

echo "🔧 Fixing GPIO permissions and edge detection issues..."

# Add user to gpio group
sudo usermod -a -G gpio $USER

# Set proper permissions
sudo chmod 666 /dev/gpiomem
sudo chmod 666 /dev/mem

# Create udev rules for GPIO
sudo tee /etc/udev/rules.d/99-gpio.rules > /dev/null <<EOF
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0664"
SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c 'chown -R root:gpio /sys/class/gpio && chmod -R 775 /sys/class/gpio; chown -R root:gpio /sys/devices/virtual/gpio && chmod -R 775 /sys/devices/virtual/gpio'"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Check if pigpio is installed (better GPIO library)
if ! command -v pigpiod &> /dev/null; then
    echo "📦 Installing pigpio for better GPIO support..."
    sudo apt-get update
    sudo apt-get install -y pigpio python3-pigpio
fi

# Start pigpio daemon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

echo "✅ GPIO permissions fixed!"
echo "🔄 Please reboot your Raspberry Pi for changes to take effect:"
echo "   sudo reboot"

