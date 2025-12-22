-- Fix foreign key constraint untuk memungkinkan delete user
-- Script ini akan mengubah foreign key di user_sessions untuk allow cascade delete

-- Step 1: Drop existing foreign key constraint
ALTER TABLE user_sessions 
DROP CONSTRAINT IF EXISTS user_sessions_user_id_fkey;

-- Step 2: Add new foreign key with ON DELETE CASCADE
ALTER TABLE user_sessions 
ADD CONSTRAINT user_sessions_user_id_fkey 
FOREIGN KEY (user_id) 
REFERENCES web_users(id) 
ON DELETE CASCADE;

-- Verify constraint
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

-- Test: Cek apakah ada data yang akan terpengaruh
SELECT 
    u.id,
    u.username,
    COUNT(s.id) as session_count
FROM web_users u
LEFT JOIN user_sessions s ON u.id = s.user_id
WHERE u.id IN (2, 3, 4)
GROUP BY u.id, u.username;


























