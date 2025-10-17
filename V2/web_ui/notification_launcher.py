#!/usr/bin/env python3
"""
Notification Launcher for WHAC
Launches system-wide notifications when user scans are detected
"""

import webbrowser
import threading
import time
import logging
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import os
import sys
import subprocess
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationLauncher:
    def __init__(self, mqtt_broker="103.87.67.139", mqtt_port=1883):
        """Initialize notification launcher"""
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.connected = False
        self.running = True
        
        # Notification settings
        self.notification_url = "http://localhost:5000/notification_popup.html"
        self.auto_close_delay = 30  # seconds
        
        # MQTT Topics
        self.SCAN_TOPIC = "WHAC/Store001/in"
        self.NOTIFICATION_TOPIC = "WHAC/Store001/notification"
        
        # Setup MQTT
        self.setup_mqtt()
        
        logger.info("✅ Notification Launcher initialized")
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(client_id=f"notification_launcher_{int(time.time())}", clean_session=True)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            logger.info("✓ MQTT client setup complete for notification launcher")
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Notification launcher MQTT client connected")
            
            # Subscribe to topics
            client.subscribe(self.SCAN_TOPIC, qos=1)
            client.subscribe(self.NOTIFICATION_TOPIC, qos=1)
            logger.info(f"✅ Subscribed to topics: {self.SCAN_TOPIC}, {self.NOTIFICATION_TOPIC}")
        else:
            logger.error(f"❌ Notification launcher MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Notification launcher MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if "in" in topic and payload.get('status') == 'Match':
                # User scan detected - launch notification
                self.launch_scan_notification(payload)
            elif "notification" in topic:
                # Handle other notifications
                self.handle_notification(payload)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def launch_scan_notification(self, scan_data):
        """Launch scan notification popup"""
        try:
            user_id = scan_data.get('fingerprint_id', 'Unknown')
            username = scan_data.get('username', f'User {user_id}')
            timestamp = scan_data.get('timestamp', datetime.now().isoformat())
            confidence = scan_data.get('confidence', 0)
            
            # Create notification parameters
            params = {
                'title': 'USER SCAN DETECTED',
                'message': f'User {username} (ID: {user_id}) has scanned in the warehouse',
                'userId': user_id,
                'username': username,
                'timestamp': timestamp,
                'confidence': confidence
            }
            
            # Launch notification in separate thread
            notification_thread = threading.Thread(
                target=self._launch_notification_popup,
                args=(params,),
                daemon=True
            )
            notification_thread.start()
            
            logger.info(f"🚨 Launched scan notification for user {username} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"Error launching scan notification: {e}")
    
    def handle_notification(self, payload):
        """Handle other notification types"""
        try:
            notification_type = payload.get('type')
            if notification_type == 'violation':
                self.launch_violation_notification(payload)
            elif notification_type == 'security_alert':
                self.launch_security_notification(payload)
                
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    def launch_violation_notification(self, payload):
        """Launch violation notification"""
        params = {
            'title': 'SECURITY VIOLATION',
            'message': payload.get('message', 'Security violation detected'),
            'userId': 'SYSTEM',
            'username': 'Security System',
            'timestamp': datetime.now().isoformat(),
            'confidence': 100
        }
        self._launch_notification_popup(params)
    
    def launch_security_notification(self, payload):
        """Launch security alert notification"""
        params = {
            'title': 'SECURITY ALERT',
            'message': payload.get('message', 'Security alert triggered'),
            'userId': 'SECURITY',
            'username': 'Security System',
            'timestamp': datetime.now().isoformat(),
            'confidence': 100
        }
        self._launch_notification_popup(params)
    
    def _launch_notification_popup(self, params):
        """Launch the actual notification popup"""
        try:
            # Build URL with parameters
            query_string = urllib.parse.urlencode(params)
            notification_url = f"{self.notification_url}?{query_string}"
            
            # Try different methods to open the notification
            
            # Method 1: Try to open in a new browser window
            try:
                webbrowser.open(notification_url, new=2)
                logger.info("📱 Notification opened in browser")
                return
            except Exception as e:
                logger.warning(f"Browser method failed: {e}")
            
            # Method 2: Try to open with system command
            try:
                if sys.platform.startswith('linux'):
                    subprocess.run(['xdg-open', notification_url], check=True)
                elif sys.platform.startswith('darwin'):  # macOS
                    subprocess.run(['open', notification_url], check=True)
                elif sys.platform.startswith('win'):  # Windows
                    subprocess.run(['start', notification_url], shell=True, check=True)
                else:
                    subprocess.run(['python', '-m', 'webbrowser', notification_url], check=True)
                
                logger.info("📱 Notification opened with system command")
                return
            except Exception as e:
                logger.warning(f"System command method failed: {e}")
            
            # Method 3: Fallback - create a simple popup
            self._create_fallback_popup(params)
            
        except Exception as e:
            logger.error(f"Error launching notification popup: {e}")
    
    def _create_fallback_popup(self, params):
        """Create a fallback popup using tkinter"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # Create root window
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Create message
            message = f"{params['title']}\n\n{params['message']}\n\n"
            message += f"User ID: {params['userId']}\n"
            message += f"Username: {params['username']}\n"
            message += f"Timestamp: {params['timestamp']}\n"
            message += f"Confidence: {params['confidence']}%"
            
            # Show messagebox
            result = messagebox.showwarning(
                "WHAC System Alert",
                message,
                icon='warning'
            )
            
            root.destroy()
            logger.info("📱 Fallback popup shown")
            
        except Exception as e:
            logger.error(f"Error creating fallback popup: {e}")
    
    def test_notification(self):
        """Test notification system"""
        try:
            logger.info("🧪 Testing notification system...")
            
            # Create test notification
            test_params = {
                'title': 'TEST NOTIFICATION',
                'message': 'This is a test notification from WHAC system',
                'userId': 'TEST_USER',
                'username': 'Test User',
                'timestamp': datetime.now().isoformat(),
                'confidence': 95
            }
            
            self._launch_notification_popup(test_params)
            logger.info("✅ Test notification launched")
            
        except Exception as e:
            logger.error(f"Error testing notification: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.running = False
            
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("Notification launcher MQTT client disconnected")
            
            logger.info("Notification launcher cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main function for testing notification launcher"""
    try:
        logger.info("🚀 Starting Notification Launcher...")
        
        # Create notification launcher
        launcher = NotificationLauncher()
        
        # Test notification
        launcher.test_notification()
        
        # Keep running
        logger.info("✅ Notification Launcher is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Notification Launcher...")
        launcher.cleanup()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        if 'launcher' in locals():
            launcher.cleanup()

if __name__ == "__main__":
    main()

