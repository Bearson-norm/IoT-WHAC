#!/bin/bash
"""
Setup script for WHAC Audio System
Installs required audio dependencies and creates audio directory structure
"""

echo "🔊 Setting up WHAC Audio System..."

# Create audio directory in current working directory
AUDIO_DIR="$(pwd)/whac_audio"
echo "📁 Creating audio directory: $AUDIO_DIR"
mkdir -p "$AUDIO_DIR"

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install audio tools
echo "🔧 Installing audio tools..."
sudo apt install -y espeak espeak-data
sudo apt install -y ffmpeg
sudo apt install -y mpg123
sudo apt install -y alsa-utils

# Install Python audio dependencies
echo "🐍 Installing Python audio dependencies..."
pip3 install pygame

# Set audio permissions
echo "🔐 Setting audio permissions..."
sudo usermod -a -G audio pi

# Test audio system
echo "🧪 Testing audio system..."
speaker-test -t wav -c 2 -l 1

# Create sample audio files
echo "🎵 Creating sample audio files..."
cd "$AUDIO_DIR"

# Create text-to-speech samples
espeak -s 150 -v en -w violation_alert.wav "Security violation detected. Please contact supervisor immediately."
espeak -s 150 -v en -w access_granted.wav "Access granted. Welcome to the warehouse."
espeak -s 150 -v en -w access_denied.wav "Access denied. Please contact your supervisor."
espeak -s 150 -v en -w exit_confirmation.wav "Exit request processed. You may now leave the warehouse."
espeak -s 150 -v en -w turn_around.wav "Please turn around and face the camera for verification."
espeak -s 150 -v en -w stretch_arms.wav "Please stretch your arms out to the sides for security check."
espeak -s 150 -v en -w show_id.wav "Please show your identification card to the camera."
espeak -s 150 -v en -w wait.wav "Please wait for further instructions from the operator."
espeak -s 150 -v en -w security_alert.wav "Security alert. Please remain where you are and wait for security personnel."

# Convert WAV to MP3
echo "🔄 Converting WAV files to MP3..."
for wav_file in *.wav; do
    if [ -f "$wav_file" ]; then
        mp3_file="${wav_file%.wav}.mp3"
        ffmpeg -i "$wav_file" -acodec mp3 -ab 128k -y "$mp3_file"
        rm "$wav_file"  # Remove WAV file after conversion
        echo "✅ Converted: $mp3_file"
    fi
done

# Set proper permissions
echo "🔐 Setting file permissions..."
chmod -R 755 "$AUDIO_DIR"

# Test MP3 playback
echo "🧪 Testing MP3 playback..."
if [ -f "$AUDIO_DIR/access_granted.mp3" ]; then
    mpg123 "$AUDIO_DIR/access_granted.mp3"
    echo "✅ Audio test successful!"
else
    echo "❌ Audio test failed - MP3 files not found"
fi

echo "🎉 WHAC Audio System setup complete!"
echo "📁 Audio files location: $AUDIO_DIR"
echo "🔊 Available audio files:"
ls -la "$AUDIO_DIR"/*.mp3 2>/dev/null || echo "No MP3 files found"

echo ""
echo "🚀 To start the integrated system, run:"
echo "   python3 whac_integrated_system.py"
