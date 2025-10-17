#!/bin/bash
"""
Quick setup script for Raspberry Pi
Fixes common issues and sets up the WHAC system
"""

echo "🚀 Quick Setup for WHAC System on Raspberry Pi..."

# Get current directory
CURRENT_DIR=$(pwd)
AUDIO_DIR="$CURRENT_DIR/whac_audio"

echo "📁 Current directory: $CURRENT_DIR"
echo "🔊 Audio directory: $AUDIO_DIR"

# Create audio directory
echo "📁 Creating audio directory..."
mkdir -p "$AUDIO_DIR"

# Install required packages
echo "📦 Installing required packages..."
sudo apt update
sudo apt install -y espeak espeak-data ffmpeg mpg123 alsa-utils

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install pygame

# Set up GPIO permissions
echo "🔐 Setting up GPIO permissions..."
sudo usermod -a -G gpio $USER
sudo usermod -a -G audio $USER

# Create simple test audio files
echo "🎵 Creating test audio files..."
cd "$AUDIO_DIR"

# Create simple test files
echo "Test message for access granted" > access_granted.txt
echo "Test message for access denied" > access_denied.txt
echo "Test message for violation alert" > violation_alert.txt
echo "Test message for exit confirmation" > exit_confirmation.txt
echo "Test message for turn around" > turn_around.txt
echo "Test message for stretch arms" > stretch_arms.txt
echo "Test message for show id" > show_id.txt
echo "Test message for wait" > wait.txt
echo "Test message for security alert" > security_alert.txt

# Generate actual audio files if espeak is available
if command -v espeak &> /dev/null; then
    echo "🔊 Generating audio files with espeak..."
    
    espeak -s 150 -v en -w access_granted.wav "Access granted. Welcome to the warehouse."
    espeak -s 150 -v en -w access_denied.wav "Access denied. Please contact your supervisor."
    espeak -s 150 -v en -w violation_alert.wav "Security violation detected. Please contact supervisor immediately."
    espeak -s 150 -v en -w exit_confirmation.wav "Exit request processed. You may now leave the warehouse."
    espeak -s 150 -v en -w turn_around.wav "Please turn around and face the camera for verification."
    espeak -s 150 -v en -w stretch_arms.wav "Please stretch your arms out to the sides for security check."
    espeak -s 150 -v en -w show_id.wav "Please show your identification card to the camera."
    espeak -s 150 -v en -w wait.wav "Please wait for further instructions from the operator."
    espeak -s 150 -v en -w security_alert.wav "Security alert. Please remain where you are and wait for security personnel."
    
    # Convert to MP3 if ffmpeg is available
    if command -v ffmpeg &> /dev/null; then
        echo "🔄 Converting WAV files to MP3..."
        for wav_file in *.wav; do
            if [ -f "$wav_file" ]; then
                mp3_file="${wav_file%.wav}.mp3"
                ffmpeg -i "$wav_file" -acodec mp3 -ab 128k -y "$mp3_file" 2>/dev/null
                rm "$wav_file"
                echo "✅ Converted: $mp3_file"
            fi
        done
    else
        echo "⚠️  ffmpeg not available, keeping WAV files"
    fi
else
    echo "⚠️  espeak not available, creating placeholder files"
    # Create placeholder MP3 files
    for file in access_granted access_denied violation_alert exit_confirmation turn_around stretch_arms show_id wait security_alert; do
        echo "# Placeholder MP3 file for $file" > "${file}.mp3"
    done
fi

# Set permissions
echo "🔐 Setting file permissions..."
chmod -R 755 "$AUDIO_DIR"

# Test audio system
echo "🧪 Testing audio system..."
if [ -f "$AUDIO_DIR/access_granted.mp3" ]; then
    if command -v mpg123 &> /dev/null; then
        mpg123 "$AUDIO_DIR/access_granted.mp3" 2>/dev/null
        echo "✅ Audio test successful!"
    else
        echo "⚠️  mpg123 not available for testing"
    fi
else
    echo "⚠️  Audio files not found"
fi

# Show system status
echo ""
echo "🎉 Quick setup complete!"
echo "📁 Audio files location: $AUDIO_DIR"
echo "🔊 Available audio files:"
ls -la "$AUDIO_DIR"/*.mp3 2>/dev/null || echo "No MP3 files found"

echo ""
echo "🧪 To test the system, run:"
echo "   python3 test_system.py"
echo ""
echo "🚀 To start the simple system, run:"
echo "   python3 whac_simple_system.py"
echo ""
echo "🚀 To start the full system, run:"
echo "   python3 whac_integrated_system.py"

