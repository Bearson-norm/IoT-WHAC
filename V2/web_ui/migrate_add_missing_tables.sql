-- Migration Script: Add Missing Tables
-- Run this script if you have an existing database that's missing user_machine and access_log tables
-- This script is safe to run multiple times (uses IF NOT EXISTS)

-- ============================================
-- 1. Create user_machine table (if not exists)
-- ============================================
CREATE TABLE IF NOT EXISTS user_machine (
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

-- Indexes for user_machine
CREATE INDEX IF NOT EXISTS idx_user_machine_user_id ON user_machine(user_id);
CREATE INDEX IF NOT EXISTS idx_user_machine_device_id ON user_machine(device_id);
CREATE INDEX IF NOT EXISTS idx_user_machine_user_device ON user_machine(user_id, device_id);
CREATE INDEX IF NOT EXISTS idx_user_machine_finger_template_id ON user_machine(finger_template_id);

-- ============================================
-- 2. Create access_log table (if not exists)
-- ============================================
CREATE TABLE IF NOT EXISTS access_log (
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

-- Indexes for access_log
CREATE INDEX IF NOT EXISTS idx_access_log_user_id ON access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_access_log_device_id ON access_log(device_id);
CREATE INDEX IF NOT EXISTS idx_access_log_status ON access_log(status);
CREATE INDEX IF NOT EXISTS idx_access_log_timestamp ON access_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_access_log_user_device ON access_log(user_id, device_id);

-- ============================================
-- 3. Verification Queries
-- ============================================
-- Uncomment to verify tables were created:
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('user_machine', 'access_log');

-- SELECT COUNT(*) FROM user_machine;
-- SELECT COUNT(*) FROM access_log;

