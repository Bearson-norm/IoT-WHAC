#!/usr/bin/env python3
"""
Server-Side Fingerprint Template Management System
Manages fingerprint templates centrally and handles ID reassignment
"""

import json
import sqlite3
import base64
import logging
import paho.mqtt.client as mqtt
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServerTemplateManager:
    def __init__(self, db_file="central_fingerprints.db"):
        self.db_file = db_file
        self.mqtt_client = None
        self.connected = False
        self.init_database()
        
        # MQTT Configuration
        self.MQTT_BROKER = "103.87.67.139"
        self.MQTT_PORT = 1883
        self.MQTT_QOS = 1
        
        # Topics
        self.EXPORT_TOPIC = "WHAC/+/export"  # Listen to all stores
        self.IMPORT_TOPIC = "WHAC/+/import"  # Listen to all stores
        self.ADD_USER_TOPIC = "WHAC/+/add_user"  # Listen to all stores
        self.SERVER_COMMAND_TOPIC = "WHAC/server/command"  # Server commands
        self.SERVER_RESPONSE_TOPIC = "WHAC/server/response"  # Server responses
        
    def init_database(self):
        """Initialize central database for template management"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Central users table with unique user IDs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    user_name TEXT NOT NULL,
                    template_data BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Sensor assignments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    store_id TEXT,
                    sensor_fingerprint_id INTEGER,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Transfer history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transfer_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    from_store_id TEXT,
                    to_store_id TEXT,
                    from_sensor_id INTEGER,
                    to_sensor_id INTEGER,
                    transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Central database initialized: {self.db_file}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker at {self.MQTT_BROKER}:{self.MQTT_PORT}")
            self.mqtt_client = mqtt.Client()
            
            # Set up callbacks
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            # Connect to broker
            self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = datetime.now().timestamp()
            while not self.connected and (datetime.now().timestamp() - start_time) < timeout:
                import time
                time.sleep(0.1)
            
            if self.connected:
                logger.info("✓ MQTT broker connected successfully!")
                # Subscribe to topics
                self.mqtt_client.subscribe(self.EXPORT_TOPIC, qos=self.MQTT_QOS)
                self.mqtt_client.subscribe(self.IMPORT_TOPIC, qos=self.MQTT_QOS)
                self.mqtt_client.subscribe(self.ADD_USER_TOPIC, qos=self.MQTT_QOS)
                self.mqtt_client.subscribe(self.SERVER_COMMAND_TOPIC, qos=self.MQTT_QOS)
                logger.info("✓ Subscribed to all topics")
                return True
            else:
                logger.error("✗ Failed to connect to MQTT broker within timeout")
                return False
                
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT client connected")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.warning(f"MQTT client disconnected (code: {rc})")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received message on {topic}")
            
            # Extract store_id from topic
            store_id = topic.split('/')[1]
            
            # Handle different message types
            if "export" in topic:
                self.handle_export_from_sensor(store_id, payload)
            elif "import" in topic:
                self.handle_import_to_sensor(store_id, payload)
            elif "add_user" in topic:
                self.handle_add_user_from_sensor(store_id, payload)
            elif "server/command" in topic:
                self.handle_server_command(payload)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def handle_export_from_sensor(self, store_id: str, payload: dict):
        """Handle export from sensor - store templates in central database"""
        try:
            logger.info(f"Processing export from {store_id}")
            
            users_data = payload.get("data", {}).get("users", [])
            if not users_data:
                logger.error("No users data in export")
                return
            
            stored_count = 0
            for user_data in users_data:
                fingerprint_id = user_data.get("fingerprint_id")
                user_name = user_data.get("user_name")
                template_data = user_data.get("template_data")
                
                if fingerprint_id and user_name and template_data:
                    # Generate unique user ID
                    user_id = f"{store_id}_{fingerprint_id}_{user_name.replace(' ', '_')}"
                    
                    # Store in central database
                    conn = sqlite3.connect(self.db_file)
                    cursor = conn.cursor()
                    
                    # Decode template data
                    template_bytes = base64.b64decode(template_data)
                    
                    # Insert or update user
                    cursor.execute('''
                        INSERT OR REPLACE INTO users (user_id, user_name, template_data, last_updated)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, user_name, template_bytes, datetime.now()))
                    
                    # Update sensor assignment
                    cursor.execute('''
                        INSERT OR REPLACE INTO sensor_assignments 
                        (user_id, store_id, sensor_fingerprint_id, assigned_at)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, store_id, fingerprint_id, datetime.now()))
                    
                    conn.commit()
                    conn.close()
                    
                    stored_count += 1
                    logger.info(f"✓ Stored user: {user_name} (ID: {user_id}) from {store_id}")
            
            logger.info(f"✓ Stored {stored_count} users from {store_id}")
            
        except Exception as e:
            logger.error(f"Error handling export from {store_id}: {e}")
    
    def handle_import_to_sensor(self, store_id: str, payload: dict):
        """Handle import request to sensor - send templates with new IDs"""
        try:
            logger.info(f"Processing import request to {store_id}")
            
            import_request = payload.get("request")
            if import_request == "all_users":
                # Send all users to sensor
                self.send_all_users_to_sensor(store_id)
            elif import_request == "specific_users":
                # Send specific users
                user_ids = payload.get("user_ids", [])
                self.send_specific_users_to_sensor(store_id, user_ids)
            else:
                logger.error(f"Unknown import request: {import_request}")
                
        except Exception as e:
            logger.error(f"Error handling import to {store_id}: {e}")
    
    def send_all_users_to_sensor(self, store_id: str):
        """Send all users to a specific sensor with new IDs"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get all active users
            cursor.execute('''
                SELECT user_id, user_name, template_data 
                FROM users 
                WHERE is_active = TRUE
                ORDER BY user_id
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                logger.info(f"No users to send to {store_id}")
                return
            
            # Prepare users data with new IDs
            users_data = []
            for i, (user_id, user_name, template_data) in enumerate(users, 1):
                # Encode template data
                template_base64 = base64.b64encode(template_data).decode('utf-8')
                
                users_data.append({
                    "fingerprint_id": i,  # New ID starting from 1
                    "user_name": user_name,
                    "template_data": template_base64,
                    "original_user_id": user_id
                })
            
            # Send to sensor
            self.send_import_to_sensor(store_id, users_data)
            
            # Update sensor assignments
            self.update_sensor_assignments(store_id, users_data)
            
            logger.info(f"✓ Sent {len(users_data)} users to {store_id}")
            
        except Exception as e:
            logger.error(f"Error sending all users to {store_id}: {e}")
    
    def send_specific_users_to_sensor(self, store_id: str, user_ids: List[str]):
        """Send specific users to a sensor"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get specific users
            placeholders = ','.join(['?' for _ in user_ids])
            cursor.execute(f'''
                SELECT user_id, user_name, template_data 
                FROM users 
                WHERE user_id IN ({placeholders}) AND is_active = TRUE
            ''', user_ids)
            
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                logger.info(f"No users found for IDs: {user_ids}")
                return
            
            # Prepare users data
            users_data = []
            for i, (user_id, user_name, template_data) in enumerate(users, 1):
                template_base64 = base64.b64encode(template_data).decode('utf-8')
                
                users_data.append({
                    "fingerprint_id": i,
                    "user_name": user_name,
                    "template_data": template_base64,
                    "original_user_id": user_id
                })
            
            # Send to sensor
            self.send_import_to_sensor(store_id, users_data)
            
            # Update sensor assignments
            self.update_sensor_assignments(store_id, users_data)
            
            logger.info(f"✓ Sent {len(users_data)} specific users to {store_id}")
            
        except Exception as e:
            logger.error(f"Error sending specific users to {store_id}: {e}")
    
    def send_import_to_sensor(self, store_id: str, users_data: List[dict]):
        """Send import command to specific sensor"""
        try:
            import_topic = f"WHAC/{store_id}/import"
            import_payload = {
                "users": users_data
            }
            
            payload = json.dumps(import_payload)
            result = self.mqtt_client.publish(import_topic, payload, qos=self.MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Import command sent to {store_id}")
            else:
                logger.error(f"✗ Failed to send import command to {store_id}")
                
        except Exception as e:
            logger.error(f"Error sending import to {store_id}: {e}")
    
    def update_sensor_assignments(self, store_id: str, users_data: List[dict]):
        """Update sensor assignments in database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            for user_data in users_data:
                user_id = user_data["original_user_id"]
                new_sensor_id = user_data["fingerprint_id"]
                
                # Deactivate old assignments
                cursor.execute('''
                    UPDATE sensor_assignments 
                    SET is_active = FALSE 
                    WHERE user_id = ?
                ''', (user_id,))
                
                # Add new assignment
                cursor.execute('''
                    INSERT INTO sensor_assignments 
                    (user_id, store_id, sensor_fingerprint_id, assigned_at)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, store_id, new_sensor_id, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Updated sensor assignments for {store_id}")
            
        except Exception as e:
            logger.error(f"Error updating sensor assignments: {e}")
    
    def handle_add_user_from_sensor(self, store_id: str, payload: dict):
        """Handle add user from sensor"""
        try:
            logger.info(f"Processing add user from {store_id}")
            
            # This would be handled by the sensor's add_user_response
            # Server can log the addition
            logger.info(f"User added on {store_id}: {payload}")
            
        except Exception as e:
            logger.error(f"Error handling add user from {store_id}: {e}")
    
    def handle_server_command(self, payload: dict):
        """Handle server management commands"""
        try:
            command = payload.get("command")
            
            if command == "list_users":
                self.list_all_users()
            elif command == "transfer_user":
                self.transfer_user(payload)
            elif command == "get_user_info":
                self.get_user_info(payload)
            else:
                logger.error(f"Unknown server command: {command}")
                
        except Exception as e:
            logger.error(f"Error handling server command: {e}")
    
    def list_all_users(self):
        """List all users in central database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.user_id, u.user_name, u.created_at, 
                       sa.store_id, sa.sensor_fingerprint_id, sa.assigned_at
                FROM users u
                LEFT JOIN sensor_assignments sa ON u.user_id = sa.user_id AND sa.is_active = TRUE
                WHERE u.is_active = TRUE
                ORDER BY u.user_name
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            # Send response
            response = {
                "command": "list_users",
                "status": "success",
                "data": {
                    "users": [
                        {
                            "user_id": user[0],
                            "user_name": user[1],
                            "created_at": user[2],
                            "current_store": user[3],
                            "current_sensor_id": user[4],
                            "assigned_at": user[5]
                        }
                        for user in users
                    ],
                    "total_count": len(users)
                }
            }
            
            self.send_server_response(response)
            logger.info(f"✓ Listed {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
    
    def transfer_user(self, payload: dict):
        """Transfer user from one sensor to another"""
        try:
            user_id = payload.get("user_id")
            to_store_id = payload.get("to_store_id")
            
            if not user_id or not to_store_id:
                logger.error("Missing user_id or to_store_id in transfer command")
                return
            
            # Get user info
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_name, template_data 
                FROM users 
                WHERE user_id = ? AND is_active = TRUE
            ''', (user_id,))
            
            user = cursor.fetchone()
            if not user:
                logger.error(f"User {user_id} not found")
                return
            
            user_name, template_data = user
            
            # Get next available ID on target sensor
            next_id = self.get_next_available_id(to_store_id)
            
            # Prepare user data for import
            template_base64 = base64.b64encode(template_data).decode('utf-8')
            user_data = [{
                "fingerprint_id": next_id,
                "user_name": user_name,
                "template_data": template_base64,
                "original_user_id": user_id
            }]
            
            # Send to target sensor
            self.send_import_to_sensor(to_store_id, user_data)
            
            # Update assignments
            self.update_sensor_assignments(to_store_id, user_data)
            
            # Log transfer
            cursor.execute('''
                INSERT INTO transfer_history 
                (user_id, to_store_id, to_sensor_id, transferred_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, to_store_id, next_id, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Transferred user {user_name} to {to_store_id} with ID {next_id}")
            
            # Send response
            response = {
                "command": "transfer_user",
                "status": "success",
                "data": {
                    "user_id": user_id,
                    "user_name": user_name,
                    "to_store_id": to_store_id,
                    "new_sensor_id": next_id,
                    "message": f"User {user_name} transferred to {to_store_id}"
                }
            }
            
            self.send_server_response(response)
            
        except Exception as e:
            logger.error(f"Error transferring user: {e}")
    
    def get_next_available_id(self, store_id: str) -> int:
        """Get next available fingerprint ID for a store"""
        # This is a simplified version - in reality you'd query the sensor
        # For now, we'll use a simple counter
        return 1
    
    def send_server_response(self, response: dict):
        """Send server response"""
        try:
            payload = json.dumps(response)
            result = self.mqtt_client.publish(self.SERVER_RESPONSE_TOPIC, payload, qos=self.MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info("✓ Server response sent")
            else:
                logger.error("✗ Failed to send server response")
                
        except Exception as e:
            logger.error(f"Error sending server response: {e}")
    
    def run(self):
        """Run the server"""
        try:
            if not self.connect_mqtt():
                logger.error("Failed to connect to MQTT broker")
                return 1
            
            logger.info("=" * 70)
            logger.info("SERVER TEMPLATE MANAGER - Running!")
            logger.info("=" * 70)
            logger.info("✓ Listening for exports from sensors")
            logger.info("✓ Managing central template database")
            logger.info("✓ Handling ID reassignment")
            logger.info("✓ Processing transfer requests")
            logger.info("=" * 70)
            
            # Keep running
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            return 1
        finally:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
        
        return 0

def main():
    """Main function"""
    server = ServerTemplateManager()
    return server.run()

if __name__ == "__main__":
    import sys
    sys.exit(main())
