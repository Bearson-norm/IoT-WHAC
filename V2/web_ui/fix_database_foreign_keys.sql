-- =====================================================
-- Script untuk Menambahkan Foreign Key Constraints
-- Database: whac_master
-- =====================================================
-- 
-- Script ini menambahkan Foreign Key constraints untuk
-- memastikan referential integrity antar tabel.
--
-- PERINGATAN: Pastikan data yang ada sudah valid sebelum
-- menjalankan script ini. Script akan gagal jika ada
-- data yang tidak valid (user_id yang tidak ada di store_001).
-- =====================================================

-- 1. Bersihkan data yang tidak valid terlebih dahulu
-- (Hapus log_data dengan user_id yang tidak ada di store_001)
-- Catatan: Hanya hapus jika user_id tidak NULL dan tidak ada di store_001
DELETE FROM log_data 
WHERE user_id IS NOT NULL 
AND user_id NOT IN (SELECT user_id FROM store_001 WHERE user_id IS NOT NULL);

-- 2. Bersihkan log_action dengan user_id yang tidak valid
DELETE FROM log_action 
WHERE user_id IS NOT NULL 
AND user_id NOT IN (SELECT user_id FROM store_001 WHERE user_id IS NOT NULL);

-- 3. Bersihkan attendance dengan user_id yang tidak valid
DELETE FROM attendance 
WHERE user_id IS NOT NULL 
AND user_id NOT IN (SELECT user_id FROM store_001 WHERE user_id IS NOT NULL);

-- 4. Tambahkan Foreign Key untuk log_data
-- ON DELETE SET NULL: Jika user dihapus, set user_id menjadi NULL (jaga history)
ALTER TABLE log_data 
DROP CONSTRAINT IF EXISTS fk_log_data_user_id;

ALTER TABLE log_data 
ADD CONSTRAINT fk_log_data_user_id 
FOREIGN KEY (user_id) 
REFERENCES store_001(user_id) 
ON DELETE SET NULL;

-- 5. Tambahkan Foreign Key untuk log_action
-- ON DELETE SET NULL: Jika user dihapus, set user_id menjadi NULL (jaga history)
ALTER TABLE log_action 
DROP CONSTRAINT IF EXISTS fk_log_action_user_id;

ALTER TABLE log_action 
ADD CONSTRAINT fk_log_action_user_id 
FOREIGN KEY (user_id) 
REFERENCES store_001(user_id) 
ON DELETE SET NULL;

-- 6. Tambahkan Foreign Key untuk attendance
-- ON DELETE CASCADE: Jika user dihapus, hapus juga attendance records
ALTER TABLE attendance 
DROP CONSTRAINT IF EXISTS fk_attendance_user_id;

ALTER TABLE attendance 
ADD CONSTRAINT fk_attendance_user_id 
FOREIGN KEY (user_id) 
REFERENCES store_001(user_id) 
ON DELETE CASCADE;

-- 7. Verifikasi constraints yang sudah ditambahkan
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
    AND tc.table_name IN ('log_data', 'log_action', 'attendance')
ORDER BY tc.table_name, tc.constraint_name;

-- =====================================================
-- Catatan:
-- =====================================================
-- 1. Foreign Key constraints akan memastikan bahwa:
--    - user_id di log_data, log_action, attendance 
--      harus ada di store_001 (atau NULL)
--
-- 2. ON DELETE SET NULL untuk log_data dan log_action:
--    - Jika user dihapus, history tetap ada tapi user_id = NULL
--    - Berguna untuk audit trail
--
-- 3. ON DELETE CASCADE untuk attendance:
--    - Jika user dihapus, attendance records juga dihapus
--    - Attendance adalah summary data, tidak perlu dipertahankan
--
-- 4. Setelah menjalankan script ini:
--    - Insert data dengan user_id yang tidak valid akan ditolak
--    - Database akan lebih konsisten dan aman
-- =====================================================












