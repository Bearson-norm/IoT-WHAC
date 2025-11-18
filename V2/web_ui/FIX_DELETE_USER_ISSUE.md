# Fix: Tidak Bisa Menghapus User dari web_users

## 🔍 Masalah

Ketika mencoba menghapus user dengan ID 2, 3, dan 4 dari tabel `web_users` menggunakan DBeaver, data tidak terhapus.

## 🔎 Penyebab

Masalahnya adalah **foreign key constraint** di tabel `user_sessions` yang mereferensi `web_users`:

```sql
user_id INTEGER REFERENCES web_users(id)
```

Constraint ini **tidak memiliki `ON DELETE CASCADE`**, sehingga PostgreSQL mencegah penghapusan user jika masih ada data di `user_sessions` yang mereferensi user tersebut.

**Default behavior** dari foreign key di PostgreSQL adalah `RESTRICT`, yang berarti:
- Tidak bisa menghapus parent record (web_users) jika ada child record (user_sessions) yang mereferensi
- Error yang muncul biasanya: `update or delete on table "web_users" violates foreign key constraint`

## 🔧 Solusi

### Solusi 1: Fix Foreign Key Constraint (Recommended)

**Jika mendapat error "constraint already exists":**

1. **Cek nama constraint yang ada dulu:**
```sql
SELECT constraint_name 
FROM information_schema.table_constraints 
WHERE table_name = 'user_sessions' 
  AND constraint_type = 'FOREIGN KEY'
  AND table_schema = 'public';
```

2. **Drop constraint yang ada (gunakan nama dari query di atas):**
```sql
-- Jika nama constraint adalah 'user_sessions_user_id_fkey'
ALTER TABLE user_sessions DROP CONSTRAINT user_sessions_user_id_fkey;

-- Atau jika nama berbeda, gunakan nama yang benar dari query step 1
-- Contoh: ALTER TABLE user_sessions DROP CONSTRAINT <nama_constraint_yang_benar>;
```

3. **Add constraint baru dengan CASCADE:**
```sql
ALTER TABLE user_sessions 
ADD CONSTRAINT user_sessions_user_id_fkey 
FOREIGN KEY (user_id) 
REFERENCES web_users(id) 
ON DELETE CASCADE;
```

4. **Verify:**
```sql
SELECT 
    tc.constraint_name,
    rc.delete_rule
FROM information_schema.referential_constraints rc
JOIN information_schema.table_constraints tc 
  ON rc.constraint_name = tc.constraint_name
WHERE tc.table_name = 'user_sessions'
  AND tc.constraint_type = 'FOREIGN KEY';
```

**Expected:** `delete_rule` harus `CASCADE`

**Keuntungan:**
- Setelah ini, menghapus user akan otomatis menghapus session terkait
- Tidak perlu manual delete session dulu
- Lebih aman dan konsisten

### Solusi 2: Hapus Manual (Temporary Fix)

Jika constraint belum di-fix, hapus session dulu sebelum hapus user:

```sql
BEGIN;

-- Hapus sessions terlebih dahulu
DELETE FROM user_sessions WHERE user_id IN (2, 3, 4);

-- Baru hapus user
DELETE FROM web_users WHERE id IN (2, 3, 4);

-- Verify
SELECT id, username FROM web_users ORDER BY id;

-- Jika OK, commit
COMMIT;

-- Jika ada masalah, rollback
-- ROLLBACK;
```

### Solusi 3: Menggunakan Script yang Sudah Dibuat

Gunakan script `delete_users_safely.sql`:

1. Buka DBeaver
2. Connect ke database
3. Buka file `delete_users_safely.sql`
4. Review query
5. Jalankan (pastikan uncomment `COMMIT` di akhir)

## 📋 Langkah-langkah Perbaikan

### Step 1: Fix Constraint (Sekali saja)

```sql
-- Jalankan di DBeaver
ALTER TABLE user_sessions 
DROP CONSTRAINT IF EXISTS user_sessions_user_id_fkey;

ALTER TABLE user_sessions 
ADD CONSTRAINT user_sessions_user_id_fkey 
FOREIGN KEY (user_id) 
REFERENCES web_users(id) 
ON DELETE CASCADE;
```

### Step 2: Verifikasi Constraint

```sql
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
```

**Expected result:** `delete_rule` harus `CASCADE`

### Step 3: Test Delete User

```sql
-- Test delete user (dengan transaction untuk safety)
BEGIN;

DELETE FROM web_users WHERE id = 2;

-- Cek apakah berhasil
SELECT id, username FROM web_users WHERE id = 2;
-- Harusnya tidak ada hasil

-- Jika OK, commit
COMMIT;

-- Jika ada masalah, rollback
-- ROLLBACK;
```

### Step 4: Hapus User yang Diinginkan

Setelah constraint sudah di-fix, Anda bisa langsung hapus:

```sql
-- Hapus user ID 2, 3, dan 4
DELETE FROM web_users WHERE id IN (2, 3, 4);

-- Verify
SELECT id, username, full_name, email, role 
FROM web_users 
ORDER BY id;
```

## 🔍 Cek Data yang Terpengaruh

Sebelum menghapus, cek apakah ada session yang terkait:

```sql
SELECT 
    u.id,
    u.username,
    COUNT(s.id) as session_count
FROM web_users u
LEFT JOIN user_sessions s ON u.id = s.user_id
WHERE u.id IN (2, 3, 4)
GROUP BY u.id, u.username;
```

Jika ada `session_count > 0`, session tersebut akan otomatis terhapus setelah constraint di-fix.

## ⚠️ Catatan Penting

1. **Backup Database** sebelum melakukan perubahan:
   ```bash
   docker exec whac-postgres pg_dump -U postgres whac_master > backup_before_fix.sql
   ```

2. **Transaction Safety**: Selalu gunakan `BEGIN` dan `COMMIT`/`ROLLBACK` saat testing

3. **Cascade Delete**: Setelah fix, menghapus user akan otomatis menghapus:
   - Session user di `user_sessions`
   - Data lain yang mereferensi user (jika ada)

4. **Future Setup**: File `database_setup.sql` sudah di-update untuk future deployment

## ✅ Verifikasi Setelah Fix

1. Constraint sudah di-update dengan `ON DELETE CASCADE`
2. Bisa menghapus user tanpa error
3. Session terkait otomatis terhapus
4. Data lain tidak terpengaruh

## 🐛 Troubleshooting

### Error: constraint does not exist
```sql
-- Cek nama constraint yang sebenarnya
SELECT constraint_name 
FROM information_schema.table_constraints 
WHERE table_name = 'user_sessions' 
  AND constraint_type = 'FOREIGN KEY';
```

### Error: cannot drop constraint because other objects depend on it
- Pastikan tidak ada view atau trigger yang depend pada constraint ini
- Jika ada, drop dulu atau ubah constraint name

### Masih tidak bisa delete setelah fix
- Pastikan transaction sudah di-commit
- Refresh connection di DBeaver
- Cek apakah ada constraint lain yang mencegah delete

---

**File yang dibuat:**
- `fix_delete_user_constraint.sql` - Script untuk fix constraint
- `delete_users_safely.sql` - Script untuk hapus user dengan aman
- `database_setup.sql` - Sudah di-update untuk future deployment

