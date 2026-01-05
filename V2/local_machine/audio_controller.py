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
    
    def __init__(self, audio_dir="audio", use_tts=True, prefer_espeak=False):
        """
        Initialize audio controller
        
        Args:
            audio_dir: Directory containing audio files
            use_tts: Use text-to-speech if audio file not found
            prefer_espeak: If True, skip pyttsx3 and use espeak directly
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
        self.use_espeak_direct = False
        if self.use_tts:
            # If prefer_espeak is True, skip pyttsx3 and use espeak directly
            if prefer_espeak:
                logger.info("ℹ️  Preferring espeak over pyttsx3")
                self.use_espeak_direct = True
                try:
                    import subprocess
                    result = subprocess.run(['which', 'espeak'], capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        logger.info("✅ Using espeak direct (preferred)")
                    else:
                        logger.warning("⚠️  espeak not found, TTS will be disabled")
                        self.use_tts = False
                except Exception as espeak_check_error:
                    logger.warning(f"⚠️  espeak check failed: {espeak_check_error}")
                    self.use_tts = False
            else:
                # Try to initialize pyttsx3 with different drivers
                pyttsx3_initialized = False
                
                # List of drivers to try (in order of preference)
                drivers_to_try = [None, 'sapi5', 'nsss', 'espeak']
                
                for driver in drivers_to_try:
                    try:
                        if driver:
                            logger.debug(f"Trying pyttsx3 with driver: {driver}")
                            self.tts_engine = pyttsx3.init(driverName=driver)
                        else:
                            logger.debug("Trying pyttsx3 with default driver")
                            self.tts_engine = pyttsx3.init()
                        
                        # Test if engine works by getting voices (this will fail if init really failed)
                        try:
                            test_voices = self.tts_engine.getProperty('voices')
                            pyttsx3_initialized = True
                            logger.info(f"✅ pyttsx3 initialized successfully (driver: {driver or 'default'})")
                            break
                        except Exception as test_error:
                            logger.debug(f"pyttsx3 init test failed with driver {driver}: {test_error}")
                            self.tts_engine = None
                            continue
                            
                    except Exception as init_error:
                        logger.debug(f"pyttsx3 init failed with driver {driver}: {init_error}")
                        self.tts_engine = None
                        continue
                
                if pyttsx3_initialized and self.tts_engine:
                    # Try to set properties, but don't fail if voice setting fails
                    try:
                        # Get available voices
                        voices = self.tts_engine.getProperty('voices')
                        
                        if voices and len(voices) > 0:
                            # Try to find and set Indonesian voice
                            voice_set = False
                            try:
                                for voice in voices:
                                    voice_name = voice.name.lower() if hasattr(voice, 'name') else ''
                                    voice_id = voice.id.lower() if hasattr(voice, 'id') else ''
                                    
                                    # Check for Indonesian voice
                                    if 'indonesia' in voice_name or 'id' in voice_id or 'indonesian' in voice_name:
                                        try:
                                            self.tts_engine.setProperty('voice', voice.id)
                                            logger.info(f"✅ Using Indonesian voice: {voice.name}")
                                            voice_set = True
                                            break
                                        except Exception as set_voice_error:
                                            logger.debug(f"Failed to set voice {voice.id}: {set_voice_error}")
                                            continue
                            except Exception as voice_iter_error:
                                logger.warning(f"⚠️  Error iterating voices: {voice_iter_error}")
                            
                            # If no Indonesian voice found or set, use default (first available)
                            if not voice_set:
                                try:
                                    # Try to use first available voice
                                    first_voice = voices[0]
                                    if hasattr(first_voice, 'id'):
                                        self.tts_engine.setProperty('voice', first_voice.id)
                                        logger.info(f"ℹ️  Using default voice: {first_voice.name}")
                                except Exception as default_voice_error:
                                    logger.debug(f"Using system default voice: {default_voice_error}")
                                    # Don't set voice, use system default
                        else:
                            logger.info("ℹ️  No voices available, using system default")
                        
                        # Set speech rate (this should always work)
                        try:
                            self.tts_engine.setProperty('rate', 150)  # Speech rate
                        except Exception as rate_error:
                            logger.debug(f"Could not set rate: {rate_error}")
                        
                        # Set volume (optional)
                        try:
                            self.tts_engine.setProperty('volume', 0.9)  # 90% volume
                        except Exception as volume_error:
                            logger.debug(f"Could not set volume: {volume_error}")
                        
                        logger.info("✅ TTS engine initialized (pyttsx3)")
                        
                    except Exception as property_error:
                        # If setting properties fails, continue with default settings
                        logger.warning(f"⚠️  Some TTS properties failed to set: {property_error}")
                        logger.info("ℹ️  Continuing with default TTS settings")
                        # Engine is still usable with default settings
                        logger.info("✅ TTS engine initialized (pyttsx3) with default settings")
                
                else:
                    # pyttsx3 init completely failed with all drivers
                    logger.warning("⚠️  pyttsx3 initialization failed with all drivers")
                    self.tts_engine = None
                    
                    # Fallback to espeak direct
                    logger.info("🔄 Falling back to espeak direct...")
                    try:
                        import subprocess
                        result = subprocess.run(['which', 'espeak'], capture_output=True, text=True, timeout=2)
                        if result.returncode == 0:
                            self.use_espeak_direct = True
                            logger.info("✅ Using espeak direct (fallback)")
                        else:
                            logger.warning("⚠️  espeak not found, TTS will be disabled")
                            self.use_tts = False
                    except Exception as espeak_check_error:
                        logger.warning(f"⚠️  espeak check failed: {espeak_check_error}")
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
                elif audio_type == 'voice_command':
                    success = self._play_voice_command(audio_data)
                
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
        # Try espeak direct first (if pyttsx3 failed)
        if self.use_espeak_direct:
            return self._play_espeak_direct(text)
        
        # Try pyttsx3
        if not self.use_tts or not self.tts_engine:
            # Fallback to espeak direct if available
            if not self.use_espeak_direct:
                try:
                    import subprocess
                    result = subprocess.run(['which', 'espeak'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.use_espeak_direct = True
                        logger.info("🔄 Falling back to espeak direct...")
                        return self._play_espeak_direct(text)
                except:
                    pass
            logger.warning("⚠️  TTS not available")
            return False
        
        try:
            logger.info(f"🔊 Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            logger.info("✅ TTS playback completed")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  pyttsx3 playback failed: {e}")
            # Fallback to espeak direct
            if not self.use_espeak_direct:
                try:
                    import subprocess
                    result = subprocess.run(['which', 'espeak'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.use_espeak_direct = True
                        logger.info("🔄 Falling back to espeak direct...")
                        return self._play_espeak_direct(text)
                except:
                    pass
            logger.error(f"❌ Error in TTS playback: {e}")
            return False
    
    def _play_espeak_direct(self, text):
        """Play text-to-speech using espeak directly (fallback)"""
        try:
            import subprocess
            logger.info(f"🔊 Speaking (espeak): {text}")
            
            # Use espeak with Indonesian language
            # -v id = Indonesian voice
            # -s 150 = speed (words per minute)
            # -a 200 = amplitude (volume)
            result = subprocess.run(
                ['espeak', '-v', 'id', '-s', '150', '-a', '200', text],
                capture_output=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ espeak playback completed")
                return True
            else:
                logger.warning(f"⚠️  espeak returned error code: {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ espeak timeout (text too long?)")
            return False
        except FileNotFoundError:
            logger.error("❌ espeak not found")
            return False
        except Exception as e:
            logger.error(f"❌ Error in espeak playback: {e}")
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
    
    def _play_voice_command(self, command_type):
        """Play voice command based on type"""
        logger.info(f"🔊 Playing voice command: {command_type}")
        
        # Voice command templates (Indonesian)
        voice_templates = {
            # Self-inspection commands
            'spin_around': {
                'file': 'spin_around.mp3',
                'text': 'Silakan berputar tiga ratus enam puluh derajat. Putar badan Anda secara perlahan.'
            },
            'raise_hands': {
                'file': 'raise_hands.mp3',
                'text': 'Angkat kedua tangan Anda ke atas. Rentangkan tangan Anda.'
            },
            'spread_arms': {
                'file': 'spread_arms.mp3',
                'text': 'Rentangkan kedua tangan Anda ke samping. Tunjukkan bahwa Anda tidak membawa barang berbahaya.'
            },
            'show_pockets': {
                'file': 'show_pockets.mp3',
                'text': 'Silakan tunjukkan isi saku Anda. Keluarkan semua barang dari saku.'
            },
            'open_bag': {
                'file': 'open_bag.mp3',
                'text': 'Silakan buka tas Anda untuk pemeriksaan. Tunjukkan isi tas Anda.'
            },
            'remove_jacket': {
                'file': 'remove_jacket.mp3',
                'text': 'Silakan lepaskan jaket atau sweater Anda untuk pemeriksaan.'
            },
            'turn_around_slowly': {
                'file': 'turn_around_slowly.mp3',
                'text': 'Silakan berbalik secara perlahan. Tunjukkan bahwa Anda tidak menyembunyikan sesuatu.'
            },
            
            # Warning messages
            'prohibited_item_warning': {
                'file': 'prohibited_warning.mp3',
                'text': 'Peringatan! Anda terdeteksi membawa barang yang tidak diperbolehkan. Silakan tinggalkan barang tersebut atau hubungi petugas.'
            },
            'weapon_warning': {
                'file': 'weapon_warning.mp3',
                'text': 'Peringatan! Terdeteksi benda berbahaya. Segera letakkan dan jangan bergerak. Petugas akan segera datang.'
            },
            'unauthorized_entry': {
                'file': 'unauthorized_entry.mp3',
                'text': 'Akses ditolak. Anda tidak memiliki izin untuk memasuki area ini. Silakan hubungi administrator.'
            },
            'suspicious_behavior': {
                'file': 'suspicious_behavior.mp3',
                'text': 'Peringatan! Perilaku mencurigakan terdeteksi. Mohon tunggu, petugas keamanan akan segera datang.'
            },
            'stop_immediately': {
                'file': 'stop_immediately.mp3',
                'text': 'Stop! Berhenti di tempat Anda berada. Jangan bergerak. Petugas akan melakukan pemeriksaan.'
            },
            
            # General instructions
            'step_forward': {
                'file': 'step_forward.mp3',
                'text': 'Silakan maju satu langkah untuk pemeriksaan lebih lanjut.'
            },
            'step_back': {
                'file': 'step_back.mp3',
                'text': 'Silakan mundur dan tunggu giliran Anda.'
            },
            'wait_moment': {
                'file': 'wait_moment.mp3',
                'text': 'Mohon tunggu sebentar. Sistem sedang memproses verifikasi Anda.'
            }
        }
        
        # Get command template
        template = voice_templates.get(command_type)
        if not template:
            logger.warning(f"⚠️  Unknown voice command: {command_type}")
            return False
        
        # Try to play audio file first
        audio_file = template['file']
        filepath = os.path.join(self.audio_dir, audio_file)
        
        if os.path.exists(filepath) and self.pygame_available:
            logger.info(f"🎵 Playing audio file: {audio_file}")
            return self._play_file(audio_file)
        
        # Fallback to TTS
        if self.use_tts:
            logger.info(f"🔄 Using TTS for voice command: {command_type}")
            return self._play_tts(template['text'])
        
        # Last resort: print message
        logger.warning(f"⚠️  No audio capability available, printing message:")
        logger.info(f"   {template['text']}")
        
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
    
    def play_voice_command(self, command_type, callback=None):
        """
        Queue voice command (NON-BLOCKING)
        
        Args:
            command_type: Type of voice command (e.g., 'spin_around', 'raise_hands', etc.)
            callback: Optional callback function(success: bool)
        
        Returns:
            bool: True if queued successfully
        """
        try:
            self.audio_queue.put_nowait({
                'type': 'voice_command',
                'data': command_type,
                'callback': callback
            })
            logger.info(f"✅ Voice command queued: {command_type}")
            return True
        except queue.Full:
            logger.error("❌ Audio queue is full")
            return False
        except Exception as e:
            logger.error(f"❌ Error queueing voice command: {e}")
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

def get_audio_controller(audio_dir="audio", use_tts=True, prefer_espeak=False):
    """Get or create global audio controller instance"""
    global _audio_controller
    if _audio_controller is None:
        _audio_controller = AudioController(audio_dir=audio_dir, use_tts=use_tts, prefer_espeak=prefer_espeak)
    return _audio_controller




















