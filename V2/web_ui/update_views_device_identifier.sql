-- =====================================================
-- Script untuk Update Views dengan Device In/Out Identifier
-- Database: whac_master
-- =====================================================
-- 
-- Script ini mengupdate views fingerprint_logs dan action_logs
-- untuk menambahkan identifier device_in dan device_out
-- =====================================================

-- =====================================================
-- 1. Update View fingerprint_logs dengan Device In/Out Identifier
-- =====================================================

DROP VIEW IF EXISTS fingerprint_logs CASCADE;

CREATE VIEW fingerprint_logs AS
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
    END as location_display,
    -- Device In/Out Identifier
    CASE
        WHEN ld.device_id = 'AS608_001' OR ld.sensor_location = 'masuk' THEN TRUE
        ELSE FALSE
    END as is_device_in,
    CASE
        WHEN ld.device_id = 'AS608_002' OR ld.sensor_location = 'keluar' THEN TRUE
        ELSE FALSE
    END as is_device_out,
    CASE
        WHEN ld.device_id = 'AS608_001' OR ld.sensor_location = 'masuk' THEN 'IN'
        WHEN ld.device_id = 'AS608_002' OR ld.sensor_location = 'keluar' THEN 'OUT'
        ELSE 'UNKNOWN'
    END as device_direction,
    CASE
        WHEN ld.device_id = 'AS608_001' OR ld.sensor_location = 'masuk' THEN 'Masuk'
        WHEN ld.device_id = 'AS608_002' OR ld.sensor_location = 'keluar' THEN 'Keluar'
        ELSE COALESCE(ld.sensor_location, 'Unknown')
    END as device_direction_display
FROM log_data ld
LEFT JOIN store_001 s ON ld.user_id = s.user_id AND ld.device_id = s.device_id
ORDER BY ld.timestamp DESC;

-- =====================================================
-- 2. Update View action_logs dengan Device In/Out Identifier
-- =====================================================

DROP VIEW IF EXISTS action_logs CASCADE;

CREATE VIEW action_logs AS
SELECT 
    la.id,
    la.user_id,
    la.store_id,
    COALESCE(s.username, 'Unknown User') as username,  -- Ambil dari store_001
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
    END as location_display,
    -- Device In/Out Identifier
    CASE
        WHEN la.device_id = 'AS608_001' OR la.sensor_location = 'masuk' THEN TRUE
        ELSE FALSE
    END as is_device_in,
    CASE
        WHEN la.device_id = 'AS608_002' OR la.sensor_location = 'keluar' THEN TRUE
        ELSE FALSE
    END as is_device_out,
    CASE
        WHEN la.device_id = 'AS608_001' OR la.sensor_location = 'masuk' THEN 'IN'
        WHEN la.device_id = 'AS608_002' OR la.sensor_location = 'keluar' THEN 'OUT'
        ELSE 'UNKNOWN'
    END as device_direction,
    CASE
        WHEN la.device_id = 'AS608_001' OR la.sensor_location = 'masuk' THEN 'Masuk'
        WHEN la.device_id = 'AS608_002' OR la.sensor_location = 'keluar' THEN 'Keluar'
        ELSE COALESCE(la.sensor_location, 'Unknown')
    END as device_direction_display
FROM log_action la
LEFT JOIN store_001 s ON la.user_id = s.user_id AND la.device_id = s.device_id
ORDER BY la.timestamp DESC;

-- =====================================================
-- 3. Verifikasi Views
-- =====================================================

-- Cek struktur view fingerprint_logs
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name = 'fingerprint_logs'
ORDER BY ordinal_position;

-- Cek struktur view action_logs
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name = 'action_logs'
ORDER BY ordinal_position;

-- Test query dengan device identifier
SELECT 
    id,
    user_id,
    username,
    timestamp,
    device_id,
    device_direction,
    device_direction_display,
    is_device_in,
    is_device_out
FROM fingerprint_logs
ORDER BY timestamp DESC
LIMIT 10;

-- =====================================================
-- Catatan:
-- =====================================================
-- 1. Views sudah di-update dengan identifier device_in dan device_out
-- 2. Kolom baru yang ditambahkan:
--    - is_device_in (BOOLEAN): TRUE jika device masuk (AS608_001 atau sensor_location='masuk')
--    - is_device_out (BOOLEAN): TRUE jika device keluar (AS608_002 atau sensor_location='keluar')
--    - device_direction (VARCHAR): 'IN', 'OUT', atau 'UNKNOWN'
--    - device_direction_display (VARCHAR): 'Masuk', 'Keluar', atau lokasi lain
--
-- 3. Query contoh:
--    -- Filter hanya device masuk
--    SELECT * FROM fingerprint_logs WHERE is_device_in = TRUE;
--    
--    -- Filter hanya device keluar
--    SELECT * FROM fingerprint_logs WHERE is_device_out = TRUE;
--    
--    -- Count per direction
--    SELECT device_direction, COUNT(*) 
--    FROM fingerprint_logs 
--    GROUP BY device_direction;
-- =====================================================












