-- Script untuk membuat tabel attendance dan view attendance_summary
-- Jalankan script ini di DBeaver jika tabel attendance belum ada
-- Database: whac_master

-- ============================================
-- 1. Buat tabel attendance jika belum ada
-- ============================================
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username VARCHAR(100),
    attendance_date DATE NOT NULL,
    clock_in TIMESTAMP,
    clock_out TIMESTAMP,
    first_granted TIMESTAMP NOT NULL,
    last_granted TIMESTAMP NOT NULL,
    total_granted INTEGER DEFAULT 1,
    device_id_in VARCHAR(50),
    device_id_out VARCHAR(50),
    sensor_location_in VARCHAR(20),
    sensor_location_out VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, attendance_date)
);

-- ============================================
-- 2. Buat index untuk performa query
-- ============================================
CREATE INDEX IF NOT EXISTS idx_attendance_user_id ON attendance(user_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, attendance_date);

-- ============================================
-- 3. Hapus view lama jika ada (untuk update)
-- ============================================
DROP VIEW IF EXISTS attendance_summary CASCADE;

-- ============================================
-- 4. Buat view attendance_summary
-- ============================================
CREATE VIEW attendance_summary AS
SELECT 
    a.id,
    a.user_id,
    a.username,
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
ORDER BY a.attendance_date DESC, a.user_id;

-- ============================================
-- 5. Verifikasi tabel dan view sudah dibuat
-- ============================================
-- Jalankan query ini untuk memverifikasi:
-- SELECT table_name, table_type 
-- FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('attendance', 'attendance_summary')
-- ORDER BY table_name;

-- ============================================
-- 6. Test query untuk melihat struktur tabel
-- ============================================
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_schema = 'public' 
-- AND table_name = 'attendance'
-- ORDER BY ordinal_position;

-- ============================================
-- Selesai!
-- ============================================
-- Setelah script ini dijalankan, Anda seharusnya bisa melihat:
-- 1. Tabel 'attendance' di DBeaver
-- 2. View 'attendance_summary' di DBeaver
-- 
-- Jika masih tidak muncul, coba:
-- 1. Refresh database connection di DBeaver (klik kanan database -> Refresh)
-- 2. Pastikan Anda terhubung ke database 'whac_master'
-- 3. Pastikan Anda menggunakan schema 'public'



















