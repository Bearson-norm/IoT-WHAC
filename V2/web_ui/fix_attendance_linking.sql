-- Fix Attendance Linking by Full Name
-- This script changes the attendance table to use full_name as the primary key
-- instead of user_id for proper linking across sensors

-- Step 1: Drop existing unique constraint
ALTER TABLE attendance DROP CONSTRAINT IF EXISTS attendance_user_id_attendance_date_key;

-- Step 2: Add new unique constraint on full_name + attendance_date
ALTER TABLE attendance ADD CONSTRAINT attendance_full_name_date_key 
    UNIQUE (full_name, attendance_date);

-- Step 3: Make user_id nullable (since we'll track user_id_in and user_id_out separately)
ALTER TABLE attendance ALTER COLUMN user_id DROP NOT NULL;

-- Step 4: Update existing data - merge records with same full_name and date
-- This will consolidate split records into single records

-- Create a temporary table with merged data
CREATE TEMP TABLE temp_attendance AS
SELECT 
    MIN(id) as id,
    full_name,
    attendance_date,
    MAX(user_id_in) as user_id_in,
    MAX(user_id_out) as user_id_out,
    COALESCE(MAX(user_id_in), MAX(user_id_out), MIN(user_id)) as user_id,
    MAX(username) as username,
    MIN(clock_in) as clock_in,  -- Earliest clock in
    MAX(clock_out) as clock_out,  -- Latest clock out
    MIN(first_granted) as first_granted,
    MAX(last_granted) as last_granted,
    SUM(total_granted) as total_granted,
    MAX(device_id_in) as device_id_in,
    MAX(device_id_out) as device_id_out,
    MAX(sensor_location_in) as sensor_location_in,
    MAX(sensor_location_out) as sensor_location_out,
    MIN(created_at) as created_at,
    MAX(updated_at) as updated_at
FROM attendance
WHERE full_name IS NOT NULL
GROUP BY full_name, attendance_date;

-- Delete old records and insert merged records
DELETE FROM attendance WHERE full_name IS NOT NULL;

INSERT INTO attendance (
    id, full_name, attendance_date, user_id_in, user_id_out, user_id,
    username, clock_in, clock_out, first_granted, last_granted, total_granted,
    device_id_in, device_id_out, sensor_location_in, sensor_location_out,
    created_at, updated_at
)
SELECT * FROM temp_attendance;

-- Reset sequence
SELECT setval('attendance_id_seq', (SELECT MAX(id) FROM attendance));

-- Step 5: Create index on full_name for better performance
CREATE INDEX IF NOT EXISTS idx_attendance_full_name_date ON attendance(full_name, attendance_date);

-- Success message
SELECT 'Attendance linking fixed! Records with same full_name are now merged.' as result;







