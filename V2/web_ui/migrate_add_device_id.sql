-- Migration: Add device_id and sensor_location columns to log tables for multi-sensor support
-- Date: 2025-11-19
-- Description: Add device_id and sensor_location columns to log_data and log_action tables
--              to support tracking which sensor (AS608_001, AS608_002, etc.) and which
--              location (masuk/keluar) generated each log entry.

-- Add device_id to log_data table
ALTER TABLE log_data 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001';

-- Add sensor_location to log_data table
ALTER TABLE log_data 
ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20) DEFAULT 'unknown';

-- Add device_id to log_action table
ALTER TABLE log_action 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001';

-- Add sensor_location to log_action table
ALTER TABLE log_action 
ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20) DEFAULT 'unknown';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_log_data_device_id ON log_data(device_id);
CREATE INDEX IF NOT EXISTS idx_log_data_sensor_location ON log_data(sensor_location);
CREATE INDEX IF NOT EXISTS idx_log_action_device_id ON log_action(device_id);
CREATE INDEX IF NOT EXISTS idx_log_action_sensor_location ON log_action(sensor_location);

-- Verify the migration
\d log_data
\d log_action

-- Show sample data
SELECT 'log_data count:' as info, COUNT(*) as count FROM log_data
UNION ALL
SELECT 'log_action count:' as info, COUNT(*) as count FROM log_action;

SELECT 'Migration completed successfully!' as status;

