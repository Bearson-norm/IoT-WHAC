-- Database Migration Script for 2 Sensor Support
-- Run this script if you already have an existing database
-- This adds device_id and sensor_location columns to existing tables

-- Add device_id and sensor_location columns to log_data table
ALTER TABLE log_data 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20);

-- Add device_id and sensor_location columns to log_action table
ALTER TABLE log_action 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_log_data_device_id ON log_data(device_id);
CREATE INDEX IF NOT EXISTS idx_log_data_sensor_location ON log_data(sensor_location);
CREATE INDEX IF NOT EXISTS idx_log_action_device_id ON log_action(device_id);
CREATE INDEX IF NOT EXISTS idx_log_action_sensor_location ON log_action(sensor_location);

-- Update views to include new columns
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

-- Migration complete
SELECT 'Migration completed successfully! New columns added: device_id, sensor_location' as status;


