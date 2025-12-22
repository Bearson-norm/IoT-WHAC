-- =====================================================
-- Script untuk Support Multiple Fingerprint per User per Device
-- Database: whac_master
-- =====================================================
-- 
-- Masalah: Saat ini store_001 hanya menyimpan satu finger_template_id
-- per user_id. Jika user enroll di dua sensor berbeda (masuk & keluar),
-- data akan di-overwrite dan menyebabkan kebingungan.
--
-- Solusi: Tambahkan device_id ke store_001 dan ubah constraint
-- menjadi composite unique key (user_id, device_id).
-- =====================================================

-- PERINGATAN: Backup database terlebih dahulu!
-- docker exec whac-postgres pg_dump -U postgres whac_master > backup_before_multi_sensor.sql

-- 1. Tambahkan kolom device_id ke store_001
ALTER TABLE store_001 
ADD COLUMN IF NOT EXISTS device_id VARCHAR(50) DEFAULT 'AS608_001';

-- 2. Tambahkan kolom sensor_location untuk kemudahan query
ALTER TABLE store_001 
ADD COLUMN IF NOT EXISTS sensor_location VARCHAR(20);

-- 3. Update sensor_location berdasarkan device_id yang ada
UPDATE store_001 
SET sensor_location = CASE 
    WHEN device_id = 'AS608_001' THEN 'masuk'
    WHEN device_id = 'AS608_002' THEN 'keluar'
    ELSE 'unknown'
END
WHERE sensor_location IS NULL;

-- 4. Hapus constraint UNIQUE pada user_id (akan diganti dengan composite)
ALTER TABLE store_001 
DROP CONSTRAINT IF EXISTS store_001_user_id_key;

-- 5. Tambahkan composite UNIQUE constraint (user_id, device_id)
-- Ini memungkinkan satu user punya multiple fingerprint di multiple sensor
-- Catatan: Drop dulu jika sudah ada, lalu buat baru
ALTER TABLE store_001 
DROP CONSTRAINT IF EXISTS store_001_user_device_unique;

ALTER TABLE store_001 
ADD CONSTRAINT store_001_user_device_unique 
UNIQUE (user_id, device_id);

-- 6. Buat index untuk performa query
CREATE INDEX IF NOT EXISTS idx_store_001_device_id ON store_001(device_id);
CREATE INDEX IF NOT EXISTS idx_store_001_user_device ON store_001(user_id, device_id);
CREATE INDEX IF NOT EXISTS idx_store_001_sensor_location ON store_001(sensor_location);

-- 7. Update view fingerprint_logs untuk include device info dari store_001
DROP VIEW IF EXISTS fingerprint_logs CASCADE;

CREATE VIEW fingerprint_logs AS
SELECT 
    ld.id,
    ld.user_id,
    ld.store_id,
    ld.timestamp,
    ld.finger_template_id,
    ld.device_id as scan_device_id,
    ld.sensor_location as scan_sensor_location,
    s.username,
    s.device_id as enrolled_device_id,
    s.sensor_location as enrolled_sensor_location,
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
LEFT JOIN store_001 s ON ld.user_id = s.user_id AND ld.device_id = s.device_id
ORDER BY ld.timestamp DESC;

-- 8. Buat view baru untuk melihat status enrollment per user per sensor
CREATE OR REPLACE VIEW user_enrollment_status AS
SELECT 
    s.user_id,
    s.username,
    s.device_id,
    s.sensor_location,
    s.finger_template_id,
    s.created_at as enrolled_at,
    s.updated_at as last_updated,
    CASE
        WHEN s.device_id = 'AS608_001' THEN 'Pintu Masuk'
        WHEN s.device_id = 'AS608_002' THEN 'Pintu Keluar'
        ELSE COALESCE(s.sensor_location, 'Unknown')
    END as location_display,
    -- Count total scans per device
    (SELECT COUNT(*) FROM log_data ld 
     WHERE ld.user_id = s.user_id AND ld.device_id = s.device_id) as total_scans,
    -- Last scan time per device
    (SELECT MAX(timestamp) FROM log_data ld 
     WHERE ld.user_id = s.user_id AND ld.device_id = s.device_id) as last_scan_time
FROM store_001 s
ORDER BY s.user_id, s.device_id;

-- 9. Buat view untuk summary user dengan status enrollment per sensor
-- Drop view dulu untuk menghindari error perubahan tipe data
DROP VIEW IF EXISTS user_enrollment_summary CASCADE;

CREATE VIEW user_enrollment_summary AS
SELECT 
    user_id,
    username,
    COUNT(DISTINCT device_id) as enrolled_sensors_count,
    STRING_AGG(DISTINCT device_id, ', ') as enrolled_devices,
    STRING_AGG(DISTINCT 
        CASE
            WHEN device_id = 'AS608_001' THEN 'Masuk'
            WHEN device_id = 'AS608_002' THEN 'Keluar'
            ELSE device_id
        END, ', '
    ) as enrolled_locations,
    MIN(created_at) as first_enrolled_at,
    MAX(updated_at) as last_updated_at,
    -- Check if enrolled in both sensors
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN device_id = 'AS608_001' THEN 1 END) > 0 
         AND COUNT(DISTINCT CASE WHEN device_id = 'AS608_002' THEN 1 END) > 0
        THEN 'Complete'
        WHEN COUNT(DISTINCT CASE WHEN device_id = 'AS608_001' THEN 1 END) > 0
        THEN 'Masuk Only'
        WHEN COUNT(DISTINCT CASE WHEN device_id = 'AS608_002' THEN 1 END) > 0
        THEN 'Keluar Only'
        ELSE 'Unknown'
    END as enrollment_status
FROM store_001
GROUP BY user_id, username
ORDER BY user_id;

-- 10. Verifikasi struktur tabel setelah perubahan
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name = 'store_001'
ORDER BY ordinal_position;

-- 11. Verifikasi constraints
SELECT 
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.table_schema = 'public'
    AND tc.table_name = 'store_001'
ORDER BY tc.constraint_type, tc.constraint_name;

-- =====================================================
-- Catatan:
-- =====================================================
-- 1. Setelah menjalankan script ini:
--    - store_001 sekarang support multiple fingerprint per user
--    - Satu user bisa punya finger_template_id berbeda di setiap sensor
--    - Constraint (user_id, device_id) UNIQUE memastikan tidak ada duplikasi
--
-- 2. Struktur baru:
--    - user_id: ID user (bisa sama untuk multiple sensor)
--    - device_id: ID sensor (AS608_001 atau AS608_002)
--    - finger_template_id: ID template di sensor tersebut
--    - username: Nama user (sama untuk semua sensor)
--
-- 3. Views baru:
--    - user_enrollment_status: Detail enrollment per user per sensor
--    - user_enrollment_summary: Summary enrollment status per user
--
-- 4. Update Application Code:
--    - handle_enrollment_response() perlu update untuk menyimpan device_id
--    - Semua query store_001 perlu update untuk handle device_id
--    - Web UI perlu update untuk menampilkan status enrollment per sensor
-- =====================================================

