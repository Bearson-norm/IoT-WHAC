#!/bin/bash
# Simple script to sync users from localhost to Docker database

echo "============================================================"
echo "Sync Users from Localhost to Docker Database"
echo "============================================================"

# Export from localhost
echo "[1] Exporting users from localhost database..."
PGPASSWORD=Admin123 pg_dump -h localhost -U postgres -d whac_master \
    -t web_users --data-only --column-inserts \
    > web_users_export.sql

if [ $? -eq 0 ]; then
    echo "✅ Export successful"
else
    echo "❌ Export failed"
    exit 1
fi

# Import to Docker
echo "[2] Importing users to Docker database..."
docker exec -i whac-postgres psql -U postgres -d whac_master < web_users_export.sql

if [ $? -eq 0 ]; then
    echo "✅ Import successful"
else
    echo "❌ Import failed"
    exit 1
fi

# Verify
echo "[3] Verifying data in Docker database..."
docker exec -i whac-postgres psql -U postgres -d whac_master -c "
SELECT id, username, full_name, email, role, is_active 
FROM web_users 
ORDER BY created_at DESC;
"

echo "============================================================"
echo "Done!"
echo "============================================================"


























