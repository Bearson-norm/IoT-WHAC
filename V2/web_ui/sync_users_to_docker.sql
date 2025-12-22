-- Script untuk sync user data dari database lokal ke Docker
-- Hanya insert user yang belum ada (berdasarkan username)

-- User: User (ID: 2)
INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until)
SELECT 'User', password_hash, 'Hilal', 'hilal@foom.id', 'operator', TRUE, created_at, last_login, login_attempts, locked_until
FROM web_users
WHERE username = 'User'
ON CONFLICT (username) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    last_login = EXCLUDED.last_login,
    login_attempts = EXCLUDED.login_attempts,
    locked_until = EXCLUDED.locked_until;

-- User: Mamat (ID: 3)
INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until)
SELECT 'Mamat', password_hash, 'Rahmat', 'Rahmat@foom.id', 'operator', TRUE, created_at, last_login, login_attempts, locked_until
FROM web_users
WHERE username = 'Mamat'
ON CONFLICT (username) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    last_login = EXCLUDED.last_login,
    login_attempts = EXCLUDED.login_attempts,
    locked_until = EXCLUDED.locked_until;

-- User: Greyoungter (ID: 4)
INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until)
SELECT 'Greyoungter', password_hash, 'Hilal Akbar Quddus Ramadhan', 'hakbarqr7333@gmail.com', 'admin', TRUE, created_at, last_login, login_attempts, locked_until
FROM web_users
WHERE username = 'Greyoungter'
ON CONFLICT (username) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    last_login = EXCLUDED.last_login,
    login_attempts = EXCLUDED.login_attempts,
    locked_until = EXCLUDED.locked_until;

-- User: Ramadhan (ID: 5)
INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, created_at, last_login, login_attempts, locked_until)
SELECT 'Ramadhan', password_hash, 'Ramadhan', 'ramadhan@foom.id', 'operator', TRUE, created_at, last_login, login_attempts, locked_until
FROM web_users
WHERE username = 'Ramadhan'
ON CONFLICT (username) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    last_login = EXCLUDED.last_login,
    login_attempts = EXCLUDED.login_attempts,
    locked_until = EXCLUDED.locked_until;

-- Verify
SELECT id, username, full_name, email, role, is_active 
FROM web_users 
ORDER BY created_at DESC;


























