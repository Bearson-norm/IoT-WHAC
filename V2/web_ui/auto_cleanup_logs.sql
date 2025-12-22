-- =====================================================
-- Script untuk Auto-Cleanup Logs (Hapus data lebih dari 3 bulan)
-- Database: whac_master
-- =====================================================
-- 
-- Script ini membuat:
-- 1. Function untuk cleanup data log_data dan log_action lebih dari 3 bulan
-- 2. Scheduled job (menggunakan pg_cron jika tersedia, atau manual trigger)
-- =====================================================

-- PERINGATAN: Backup database terlebih dahulu!
-- docker exec whac-postgres pg_dump -U postgres whac_master > backup_before_cleanup.sql

-- =====================================================
-- 1. Function untuk Cleanup Log Data (lebih dari 3 bulan)
-- =====================================================

CREATE OR REPLACE FUNCTION cleanup_old_log_data()
RETURNS TABLE(
    deleted_log_data_count BIGINT,
    deleted_log_action_count BIGINT,
    deleted_attendance_count BIGINT
) AS $$
DECLARE
    v_log_data_count BIGINT;
    v_log_action_count BIGINT;
    v_attendance_count BIGINT;
BEGIN
    -- Hapus log_data lebih dari 3 bulan
    DELETE FROM log_data
    WHERE timestamp < NOW() - INTERVAL '3 months';
    
    GET DIAGNOSTICS v_log_data_count = ROW_COUNT;
    
    -- Hapus log_action lebih dari 3 bulan
    DELETE FROM log_action
    WHERE timestamp < NOW() - INTERVAL '3 months';
    
    GET DIAGNOSTICS v_log_action_count = ROW_COUNT;
    
    -- Hapus attendance lebih dari 3 bulan (optional, bisa di-comment jika tidak perlu)
    DELETE FROM attendance
    WHERE attendance_date < CURRENT_DATE - INTERVAL '3 months';
    
    GET DIAGNOSTICS v_attendance_count = ROW_COUNT;
    
    -- Return hasil
    RETURN QUERY SELECT v_log_data_count, v_log_action_count, v_attendance_count;
    
    -- Log hasil (jika ada table untuk logging)
    RAISE NOTICE 'Cleanup completed: % log_data, % log_action, % attendance records deleted', 
        v_log_data_count, v_log_action_count, v_attendance_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. Function untuk Manual Cleanup (dengan parameter retention period)
-- =====================================================

CREATE OR REPLACE FUNCTION cleanup_old_logs_custom(retention_months INTEGER DEFAULT 3)
RETURNS TABLE(
    deleted_log_data_count BIGINT,
    deleted_log_action_count BIGINT,
    deleted_attendance_count BIGINT
) AS $$
DECLARE
    v_log_data_count BIGINT;
    v_log_action_count BIGINT;
    v_attendance_count BIGINT;
BEGIN
    -- Hapus log_data lebih dari retention_months
    DELETE FROM log_data
    WHERE timestamp < NOW() - (retention_months || ' months')::INTERVAL;
    
    GET DIAGNOSTICS v_log_data_count = ROW_COUNT;
    
    -- Hapus log_action lebih dari retention_months
    DELETE FROM log_action
    WHERE timestamp < NOW() - (retention_months || ' months')::INTERVAL;
    
    GET DIAGNOSTICS v_log_action_count = ROW_COUNT;
    
    -- Hapus attendance lebih dari retention_months
    DELETE FROM attendance
    WHERE attendance_date < CURRENT_DATE - (retention_months || ' months')::INTERVAL;
    
    GET DIAGNOSTICS v_attendance_count = ROW_COUNT;
    
    -- Return hasil
    RETURN QUERY SELECT v_log_data_count, v_log_action_count, v_attendance_count;
    
    RAISE NOTICE 'Cleanup completed (retention: % months): % log_data, % log_action, % attendance records deleted', 
        retention_months, v_log_data_count, v_log_action_count, v_attendance_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. Function untuk Preview Data yang Akan Dihapus (Dry Run)
-- =====================================================

CREATE OR REPLACE FUNCTION preview_old_logs(retention_months INTEGER DEFAULT 3)
RETURNS TABLE(
    table_name TEXT,
    record_count BIGINT,
    oldest_timestamp TIMESTAMP,
    newest_timestamp TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'log_data'::TEXT as table_name,
        COUNT(*)::BIGINT as record_count,
        MIN(timestamp) as oldest_timestamp,
        MAX(timestamp) as newest_timestamp
    FROM log_data
    WHERE timestamp < NOW() - (retention_months || ' months')::INTERVAL
    
    UNION ALL
    
    SELECT 
        'log_action'::TEXT as table_name,
        COUNT(*)::BIGINT as record_count,
        MIN(timestamp) as oldest_timestamp,
        MAX(timestamp) as newest_timestamp
    FROM log_action
    WHERE timestamp < NOW() - (retention_months || ' months')::INTERVAL
    
    UNION ALL
    
    SELECT 
        'attendance'::TEXT as table_name,
        COUNT(*)::BIGINT as record_count,
        MIN(attendance_date)::TIMESTAMP as oldest_timestamp,
        MAX(attendance_date)::TIMESTAMP as newest_timestamp
    FROM attendance
    WHERE attendance_date < CURRENT_DATE - (retention_months || ' months')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. Scheduled Job (menggunakan pg_cron jika tersedia)
-- =====================================================

-- Catatan: pg_cron extension perlu diinstall terlebih dahulu
-- Jika pg_cron tidak tersedia, gunakan cron job di sistem operasi atau manual trigger

-- Install pg_cron extension (jika belum ada)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule cleanup setiap hari jam 2 pagi
-- SELECT cron.schedule('cleanup-old-logs', '0 2 * * *', 'SELECT cleanup_old_log_data();');

-- =====================================================
-- 5. Verifikasi Functions
-- =====================================================

-- Cek functions yang sudah dibuat
SELECT 
    routine_name,
    routine_type,
    data_type as return_type
FROM information_schema.routines
WHERE routine_schema = 'public'
    AND routine_name LIKE 'cleanup%' OR routine_name LIKE 'preview%'
ORDER BY routine_name;

-- =====================================================
-- 6. Test Functions
-- =====================================================

-- Preview data yang akan dihapus (dry run)
-- SELECT * FROM preview_old_logs(3);

-- Jalankan cleanup (default 3 bulan)
-- SELECT * FROM cleanup_old_log_data();

-- Jalankan cleanup dengan custom retention period (contoh: 6 bulan)
-- SELECT * FROM cleanup_old_logs_custom(6);

-- =====================================================
-- Catatan:
-- =====================================================
-- 1. Function cleanup_old_log_data() akan menghapus data lebih dari 3 bulan
-- 2. Function cleanup_old_logs_custom() memungkinkan custom retention period
-- 3. Function preview_old_logs() untuk preview data yang akan dihapus (dry run)
-- 4. Untuk auto-schedule, install pg_cron extension atau gunakan cron job di OS
-- 5. Backup database secara berkala sebelum cleanup
-- =====================================================












