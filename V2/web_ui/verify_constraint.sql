-- Query untuk verify constraint (fixed - no ambiguous column)
-- Jalankan query ini untuk memastikan constraint sudah benar

SELECT 
    tc.constraint_name,
    rc.delete_rule
FROM information_schema.referential_constraints rc
JOIN information_schema.table_constraints tc 
  ON rc.constraint_name = tc.constraint_name
WHERE tc.table_name = 'user_sessions'
  AND tc.constraint_type = 'FOREIGN KEY';

-- Expected result:
-- constraint_name: user_sessions_user_id_fkey
-- delete_rule: CASCADE

-- Jika delete_rule = 'NO ACTION' atau 'RESTRICT', berarti constraint belum di-fix
-- Jika delete_rule = 'CASCADE', berarti constraint sudah benar ✅

