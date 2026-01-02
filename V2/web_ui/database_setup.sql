-- PostgreSQL Database Setup for WHAC Fingerprint System
-- Database: whac_master
-- Username: postgres
-- Password: Admin123

-- Create database (run as superuser)
-- CREATE DATABASE whac_master;

-- Connect to whac_master database
-- \c whac_master;

-- ============================================
-- DROP ALL EXISTING TABLES AND VIEWS
-- ============================================
-- Drop views first (they depend on tables)
DROP VIEW IF EXISTS fingerprint_logs CASCADE;
DROP VIEW IF EXISTS action_logs CASCADE;
DROP VIEW IF EXISTS attendance_summary CASCADE;

-- Drop all existing tables
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS store_001 CASCADE;
DROP TABLE IF EXISTS log_data CASCADE;
DROP TABLE IF EXISTS log_action CASCADE;
DROP TABLE IF EXISTS access_log CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS user_sensor_1 CASCADE;
DROP TABLE IF EXISTS user_sensor_2 CASCADE;
DROP TABLE IF EXISTS user_machine CASCADE;
DROP TABLE IF EXISTS web_users CASCADE;

-- ============================================
-- CREATE NEW TABLES
-- ============================================

-- 1. Web UI Users table for authentication
CREATE TABLE web_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- 2. User sessions table (for web UI authentication)
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES web_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. User Sensor 1 (AS608_001 - Pintu Masuk)
CREATE TABLE user_sensor_1 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    finger_template_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. User Sensor 2 (AS608_002 - Pintu Keluar)
CREATE TABLE user_sensor_2 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    finger_template_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. User Machine (unified table for user enrollment from modal)
CREATE TABLE user_machine (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    nama VARCHAR(100) NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    posisi VARCHAR(50),
    finger_template_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, device_id)
);

-- 6. Log Data (fingerprint scan logs)
CREATE TABLE log_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    store_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finger_template_id INTEGER,
    device_id VARCHAR(50),
    sensor_location VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Log Action (access granted/denied logs)
CREATE TABLE log_action (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    store_id VARCHAR(50) NOT NULL,
    username VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50) NOT NULL,
    granted_denied VARCHAR(20) NOT NULL,
    device_id VARCHAR(50),
    sensor_location VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Access Log (access granted/denied logs from modal)
CREATE TABLE access_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    nama VARCHAR(100),
    device_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_source VARCHAR(50) DEFAULT 'modal',
    finger_template_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Attendance (attendance tracking)
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username VARCHAR(100),
    attendance_date DATE NOT NULL,
    clock_in TIMESTAMP,
    clock_out TIMESTAMP,
    first_granted TIMESTAMP NOT NULL,
    last_granted TIMESTAMP NOT NULL,
    total_granted INTEGER DEFAULT 1,
    device_id_in VARCHAR(50),
    device_id_out VARCHAR(50),
    sensor_location_in VARCHAR(20),
    sensor_location_out VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, attendance_date)
);

-- ============================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================

-- Indexes for user_sensor_1
CREATE INDEX idx_user_sensor_1_user_id ON user_sensor_1(user_id);
CREATE INDEX idx_user_sensor_1_finger_template_id ON user_sensor_1(finger_template_id);

-- Indexes for user_sensor_2
CREATE INDEX idx_user_sensor_2_user_id ON user_sensor_2(user_id);
CREATE INDEX idx_user_sensor_2_finger_template_id ON user_sensor_2(finger_template_id);

-- Indexes for user_machine
CREATE INDEX idx_user_machine_user_id ON user_machine(user_id);
CREATE INDEX idx_user_machine_device_id ON user_machine(device_id);
CREATE INDEX idx_user_machine_user_device ON user_machine(user_id, device_id);
CREATE INDEX idx_user_machine_finger_template_id ON user_machine(finger_template_id);

-- Indexes for log_data
CREATE INDEX idx_log_data_timestamp ON log_data(timestamp);
CREATE INDEX idx_log_data_store_id ON log_data(store_id);
CREATE INDEX idx_log_data_user_id ON log_data(user_id);
CREATE INDEX idx_log_data_device_id ON log_data(device_id);
CREATE INDEX idx_log_data_sensor_location ON log_data(sensor_location);

-- Indexes for log_action
CREATE INDEX idx_log_action_timestamp ON log_action(timestamp);
CREATE INDEX idx_log_action_store_id ON log_action(store_id);
CREATE INDEX idx_log_action_user_id ON log_action(user_id);
CREATE INDEX idx_log_action_device_id ON log_action(device_id);
CREATE INDEX idx_log_action_sensor_location ON log_action(sensor_location);

