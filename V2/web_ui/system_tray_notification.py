#!/usr/bin/env python3
"""
System Tray Notification for WHAC
Creates system tray notifications that don't interrupt operator activity
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import os
import sys

# Try to import pystray for system tray functionality
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logging.warning("pystray not available - system tray notifications disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemTrayNotification:
    def __init__(self, mqtt_broker="103.87.67.139", mqtt_port=1883):
        """Initialize system tray notification"""
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.connected = False
        self.running = True
        self.tray_icon = None
        
        # Notification queue
        self.notification_queue = []
        
        # MQTT Topics
        self.SCAN_TOPIC = "WHAC/Store001/in"
        self.NOTIFICATION_TOPIC = "WHAC/Store001/notification"
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Start notification processor
        self.notification_thread = threading.Thread(target=self.process_notifications, daemon=True)
        self.notification_thread.start()
        
        # Setup system tray if available
        if TRAY_AVAILABLE:
            self.setup_system_tray()
        
        logger.info("✅ System Tray Notification initialized")
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(client_id=f"tray_notification_{int(time.time())}", clean_session=True)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            logger.info("✓ MQTT client setup complete for tray notifications")
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Tray notification MQTT client connected")
            
            # Subscribe to topics
            client.subscribe(self.SCAN_TOPIC, qos=1)
            client.subscribe(self.NOTIFICATION_TOPIC, qos=1)
            logger.info(f"✅ Subscribed to topics: {self.SCAN_TOPIC}, {self.NOTIFICATION_TOPIC}")
        else:
            logger.error(f"❌ Tray notification MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Tray notification MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if "in" in topic and payload.get('status') == 'Match':
                # User scan detected - create notification
                self.create_scan_notification(payload)
            elif "notification" in topic:
                # Handle other notifications
                self.handle_notification(payload)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def create_scan_notification(self, scan_data):
        """Create scan notification"""
        try:
            user_id = scan_data.get('fingerprint_id', 'Unknown')
            username = scan_data.get('username', f'User {user_id}')
            timestamp = scan_data.get('timestamp', datetime.now().isoformat())
            confidence = scan_data.get('confidence', 0)
            
            notification_data = {
                'type': 'user_scan',
                'title': 'User Scan Detected',
                'message': f'User {username} (ID: {user_id}) has scanned in the warehouse',
                'user_id': user_id,
                'username': username,
                'timestamp': timestamp,
                'confidence': confidence,
                'priority': 'normal'
            }
            
            # Add to notification queue
            self.notification_queue.append(notification_data)
            logger.info(f"📱 Added scan notification for user {username} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"Error creating scan notification: {e}")
    
    def handle_notification(self, payload):
        """Handle other notification types"""
        try:
            notification_type = payload.get('type')
            if notification_type == 'violation':
                self.create_violation_notification(payload)
            elif notification_type == 'security_alert':
                self.create_security_notification(payload)
                
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    def create_violation_notification(self, payload):
        """Create violation notification"""
        notification_data = {
            'type': 'violation',
            'title': 'Security Violation',
            'message': payload.get('message', 'Security violation detected'),
            'priority': 'high'
        }
        self.notification_queue.append(notification_data)
    
    def create_security_notification(self, payload):
        """Create security alert notification"""
        notification_data = {
            'type': 'security_alert',
            'title': 'Security Alert',
            'message': payload.get('message', 'Security alert triggered'),
            'priority': 'high'
        }
        self.notification_queue.append(notification_data)
    
    def process_notifications(self):
        """Process notification queue"""
        while self.running:
            try:
                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    self.show_notification(notification)
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing notifications: {e}")
                time.sleep(1)
    
    def show_notification(self, notification_data):
        """Show notification"""
        try:
            if TRAY_AVAILABLE and self.tray_icon:
                # Show system tray notification
                self._show_tray_notification(notification_data)
            else:
                # Fallback to messagebox
                self._show_messagebox_notification(notification_data)
                
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
    
    def _show_tray_notification(self, notification_data):
        """Show system tray notification"""
        try:
            title = notification_data['title']
            message = notification_data['message']
            
            # Show notification
            self.tray_icon.notify(message, title)
            
            # Update tray icon title
            self.tray_icon.title = f"WHAC - {title}"
            
            logger.info(f"📱 Tray notification shown: {title}")
            
        except Exception as e:
            logger.error(f"Error showing tray notification: {e}")
    
    def _show_messagebox_notification(self, notification_data):
        """Show messagebox notification as fallback"""
        try:
            title = notification_data['title']
            message = notification_data['message']
            
            # Create a simple popup
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Show messagebox
            result = messagebox.showinfo(title, message)
            
            root.destroy()
            
            logger.info(f"📱 MessageBox notification shown: {title}")
            
        except Exception as e:
            logger.error(f"Error showing messagebox notification: {e}")
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        try:
            # Create icon image
            image = self._create_tray_icon()
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Open Dashboard", self._open_dashboard),
                pystray.MenuItem("Show Status", self._show_status),
                pystray.MenuItem("Quit", self._quit_application)
            )
            
            # Create tray icon
            self.tray_icon = pystray.Icon("WHAC", image, "WHAC Fingerprint System", menu)
            
            # Start tray icon in separate thread
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
            logger.info("✅ System tray icon created")
            
        except Exception as e:
            logger.error(f"Error setting up system tray: {e}")
    
    def _create_tray_icon(self):
        """Create tray icon image"""
        try:
            # Create a simple icon
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color='blue')
            draw = ImageDraw.Draw(image)
            
            # Draw a simple fingerprint icon
            draw.ellipse([10, 10, 54, 54], fill='white', outline='black', width=2)
            draw.ellipse([20, 20, 44, 44], fill='lightblue', outline='black', width=1)
            
            return image
            
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
            # Return a simple colored square as fallback
            return Image.new('RGB', (64, 64), color='blue')
    
    def _open_dashboard(self, icon, item):
        """Open dashboard in browser"""
        try:
            import webbrowser
            webbrowser.open('http://localhost:5000')
            logger.info("🌐 Dashboard opened in browser")
        except Exception as e:
            logger.error(f"Error opening dashboard: {e}")
    
    def _show_status(self, icon, item):
        """Show system status"""
        try:
            status_message = f"WHAC System Status\n"
            status_message += f"MQTT Connected: {'Yes' if self.connected else 'No'}\n"
            status_message += f"Notifications Queued: {len(self.notification_queue)}\n"
            status_message += f"Uptime: {time.time() - self.start_time:.0f} seconds"
            
            messagebox.showinfo("WHAC System Status", status_message)
            
        except Exception as e:
            logger.error(f"Error showing status: {e}")
    
    def _quit_application(self, icon, item):
        """Quit application"""
        try:
            self.running = False
            if self.tray_icon:
                self.tray_icon.stop()
            logger.info("🛑 Application quit requested")
        except Exception as e:
            logger.error(f"Error quitting application: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.running = False
            
            if self.tray_icon:
                self.tray_icon.stop()
            
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("Tray notification MQTT client disconnected")
            
            logger.info("System tray notification system cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main function for testing system tray notifications"""
    try:
        logger.info("🚀 Starting System Tray Notification...")
        
        # Create system tray notification
        notification_system = SystemTrayNotification()
        notification_system.start_time = time.time()
        
        # Keep running
        logger.info("✅ System Tray Notification is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down System Tray Notification...")
        notification_system.cleanup()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        if 'notification_system' in locals():
            notification_system.cleanup()

if __name__ == "__main__":
    main()







