-- Fix foreign key constraint untuk memungkinkan delete user
-- Versi 2: Handle jika constraint sudah ada

-- Step 1: Cek constraint yang ada
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_name = 'user_sessions'
  AND ccu.table_name = 'web_users';

-- Step 2: Drop existing constraint (jika ada)
-- Catatan: Nama constraint mungkin berbeda, cek dulu dengan query di atas
ALTER TABLE user_sessions 
DROP CONSTRAINT IF EXISTS user_sessions_user_id_fkey;

-- Jika nama constraint berbeda, gunakan nama yang benar dari query Step 1
-- Contoh: ALTER TABLE user_sessions DROP CONSTRAINT IF EXISTS <nama_constraint_dari_step1>;

-- Step 3: Add new constraint with ON DELETE CASCADE
ALTER TABLE user_sessions 
ADD CONSTRAINT user_sessions_user_id_fkey 
FOREIGN KEY (user_id) 
REFERENCES web_users(id) 
ON DELETE CASCADE;

-- Step 4: Verify constraint sudah benar
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_name = 'user_sessions'
  AND ccu.table_name = 'web_users';

-- Expected result: delete_rule harus 'CASCADE'

