-- Simple fix: Drop dan recreate constraint dengan CASCADE
-- Jalankan query ini satu per satu di DBeaver

-- 1. Cek nama constraint yang ada
SELECT constraint_name 
FROM information_schema.table_constraints 
WHERE table_name = 'user_sessions' 
  AND constraint_type = 'FOREIGN KEY'
  AND table_schema = 'public';

-- 2. Drop constraint (gunakan nama dari query di atas jika berbeda)
ALTER TABLE user_sessions DROP CONSTRAINT user_sessions_user_id_fkey;

-- Jika error "constraint does not exist", cek nama constraint dengan query di step 1
-- Lalu gunakan nama yang benar, contoh:
-- ALTER TABLE user_sessions DROP CONSTRAINT <nama_constraint_yang_benar>;

-- 3. Add constraint baru dengan CASCADE
ALTER TABLE user_sessions 
ADD CONSTRAINT user_sessions_user_id_fkey 
FOREIGN KEY (user_id) 
REFERENCES web_users(id) 
ON DELETE CASCADE;

-- 4. Verify
SELECT 
    tc.constraint_name,
    rc.delete_rule
FROM information_schema.referential_constraints rc
JOIN information_schema.table_constraints tc 
  ON rc.constraint_name = tc.constraint_name
WHERE tc.table_name = 'user_sessions'
  AND tc.constraint_type = 'FOREIGN KEY';

-- delete_rule harus menunjukkan 'CASCADE'

