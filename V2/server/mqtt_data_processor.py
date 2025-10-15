#!/usr/bin/env python3
"""
MQTT Data Processor for WHAC Fingerprint System
Receives fingerprint scan data from local machines and processes it
"""

import paho.mqtt.client as mqtt
import json
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
import threading
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTDataProcessor:
    def __init__(self, mqtt_broker=None, mqtt_port=None):
        """
        Initialize MQTT data processor
        
        Args:
            mqtt_broker: MQTT broker IP address (defaults to environment variable)
            mqtt_port: MQTT broker port (defaults to environment variable)
        """
        self.mqtt_broker = mqtt_broker or os.getenv('MQTT_BROKER', '103.87.67.139')
        self.mqtt_port = mqtt_port or int(os.getenv('MQTT_PORT', '1883'))
        self.mqtt_client = None
        self.connected = False
        self.running = True
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'whac_master'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'Admin123'),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
        
        # MQTT Topics
        self.SCAN_TOPIC = os.getenv('SCAN_TOPIC', 'WHAC/Store001/in')  # Receive scan data
        self.ACTION_TOPIC = os.getenv('ACTION_TOPIC', 'WHAC/Store001/action')  # Send relay commands
        self.STATUS_TOPIC = os.getenv('STATUS_TOPIC', 'WHAC/Store001/status')  # Send status updates
        
        # Setup MQTT
        self.setup_mqtt()
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            # Use unique client ID to avoid conflicts with web UI
            self.mqtt_client = mqtt.Client(client_id="whac_server_processor", clean_session=True)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("✓ MQTT data processor connected")
            else:
                logger.error("✗ Failed to connect to MQTT broker within timeout")
                
        except Exception as e:
            logger.error(f"MQTT setup error: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Server processor MQTT client connected successfully")
            client.subscribe(self.SCAN_TOPIC, qos=1)
            logger.info(f"✅ Server processor subscribed to topic: {self.SCAN_TOPIC} (QoS 1)")
            logger.info("🔔 Server processor is now listening for scan data...")
        else:
            logger.error(f"❌ Server processor MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning(f"MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT scan messages"""
        try:
            logger.info("=" * 80)
            logger.info(f"📨 Server processor received MQTT message on topic: {msg.topic}")
            logger.info(f"📦 Raw payload: {msg.payload.decode()}")
            
            payload = json.loads(msg.payload.decode())
            logger.info(f"📋 Parsed JSON payload: {payload}")
            
            # Process the scan data
            self.process_scan_data(payload)
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Error processing MQTT message: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    def process_scan_data(self, data):
        """Process fingerprint scan data"""
        try:
            store_id = data.get('store_id')
            timestamp = data.get('timestamp')
            status = data.get('status')  # "Match" or "Not Match"
            fingerprint_id = data.get('fingerprint_id')
            device_id = data.get('device_id')
            username = data.get('username')  # From local machine
            confidence = data.get('confidence')
            
            if not all([store_id, timestamp, status, fingerprint_id is not None, device_id]):
                logger.warning(f"Incomplete scan data: {data}")
                return
            
            # Parse timestamp
            try:
                scan_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                scan_time = datetime.now()
            
            # Determine action based on status
            if status == "Match":
                action = "scan_detected"
                granted_denied = "pending"  # Waiting for admin decision
            else:
                action = "no_match"
                granted_denied = "denied"
            
            # Log to database
            self.log_scan_data(store_id, fingerprint_id, scan_time, action, username)
            
            # Log action
            self.log_action(store_id, fingerprint_id, username, scan_time, action, granted_denied)
            
            # Send status update
            self.send_status_update(store_id, fingerprint_id, action, device_id)
            
            logger.info(f"✓ Processed scan: {action} for user {fingerprint_id} ({username})")
            
        except Exception as e:
            logger.error(f"Error processing scan data: {e}")
    
    def get_user_info(self, fingerprint_id):
        """Get user information from database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT username FROM store_001 WHERE user_id = %s
            """, (fingerprint_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def log_scan_data(self, store_id, fingerprint_id, timestamp, action, username):
        """Log scan data to database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO log_data (user_id, store_id, timestamp, finger_template_id)
                VALUES (%s, %s, %s, %s)
            """, (fingerprint_id, store_id, timestamp, fingerprint_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging scan data: {e}")
            return False
    
    def log_action(self, store_id, fingerprint_id, username, timestamp, action, granted_denied="denied"):
        """Log action to database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO log_action (user_id, store_id, username, timestamp, action, granted_denied)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (fingerprint_id, store_id, username, timestamp, action, granted_denied))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return False
    
    def send_status_update(self, store_id, fingerprint_id, action, device_id):
        """Send status update via MQTT"""
        try:
            if not self.connected:
                logger.error("MQTT not connected, cannot send status update")
                return False
            
            payload = {
                'store_id': store_id,
                'fingerprint_id': fingerprint_id,
                'action': action,
                'device_id': device_id,
                'timestamp': datetime.now().isoformat(),
                'processed': True
            }
            
            result = self.mqtt_client.publish(self.STATUS_TOPIC, json.dumps(payload))
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Status update sent: {action} for user {fingerprint_id}")
                return True
            else:
                logger.error(f"✗ Failed to send status update (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return False
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up MQTT data processor...")
            self.running = False
            
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("MQTT client disconnected")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main function"""
    processor = MQTTDataProcessor()
    
    try:
        logger.info("=" * 60)
        logger.info("WHAC MQTT Data Processor - Running!")
        logger.info("=" * 60)
        logger.info(f"MQTT Broker: {processor.mqtt_broker}:{processor.mqtt_port}")
        logger.info(f"Scan Topic: {processor.SCAN_TOPIC}")
        logger.info(f"Status Topic: {processor.STATUS_TOPIC}")
        logger.info("=" * 60)
        logger.info("✓ Listening for fingerprint scan data...")
        logger.info("✓ Processing and logging to PostgreSQL...")
        logger.info("=" * 60)
        
        # Keep running
        while processor.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("MQTT data processor stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        processor.cleanup()

if __name__ == "__main__":
    main()
