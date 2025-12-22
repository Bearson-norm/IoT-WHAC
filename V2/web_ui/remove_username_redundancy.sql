-- =====================================================
-- Script untuk Menghapus Redundansi Username
-- Database: whac_master
-- =====================================================
-- 
-- Script ini menghapus kolom username dari log_action dan attendance
-- karena username sudah ada di store_001 (sumber utama).
-- 
-- Setelah kolom dihapus, gunakan JOIN ke store_001 untuk
-- mendapatkan username saat query.
-- =====================================================

-- PERINGATAN: Backup data terlebih dahulu!
-- pg_dump -U postgres -d whac_master > backup_before_remove_username.sql

-- 1. Update views yang mungkin menggunakan kolom username
-- (Views akan otomatis update setelah kolom dihapus)

-- 2. Hapus kolom username dari log_action
-- Catatan: Pastikan views sudah di-drop terlebih dahulu
DROP VIEW IF EXISTS action_logs CASCADE;

ALTER TABLE log_action 
DROP COLUMN IF EXISTS username;

-- 3. Hapus kolom username dari attendance
DROP VIEW IF EXISTS attendance_summary CASCADE;

ALTER TABLE attendance 
DROP COLUMN IF EXISTS username;

-- 4. Recreate view action_logs dengan JOIN ke store_001
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
    END as location_display
FROM log_action la
LEFT JOIN store_001 s ON la.user_id = s.user_id
ORDER BY la.timestamp DESC;

-- 5. Recreate view attendance_summary dengan JOIN ke store_001
CREATE VIEW attendance_summary AS
SELECT 
    a.id,
    a.user_id,
    COALESCE(s.username, 'Unknown User') as username,  -- Ambil dari store_001
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
LEFT JOIN store_001 s ON a.user_id = s.user_id
ORDER BY a.attendance_date DESC, a.user_id;

-- 6. Verifikasi struktur tabel setelah perubahan
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name IN ('log_action', 'attendance', 'store_001')
ORDER BY table_name, ordinal_position;

-- =====================================================
-- Catatan:
-- =====================================================
-- 1. Setelah menjalankan script ini:
--    - Kolom username dihapus dari log_action dan attendance
--    - Views (action_logs, attendance_summary) sudah di-update
--      untuk menggunakan JOIN ke store_001
--
-- 2. Update Application Code:
--    - Pastikan semua query yang menggunakan username
--      dari log_action/attendance di-update untuk JOIN ke store_001
--    - Atau gunakan views yang sudah di-update
--
-- 3. Keuntungan:
--    - Tidak ada redundansi data
--    - Username selalu konsisten (sumber tunggal: store_001)
--    - Menghemat storage space
--
-- 4. File yang perlu di-update di application:
--    - web_ui/app.py (fungsi log_scan_to_database, log_manual_action)
--    - Semua query yang SELECT username dari log_action/attendance
-- =====================================================