-- Indexes for access_log
CREATE INDEX idx_access_log_user_id ON access_log(user_id);
CREATE INDEX idx_access_log_device_id ON access_log(device_id);
CREATE INDEX idx_access_log_status ON access_log(status);
CREATE INDEX idx_access_log_timestamp ON access_log(timestamp);
CREATE INDEX idx_access_log_user_device ON access_log(user_id, device_id);

-- Indexes for attendance
CREATE INDEX idx_attendance_user_id ON attendance(user_id);
CREATE INDEX idx_attendance_date ON attendance(attendance_date);
CREATE INDEX idx_attendance_user_date ON attendance(user_id, attendance_date);

-- ============================================
-- CREATE VIEWS FOR EASY QUERYING
-- ============================================

-- View for fingerprint logs (combines log_data with user info from both sensors)
CREATE VIEW fingerprint_logs AS
SELECT 
    ld.id,
    ld.user_id,
    ld.store_id,
    ld.timestamp,
    ld.finger_template_id,
    ld.device_id,
    ld.sensor_location,
    COALESCE(s1.username, s2.username) as username,
    CASE 
        WHEN ld.user_id IS NULL THEN 'Unknown User'
        ELSE COALESCE(s1.username, s2.username)
    END as display_name,
    CASE
        WHEN ld.device_id = 'AS608_001' THEN 'Pintu Masuk'
        WHEN ld.device_id = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(ld.sensor_location, 'Unknown')
    END as location_display
FROM log_data ld
LEFT JOIN user_sensor_1 s1 ON ld.user_id = s1.user_id AND ld.device_id = 'AS608_001'
LEFT JOIN user_sensor_2 s2 ON ld.user_id = s2.user_id AND ld.device_id = 'AS608_002'
ORDER BY ld.timestamp DESC;

-- View for action logs
CREATE VIEW action_logs AS
SELECT 
    la.id,
    la.user_id,
    la.store_id,
    la.username,
    la.timestamp,
    la.action,
    la.granted_denied,
    la.device_id,
    la.sensor_location,
    CASE 
        WHEN la.granted_denied = 'granted' THEN 'success'
        WHEN la.granted_denied = 'denied' THEN 'danger'
        ELSE 'warning'
    END as status_class,
    CASE
        WHEN la.device_id = 'AS608_001' THEN 'Pintu Masuk'
        WHEN la.device_id = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(la.sensor_location, 'Unknown')
    END as location_display
FROM log_action la
ORDER BY la.timestamp DESC;

-- View for attendance summary
CREATE VIEW attendance_summary AS
SELECT 
    a.id,
    a.user_id,
    a.username,
    a.attendance_date,
    a.clock_in,
    a.clock_out,
    a.first_granted as first_access,
    a.last_granted as last_access,
    a.total_granted,
    a.device_id_in,
    a.device_id_out,
    a.sensor_location_in,
    a.sensor_location_out,
    CASE
        WHEN a.clock_in IS NOT NULL AND a.clock_out IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (a.clock_out - a.clock_in)) / 3600
        ELSE NULL
    END as hours_worked,
    CASE
        WHEN a.device_id_in = 'AS608_001' THEN 'Pintu Masuk'
        WHEN a.device_id_in = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(a.sensor_location_in, 'Unknown')
    END as location_in_display,
    CASE
        WHEN a.device_id_out = 'AS608_001' THEN 'Pintu Masuk'
        WHEN a.device_id_out = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(a.sensor_location_out, 'Unknown')
    END as location_out_display
FROM attendance a
ORDER BY a.attendance_date DESC, a.user_id;

-- ============================================
-- INSERT DEFAULT DATA
-- ============================================

-- Insert default admin user (password: Admin123)
-- Password hash for 'Admin123' using bcrypt (verified working)
INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, login_attempts, locked_until) VALUES 
('admin', '$2b$12$CSTFKuIf6vyTKPu5PifqVOJs14ULspN8ZuGUdu5yEgFpPh6y9X7me', 'System Administrator', 'admin@whac.com', 'admin', TRUE, 0, NULL)
ON CONFLICT (username) DO UPDATE SET 
    password_hash = EXCLUDED.password_hash,
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    is_active = TRUE,
    login_attempts = 0,
    locked_until = NULL;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
