#!/bin/bash
# =====================================================
# Script untuk Setup Auto-Cleanup dengan Cron Job
# Database: whac_master
# =====================================================
# 
# Script ini membuat cron job untuk auto-cleanup logs
# lebih dari 3 bulan setiap hari jam 2 pagi
# =====================================================

# Konfigurasi
CONTAINER_NAME="whac-postgres"
DB_NAME="whac_master"
DB_USER="postgres"
CLEANUP_TIME="02:00"  # Jam 2 pagi

echo "============================================================"
echo "Setup Auto-Cleanup Cron Job"
echo "============================================================"
echo ""

# Cek apakah container berjalan
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container ${CONTAINER_NAME} tidak berjalan!"
    echo "   Jalankan: docker-compose up -d postgres"
    exit 1
fi

echo "✅ Container ${CONTAINER_NAME} berjalan"
echo ""

# Test koneksi database
echo "🔍 Testing database connection..."
if docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database connection OK"
else
    echo "❌ Database connection failed!"
    exit 1
fi
echo ""

# Cek apakah function sudah ada
echo "🔍 Checking cleanup functions..."
FUNCTION_EXISTS=$(docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -t -c "SELECT COUNT(*) FROM pg_proc WHERE proname = 'cleanup_old_log_data';" 2>/dev/null | tr -d ' ')

if [ "$FUNCTION_EXISTS" = "0" ]; then
    echo "⚠️  Cleanup function belum ada"
    echo "   Jalankan auto_cleanup_logs.sql terlebih dahulu"
    exit 1
fi

echo "✅ Cleanup function sudah ada"
echo ""

# Buat script untuk cleanup
CLEANUP_SCRIPT="/tmp/cleanup_logs.sh"
cat > ${CLEANUP_SCRIPT} << 'EOF'
#!/bin/bash
# Auto-cleanup logs lebih dari 3 bulan
docker exec whac-postgres psql -U postgres -d whac_master -c "SELECT * FROM cleanup_old_log_data();" >> /var/log/whac_cleanup.log 2>&1
EOF

chmod +x ${CLEANUP_SCRIPT}

echo "📝 Cleanup script created: ${CLEANUP_SCRIPT}"
echo ""

# Setup cron job (jika belum ada)
CRON_JOB="0 2 * * * ${CLEANUP_SCRIPT}"

if crontab -l 2>/dev/null | grep -q "${CLEANUP_SCRIPT}"; then
    echo "⚠️  Cron job sudah ada"
else
    echo "📅 Adding cron job..."
    (crontab -l 2>/dev/null; echo "${CRON_JOB}") | crontab -
    echo "✅ Cron job added: ${CRON_JOB}"
fi

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Cron job akan menjalankan cleanup setiap hari jam ${CLEANUP_TIME}"
echo "Log akan disimpan di: /var/log/whac_cleanup.log"
echo ""
echo "Untuk test manual:"
echo "  docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -c \"SELECT * FROM cleanup_old_log_data();\""
echo ""












