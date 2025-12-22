-- Database Schema untuk User Machine dan Access Log
-- Tabel untuk menyimpan user yang terdaftar di local machine dengan device identifier

-- ============================================
-- 1. Tabel user_machine
-- ============================================
-- Menyimpan user yang terdaftar di local machine
-- Setiap user bisa terdaftar di multiple device dengan finger_template_id yang berbeda

CREATE TABLE IF NOT EXISTS user_machine (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,                    -- ID user fingerprint (sama dengan finger_template_id)
    nama VARCHAR(100) NOT NULL,                   -- Nama user
    device_id VARCHAR(50) NOT NULL,               -- Device identifier (AS608_001, AS608_002, dll)
    posisi VARCHAR(50),                           -- Posisi/jabatan user
    finger_template_id INTEGER NOT NULL,          -- ID template fingerprint di sensor
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, device_id)                    -- Satu user bisa punya multiple device, tapi tidak duplikat per device
);

-- Index untuk performa query
CREATE INDEX IF NOT EXISTS idx_user_machine_user_id ON user_machine(user_id);
CREATE INDEX IF NOT EXISTS idx_user_machine_device_id ON user_machine(device_id);
CREATE INDEX IF NOT EXISTS idx_user_machine_user_device ON user_machine(user_id, device_id);
CREATE INDEX IF NOT EXISTS idx_user_machine_finger_template_id ON user_machine(finger_template_id);

-- ============================================
-- 2. Tabel access_log
-- ============================================
-- Menyimpan log akses (grant/deny) dari modal popup

CREATE TABLE IF NOT EXISTS access_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,                              -- ID user (bisa NULL jika tidak terdaftar)
    nama VARCHAR(100),                            -- Nama user (untuk log, bisa dari user_machine atau input manual)
    device_id VARCHAR(50) NOT NULL,               -- Device identifier
    status VARCHAR(20) NOT NULL,                 -- 'granted' atau 'denied'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_source VARCHAR(50) DEFAULT 'modal',    -- 'modal', 'automatic', 'manual'
    finger_template_id INTEGER,                   -- ID template fingerprint yang di-scan
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk performa query
CREATE INDEX IF NOT EXISTS idx_access_log_user_id ON access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_access_log_device_id ON access_log(device_id);
CREATE INDEX IF NOT EXISTS idx_access_log_status ON access_log(status);
CREATE INDEX IF NOT EXISTS idx_access_log_timestamp ON access_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_access_log_user_device ON access_log(user_id, device_id);

-- ============================================
-- 3. Tabel gpio_log (jika belum ada)
-- ============================================
-- Menyimpan log GPIO status untuk monitoring

CREATE TABLE IF NOT EXISTS gpio_log (
    id SERIAL PRIMARY KEY,
    gpio_pin INTEGER NOT NULL,                    -- GPIO pin number (1, 2, 3)
    gpio_state VARCHAR(10) NOT NULL,             -- 'HIGH' atau 'LOW'
    event_type VARCHAR(50),                      -- 'relay_control', 'door_sensor', 'output_control'
    user_id INTEGER,                             -- ID user terkait (jika ada)
    device_id VARCHAR(50),                        -- Device identifier
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                             -- Deskripsi event
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk performa query
CREATE INDEX IF NOT EXISTS idx_gpio_log_gpio_pin ON gpio_log(gpio_pin);
CREATE INDEX IF NOT EXISTS idx_gpio_log_timestamp ON gpio_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_gpio_log_user_id ON gpio_log(user_id);
CREATE INDEX IF NOT EXISTS idx_gpio_log_device_id ON gpio_log(device_id);

-- ============================================
-- 4. Foreign Key Constraints (Optional)
-- ============================================
-- Uncomment jika ingin enforce referential integrity

-- ALTER TABLE access_log 
-- ADD CONSTRAINT fk_access_log_user_id 
-- FOREIGN KEY (user_id) REFERENCES user_machine(user_id) ON DELETE SET NULL;

-- ============================================
-- 5. Views untuk Query yang Sering Digunakan
-- ============================================

-- View untuk access log dengan info user
CREATE OR REPLACE VIEW access_log_with_user AS
SELECT 
    al.id,
    al.user_id,
    COALESCE(um.nama, al.nama) as nama,
    al.device_id,
    al.status,
    al.timestamp,
    al.action_source,
    al.finger_template_id,
    um.posisi,
    CASE
        WHEN al.device_id = 'AS608_001' THEN 'Pintu Masuk'
        WHEN al.device_id = 'AS608_002' THEN 'Pintu Keluar'
        ELSE al.device_id
    END as device_display
FROM access_log al
LEFT JOIN user_machine um ON al.user_id = um.user_id AND al.device_id = um.device_id
ORDER BY al.timestamp DESC;

-- ============================================
-- 6. Sample Data (Optional - untuk testing)
-- ============================================

-- INSERT INTO user_machine (user_id, nama, device_id, posisi, finger_template_id) VALUES
-- (1, 'John Doe', 'AS608_001', 'Manager', 1),
-- (2, 'Jane Smith', 'AS608_001', 'Staff', 2),
-- (1, 'John Doe', 'AS608_002', 'Manager', 1),
-- (2, 'Jane Smith', 'AS608_002', 'Staff', 2);

-- ============================================
-- Verification Queries
-- ============================================

-- Cek struktur tabel
-- \d user_machine
-- \d access_log
-- \d gpio_log

-- Cek data
-- SELECT * FROM user_machine;
-- SELECT * FROM access_log ORDER BY timestamp DESC LIMIT 10;
-- SELECT * FROM gpio_log ORDER BY timestamp DESC LIMIT 10;

