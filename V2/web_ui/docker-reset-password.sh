#!/bin/bash
# Script to reset user password in Docker container
# Usage: bash docker-reset-password.sh <username> [new_password]

if [ $# -lt 1 ]; then
    echo "Usage: bash docker-reset-password.sh <username> [new_password]"
    echo ""
    echo "Contoh:"
    echo "  bash docker-reset-password.sh admin"
    echo "  bash docker-reset-password.sh admin mynewpassword"
    echo "  bash docker-reset-password.sh Mamat"
    exit 1
fi

USERNAME=$1
NEW_PASSWORD=${2:-password123}
CONTAINER_NAME="whac-postgres"

echo "============================================================"
echo "🔐 Reset Password di Docker Container"
echo "============================================================"

# Check if container exists
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  Container '${CONTAINER_NAME}' tidak ditemukan, mencari container PostgreSQL..."
    CONTAINER_NAME=$(docker ps --format '{{.Names}}' | grep -i postgres | head -n1)
    if [ -z "$CONTAINER_NAME" ]; then
        echo "❌ Container PostgreSQL tidak ditemukan!"
        echo "Pastikan Docker container sudah berjalan: docker ps"
        exit 1
    fi
    echo "✓ Menggunakan container: ${CONTAINER_NAME}"
fi

# Check if user exists
echo ""
echo "[*] Mengecek user '${USERNAME}'..."
USER_EXISTS=$(docker exec -i ${CONTAINER_NAME} psql -U postgres -d whac_master -t -c "SELECT COUNT(*) FROM web_users WHERE username = '${USERNAME}';" | tr -d ' ')

if [ "$USER_EXISTS" = "0" ]; then
    echo "❌ User '${USERNAME}' tidak ditemukan!"
    echo ""
    echo "[*] User yang tersedia:"
    docker exec -i ${CONTAINER_NAME} psql -U postgres -d whac_master -c "SELECT username, full_name, email, role FROM web_users ORDER BY username;"
    exit 1
fi

# Show user info
echo "✓ User ditemukan"
docker exec -i ${CONTAINER_NAME} psql -U postgres -d whac_master -c "SELECT id, username, full_name, email, role FROM web_users WHERE username = '${USERNAME}';"

# Generate password hash using Python in web-ui container (has bcrypt installed)
echo ""
echo "[*] Membuat password hash..."
WEB_UI_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i "web-ui\|webui" | head -n1)

if [ -n "$WEB_UI_CONTAINER" ]; then
    echo "   Menggunakan container: ${WEB_UI_CONTAINER}"
    HASH=$(docker exec ${WEB_UI_CONTAINER} python3 -c "import bcrypt; print(bcrypt.hashpw('${NEW_PASSWORD}'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))" 2>/dev/null)
fi

# Fallback: try postgres container
if [ -z "$HASH" ]; then
    HASH=$(docker exec ${CONTAINER_NAME} python3 -c "import bcrypt; print(bcrypt.hashpw('${NEW_PASSWORD}'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))" 2>/dev/null)
fi

# If still no hash, use Python script approach
if [ -z "$HASH" ]; then
    echo "   Python tidak tersedia di container, menggunakan script Python lokal..."
    HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw('${NEW_PASSWORD}'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))" 2>/dev/null)
fi

if [ -z "$HASH" ]; then
    echo "❌ Tidak bisa membuat password hash!"
    echo "   Pastikan Python dan bcrypt terinstall di salah satu container atau di host."
    exit 1
fi

# Update password
echo ""
echo "[*] Mereset password..."
docker exec -i ${CONTAINER_NAME} psql -U postgres -d whac_master << EOF
UPDATE web_users 
SET password_hash = '${HASH}',
    is_active = TRUE,
    locked_until = NULL,
    login_attempts = 0
WHERE username = '${USERNAME}';

SELECT id, username, is_active, login_attempts, locked_until 
FROM web_users 
WHERE username = '${USERNAME}';
EOF

echo ""
echo "============================================================"
echo "✅ Password berhasil direset!"
echo "============================================================"
echo "Login Credentials:"
echo "   Username: ${USERNAME}"
echo "   Password: ${NEW_PASSWORD}"
echo "============================================================"
echo "⚠️  Silakan ubah password setelah login!"
echo "============================================================"

