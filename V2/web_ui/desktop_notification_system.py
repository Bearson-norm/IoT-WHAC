#!/usr/bin/env python3
"""
Desktop Notification System for WHAC
Creates system-wide popup notifications that interrupt operator activity
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import logging
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DesktopNotificationSystem:
    def __init__(self, mqtt_broker="103.87.67.139", mqtt_port=1883):
        """Initialize desktop notification system"""
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.connected = False
        self.running = True
        
        # Notification queue
        self.notification_queue = []
        self.active_notifications = []
        
        # MQTT Topics
        self.SCAN_TOPIC = "WHAC/Store001/in"
        self.NOTIFICATION_TOPIC = "WHAC/Store001/notification"
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Start notification processor
        self.notification_thread = threading.Thread(target=self.process_notifications, daemon=True)
        self.notification_thread.start()
        
        logger.info("✅ Desktop Notification System initialized")
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(client_id=f"desktop_notification_{int(time.time())}", clean_session=True)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            logger.info("✓ MQTT client setup complete for desktop notifications")
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Desktop notification MQTT client connected")
            
            # Subscribe to topics
            client.subscribe(self.SCAN_TOPIC, qos=1)
            client.subscribe(self.NOTIFICATION_TOPIC, qos=1)
            logger.info(f"✅ Subscribed to topics: {self.SCAN_TOPIC}, {self.NOTIFICATION_TOPIC}")
        else:
            logger.error(f"❌ Desktop notification MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Desktop notification MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if "in" in topic and payload.get('status') == 'Match':
                # User scan detected - create interrupt notification
                self.create_interrupt_notification(payload)
            elif "notification" in topic:
                # Handle other notifications
                self.handle_notification(payload)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def create_interrupt_notification(self, scan_data):
        """Create interrupt notification for user scans"""
        try:
            user_id = scan_data.get('fingerprint_id', 'Unknown')
            username = scan_data.get('username', f'User {user_id}')
            timestamp = scan_data.get('timestamp', datetime.now().isoformat())
            confidence = scan_data.get('confidence', 0)
            
            notification_data = {
                'type': 'user_scan_interrupt',
                'title': '🚨 USER SCAN DETECTED',
                'message': f'User {username} (ID: {user_id}) has scanned in the warehouse',
                'user_id': user_id,
                'username': username,
                'timestamp': timestamp,
                'confidence': confidence,
                'priority': 'high',
                'action_required': True,
                'scan_data': scan_data
            }
            
            # Add to notification queue
            self.notification_queue.append(notification_data)
            logger.info(f"🚨 Added interrupt notification for user {username} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"Error creating interrupt notification: {e}")
    
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
            'title': '⚠️ SECURITY VIOLATION',
            'message': payload.get('message', 'Security violation detected'),
            'priority': 'critical',
            'action_required': True
        }
        self.notification_queue.append(notification_data)
    
    def create_security_notification(self, payload):
        """Create security alert notification"""
        notification_data = {
            'type': 'security_alert',
            'title': '🔒 SECURITY ALERT',
            'message': payload.get('message', 'Security alert triggered'),
            'priority': 'critical',
            'action_required': True
        }
        self.notification_queue.append(notification_data)
    
    def process_notifications(self):
        """Process notification queue"""
        while self.running:
            try:
                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    self.show_desktop_notification(notification)
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing notifications: {e}")
                time.sleep(1)
    
    def show_desktop_notification(self, notification_data):
        """Show desktop notification popup"""
        try:
            # Create notification in a separate thread to avoid blocking
            notification_thread = threading.Thread(
                target=self._create_notification_window,
                args=(notification_data,),
                daemon=True
            )
            notification_thread.start()
            
        except Exception as e:
            logger.error(f"Error showing desktop notification: {e}")
    
    def _create_notification_window(self, notification_data):
        """Create the actual notification window"""
        try:
            # Create main window
            root = tk.Tk()
            root.title("WHAC System Alert")
            
            # Make window always on top and fullscreen
            root.attributes('-topmost', True)
            root.attributes('-fullscreen', True)
            root.configure(bg='black')
            
            # Create main frame
            main_frame = tk.Frame(root, bg='black')
            main_frame.pack(expand=True, fill='both')
            
            # Create notification content
            self._create_notification_content(main_frame, notification_data, root)
            
            # Auto-close after 30 seconds
            root.after(30000, root.destroy)
            
            # Start the GUI
            root.mainloop()
            
        except Exception as e:
            logger.error(f"Error creating notification window: {e}")
    
    def _create_notification_content(self, parent, notification_data, root):
        """Create notification content"""
        try:
            # Main container
            container = tk.Frame(parent, bg='black', padx=50, pady=50)
            container.pack(expand=True, fill='both')
            
            # Title
            title_frame = tk.Frame(container, bg='red', relief='raised', bd=5)
            title_frame.pack(fill='x', pady=(0, 20))
            
            title_label = tk.Label(
                title_frame,
                text=notification_data['title'],
                font=('Arial', 36, 'bold'),
                fg='white',
                bg='red',
                pady=20
            )
            title_label.pack()
            
            # Message
            message_frame = tk.Frame(container, bg='darkred', relief='raised', bd=3)
            message_frame.pack(fill='x', pady=(0, 20))
            
            message_label = tk.Label(
                message_frame,
                text=notification_data['message'],
                font=('Arial', 24),
                fg='white',
                bg='darkred',
                wraplength=800,
                justify='center',
                pady=20
            )
            message_label.pack()
            
            # User details
            if 'user_id' in notification_data:
                details_frame = tk.Frame(container, bg='darkgray', relief='raised', bd=2)
                details_frame.pack(fill='x', pady=(0, 20))
                
                details_text = f"User ID: {notification_data['user_id']}\n"
                details_text += f"Username: {notification_data['username']}\n"
                details_text += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                if 'confidence' in notification_data:
                    details_text += f"Confidence: {notification_data['confidence']}%"
                
                details_label = tk.Label(
                    details_frame,
                    text=details_text,
                    font=('Arial', 18),
                    fg='white',
                    bg='darkgray',
                    justify='center',
                    pady=15
                )
                details_label.pack()
            
            # Action buttons
            if notification_data.get('action_required', False):
                button_frame = tk.Frame(container, bg='black')
                button_frame.pack(fill='x', pady=(0, 20))
                
                # Open Dashboard button
                dashboard_btn = tk.Button(
                    button_frame,
                    text="🔍 OPEN DASHBOARD",
                    font=('Arial', 20, 'bold'),
                    bg='blue',
                    fg='white',
                    command=lambda: self._open_dashboard(root),
                    padx=30,
                    pady=15
                )
                dashboard_btn.pack(side='left', padx=10)
                
                # Acknowledge button
                ack_btn = tk.Button(
                    button_frame,
                    text="✅ ACKNOWLEDGE",
                    font=('Arial', 20, 'bold'),
                    bg='green',
                    fg='white',
                    command=lambda: self._acknowledge_notification(root),
                    padx=30,
                    pady=15
                )
                ack_btn.pack(side='left', padx=10)
                
                # Dismiss button
                dismiss_btn = tk.Button(
                    button_frame,
                    text="❌ DISMISS",
                    font=('Arial', 20, 'bold'),
                    bg='red',
                    fg='white',
                    command=root.destroy,
                    padx=30,
                    pady=15
                )
                dismiss_btn.pack(side='right', padx=10)
            
            # Blinking effect
            self._start_blinking(title_label)
            
            # Sound alert (if available)
            self._play_alert_sound()
            
        except Exception as e:
            logger.error(f"Error creating notification content: {e}")
    
    def _start_blinking(self, widget):
        """Start blinking effect for the title"""
        def blink():
            try:
                current_color = widget.cget('bg')
                new_color = 'yellow' if current_color == 'red' else 'red'
                widget.configure(bg=new_color)
                widget.after(500, blink)
            except:
                pass  # Widget might be destroyed
        
        blink()
    
    def _play_alert_sound(self):
        """Play alert sound"""
        try:
            # Try to play system beep
            import subprocess
            subprocess.run(['beep'], check=False, capture_output=True)
        except:
            try:
                # Try to play with speaker-test
                subprocess.run(['speaker-test', '-t', 'sine', '-f', '1000', '-l', '1'], 
                             check=False, capture_output=True)
            except:
                pass  # Sound not available
    
    def _open_dashboard(self, root):
        """Open dashboard in browser"""
        try:
            import webbrowser
            webbrowser.open('http://localhost:5000')
            root.destroy()
        except Exception as e:
            logger.error(f"Error opening dashboard: {e}")
    
    def _acknowledge_notification(self, root):
        """Acknowledge notification"""
        try:
            logger.info("✅ Notification acknowledged by operator")
            root.destroy()
        except Exception as e:
            logger.error(f"Error acknowledging notification: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.running = False
            
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("Desktop notification MQTT client disconnected")
            
            logger.info("Desktop notification system cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main function for testing desktop notifications"""
    try:
        logger.info("🚀 Starting Desktop Notification System...")
        
        # Create desktop notification system
        notification_system = DesktopNotificationSystem()
        
        # Keep running
        logger.info("✅ Desktop Notification System is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Desktop Notification System...")
        notification_system.cleanup()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        if 'notification_system' in locals():
            notification_system.cleanup()

if __name__ == "__main__":
    main()









