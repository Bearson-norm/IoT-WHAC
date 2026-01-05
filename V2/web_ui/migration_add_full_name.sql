-- Migration Script: Add full_name support for user linking
-- Run this script on existing database to add full_name columns

-- Add full_name column to user_sensor_1
ALTER TABLE user_sensor_1 
ADD COLUMN IF NOT EXISTS full_name VARCHAR(200);

-- Add full_name column to user_sensor_2
ALTER TABLE user_sensor_2 
ADD COLUMN IF NOT EXISTS full_name VARCHAR(200);

-- Add full_name and user_id tracking columns to attendance
ALTER TABLE attendance 
ADD COLUMN IF NOT EXISTS full_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS user_id_in INTEGER,
ADD COLUMN IF NOT EXISTS user_id_out INTEGER;

-- Update existing attendance records with full_name from sensor tables
UPDATE attendance a
SET full_name = COALESCE(
    (SELECT s1.full_name FROM user_sensor_1 s1 WHERE s1.user_id = a.user_id AND a.device_id_in = 'AS608_001'),
    (SELECT s2.full_name FROM user_sensor_2 s2 WHERE s2.user_id = a.user_id AND a.device_id_out = 'AS608_002')
)
WHERE a.full_name IS NULL;

-- Drop and recreate the attendance_summary view
DROP VIEW IF EXISTS attendance_summary CASCADE;

CREATE VIEW attendance_summary AS
SELECT 
    a.id,
    a.user_id,
    a.username,
    a.full_name,
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
    a.user_id_in,
    a.user_id_out,
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

-- Create index on full_name for faster queries
CREATE INDEX IF NOT EXISTS idx_user_sensor_1_full_name ON user_sensor_1(full_name);
CREATE INDEX IF NOT EXISTS idx_user_sensor_2_full_name ON user_sensor_2(full_name);
CREATE INDEX IF NOT EXISTS idx_attendance_full_name ON attendance(full_name);

-- Success message
SELECT 'Migration completed successfully! full_name columns added.' as result;







