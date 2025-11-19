-- PostgreSQL Database Setup for WHAC Fingerprint System
-- Database: whac_master
-- Username: postgres
-- Password: Admin123

-- Create database (run as superuser)
-- CREATE DATABASE whac_master;

-- Connect to whac_master database
-- \c whac_master;

-- Create tables

-- Web UI Users table for authentication
CREATE TABLE IF NOT EXISTS web_users (
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

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES web_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS log_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    store_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finger_template_id INTEGER,
    device_id VARCHAR(50),
    sensor_location VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS log_action (
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

CREATE TABLE IF NOT EXISTS store_001 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE,
    username VARCHAR(100) NOT NULL,
    finger_template_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add missing columns to existing tables (for migration compatibility)
-- This ensures columns exist even if tables were created before
ALTER TABLE log_data 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20);

ALTER TABLE log_action 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_log_data_timestamp ON log_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_data_store_id ON log_data(store_id);
CREATE INDEX IF NOT EXISTS idx_log_data_user_id ON log_data(user_id);
CREATE INDEX IF NOT EXISTS idx_log_data_device_id ON log_data(device_id);
CREATE INDEX IF NOT EXISTS idx_log_data_sensor_location ON log_data(sensor_location);

CREATE INDEX IF NOT EXISTS idx_log_action_timestamp ON log_action(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_action_store_id ON log_action(store_id);
CREATE INDEX IF NOT EXISTS idx_log_action_user_id ON log_action(user_id);
CREATE INDEX IF NOT EXISTS idx_log_action_device_id ON log_action(device_id);
CREATE INDEX IF NOT EXISTS idx_log_action_sensor_location ON log_action(sensor_location);

CREATE INDEX IF NOT EXISTS idx_store_001_user_id ON store_001(user_id);
CREATE INDEX IF NOT EXISTS idx_store_001_finger_template_id ON store_001(finger_template_id);

-- Insert sample data for testing
INSERT INTO store_001 (user_id, username, finger_template_id) VALUES 
(1, 'John Doe', 1),
(2, 'Jane Smith', 2),
(3, 'Bob Johnson', 3)
ON CONFLICT (user_id) DO NOTHING;

-- Insert default admin user (password: admin123)
-- Password hash for 'admin123' using bcrypt (verified working)
INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, login_attempts, locked_until) VALUES 
('admin', '$2b$12$7cD0.neGPVGRNL3X9nzY6uc5G1Ek8OB/PBhYDvcjKvZ0mcYK9yOyS', 'System Administrator', 'admin@whac.com', 'admin', TRUE, 0, NULL)
ON CONFLICT (username) DO UPDATE SET 
    password_hash = EXCLUDED.password_hash,
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    is_active = TRUE,
    login_attempts = 0,
    locked_until = NULL;

-- Insert sample log data
INSERT INTO log_data (user_id, store_id, finger_template_id) VALUES 
(1, 'Store001', 1),
(2, 'Store001', 2),
(3, 'Store001', 3)
ON CONFLICT DO NOTHING;

-- Insert sample action logs
INSERT INTO log_action (user_id, store_id, username, action, granted_denied) VALUES 
(1, 'Store001', 'John Doe', 'access_granted', 'granted'),
(2, 'Store001', 'Jane Smith', 'access_granted', 'granted'),
(3, 'Store001', 'Bob Johnson', 'access_denied', 'denied')
ON CONFLICT DO NOTHING;

-- Create a view for easy querying
CREATE OR REPLACE VIEW fingerprint_logs AS
SELECT 
    ld.id,
    ld.user_id,
    ld.store_id,
    ld.timestamp,
    ld.finger_template_id,
    ld.device_id,
    ld.sensor_location,
    s.username,
    CASE 
        WHEN ld.user_id IS NULL THEN 'Unknown User'
        ELSE s.username
    END as display_name,
    CASE
        WHEN ld.device_id = 'AS608_001' THEN 'Pintu Masuk'
        WHEN ld.device_id = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(ld.sensor_location, 'Unknown')
    END as location_display
FROM log_data ld
LEFT JOIN store_001 s ON ld.user_id = s.user_id
ORDER BY ld.timestamp DESC;

-- Create a view for action logs
CREATE OR REPLACE VIEW action_logs AS
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

-- Attendance tracking table for clock in/out
CREATE TABLE IF NOT EXISTS attendance (
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

-- Create indexes for attendance table
CREATE INDEX IF NOT EXISTS idx_attendance_user_id ON attendance(user_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, attendance_date);

-- Create view for attendance summary
CREATE OR REPLACE VIEW attendance_summary AS
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

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
