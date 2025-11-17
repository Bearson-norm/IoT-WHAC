#!/bin/bash
# Script to fix admin password in Docker container

echo "============================================================"
echo "Fixing Admin Password in Docker Database"
echo "============================================================"

# Connect to PostgreSQL container and fix admin password
docker exec -i whac-postgres psql -U postgres -d whac_master << EOF

-- Update admin password to 'admin123' with verified hash
UPDATE web_users 
SET password_hash = '\$2b\$12\$7cD0.neGPVGRNL3X9nzY6uc5G1Ek8OB/PBhYDvcjKvZ0mcYK9yOyS',
    is_active = TRUE,
    login_attempts = 0,
    locked_until = NULL
WHERE username = 'admin';

-- If admin doesn't exist, create it
INSERT INTO web_users (username, password_hash, full_name, email, role, is_active, login_attempts, locked_until)
SELECT 'admin', '\$2b\$12\$7cD0.neGPVGRNL3X9nzY6uc5G1Ek8OB/PBhYDvcjKvZ0mcYK9yOyS', 'System Administrator', 'admin@whac.com', 'admin', TRUE, 0, NULL
WHERE NOT EXISTS (SELECT 1 FROM web_users WHERE username = 'admin');

-- Show result
SELECT id, username, is_active, login_attempts, locked_until FROM web_users WHERE username = 'admin';

EOF

echo "============================================================"
echo "Done! Login with: admin / admin123"
echo "============================================================"


