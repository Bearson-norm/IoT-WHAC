-- Script untuk menghapus user dengan aman
-- Menghapus user ID 2, 3, dan 4 beserta data terkait

BEGIN;

-- Step 1: Hapus user sessions terlebih dahulu (jika constraint belum di-fix)
DELETE FROM user_sessions WHERE user_id IN (2, 3, 4);

-- Step 2: Hapus user dari web_users
DELETE FROM web_users WHERE id IN (2, 3, 4);

-- Step 3: Verify deletion
SELECT id, username, full_name, email, role 
FROM web_users 
ORDER BY id;

-- Jika semua terlihat baik, commit transaction
-- COMMIT;

-- Jika ada masalah, rollback
-- ROLLBACK;

-- Catatan: Uncomment COMMIT atau ROLLBACK sesuai kebutuhan
-- Setelah yakin, jalankan COMMIT untuk menyimpan perubahan



