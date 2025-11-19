#!/usr/bin/env python3
"""
Audio Feedback Module for Local Machine
Provides audio feedback for various system events
"""

import os
import logging
import subprocess

logger = logging.getLogger(__name__)

class AudioFeedback:
    """Handle audio feedback using system commands"""
    
    def __init__(self):
        self.enabled = True
        self.audio_path = "/usr/share/sounds"  # Default sound path on Raspberry Pi
        
        # Check if espeak is available for text-to-speech
        try:
            subprocess.run(['which', 'espeak'], capture_output=True, check=True)
            self.tts_available = True
            logger.info("✅ Text-to-speech (espeak) is available")
        except:
            self.tts_available = False
            logger.warning("⚠️  Text-to-speech (espeak) not available")
        
        # Check if aplay is available for playing sounds
        try:
            subprocess.run(['which', 'aplay'], capture_output=True, check=True)
            self.audio_player = 'aplay'
            logger.info("✅ Audio player (aplay) is available")
        except:
            logger.warning("⚠️  Audio player not available")
            self.audio_player = None
    
    def play_beep(self, count=1, duration=100):
        """Play system beep sound"""
        try:
            if self.audio_player:
                # Use speaker-test for beep
                subprocess.run(
                    ['speaker-test', '-t', 'sine', '-f', '1000', '-l', '1'],
                    timeout=2,
                    capture_output=True
                )
                logger.info(f"🔊 Played beep sound")
            else:
                # Fallback to console beep
                print('\a' * count)
                logger.info(f"🔊 Played console beep (fallback)")
        except Exception as e:
            logger.error(f"Error playing beep: {e}")
    
    def play_success(self):
        """Play success sound"""
        try:
            if self.tts_available:
                subprocess.run(
                    ['espeak', '-v', 'en', '-s', '150', 'Access Granted'],
                    timeout=3,
                    capture_output=True
                )
                logger.info("🔊 Played success sound (TTS)")
            else:
                # Fallback to beeps
                self.play_beep(count=2)
        except Exception as e:
            logger.error(f"Error playing success sound: {e}")
    
    def play_error(self):
        """Play error sound"""
        try:
            if self.tts_available:
                subprocess.run(
                    ['espeak', '-v', 'en', '-s', '150', 'Error'],
                    timeout=3,
                    capture_output=True
                )
                logger.info("🔊 Played error sound (TTS)")
            else:
                # Fallback to long beep
                self.play_beep(count=1)
        except Exception as e:
            logger.error(f"Error playing error sound: {e}")
    
    def play_welcome(self):
        """Play welcome message"""
        try:
            if self.tts_available:
                subprocess.run(
                    ['espeak', '-v', 'en', '-s', '150', 'Welcome'],
                    timeout=3,
                    capture_output=True
                )
                logger.info("🔊 Played welcome sound (TTS)")
            else:
                self.play_beep(count=3)
        except Exception as e:
            logger.error(f"Error playing welcome sound: {e}")
    
    def speak(self, message):
        """Speak custom message using TTS"""
        try:
            if self.tts_available:
                subprocess.run(
                    ['espeak', '-v', 'en', '-s', '150', message],
                    timeout=10,
                    capture_output=True
                )
                logger.info(f"🔊 Spoke message: {message}")
            else:
                logger.warning(f"Cannot speak message (TTS not available): {message}")
                self.play_beep()
        except Exception as e:
            logger.error(f"Error speaking message: {e}")
    
    def play_audio_type(self, audio_type, message=''):
        """Play audio based on type"""
        try:
            if not self.enabled:
                logger.info("Audio feedback is disabled")
                return
            
            logger.info(f"🔊 Playing audio type: {audio_type}")
            
            if audio_type == 'beep':
                self.play_beep()
            elif audio_type == 'success':
                self.play_success()
            elif audio_type == 'error':
                self.play_error()
            elif audio_type == 'welcome':
                self.play_welcome()
            elif audio_type == 'speak' and message:
                self.speak(message)
            elif audio_type == 'enrollment_start':
                self.speak("Place finger on sensor")
            elif audio_type == 'enrollment_success':
                self.speak("Enrollment successful")
            elif audio_type == 'enrollment_failed':
                self.speak("Enrollment failed")
            elif audio_type == 'match':
                self.speak("Fingerprint matched")
            elif audio_type == 'no_match':
                self.speak("Fingerprint not matched")
            elif audio_type == 'system_ready':
                self.speak("System ready")
            elif audio_type == 'system_check':
                self.speak("Running system check")
            else:
                logger.warning(f"Unknown audio type: {audio_type}")
                self.play_beep()
        except Exception as e:
            logger.error(f"Error playing audio: {e}")

# Global instance
audio_feedback = AudioFeedback()

if __name__ == "__main__":
    # Test audio feedback
    logging.basicConfig(level=logging.INFO)
    
    print("Testing audio feedback...")
    audio = AudioFeedback()
    
    print("\n1. Testing beep...")
    audio.play_beep()
    
    print("\n2. Testing success...")
    audio.play_success()
    
    print("\n3. Testing error...")
    audio.play_error()
    
    print("\n4. Testing welcome...")
    audio.play_welcome()
    
    print("\n5. Testing custom message...")
    audio.speak("System test complete")
    
    print("\nAudio feedback test completed!")

