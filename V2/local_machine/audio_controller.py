#!/usr/bin/env python3
"""
Audio Controller for Self-Inspection
Non-blocking audio playback with queue system to prevent overlapping
"""

import logging
import threading
import queue
import time
import os
import sys

logger = logging.getLogger(__name__)

# Try to import audio libraries
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("⚠️  pygame not available, audio will be disabled")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("⚠️  pyttsx3 not available, TTS will be disabled")


class AudioController:
    """Non-blocking audio controller with queue system"""
    
    def __init__(self, audio_dir="audio", use_tts=True):
        """
        Initialize audio controller
        
        Args:
            audio_dir: Directory containing audio files
            use_tts: Use text-to-speech if audio file not found
        """
        self.audio_dir = audio_dir
        self.use_tts = use_tts and TTS_AVAILABLE
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.playback_thread = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        
        # Initialize pygame mixer if available
        self.pygame_available = PYGAME_AVAILABLE
        if self.pygame_available:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                logger.info("✅ Pygame mixer initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize pygame mixer: {e}")
                self.pygame_available = False
        
        # Initialize TTS engine if available
        self.tts_engine = None
        if self.use_tts:
            try:
                self.tts_engine = pyttsx3.init()
                # Set TTS properties (optional)
                if self.tts_engine:
                    voices = self.tts_engine.getProperty('voices')
                    if voices:
                        # Try to use Indonesian voice if available
                        for voice in voices:
                            if 'indonesia' in voice.name.lower() or 'id' in voice.id.lower():
                                self.tts_engine.setProperty('voice', voice.id)
                                break
                    self.tts_engine.setProperty('rate', 150)  # Speech rate
                    logger.info("✅ TTS engine initialized")
            except Exception as e:
                logger.warning(f"⚠️  TTS initialization failed: {e}")
                self.use_tts = False
        
        # Start playback thread
        self._start_playback_thread()
        
        logger.info("✅ AudioController initialized")
    
    def _start_playback_thread(self):
        """Start background thread for audio playback"""
        if self.playback_thread is None or not self.playback_thread.is_alive():
            self.playback_thread = threading.Thread(
                target=self._playback_worker,
                daemon=True,
                name="AudioPlayback"
            )
            self.playback_thread.start()
            logger.info("✅ Audio playback thread started")
    
    def _playback_worker(self):
        """Background worker that processes audio queue"""
        logger.info("🎵 Audio playback worker started")
        
        while True:
            try:
                # Wait for audio request (with timeout to check stop_event)
                try:
                    audio_request = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    # Check if we should stop
                    if self.stop_event.is_set():
                        break
                    continue
                
                # Process audio request
                audio_type = audio_request.get('type', 'file')
                audio_data = audio_request.get('data', '')
                callback = audio_request.get('callback', None)
                
                logger.info(f"🎵 Playing audio: {audio_type} - {audio_data}")
                
                # Mark as playing
                with self.lock:
                    self.is_playing = True
                
                # Play audio based on type
                success = False
                if audio_type == 'file':
                    success = self._play_file(audio_data)
                elif audio_type == 'tts':
                    success = self._play_tts(audio_data)
                elif audio_type == 'self_inspection':
                    success = self._play_self_inspection()
                
                # Mark as not playing
                with self.lock:
                    self.is_playing = False
                
                # Call callback if provided
                if callback:
                    try:
                        callback(success)
                    except Exception as e:
                        logger.error(f"Error in audio callback: {e}")
                
                # Mark task as done
                self.audio_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Error in playback worker: {e}")
                with self.lock:
                    self.is_playing = False
    
    def _play_file(self, filename):
        """Play audio file"""
        if not self.pygame_available:
            logger.warning("⚠️  pygame not available, cannot play audio file")
            return False
        
        try:
            filepath = os.path.join(self.audio_dir, filename)
            
            # Check if file exists
            if not os.path.exists(filepath):
                logger.warning(f"⚠️  Audio file not found: {filepath}")
                # Try TTS as fallback if enabled
                if self.use_tts:
                    logger.info("🔄 Trying TTS fallback...")
                    return self._play_tts(f"Audio file {filename} not found")
                return False
            
            # Load and play audio
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                if self.stop_event.is_set():
                    pygame.mixer.music.stop()
                    return False
                time.sleep(0.1)
            
            logger.info(f"✅ Audio file played: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error playing audio file: {e}")
            return False
    
    def _play_tts(self, text):
        """Play text-to-speech"""
        if not self.use_tts or not self.tts_engine:
            logger.warning("⚠️  TTS not available")
            return False
        
        try:
            logger.info(f"🔊 Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            logger.info("✅ TTS playback completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in TTS playback: {e}")
            return False
    
    def _play_self_inspection(self):
        """Play self-inspection audio sequence"""
        logger.info("🔍 Starting self-inspection audio sequence")
        
        # Self-inspection messages (Indonesian)
        messages = [
            "Sistem sedang melakukan self inspection",
            "Silakan periksa sensor fingerprint",
            "Pastikan sensor dalam kondisi baik",
            "Self inspection selesai"
        ]
        
        # Try to play audio file first
        audio_file = "self_inspection.mp3"
        filepath = os.path.join(self.audio_dir, audio_file)
        
        if os.path.exists(filepath) and self.pygame_available:
            logger.info(f"🎵 Playing audio file: {audio_file}")
            return self._play_file(audio_file)
        
        # Fallback to TTS
        if self.use_tts:
            logger.info("🔄 Using TTS for self-inspection")
            full_message = ". ".join(messages)
            return self._play_tts(full_message)
        
        # Last resort: print messages
        logger.warning("⚠️  No audio capability available, printing messages:")
        for msg in messages:
            logger.info(f"   {msg}")
            time.sleep(1)
        
        return True
    
    def play_self_inspection(self, callback=None):
        """
        Queue self-inspection audio (NON-BLOCKING)
        
        Args:
            callback: Optional callback function(success: bool)
        
        Returns:
            bool: True if queued successfully, False if queue is full
        """
        try:
            # Check if already playing
            with self.lock:
                if self.is_playing:
                    logger.warning("⚠️  Audio already playing, queuing request")
            
            # Add to queue (non-blocking)
            try:
                self.audio_queue.put_nowait({
                    'type': 'self_inspection',
                    'data': '',
                    'callback': callback
                })
                logger.info("✅ Self-inspection audio queued")
                return True
            except queue.Full:
                logger.error("❌ Audio queue is full")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error queueing self-inspection audio: {e}")
            return False
    
    def play_file(self, filename, callback=None):
        """
        Queue audio file (NON-BLOCKING)
        
        Args:
            filename: Audio file name
            callback: Optional callback function(success: bool)
        
        Returns:
            bool: True if queued successfully
        """
        try:
            self.audio_queue.put_nowait({
                'type': 'file',
                'data': filename,
                'callback': callback
            })
            logger.info(f"✅ Audio file queued: {filename}")
            return True
        except queue.Full:
            logger.error("❌ Audio queue is full")
            return False
        except Exception as e:
            logger.error(f"❌ Error queueing audio file: {e}")
            return False
    
    def play_tts(self, text, callback=None):
        """
        Queue text-to-speech (NON-BLOCKING)
        
        Args:
            text: Text to speak
            callback: Optional callback function(success: bool)
        
        Returns:
            bool: True if queued successfully
        """
        try:
            self.audio_queue.put_nowait({
                'type': 'tts',
                'data': text,
                'callback': callback
            })
            logger.info(f"✅ TTS queued: {text[:50]}...")
            return True
        except queue.Full:
            logger.error("❌ Audio queue is full")
            return False
        except Exception as e:
            logger.error(f"❌ Error queueing TTS: {e}")
            return False
    
    def is_busy(self):
        """Check if audio is currently playing or queue has items"""
        with self.lock:
            return self.is_playing or not self.audio_queue.empty()
    
    def stop(self):
        """Stop current playback and clear queue"""
        logger.info("🛑 Stopping audio playback")
        
        # Stop pygame mixer
        if self.pygame_available:
            try:
                pygame.mixer.music.stop()
            except:
                pass
        
        # Stop TTS
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except:
                break
        
        # Set stop event
        self.stop_event.set()
        
        # Mark as not playing
        with self.lock:
            self.is_playing = False
        
        logger.info("✅ Audio stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up audio controller")
        self.stop()
        
        if self.pygame_available:
            try:
                pygame.mixer.quit()
            except:
                pass
        
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass


# Global audio controller instance
_audio_controller = None

def get_audio_controller(audio_dir="audio", use_tts=True):
    """Get or create global audio controller instance"""
    global _audio_controller
    if _audio_controller is None:
        _audio_controller = AudioController(audio_dir=audio_dir, use_tts=use_tts)
    return _audio_controller




















