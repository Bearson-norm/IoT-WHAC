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
    user_id INTEGER REFERENCES web_users(id),
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_log_data_timestamp ON log_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_data_store_id ON log_data(store_id);
CREATE INDEX IF NOT EXISTS idx_log_data_user_id ON log_data(user_id);

CREATE INDEX IF NOT EXISTS idx_log_action_timestamp ON log_action(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_action_store_id ON log_action(store_id);
CREATE INDEX IF NOT EXISTS idx_log_action_user_id ON log_action(user_id);

CREATE INDEX IF NOT EXISTS idx_store_001_user_id ON store_001(user_id);
CREATE INDEX IF NOT EXISTS idx_store_001_finger_template_id ON store_001(finger_template_id);

-- Insert sample data for testing
INSERT INTO store_001 (user_id, username, finger_template_id) VALUES 
(1, 'John Doe', 1),
(2, 'Jane Smith', 2),
(3, 'Bob Johnson', 3)
ON CONFLICT (user_id) DO NOTHING;

-- Insert default admin user (password: admin123)
-- Password hash for 'admin123' using bcrypt
INSERT INTO web_users (username, password_hash, full_name, email, role) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8Kz8Kz2', 'System Administrator', 'admin@whac.com', 'admin')
ON CONFLICT (username) DO NOTHING;

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
    s.username,
    CASE 
        WHEN ld.user_id IS NULL THEN 'Unknown User'
        ELSE s.username
    END as display_name
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
    CASE 
        WHEN la.granted_denied = 'granted' THEN 'success'
        WHEN la.granted_denied = 'denied' THEN 'danger'
        ELSE 'warning'
    END as status_class
FROM log_action la
ORDER BY la.timestamp DESC;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
