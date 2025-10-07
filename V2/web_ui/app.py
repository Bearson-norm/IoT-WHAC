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
import paho.mqtt.client as mqtt
import threading
import bcrypt
import secrets
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'whac_fingerprint_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'whac_master',
    'user': 'postgres',
    'password': 'Admin123',
    'port': 5432
}

# MQTT configuration
MQTT_BROKER = "103.87.67.139"
MQTT_PORT = 1883
MQTT_ACTION_TOPIC = "WHAC/Store001/action"
MQTT_SCAN_TOPIC = "WHAC/Store001/in"

# Global MQTT client
mqtt_client = None

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
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info("✓ MQTT client connected for real-time notifications")
    except Exception as e:
        logger.error(f"MQTT client setup error: {e}")

def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    if rc == 0:
        logger.info("MQTT client connected")
        client.subscribe(MQTT_SCAN_TOPIC)
        logger.info(f"Subscribed to {MQTT_SCAN_TOPIC}")
    else:
        logger.error(f"MQTT connection failed with code {rc}")

def on_mqtt_message(client, userdata, msg):
    """Handle incoming MQTT scan messages"""
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"Received scan notification: {payload}")
        
        # Emit to all connected WebSocket clients
        socketio.emit('scan_notification', {
            'user_id': payload.get('fingerprint_id'),
            'action': payload.get('action'),
            'timestamp': payload.get('timestamp'),
            'store_id': payload.get('store_id'),
            'device_id': payload.get('device_id')
        })
        
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to WHAC Fingerprint System'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('grant_access')
def handle_grant_access(data):
    """Handle grant access command"""
    try:
        user_id = data.get('user_id')
        action = data.get('action', 'access_granted')
        
        # Send MQTT command to control relay
        send_relay_command('grant', user_id, action)
        
        # Log to database
        log_manual_action(user_id, action, 'granted')
        
        emit('action_result', {
            'status': 'success',
            'message': f'Access granted for user {user_id}',
            'action': 'granted'
        })
        
    except Exception as e:
        logger.error(f"Error granting access: {e}")
        emit('action_result', {
            'status': 'error',
            'message': str(e)
        })

@socketio.on('deny_access')
def handle_deny_access(data):
    """Handle deny access command"""
    try:
        user_id = data.get('user_id')
        action = data.get('action', 'access_denied')
        
        # Send MQTT command to control relay
        send_relay_command('deny', user_id, action)
        
        # Log to database
        log_manual_action(user_id, action, 'denied')
        
        emit('action_result', {
            'status': 'success',
            'message': f'Access denied for user {user_id}',
            'action': 'denied'
        })
        
    except Exception as e:
        logger.error(f"Error denying access: {e}")
        emit('action_result', {
            'status': 'error',
            'message': str(e)
        })

def send_relay_command(command, user_id, action):
    """Send relay control command via MQTT"""
    try:
        if not mqtt_client:
            logger.error("MQTT client not available")
            return False
        
        payload = {
            'command': command,
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'source': 'web_ui'
        }
        
        result = mqtt_client.publish(MQTT_ACTION_TOPIC, json.dumps(payload))
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"✓ Relay command sent: {command} for user {user_id}")
            return True
        else:
            logger.error(f"✗ Failed to send relay command (rc: {result.rc})")
            return False
            
    except Exception as e:
        logger.error(f"Error sending relay command: {e}")
        return False

def log_manual_action(user_id, action, granted_denied):
    """Log manual action to database"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get username if user_id exists
        username = None
        if user_id and user_id > 0:
            cursor.execute("SELECT username FROM store_001 WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                username = result[0]
        
        # Insert action log
        cursor.execute("""
            INSERT INTO log_action (user_id, store_id, username, timestamp, action, granted_denied)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, 'Store001', username, datetime.now(), action, granted_denied))
        
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

@app.route('/api/dashboard_stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get total users
        cursor.execute("SELECT COUNT(*) as total_users FROM store_001")
        total_users = cursor.fetchone()['total_users']
        
        # Get total scans today
        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(*) as total_scans_today 
            FROM log_data 
            WHERE DATE(timestamp) = %s
        """, (today,))
        total_scans_today = cursor.fetchone()['total_scans_today']
        
        # Get successful access today
        cursor.execute("""
            SELECT COUNT(*) as successful_access_today 
            FROM log_action 
            WHERE DATE(timestamp) = %s AND granted_denied = 'granted'
        """, (today,))
        successful_access_today = cursor.fetchone()['successful_access_today']
        
        # Get denied access today
        cursor.execute("""
            SELECT COUNT(*) as denied_access_today 
            FROM log_action 
            WHERE DATE(timestamp) = %s AND granted_denied = 'denied'
        """, (today,))
        denied_access_today = cursor.fetchone()['denied_access_today']
        
        # Get recent activity (last 10 scans)
        cursor.execute("""
            SELECT * FROM fingerprint_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        recent_activity = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'total_scans_today': total_scans_today,
            'successful_access_today': successful_access_today,
            'denied_access_today': denied_access_today,
            'recent_activity': [dict(row) for row in recent_activity]
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
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
    """Get all users from store_001"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT s.*, 
                   COUNT(ld.id) as total_scans,
                   MAX(ld.timestamp) as last_scan
            FROM store_001 s
            LEFT JOIN log_data ld ON s.user_id = ld.user_id
            GROUP BY s.id, s.user_id, s.username, s.finger_template_id, s.created_at, s.updated_at
            ORDER BY s.username
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
def daily_stats_chart():
    """Get daily statistics for charts"""
    try:
        days = int(request.args.get('days', 7))
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get daily scan counts
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as scan_count
            FROM log_data 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (days,))
        
        daily_scans = cursor.fetchall()
        
        # Get daily access granted/denied
        cursor.execute("""
            SELECT DATE(timestamp) as date, 
                   granted_denied,
                   COUNT(*) as count
            FROM log_action 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(timestamp), granted_denied
            ORDER BY date
        """, (days,))
        
        daily_access = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'daily_scans': [dict(row) for row in daily_scans],
            'daily_access': [dict(row) for row in daily_access]
        })
        
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_user', methods=['POST'])
@login_required
def add_user():
    """Add new user to store_001"""
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
        
        cursor.execute("""
            INSERT INTO store_001 (user_id, username, finger_template_id)
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
    """Delete user from store_001"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM store_001 WHERE user_id = %s", (user_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Setup MQTT client for real-time notifications
    setup_mqtt_client()
    
    # Run the application with SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
