#!/usr/bin/env python3
"""
Web UI for WHAC Fingerprint System
Displays fingerprint data from PostgreSQL database
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from functools import wraps
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import json
import logging
import pytz
import paho.mqtt.client as mqtt
import threading
import bcrypt
import secrets
import hashlib
import os
from enrollment_manager import enrollment_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'whac_fingerprint_secret_key')
app.config['DEBUG'] = False  # Explicitly disable debug mode

# Initialize SocketIO with explicit async_mode for thread compatibility
# async_mode='threading' is required for MQTT background thread communication
socketio = SocketIO(app, 
                    cors_allowed_origins="*",
                    async_mode='threading',
                    logger=False,
                    engineio_logger=False)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'whac_master'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Admin123'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# MQTT configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', '103.87.67.139')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_ACTION_TOPIC = os.getenv('MQTT_ACTION_TOPIC', 'WHAC/Store001/action')
MQTT_SCAN_TOPIC = os.getenv('MQTT_SCAN_TOPIC', 'WHAC/Store001/in')
MQTT_AUDIO_TOPIC = os.getenv('MQTT_AUDIO_TOPIC', 'WHAC/Store001/audio')
MQTT_AUDIO_RESPONSE_TOPIC = os.getenv('MQTT_AUDIO_RESPONSE_TOPIC', 'WHAC/Store001/audio_response')
MQTT_DOOR_STATUS_TOPIC = os.getenv('MQTT_DOOR_STATUS_TOPIC', 'WHAC/Store001/door_status')
MQTT_GPIO_LOG_TOPIC = os.getenv('MQTT_GPIO_LOG_TOPIC', 'WHAC/Store001/gpio_log')

# Global MQTT client
mqtt_client = None
mqtt_reconnect_attempts = 0
MAX_RECONNECT_ATTEMPTS = 5

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def setup_mqtt_client():
    """Setup MQTT client for receiving scan notifications"""
    global mqtt_client
    
    # Prevent multiple MQTT client instances
    if mqtt_client is not None:
        logger.warning("⚠️  MQTT client already exists, cleaning up previous instance...")
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        except:
            pass
        mqtt_client = None
    
    try:
        # Use unique client ID with timestamp to avoid conflicts
        # clean_session=False to maintain subscription state during reconnections
        import time
        unique_client_id = f"whac_web_ui_{int(time.time())}"
        mqtt_client = mqtt.Client(client_id=unique_client_id, clean_session=False)
        
        # Configure connection options for better stability
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.on_disconnect = on_mqtt_disconnect
        
        # Set keepalive to 60 seconds to reduce disconnections
        # Add connection options for better stability
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Enable automatic reconnection
        mqtt_client.enable_logger(logger)
        
        # Start the loop with better error handling
        mqtt_client.loop_start()
        logger.info("✓ MQTT client connected for real-time notifications")
    except Exception as e:
        logger.error(f"MQTT client setup error: {e}")

def on_mqtt_disconnect(client, userdata, rc):
    """MQTT disconnection callback"""
    global mqtt_reconnect_attempts
    
    if rc == 0:
        # Normal disconnection (client requested)
        logger.info("🔌 MQTT client disconnected normally")
        mqtt_reconnect_attempts = 0  # Reset counter on normal disconnect
    else:
        # Unexpected disconnection
        logger.warning(f"⚠️  MQTT client disconnected unexpectedly (code: {rc})")
        
        # Code 7 = Connection lost, but don't panic - it might be a false alarm
        if rc == 7:
            logger.info("ℹ️  Code 7: Connection lost - this may be a network hiccup")
            logger.info("ℹ️  Will verify connection status before next command")
            
            # For Code 7, only reconnect if we haven't reconnected recently
            # This prevents connection storms on unstable networks
            import time
            current_time = time.time()
            
            # Only reconnect if it's been more than 30 seconds since last reconnection
            if not hasattr(on_mqtt_disconnect, 'last_reconnect_time'):
                on_mqtt_disconnect.last_reconnect_time = 0
            
            if current_time - on_mqtt_disconnect.last_reconnect_time > 30:
                on_mqtt_disconnect.last_reconnect_time = current_time
                logger.info("🔄 Code 7: Scheduling reconnection after 30s cooldown...")
                
                def delayed_reconnect():
                    time.sleep(30)
                    ensure_mqtt_connection()
                
                import threading
                threading.Thread(target=delayed_reconnect, daemon=True).start()
            else:
                logger.info("ℹ️  Code 7: Skipping reconnection (too recent)")
        else:
            logger.warning("MQTT connection lost - will attempt to reconnect on next command")
            
            # Increment reconnect attempts counter for non-Code 7 disconnections
            mqtt_reconnect_attempts += 1
            
            # Schedule automatic reconnection with exponential backoff
            if mqtt_reconnect_attempts <= MAX_RECONNECT_ATTEMPTS:
                import threading
                import time
                
                # Calculate backoff delay: 2^attempts seconds, max 60 seconds
                delay = min(2 ** mqtt_reconnect_attempts, 60)
                logger.info(f"🔄 Scheduling MQTT reconnection in {delay} seconds (attempt {mqtt_reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS})")
                
                def delayed_reconnect():
                    time.sleep(delay)
                    ensure_mqtt_connection()
                
                threading.Thread(target=delayed_reconnect, daemon=True).start()
            else:
                logger.error(f"❌ Max reconnection attempts ({MAX_RECONNECT_ATTEMPTS}) reached. Manual intervention required.")

def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    global mqtt_reconnect_attempts
    
    if rc == 0:
        logger.info("✅ Web UI MQTT client connected successfully")
        
        # Reset reconnection counter on successful connection
        mqtt_reconnect_attempts = 0
        
        # Subscribe to scan notifications
        client.subscribe(MQTT_SCAN_TOPIC, qos=1)
        logger.info(f"✅ Web UI subscribed to topic: {MQTT_SCAN_TOPIC} (QoS 1)")
        
        # Subscribe to enrollment responses
        client.subscribe("WHAC/Store001/add_user_response", qos=1)
        logger.info(f"✅ Web UI subscribed to topic: WHAC/Store001/add_user_response (QoS 1)")
        
        # Subscribe to audio responses
        client.subscribe(MQTT_AUDIO_RESPONSE_TOPIC, qos=1)
        logger.info(f"✅ Web UI subscribed to topic: {MQTT_AUDIO_RESPONSE_TOPIC} (QoS 1)")
        
        # Subscribe to door status updates
        client.subscribe(MQTT_DOOR_STATUS_TOPIC, qos=1)
        logger.info(f"✅ Web UI subscribed to topic: {MQTT_DOOR_STATUS_TOPIC} (QoS 1)")
        
        # Subscribe to GPIO log updates
        client.subscribe(MQTT_GPIO_LOG_TOPIC, qos=1)
        logger.info(f"✅ Web UI subscribed to topic: {MQTT_GPIO_LOG_TOPIC} (QoS 1)")
        
        logger.info("🔔 Web UI is now listening for scan notifications, enrollment responses, door status updates, and GPIO logs...")
    else:
        logger.error(f"❌ Web UI MQTT connection failed with code {rc}")

def emit_scan_notification_task(scan_data):
    """Background task to emit scan notification via WebSocket"""
    try:
        logger.info("=" * 80)
        logger.info(f"🎯 BACKGROUND TASK STARTED - SCAN NOTIFICATION")
        logger.info(f"📊 Thread: {threading.current_thread().name}")
        logger.info(f"📊 Thread ID: {threading.current_thread().ident}")
        logger.info(f"📦 Scan data to emit: {scan_data}")
        
        # Sleep briefly to ensure task is running in proper context
        socketio.sleep(0.01)
        
        # Emit from background task context
        logger.info("🚀 Calling socketio.emit() now...")
        socketio.emit('scan_notification', scan_data, namespace='/')
        logger.info("✅ socketio.emit() call completed!")
        
        # Force flush
        socketio.sleep(0.01)
        logger.info("✅ BACKGROUND TASK COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ BACKGROUND TASK ERROR: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
        logger.error("=" * 80)

def emit_notification_task(notification_data):
    """Background task to emit general notifications via WebSocket"""
    try:
        logger.info(f"🎯 BACKGROUND TASK - NOTIFICATION: {notification_data.get('type')}")
        
        socketio.sleep(0.01)
        socketio.emit('enrollment_notification', notification_data, namespace='/')
        socketio.sleep(0.01)
        
        logger.info("✅ Notification emitted successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error emitting notification: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

def on_mqtt_message(client, userdata, msg):
    """Handle incoming MQTT messages"""
    try:
        logger.info("=" * 80)
        logger.info(f"📨 Web UI received MQTT message on topic: {msg.topic}")
        logger.info(f"📦 Raw payload: {msg.payload.decode()}")
        
        payload = json.loads(msg.payload.decode())
        logger.info(f"📋 Parsed JSON payload: {payload}")
        
        # Route to appropriate handler based on topic
        if msg.topic == MQTT_SCAN_TOPIC:
            # Handle scan notifications
            handle_scan_message(payload)
        elif msg.topic == "WHAC/Store001/add_user_response":
            # Handle enrollment responses (both success/error and progress)
            if payload.get('status') == 'progress':
                handle_enrollment_progress(payload)
            else:
                handle_enrollment_response(payload)
        elif msg.topic == MQTT_DOOR_STATUS_TOPIC:
            # Handle door status updates
            handle_door_status_message(payload)
        elif msg.topic == MQTT_GPIO_LOG_TOPIC:
            # Handle GPIO log updates
            handle_gpio_log_message(payload)
        else:
            logger.warning(f"⚠️  Unknown topic: {msg.topic}")
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error processing MQTT message: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

def handle_scan_message(payload):
    """Handle fingerprint scan messages with verification"""
    try:
        fingerprint_id = payload.get('fingerprint_id')
        device_id = payload.get('device_id')
        status = payload.get('status')  # "Match" or "Not Match"
        
        # For "Not Match" with fingerprint_id = 0, treat as unverified scan
        # This means a fingerprint was scanned but not found in database
        if status == "Not Match" and (fingerprint_id == 0 or fingerprint_id is None):
            # This is an unverified scan - no user found
            user_info = None
            is_verified = False
            # Generate a temporary ID for tracking this unverified scan
            # Use timestamp-based ID to track this specific scan attempt
            import time
            temp_scan_id = int(time.time() * 1000) % 1000000  # Use last 6 digits of timestamp
        else:
            # Check if user is registered in user_machine table
            user_info = check_user_in_user_machine(fingerprint_id, device_id)
            is_verified = user_info is not None
            temp_scan_id = None
        
        # Process the scan data and log to database
        process_incoming_scan(payload)
        
        # Format scan data for WebSocket with verification status
        scan_data = {
            'user_id': fingerprint_id if fingerprint_id and fingerprint_id > 0 else temp_scan_id,
            'fingerprint_id': fingerprint_id if fingerprint_id and fingerprint_id > 0 else temp_scan_id,
            'status': status,
            'username': user_info.get('nama') if user_info else payload.get('username'),
            'confidence': payload.get('confidence'),
            'timestamp': payload.get('timestamp'),
            'store_id': payload.get('store_id'),
            'device_id': device_id,
            'is_verified': is_verified,  # New field: apakah user terdaftar
            'user_info': user_info,  # Info user jika terdaftar
            'is_unverified_scan': status == "Not Match" and (fingerprint_id == 0 or fingerprint_id is None)  # Flag untuk scan tidak terdaftar
        }
        
        logger.info(f"🔄 Formatted scan data for WebSocket: {scan_data}")
        logger.info(f"📊 Verification status: {'VERIFIED' if is_verified else 'NOT VERIFIED'}")
        logger.info(f"📊 MQTT Thread: {threading.current_thread().name}")
        
        # Use SocketIO background task to emit from MQTT thread
        logger.info("🚀 Starting background task to emit WebSocket event...")
        socketio.start_background_task(emit_scan_notification_task, scan_data)
        logger.info("✅ Background task started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error handling scan message: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

def handle_enrollment_progress(payload):
    """Handle enrollment progress updates from local machine"""
    try:
        data = payload.get('data', {})
        enrollment_id = data.get('enrollment_id') or payload.get('enrollment_id')
        progress = data.get('progress', 0)
        progress_message = data.get('progress_message', '')
        status = data.get('status', 'in_progress')
        
        if enrollment_id:
            enrollment_manager.update_enrollment_status(
                enrollment_id,
                status,
                progress=progress,
                progress_message=progress_message,
                device_id=data.get('device_id')
            )
            
            logger.info(f"📊 Enrollment progress: {enrollment_id} - {progress}% - {progress_message}")
            
            # Emit progress update to WebSocket
            notification_data = {
                'type': 'enrollment_progress',
                'enrollment_id': enrollment_id,
                'progress': progress,
                'progress_message': progress_message,
                'status': status,
                'device_id': data.get('device_id'),
                'timestamp': datetime.now().isoformat()
            }
            
            socketio.start_background_task(emit_notification_task, notification_data)
        
    except Exception as e:
        logger.error(f"Error handling enrollment progress: {e}")

def handle_enrollment_response(payload):
    """Handle enrollment response from local machine
    
    FIXED: Enhanced notification with better error handling and ensured
    modal popup always appears for successful enrollments.
    """
    try:
        logger.info("=" * 80)
        logger.info("📥 ENROLLMENT RESPONSE RECEIVED")
        logger.info(f"   Status: {payload.get('status')}")
        logger.info(f"   Message: {payload.get('data', {}).get('message')}")
        logger.info(f"   Full payload: {payload}")
        
        status = payload.get('status')
        data = payload.get('data', {})
        fingerprint_id = data.get('fingerprint_id')
        user_name = data.get('user_name')
        device_id = data.get('device_id', 'AS608_001')  # Default to AS608_001 if not provided
        
        # Debug logging
        logger.info(f"🔍 Parsing enrollment response:")
        logger.info(f"   status: {status}")
        logger.info(f"   data: {data}")
        logger.info(f"   fingerprint_id: {fingerprint_id} (type: {type(fingerprint_id)})")
        logger.info(f"   user_name: {user_name} (type: {type(user_name)})")
        logger.info(f"   device_id: {device_id}")
        
        # Find active enrollment for this user
        # Try to find by enrollment_id first (from response), then by user_id
        enrollment_id_from_response = data.get('enrollment_id') or payload.get('enrollment_id')
        active_enrollment = None
        
        if enrollment_id_from_response:
            active_enrollment = enrollment_manager.get_enrollment_status(enrollment_id_from_response)
            enrollment_id = enrollment_id_from_response
        elif fingerprint_id:
            active_enrollment = enrollment_manager.get_enrollment_by_user_id(fingerprint_id)
            enrollment_id = active_enrollment['enrollment_id'] if active_enrollment else None
        else:
            enrollment_id = None
        
        logger.info(f"   Found enrollment: {active_enrollment is not None}, enrollment_id: {enrollment_id}")
        
        # Determine sensor_location based on device_id
        sensor_location = None
        if device_id == 'AS608_001':
            sensor_location = 'masuk'
        elif device_id == 'AS608_002':
            sensor_location = 'keluar'
        
        # Check if this is a success response
        # Allow fingerprint_id to be 0 or None for debugging, but user_name must exist
        is_success = status == 'success' and user_name
        
        logger.info(f"🔍 Enrollment response check:")
        logger.info(f"   status == 'success': {status == 'success'}")
        logger.info(f"   user_name exists: {bool(user_name)}")
        logger.info(f"   fingerprint_id: {fingerprint_id}")
        logger.info(f"   is_success: {is_success}")
        
        if is_success and fingerprint_id:
            # Update enrollment status
            if enrollment_id:
                enrollment_manager.update_enrollment_status(
                    enrollment_id,
                    'in_progress',
                    device_id=device_id,
                    sensor_location=sensor_location,
                    progress=50,
                    progress_message='Enrollment successful, saving to database...'
                )
            # Add user to PostgreSQL database with device_id support
            conn = get_db_connection()
            db_success = False
            db_error_msg = None
            
            if conn:
                try:
                    cursor = conn.cursor()
                    # Determine which sensor table to use based on device_id
                    table_name = get_sensor_table_name(device_id)
                    
                    cursor.execute(f"""
                        INSERT INTO {table_name} (user_id, username, finger_template_id)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            username = EXCLUDED.username,
                            finger_template_id = EXCLUDED.finger_template_id,
                            updated_at = CURRENT_TIMESTAMP
                    """, (fingerprint_id, user_name, fingerprint_id))
                    
                    logger.info(f"✅ User added to {table_name}: {user_name} (ID: {fingerprint_id})")
                    
                    # Also add to user_machine table
                    cursor.execute("""
                        INSERT INTO user_machine (user_id, nama, device_id, posisi, finger_template_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, device_id) DO UPDATE SET
                            nama = EXCLUDED.nama,
                            finger_template_id = EXCLUDED.finger_template_id,
                            updated_at = CURRENT_TIMESTAMP
                    """, (fingerprint_id, user_name, device_id, '', fingerprint_id))
                    
                    conn.commit()
                    conn.close()
                    db_success = True
                    
                    logger.info(f"✅ User added to PostgreSQL database: {user_name} (ID: {fingerprint_id}, Device: {device_id}, Location: {sensor_location}, Table: {table_name})")
                    
                except Exception as db_error:
                    logger.error(f"❌ Error adding user to database: {db_error}")
                    db_error_msg = str(db_error)
                    conn.rollback()
                    conn.close()
            else:
                logger.error("❌ Failed to connect to database")
                db_error_msg = "Database connection failed"
            
            # Update enrollment status to success
            if enrollment_id:
                enrollment_manager.complete_enrollment(
                    enrollment_id,
                    success=db_success,
                    device_id=device_id,
                    sensor_location=sensor_location,
                    progress=100 if db_success else 50,
                    progress_message='Enrollment completed' if db_success else f'Database error: {db_error_msg}',
                    error_message=None if db_success else db_error_msg
                )
            
            # Emit success notification to web UI (even if DB failed, enrollment was successful)
            if db_success:
                notification_data = {
                    'type': 'enrollment_success',
                    'message': f'User {user_name} enrolled successfully on {device_id} ({sensor_location or "unknown"})!',
                    'user_id': fingerprint_id,
                    'username': user_name,
                    'fingerprint_id': fingerprint_id,
                    'device_id': device_id,
                    'sensor_location': sensor_location,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Enrollment succeeded but database failed
                notification_data = {
                    'type': 'enrollment_success_db_error',
                    'message': f'User {user_name} enrolled but database save failed: {db_error_msg}',
                    'user_id': fingerprint_id,
                    'username': user_name,
                    'fingerprint_id': fingerprint_id,
                    'error': db_error_msg,
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"📤 Emitting enrollment notification: {notification_data['type']}")
            socketio.start_background_task(emit_notification_task, notification_data)
            logger.info("=" * 80)
            
        elif is_success and not fingerprint_id:
            # Success but missing fingerprint_id - try to extract from enrollment
            logger.warning(f"⚠️  Success response but missing fingerprint_id, trying to extract from enrollment...")
            if active_enrollment:
                fingerprint_id = active_enrollment.get('user_id')
                logger.info(f"   Extracted fingerprint_id from enrollment: {fingerprint_id}")
                # Retry with extracted fingerprint_id
                if fingerprint_id:
                    # Recursively call with extracted data
                    data['fingerprint_id'] = fingerprint_id
                    handle_enrollment_response(payload)
                    return
            else:
                error_message = "Success response but missing fingerprint_id and no active enrollment found"
                logger.error(f"❌ {error_message}")
                notification_data = {
                    'type': 'enrollment_error',
                    'message': error_message,
                    'error': error_message,
                    'enrollment_id': enrollment_id,
                    'timestamp': datetime.now().isoformat()
                }
                socketio.start_background_task(emit_notification_task, notification_data)
        else:
            error_message = data.get('message', 'Unknown error')
            logger.error(f"❌ Enrollment failed: {error_message}")
            logger.error(f"   Status: {status}, fingerprint_id: {fingerprint_id}, user_name: {user_name}")
            
            # Update enrollment status to error
            if enrollment_id:
                enrollment_manager.complete_enrollment(
                    enrollment_id,
                    success=False,
                    error_message=error_message,
                    progress_message=f'Enrollment failed: {error_message}'
                )
            
            # Emit error notification to web UI
            notification_data = {
                'type': 'enrollment_error',
                'message': f'Enrollment failed: {error_message}',
                'error': error_message,
                'enrollment_id': enrollment_id,
                'user_id': fingerprint_id,
                'username': user_name,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"📤 Emitting error notification")
            socketio.start_background_task(emit_notification_task, notification_data)
            logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error handling enrollment response: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Emit error notification even on exception
        try:
            notification_data = {
                'type': 'enrollment_error',
                'message': f'Error processing enrollment response: {str(e)}',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            socketio.start_background_task(emit_notification_task, notification_data)
        except:
            pass  # Don't fail if notification fails too

def emit_door_status_task(door_data):
    """Background task to emit door status via WebSocket"""
    try:
        logger.info(f"🚪 BACKGROUND TASK - DOOR STATUS: {door_data.get('door_status')}")
        
        socketio.sleep(0.01)
        socketio.emit('door_status_update', door_data, namespace='/')
        socketio.sleep(0.01)
        
        logger.info("✅ Door status emitted successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error emitting door status: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

def handle_door_status_message(payload):
    """Handle door status messages from local machine"""
    try:
        logger.info("=" * 80)
        logger.info("🚪 DOOR STATUS UPDATE RECEIVED")
        logger.info(f"   Status: {payload.get('door_status')}")
        logger.info(f"   Is Closed: {payload.get('is_closed')}")
        logger.info(f"   Timestamp: {payload.get('timestamp')}")
        logger.info(f"   Full payload: {payload}")
        
        door_status = payload.get('door_status', 'unknown')
        is_closed = payload.get('is_closed')
        timestamp = payload.get('timestamp')
        store_id = payload.get('store_id', 'Store001')
        sensor_pin = payload.get('sensor_pin')
        sensor_type = payload.get('sensor_type', 'NC')
        
        # Format door data for WebSocket
        door_data = {
            'door_status': door_status,
            'is_closed': is_closed,
            'status_text': 'Tertutup' if is_closed else 'Terbuka',
            'timestamp': timestamp,
            'store_id': store_id,
            'sensor_pin': sensor_pin,
            'sensor_type': sensor_type
        }
        
        logger.info(f"🔄 Formatted door data for WebSocket: {door_data}")
        
        # Use SocketIO background task to emit from MQTT thread
        logger.info("🚀 Starting background task to emit door status...")
        socketio.start_background_task(emit_door_status_task, door_data)
        logger.info("✅ Background task started successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error handling door status message: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

def handle_gpio_log_message(payload):
    """Handle GPIO log messages from local machine and save to database"""
    try:
        logger.info("=" * 80)
        logger.info("📊 GPIO LOG UPDATE RECEIVED")
        logger.info(f"   GPIO Pin: {payload.get('gpio_pin')}")
        logger.info(f"   GPIO State: {payload.get('gpio_state')}")
        logger.info(f"   Event Type: {payload.get('event_type')}")
        logger.info(f"   Full payload: {payload}")
        
        gpio_pin = payload.get('gpio_pin')
        gpio_state = payload.get('gpio_state')
        event_type = payload.get('event_type')
        user_id = payload.get('user_id')
        device_id = payload.get('device_id')
        description = payload.get('description')
        timestamp = payload.get('timestamp')
        
        # Validate required fields
        if gpio_pin is None or gpio_state is None:
            logger.error("❌ Missing required fields: gpio_pin or gpio_state")
            return
        
        # Connect to database and save GPIO log
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Failed to connect to database")
            return
        
        try:
            cursor = conn.cursor()
            
            # Check if gpio_log table exists, if not create it
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'gpio_log'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                logger.info("📋 Creating gpio_log table...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gpio_log (
                        id SERIAL PRIMARY KEY,
                        gpio_pin INTEGER NOT NULL,
                        gpio_state VARCHAR(10) NOT NULL,
                        event_type VARCHAR(50),
                        user_id INTEGER,
                        device_id VARCHAR(50),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    );
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_gpio_log_timestamp ON gpio_log(timestamp);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_gpio_log_gpio_pin ON gpio_log(gpio_pin);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_gpio_log_event_type ON gpio_log(event_type);
                """)
                conn.commit()
                logger.info("✅ gpio_log table created successfully")
            
            # Insert GPIO log
            if timestamp:
                try:
                    # Parse timestamp if provided
                    from datetime import datetime
                    if isinstance(timestamp, str):
                        # Try to parse ISO format timestamp
                        try:
                            parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            parsed_timestamp = datetime.now()
                    else:
                        parsed_timestamp = datetime.now()
                except:
                    parsed_timestamp = None
            else:
                parsed_timestamp = None
            
            if parsed_timestamp:
                cursor.execute("""
                    INSERT INTO gpio_log (gpio_pin, gpio_state, event_type, user_id, device_id, timestamp, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (gpio_pin, gpio_state, event_type, user_id, device_id, parsed_timestamp, description))
            else:
                cursor.execute("""
                    INSERT INTO gpio_log (gpio_pin, gpio_state, event_type, user_id, device_id, timestamp, description)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                """, (gpio_pin, gpio_state, event_type, user_id, device_id, description))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ GPIO log saved: GPIO({gpio_pin}) = {gpio_state} ({event_type})")
            logger.info("=" * 80)
            
        except Exception as db_error:
            logger.error(f"❌ Database error: {db_error}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            if conn:
                conn.rollback()
                conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error handling GPIO log message: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

def process_incoming_scan(data):
    """Process incoming scan data and log to database"""
    try:
        store_id = data.get('store_id')
        timestamp = data.get('timestamp')
        status = data.get('status')  # "Match" or "Not Match"
        fingerprint_id = data.get('fingerprint_id')
        device_id = data.get('device_id')
        username = data.get('username')
        confidence = data.get('confidence')
        
        # For "Not Match" with fingerprint_id = 0, we still want to log it
        # So we allow None or 0 for fingerprint_id in this case
        if not all([store_id, timestamp, status, device_id]):
            logger.warning(f"Incomplete scan data: {data}")
            return
        
        # Allow fingerprint_id to be None or 0 for unverified scans
        if fingerprint_id is None and status == "Not Match":
            fingerprint_id = 0
        
        # Determine sensor location based on device_id
        # AS608_001 = Pintu Masuk, AS608_002 = Pintu Keluar
        sensor_location = None
        if device_id == 'AS608_001':
            sensor_location = 'masuk'
        elif device_id == 'AS608_002':
            sensor_location = 'keluar'
        
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
            # For "Not Match" with fingerprint_id = 0, this is an unverified scan
            # Don't mark as denied yet - wait for user decision (enroll or dismiss)
            if fingerprint_id == 0 or fingerprint_id is None:
                granted_denied = "pending"  # Wait for user decision
            else:
                granted_denied = "denied"
        
        # Use username from payload if available, otherwise get from database
        if not username:
            # Only check database if fingerprint_id is valid (> 0)
            if fingerprint_id and fingerprint_id > 0:
                user_info = get_user_info_from_fingerprint(fingerprint_id, device_id)
                username = user_info.get('username') if user_info else None
            else:
                username = None  # Unverified scan - no username
        
        # Log to database with device_id and sensor_location
        # For unverified scans (fingerprint_id = 0), still log but with pending status
        log_scan_to_database(store_id, fingerprint_id if fingerprint_id and fingerprint_id > 0 else None, scan_time, action, username, granted_denied, device_id, sensor_location)
        
        logger.info(f"✓ Processed incoming scan: {status} for user {fingerprint_id} ({username}) at {sensor_location or device_id}")
        
    except Exception as e:
        logger.error(f"Error processing incoming scan: {e}")

def get_sensor_table_name(device_id):
    """Get sensor table name based on device_id"""
    if device_id == 'AS608_001':
        return 'user_sensor_1'
    elif device_id == 'AS608_002':
        return 'user_sensor_2'
    else:
        # Default to sensor 1 if device_id is not recognized
        return 'user_sensor_1'

def check_user_in_user_machine(fingerprint_id, device_id):
    """Check if user exists in user_machine table (new unified table)
    
    Returns:
        dict: User info if found, None if not found
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check in user_machine table
        cursor.execute("""
            SELECT id, user_id, nama, device_id, posisi, finger_template_id
            FROM user_machine
            WHERE user_id = %s AND device_id = %s
            LIMIT 1
        """, (fingerprint_id, device_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
        
    except Exception as e:
        logger.error(f"Error checking user in user_machine: {e}")
        return None

def get_user_info_from_fingerprint(fingerprint_id, device_id=None):
    """Get user information from fingerprint ID
    Checks user_machine table first, then sensor tables if device_id is not provided
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if device_id:
            # Check user_machine table first (new unified table)
            cursor.execute("""
                SELECT nama as username FROM user_machine 
                WHERE user_id = %s AND device_id = %s 
                LIMIT 1
            """, (fingerprint_id, device_id))
            result = cursor.fetchone()
            
            if not result:
                # Fallback to sensor table
                table_name = get_sensor_table_name(device_id)
                cursor.execute(f"""
                    SELECT username FROM {table_name} WHERE user_id = %s LIMIT 1
                """, (fingerprint_id,))
                result = cursor.fetchone()
        else:
            # Check user_machine table first
            cursor.execute("""
                SELECT nama as username FROM user_machine 
                WHERE user_id = %s 
                LIMIT 1
            """, (fingerprint_id,))
            result = cursor.fetchone()
            
            if not result:
                # Fallback to both sensor tables
                cursor.execute("""
                    SELECT username FROM user_sensor_1 WHERE user_id = %s
                    UNION
                    SELECT username FROM user_sensor_2 WHERE user_id = %s
                    LIMIT 1
                """, (fingerprint_id, fingerprint_id))
                result = cursor.fetchone()
        
        conn.close()
        
        return dict(result) if result else None
        
    except Exception as e:
        logger.error(f"Error getting user info from fingerprint: {e}")
        return None

def log_scan_to_database(store_id, fingerprint_id, timestamp, action, username, granted_denied="denied", device_id=None, sensor_location=None):
    """Log scan data to database"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Log to log_data table with device_id and sensor_location
        cursor.execute("""
            INSERT INTO log_data (user_id, store_id, timestamp, finger_template_id, device_id, sensor_location)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (fingerprint_id, store_id, timestamp, fingerprint_id, device_id, sensor_location))
        
        # Log to log_action table with device_id and sensor_location
        cursor.execute("""
            INSERT INTO log_action (user_id, store_id, username, timestamp, action, granted_denied, device_id, sensor_location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (fingerprint_id, store_id, username, timestamp, action, granted_denied, device_id, sensor_location))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error logging scan to database: {e}")
        return False

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info("=" * 80)
    logger.info(f"🔌 NEW WebSocket client connected!")
    logger.info(f"   Session ID: {request.sid}")
    logger.info(f"   Client IP: {request.remote_addr}")
    try:
        total_clients = len(socketio.server.manager.rooms.get('/', {}).get('', set()))
        logger.info(f"   Total connected clients: {total_clients}")
    except:
        logger.info("   Total connected clients: Unable to determine")
    logger.info("=" * 80)
    emit('status', {'message': 'Connected to WHAC Fingerprint System', 'status': 'success'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info("=" * 80)
    logger.info(f"🔌 WebSocket client disconnected!")
    logger.info(f"   Session ID: {request.sid}")
    logger.info(f"   Client IP: {request.remote_addr}")
    logger.info("=" * 80)

def log_access_to_database(nama, device_id, status, user_id=None, action_source='modal', finger_template_id=None):
    """Log access (grant/deny) to access_log table
    
    Args:
        nama: Nama user
        device_id: Device identifier (AS608_001, AS608_002, dll)
        status: 'granted' atau 'denied'
        user_id: ID user (bisa None jika tidak terdaftar)
        action_source: 'modal', 'automatic', 'manual'
        finger_template_id: ID template fingerprint yang di-scan
    """
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO access_log (nama, device_id, status, user_id, action_source, finger_template_id, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (nama, device_id, status, user_id, action_source, finger_template_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✓ Access logged: {status} for {nama} ({device_id}) - Source: {action_source}")
        return True
        
    except Exception as e:
        logger.error(f"Error logging access: {e}")
        return False

@socketio.on('grant_access')
def handle_grant_access(data):
    """Handle grant access command"""
    try:
        user_id = data.get('user_id')
        action = data.get('action', 'access_granted')
        username = data.get('username', 'Unknown')
        nama = data.get('nama', username)
        device_id = data.get('device_id', 'AS608_001')
        
        logger.info(f"Granting access for user {user_id} ({nama}) from device {device_id}")
        
        # Get user info if available
        user_info = check_user_in_user_machine(user_id, device_id) if user_id else None
        if user_info:
            nama = user_info.get('nama', nama)
        
        # Get finger_template_id from payload or user_id
        finger_template_id = data.get('finger_template_id', user_id)
        
        # Log to access_log table
        log_access_to_database(nama, device_id, 'granted', user_id, 'modal', finger_template_id)
        
        # Send MQTT command to control relay (GPIO)
        success = send_relay_command('grant', user_id, action, device_id)
        
        if success:
            # Log to database (legacy)
            log_manual_action(user_id, action, 'granted', device_id, None)
            
            emit('action_result', {
                'status': 'success',
                'message': f'Access granted for {nama}',
                'action': 'granted'
            })
            logger.info(f"✓ Access granted for user {user_id} ({nama})")
        else:
            emit('action_result', {
                'status': 'error',
                'message': 'Failed to send relay command - Check MQTT connection to Raspberry Pi'
            })
            logger.error(f"✗ Failed to grant access for user {user_id} - MQTT relay command failed")
        
    except Exception as e:
        logger.error(f"Error granting access: {e}")
        emit('action_result', {
            'status': 'error',
            'message': str(e)
        })

@socketio.on('check_mqtt_status')
def handle_check_mqtt_status():
    """Check MQTT connection status"""
    try:
        if not mqtt_client:
            emit('mqtt_status', {
                'status': 'error',
                'message': 'MQTT client not initialized',
                'connected': False
            })
            return
        
        is_connected = mqtt_client.is_connected()
        if is_connected:
            emit('mqtt_status', {
                'status': 'success',
                'message': 'MQTT client connected to Raspberry Pi',
                'connected': True,
                'broker': MQTT_BROKER,
                'port': MQTT_PORT
            })
        else:
            emit('mqtt_status', {
                'status': 'error',
                'message': 'MQTT client disconnected from Raspberry Pi',
                'connected': False,
                'broker': MQTT_BROKER,
                'port': MQTT_PORT
            })
    except Exception as e:
        logger.error(f"Error checking MQTT status: {e}")
        emit('mqtt_status', {
            'status': 'error',
            'message': f'Error checking MQTT status: {str(e)}',
            'connected': False
        })

def ensure_mqtt_connection():
    """Ensure MQTT connection is active, reconnect if needed"""
    global mqtt_client
    try:
        if not mqtt_client:
            logger.warning("MQTT client not initialized, setting up...")
            setup_mqtt_client()
            return mqtt_client and mqtt_client.is_connected()
        
        # Check connection status
        is_connected = mqtt_client.is_connected()
        
        if not is_connected:
            logger.warning("MQTT client disconnected, attempting to reconnect...")
            try:
                # Stop current loop if running
                try:
                    mqtt_client.loop_stop()
                except:
                    pass  # Loop might not be running
                
                # Reconnect with shorter keepalive for faster detection
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 30)
                mqtt_client.loop_start()
                
                # Wait for connection to establish with exponential backoff
                import time
                time.sleep(1)  # Reduced from 2 seconds
                
                # Verify connection
                if mqtt_client.is_connected():
                    logger.info("✅ MQTT client reconnected successfully")
                    return True
                else:
                    logger.error("❌ Failed to reconnect MQTT client")
                    return False
            except Exception as reconnect_error:
                logger.error(f"❌ MQTT reconnection error: {reconnect_error}")
                return False
        else:
            # Connection appears to be active
            logger.debug("✅ MQTT client connection verified")
            return True
        
    except Exception as e:
        logger.error(f"Error ensuring MQTT connection: {e}")
        return False

def test_mqtt_connection():
    """Test MQTT connection by sending a ping"""
    global mqtt_client
    try:
        if not mqtt_client:
            return False
        
        # Try to ping the broker
        result = mqtt_client.ping()
        if result == 0:
            logger.debug("✅ MQTT ping successful - connection is active")
            return True
        else:
            logger.warning(f"⚠️  MQTT ping failed (result: {result})")
            return False
    except Exception as e:
        logger.warning(f"⚠️  MQTT ping error: {e}")
        return False

@socketio.on('deny_access')
def handle_deny_access(data):
    """Handle deny access command"""
    try:
        user_id = data.get('user_id')
        action = data.get('action', 'access_denied')
        username = data.get('username', 'Unknown')
        nama = data.get('nama', username)
        device_id = data.get('device_id', 'AS608_001')
        
        logger.info(f"Denying access for user {user_id} ({nama}) from device {device_id}")
        
        # Get finger_template_id from payload or user_id
        finger_template_id = data.get('finger_template_id', user_id)
        
        # Log to access_log table
        log_access_to_database(nama, device_id, 'denied', user_id, 'modal', finger_template_id)
        
        # Send MQTT command to control relay
        success = send_relay_command('deny', user_id, action, device_id)
        
        if success:
            # Log to database (legacy)
            log_manual_action(user_id, action, 'denied', device_id, None)
            
            emit('action_result', {
                'status': 'success',
                'message': f'Access denied for {nama}',
                'action': 'denied'
            })
            logger.info(f"✓ Access denied for user {user_id} ({nama})")
        else:
            emit('action_result', {
                'status': 'error',
                'message': 'Failed to send relay command - Check MQTT connection to Raspberry Pi'
            })
            logger.error(f"✗ Failed to deny access for user {user_id} - MQTT relay command failed")
        
    except Exception as e:
        logger.error(f"Error denying access: {e}")
        emit('action_result', {
            'status': 'error',
            'message': str(e)
        })

def send_relay_command(command, user_id, action, device_id=None):
    """Send relay control command via MQTT with GPIO control"""
    try:
        # Ensure MQTT connection is active
        if not ensure_mqtt_connection():
            logger.error("❌ Cannot establish MQTT connection")
            return False
        
        # Test connection with ping to verify it's really working
        if not test_mqtt_connection():
            logger.warning("⚠️  MQTT ping failed, but connection appears active - proceeding anyway")
        
        payload = {
            'command': command,
            'user_id': user_id,
            'action': action,
            'device_id': device_id,
            'timestamp': datetime.now().isoformat(),
            'source': 'web_ui',
            'gpio_config': {
                'gpio_1': 1,  # Relay control pin
                'gpio_2': 2,  # Digital input pin (door sensor)
                'gpio_3': 3   # Output control pin
            }
        }
        
        logger.info(f"📤 Sending relay command: {command} for user {user_id} (device: {device_id})")
        logger.info(f"📤 MQTT Topic: {MQTT_ACTION_TOPIC}")
        logger.info(f"📤 Payload: {payload}")
        
        result = mqtt_client.publish(MQTT_ACTION_TOPIC, json.dumps(payload), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"✓ Relay command sent successfully: {command} for user {user_id}")
            return True
        else:
            logger.error(f"✗ Failed to send relay command (rc: {result.rc})")
            logger.error(f"✗ MQTT Error codes: SUCCESS=0, ERR_NO_CONN=3, ERR_CONN_LOST=4")
            return False
            
    except Exception as e:
        logger.error(f"Error sending relay command: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def log_manual_action(user_id, action, granted_denied, device_id=None, sensor_location=None):
    """Log manual action to database"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get username if user_id exists - check user_machine table first, then sensor tables
        username = None
        if user_id and user_id > 0:
            # Try user_machine table first (new unified table)
            cursor.execute("""
                SELECT nama FROM user_machine 
                WHERE user_id = %s AND device_id = %s 
                LIMIT 1
            """, (user_id, device_id))
            result = cursor.fetchone()
            if result:
                username = result[0]
            else:
                # Fallback to sensor tables
                table_name = get_sensor_table_name(device_id)
                cursor.execute(f"SELECT username FROM {table_name} WHERE user_id = %s LIMIT 1", (user_id,))
                result = cursor.fetchone()
                if result:
                    username = result[0]
        
        # Insert action log with device_id and sensor_location
        cursor.execute("""
            INSERT INTO log_action (user_id, store_id, username, timestamp, action, granted_denied, device_id, sensor_location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, 'Store001', username, datetime.now(), action, granted_denied, device_id, sensor_location))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ Manual action logged: {action} - {granted_denied} for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error logging manual action: {e}")
        return False

# Authentication functions
def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged in user"""
    if 'user_id' not in session:
        return None
    
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, username, full_name, email, role, is_active
            FROM web_users 
            WHERE id = %s AND is_active = TRUE
        """, (session['user_id'],))
        
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None

def is_user_locked(username):
    """Check if user account is locked"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT locked_until, login_attempts
            FROM web_users 
            WHERE username = %s
        """, (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:  # locked_until is not None
            if datetime.now() < result[0]:
                return True
            else:
                # Unlock account if lock time has passed
                unlock_user(username)
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking user lock status: {e}")
        return False

def lock_user(username):
    """Lock user account after failed attempts"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        # Lock for 15 minutes after 5 failed attempts
        lock_until = datetime.now() + timedelta(minutes=15)
        cursor.execute("""
            UPDATE web_users 
            SET locked_until = %s, login_attempts = login_attempts + 1
            WHERE username = %s
        """, (lock_until, username))
        
        conn.commit()
        conn.close()
        
        logger.warning(f"User {username} locked due to failed login attempts")
        return True
        
    except Exception as e:
        logger.error(f"Error locking user: {e}")
        return False

def unlock_user(username):
    """Unlock user account"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE web_users 
            SET locked_until = NULL, login_attempts = 0
            WHERE username = %s
        """, (username,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User {username} unlocked")
        return True
        
    except Exception as e:
        logger.error(f"Error unlocking user: {e}")
        return False

def create_session(user_id, ip_address, user_agent):
    """Create user session"""
    try:
        session_token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session
        
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, session_token, expires_at, ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        return session_token
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return None

def validate_session(session_token):
    """Validate user session"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT s.user_id, s.expires_at, u.username, u.is_active
            FROM user_sessions s
            JOIN web_users u ON s.user_id = u.id
            WHERE s.session_token = %s AND s.is_active = TRUE AND s.expires_at > %s
        """, (session_token, datetime.now()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result['is_active']:
            return dict(result)
        
        return False
        
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        return False

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        # Check if user is locked
        if is_user_locked(username):
            flash('Account is temporarily locked due to failed login attempts. Please try again later.', 'error')
            return render_template('login.html')
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Database connection error', 'error')
                return render_template('login.html')
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT id, username, password_hash, full_name, role, is_active
                FROM web_users 
                WHERE username = %s AND is_active = TRUE
            """, (username,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user and verify_password(password, user['password_hash']):
                # Successful login
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                
                # Create session record
                session_token = create_session(
                    user['id'], 
                    request.remote_addr, 
                    request.headers.get('User-Agent', '')
                )
                
                if session_token:
                    session['session_token'] = session_token
                
                # Update last login
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE web_users 
                        SET last_login = %s, login_attempts = 0, locked_until = NULL
                        WHERE id = %s
                    """, (datetime.now(), user['id']))
                    conn.commit()
                    conn.close()
                
                logger.info(f"User {username} logged in successfully")
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                # Failed login
                lock_user(username)
                flash('Invalid username or password', 'error')
                logger.warning(f"Failed login attempt for user {username}")
                return render_template('login.html')
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Login error occurred', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    if 'session_token' in session:
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE session_token = %s
                """, (session['session_token'],))
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error deactivating session: {e}")
    
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('Please fill in all fields', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return render_template('change_password.html')
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Database connection error', 'error')
                return render_template('change_password.html')
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT password_hash FROM web_users WHERE id = %s
            """, (session['user_id'],))
            
            result = cursor.fetchone()
            
            if result and verify_password(current_password, result['password_hash']):
                # Update password
                new_hash = hash_password(new_password)
                cursor.execute("""
                    UPDATE web_users 
                    SET password_hash = %s 
                    WHERE id = %s
                """, (new_hash, session['user_id']))
                
                conn.commit()
                conn.close()
                
                flash('Password changed successfully!', 'success')
                logger.info(f"User {session['username']} changed password")
                return redirect(url_for('index'))
            else:
                flash('Current password is incorrect', 'error')
                return render_template('change_password.html')
                
        except Exception as e:
            logger.error(f"Password change error: {e}")
            flash('Error changing password', 'error')
            return render_template('change_password.html')
    
    return render_template('change_password.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard for user management"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin.html')

@app.route('/api/admin/web_users')
@login_required
def get_web_users():
    """Get all web UI users (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Log database configuration for debugging
        logger.info(f"Getting web users - DB config: host={DB_CONFIG['host']}, db={DB_CONFIG['database']}")
        
        conn = get_db_connection()
        if not conn:
            logger.error("Database connection failed")
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, username, full_name, email, role, is_active, 
                   created_at, last_login, login_attempts, locked_until
            FROM web_users
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        user_count = len(users)
        logger.info(f"Found {user_count} users in database")
        
        # Log each user for debugging
        for u in users:
            logger.debug(f"User: ID={u['id']}, username={u['username']}, role={u['role']}")
        
        conn.close()
        
        return jsonify([dict(user) for user in users])
        
    except Exception as e:
        logger.error(f"Error getting web users: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/web_users', methods=['POST'])
@login_required
def create_web_user():
    """Create new web UI user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name')
        email = data.get('email')
        role = data.get('role', 'viewer')
        
        if not all([username, password]):
            return jsonify({'error': 'Username and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM web_users WHERE username = %s", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Username already exists'}), 400
        
        # Hash password and create user
        password_hash = hash_password(password)
        
        logger.info(f"Creating user: username={username}, role={role}, email={email or 'N/A'}")
        
        try:
            cursor.execute("""
                INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, password_hash, full_name, email, role, True, datetime.now()))
            
            conn.commit()
            logger.info(f"Admin {user['username']} created new web user: {username} (ID: {cursor.lastrowid if hasattr(cursor, 'lastrowid') else 'N/A'})")
            
            # Verify user was created
            cursor.execute("SELECT id, username, role FROM web_users WHERE username = %s", (username,))
            created_user = cursor.fetchone()
            if created_user:
                logger.info(f"User verified in database: ID={created_user[0]}, username={created_user[1]}")
            else:
                logger.warning(f"User {username} was not found after creation!")
            
            conn.close()
            return jsonify({'message': f'User {username} created successfully'})
            
        except psycopg2.IntegrityError as e:
            conn.rollback()
            conn.close()
            error_msg = str(e)
            if 'unique constraint' in error_msg.lower() or 'duplicate key' in error_msg.lower():
                logger.warning(f"Username {username} already exists")
                return jsonify({'error': 'Username already exists'}), 400
            else:
                logger.error(f"Integrity error creating user {username}: {e}")
                return jsonify({'error': f'Database constraint violation: {error_msg}'}), 400
        except psycopg2.Error as e:
            conn.rollback()
            conn.close()
            logger.error(f"Database error creating user {username}: {e}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Error creating web user: {e}", exc_info=True)
        if 'conn' in locals():
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/web_users/<int:user_id>', methods=['PUT'])
@login_required
def update_web_user(user_id):
    """Update web UI user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        email = data.get('email')
        role = data.get('role')
        is_active = data.get('is_active')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM web_users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        username = result[0]
        
        # Update user
        cursor.execute("""
            UPDATE web_users 
            SET full_name = %s, email = %s, role = %s, is_active = %s
            WHERE id = %s
        """, (full_name, email, role, is_active, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {user['username']} updated web user: {username}")
        return jsonify({'message': f'User {username} updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating web user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/web_users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_web_user(user_id):
    """Delete web UI user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM web_users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        username = result[0]
        
        # Don't allow deleting the last admin
        cursor.execute("SELECT COUNT(*) FROM web_users WHERE role = 'admin' AND is_active = TRUE")
        admin_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT role FROM web_users WHERE id = %s", (user_id,))
        user_role = cursor.fetchone()[0]
        
        if user_role == 'admin' and admin_count <= 1:
            conn.close()
            return jsonify({'error': 'Cannot delete the last admin user'}), 400
        
        # Delete user sessions first
        cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
        
        # Delete user
        cursor.execute("DELETE FROM web_users WHERE id = %s", (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {user['username']} deleted web user: {username}")
        return jsonify({'message': f'User {username} deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting web user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/web_users/<int:user_id>/reset_password', methods=['POST'])
@login_required
def reset_web_user_password(user_id):
    """Reset web UI user password (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM web_users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        username = result[0]
        
        # Update password
        password_hash = hash_password(new_password)
        cursor.execute("""
            UPDATE web_users 
            SET password_hash = %s, login_attempts = 0, locked_until = NULL
            WHERE id = %s
        """, (password_hash, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {user['username']} reset password for web user: {username}")
        return jsonify({'message': f'Password reset successfully for {username}'})
        
    except Exception as e:
        logger.error(f"Error resetting web user password: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test_websocket')
@login_required
def test_websocket():
    """Test WebSocket connection"""
    try:
        test_data = {
            'user_id': 999,
            'status': 'Test',
            'username': 'Test User',
            'confidence': 100,
            'timestamp': datetime.now().isoformat(),
            'store_id': 'Store001',
            'device_id': 'TEST_001'
        }
        
        logger.info("=" * 80)
        logger.info("🧪 TESTING WEBSOCKET CONNECTION")
        logger.info(f"📋 Test data: {test_data}")
        logger.info(f"📊 Thread info: {threading.current_thread().name}")
        
        # Emit test message
        socketio.emit('scan_notification', test_data, namespace='/')
        logger.info("✅ Test WebSocket message emitted")
        logger.info("=" * 80)
        
        return jsonify({
            'status': 'success', 
            'message': 'Test WebSocket message sent',
            'test_data': test_data
        })
        
    except Exception as e:
        logger.error(f"❌ Error sending test WebSocket message: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/mqtt_status')
@login_required
def mqtt_status():
    """Check MQTT connection status"""
    try:
        status = {
            'mqtt_connected': mqtt_client is not None and mqtt_client.is_connected() if hasattr(mqtt_client, 'is_connected') else False,
            'mqtt_broker': MQTT_BROKER,
            'mqtt_port': MQTT_PORT,
            'mqtt_topic': MQTT_SCAN_TOPIC,
            'mqtt_client_id': 'whac_web_ui',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📊 MQTT Status Check: {status}")
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Error checking MQTT status: {e}")
        return jsonify({
            'error': str(e),
            'mqtt_connected': False
        })

@app.route('/simulate_scan')
@login_required
def simulate_scan():
    """Simulate a real fingerprint scan"""
    try:
        # Get a real user from database for more realistic simulation
        fingerprint_id = 1
        username = 'Test User'
        try:
            user_info = get_user_info_from_fingerprint(1)  # Try to get user with fingerprint_id = 1
            if user_info:
                username = user_info.get('username', 'Test User')
            else:
                # Fallback: use first available user from either sensor
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT user_id, username FROM user_sensor_1 ORDER BY user_id LIMIT 1
                        UNION
                        SELECT user_id, username FROM user_sensor_2 ORDER BY user_id LIMIT 1
                        ORDER BY user_id LIMIT 1
                    """)
                    user_row = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    if user_row:
                        fingerprint_id = user_row[0]
                        username = user_row[1]
        except Exception as e:
            logger.warning(f"⚠️  Could not get user from database, using defaults: {e}")
        
        # Simulate the exact same data format that comes from MQTT
        # Note: process_incoming_scan expects 'fingerprint_id' not 'user_id'
        payload = {
            'fingerprint_id': fingerprint_id,
            'status': 'Match',
            'username': username,
            'confidence': 85,
            'timestamp': datetime.now().isoformat(),
            'store_id': 'Store001',
            'device_id': 'AS608_001'
        }
        
        logger.info("=" * 80)
        logger.info("🧪 SIMULATING SCAN NOTIFICATION")
        logger.info(f"📋 Payload data: {payload}")
        logger.info(f"📊 Thread info: {threading.current_thread().name}")
        
        # Process the scan data and log to database (like real MQTT data)
        try:
            process_incoming_scan(payload)
            logger.info("✅ Simulated scan saved to database")
        except Exception as db_error:
            logger.warning(f"⚠️  Could not save to database: {db_error}")
            # Continue even if DB save fails
        
        # Format scan data for WebSocket (use same format as handle_scan_message)
        scan_data = {
            'user_id': payload.get('fingerprint_id'),
            'status': payload.get('status'),
            'username': payload.get('username'),
            'confidence': payload.get('confidence'),
            'timestamp': payload.get('timestamp'),
            'store_id': payload.get('store_id'),
            'device_id': payload.get('device_id')
        }
        
        # Emit simulated scan using same method as real MQTT data
        socketio.start_background_task(emit_scan_notification_task, scan_data)
        logger.info("✅ Simulated scan notification emitted to WebSocket")
        logger.info("=" * 80)
        
        return jsonify({
            'status': 'success', 
            'message': 'Simulated scan sent and saved to database',
            'scan_data': scan_data
        })
        
    except Exception as e:
        logger.error(f"❌ Error simulating scan: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/admin/fingerprint_users')
@login_required
def get_fingerprint_users():
    """Get all fingerprint users (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT user_id, username, finger_template_id, 'AS608_001' as device_id, 'masuk' as sensor_location
            FROM user_sensor_1
            UNION ALL
            SELECT user_id, username, finger_template_id, 'AS608_002' as device_id, 'keluar' as sensor_location
            FROM user_sensor_2
            ORDER BY user_id, device_id
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        return jsonify([dict(user) for user in users])
        
    except Exception as e:
        logger.error(f"Error getting fingerprint users: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/fingerprint_users', methods=['POST'])
@login_required
def create_fingerprint_user():
    """Create new fingerprint user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        username = data.get('username')
        finger_template_id = data.get('finger_template_id')
        
        if not all([user_id, username, finger_template_id]):
            return jsonify({'error': 'User ID, username, and fingerprint template ID are required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get device_id from request (default to AS608_001 if not provided)
        device_id = data.get('device_id', 'AS608_001')
        table_name = get_sensor_table_name(device_id)
        
        # Check if user ID already exists in the specified sensor table
        cursor.execute(f"SELECT user_id FROM {table_name} WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': f'User ID already exists in {table_name}'}), 400
        
        # Check if fingerprint template ID already exists in the specified sensor table
        cursor.execute(f"SELECT finger_template_id FROM {table_name} WHERE finger_template_id = %s", (finger_template_id,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Fingerprint template ID already exists'}), 400
        
        # Create user in the appropriate sensor table
        cursor.execute(f"""
            INSERT INTO {table_name} (user_id, username, finger_template_id)
            VALUES (%s, %s, %s)
        """, (user_id, username, finger_template_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {user['username']} created new fingerprint user: {username} (ID: {user_id})")
        return jsonify({'message': f'Fingerprint user {username} created successfully'})
        
    except Exception as e:
        logger.error(f"Error creating fingerprint user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/fingerprint_users/<int:user_id>', methods=['PUT'])
@login_required
def update_fingerprint_user(user_id):
    """Update fingerprint user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        username = data.get('username')
        finger_template_id = data.get('finger_template_id')
        
        if not all([username, finger_template_id]):
            return jsonify({'error': 'Username and fingerprint template ID are required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get device_id from request (default to AS608_001 if not provided)
        device_id = data.get('device_id', 'AS608_001')
        table_name = get_sensor_table_name(device_id)
        
        # Check if user exists in the specified sensor table
        cursor.execute(f"SELECT user_id FROM {table_name} WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': f'User not found in {table_name}'}), 404
        
        # Check if new fingerprint template ID already exists (excluding current user)
        cursor.execute(f"SELECT finger_template_id FROM {table_name} WHERE finger_template_id = %s AND user_id != %s", (finger_template_id, user_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Fingerprint template ID already exists'}), 400
        
        # Update user in the appropriate sensor table
        cursor.execute(f"""
            UPDATE {table_name} 
            SET username = %s, finger_template_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """, (username, finger_template_id, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {user['username']} updated fingerprint user: {username} (ID: {user_id})")
        return jsonify({'message': f'Fingerprint user {username} updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating fingerprint user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/fingerprint_users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_fingerprint_user(user_id):
    """Delete fingerprint user (admin only)"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get device_id from request (optional, if not provided delete from both tables)
        device_id = request.args.get('device_id')
        
        if device_id:
            # Delete from specific sensor table
            table_name = get_sensor_table_name(device_id)
            cursor.execute(f"SELECT username FROM {table_name} WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return jsonify({'error': f'User not found in {table_name}'}), 404
            
            username = result[0]
            cursor.execute(f"DELETE FROM {table_name} WHERE user_id = %s", (user_id,))
        else:
            # Delete from both sensor tables
            cursor.execute("SELECT username FROM user_sensor_1 WHERE user_id = %s", (user_id,))
            result1 = cursor.fetchone()
            cursor.execute("SELECT username FROM user_sensor_2 WHERE user_id = %s", (user_id,))
            result2 = cursor.fetchone()
            
            if not result1 and not result2:
                conn.close()
                return jsonify({'error': 'User not found in any sensor table'}), 404
            
            username = (result1[0] if result1 else result2[0])
            cursor.execute("DELETE FROM user_sensor_1 WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM user_sensor_2 WHERE user_id = %s", (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {user['username']} deleted fingerprint user: {username} (ID: {user_id})")
        return jsonify({'message': f'Fingerprint user {username} deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting fingerprint user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard_stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        logger.info("📊 Dashboard stats requested")
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database connection failed for dashboard stats")
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get total users (count unique user_id from both sensor tables)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as total_users 
            FROM (
                SELECT user_id FROM user_sensor_1
                UNION
                SELECT user_id FROM user_sensor_2
            ) as all_users
        """)
        total_users = cursor.fetchone()['total_users']
        logger.info(f"  Total users: {total_users}")
        
        # Get total scans today using Asia/Jakarta timezone
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        now_jakarta = datetime.now(jakarta_tz)
        today = now_jakarta.date()
        logger.info(f"  Checking data for date: {today} (Jakarta time: {now_jakarta.strftime('%Y-%m-%d %H:%M:%S')})")
        
        cursor.execute("""
            SELECT COUNT(*) as total_scans_today 
            FROM log_data 
            WHERE DATE(timestamp) = %s
        """, (today,))
        total_scans_today = cursor.fetchone()['total_scans_today']
        logger.info(f"  Scans today: {total_scans_today}")
        
        # Get successful access today
        cursor.execute("""
            SELECT COUNT(*) as successful_access_today 
            FROM log_action 
            WHERE DATE(timestamp) = %s AND granted_denied = 'granted'
        """, (today,))
        successful_access_today = cursor.fetchone()['successful_access_today']
        logger.info(f"  Access granted today: {successful_access_today}")
        
        # Get denied access today
        cursor.execute("""
            SELECT COUNT(*) as denied_access_today 
            FROM log_action 
            WHERE DATE(timestamp) = %s AND granted_denied = 'denied'
        """, (today,))
        denied_access_today = cursor.fetchone()['denied_access_today']
        logger.info(f"  Access denied today: {denied_access_today}")
        
        # Get recent activity (last 10 scans)
        cursor.execute("""
            SELECT * FROM fingerprint_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        recent_activity = cursor.fetchall()
        
        conn.close()
        
        response_data = {
            'total_users': total_users,
            'total_scans_today': total_scans_today,
            'successful_access_today': successful_access_today,
            'denied_access_today': denied_access_today,
            'recent_activity': [dict(row) for row in recent_activity]
        }
        
        logger.info(f"✅ Dashboard stats returned: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
@login_required
def get_logs():
    """Get fingerprint logs with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM log_data")
        total = cursor.fetchone()['total']
        
        # Get logs with pagination
        cursor.execute("""
            SELECT * FROM fingerprint_logs 
            ORDER BY timestamp DESC 
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        logs = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'logs': [dict(row) for row in logs],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/action_logs')
@login_required
def get_action_logs():
    """Get action logs with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM log_action")
        total = cursor.fetchone()['total']
        
        # Get action logs with pagination
        cursor.execute("""
            SELECT * FROM action_logs 
            ORDER BY timestamp DESC 
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        logs = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'logs': [dict(row) for row in logs],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting action logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users')
@login_required
def get_users():
    """Get all users from user_sensor_1 and user_sensor_2"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT 
                s1.user_id,
                s1.username,
                s1.finger_template_id,
                'AS608_001' as device_id,
                'masuk' as sensor_location,
                s1.created_at,
                s1.updated_at,
                COUNT(ld.id) as total_scans,
                MAX(ld.timestamp) as last_scan
            FROM user_sensor_1 s1
            LEFT JOIN log_data ld ON s1.user_id = ld.user_id AND ld.device_id = 'AS608_001'
            GROUP BY s1.id, s1.user_id, s1.username, s1.finger_template_id, s1.created_at, s1.updated_at
            
            UNION ALL
            
            SELECT 
                s2.user_id,
                s2.username,
                s2.finger_template_id,
                'AS608_002' as device_id,
                'keluar' as sensor_location,
                s2.created_at,
                s2.updated_at,
                COUNT(ld.id) as total_scans,
                MAX(ld.timestamp) as last_scan
            FROM user_sensor_2 s2
            LEFT JOIN log_data ld ON s2.user_id = ld.user_id AND ld.device_id = 'AS608_002'
            GROUP BY s2.id, s2.user_id, s2.username, s2.finger_template_id, s2.created_at, s2.updated_at
            
            ORDER BY user_id, device_id
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'users': [dict(row) for row in users]
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/daily_stats')
@login_required
def daily_stats_chart():
    """Get daily statistics for charts"""
    try:
        days = int(request.args.get('days', 7))
        
        conn = get_db_connection()
        if not conn:
            logger.error("Database connection failed for daily stats")
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get daily scan counts - Use proper PostgreSQL INTERVAL syntax
        logger.info(f"Fetching daily stats for last {days} days")
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as scan_count
            FROM log_data 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day' * %s
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (days,))
        
        daily_scans = cursor.fetchall()
        logger.info(f"Found {len(daily_scans)} days of scan data")
        
        # Get daily access granted/denied - Use proper PostgreSQL INTERVAL syntax
        cursor.execute("""
            SELECT DATE(timestamp) as date, 
                   granted_denied,
                   COUNT(*) as count
            FROM log_action 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day' * %s
            GROUP BY DATE(timestamp), granted_denied
            ORDER BY date
        """, (days,))
        
        daily_access = cursor.fetchall()
        logger.info(f"Found {len(daily_access)} days of access data")
        conn.close()
        
        # Convert dates to strings for JSON serialization
        daily_scans_result = []
        for row in daily_scans:
            row_dict = dict(row)
            if row_dict.get('date'):
                row_dict['date'] = row_dict['date'].isoformat()
            daily_scans_result.append(row_dict)
        
        daily_access_result = []
        for row in daily_access:
            row_dict = dict(row)
            if row_dict.get('date'):
                row_dict['date'] = row_dict['date'].isoformat()
            daily_access_result.append(row_dict)
        
        return jsonify({
            'daily_scans': daily_scans_result,
            'daily_access': daily_access_result
        })
        
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/enroll_user_from_modal', methods=['POST'])
@login_required
def enroll_user_from_modal():
    """Enroll user from modal popup (untuk user yang tidak terdaftar)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        nama = data.get('nama')
        device_id = data.get('device_id')
        posisi = data.get('posisi', '')
        finger_template_id = data.get('finger_template_id', user_id)
        
        if not all([user_id, nama, device_id]):
            return jsonify({'error': 'Missing required fields: user_id, nama, device_id'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Insert ke user_machine table (unified table)
        cursor.execute("""
            INSERT INTO user_machine (user_id, nama, device_id, posisi, finger_template_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, device_id) DO UPDATE SET
                nama = EXCLUDED.nama,
                posisi = EXCLUDED.posisi,
                finger_template_id = EXCLUDED.finger_template_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, nama, device_id, posisi, finger_template_id))
        
        # Also insert to sensor table for backward compatibility
        table_name = get_sensor_table_name(device_id)
        cursor.execute(f"""
            INSERT INTO {table_name} (user_id, username, finger_template_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                finger_template_id = EXCLUDED.finger_template_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, nama, finger_template_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✓ User enrolled: {nama} (ID: {user_id}, Device: {device_id})")
        
        return jsonify({
            'status': 'success',
            'message': f'User {nama} berhasil didaftarkan',
            'user_id': user_id,
            'nama': nama,
            'device_id': device_id
        })
        
    except Exception as e:
        logger.error(f"Error enrolling user from modal: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_user', methods=['POST'])
@login_required
def add_user():
    """Add new user to user_sensor_1 or user_sensor_2 based on device_id"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        username = data.get('username')
        finger_template_id = data.get('finger_template_id')
        
        if not all([user_id, username, finger_template_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get device_id from request (default to AS608_001 if not provided)
        device_id = data.get('device_id', 'AS608_001')
        table_name = get_sensor_table_name(device_id)
        
        cursor.execute(f"""
            INSERT INTO {table_name} (user_id, username, finger_template_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                finger_template_id = EXCLUDED.finger_template_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, username, finger_template_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User added successfully'})
        
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete user from user_sensor_1 and/or user_sensor_2"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get device_id from request (optional, if not provided delete from both tables)
        device_id = request.args.get('device_id')
        
        if device_id:
            # Delete from specific sensor table
            table_name = get_sensor_table_name(device_id)
            cursor.execute(f"DELETE FROM {table_name} WHERE user_id = %s", (user_id,))
        else:
            # Delete from both sensor tables
            cursor.execute("DELETE FROM user_sensor_1 WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM user_sensor_2 WHERE user_id = %s", (user_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mqtt_status', methods=['GET'])
@login_required
def get_mqtt_status():
    """Get MQTT connection status"""
    try:
        global mqtt_client
        
        if mqtt_client is None:
            return jsonify({
                'connected': False,
                'error': 'MQTT client not initialized',
                'broker': f'{MQTT_BROKER}:{MQTT_PORT}'
            }), 200
        
        is_connected = mqtt_client.is_connected()
        
        return jsonify({
            'connected': is_connected,
            'broker': f'{MQTT_BROKER}:{MQTT_PORT}',
            'status': 'Connected' if is_connected else 'Disconnected'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting MQTT status: {e}")
        return jsonify({
            'connected': False,
            'error': str(e),
            'broker': f'{MQTT_BROKER}:{MQTT_PORT}'
        }), 200

@app.route('/api/enrollment_status/<enrollment_id>', methods=['GET'])
@login_required
def get_enrollment_status(enrollment_id):
    """Get enrollment status by enrollment ID"""
    try:
        enrollment = enrollment_manager.get_enrollment_status(enrollment_id)
        
        if not enrollment:
            return jsonify({
                'error': 'Enrollment not found',
                'enrollment_id': enrollment_id
            }), 404
        
        # Convert datetime to ISO format for JSON
        enrollment_data = enrollment.copy()
        if enrollment_data.get('started_at'):
            enrollment_data['started_at'] = enrollment_data['started_at'].isoformat()
        if enrollment_data.get('completed_at'):
            enrollment_data['completed_at'] = enrollment_data['completed_at'].isoformat()
        
        return jsonify(enrollment_data), 200
        
    except Exception as e:
        logger.error(f"Error getting enrollment status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/enrollment_status', methods=['GET'])
@login_required
def get_active_enrollments():
    """Get all active enrollments"""
    try:
        user_id = request.args.get('user_id')
        
        if user_id:
            enrollment = enrollment_manager.get_enrollment_by_user_id(int(user_id))
            if enrollment:
                enrollment_data = enrollment.copy()
                if enrollment_data.get('started_at'):
                    enrollment_data['started_at'] = enrollment_data['started_at'].isoformat()
                if enrollment_data.get('completed_at'):
                    enrollment_data['completed_at'] = enrollment_data['completed_at'].isoformat()
                return jsonify(enrollment_data), 200
            else:
                return jsonify({'error': 'No active enrollment found for this user'}), 404
        else:
            # Return all active enrollments
            with enrollment_manager.lock:
                active = [
                    e for e in enrollment_manager.active_enrollments.values()
                    if e['status'] in ['pending', 'in_progress']
                ]
            
            # Convert datetime to ISO format
            for enrollment in active:
                if enrollment.get('started_at'):
                    enrollment['started_at'] = enrollment['started_at'].isoformat()
                if enrollment.get('completed_at'):
                    enrollment['completed_at'] = enrollment['completed_at'].isoformat()
            
            return jsonify({'active_enrollments': active}), 200
        
    except Exception as e:
        logger.error(f"Error getting active enrollments: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/next_user_id', methods=['GET'])
@login_required
def get_next_user_id():
    """Get the next available user ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        # Get next user_id from both sensor tables
        cursor.execute("""
            SELECT COALESCE(MAX(user_id), 0) + 1 as next_id 
            FROM (
                SELECT user_id FROM user_sensor_1
                UNION
                SELECT user_id FROM user_sensor_2
            ) as all_users
        """)
        result = cursor.fetchone()
        conn.close()
        
        next_id = result[0] if result else 1
        return jsonify({'next_id': next_id}), 200
        
    except Exception as e:
        logger.error(f"Error getting next user ID: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/enroll_user', methods=['POST'])
@login_required
def enroll_user():
    """Send enrollment command to local machine via MQTT"""
    try:
        logger.info("=" * 80)
        logger.info("📝 ENROLLMENT REQUEST RECEIVED")
        
        # Get request data
        data = request.get_json()
        if not data:
            logger.error("❌ No JSON data in request")
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"📦 Request data: {data}")
        
        user_id = data.get('user_id')
        username = data.get('username')
        
        logger.info(f"   User ID: {user_id} (type: {type(user_id)})")
        logger.info(f"   Username: {username} (type: {type(username)})")
        logger.info(f"   Requested by: {session.get('username', 'Unknown')}")
        
        if not user_id or not username:
            logger.error(f"❌ Missing required fields: user_id={user_id}, username={username}")
            return jsonify({
                'error': 'User ID and username are required',
                'debug': {
                    'user_id': user_id,
                    'username': username,
                    'user_id_type': str(type(user_id)),
                    'username_type': str(type(username))
                }
            }), 400
        
        # Check enrollment status (allow re-enrollment for multi-sensor support)
        logger.info("🔍 Checking enrollment status...")
        enrolled_devices = []
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                # Check which devices this user is already enrolled on
                cursor.execute("""
                    SELECT 'AS608_001' as device_id, 'masuk' as sensor_location 
                    FROM user_sensor_1 
                    WHERE user_id = %s
                    UNION
                    SELECT 'AS608_002' as device_id, 'keluar' as sensor_location 
                    FROM user_sensor_2 
                    WHERE user_id = %s
                """, (user_id, user_id))
                existing_enrollments = cursor.fetchall()
                conn.close()
                
                if existing_enrollments:
                    enrolled_devices = [row[0] for row in existing_enrollments]
                    logger.info(f"ℹ️  User ID {user_id} already enrolled on: {', '.join(enrolled_devices)}")
                    logger.info(f"ℹ️  Allowing re-enrollment for multi-sensor support")
                else:
                    logger.info(f"✅ User ID {user_id} is new - no existing enrollments")
            else:
                logger.warning("⚠️  Could not connect to database, skipping enrollment check")
        except Exception as db_error:
            logger.error(f"❌ Database check error: {db_error}")
            # Continue anyway - better to try enrollment than fail here
        
        # Check MQTT client
        logger.info("🔍 Checking MQTT client...")
        if mqtt_client is None:
            logger.error("❌ MQTT client is None")
            return jsonify({'error': 'MQTT client not initialized. Please restart the web UI.'}), 500
        
        # Check if MQTT client is connected
        if not mqtt_client.is_connected():
            logger.warning("⚠️  MQTT client not connected, attempting to reconnect...")
            try:
                mqtt_client.reconnect()
                # Wait a bit for reconnection
                import time
                time.sleep(1)
                
                if not mqtt_client.is_connected():
                    logger.error("❌ MQTT reconnection failed")
                    return jsonify({
                        'error': 'MQTT client not connected to broker. Please check MQTT broker status.',
                        'details': f'Broker: {MQTT_BROKER}:{MQTT_PORT}'
                    }), 503
                else:
                    logger.info("✅ MQTT client reconnected successfully")
            except Exception as reconnect_error:
                logger.error(f"❌ MQTT reconnection error: {reconnect_error}")
                return jsonify({
                    'error': f'MQTT connection failed: {str(reconnect_error)}',
                    'details': f'Broker: {MQTT_BROKER}:{MQTT_PORT}'
                }), 503
        
        logger.info(f"✅ MQTT client connected and ready")
        
        # Start tracking enrollment
        target_sensor = data.get('target_sensor')  # Optional: specific sensor
        enrollment_data = enrollment_manager.start_enrollment(
            user_id=int(user_id),
            username=str(username),
            requested_by=session.get('username', 'admin'),
            target_sensor=target_sensor
        )
        enrollment_id = enrollment_data['enrollment_id']
        
        # Prepare enrollment command
        enrollment_command = {
            'fingerprint_id': int(user_id),  # Ensure it's an integer
            'user_name': str(username),      # Ensure it's a string
            'timestamp': datetime.now().isoformat(),
            'source': 'web_ui',
            'requested_by': session.get('username', 'admin'),
            'enrollment_id': enrollment_id,  # Include enrollment ID for tracking
            'target_sensor': target_sensor   # Optional: specific sensor to enroll
        }
        
        logger.info(f"📤 Sending enrollment command to MQTT topic: WHAC/Store001/add_user")
        logger.info(f"📦 Payload: {enrollment_command}")
        
        # Update status to in_progress
        enrollment_manager.update_enrollment_status(
            enrollment_id,
            'in_progress',
            progress=10,
            progress_message='Sending enrollment command to local machine...'
        )
        
        # Publish to MQTT
        try:
            result = mqtt_client.publish(
                'WHAC/Store001/add_user',
                json.dumps(enrollment_command),
                qos=1
            )
            
            logger.info(f"📡 MQTT publish result: rc={result.rc}, mid={result.mid}")
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info("✅ Enrollment command sent successfully!")
                logger.info("⏳ Waiting for local machine to complete enrollment...")
                logger.info("=" * 80)
                
                # Update status
                enrollment_manager.update_enrollment_status(
                    enrollment_id,
                    'in_progress',
                    progress=20,
                    progress_message='Waiting for fingerprint scan on sensor...'
                )
                
                return jsonify({
                    'message': 'Enrollment command sent. Please follow instructions on the fingerprint scanner.',
                    'user_id': user_id,
                    'username': username,
                    'status': 'enrollment_started',
                    'enrollment_id': enrollment_id
                }), 200
            else:
                # Map MQTT error codes to user-friendly messages
                error_messages = {
                    mqtt.MQTT_ERR_NO_CONN: 'Not connected to MQTT broker',
                    mqtt.MQTT_ERR_PROTOCOL: 'MQTT protocol error',
                    mqtt.MQTT_ERR_INVAL: 'Invalid MQTT parameters',
                    mqtt.MQTT_ERR_ERRNO: 'System error',
                }
                error_msg = error_messages.get(result.rc, f'Unknown MQTT error (code: {result.rc})')
                
                logger.error(f"❌ Failed to send enrollment command: {error_msg}")
                
                # Update enrollment status to error
                enrollment_manager.complete_enrollment(
                    enrollment_id,
                    success=False,
                    error_message=error_msg,
                    progress_message=f'Failed to send command: {error_msg}'
                )
                
                return jsonify({
                    'error': f'Failed to send enrollment command: {error_msg}',
                    'mqtt_error_code': result.rc,
                    'suggestion': 'Please check MQTT broker connection and try again.',
                    'enrollment_id': enrollment_id
                }), 500
                
        except Exception as mqtt_error:
            logger.error(f"❌ MQTT publish exception: {mqtt_error}")
            import traceback
            logger.error(f"❌ MQTT Traceback: {traceback.format_exc()}")
            
            # Update enrollment status to error
            if enrollment_id:
                enrollment_manager.complete_enrollment(
                    enrollment_id,
                    success=False,
                    error_message=str(mqtt_error),
                    progress_message=f'MQTT error: {str(mqtt_error)}'
                )
            
            return jsonify({
                'error': f'MQTT error: {str(mqtt_error)}',
                'enrollment_id': enrollment_id
            }), 500
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ FATAL ERROR in enroll_user: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': f'Fatal error: {str(e)}',
            'error_type': type(e).__name__
        }), 500

@app.route('/api/audio/self_inspection', methods=['POST'])
@login_required
def trigger_self_inspection():
    """Trigger self-inspection audio on local machine via MQTT"""
    try:
        logger.info("=" * 80)
        logger.info("🔊 SELF-INSPECTION AUDIO REQUEST")
        
        # Check MQTT client
        if not mqtt_client:
            logger.error("❌ MQTT client not initialized")
            return jsonify({'error': 'MQTT client not initialized. Please restart the web UI.'}), 500
        
        # Check if MQTT client is connected
        if not mqtt_client.is_connected():
            logger.warning("⚠️  MQTT client not connected, attempting to reconnect...")
            try:
                mqtt_client.reconnect()
                import time
                time.sleep(1)
                
                if not mqtt_client.is_connected():
                    logger.error("❌ MQTT reconnection failed")
                    return jsonify({
                        'error': 'MQTT client not connected to broker.',
                        'details': f'Broker: {MQTT_BROKER}:{MQTT_PORT}'
                    }), 503
                else:
                    logger.info("✅ MQTT client reconnected successfully")
            except Exception as reconnect_error:
                logger.error(f"❌ MQTT reconnection error: {reconnect_error}")
                return jsonify({
                    'error': f'MQTT connection failed: {str(reconnect_error)}',
                    'details': f'Broker: {MQTT_BROKER}:{MQTT_PORT}'
                }), 503
        
        logger.info(f"✅ MQTT client connected and ready")
        
        # Prepare audio command
        audio_command = {
            'command': 'self_inspection',
            'timestamp': datetime.now().isoformat(),
            'source': 'web_ui',
            'requested_by': session.get('username', 'admin')
        }
        
        logger.info(f"📤 Sending audio command to MQTT topic: {MQTT_AUDIO_TOPIC}")
        logger.info(f"📦 Payload: {audio_command}")
        
        # Publish to MQTT
        try:
            result = mqtt_client.publish(
                MQTT_AUDIO_TOPIC,
                json.dumps(audio_command),
                qos=1
            )
            
            logger.info(f"📡 MQTT publish result: rc={result.rc}, mid={result.mid}")
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info("✅ Self-inspection audio command sent successfully!")
                logger.info("=" * 80)
                
                return jsonify({
                    'message': 'Self-inspection audio command sent successfully.',
                    'status': 'queued',
                    'timestamp': audio_command['timestamp']
                }), 200
            else:
                error_messages = {
                    mqtt.MQTT_ERR_NO_CONN: 'Not connected to MQTT broker',
                    mqtt.MQTT_ERR_PROTOCOL: 'MQTT protocol error',
                    mqtt.MQTT_ERR_INVAL: 'Invalid MQTT parameters',
                    mqtt.MQTT_ERR_ERRNO: 'System error',
                }
                error_msg = error_messages.get(result.rc, f'Unknown MQTT error (code: {result.rc})')
                
                logger.error(f"❌ Failed to send audio command: {error_msg}")
                return jsonify({
                    'error': f'Failed to send audio command: {error_msg}',
                    'mqtt_error_code': result.rc
                }), 500
                
        except Exception as mqtt_error:
            logger.error(f"❌ MQTT publish exception: {mqtt_error}")
            import traceback
            logger.error(f"❌ MQTT Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'MQTT error: {str(mqtt_error)}'}), 500
        
    except Exception as e:
        logger.error(f"❌ Error in trigger_self_inspection: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance')
@login_required
def get_attendance():
    """Get attendance records with pagination and date filtering"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build WHERE clause for date filtering
        where_clauses = []
        params = []
        
        if start_date:
            where_clauses.append("attendance_date >= %s")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("attendance_date <= %s")
            params.append(end_date)
        
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM attendance_summary {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get attendance records with pagination
        query = f"""
            SELECT 
                attendance_date,
                user_id,
                username,
                clock_in,
                clock_out,
                hours_worked,
                total_granted,
                location_in_display,
                location_out_display
            FROM attendance_summary 
            {where_sql}
            ORDER BY attendance_date DESC, user_id
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        cursor.execute(query, params)
        
        attendance = cursor.fetchall()
        conn.close()
        
        # Convert dates to ISO format for JSON serialization
        attendance_list = []
        for row in attendance:
            record = dict(row)
            # Convert date objects to strings
            if record.get('attendance_date'):
                record['attendance_date'] = record['attendance_date'].isoformat() if hasattr(record['attendance_date'], 'isoformat') else str(record['attendance_date'])
            if record.get('clock_in'):
                record['clock_in'] = record['clock_in'].isoformat() if hasattr(record['clock_in'], 'isoformat') else str(record['clock_in'])
            if record.get('clock_out'):
                record['clock_out'] = record['clock_out'].isoformat() if hasattr(record['clock_out'], 'isoformat') else str(record['clock_out'])
            attendance_list.append(record)
        
        return jsonify({
            'attendance': attendance_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page if total > 0 else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting attendance: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/report')
@login_required
def get_attendance_report():
    """Generate attendance report (CSV format)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build WHERE clause for date filtering
        where_clauses = []
        params = []
        
        if start_date:
            where_clauses.append("attendance_date >= %s")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("attendance_date <= %s")
            params.append(end_date)
        
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
        
        # Get all attendance records (no pagination for report)
        query = f"""
            SELECT 
                attendance_date,
                user_id,
                username,
                clock_in,
                clock_out,
                hours_worked,
                total_granted,
                location_in_display,
                location_out_display
            FROM attendance_summary 
            {where_sql}
            ORDER BY attendance_date DESC, user_id
        """
        cursor.execute(query, params)
        
        attendance = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts with date serialization
        attendance_list = []
        for row in attendance:
            record = dict(row)
            if record.get('attendance_date'):
                record['attendance_date'] = record['attendance_date'].isoformat() if hasattr(record['attendance_date'], 'isoformat') else str(record['attendance_date'])
            if record.get('clock_in'):
                record['clock_in'] = record['clock_in'].isoformat() if hasattr(record['clock_in'], 'isoformat') else str(record['clock_in'])
            if record.get('clock_out'):
                record['clock_out'] = record['clock_out'].isoformat() if hasattr(record['clock_out'], 'isoformat') else str(record['clock_out'])
            attendance_list.append(record)
        
        return jsonify({
            'attendance': attendance_list,
            'total': len(attendance_list),
            'start_date': start_date,
            'end_date': end_date
        })
        
    except Exception as e:
        logger.error(f"Error generating attendance report: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🚀 STARTING WHAC WEB UI")
    logger.info("=" * 80)
    logger.info(f"📊 SocketIO async_mode: {socketio.async_mode}")
    logger.info(f"🌐 CORS: Enabled for all origins")
    logger.info(f"🔧 Debug mode: {app.config.get('DEBUG', False)}")
    logger.info(f"🌍 Host: 0.0.0.0 (all interfaces)")
    logger.info(f"🔌 Port: 5000")
    logger.info("=" * 80)
    
    # Setup MQTT client for real-time notifications
    setup_mqtt_client()
    
    logger.info("=" * 80)
    logger.info("✅ MQTT client setup complete")
    logger.info("🎯 Starting Flask-SocketIO server...")
    logger.info("=" * 80)
    
    # Run the application with SocketIO
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
