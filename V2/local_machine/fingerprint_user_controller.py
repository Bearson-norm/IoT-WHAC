#!/usr/bin/env python3
"""
Advanced User Management Controller for Fingerprint System
Based on fingerprint_simple_client.py configuration
Provides comprehensive user management with enhanced logging and reporting
"""

import serial
import adafruit_fingerprint
import paho.mqtt.client as mqtt
import json
import time
import logging
import sys
import sqlite3
import threading
import glob
import os
import csv
from datetime import datetime, timedelta
from config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_controller.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FingerprintUserController:
    def __init__(self):
        self.uart = None
        self.finger = None
        self.mqtt_client = None
        self.connected = False
        self.running = True
        self.enrolling = False
        self.command_lock = threading.Lock()
        self.db_file = "fingerprints.db"
        self.init_database()
        
        # Use configured port directly
        self.detected_port = FINGERPRINT_PORT
        logger.info(f"🎯 Using configured port: {self.detected_port}")
        
        # Verify the port exists
        if not os.path.exists(self.detected_port):
            logger.warning(f"⚠️  Configured port {self.detected_port} does not exist!")
            logger.info("🔍 Falling back to auto-detection...")
            self.detected_port = self.auto_detect_fingerprint_port()
        
        # MQTT Topics
        self.SCAN_TOPIC = MQTT_TOPIC
        self.ADD_USER_TOPIC = "WHAC/Store001/add_user"
        self.IMPORT_TOPIC = "WHAC/Store001/import"
        self.EXPORT_TOPIC = "WHAC/Store001/export"
        self.ACTION_TOPIC = "WHAC/Store001/action"
        self.STATUS_TOPIC = "WHAC/Store001/relay_status"
        self.USER_MGMT_TOPIC = "WHAC/Store001/user_mgmt"  # New topic for user management
    
    def auto_detect_fingerprint_port(self):
        """Auto-detect AS608 fingerprint sensor port"""
        logger.info("🔍 Auto-detecting fingerprint sensor port...")
        
        if os.name == 'posix':  # Linux/Unix (Raspberry Pi)
            logger.info("📋 Scanning for available serial ports...")
            all_ports = []
            
            usb_patterns = ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/tty.usbserial*', '/dev/tty.usbmodem*']
            for pattern in usb_patterns:
                found_ports = glob.glob(pattern)
                all_ports.extend(found_ports)
                if found_ports:
                    logger.info(f"  Found USB ports: {found_ports}")
            
            builtin_patterns = ['/dev/ttyS*', '/dev/ttyAMA*', '/dev/serial0', '/dev/serial1']
            for pattern in builtin_patterns:
                if pattern.startswith('/dev/serial'):
                    if os.path.exists(pattern):
                        all_ports.append(pattern)
                        logger.info(f"  Found serial port: {pattern}")
                else:
                    found_ports = glob.glob(pattern)
                    all_ports.extend(found_ports)
                    if found_ports:
                        logger.info(f"  Found built-in ports: {found_ports}")
            
            possible_ports = sorted(list(set(all_ports)))
            logger.info(f"📋 Total available ports: {possible_ports}")
            
        elif os.name == 'nt':  # Windows
            try:
                import serial.tools.list_ports
                available_ports = [port.device for port in serial.tools.list_ports.comports()]
                possible_ports = available_ports
                logger.info(f"📋 Windows COM ports: {possible_ports}")
            except ImportError:
                possible_ports = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8"]
                logger.info(f"📋 Using default COM ports: {possible_ports}")
        else:
            possible_ports = [
                "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyUSB3",
                "/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2", "/dev/ttyACM3",
                "/dev/ttyS0", "/dev/ttyS1", "/dev/ttyS2", "/dev/ttyS3"
            ]
            logger.info(f"📋 Using fallback ports: {possible_ports}")
        
        if not possible_ports:
            logger.warning("⚠️  No serial ports found! Check your AS608 connection.")
            return FINGERPRINT_PORT
        
        # Prioritize the configured port if it exists
        if FINGERPRINT_PORT in possible_ports:
            possible_ports.remove(FINGERPRINT_PORT)
            possible_ports.insert(0, FINGERPRINT_PORT)
            logger.info(f"🎯 Prioritizing configured port: {FINGERPRINT_PORT}")
        
        logger.info(f"🔍 Testing {len(possible_ports)} ports for AS608 sensor...")
        
        for port in possible_ports:
            if not os.path.exists(port):
                logger.debug(f"  Port {port} does not exist, skipping")
                continue
                
            try:
                logger.info(f"🔌 Testing port: {port}")
                
                test_uart = serial.Serial(port, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)
                
                test_finger = adafruit_fingerprint.Adafruit_Fingerprint(test_uart)
                result = test_finger.read_templates()
                
                if result == adafruit_fingerprint.OK:
                    logger.info(f"✅ AS608 fingerprint sensor found on {port}!")
                    logger.info(f"   📊 Templates: {test_finger.template_count}")
                    test_uart.close()
                    return port
                else:
                    logger.debug(f"   ❌ Not an AS608 sensor on {port} (result: {result})")
                    test_uart.close()
                    
            except serial.SerialException as e:
                logger.debug(f"   ❌ Serial error on {port}: {e}")
                continue
            except Exception as e:
                logger.debug(f"   ❌ General error on {port}: {e}")
                continue
        
        logger.warning(f"⚠️  Auto-detection failed, using configured port: {FINGERPRINT_PORT}")
        return FINGERPRINT_PORT
    
    def connect_sensor(self, retries=3):
        """Connect to AS608 fingerprint sensor"""
        for attempt in range(retries):
            try:
                logger.info(f"Connecting to fingerprint sensor on {self.detected_port} (attempt {attempt + 1})")
                
                self.uart = serial.Serial(self.detected_port, baudrate=BAUD_RATE, timeout=2)
                time.sleep(0.5)
                self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)
                logger.info("✓ Sensor connected successfully!")
                return True
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self.uart:
                    self.uart.close()
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    raise
        return False
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client = mqtt.Client(client_id="whac_user_controller")
            
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.mqtt_client.loop_start()
            
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("✓ MQTT broker connected successfully!")
                self.mqtt_client.subscribe(self.ADD_USER_TOPIC, qos=MQTT_QOS)
                self.mqtt_client.subscribe(self.IMPORT_TOPIC, qos=MQTT_QOS)
                self.mqtt_client.subscribe(self.EXPORT_TOPIC, qos=MQTT_QOS)
                self.mqtt_client.subscribe(self.ACTION_TOPIC, qos=MQTT_QOS)
                self.mqtt_client.subscribe(self.USER_MGMT_TOPIC, qos=MQTT_QOS)
                logger.info(f"✓ Subscribed to command topics:")
                logger.info(f"  - {self.ADD_USER_TOPIC}")
                logger.info(f"  - {self.IMPORT_TOPIC}")
                logger.info(f"  - {self.EXPORT_TOPIC}")
                logger.info(f"  - {self.ACTION_TOPIC}")
                logger.info(f"  - {self.USER_MGMT_TOPIC}")
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
        """Handle incoming MQTT commands"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received command on {topic}: {payload}")
            
            if topic == self.ADD_USER_TOPIC:
                self.handle_add_user_command(payload)
            elif topic == self.IMPORT_TOPIC:
                self.handle_import_command(payload)
            elif topic == self.EXPORT_TOPIC:
                self.handle_export_command(payload)
            elif topic == self.ACTION_TOPIC:
                self.handle_relay_command(payload)
            elif topic == self.USER_MGMT_TOPIC:
                self.handle_user_mgmt_command(payload)
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def init_database(self):
        """Initialize SQLite database with backward compatibility"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if we need to migrate from simple schema to enhanced schema
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                logger.info("🔄 Migrating database schema to enhanced version...")
                self.migrate_database_schema(cursor)
            else:
                logger.info("✓ Database already has enhanced schema")
            
            # Create verification log table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint_id INTEGER,
                    user_name TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence INTEGER,
                    verification_result TEXT,
                    action_taken TEXT,
                    mqtt_sent BOOLEAN DEFAULT FALSE,
                    device_id TEXT,
                    store_id TEXT
                )
            ''')
            
            # Create system statistics table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    total_scans INTEGER DEFAULT 0,
                    successful_verifications INTEGER DEFAULT 0,
                    failed_verifications INTEGER DEFAULT 0,
                    mqtt_messages_sent INTEGER DEFAULT 0,
                    avg_confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_log_timestamp ON verification_log(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_log_fingerprint_id ON verification_log(fingerprint_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_stats_date ON system_stats(date)')
            
            # Add a test user if database is empty
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                cursor.execute("INSERT INTO users (fingerprint_id, user_name, user_id, department, access_level) VALUES (1, 'Test User', 'TEST001', 'IT', 1)")
                logger.info("✓ Added test user: Test User (ID: 1)")
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Database initialized: {self.db_file}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def migrate_database_schema(self, cursor):
        """Migrate from simple schema to enhanced schema"""
        try:
            # Create new table with enhanced schema
            cursor.execute('''
                CREATE TABLE users_new (
                    fingerprint_id INTEGER PRIMARY KEY,
                    user_name TEXT NOT NULL,
                    user_id TEXT,
                    department TEXT,
                    access_level INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_access TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    notes TEXT
                )
            ''')
            
            # Copy existing data
            cursor.execute('''
                INSERT INTO users_new (fingerprint_id, user_name, created_at)
                SELECT fingerprint_id, user_name, created_at FROM users
            ''')
            
            # Drop old table and rename new one
            cursor.execute('DROP TABLE users')
            cursor.execute('ALTER TABLE users_new RENAME TO users')
            
            logger.info("✓ Database schema migration completed")
            
        except Exception as e:
            logger.error(f"Database migration error: {e}")
            raise
    
    def handle_user_mgmt_command(self, payload):
        """Handle user management commands"""
        try:
            command = payload.get('command')
            data = payload.get('data', {})
            
            logger.info(f"Processing user management command: {command}")
            
            if command == 'list_users':
                self.handle_list_users_command(data)
            elif command == 'get_user_info':
                self.handle_get_user_info_command(data)
            elif command == 'update_user':
                self.handle_update_user_command(data)
            elif command == 'deactivate_user':
                self.handle_deactivate_user_command(data)
            elif command == 'activate_user':
                self.handle_activate_user_command(data)
            elif command == 'delete_user':
                self.handle_delete_user_command(data)
            elif command == 'get_user_stats':
                self.handle_get_user_stats_command(data)
            elif command == 'export_users':
                self.handle_export_users_command(data)
            elif command == 'get_verification_logs':
                self.handle_get_verification_logs_command(data)
            elif command == 'get_system_stats':
                self.handle_get_system_stats_command(data)
            else:
                logger.warning(f"Unknown user management command: {command}")
                self.send_user_mgmt_response(command, 'error', {'message': f'Unknown command: {command}'})
                
        except Exception as e:
            logger.error(f"Error handling user management command: {e}")
            self.send_user_mgmt_response('unknown', 'error', {'message': str(e)})
    
    def handle_list_users_command(self, data):
        """Handle list users command"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check which columns exist in the database
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Get filter parameters
            active_only = data.get('active_only', True)
            department = data.get('department')
            
            if 'user_id' in columns:
                # Enhanced schema
                query = '''
                    SELECT fingerprint_id, user_name, user_id, department, access_level, 
                           is_active, created_at, last_access, access_count
                    FROM users
                '''
                params = []
                
                conditions = []
                if active_only:
                    conditions.append('is_active = ?')
                    params.append(True)
                
                if department:
                    conditions.append('department = ?')
                    params.append(department)
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                
                query += ' ORDER BY fingerprint_id'
                
                cursor.execute(query, params)
                users = cursor.fetchall()
                
                # Format users data
                users_data = []
                for user in users:
                    users_data.append({
                        'fingerprint_id': user[0],
                        'user_name': user[1],
                        'user_id': user[2],
                        'department': user[3],
                        'access_level': user[4],
                        'is_active': bool(user[5]),
                        'created_at': user[6],
                        'last_access': user[7],
                        'access_count': user[8]
                    })
            else:
                # Simple schema (backward compatibility)
                query = '''
                    SELECT fingerprint_id, user_name, created_at
                    FROM users
                '''
                query += ' ORDER BY fingerprint_id'
                
                cursor.execute(query)
                users = cursor.fetchall()
                
                # Format users data with default values
                users_data = []
                for user in users:
                    users_data.append({
                        'fingerprint_id': user[0],
                        'user_name': user[1],
                        'user_id': None,
                        'department': None,
                        'access_level': 1,
                        'is_active': True,
                        'created_at': user[2],
                        'last_access': None,
                        'access_count': 0
                    })
            
            conn.close()
            
            self.send_user_mgmt_response('list_users', 'success', {
                'users': users_data,
                'total_count': len(users_data)
            })
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            self.send_user_mgmt_response('list_users', 'error', {'message': str(e)})
    
    def handle_get_user_info_command(self, data):
        """Handle get user info command"""
        try:
            fingerprint_id = data.get('fingerprint_id')
            if not fingerprint_id:
                self.send_user_mgmt_response('get_user_info', 'error', {'message': 'fingerprint_id required'})
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check which columns exist in the database
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Build query based on available columns
            if 'user_id' in columns:
                # Enhanced schema
                cursor.execute('''
                    SELECT fingerprint_id, user_name, user_id, department, access_level, 
                           is_active, created_at, updated_at, last_access, access_count, notes
                    FROM users WHERE fingerprint_id = ?
                ''', (fingerprint_id,))
                
                user = cursor.fetchone()
                if user:
                    user_data = {
                        'fingerprint_id': user[0],
                        'user_name': user[1],
                        'user_id': user[2],
                        'department': user[3],
                        'access_level': user[4],
                        'is_active': bool(user[5]),
                        'created_at': user[6],
                        'updated_at': user[7],
                        'last_access': user[8],
                        'access_count': user[9],
                        'notes': user[10]
                    }
                else:
                    user_data = None
            else:
                # Simple schema (backward compatibility)
                cursor.execute('''
                    SELECT fingerprint_id, user_name, created_at
                    FROM users WHERE fingerprint_id = ?
                ''', (fingerprint_id,))
                
                user = cursor.fetchone()
                if user:
                    user_data = {
                        'fingerprint_id': user[0],
                        'user_name': user[1],
                        'user_id': None,
                        'department': None,
                        'access_level': 1,
                        'is_active': True,
                        'created_at': user[2],
                        'updated_at': user[2],
                        'last_access': None,
                        'access_count': 0,
                        'notes': None
                    }
                else:
                    user_data = None
            
            conn.close()
            
            if user_data:
                self.send_user_mgmt_response('get_user_info', 'success', {'user': user_data})
            else:
                self.send_user_mgmt_response('get_user_info', 'error', {'message': 'User not found'})
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            self.send_user_mgmt_response('get_user_info', 'error', {'message': str(e)})
    
    def handle_update_user_command(self, data):
        """Handle update user command"""
        try:
            fingerprint_id = data.get('fingerprint_id')
            if not fingerprint_id:
                self.send_user_mgmt_response('update_user', 'error', {'message': 'fingerprint_id required'})
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT user_name FROM users WHERE fingerprint_id = ?', (fingerprint_id,))
            if not cursor.fetchone():
                conn.close()
                self.send_user_mgmt_response('update_user', 'error', {'message': 'User not found'})
                return
            
            # Check which columns exist in the database
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' in columns:
                # Enhanced schema - update fields
                update_fields = []
                params = []
                
                if 'user_name' in data:
                    update_fields.append('user_name = ?')
                    params.append(data['user_name'])
                
                if 'user_id' in data:
                    update_fields.append('user_id = ?')
                    params.append(data['user_id'])
                
                if 'department' in data:
                    update_fields.append('department = ?')
                    params.append(data['department'])
                
                if 'access_level' in data:
                    update_fields.append('access_level = ?')
                    params.append(data['access_level'])
                
                if 'notes' in data:
                    update_fields.append('notes = ?')
                    params.append(data['notes'])
                
                if update_fields:
                    update_fields.append('updated_at = CURRENT_TIMESTAMP')
                    params.append(fingerprint_id)
                    
                    query = f'UPDATE users SET {", ".join(update_fields)} WHERE fingerprint_id = ?'
                    cursor.execute(query, params)
                    conn.commit()
                    
                    logger.info(f"✓ Updated user: {fingerprint_id}")
                    self.send_user_mgmt_response('update_user', 'success', {
                        'message': 'User updated successfully',
                        'fingerprint_id': fingerprint_id
                    })
                else:
                    self.send_user_mgmt_response('update_user', 'error', {'message': 'No fields to update'})
            else:
                # Simple schema - only update user_name
                if 'user_name' in data:
                    cursor.execute('UPDATE users SET user_name = ? WHERE fingerprint_id = ?', 
                                 (data['user_name'], fingerprint_id))
                    conn.commit()
                    
                    logger.info(f"✓ Updated user name: {fingerprint_id}")
                    self.send_user_mgmt_response('update_user', 'success', {
                        'message': 'User name updated successfully',
                        'fingerprint_id': fingerprint_id
                    })
                else:
                    self.send_user_mgmt_response('update_user', 'error', {'message': 'Only user_name can be updated in simple schema'})
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            self.send_user_mgmt_response('update_user', 'error', {'message': str(e)})
    
    def handle_deactivate_user_command(self, data):
        """Handle deactivate user command"""
        try:
            fingerprint_id = data.get('fingerprint_id')
            if not fingerprint_id:
                self.send_user_mgmt_response('deactivate_user', 'error', {'message': 'fingerprint_id required'})
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check which columns exist in the database
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_active' in columns:
                cursor.execute('UPDATE users SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE fingerprint_id = ?', (fingerprint_id,))
            else:
                # Simple schema - cannot deactivate, just return error
                conn.close()
                self.send_user_mgmt_response('deactivate_user', 'error', {'message': 'User deactivation not supported in simple schema'})
                return
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"✓ Deactivated user: {fingerprint_id}")
                self.send_user_mgmt_response('deactivate_user', 'success', {
                    'message': 'User deactivated successfully',
                    'fingerprint_id': fingerprint_id
                })
            else:
                self.send_user_mgmt_response('deactivate_user', 'error', {'message': 'User not found'})
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            self.send_user_mgmt_response('deactivate_user', 'error', {'message': str(e)})
    
    def handle_activate_user_command(self, data):
        """Handle activate user command"""
        try:
            fingerprint_id = data.get('fingerprint_id')
            if not fingerprint_id:
                self.send_user_mgmt_response('activate_user', 'error', {'message': 'fingerprint_id required'})
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check which columns exist in the database
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_active' in columns:
                cursor.execute('UPDATE users SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP WHERE fingerprint_id = ?', (fingerprint_id,))
            else:
                # Simple schema - all users are active by default
                conn.close()
                self.send_user_mgmt_response('activate_user', 'success', {
                    'message': 'User is active (simple schema)',
                    'fingerprint_id': fingerprint_id
                })
                return
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"✓ Activated user: {fingerprint_id}")
                self.send_user_mgmt_response('activate_user', 'success', {
                    'message': 'User activated successfully',
                    'fingerprint_id': fingerprint_id
                })
            else:
                self.send_user_mgmt_response('activate_user', 'error', {'message': 'User not found'})
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error activating user: {e}")
            self.send_user_mgmt_response('activate_user', 'error', {'message': str(e)})
    
    def handle_delete_user_command(self, data):
        """Handle delete user command"""
        try:
            fingerprint_id = data.get('fingerprint_id')
            if not fingerprint_id:
                self.send_user_mgmt_response('delete_user', 'error', {'message': 'fingerprint_id required'})
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get user info before deletion
            cursor.execute('SELECT user_name FROM users WHERE fingerprint_id = ?', (fingerprint_id,))
            user = cursor.fetchone()
            
            if user:
                # Delete verification logs first (if table exists)
                try:
                    cursor.execute('DELETE FROM verification_log WHERE fingerprint_id = ?', (fingerprint_id,))
                except:
                    pass  # Table might not exist
                
                # Delete user
                cursor.execute('DELETE FROM users WHERE fingerprint_id = ?', (fingerprint_id,))
                
                conn.commit()
                logger.info(f"✓ Deleted user: {fingerprint_id} ({user[0]})")
                self.send_user_mgmt_response('delete_user', 'success', {
                    'message': f'User {user[0]} deleted successfully',
                    'fingerprint_id': fingerprint_id
                })
            else:
                self.send_user_mgmt_response('delete_user', 'error', {'message': 'User not found'})
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            self.send_user_mgmt_response('delete_user', 'error', {'message': str(e)})
    
    def handle_get_user_stats_command(self, data):
        """Handle get user stats command"""
        try:
            fingerprint_id = data.get('fingerprint_id')
            days = data.get('days', 30)
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if verification_log table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verification_log'")
            has_verification_log = cursor.fetchone() is not None
            
            if has_verification_log:
                if fingerprint_id:
                    # Get stats for specific user
                    cursor.execute('''
                        SELECT COUNT(*) as total_scans,
                               COUNT(CASE WHEN verification_result = 'Match' THEN 1 END) as successful_scans,
                               COUNT(CASE WHEN verification_result = 'No Match' THEN 1 END) as failed_scans,
                               AVG(confidence) as avg_confidence,
                               MAX(timestamp) as last_scan
                        FROM verification_log 
                        WHERE fingerprint_id = ? AND timestamp >= datetime('now', '-{} days')
                    '''.format(days), (fingerprint_id,))
                    
                    stats = cursor.fetchone()
                    
                    if stats:
                        user_stats = {
                            'fingerprint_id': fingerprint_id,
                            'total_scans': stats[0],
                            'successful_scans': stats[1],
                            'failed_scans': stats[2],
                            'avg_confidence': round(stats[3], 2) if stats[3] else 0,
                            'last_scan': stats[4],
                            'success_rate': round((stats[1] / stats[0] * 100), 2) if stats[0] > 0 else 0
                        }
                        self.send_user_mgmt_response('get_user_stats', 'success', {'stats': user_stats})
                    else:
                        self.send_user_mgmt_response('get_user_stats', 'error', {'message': 'No stats found for user'})
                else:
                    # Get overall system stats
                    cursor.execute('''
                        SELECT COUNT(*) as total_scans,
                               COUNT(CASE WHEN verification_result = 'Match' THEN 1 END) as successful_scans,
                               COUNT(CASE WHEN verification_result = 'No Match' THEN 1 END) as failed_scans,
                               AVG(confidence) as avg_confidence,
                               COUNT(DISTINCT fingerprint_id) as unique_users
                        FROM verification_log 
                        WHERE timestamp >= datetime('now', '-{} days')
                    '''.format(days))
                    
                    stats = cursor.fetchone()
                    
                    if stats:
                        system_stats = {
                            'total_scans': stats[0],
                            'successful_scans': stats[1],
                            'failed_scans': stats[2],
                            'avg_confidence': round(stats[3], 2) if stats[3] else 0,
                            'unique_users': stats[4],
                            'success_rate': round((stats[1] / stats[0] * 100), 2) if stats[0] > 0 else 0
                        }
                        self.send_user_mgmt_response('get_user_stats', 'success', {'stats': system_stats})
                    else:
                        self.send_user_mgmt_response('get_user_stats', 'error', {'message': 'No stats found'})
            else:
                # No verification log table - return basic user count
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                basic_stats = {
                    'total_users': user_count,
                    'message': 'No verification logs available - basic stats only'
                }
                self.send_user_mgmt_response('get_user_stats', 'success', {'stats': basic_stats})
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            self.send_user_mgmt_response('get_user_stats', 'error', {'message': str(e)})
    
    def handle_export_users_command(self, data):
        """Handle export users command"""
        try:
            format_type = data.get('format', 'json')
            active_only = data.get('active_only', True)
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check which columns exist in the database
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' in columns:
                # Enhanced schema
                query = '''
                    SELECT fingerprint_id, user_name, user_id, department, access_level, 
                           is_active, created_at, last_access, access_count, notes
                    FROM users
                '''
                params = []
                
                if active_only:
                    query += ' WHERE is_active = ?'
                    params.append(True)
                
                query += ' ORDER BY fingerprint_id'
                
                cursor.execute(query, params)
                users = cursor.fetchall()
                
                if format_type == 'csv':
                    # Export to CSV
                    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Fingerprint ID', 'User Name', 'User ID', 'Department', 
                                       'Access Level', 'Active', 'Created At', 'Last Access', 'Access Count', 'Notes'])
                        
                        for user in users:
                            writer.writerow(user)
                    
                    self.send_user_mgmt_response('export_users', 'success', {
                        'message': f'Users exported to {filename}',
                        'filename': filename,
                        'count': len(users)
                    })
                else:
                    # Export to JSON
                    users_data = []
                    for user in users:
                        users_data.append({
                            'fingerprint_id': user[0],
                            'user_name': user[1],
                            'user_id': user[2],
                            'department': user[3],
                            'access_level': user[4],
                            'is_active': bool(user[5]),
                            'created_at': user[6],
                            'last_access': user[7],
                            'access_count': user[8],
                            'notes': user[9]
                        })
                    
                    self.send_user_mgmt_response('export_users', 'success', {
                        'users': users_data,
                        'count': len(users_data)
                    })
            else:
                # Simple schema
                query = 'SELECT fingerprint_id, user_name, created_at FROM users ORDER BY fingerprint_id'
                cursor.execute(query)
                users = cursor.fetchall()
                
                if format_type == 'csv':
                    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Fingerprint ID', 'User Name', 'Created At'])
                        
                        for user in users:
                            writer.writerow(user)
                    
                    self.send_user_mgmt_response('export_users', 'success', {
                        'message': f'Users exported to {filename} (simple schema)',
                        'filename': filename,
                        'count': len(users)
                    })
                else:
                    users_data = []
                    for user in users:
                        users_data.append({
                            'fingerprint_id': user[0],
                            'user_name': user[1],
                            'created_at': user[2]
                        })
                    
                    self.send_user_mgmt_response('export_users', 'success', {
                        'users': users_data,
                        'count': len(users_data)
                    })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error exporting users: {e}")
            self.send_user_mgmt_response('export_users', 'error', {'message': str(e)})
    
    def handle_get_verification_logs_command(self, data):
        """Handle get verification logs command with filtering and sorting"""
        try:
            # Get filter parameters
            fingerprint_id = data.get('fingerprint_id')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            limit = data.get('limit', 100)
            offset = data.get('offset', 0)
            sort_by = data.get('sort_by', 'timestamp')
            sort_order = data.get('sort_order', 'DESC')
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if verification_log table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verification_log'")
            has_verification_log = cursor.fetchone() is not None
            
            if not has_verification_log:
                conn.close()
                self.send_user_mgmt_response('get_verification_logs', 'error', {'message': 'Verification log table not found'})
                return
            
            query = '''
                SELECT vl.id, vl.fingerprint_id, vl.user_name, vl.timestamp, 
                       vl.confidence, vl.verification_result, vl.action_taken, 
                       vl.mqtt_sent, vl.device_id, vl.store_id
                FROM verification_log vl
            '''
            params = []
            conditions = []
            
            if fingerprint_id:
                conditions.append('vl.fingerprint_id = ?')
                params.append(fingerprint_id)
            
            if start_date:
                conditions.append('vl.timestamp >= ?')
                params.append(start_date)
            
            if end_date:
                conditions.append('vl.timestamp <= ?')
                params.append(end_date)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            # Add sorting
            valid_sort_columns = ['timestamp', 'fingerprint_id', 'confidence', 'verification_result']
            if sort_by in valid_sort_columns:
                query += f' ORDER BY vl.{sort_by} {sort_order}'
            else:
                query += ' ORDER BY vl.timestamp DESC'
            
            # Add pagination
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            # Get total count
            count_query = 'SELECT COUNT(*) FROM verification_log vl'
            if conditions:
                count_query += ' WHERE ' + ' AND '.join(conditions)
            
            cursor.execute(count_query, params[:-2])  # Remove limit and offset
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            # Format logs data
            logs_data = []
            for log in logs:
                logs_data.append({
                    'id': log[0],
                    'fingerprint_id': log[1],
                    'user_name': log[2],
                    'timestamp': log[3],
                    'confidence': log[4],
                    'verification_result': log[5],
                    'action_taken': log[6],
                    'mqtt_sent': bool(log[7]),
                    'device_id': log[8],
                    'store_id': log[9]
                })
            
            self.send_user_mgmt_response('get_verification_logs', 'success', {
                'logs': logs_data,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            })
            
        except Exception as e:
            logger.error(f"Error getting verification logs: {e}")
            self.send_user_mgmt_response('get_verification_logs', 'error', {'message': str(e)})
    
    def handle_get_system_stats_command(self, data):
        """Handle get system stats command"""
        try:
            days = data.get('days', 30)
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if system_stats table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_stats'")
            has_system_stats = cursor.fetchone() is not None
            
            if has_system_stats:
                # Get daily stats
                cursor.execute('''
                    SELECT date, total_scans, successful_verifications, failed_verifications,
                           mqtt_messages_sent, avg_confidence
                    FROM system_stats 
                    WHERE date >= date('now', '-{} days')
                    ORDER BY date DESC
                '''.format(days))
                
                daily_stats = cursor.fetchall()
                
                # Get overall stats
                cursor.execute('''
                    SELECT COUNT(*) as total_users,
                           COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
                           COUNT(CASE WHEN is_active = 0 THEN 1 END) as inactive_users
                    FROM users
                ''')
                
                user_stats = cursor.fetchone()
                
                # Format daily stats
                daily_data = []
                for stat in daily_stats:
                    daily_data.append({
                        'date': stat[0],
                        'total_scans': stat[1],
                        'successful_verifications': stat[2],
                        'failed_verifications': stat[3],
                        'mqtt_messages_sent': stat[4],
                        'avg_confidence': round(stat[5], 2) if stat[5] else 0
                    })
                
                system_stats = {
                    'total_users': user_stats[0],
                    'active_users': user_stats[1],
                    'inactive_users': user_stats[2],
                    'daily_stats': daily_data
                }
            else:
                # No system stats table - return basic info
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                system_stats = {
                    'total_users': user_count,
                    'active_users': user_count,
                    'inactive_users': 0,
                    'daily_stats': [],
                    'message': 'No system statistics available - basic info only'
                }
            
            conn.close()
            
            self.send_user_mgmt_response('get_system_stats', 'success', {'stats': system_stats})
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            self.send_user_mgmt_response('get_system_stats', 'error', {'message': str(e)})
    
    def send_user_mgmt_response(self, command, status, data):
        """Send user management response back to MQTT"""
        try:
            response = {
                "store_id": STORE_ID,
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "status": status,
                "data": data,
                "device_id": "AS608_001"
            }
            
            response_topic = f"WHAC/Store001/user_mgmt_response"
            payload = json.dumps(response)
            result = self.mqtt_client.publish(response_topic, payload, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ User management response sent: {command} - {status}")
            else:
                logger.error(f"✗ Failed to send user management response (rc: {result.rc})")
                
        except Exception as e:
            logger.error(f"Error sending user management response: {e}")
    
    def handle_add_user_command(self, payload):
        """Handle add user command (inherited from simple client)"""
        # This would be the same implementation as in fingerprint_simple_client.py
        # For brevity, I'm not duplicating the entire method here
        pass
    
    def handle_import_command(self, payload):
        """Handle import command (inherited from simple client)"""
        # This would be the same implementation as in fingerprint_simple_client.py
        pass
    
    def handle_export_command(self, payload):
        """Handle export command (inherited from simple client)"""
        # This would be the same implementation as in fingerprint_simple_client.py
        pass
    
    def handle_relay_command(self, payload):
        """Handle relay command (inherited from simple client)"""
        # This would be the same implementation as in fingerprint_simple_client.py
        pass
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        self.running = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        
        if self.uart:
            self.uart.close()
            logger.info("Serial connection closed")

def main():
    """Main function"""
    controller = FingerprintUserController()
    
    try:
        # Connect to fingerprint sensor
        if not controller.connect_sensor():
            logger.error("Failed to connect to fingerprint sensor")
            return 1
        
        # Connect to MQTT broker
        if not controller.connect_mqtt():
            logger.error("Failed to connect to MQTT broker")
            return 1
        
        logger.info("=" * 70)
        logger.info("FINGERPRINT USER CONTROLLER - Ready!")
        logger.info("=" * 70)
        logger.info(f"Store ID: {STORE_ID}")
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        logger.info(f"Fingerprint Port: {controller.detected_port}")
        logger.info(f"User Management Topic: {controller.USER_MGMT_TOPIC}")
        logger.info("=" * 70)
        logger.info("✓ User management commands active")
        logger.info("✓ Enhanced logging and reporting available")
        logger.info("=" * 70)
        
        # Keep the program running to handle MQTT commands
        try:
            while controller.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Controller stopped by user")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        controller.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
