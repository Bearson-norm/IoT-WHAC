-- Script Cepat: Cek Apakah Tabel Attendance Ada
-- Jalankan script ini di DBeaver untuk memverifikasi tabel attendance

-- ============================================
-- 1. Cek Tabel Attendance
-- ============================================
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Tabel attendance ADA'
        ELSE '❌ Tabel attendance TIDAK ADA'
    END as status_tabel,
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'attendance';

-- ============================================
-- 2. Cek View Attendance Summary
-- ============================================
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ View attendance_summary ADA'
        ELSE '❌ View attendance_summary TIDAK ADA'
    END as status_view,
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'attendance_summary';

-- ============================================
-- 3. Cek Struktur Tabel (jika ada)
-- ============================================
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'attendance'
ORDER BY ordinal_position;

-- ============================================
-- 4. Cek Jumlah Data (jika ada)
-- ============================================
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'attendance')
        THEN (SELECT COUNT(*)::text || ' baris data' FROM attendance)
        ELSE 'Tabel tidak ada'
    END as jumlah_data;

-- ============================================
-- 5. Test Query View (jika ada)
-- ============================================
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'attendance_summary')
        THEN '✅ View bisa diakses'
        ELSE '❌ View tidak bisa diakses'
    END as status_query_view;

-- Jika view ada, coba query ini:
-- SELECT * FROM attendance_summary LIMIT 5;



















