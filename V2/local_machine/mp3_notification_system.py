#!/usr/bin/env python3
"""
MP3 Notification System for WHAC Fingerprint System
Handles MP3 notifications for violations and user commands
"""

import paho.mqtt.client as mqtt
import json
import logging
import threading
import time
import os
import subprocess
from datetime import datetime
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MP3NotificationSystem:
    def __init__(self, mqtt_broker=MQTT_BROKER, mqtt_port=MQTT_PORT):
        """
        Initialize MP3 notification system
        
        Args:
            mqtt_broker: MQTT broker IP address
            mqtt_port: MQTT broker port
        """
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.connected = False
        self.running = True
        
        # Audio settings
        self.audio_device = "default"  # Default audio device
        self.volume = 80  # Volume percentage (0-100)
        
        # MP3 file paths - use current directory instead of /home/pi
        self.mp3_directory = os.path.join(os.getcwd(), "whac_audio")  # Directory for MP3 files
        self.violation_mp3 = os.path.join(self.mp3_directory, "violation_alert.mp3")
        self.command_mp3 = os.path.join(self.mp3_directory, "command_instruction.mp3")
        self.exit_mp3 = os.path.join(self.mp3_directory, "exit_confirmation.mp3")
        self.access_granted_mp3 = os.path.join(self.mp3_directory, "access_granted.mp3")
        self.access_denied_mp3 = os.path.join(self.mp3_directory, "access_denied.mp3")
        
        # User command MP3 templates
        self.turn_around_mp3 = os.path.join(self.mp3_directory, "turn_around.mp3")
        self.stretch_arms_mp3 = os.path.join(self.mp3_directory, "stretch_arms.mp3")
        self.show_id_mp3 = os.path.join(self.mp3_directory, "show_id.mp3")
        self.wait_mp3 = os.path.join(self.mp3_directory, "wait.mp3")
        self.security_alert_mp3 = os.path.join(self.mp3_directory, "security_alert.mp3")
        
        # MQTT Topics
        self.NOTIFICATION_TOPIC = f"WHAC/{STORE_ID}/notification"
        self.COMMAND_TOPIC = f"WHAC/{STORE_ID}/command"
        self.STATUS_TOPIC = f"WHAC/{STORE_ID}/audio_status"
        
        # Create audio directory if it doesn't exist
        self.setup_audio_directory()
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Audio player thread
        self.audio_thread = None
        self.audio_queue = []
        self.audio_lock = threading.Lock()
    
    def setup_audio_directory(self):
        """Create audio directory and default MP3 files if they don't exist"""
        try:
            if not os.path.exists(self.mp3_directory):
                os.makedirs(self.mp3_directory)
                logger.info(f"✓ Created audio directory: {self.mp3_directory}")
            
            # Create default MP3 files if they don't exist
            self.create_default_audio_files()
            
        except Exception as e:
            logger.error(f"Error setting up audio directory: {e}")
    
    def create_default_audio_files(self):
        """Create default MP3 files using text-to-speech"""
        try:
            # Check if espeak is available
            if self.check_audio_tools():
                self.generate_default_audio_files()
            else:
                logger.warning("⚠️  Audio tools not available - using placeholder files")
                self.create_placeholder_files()
                
        except Exception as e:
            logger.error(f"Error creating default audio files: {e}")
    
    def check_audio_tools(self):
        """Check if required audio tools are available"""
        try:
            # Check for espeak (text-to-speech)
            result = subprocess.run(['which', 'espeak'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✓ espeak found")
                return True
            else:
                logger.warning("⚠️  espeak not found")
                return False
        except Exception as e:
            logger.error(f"Error checking audio tools: {e}")
            return False
    
    def generate_default_audio_files(self):
        """Generate default MP3 files using espeak and ffmpeg"""
        try:
            # Audio messages
            messages = {
                self.violation_mp3: "Security violation detected. Please contact supervisor immediately.",
                self.command_mp3: "Please follow the instructions displayed on the operator dashboard.",
                self.exit_mp3: "Exit request processed. You may now leave the warehouse.",
                self.access_granted_mp3: "Access granted. Welcome to the warehouse.",
                self.access_denied_mp3: "Access denied. Please contact your supervisor.",
                self.turn_around_mp3: "Please turn around and face the camera for verification.",
                self.stretch_arms_mp3: "Please stretch your arms out to the sides for security check.",
                self.show_id_mp3: "Please show your identification card to the camera.",
                self.wait_mp3: "Please wait for further instructions from the operator.",
                self.security_alert_mp3: "Security alert. Please remain where you are and wait for security personnel."
            }
            
            for mp3_file, message in messages.items():
                if not os.path.exists(mp3_file):
                    self.text_to_mp3(message, mp3_file)
                    logger.info(f"✓ Generated: {mp3_file}")
                    
        except Exception as e:
            logger.error(f"Error generating default audio files: {e}")
    
    def text_to_mp3(self, text, output_file):
        """Convert text to MP3 using espeak and ffmpeg"""
        try:
            # Create temporary WAV file
            temp_wav = output_file.replace('.mp3', '_temp.wav')
            
            # Generate WAV using espeak
            espeak_cmd = [
                'espeak', '-s', '150', '-v', 'en', '-w', temp_wav, text
            ]
            subprocess.run(espeak_cmd, check=True, capture_output=True)
            
            # Convert WAV to MP3 using ffmpeg
            ffmpeg_cmd = [
                'ffmpeg', '-i', temp_wav, '-acodec', 'mp3', '-ab', '128k', 
                '-y', output_file
            ]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            # Clean up temporary file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
                
        except Exception as e:
            logger.error(f"Error converting text to MP3: {e}")
    
    def create_placeholder_files(self):
        """Create placeholder MP3 files"""
        try:
            placeholder_files = [
                self.violation_mp3,
                self.command_mp3,
                self.exit_mp3,
                self.access_granted_mp3,
                self.access_denied_mp3,
                self.turn_around_mp3,
                self.stretch_arms_mp3,
                self.show_id_mp3,
                self.wait_mp3,
                self.security_alert_mp3
            ]
            
            for mp3_file in placeholder_files:
                if not os.path.exists(mp3_file):
                    # Create empty file as placeholder
                    with open(mp3_file, 'w') as f:
                        f.write("# Placeholder MP3 file")
                    logger.info(f"✓ Created placeholder: {mp3_file}")
                    
        except Exception as e:
            logger.error(f"Error creating placeholder files: {e}")
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(client_id=f"mp3_notification_{STORE_ID}", clean_session=True)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            logger.info("✓ MQTT client setup complete for MP3 notifications")
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✅ MP3 notification MQTT client connected successfully")
            
            # Subscribe to notification and command topics
            client.subscribe(self.NOTIFICATION_TOPIC, qos=1)
            client.subscribe(self.COMMAND_TOPIC, qos=1)
            logger.info(f"✅ Subscribed to topics: {self.NOTIFICATION_TOPIC}, {self.COMMAND_TOPIC}")
        else:
            logger.error(f"❌ MP3 notification MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning(f"MP3 notification MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message on {topic}: {payload}")
            
            if "notification" in topic:
                self.handle_notification(payload)
            elif "command" in topic:
                self.handle_command(payload)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def handle_notification(self, payload):
        """Handle notification messages"""
        try:
            notification_type = payload.get('type')
            message = payload.get('message', '')
            user_id = payload.get('user_id', '')
            
            logger.info(f"🔊 Processing notification: {notification_type}")
            
            if notification_type == 'violation':
                self.play_violation_alert(user_id, message)
            elif notification_type == 'access_granted':
                self.play_access_granted(user_id)
            elif notification_type == 'access_denied':
                self.play_access_denied(user_id)
            elif notification_type == 'exit_confirmation':
                self.play_exit_confirmation(user_id)
            else:
                logger.warning(f"Unknown notification type: {notification_type}")
                
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    def handle_command(self, payload):
        """Handle command messages"""
        try:
            command_type = payload.get('command_type')
            instruction = payload.get('instruction', '')
            user_id = payload.get('user_id', '')
            
            logger.info(f"🎯 Processing command: {command_type} - {instruction}")
            
            if command_type == 'user_instruction':
                self.play_user_instruction(user_id, instruction)
            else:
                logger.warning(f"Unknown command type: {command_type}")
                
        except Exception as e:
            logger.error(f"Error handling command: {e}")
    
    def play_audio(self, mp3_file, user_id=None):
        """Play MP3 file"""
        try:
            if not os.path.exists(mp3_file):
                logger.error(f"MP3 file not found: {mp3_file}")
                return False
            
            # Add to audio queue
            with self.audio_lock:
                self.audio_queue.append({
                    'file': mp3_file,
                    'user_id': user_id,
                    'timestamp': datetime.now()
                })
            
            # Start audio thread if not running
            if not self.audio_thread or not self.audio_thread.is_alive():
                self.audio_thread = threading.Thread(target=self.audio_worker, daemon=True)
                self.audio_thread.start()
            
            logger.info(f"🔊 Added to audio queue: {os.path.basename(mp3_file)}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    def audio_worker(self):
        """Audio worker thread"""
        while self.running:
            try:
                with self.audio_lock:
                    if self.audio_queue:
                        audio_item = self.audio_queue.pop(0)
                    else:
                        audio_item = None
                
                if audio_item:
                    self.play_mp3_file(audio_item['file'], audio_item['user_id'])
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in audio worker: {e}")
                time.sleep(1)
    
    def play_mp3_file(self, mp3_file, user_id=None):
        """Play MP3 file using system audio player"""
        try:
            # Try different audio players
            players = ['mpg123', 'mpv', 'mplayer', 'omxplayer']
            
            for player in players:
                try:
                    if player == 'mpg123':
                        cmd = ['mpg123', '-q', mp3_file]
                    elif player == 'mpv':
                        cmd = ['mpv', '--no-video', '--really-quiet', mp3_file]
                    elif player == 'mplayer':
                        cmd = ['mplayer', '-really-quiet', mp3_file]
                    elif player == 'omxplayer':
                        cmd = ['omxplayer', mp3_file]
                    
                    # Check if player is available
                    result = subprocess.run(['which', player], capture_output=True, text=True)
                    if result.returncode == 0:
                        logger.info(f"🔊 Playing {os.path.basename(mp3_file)} using {player}")
                        subprocess.run(cmd, check=True, capture_output=True)
                        return True
                        
                except subprocess.CalledProcessError:
                    continue
                except Exception as e:
                    logger.error(f"Error with {player}: {e}")
                    continue
            
            logger.error(f"❌ No audio player available to play {mp3_file}")
            return False
            
        except Exception as e:
            logger.error(f"Error playing MP3 file: {e}")
            return False
    
    def play_violation_alert(self, user_id, message):
        """Play violation alert"""
        logger.warning(f"🚨 VIOLATION ALERT for user {user_id}: {message}")
        self.play_audio(self.violation_mp3, user_id)
        self.send_audio_status("violation_alert_played", user_id)
    
    def play_access_granted(self, user_id):
        """Play access granted message"""
        logger.info(f"✅ Access granted for user {user_id}")
        self.play_audio(self.access_granted_mp3, user_id)
        self.send_audio_status("access_granted_played", user_id)
    
    def play_access_denied(self, user_id):
        """Play access denied message"""
        logger.warning(f"❌ Access denied for user {user_id}")
        self.play_audio(self.access_denied_mp3, user_id)
        self.send_audio_status("access_denied_played", user_id)
    
    def play_exit_confirmation(self, user_id):
        """Play exit confirmation message"""
        logger.info(f"🚪 Exit confirmation for user {user_id}")
        self.play_audio(self.exit_mp3, user_id)
        self.send_audio_status("exit_confirmation_played", user_id)
    
    def play_user_instruction(self, user_id, instruction):
        """Play user instruction message"""
        logger.info(f"🎯 User instruction for user {user_id}: {instruction}")
        
        # Map instruction to specific MP3 file
        instruction_map = {
            'turn_around': self.turn_around_mp3,
            'stretch_arms': self.stretch_arms_mp3,
            'show_id': self.show_id_mp3,
            'wait': self.wait_mp3,
            'security_alert': self.security_alert_mp3
        }
        
        # Get the appropriate MP3 file for the instruction
        mp3_file = instruction_map.get(instruction, self.command_mp3)
        
        # Play the specific instruction
        self.play_audio(mp3_file, user_id)
        self.send_audio_status(f"user_instruction_played_{instruction}", user_id)
    
    def send_audio_status(self, status, user_id):
        """Send audio status update via MQTT"""
        try:
            status_data = {
                "status": status,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "store_id": STORE_ID
            }
            
            if self.connected:
                self.mqtt_client.publish(self.STATUS_TOPIC, json.dumps(status_data), qos=1)
                logger.info(f"📤 Audio status sent: {status}")
            else:
                logger.error("❌ Cannot send audio status - MQTT not connected")
                
        except Exception as e:
            logger.error(f"Error sending audio status: {e}")
    
    def test_audio_system(self):
        """Test audio system functionality"""
        try:
            logger.info("🔊 Testing MP3 notification system...")
            
            # Test each audio file
            test_files = [
                (self.violation_mp3, "violation_alert"),
                (self.access_granted_mp3, "access_granted"),
                (self.access_denied_mp3, "access_denied"),
                (self.exit_mp3, "exit_confirmation"),
                (self.command_mp3, "user_instruction"),
                (self.turn_around_mp3, "turn_around"),
                (self.stretch_arms_mp3, "stretch_arms"),
                (self.show_id_mp3, "show_id"),
                (self.wait_mp3, "wait"),
                (self.security_alert_mp3, "security_alert")
            ]
            
            for mp3_file, test_type in test_files:
                if os.path.exists(mp3_file):
                    logger.info(f"Testing {test_type}...")
                    self.play_audio(mp3_file, "test_user")
                    time.sleep(2)  # Wait between tests
                else:
                    logger.warning(f"Test file not found: {mp3_file}")
            
            logger.info("✓ MP3 notification system test completed")
            
        except Exception as e:
            logger.error(f"MP3 notification system test error: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up MP3 notification system...")
            
            self.running = False
            
            # Disconnect MQTT
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("MP3 notification MQTT client disconnected")
            
            logger.info("MP3 notification system cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main function for testing MP3 notification system"""
    try:
        logger.info("🚀 Starting MP3 Notification System...")
        
        # Create MP3 notification system
        mp3_system = MP3NotificationSystem()
        
        # Wait for MQTT connection
        time.sleep(2)
        
        # Test audio system
        logger.info("Testing MP3 notification system...")
        mp3_system.test_audio_system()
        
        # Keep running
        logger.info("✅ MP3 Notification System is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down MP3 Notification System...")
        mp3_system.cleanup()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        if 'mp3_system' in locals():
            mp3_system.cleanup()

if __name__ == "__main__":
    main()
