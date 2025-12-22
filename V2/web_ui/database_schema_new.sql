-- Database Schema untuk Sistem Baru
-- Unified table untuk user dari kedua sensor dengan device_id sebagai identifier
-- Tabel user_machine untuk enrollment dari modal
-- Tabel log unified untuk grant/deny

-- ============================================
-- 1. Tabel user_machine (User yang terdaftar di sistem)
-- ============================================
CREATE TABLE IF NOT EXISTS user_machine (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,                    -- ID user fingerprint dari sensor
    nama VARCHAR(100) NOT NULL,                 -- Nama user
    device_id VARCHAR(50) NOT NULL,              -- AS608_001, AS608_002 (unique identifier per device)
    posisi VARCHAR(100),                          -- Posisi/jabatan user
    finger_template_id INTEGER NOT NULL,         -- ID template fingerprint di sensor
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, device_id)                   -- Satu user bisa punya fingerprint di multiple device
);

-- Index untuk performa query
CREATE INDEX IF NOT EXISTS idx_user_machine_user_id ON user_machine(user_id);
CREATE INDEX IF NOT EXISTS idx_user_machine_device_id ON user_machine(device_id);
CREATE INDEX IF NOT EXISTS idx_user_machine_finger_template_id ON user_machine(finger_template_id);

-- ============================================
-- 2. Tabel access_log (Log unified untuk grant/deny)
-- ============================================
CREATE TABLE IF NOT EXISTS access_log (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,                 -- Nama user (bisa dari user_machine atau unknown)
    device_id VARCHAR(50) NOT NULL,              -- Nama Device (AS608_001, AS608_002)
    status VARCHAR(20) NOT NULL,                 -- 'granted' atau 'denied'
    user_id INTEGER,                             -- ID user jika terdaftar (NULL jika tidak terdaftar)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50),                     -- 'scan_verified', 'scan_unverified', 'manual'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk performa query
CREATE INDEX IF NOT EXISTS idx_access_log_timestamp ON access_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_access_log_device_id ON access_log(device_id);
CREATE INDEX IF NOT EXISTS idx_access_log_status ON access_log(status);
CREATE INDEX IF NOT EXISTS idx_access_log_user_id ON access_log(user_id);

-- ============================================
-- 3. Tabel gpio_log (Log untuk GPIO status)
-- ============================================
CREATE TABLE IF NOT EXISTS gpio_log (
    id SERIAL PRIMARY KEY,
    gpio_pin INTEGER NOT NULL,                   -- GPIO pin number (1, 2, 3)
    gpio_state VARCHAR(10) NOT NULL,             -- 'HIGH' atau 'LOW'
    event_type VARCHAR(50),                      -- 'relay_control', 'door_sensor', 'output_control'
    user_id INTEGER,                              -- ID user terkait (jika ada)
    device_id VARCHAR(50),                        -- Device ID terkait
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT                              -- Deskripsi event
);

-- Index untuk performa query
CREATE INDEX IF NOT EXISTS idx_gpio_log_timestamp ON gpio_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_gpio_log_gpio_pin ON gpio_log(gpio_pin);
CREATE INDEX IF NOT EXISTS idx_gpio_log_event_type ON gpio_log(event_type);

-- ============================================
-- View untuk query yang sering digunakan
-- ============================================

-- View untuk access log dengan detail user
CREATE OR REPLACE VIEW access_log_detail AS
SELECT 
    al.id,
    al.nama,
    al.device_id,
    CASE 
        WHEN al.device_id = 'AS608_001' THEN 'Pintu Masuk'
        WHEN al.device_id = 'AS608_002' THEN 'Pintu Keluar'
        ELSE al.device_id
    END as device_name,
    al.status,
    al.user_id,
    al.timestamp,
    al.action_type,
    um.posisi,
    CASE 
        WHEN al.status = 'granted' THEN 'success'
        WHEN al.status = 'denied' THEN 'danger'
        ELSE 'warning'
    END as status_class
FROM access_log al
LEFT JOIN user_machine um ON al.user_id = um.user_id AND al.device_id = um.device_id
ORDER BY al.timestamp DESC;

-- View untuk GPIO log dengan detail
CREATE OR REPLACE VIEW gpio_log_detail AS
SELECT 
    gl.id,
    gl.gpio_pin,
    gl.gpio_state,
    gl.event_type,
    gl.user_id,
    gl.device_id,
    gl.timestamp,
    gl.description,
    CASE 
        WHEN gl.gpio_state = 'HIGH' THEN 'success'
        WHEN gl.gpio_state = 'LOW' THEN 'secondary'
        ELSE 'warning'
    END as state_class
FROM gpio_log gl
ORDER BY gl.timestamp DESC;

-- ============================================
-- Comments untuk dokumentasi
-- ============================================
COMMENT ON TABLE user_machine IS 'Tabel untuk menyimpan user yang terdaftar di sistem fingerprint dari kedua sensor';
COMMENT ON TABLE access_log IS 'Tabel untuk menyimpan log akses (grant/deny) dari kedua sensor';
COMMENT ON TABLE gpio_log IS 'Tabel untuk menyimpan log status GPIO (relay control, door sensor, output control)';

COMMENT ON COLUMN user_machine.device_id IS 'Identifier unik per device: AS608_001 atau AS608_002';
COMMENT ON COLUMN access_log.device_id IS 'Identifier device yang mengirim data: AS608_001 atau AS608_002';
COMMENT ON COLUMN access_log.status IS 'Status akses: granted atau denied';



